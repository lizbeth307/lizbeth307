#!/usr/bin/env python3
"""Audit graph-to-PCB preparation without inventing commercial-module pads.

Run from any directory: python pcb/prepare.py [--check]
Outputs are deterministic; --check compares them with committed outputs.
This creates partition and placement INPUTS, not a fabrication release.
"""
from __future__ import annotations
import argparse
import collections
import csv
import hashlib
import io
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'pcb/generated'
ASSEMBLY_DETAIL = {'U102', 'R101', 'C101', 'C102'}
EXISTING_BOARD_DETAIL = {'U500'}
MODULE_REWORK = {'R117', 'R118', 'R119', 'R120', 'C118'}
SMT_MODULES = {'A407', 'A424'}  # Documented physical SMT pad maps, despite kind=module.
RF_TAP = {'R4420', 'R4430', 'R4440', 'C4420', 'C4430', 'C4440'}
RF_BLEED = {f'R{i}' for i in range(4460, 4472)}
RELAY_REFS = {'K401','K402','Q401','Q402','D401','R412','R413','R414','R415','R417','R418','R419','L407'}
BIAS_REFS = {'A424','C446','L401','L402','L403','L404','L406'} | {f'C{i}' for i in range(447,453)}
BOARDS = {
 'PWR_MAIN': {'purpose':'Main eFuse, AON/UV, charge inhibit and converter interconnect passives; commercial converters stay separate.', 'source':['design/E1-review.md','STACK.md §5.1']},
 'PWR_BRANCH': {'purpose':'E2 protected branches, current monitors and low-noise regulators. Candidate sub-board thermal split remains open.', 'source':['design/E2-review.md','STACK.md §5.1']},
 'CTRL_HMI': {'purpose':'Bare MCP/HMI control, input protection, cooling drivers and local interface passives; purchased Pico/sensors remain modules.', 'source':['design/E3-review.md','STACK.md §5.2']},
 'USB_POWER': {'purpose':'USB VBUS switches, HF+ LC damping, HDMI reverse isolation and LAB I2C buffer; intact high-speed cables retained.', 'source':['design/E5-review.md','design/E5-connection-guide.md']},
 'RF_HMC': {'purpose':'Three HMC7992 switches, their blocks, controls, pads/loads; final 50 ohm stackup not selected.', 'source':['design/E4-review.md','STACK.md §5.3/5.7']},
 'RF_HF': {'purpose':'Two DPDT HF/VHF relays, drivers and individually terminated PARK paths.', 'source':['design/E4-review.md','STACK.md §5.7']},
 'RF_INJECTOR': {'purpose':'Band-specific RF bias injectors, local RF bypass and three DC-tap/bleed front ends. May share RF substrate after qualification.', 'source':['design/E4-review.md','STACK.md §5.3']},
 'DC_CORE': {'purpose':'71-part low-frequency comparator/reference/sink core; RF taps and hot bleeds remain at RF ports, not on this core.', 'source':['design/E4-review.md','design/E4-detector-analysis.py']},
}
CONSTRAINTS = [
 {'id':'PWR-01','boards':['PWR_MAIN','PWR_BRANCH'],'requirement':'4.6 A main path and 50 °C enclosure qualification; LAB5 <=3.2 A continuous, 4 A transient acceptance. Size copper/vias/connectors from chosen stackup and thermal calculation; no trace width is asserted here.','source':'design/E1-review.md; E1-05/E1-06'},
 {'id':'PWR-02','boards':['PWR_MAIN'],'requirement':'Keep raw E1_CELL0/B- distinct from GND/P-. No accidental copper, mounting-hole or balance-cable BMS bypass. J102 remains DNP/service-only.','source':'design/E1-review.md; design/charger-bms-review.md'},
 {'id':'PWR-03','boards':['PWR_BRANCH'],'requirement':'LT3045 pair <=1 A physical total; Kelvin current-shunt routes, low-drop high-current planes, regulator exposed-pad heat flow and vendor capacitor placement are release work. LNB precision OVP and switch ratings need full temperature validation.','source':'design/E2-review.md'},
 {'id':'DC-01','boards':['DC_CORE','RF_INJECTOR'],'requirement':'Keep each first24.9k RF tap plus100pF at its RF port; place12 bleeds at RF ports, away from core reference/precision dividers. Core boundary carries filtered DC TAP, not50ohm RF. Original schematic nodes preserved.','source':'design/E4-review.md; E4.json DC detector groups'},
 {'id':'DC-02','boards':['DC_CORE'],'requirement':'Clean low-leakage SENSE layout, short divider/input routes and local ground; do not place hot bleeds/regulators beside precision network. Leakage/TCR/RF/ground error must be measured:98.630mV analytical corner has only1.370mV margin to100mV.','source':'design/E4-review.md; design/E4-detector-analysis.py'},
 {'id':'DC-03','boards':['DC_CORE'],'requirement':'Local100nF per comparator;1nF on each used internal reference; reference shunt/clamps/ground paths close. DCS HIGH=unsafe; LOW requires both window and both reference-good decisions. No signal pullup added on detector board; existing pullups belong E3.','source':'E4.json; https://www.ti.com/lit/ds/symlink/tlv3011.pdf'},
 {'id':'DC-04','boards':['DC_CORE','RF_INJECTOR'],'requirement':'Design envelope +/-30V limited DC. Verify chosen resistors rated voltage/power and PCB clearance for that envelope; no lightning/ESD compliance claim. Four249ohm bleeds dissipate0.226W each at30V and require >=0.5W parts with50C derating.','source':'design/E4-review.md; E4-06'},
 {'id':'DC-05','boards':['DC_CORE'],'requirement':'3V3_Q6A budget<=12mA includes E3 DCS pullups. At3.135V min supply, cold D450 VF must satisfy<=1.015V headroom for LM4040>=80uA. Each channel must reject+/-100mV over accepted temperature/supply and remain unsafe through startup/reference failure.','source':'design/E4-detector-analysis.py; design/E4-review.md'},
 {'id':'RF-01','boards':['RF_HMC','RF_INJECTOR'],'requirement':'50ohm geometry requires approved dielectric/copper stackup and vendor footprint reference planes. Ground EPAD/grounds with short low-inductance returns and via fences; all15 HMC RF-terminal DC blocks remain. No generic width or finished impedance claimed.','source':'https://www.analog.com/media/en/technical-documentation/data-sheets/hmc7992.pdf; design/E4-review.md'},
 {'id':'RF-02','boards':['RF_HF'],'requirement':'HF selector10kHz..260MHz IL<=0.3dB, RL>=21dB, isolation>=35dB at162..260MHz plus STACK LF gates. The detector996ohm bleed alone adds0.2153dB ideal loss, making this a real acceptance risk. Relays use2/3 contacts for HF/VHF.','source':'design/E4-review.md; STACK.md §5.7'},
 {'id':'RF-03','boards':['RF_HMC'],'requirement':'Power order GND->VDD->controls; shared3V3_Q6A,1k/100k/100pF controls,00 RF1 PARK. HMC isolation>=40dB at0.1..1.7GHz;37..40dB conditional only. X1 TX stays on internal load.','source':'design/E4-review.md'},
 {'id':'IO-01','boards':['CTRL_HMI','USB_POWER'],'requirement':'3.3V GPIO only; retain existing USB3/HDMI/PCIe cables/riser and their shield return. Do not create an unqualified high-speed PCB route from functional cable symbols. T7 WSON thermal condition TJ<=105C at1.5A requires copper/thermal validation.','source':'design/E3-review.md; design/E5-review.md'},
 {'id':'MECH-02','boards':['CTRL_HMI','PWR_BRANCH'],'requirement':'Existing mechanical source calls for MCP expanders15..20mm from TPS7A4701, PTC and buck inductors, and I2C away from switching nodes. Separate CTRL/PWR domains are candidates; if combined, preserve this separation and recheck enclosure fit.','source':'build/05-mekhanika.md §3 item15; STACK.md §5.8'},
 {'id':'MECH-01','boards':list(BOARDS),'requirement':'All partitions are engineering candidates. Final outline, mounting, stackup, copper weight, connector MPN/orientation and enclosure proof-fit are unset. No Gerbers/drill/production DRC is authorized by this preparation output.','source':'STACK.md §5.8; build/05-mekhanika.md; build/13-pcb-preparation.md'},
]

def dump(value): return json.dumps(value, ensure_ascii=False, indent=2) + '\n'
def require(ok, detail):
    # Not assert: python -O must not strip an audit and still print PASS.
    if not ok: raise SystemExit('PCB preparation audit FAIL: ' + str(detail))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def sort_ref(s):
    m=re.fullmatch(r'([^0-9]+)([0-9]+)',s)
    return (m[1],int(m[2])) if m else (s,0)
def csv_text(rows, fields):
    stream=io.StringIO(newline=''); w=csv.DictWriter(stream,fieldnames=fields,lineterminator='\n')
    w.writeheader();w.writerows({k:r.get(k,'') for k in fields} for r in rows)
    return stream.getvalue()

def category(c):
    ref=c['ref'];kind=c['kind']
    if ref in ASSEMBLY_DETAIL: return 'purchased_module_internal_detail', 'Adafruit5832', 'Existing purchased-breakout detail; do not buy/place a second INA228/shunt/capacitor.'
    if ref in EXISTING_BOARD_DETAIL:return 'purchased_module_internal_detail', 'Radxa_Q6A', 'Existing Q6A onboard rail-source detail; no second power module or PCB part is procured.'
    if ref.startswith('J'):return 'physical_interface_boundary','', 'Existing board/panel/cable or assembly feed boundary; physical mating part and mounting must be selected separately.'
    if ref in MODULE_REWORK: return 'module_rework_part', 'IP2368_COUT', 'Stock-board replacement/addition; actual revision pad locations/package remain to verify.'
    if ref in SMT_MODULES: return 'bare_board_part', '', 'Physical SMT RF component; kind=module does not mean a purchased enclosed module.'
    if kind=='module': return ('harness_assembly' if ref.startswith('W') else 'purchased_module'),'', 'Retain functional connector interfaces; no arbitrary module-pad footprint.'
    if kind=='connector':return 'physical_interface_boundary','', 'Existing board/panel/cable or assembly feed boundary; numeric contact map alone does not select a connector MPN.'
    if kind in ('battery','fuse','switch') or ref in ('TH101','TH102'):return 'mechanical_or_remote_part','', 'Mounting/terminal style and assembly ownership require mechanical integration; not automatically a PCB part.'
    if kind=='testpoint':return 'test_access_requirement','', 'Schematic access requirement; actual pad/hardware footprint not yet selected.'
    if kind=='net_tie':return 'bond_implementation_requirement','', 'Electrical bond requirement; choose physical strap/net-tie/mount implementation explicitly.'
    return 'bare_board_part','', 'Physical IC/passive/device for a custom board candidate.'

def board(c,cat):
    if cat!='bare_board_part':return ''
    s=c['_sheet'];ref=c['ref']
    if s!='E4':return {'E1':'PWR_MAIN','E2':'PWR_BRANCH','E3':'CTRL_HMI','E5':'USB_POWER'}[s]
    if c['group'].startswith('DC detectors'):
        return 'RF_INJECTOR' if ref in RF_TAP|RF_BLEED else 'DC_CORE'
    if ref in RELAY_REFS:return 'RF_HF'
    if ref in BIAS_REFS:return 'RF_INJECTOR'
    return 'RF_HMC'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    components=[];sources=[];graph_paths=[]
    for i in range(1,6):
        path=ROOT/f'design/E{i}.json';j=json.loads(path.read_text(encoding='utf-8'));graph_paths.append(path)
        sources.extend(j['sources'])
        for c in j['components']:components.append({**c,'_sheet':f'E{i}'})
    refs=[c['ref'] for c in components];require(len(refs)==len(set(refs)), 'Duplicate schematic reference')
    manifest_path=ROOT/'build/kicad/footprints/manifest.json'
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'));fps={f['footprint']:f for f in manifest['footprints']}
    for fp in fps.values():
        path=ROOT/fp['file'];require(sha(path)==fp['sha256'],f'Portable footprint hash mismatch: {path}')
        # Independently parse actual pad IDs, not just manifest claims.
        pads=set(re.findall(r'\(pad\s+"([^"]+)"',path.read_text(encoding='utf-8')))
        require(set(fp['pads'])<=pads,(fp['file'],pads,fp['pads']))
    all_nodes={};net_nodes=collections.defaultdict(list);rows=[];issues=[];core=[]
    for c in components:
        ref=c['ref'];cat,owner,why=category(c);domain=board(c,cat);pin_nums=[str(p['number']) for p in c['pins']]
        require(len(pin_nums)==len(set(pin_nums)),f'Duplicate pin: {ref}')
        for p in c['pins']:
            require(bool(p.get('net'))!=bool(p.get('nc')),f'Net/NC ambiguity: {ref}.{p["number"]}')
            if p.get('net'):
                all_nodes[(ref,str(p['number']))]=p['net'];net_nodes[p['net']].append({'ref':ref,'pin':str(p['number']),'sheet':c['_sheet'],'name':p['name']})
        fp=c.get('footprint','');portable=fp in fps
        missing=sorted(set(pin_nums)-set(fps[fp]['pads'])) if portable else []
        if missing:issues.append({'ref':ref,'type':'pin_pad_mismatch','blocking':True,'detail':missing})
        active=not c.get('dnp',False)
        if cat=='bare_board_part' and active and not fp:issues.append({'ref':ref,'type':'missing_physical_footprint','blocking':True,'detail':'Manufacturer land pattern/package and selected PCB footprint are not fixed.'})
        elif cat=='bare_board_part' and active and not portable:issues.append({'ref':ref,'type':'footprint_not_portable','blocking':True,'detail':fp})
        if cat in ('physical_interface_boundary','module_rework_part'):
            issues.append({'ref':ref,'type':'physical_interface_or_rework_unresolved','blocking':True,'detail':why})
        if cat=='bare_board_part' and active and c.get('status')=='TBD':issues.append({'ref':ref,'type':'schematic_component_TBD','blocking':True,'detail':c['value']})
        row={'ref':ref,'sheet':c['_sheet'],'value':c['value'],'kind':c['kind'],'category':cat,'assembly_owner':owner,'board_candidate':domain,'dnp':not active,'footprint':fp,'portable_footprint':portable,'pad_coverage':'PASS' if portable and not missing else 'UNASSIGNED' if not fp else 'FAIL','pin_count':len(pin_nums),'source':c.get('source',''),'classification_reason':why}
        rows.append(row)
        if domain=='DC_CORE':
            # Physical package selection is separate from verification/procurement readiness.
            candidate=fp
            status='graph_assigned_portable' if portable else 'proposed_not_production_qualified'
            if not candidate:
                if c['kind']=='resistor':candidate='Resistor_SMD:R_0402_1005Metric' if '0402' in c['value'] else 'Resistor_SMD:R_0603_1608Metric'
                elif c['kind']=='capacitor':candidate='Capacitor_SMD:C_0603_1608Metric'
            require(candidate, f'Core part lacks a footprint candidate: {ref}')
            core.append({k:v for k,v in c.items() if k!='_sheet'}|{'sheet':c['_sheet'],'placement_footprint':candidate,'placement_footprint_status':status,'placement_footprint_file':fps[candidate]['file'] if candidate in fps else None,'placement_blockers':[] if portable else ['Manufacturer MPN/land pattern approval required before production','Fetch official portable footprint first'] if candidate not in fps else ['Manufacturer MPN/package/land pattern approval required before production']})
    rows.sort(key=lambda r:sort_ref(r['ref']));core.sort(key=lambda c:sort_ref(c['ref']))
    # Audit source graph against the actual final KiCad-exported XML at every connected pin.
    xml_path=ROOT/'verification/netlist.xml';xml_nodes={}
    xml=ET.parse(xml_path).getroot()
    for n in xml.findall('./nets/net'):
        for node in n.findall('node'):
            key=(node.attrib['ref'],node.attrib['pin'])
            if key in all_nodes:xml_nodes[key]=n.attrib['name']
    mismatches=[{'ref':ref,'pin':pin,'graph_net':net,'xml_net':xml_nodes.get((ref,pin))} for (ref,pin),net in all_nodes.items() if xml_nodes.get((ref,pin))!=net]
    require(not mismatches,f'Schematic/XML mismatch: {mismatches[:5]}')
    core_refs={c['ref'] for c in core};core_nets={p['net'] for c in core for p in c['pins'] if p.get('net')}
    boundary=[]
    for net in sorted(core_nets):
        inside=[n for n in net_nodes[net] if n['ref'] in core_refs];outside=[n for n in net_nodes[net] if n['ref'] not in core_refs]
        if outside:boundary.append({'net':net,'core_nodes':inside,'external_nodes':outside,'connector_or_wire_pad_selected':False})
    expected_boundary={'3V3_Q6A','GND','DCS_UHF','DCS_LBAND','DCS_HF','E4_DCS_UHF_TAP','E4_DCS_LBAND_TAP','E4_DCS_HF_TAP'}
    require({b['net'] for b in boundary}==expected_boundary, sorted(b['net'] for b in boundary))
    require(len(core)==71, len(core))
    connected_core=sum(bool(p.get('net')) for c in core for p in c['pins'])
    summary={'status':'PREPARATION_ONLY_NOT_FOR_FABRICATION','components':len(rows),'schematic_contacts':sum(len(c['pins']) for c in components),'connected_contacts':len(all_nodes),'nets':len(net_nodes),'categories':dict(sorted(collections.Counter(r['category'] for r in rows).items())),'board_candidates':dict(sorted(collections.Counter(r['board_candidate'] for r in rows if r['board_candidate']).items())),'graph_assigned_footprints':sum(bool(r['footprint']) for r in rows),'portable_graph_assignments':sum(r['portable_footprint'] for r in rows),'bare_parts_without_footprint':sum(r['category']=='bare_board_part' and not r['footprint'] and not r['dnp'] for r in rows),'pin_pad_mismatches':sum(i['type']=='pin_pad_mismatch' for i in issues),'xml_connected_pin_audit':'PASS','xml_compared_connected_pins':len(all_nodes),'core_parts':len(core),'core_connected_pins':connected_core,'core_boundary_nets':len(boundary),'core_graph_assigned_footprints':sum(c['placement_footprint_status']=='graph_assigned_portable' for c in core),'core_proposed_footprints':sum(c['placement_footprint_status']!='graph_assigned_portable' for c in core),'blocking_issue_records':len(issues)}
    provenance={'inputs':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in graph_paths+[manifest_path,xml_path]],'source_documents':sorted({s['url'] for s in sources}),'generator':'pcb/prepare.py','note':'All classification/board splits are new controlled engineering proposals. They do not change E1..E5, claim module pin order, or authorize production.'}
    package={'summary':summary,'provenance':provenance,'boards':BOARDS,'constraints':CONSTRAINTS,'parts':rows,'unresolved':issues}
    detector={'board_id':'DC_CORE','status':'UNROUTED_PLACEMENT_INPUT_NOT_FABRICATION','part_count':len(core),'components':core,'nets':{n:[x for x in net_nodes[n] if x['ref'] in core_refs] for n in sorted(core_nets)},'external_boundary':boundary,'must_remain_at_RF_port':sorted(RF_TAP|RF_BLEED,key=sort_ref),'constraints':[c for c in CONSTRAINTS if 'DC_CORE' in c['boards']],'blockers':['50 passive land patterns are placement proposals, not approved production MPN selections.',*(['Three explicitly0402 resistor footprints must be fetched from official KiCad if absent.'] if not (ROOT/'build/kicad/footprints/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod').is_file() else []),'Eight-net connector/wire-pad implementation, mounting/outline and cable routing are unselected.','RF-port tap/bleed assemblies are excluded from this core and must be placed on the RF substrate.','Prototype threshold/leakage/temperature/ground-offset/RF/rail-off tests remain mandatory.'],'source_node_audit':{'source_graph':'design/E4.json','actual_xml':'verification/netlist.xml','connected_pins_checked':connected_core,'status':'PASS','all_pins':sum(len(c['pins']) for c in core),'nc_pins':sum(bool(p.get('nc')) for c in core for p in c['pins'])},'provenance':provenance}
    files={'partition.json':dump(package),'components.csv':csv_text(rows,['ref','sheet','value','kind','category','assembly_owner','board_candidate','dnp','footprint','portable_footprint','pad_coverage','pin_count','source','classification_reason']),'unresolved.csv':csv_text([{**i,'detail':json.dumps(i['detail'],ensure_ascii=False) if not isinstance(i['detail'],str) else i['detail']} for i in issues],['ref','type','blocking','detail']),'constraints.json':dump(CONSTRAINTS),'detector-core-input.json':dump(detector),'summary.json':dump(summary),'provenance.json':dump(provenance),'detector-core-nodes.csv':csv_text([{'ref':c['ref'],'pin':p['number'],'name':p['name'],'net':p.get('net',''),'nc':p.get('nc',False),'placement_footprint':c['placement_footprint'],'footprint_status':c['placement_footprint_status']} for c in core for p in c['pins']],['ref','pin','name','net','nc','placement_footprint','footprint_status'])}
    if args.check:
        stale=[name for name,content in files.items() if not (OUT/name).exists() or (OUT/name).read_text(encoding='utf-8')!=content]
        require(not stale,'Stale generated output: '+', '.join(stale))
    else:
        OUT.mkdir(parents=True,exist_ok=True)
        for name,content in files.items():(OUT/name).write_text(content,encoding='utf-8',newline='\n')
    print(dump(summary),end='')

if __name__=='__main__': main()
