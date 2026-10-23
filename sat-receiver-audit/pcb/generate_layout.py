#!/usr/bin/env python3
"""Place the frozen detector-core input using real KiCad footprint candidates.

This creates an UNROUTED BOARD STARTER, never Gerbers or a production release.
Run using Python with KiCad 10's pcbnew module, or use --runtime-root for an
unpacked official Ubuntu KiCad runtime. No schematic or source graph is edited.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET

BASE = Path(__file__).resolve().parents[1]
BOARD_NAME = 'detector-core-placement'
OUTLINE = (20.0, 20.0, 145.0, 135.0)
STATUS = 'UNROUTED_PLACEMENT_STARTER_NOT_FOR_FABRICATION'
EXTRA_DRC_WARNINGS = ('missing_courtyard', 'track_not_centered_on_via',
                      'tuning_profile_track_geometries', 'footprint_filters_mismatch',
                      'footprint_type_mismatch')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data if isinstance(data, bytes) else data.encode('utf-8'))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def import_pymupdf():
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf  # PyMuPDF < 1.24.3 only has the legacy name
    return pymupdf


def prepend_search_path(env, key, entry):
    """Put entry first in a ':'-separated search path.

    An empty element in LD_LIBRARY_PATH or PYTHONPATH means the current
    directory, so an unset or empty old value must not leave a trailing ':'.
    """
    old = env.get(key)
    env[key] = entry + os.pathsep + old if old else entry


def trusted_directory(path):
    """Refuse a library/module directory that another local user could modify.

    The runtime is put on LD_LIBRARY_PATH and PYTHONPATH, so a writable
    directory there would let another account run code as this user. The
    directory itself must not be world-writable; its parents may be only if
    they are sticky (as /tmp is), and every level must belong to root or us.
    """
    uid = os.getuid()
    for level, part in enumerate((path, *path.parents)):
        info = part.stat()
        if not stat.S_ISDIR(info.st_mode):
            raise SystemExit(f'--runtime-root: {part} is not a directory')
        if info.st_uid not in (0, uid):
            raise SystemExit(f'Refusing --runtime-root: {part} belongs to uid {info.st_uid}, not root or this user')
        if info.st_mode & stat.S_IWOTH and (level == 0 or not info.st_mode & stat.S_ISVTX):
            raise SystemExit(f'Refusing --runtime-root: {part} is world-writable; use a private directory '
                             '(for example under $HOME, or mkdir -m 700 under /tmp)')


def runtime_environment(runtime_root, marker):
    """Environment that runs this script again on an unpacked KiCad runtime."""
    runtime = Path(runtime_root).resolve()
    libraries = runtime / 'usr/lib/x86_64-linux-gnu'
    modules = runtime / 'usr/lib/python3/dist-packages'
    for directory in (libraries, modules):
        trusted_directory(directory)
    env = dict(os.environ)
    prepend_search_path(env, 'LD_LIBRARY_PATH', str(libraries))
    prepend_search_path(env, 'PYTHONPATH', str(modules))
    env[marker] = '1'
    return env


def native_module(runtime_root):
    if runtime_root and not os.environ.get('SR_RX_PCB_RUNTIME_ACTIVE'):
        env = runtime_environment(runtime_root, 'SR_RX_PCB_RUNTIME_ACTIVE')
        os.execve(sys.executable, [sys.executable, str(Path(__file__).resolve()), *sys.argv[1:]], env)
    try:
        import pcbnew
    except ImportError as error:
        raise SystemExit('KiCad pcbnew is required. Use KiCad Python or --runtime-root PATH. ' + str(error))
    return pcbnew


def placement():
    # Deliberately generous first placement, not a routed/minimized board.
    result = {
        'D450': (30, 40), 'R4400': (37, 40), 'U458': (45, 40), 'C4400': (53, 40),
        'R4402': (30, 52), 'R4403': (37, 52), 'C4401': (44, 52),
        'R4404': (30, 61), 'R4405': (37, 61), 'C4402': (44, 61),
        'R4406': (30, 70), 'R4407': (37, 70), 'C4405': (44, 70),
        'R4408': (30, 79), 'R4409': (37, 79), 'C4406': (44, 79),
        'U456': (58, 70), 'C4403': (65, 70), 'C4416': (58, 65.5),
        'U457': (58, 85), 'C4404': (65, 85), 'C4417': (58, 80.5),
        'R4450': (55, 98), 'R4451': (55, 105), 'Q456': (63, 98),
        'R4452': (72, 98), 'R4453': (72, 105), 'Q457': (80, 98), 'R4401': (45, 94),
    }
    for index, start_y in enumerate((37, 67, 97)):
        u = 450 + index * 2
        r = 4420 + index * 10
        result.update({
            f'U{u}': (96, start_y), f'U{u+1}': (118, start_y),
            f'C{4410+index*2}': (96, start_y-4.5), f'C{4411+index*2}': (118, start_y-4.5),
            f'C{r+1}': (88, start_y+8), f'D{451+index}': (96, start_y+8),
            f'R{r+1}': (104, start_y+8), f'R{r+2}': (112, start_y+8),
            f'Q{450+index*2}': (96, start_y+16), f'Q{451+index*2}': (118, start_y+16),
            f'R{r+3}': (88, start_y+16), f'R{r+4}': (88, start_y+24),
            f'R{r+5}': (110, start_y+16), f'R{r+6}': (110, start_y+24),
        })
    return result


def add_text(pcb, board, value, xy, size=1.2, layer=None):
    item = pcb.PCB_TEXT(board)
    item.SetText(value)
    item.SetPosition(pcb.VECTOR2I(pcb.FromMM(xy[0]), pcb.FromMM(xy[1])))
    item.SetTextSize(pcb.VECTOR2I(pcb.FromMM(size), pcb.FromMM(size)))
    item.SetTextThickness(pcb.FromMM(0.15))
    item.SetLayer(pcb.F_SilkS if layer is None else layer)
    board.Add(item)


def create_board(pcb, source, out):
    board = pcb.BOARD()
    board.SetCopperLayerCount(2)
    block = pcb.TITLE_BLOCK()
    block.SetTitle('DC_CORE - UNROUTED PLACEMENT ONLY - NOT FOR FABRICATION')
    block.SetDate(date.today().isoformat())
    block.SetRevision('placement-candidate-1')
    block.SetComment(0, 'Outline and passives are unqualified candidates; no enclosure fit or production DRC.')
    board.SetTitleBlock(block)
    positions = placement()
    refs = {c['ref'] for c in source['components']}
    if refs & set(source['must_remain_at_RF_port']):
        raise ValueError('RF-port components leaked into DC core')
    if refs != set(positions):
        raise ValueError({'missing_positions': sorted(refs-set(positions)), 'unused_positions': sorted(set(positions)-refs)})
    netmap = {}
    for code, name in enumerate(sorted(source['nets']), 1):
        net = pcb.NETINFO_ITEM(board, name, code)
        board.Add(net)
        netmap[name] = net
    footprint_sources = []
    for comp in source['components']:
        ident = comp['placement_footprint']
        library, name = ident.split(':', 1)
        relative_file = comp.get('placement_footprint_file') or f'build/kicad/footprints/{library}.pretty/{name}.kicad_mod'
        path = BASE / relative_file
        if not path.is_file():
            raise FileNotFoundError(path)
        footprint = pcb.FootprintLoad(str(path.parent), name)
        if footprint is None:
            raise RuntimeError('KiCad could not load footprint: ' + ident)
        footprint.SetReference(comp['ref'])
        footprint.SetValue(comp['value'].strip())
        footprint.SetFPID(pcb.LIB_ID(library, name))
        x, y = positions[comp['ref']]
        footprint.SetPosition(pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y)))
        footprint.SetOrientationDegrees(0)
        # Keep the long value available on F.Fab, not over the physical pads.
        footprint.Value().SetVisible(False)
        footprint.Reference().SetTextSize(pcb.VECTOR2I(pcb.FromMM(0.8), pcb.FromMM(0.8)))
        footprint.Reference().SetTextThickness(pcb.FromMM(0.12))
        pins = {str(pin['number']): pin for pin in comp['pins']}
        found = set()
        for pad in footprint.Pads():
            number = str(pad.GetNumber())
            if not number:
                continue
            if number not in pins:
                raise ValueError(f'Footprint extra numbered pad: {comp["ref"]}.{number}')
            found.add(number)
            pin = pins[number]
            if pin.get('net'):
                pad.SetNet(netmap[pin['net']])
            elif pin.get('nc'):
                pad.SetNetCode(0)
            else:
                raise ValueError(f'Pin lacks net or NC: {comp["ref"]}.{number}')
            if hasattr(pad, 'SetPinFunction'):
                pad.SetPinFunction(pin.get('name', number))
            if hasattr(pad, 'SetPinType'):
                pad.SetPinType('no_connect' if pin.get('nc') else pin.get('type', 'passive'))
        if found != set(pins):
            raise ValueError(f'Unmapped source pins: {comp["ref"]}: {sorted(set(pins)-found)}')
        board.Add(footprint)
        footprint_sources.append(dict(ref=comp['ref'],footprint=ident,file=relative_file,sha256=digest(path),status=comp['placement_footprint_status']))
    x1, y1, x2, y2 = OUTLINE
    for a, b in [((x1,y1),(x2,y1)),((x2,y1),(x2,y2)),((x2,y2),(x1,y2)),((x1,y2),(x1,y1))]:
        edge = pcb.PCB_SHAPE(board)
        edge.SetShape(pcb.SHAPE_T_SEGMENT)
        edge.SetLayer(pcb.Edge_Cuts)
        edge.SetStart(pcb.VECTOR2I(pcb.FromMM(a[0]),pcb.FromMM(a[1])))
        edge.SetEnd(pcb.VECTOR2I(pcb.FromMM(b[0]),pcb.FromMM(b[1])))
        edge.SetWidth(pcb.FromMM(0.05))
        board.Add(edge)
    add_text(pcb,board,'DC CORE / UNROUTED / NOT FOR FABRICATION',(82.5,25),1.35)
    add_text(pcb,board,'50 PASSIVE FOOTPRINTS: UNQUALIFIED',(82.5,125),0.85)
    add_text(pcb,board,'CANDIDATE OUTLINE ONLY - NO ENCLOSURE FIT',(82.5,129),1.0)
    add_text(pcb,board,'REF / RETURN',(47,31),1.0)
    for name, yy in [('UHF DC',(29)),('LBAND DC',(59)),('HF DC',(89))]:
        add_text(pcb,board,name,(130,yy),0.9)
    add_text(pcb,board,'0 tracks / 0 vias / RF taps and bleeds stay at RF ports',(80,133),0.8,pcb.Cmts_User)
    path = out / (BOARD_NAME + '.kicad_pcb')
    with tempfile.TemporaryDirectory(prefix='sr-rx-board-') as temp:
        candidate = Path(temp) / path.name
        if not pcb.SaveBoard(str(candidate),board):
            raise RuntimeError('KiCad SaveBoard failed')
        # Native parser round-trip before atomic publication.
        if len(list(pcb.LoadBoard(str(candidate)).GetFootprints())) != source['part_count']:
            raise RuntimeError('Native board re-read part count mismatch')
        atomic_write(path,candidate.read_bytes())
    libraries = sorted({c['placement_footprint'].split(':',1)[0] for c in source['components']})
    table=['(fp_lib_table (version 7)']
    for lib in libraries:
        table.append(f'(lib (name "{lib}")(type "KiCad")(uri "${{KIPRJMOD}}/../footprints/{lib}.pretty")(options "")(descr "Official KiCad 10.0.7 placement candidates"))')
    table.append(')')
    atomic_write(out/'fp-lib-table','\n'.join(table)+'\n')
    atomic_write(out/(BOARD_NAME+'.kicad_pro'),json.dumps({'meta':{'filename':BOARD_NAME+'.kicad_pro','version':1},'board':{'design_settings':{'rule_severities':{key:'warning' for key in EXTRA_DRC_WARNINGS}}}},indent=2)+'\n')
    return path, footprint_sources


def audit(pcb, source, board_path):
    board=pcb.LoadBoard(str(board_path))
    actual={fp.GetReference():fp for fp in board.GetFootprints()}
    errors=[];nodes=[]
    expected_refs={c['ref'] for c in source['components']}
    if set(actual)!=expected_refs:
        errors.append(dict(kind='reference_set',missing=sorted(expected_refs-set(actual)),extra=sorted(set(actual)-expected_refs)))
    for comp in source['components']:
        fp=actual.get(comp['ref'])
        if fp is None:continue
        ident = str(fp.GetFPID().GetLibNickname()) + ':' + str(fp.GetFPID().GetLibItemName())
        if ident != comp['placement_footprint']:errors.append(dict(kind='footprint_id',ref=comp['ref'],expected=comp['placement_footprint'],observed=ident))
        if fp.GetValue().strip() != comp['value'].strip():errors.append(dict(kind='component_value',ref=comp['ref']))
        pads={}
        for pad in fp.Pads():
            if pad.GetNumber():pads.setdefault(str(pad.GetNumber()),[]).append(pad)
        expected={str(pin['number']):pin for pin in comp['pins']}
        if set(pads)!=set(expected):errors.append(dict(kind='pad_number_set',ref=comp['ref'],missing=sorted(set(expected)-set(pads)),extra=sorted(set(pads)-set(expected))))
        for num,pin in expected.items():
            observed=[p.GetNetname() for p in pads.get(num,[])]
            want=pin.get('net','')
            if len(observed)!=1 or observed[0]!=want:errors.append(dict(kind='pad_net',ref=comp['ref'],pin=num,expected=want,observed=observed))
            nodes.append(dict(ref=comp['ref'],pad=num,net=want,nc=bool(pin.get('nc')),position_mm=[pcb.ToMM(pads[num][0].GetPosition().x),pcb.ToMM(pads[num][0].GetPosition().y)] if num in pads else None))
    tracks=list(board.GetTracks());zones=list(board.Zones())
    if tracks or zones:errors.append(dict(kind='unexpected_copper',tracks_vias=len(tracks),zones=len(zones)))
    return dict(passed=not errors,status=STATUS,components=len(actual),source_pins=len(nodes),connected_pads=sum(not n['nc'] for n in nodes),nc_pads=sum(n['nc'] for n in nodes),net_count=len(source['nets']),external_boundary_nets=[n['net'] for n in source['external_boundary']],tracks_and_vias=len(tracks),copper_zones=len(zones),errors=errors,pad_assignments=nodes)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,default=BASE/'pcb/generated/detector-core-input.json')
    parser.add_argument('--output',type=Path,default=BASE/'build/kicad/pcb-preparation')
    parser.add_argument('--runtime-root',type=Path)
    parser.add_argument('--kicad-cli',default='kicad-cli')
    parser.add_argument('--check',action='store_true',help='Read-only source-pin-to-board-pad audit')
    args=parser.parse_args();pcb=native_module(args.runtime_root)
    source=json.loads(args.input.read_text(encoding='utf-8'));out=args.output.resolve()
    if source['source_node_audit']['status']!='PASS':raise SystemExit('Input source-node audit is not PASS')
    if source['part_count']!=71 or len(source['components'])!=71:raise SystemExit('This starter is frozen for71parts')
    if sum(len(c['pins']) for c in source['components'])!=187:raise SystemExit('Input pin count changed')
    board_path=out/(BOARD_NAME+'.kicad_pcb')
    if args.check:
        result=audit(pcb,source,board_path)
        stored_path=out/'placement-audit.json'
        if stored_path.is_file():
            stored=json.loads(stored_path.read_text(encoding='utf-8'))
            if stored.get('input_sha256')!=digest(args.input):result['errors'].append(dict(kind='input_snapshot_changed'))
            if stored.get('board_sha256')!=digest(board_path):result['errors'].append(dict(kind='board_snapshot_changed'))
            for entry in stored.get('footprint_sources',[]):
                if digest(BASE/entry['file'])!=entry['sha256']:result['errors'].append(dict(kind='footprint_resource_changed',file=entry['file']))
            result['passed']=not result['errors']
        print(json.dumps({k:v for k,v in result.items() if k!='pad_assignments'},ensure_ascii=False,indent=2))
        raise SystemExit(0 if result['passed'] else 1)
    out.mkdir(parents=True,exist_ok=True)
    board_path,footprints=create_board(pcb,source,out)
    result=audit(pcb,source,board_path)
    result.update(input_file=args.input.resolve().relative_to(BASE).as_posix(),input_sha256=digest(args.input),board_file=board_path.relative_to(BASE).as_posix(),board_sha256=digest(board_path),kicad_version=pcb.Version(),outline_candidate_mm={'x':OUTLINE[2]-OUTLINE[0],'y':OUTLINE[3]-OUTLINE[1],'production_qualified':False},footprint_sources=footprints,passive_land_patterns_proposed=sum(c['placement_footprint_status']=='proposed_not_production_qualified' for c in source['components']),boundary_implementation='Unselected: no invented connector/wire-pad numbers were added.',rf_exclusions=source['must_remain_at_RF_port'],constraints=source['constraints'],blockers=source['blockers'])
    result['resource_resolution']={'R_0402_1005Metric':'Resolved using unmodified official KiCad 10.0.7 resource; actual file paths and hashes are recorded in placement-audit.json. Passive production qualification remains open.','source_metadata_null_paths':sum(c.get('placement_footprint_file') is None for c in source['components']),'provenance_file':'build/kicad/pcb-preparation/footprint-provenance.json'}
    atomic_write(out/'placement-audit.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    review=BASE/'verification/pcb-review.json'
    atomic_write(review,json.dumps({k:v for k,v in result.items() if k not in ('pad_assignments','footprint_sources')},ensure_ascii=False,indent=2)+'\n')
    if not result['passed']:raise SystemExit('Source pad audit failed; see placement-audit.json')
    cli=shutil.which(args.kicad_cli) if not Path(args.kicad_cli).is_file() else args.kicad_cli
    if not cli:raise SystemExit('Board and pin audit written; KiCad CLI is required for raw DRC.')
    raw=out/'drc-raw.json'
    drc=subprocess.run([str(cli),'pcb','drc','--format','json','--severity-all','--all-track-errors','--exit-code-violations','--output',str(raw),str(board_path)],capture_output=True,text=True)
    atomic_write(out/'drc-command.log',drc.stdout+'\n'+drc.stderr)
    if not raw.is_file():raise SystemExit('KiCad DRC report not produced: '+drc.stderr)
    rawdoc=json.loads(raw.read_text(encoding='utf-8'));types=Counter(v.get('type','unknown') for key in ('violations','unconnected_items','schematic_parity') for v in rawdoc.get(key,[]))
    if drc.returncode not in (0,5):
        raise SystemExit('KiCad DRC failed to complete; raw output and log retained.')
    summary=dict(exit_code=drc.returncode,raw_file=raw.relative_to(BASE).as_posix(),raw_sha256=digest(raw),counts=dict(types),sections={key:len(rawdoc.get(key,[])) for key in ('violations','unconnected_items','schematic_parity')},ignored_checks=rawdoc.get('ignored_checks',[]),configuration='Five normally ignored KiCad categories explicitly enabled as warning in the candidate project.',additional_warning_categories=list(EXTRA_DRC_WARNINGS),suppressed_or_filtered=False,release_status='NOT_RELEASED_UNROUTED')
    result['drc']=summary
    atomic_write(out/'placement-audit.json',json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    atomic_write(review,json.dumps({k:v for k,v in result.items() if k not in ('pad_assignments','footprint_sources')},ensure_ascii=False,indent=2)+'\n')
    with tempfile.TemporaryDirectory(prefix='sr-rx-pcb-svg-') as temp:
        preview=Path(temp)/'placement.svg'
        export=subprocess.run([str(cli),'pcb','export','svg','--mode-single','--black-and-white','--layers','F.Cu,F.Silkscreen,Edge.Cuts','--page-size-mode','2','--exclude-drawing-sheet','--output',str(preview),str(board_path)],capture_output=True,text=True)
        atomic_write(out/'svg-command.log',export.stdout+'\n'+export.stderr)
        if export.returncode or not preview.is_file():raise SystemExit('KiCad SVG export failed')
        ET.fromstring(preview.read_bytes())
        atomic_write(out/(BOARD_NAME+'.svg'),preview.read_bytes())
    try:
        pymupdf=import_pymupdf()
        image_doc=pymupdf.open(out/(BOARD_NAME+'.svg'))
        atomic_write(out/(BOARD_NAME+'.png'),image_doc[0].get_pixmap(matrix=pymupdf.Matrix(3,3),alpha=False).tobytes('png'))
    except ImportError:
        pass # The native vector SVG remains available without optional PyMuPDF.
    provenance=dict(resource='build/kicad/footprints/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod',sha256=digest(BASE/'build/kicad/footprints/Resistor_SMD.pretty/R_0402_1005Metric.kicad_mod'),source='https://ppa.launchpadcontent.net/kicad/kicad-10.0-releases/ubuntu/pool/main/k/kicad-library-footprints/kicad-footprints_10.0.7~ubuntu24.04.1_all.deb',package_sha256='a1c25a690348180d572b73496668cffafdaecf284d6555279fa89d5e4fefa46c',license='build/kicad/footprints/LICENSE.md',content_modified=False,qualification='Placement candidate only, not approved MPN/land pattern')
    atomic_write(out/'footprint-provenance.json',json.dumps(provenance,indent=2)+'\n')
    print(json.dumps(dict(status=STATUS,source_pad_audit='PASS',parts=result['components'],pins=result['source_pins'],drc=summary),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
