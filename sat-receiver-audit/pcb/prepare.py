#!/usr/bin/env python3
"""Audit graph-to-PCB preparation without inventing commercial-module pads.

Run from any directory: python pcb/prepare.py [--check]
Outputs are deterministic; --check compares them with committed outputs.
This creates partition and placement INPUTS, not a fabrication release.
"""
from __future__ import annotations
import argparse
import ast
import collections
import csv
import hashlib
import io
import json
import math
import re
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'pcb/generated'
ASSEMBLY_DETAIL = {'U102', 'R101', 'C101', 'C102'}
EXISTING_BOARD_DETAIL = {'U500'}
MODULE_REWORK = {'R117', 'R118', 'R119', 'R120', 'C118'}
SMT_MODULES = {'A407', 'A424'}  # Documented physical SMT pad maps, despite kind=module.
PARTS_DB = ROOT / 'design/parts/parts.json'
# pcb_pad: bare copper test pads and the NT401 net tie are board parts too (footprint, nothing to buy).
BOARD_MOUNTS = {'pcb_smt', 'pcb_tht', 'pcb_module', 'pcb_pad'}
RF_TAP = {'R4420', 'R4430', 'R4440', 'C4420', 'C4430', 'C4440'}
RF_BLEED = {f'R{i}' for i in range(4460, 4472)}
RELAY_REFS = {'K401','K402','Q401','Q402','D401','R412','R413','R414','R415','R417','R418','R419','L407'}
BIAS_REFS = {'A424','C446','L402','L403','L404','L406'} | {f'C{i}' for i in range(447,453)}
# Board-side RF port connectors (W2 GR-2): each sits with the circuit it feeds (injector ports, the P6 relay input).
# The panel pigtail ends (J401-J403, J406, J408) and J428 (input of the external P8 accessory) stay interfaces.
RF_PORT_BOARD = {'J423':'RF_INJECTOR','J424':'RF_INJECTOR','J425':'RF_HF','J426':'RF_INJECTOR','J427':'RF_INJECTOR'}
BOARDS = {
 'PWR_MAIN': {'purpose':'Main eFuse, AON/UV, charge inhibit and converter interconnect passives; commercial converters stay separate.', 'source':['design/E1-review.md','STACK.md §5.1']},
 'PWR_BRANCH': {'purpose':'E2 protected branches, current monitors and low-noise regulators. Candidate sub-board thermal split remains open.', 'source':['design/E2-review.md','STACK.md §5.1']},
 'PWR_BRANCH_SW': {'purpose':'PWR-B mezzanine (W2 AREA/GR-3): the E2 switch groups of partition.PWR_B_groups (LNA ch1-4, RTL-B, S-band LaNA, INA3221 #1, LNB/Boni/AUX12 monitors) no taller than hB, plus the PWR-B side-entry harness headers; joined to PWR-A by the Samtec LSHM-150 pair J208 (PWR-A top) / J209 (PWR-B bottom) (b2b-nets.json, W2 B2B).', 'source':['pcb/partition-spec.json','design/E2-review.md']},
 'USB_POWER_SW': {'purpose':'PWR-B mezzanine (W2 AREA/GR-3): the E5 groups VBUS RTL-A/LAB PORT and LAB BUS I2C buffer no taller than hB, plus the PWR-B side-entry harness headers of E5.', 'source':['pcb/partition-spec.json','design/E5-review.md']},
 'CTRL_HMI': {'purpose':'Bare MCP/HMI control, input protection, cooling drivers and local interface passives; purchased Pico/sensors remain modules.', 'source':['design/E3-review.md','STACK.md §5.2']},
 'USB_POWER': {'purpose':'USB VBUS switches, HF+ LC damping, HDMI reverse isolation and LAB I2C buffer; intact high-speed cables retained.', 'source':['design/E5-review.md','design/E5-connection-guide.md']},
 'RF_HMC': {'purpose':'Three HMC7992 switches, their blocks, controls, pads/loads; final 50 ohm stackup not selected.', 'source':['design/E4-review.md','STACK.md §5.3/5.7']},
 'RF_HF': {'purpose':'Two DPDT HF/VHF relays, drivers and individually terminated PARK paths.', 'source':['design/E4-review.md','STACK.md §5.7']},
 'RF_INJECTOR': {'purpose':'Band-specific RF bias injectors, local RF bypass and three DC-tap/bleed front ends. May share RF substrate after qualification.', 'source':['design/E4-review.md','STACK.md §5.3']},
 'DC_CORE': {'purpose':'71-part low-frequency comparator/reference/sink core; RF taps and hot bleeds remain at RF ports, not on this core.', 'source':['design/E4-review.md','design/E4-detector-analysis.py']},
 'ENC': {'purpose':'Replaceable encoder daughterboard (PEC11R-4220F with its push switch), two in use plus one spare; harness to CTRL_HMI.', 'source':['STACK.md §5.8','mechanical/params/boards.json ENC','build/15-rishennia-komplektu.md']},
 'HATCH': {'purpose':'Service-hatch board in the rear hatch bay: J503 J21 service header (Micro-Fit 3) and J502 UART5 console header (JST PH 3); harness from PWR/CTRL.', 'source':['STACK.md §5.8 (service hatch)','build/15-rishennia-komplektu.md']},
 'T7_INSERT': {'purpose':'In-line VBUS key insert of the T7 USB3 cable (E5 U505 and its passives); built off the plate boards.', 'source':['design/E5-connection-guide.md §7','build/16-dzhgut.md']},
 'HDMI_INSERT': {'purpose':'In-line HDMI pin-18 insert of the display cable (E5 U506 and its passives); built off the plate boards.', 'source':['design/E5-connection-guide.md §8','build/16-dzhgut.md']},
 'IMU_CARRIER': {'purpose':'Carrier board inside the Hammond 1550Z101 IMU pack: E5 IMU supply/data protection and the bare parts of E3 group External IMU.', 'source':['design/E5-connection-guide.md','design/E3-review.md','mechanical/params/imu_pack.json']},
 'PACK_FUSE': {'purpose':'Small F101 carrier at the pack positive: Keystone 3568 mini-blade holder and 18 AWG solder pads, insulated and fixed beside the battery tray.', 'source':['STACK.md D2','build/15-rishennia-komplektu.md']},
}
PARTITION_SPEC = ROOT / 'pcb/partition-spec.json'
PWR_A_DOMAINS = ('PWR_MAIN', 'PWR_BRANCH', 'USB_POWER')
PWR_B_DOMAINS = ('PWR_BRANCH_SW', 'USB_POWER_SW')
def pwr_b_overrides():
    """PWR-A/PWR-B partition of pcb/partition-spec.json (W2 AREA decision, GR-3): E2 parts of partition.PWR_B_groups -> PWR_BRANCH_SW,
    E5 parts -> USB_POWER_SW; the parts of partition.domain_override_pwr_a (taller than hB) keep their PWR-A domain."""
    spec = json.loads(PARTITION_SPEC.read_text(encoding='utf-8'))['partition']
    groups = {(g['sheet'], g['group']) for g in spec['PWR_B_groups']}
    keep = set(spec['domain_override_pwr_a'])
    out = {}
    for sheet, dom in (('E2', 'PWR_BRANCH_SW'), ('E5', 'USB_POWER_SW')):
        for c in json.loads((ROOT / f'design/{sheet}.json').read_text(encoding='utf-8'))['components']:
            if (sheet, c.get('group', '')) in groups and c['ref'] not in keep:
                out[c['ref']] = dom
    return out
# Board parts assembled off the plate boards (build/15, build/16 §2): their own domain instead of the sheet default.
# W2 GR-3: the hatch-board harness headers sit on HATCH, and the PWR side-entry headers that tie to PWR-B parts on PWR-B
# (tools/assembly_data.py HEADERS); the other PWR headers keep their sheet domain on PWR-A.
# W2 GR-4: the boundary refs of the insert boards (S24 header J514, solder-wire pads J515-J517, J518, J320-J322, J116/J117)
# sit on their insert board, so every off-board net of T7_INSERT, IMU_CARRIER and PACK_FUSE ends on a connector of that board.
# W2 B2B: J209, the PWR-B half of the Samtec LSHM-150 board-to-board pair (bottom side of PWR-B), sits on PWR-B; J208 keeps E2 PWR-A.
DOMAIN_OVERRIDE = {**pwr_b_overrides(), **{r:'ENC' for r in ('ENC301','ENC302')}, **{r:'HATCH' for r in ('J502','J503','J509','J510','J513')},
 **{r:'PWR_BRANCH_SW' for r in ('J201','J202','J203','J204','J207','J209')}, **{r:'USB_POWER_SW' for r in ('J506','J508')},
 **{r:'T7_INSERT' for r in ('U505','R514','R515','R516','R517','C514','C515','C516','TP501','J514','J515','J516','J517')},
 **{r:'HDMI_INSERT' for r in ('U506','C517','C518','R552','TP502')},
 **{r:'IMU_CARRIER' for r in ('U552','D502','C519','C520','C340','C341','R390','R391','J518','J320','J321','J322')},
 **{r:'PACK_FUSE' for r in ('F101','J116','J117')}}
CONSTRAINTS = [
 {'id':'PWR-01','boards':['PWR_MAIN','PWR_BRANCH','PWR_BRANCH_SW','USB_POWER_SW'],'requirement':'4.6 A main path and 50 °C enclosure qualification; LAB5 <=3.2 A continuous, 4 A transient acceptance. Size copper/vias/connectors from chosen stackup and thermal calculation; no trace width is asserted here.','source':'design/E1-review.md; E1-05/E1-06'},
 {'id':'PWR-02','boards':['PWR_MAIN'],'requirement':'Keep raw E1_CELL0/B- distinct from GND/P-. No accidental copper, mounting-hole or balance-cable BMS bypass. J102 remains DNP/service-only.','source':'design/E1-review.md; design/charger-bms-review.md'},
 {'id':'PWR-03','boards':['PWR_BRANCH','PWR_BRANCH_SW'],'requirement':'LT3045 pair <=1 A physical total; Kelvin current-shunt routes, low-drop high-current planes, regulator exposed-pad heat flow and vendor capacitor placement are release work. LNB precision OVP and switch ratings need full temperature validation.','source':'design/E2-review.md'},
 {'id':'PWR-04','boards':['PWR_MAIN','PWR_BRANCH','USB_POWER','PWR_BRANCH_SW','USB_POWER_SW'],'requirement':'PWR-A/PWR-B mezzanine: every net with pins on both boards crosses only through the Samtec LSHM-150-02.5-L-DV-A-N-K-TR pair J208 (PWR-A top) / J209 (PWR-B bottom), 5.00 mm mated (pcb/generated/b2b-nets.json contacts: ceil(I_protection / 1 A) contacts per power net, no ground plane, so every rail contact (power, sense/supply tap, rail node) has its GND return in the same column and only GND contacts beside it in its row (b2b.guard_rule); pin n of J208 meets pin n+1 (n odd) / n-1 (n even) of J209); no Kelvin or precision net crosses except the declared sense pairs. PWR-B parts no taller than hB 5.5 mm; PWR-A parts under PWR-B no taller than hA 4.5 mm (pcb/partition-spec.json).','source':'pcb/partition-spec.json (W2 AREA, W2 B2B); Samtec LSHM specification Rev H, catalogue F-224, print Rev Z note 4'},
 {'id':'DC-01','boards':['DC_CORE','RF_INJECTOR'],'requirement':'Keep each first26.7k RF tap (R4420/R4430/R4440) plus100pF at its RF port (U.FL J423/J424, HF_CM); place12 bleeds at RF ports, away from core reference/precision dividers. Core boundary carries filtered DC TAP, not50ohm RF. Original schematic nodes preserved.','source':'design/E4-review.md; E4.json DC detector groups'},
 {'id':'DC-02','boards':['DC_CORE'],'requirement':'Clean low-leakage SENSE layout, short divider/input routes and local ground; do not place hot bleeds/regulators beside precision network. Leakage/TCR/RF/ground error must be measured:98.638mV analytical corner has only1.362mV margin to100mV.','source':'design/E4-review.md; design/E4-detector-analysis.py'},
 {'id':'DC-03','boards':['DC_CORE'],'requirement':'Local100nF per comparator;1nF on each used internal reference; reference shunt/clamps/ground paths close. DCS HIGH=unsafe; LOW requires both window and both reference-good decisions. No signal pullup added on detector board; existing pullups belong E3.','source':'E4.json; https://www.ti.com/lit/ds/symlink/tlv3011.pdf'},
 {'id':'DC-04','boards':['DC_CORE','RF_INJECTOR'],'requirement':'Design envelope +/-30V limited DC. Verify chosen resistors rated voltage/power and PCB clearance for that envelope; no lightning/ESD compliance claim. Four249ohm bleeds dissipate0.226W each at30V and require >=0.5W parts with50C derating.','source':'design/E4-review.md; E4-06'},
 {'id':'DC-05','boards':['DC_CORE'],'requirement':'3V3_Q6A budget<=12mA includes E3 DCS pullups. At3.135V min supply, cold D450 VF must satisfy<=1.015V headroom for LM4040>=80uA. Each channel must reject+/-100mV over accepted temperature/supply and remain unsafe through startup/reference failure.','source':'design/E4-detector-analysis.py; design/E4-review.md'},
 {'id':'RF-01','boards':['RF_HMC','RF_INJECTOR'],'requirement':'50ohm geometry requires approved dielectric/copper stackup and vendor footprint reference planes. Ground EPAD/grounds with short low-inductance returns and via fences; all15 HMC RF-terminal DC blocks remain. No generic width or finished impedance claimed.','source':'https://www.analog.com/media/en/technical-documentation/data-sheets/hmc7992.pdf; design/E4-review.md'},
 {'id':'RF-02','boards':['RF_HF'],'requirement':'HF selector10kHz..260MHz IL<=0.3dB, RL>=21dB, isolation>=35dB at162..260MHz plus STACK LF gates. The detector996ohm bleed alone adds0.2153dB ideal loss, making this a real acceptance risk. Relays use2/3 contacts for HF/VHF.','source':'design/E4-review.md; STACK.md §5.7'},
 {'id':'RF-03','boards':['RF_HMC'],'requirement':'Power order GND->VDD->controls; shared3V3_Q6A,1k/100k/100pF controls,00 RF1 PARK. HMC isolation>=40dB at0.1..1.7GHz;37..40dB conditional only. X1 TX stays on internal load.','source':'design/E4-review.md'},
 {'id':'IO-01','boards':['CTRL_HMI','USB_POWER','USB_POWER_SW'],'requirement':'3.3V GPIO only; retain existing USB3/HDMI/PCIe cables/riser and their shield return. Do not create an unqualified high-speed PCB route from functional cable symbols. T7 WSON thermal condition TJ<=105C at1.5A requires copper/thermal validation.','source':'design/E3-review.md; design/E5-review.md'},
 {'id':'MECH-02','boards':['CTRL_HMI','PWR_BRANCH','PWR_BRANCH_SW'],'requirement':'Existing mechanical source calls for MCP expanders15..20mm from TPS7A4701, PTC and buck inductors, and I2C away from switching nodes. Separate CTRL/PWR domains are candidates; if combined, preserve this separation and recheck enclosure fit.','source':'build/05-mekhanika.md §3 item15; STACK.md §5.8'},
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

def parts_db():
    # Mount decision per ref (design/parts/parts.json, tools/build_parts.py): which refs are board parts.
    db=json.loads(PARTS_DB.read_text(encoding='utf-8'))
    return {r:p for p in db['parts'] for r in p['refs']}

PARTS_DB_FIELDS=('id','mount','mpn','tbd','host','interface_open','interface_resolved')
def parts_projection(db):
    # Only the parts-database fields this script reads, per ref: a stock note or harness family edit does not change the outputs.
    def field(p,k,ref):
        v=p.get(k)
        return v.get(ref) if isinstance(v,dict) and k in ('host','interface_open') else v
    return {ref:{k:field(p,k,ref) for k in PARTS_DB_FIELDS if field(p,k,ref) is not None} for ref,p in sorted(db.items(),key=lambda x:sort_ref(x[0]))}

def interface_issues(c,cat,db,by_ref):
    """Blocking records of a connector/feed that is not a board part, and of a virtual contact whose host pad has no net."""
    ref=c['ref'];p=db.get(ref);out=[];why=category(c)[2]
    if cat=='module_rework_part' or (cat=='physical_interface_boundary' and (p is None or p.get('tbd'))):
        out.append({'ref':ref,'type':'physical_interface_or_rework_unresolved','blocking':True,'detail':why if p is None or not p.get('tbd') else why+' Parts database: '+p['tbd']})
    elif cat=='physical_interface_boundary' and not p.get('interface_resolved'):
        # The part is selected, but its mating part and/or mounting are not: still blocking.
        opened=p.get('interface_open');opened=opened.get(ref) if isinstance(opened,dict) else opened
        chosen=f"{p['id']} (mount {p['mount']}"+(f", MPN {p['mpn']}" if p.get('mpn') else ', no MPN')+')'
        out.append({'ref':ref,'type':'interface_mounting_unresolved','blocking':True,'detail':f'Parts database entry {chosen} in design/parts/parts.json: mating part and mounting are not both fixed. Open: '+(opened or 'not stated (tools/build_parts.py requires interface_open)')})
    if cat=='integral_to_host_part' and p is not None:
        host=(p.get('host') or {}).get(ref);host_nets={x['net'] for x in by_ref[host]['pins'] if x.get('net')} if host in by_ref else set()
        missing=sorted({x['net'] for x in c['pins'] if x.get('net')}-host_nets)
        if host is None or missing:
            out.append({'ref':ref,'type':'host_pads_unconnected','blocking':True,'detail':f'Contact of {host} (host in design/parts/parts.json), but net(s) {", ".join(missing)} reach no pin of {host}: the host footprint pads for this contact carry no net, so it is unconnected on any layout until the sheet owner moves the nets onto host pins.'})
    return out

def category(c):
    ref=c['ref'];kind=c['kind'];mount=c.get('_mount')
    if mount in BOARD_MOUNTS and ref not in ASSEMBLY_DETAIL|EXISTING_BOARD_DETAIL|MODULE_REWORK:
        return 'bare_board_part','', f'Board part, mount {mount} in design/parts/parts.json.'
    if mount=='remote':return 'mechanical_or_remote_part','', 'Leaded/remote part on wires (mount remote in design/parts/parts.json); not a PCB footprint.'
    if mount=='virtual':return 'integral_to_host_part','', 'Contact of another board part (host in design/parts/parts.json); not bought or placed separately.'
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

def net_currents():
    # tools/assembly_data.py NET_CURRENT (protection limits), read with ast: this script imports no tool module.
    tree=ast.parse((ROOT/'tools/assembly_data.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='NET_CURRENT' for t in node.targets):
            return {k:v[1] for k,v in ast.literal_eval(node.value).items()}
    raise SystemExit('PCB preparation audit FAIL: tools/assembly_data.py NET_CURRENT not found')

def sense_nets(components,currents):
    """Kelvin nets (a part value says Kelvin), INA inputs (pins IN+/IN-, either minus sign) and precision divider mid-points (two or more 0.1/0.5 %
    resistors into an IC input, not a rail): the rule of pcb/partition_budget.py (W2 AREA), applied here to the B2B net list."""
    kelvin,precision,res=set(),set(),{}
    flags=set().union(*(c['_flags'] for c in components))
    for c in components:
        nets={p['net'] for p in c['pins'] if p.get('net')}
        if 'Kelvin' in c.get('value',''):kelvin|=nets-{'GND'}
        for p in c['pins']:
            if p.get('net') and re.match(r'IN[+\-\u2212]\d?$',p.get('name','')):precision.add(p['net'])
        if c['ref'].startswith('R') and re.search(r'0\.[15] ?%',c.get('value','')):
            for n in nets:res.setdefault(n,set()).add(c['ref'])
    for n,refs in res.items():
        ic_input=any(p.get('net')==n and p.get('type')=='input' for c in components if not c['ref'].startswith('R') for p in c['pins'])
        rail=n in flags or n in currents or any(p.get('net')==n and p.get('type') in ('power_in','power_out') for c in components for p in c['pins'])
        if len(refs)>=2 and ic_input and n!='GND' and not rail:precision.add(n)
    return kelvin,precision-{'GND'},flags

def b2b_mate(n):
    """Contact of the other LSHM-DV half that meets contact n (W2 B2B). Samtec print LSHM-1XX-XX.X-XXX-DV-A-X-X-TR Rev Z note 4: when two
    LSHM-DV mate, pin 01 mates contact 02 of the mating connector. Both halves are the same part (odd contacts in one row, even contacts in
    the other, contacts 2k-1 and 2k at the same place along the strip), so the mating half is turned over about the strip axis and every
    column pairs the same way: n odd meets n+1, n even meets n-1. The map is its own inverse, so it holds from either board."""
    return n+1 if n%2 else n-1

B2B_RAIL_KINDS=('power','sense/supply tap','rail node')

def low_ohm_links(components,max_ohm):
    """W2 B2B review R2: nets that a resistor below max_ohm joins to a net other than GND, {net: 'Rref value to NET'} (lowest ref
    first). Such a node sits at the potential of the net it is joined to: the 0.22 ohm damper nodes (BIAS_CH1_DAMP: R232 from
    BIAS_CH1, C235 to GND) are rail nodes of b2b.guard_rule. A resistor to GND (a low-side shunt) does not count."""
    out={}
    for c in sorted(components,key=lambda c:sort_ref(c['ref'])):
        m=re.match(r'\s*(\d+(?:\.\d+)?)\s*(R|Ω|m)',c.get('value','')) if c.get('kind')=='resistor' else None
        if not m:continue
        nets=[p.get('net') for p in c['pins'] if p.get('net')]
        if float(m.group(1))*(1e-3 if m.group(2)=='m' else 1.0)>=max_ohm or len(set(nets))!=2 or 'GND' in nets:continue
        a,b=nets
        out.setdefault(a,f"{c['ref']} {c['value']} to {b}");out.setdefault(b,f"{c['ref']} {c['value']} to {a}")
    return out

def b2b_pairs(out,bb):
    """Declared sense pairs whose nets both cross (pcb/partition-spec.json b2b.declared_sense_pairs)."""
    return [pair['nets'] for pair in bb['declared_sense_pairs'] if all(any(r['net']==n for r in out) for n in pair['nets'])]

def b2b_guards(out,bb):
    """GND guard contacts of b2b.guard_rule: a GND column (2 contacts) beside each crossing declared sense pair, and one GND
    contact after the last rail column, in the row of that rail contact."""
    return 2*len(b2b_pairs(out,bb))+(1 if any(r['kind'] in B2B_RAIL_KINDS and r['pins'] for r in out) else 0)

def b2b_contacts(out,bb):
    """Contact map of the two B2B halves (W2 B2B, pcb/partition-spec.json b2b.pin_map_rule and b2b.guard_rule), J208 column c =
    contacts 2c-1 (odd row) and 2c (even row). Each declared sense pair takes one column at the end of the strip (the last
    column, the next pair two columns before it), with a GND guard column before it. From contact 1: the rail block, one column per
    rail contact (power: ceil(I/I_pin) per net; sense/supply taps; rail nodes) in the order b2b.rail_order, which lists the rail
    contacts column by column (a net listed once keeps all its contacts side by side; unlisted rails after it, by name), the
    rail contact on the odd row in odd columns and on the even row in even columns, its GND return in the other
    row of the same column (a checkerboard: every in-row neighbour of a rail contact is GND); one GND guard after the last rail
    contact in its row; the other nets in name order, one per column on the free even contacts in contact order (the even row of
    J208, the odd row of J209: on PWR-B the row that faces the harness headers); the rest spare (nc). The PWR-B half carries on
    contact m the net of PWR-A contact b2b_mate(m). Returns (map, fits)."""
    n_all=bb['contacts'];slots={};over=[]
    def put(pin,net,role):
        if 1<=pin<=n_all and pin not in slots:slots[pin]=(net,role)
        else:over.append(net)
    end=n_all//2
    for k,pair in enumerate(b2b_pairs(out,bb)):
        c=end-2*k
        put(2*c-1,pair[0],'sense pair');put(2*c,pair[1],'sense pair');put(2*c-3,'GND','guard');put(2*c-2,'GND','guard')
    col=1
    order=bb['rail_order'];last=None
    rails=[r for r in out if r['kind'] in B2B_RAIL_KINDS and r['pins']];kind={r['net']:r['kind'] for r in rails}
    left={r['net']:r['pins'] for r in rails};seq=[]
    for i,n in enumerate(order):
        if not left.get(n):continue
        k=1 if n in order[i+1:] else left[n];seq+=[n]*k;left[n]-=k
    for r in sorted(rails,key=lambda r:r['net']):seq+=[r['net']]*left[r['net']];left[r['net']]=0
    for net in seq:
        rail,gnd=(2*col-1,2*col) if col%2 else (2*col,2*col-1)
        put(rail,net,kind[net]);put(gnd,'GND','gnd');last=rail;col+=1
    if last is not None:put(last+2,'GND','guard')
    rest=[(r['net'],r['kind']) for r in out if r['kind'] not in B2B_RAIL_KINDS+('declared sense pair',) and r['pins']]
    free=[p for p in range(2,n_all+1,2) if p not in slots]
    fits=not over and len(rest)<=len(free)
    slots.update(zip(free,rest))
    return [{'pwr_a_pin':str(i),'pwr_b_pin':str(b2b_mate(i)),'net':slots.get(i,('','spare'))[0],'role':slots.get(i,('','spare'))[1]} for i in range(1,n_all+1)],fits

def b2b_nets(components,rows,currents):
    """Nets with pins on PWR-A and PWR-B bare board parts (W2 GR-3): the B2B net list by pcb/partition-spec.json b2b.rule. W2 B2B: the
    contact map of both halves (b2b_contacts), audited against the graph refs b2b.graph_refs, which are left out of the net list."""
    spec=json.loads(PARTITION_SPEC.read_text(encoding='utf-8'));bb=spec['b2b'];i_pin=spec['parameters']['b2b_i_pin_A']
    halves=bb['graph_refs'];b2b_refs=set(halves.values())
    side={r['ref']:('PWR_A' if r['board_candidate'] in PWR_A_DOMAINS else 'PWR_B') for r in rows
          if r['category']=='bare_board_part' and r['board_candidate'] in PWR_A_DOMAINS+PWR_B_DOMAINS and not r['dnp'] and r['ref'] not in b2b_refs}
    by_ref={c['ref']:c for c in components}
    pins=collections.defaultdict(lambda:collections.defaultdict(list))
    for ref,s in side.items():
        for n in sorted({p['net'] for p in by_ref[ref]['pins'] if p.get('net')}):pins[n][s].append(ref)
    cross={n:v for n,v in pins.items() if n!='GND' and len(v)==2}
    kelvin,precision,flags=sense_nets(components,currents)
    declared={n for pair in bb['declared_sense_pairs'] for n in pair['nets']}
    links=low_ohm_links(components,bb['rail_node_max_ohm'])
    extra=bb['net_current_extra'];out=[];errors=[]
    if bb['gnd_pins_per_power_contact']!=1:errors.append('b2b.guard_rule: the checkerboard has one GND contact beside each rail contact, so gnd_pins_per_power_contact must be 1')
    for n in sorted(cross):
        row={'net':n,'pwr_a':sorted(cross[n]['PWR_A'],key=sort_ref),'pwr_b':sorted(cross[n]['PWR_B'],key=sort_ref)}
        if n in declared:row.update(kind='declared sense pair',pins=1)
        elif n in bb['sense_taps']:row.update(kind='sense/supply tap',pins=1,gnd_pins=1,why=bb['sense_taps'][n])
        elif n in kelvin or n in precision:
            row.update(kind='Kelvin/precision (refused)',pins=None);errors.append(f'{n}: Kelvin/precision net crosses PWR-A/PWR-B and is not a declared sense pair')
        else:
            prot=currents.get(n)
            if prot is None and n in extra:prot=sum(currents[x] for x in extra[n]['sum_of'])
            power=prot is not None or n in flags or any(p.get('net')==n and p.get('type') in ('power_in','power_out') for r in cross[n]['PWR_A']+cross[n]['PWR_B'] for p in by_ref[r]['pins'])
            if power and prot is None:
                row.update(kind='power (no current)',pins=None);errors.append(f'{n}: power net crosses PWR-A/PWR-B without a protection current (tools/assembly_data.py NET_CURRENT)')
            elif power:
                n_pins=math.ceil(prot/i_pin-1e-9);row.update(kind='power',prot_A=round(prot,3),pins=n_pins,gnd_pins=n_pins*bb['gnd_pins_per_power_contact'])
            elif n in links:row.update(kind='rail node',pins=1,gnd_pins=1,why=links[n])
            else:row.update(kind='signal',pins=1)
        out.append(row)
    signal=sum(r['pins'] or 0 for r in out if r['kind']!='power');power=sum(r['pins'] for r in out if r['kind']=='power')
    guards=b2b_guards(out,bb);gnd=sum(r.get('gnd_pins',0) for r in out)+guards;need=signal+power+gnd;spare=math.ceil(need*(1+bb['spare_fraction'])-1e-9)
    contacts,placed=b2b_contacts(out,bb)
    if not placed:errors.append(f'B2B contact map: {need} contacts (with the sense pair and guard columns) exceed the {bb["contacts"]} contacts of the pair')
    # The graph refs carry the map pin for pin (design/E2.json) and sit on PWR-A and PWR-B.
    board_of={r['ref']:r['board_candidate'] for r in rows}
    for half,ref,doms in (('pwr_a',halves['pwr_a'],PWR_A_DOMAINS),('pwr_b',halves['pwr_b'],PWR_B_DOMAINS)):
        if ref not in by_ref:
            errors.append(f'{ref}: B2B half {half} is not a graph ref');continue
        if board_of.get(ref) not in doms:errors.append(f'{ref}: B2B half {half} has domain {board_of.get(ref)!r}, not one of {", ".join(doms)}')
        want={c[half+'_pin']:c['net'] for c in contacts}
        got={str(p['number']):p.get('net','') for p in by_ref[ref]['pins']}
        diff=[f'{ref}.{x} graph {got.get(x)!r} map {want.get(x)!r}' for x in sorted(set(want)|set(got),key=sort_ref) if got.get(x)!=want.get(x)]
        if diff:errors.append(f'{ref}: graph pins differ from the B2B contact map ({len(diff)}; rewrite J208/J209 from the map with '
                              f'python -I pcb/write_b2b_graph.py, then rerun the chain): '+'; '.join(diff[:6]))
    return {'schema':'srrx-b2b-nets-v1','status':'DESIGN INPUT (W2 GR-3, W2 B2B): nets with pins on PWR-A and PWR-B bare board parts of components.csv '
            '(the B2B halves themselves left out) and the contact map of both halves, which the graph refs carry pin for pin. Not a placement and not a measured current.',
            'generator':'pcb/prepare.py','rule':bb['rule'],'i_pin_A':i_pin,'i_pin_note':bb['i_pin_note'],'mpn':{k:bb['mpn'][k] for k in ('pwr_a','pwr_b','read')},
            'contacts_available':bb['contacts'],'pwr_a_domains':list(PWR_A_DOMAINS),'pwr_b_domains':list(PWR_B_DOMAINS),
            'totals':{'crossing_nets':len(out),'power_nets':sum(r['kind']=='power' for r in out),'power_pins':power,'signal_pins':signal,'gnd_pins':gnd,
                      'guard_pins':guards,'contacts_needed':need,'contacts_with_spare':spare,'fits':need<=bb['contacts'] and not errors,'meets_spare_rule':spare<=bb['contacts']},
            'nets':out,'graph_refs':halves,'footprint':bb['footprint'],'mating_map':bb['mating_map'],'pin_map_rule':bb['pin_map_rule'],
            'guard_rule':bb['guard_rule'],'rail_order':bb['rail_order'],'contacts':contacts,'errors':errors}

def board(c,cat):
    if cat!='bare_board_part':return ''
    s=c['_sheet'];ref=c['ref']
    if ref in DOMAIN_OVERRIDE:return DOMAIN_OVERRIDE[ref]
    if s!='E4':return {'E1':'PWR_MAIN','E2':'PWR_BRANCH','E3':'CTRL_HMI','E5':'USB_POWER'}[s]
    if c['group'].startswith('DC detectors'):
        return 'RF_INJECTOR' if ref in RF_TAP|RF_BLEED else 'DC_CORE'
    if ref in RF_PORT_BOARD:return RF_PORT_BOARD[ref]
    if ref in RELAY_REFS:return 'RF_HF'
    if ref in BIAS_REFS:return 'RF_INJECTOR'
    return 'RF_HMC'

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');args=ap.parse_args()
    components=[];sources=[];graph_paths=[];db=parts_db()
    for i in range(1,6):
        path=ROOT/f'design/E{i}.json';j=json.loads(path.read_text(encoding='utf-8'));graph_paths.append(path)
        sources.extend(j['sources']);flags=frozenset(f['net'] for f in j.get('power_flags',[]))
        for c in j['components']:components.append({**c,'_sheet':f'E{i}','_mount':db[c['ref']]['mount'] if c['ref'] in db else None,'_flags':flags})
    refs=[c['ref'] for c in components];require(len(refs)==len(set(refs)), 'Duplicate schematic reference');by_ref={c['ref']:c for c in components}
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
        issues.extend(interface_issues(c,cat,db,by_ref))
        if cat=='bare_board_part' and active and c.get('status')=='TBD':issues.append({'ref':ref,'type':'schematic_component_TBD','blocking':True,'detail':c['value']})
        row={'ref':ref,'sheet':c['_sheet'],'mount':c['_mount'] or '','value':c['value'],'kind':c['kind'],'category':cat,'assembly_owner':owner,'board_candidate':domain,'dnp':not active,'footprint':fp,'portable_footprint':portable,'pad_coverage':'PASS' if portable and not missing else 'UNASSIGNED' if not fp else 'FAIL','pin_count':len(pin_nums),'source':c.get('source',''),'classification_reason':why}
        rows.append(row)
        if domain=='DC_CORE':
            c={k:v for k,v in c.items() if k not in ('_mount','_flags')}
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
    summary={'status':'PREPARATION_ONLY_NOT_FOR_FABRICATION','components':len(rows),'schematic_contacts':sum(len(c['pins']) for c in components),'connected_contacts':len(all_nodes),'nets':len(net_nodes),'categories':dict(sorted(collections.Counter(r['category'] for r in rows).items())),'board_candidates':dict(sorted(collections.Counter(r['board_candidate'] for r in rows if r['board_candidate']).items())),'graph_assigned_footprints':sum(bool(r['footprint']) for r in rows),'portable_graph_assignments':sum(r['portable_footprint'] for r in rows),'bare_parts_without_footprint':sum(r['category']=='bare_board_part' and not r['footprint'] and not r['dnp'] for r in rows),'pin_pad_mismatches':sum(i['type']=='pin_pad_mismatch' for i in issues),'xml_connected_pin_audit':'PASS','xml_compared_connected_pins':len(all_nodes),'core_parts':len(core),'core_connected_pins':connected_core,'core_boundary_nets':len(boundary),'core_graph_assigned_footprints':sum(c['placement_footprint_status']=='graph_assigned_portable' for c in core),'core_proposed_footprints':sum(c['placement_footprint_status']!='graph_assigned_portable' for c in core),'blocking_issue_records':len(issues),'blocking_issue_types':dict(sorted(collections.Counter(i['type'] for i in issues).items()))}
    # DC_CORE provenance (embedded in detector-core-input.json, which the PCB re-freeze pins) names only the graphs, footprints
    # and XML; the parts-database projection is recorded in partition/provenance.json, so a parts.json edit outside these fields
    # does not force a re-freeze.
    core_provenance={'inputs':[{'file':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in graph_paths+[manifest_path,xml_path]],'source_documents':sorted({s['url'] for s in sources}),'generator':'pcb/prepare.py','note':'All classification/board splits are new controlled engineering proposals. They do not change E1..E5, claim module pin order, or authorize production.'}
    projection=json.dumps(parts_projection(db),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    b2b=b2b_nets(components,rows,net_currents())
    require(not b2b['errors'],'B2B rule: '+'; '.join(b2b['errors']))
    provenance={**core_provenance,'parts_database':{'file':PARTS_DB.relative_to(ROOT).as_posix(),'fields_used':list(PARTS_DB_FIELDS),'projection_sha256':hashlib.sha256(projection).hexdigest()},
                'partition':{'file':PARTITION_SPEC.relative_to(ROOT).as_posix(),'sha256':sha(PARTITION_SPEC),'b2b_currents':'tools/assembly_data.py NET_CURRENT'}}
    package={'summary':summary,'provenance':provenance,'boards':BOARDS,'constraints':CONSTRAINTS,'parts':rows,'unresolved':issues}
    proposed=summary['core_proposed_footprints']
    footprint_blocker=(f'{proposed} passive land patterns are placement proposals, not approved production MPN selections.' if proposed else
                       f'All {len(core)} core parts carry graph-assigned footprints and MPNs selected in design/parts/parts.json; a selected MPN is a procurement record, not a qualification: voltage/power/TCR/leakage ratings and land patterns still need review before production.')
    detector={'board_id':'DC_CORE','status':'UNROUTED_PLACEMENT_INPUT_NOT_FABRICATION','part_count':len(core),'components':core,'nets':{n:[x for x in net_nodes[n] if x['ref'] in core_refs] for n in sorted(core_nets)},'external_boundary':boundary,'must_remain_at_RF_port':sorted(RF_TAP|RF_BLEED,key=sort_ref),'constraints':[c for c in CONSTRAINTS if 'DC_CORE' in c['boards']],'blockers':[footprint_blocker,*(['Three explicitly0402 resistor footprints must be fetched from official KiCad if absent.'] if not (ROOT/'build/kicad/footprints/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod').is_file() else []),'Eight-net connector/wire-pad implementation, mounting/outline and cable routing are unselected.','RF-port tap/bleed assemblies are excluded from this core and must be placed on the RF substrate.','Prototype threshold/leakage/temperature/ground-offset/RF/rail-off tests remain mandatory.'],'source_node_audit':{'source_graph':'design/E4.json','actual_xml':'verification/netlist.xml','connected_pins_checked':connected_core,'status':'PASS','all_pins':sum(len(c['pins']) for c in core),'nc_pins':sum(bool(p.get('nc')) for c in core for p in c['pins'])},'provenance':core_provenance}
    files={'partition.json':dump(package),'components.csv':csv_text(rows,['ref','sheet','value','kind','mount','category','assembly_owner','board_candidate','dnp','footprint','portable_footprint','pad_coverage','pin_count','source','classification_reason']),'unresolved.csv':csv_text([{**i,'detail':json.dumps(i['detail'],ensure_ascii=False) if not isinstance(i['detail'],str) else i['detail']} for i in issues],['ref','type','blocking','detail']),'constraints.json':dump(CONSTRAINTS),'detector-core-input.json':dump(detector),'summary.json':dump(summary),'provenance.json':dump(provenance),'b2b-nets.json':dump(b2b),'detector-core-nodes.csv':csv_text([{'ref':c['ref'],'pin':p['number'],'name':p['name'],'net':p.get('net',''),'nc':p.get('nc',False),'placement_footprint':c['placement_footprint'],'footprint_status':c['placement_footprint_status']} for c in core for p in c['pins']],['ref','pin','name','net','nc','placement_footprint','footprint_status'])}
    if args.check:
        stale=[name for name,content in files.items() if not (OUT/name).exists() or (OUT/name).read_text(encoding='utf-8')!=content]
        require(not stale,'Stale generated output: '+', '.join(stale))
    else:
        OUT.mkdir(parents=True,exist_ok=True)
        for name,content in files.items():(OUT/name).write_text(content,encoding='utf-8',newline='\n')
    print(dump(summary),end='')

if __name__=='__main__': main()
