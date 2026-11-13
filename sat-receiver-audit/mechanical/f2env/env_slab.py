#!/usr/bin/env python3
"""F2-ENV probe transform (W2 PWRJ F2ENV): a slab of E mm between the battery tray and the plate (standard library).

Everything above the cut line Y_C (enclosure mm) moves up by E as one rigid block, with the HDMI chain of the right column
(Q6A clip, rear run, ferrite, rise, front-up, insert, plate notch) and the BMS that spans the cut. What stays: the
battery tray and pack, the bottom-face ports and intake, the bottom-edge closure bosses, the front vent V2 over the tray,
the rear-face GX16 and T7 holder, and the pack-positive group beside the tray end (pack fuse carrier and board, its two
standoffs, NTC, plate extension with its two mount bosses and slot SL3). The plate keeps its lower edge on the tray rib
and grows down by E. PWR-A and PWR-B keep the board frame of the L and grow down by E: outline (0,-E)-(136,-E)-(136,35)-
(42,35)-(42,110)-(0,110), so their place.origin moves up by E while the lower-left corner stays at enclosure (6, 38.5);
the PCB probe moves the bottom header row down to the new bottom edge (it stays where it is in the enclosure). CTRL, RF
and ENC move rigidly (+E, outlines unchanged).

  python -I mechanical/f2env/env_slab.py <sat-receiver-audit dir> [--e 30]   (on the SHRINK-2 params; the notes are added by hand)

Rewrites mechanical/params/mechanical.json and boards.json in place, number for number (the formatting of the files is
kept); MODEL inputs of the probe only.
"""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jpatch  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('root', type=Path)
ap.add_argument('--e', type=float, default=30.0)
a = ap.parse_args()
E = a.e
Y_C = 38.25        # cut line: battery tray top 37.95, plate lower edge 38.5
STAY_ITEMS = {'battery_tray', 'battery_pack', 'gx16', 'pack_fuse', 'pack_fuse_board', 'ntc_case'}
MOVE_LOW = {'hdmi_fpc_q6a', 'hdmi_route_rear', 'hdmi_ferrite', 'hdmi_route_rise', 'hdmi_route_front_up'}  # HDMI chain

mp = a.root / 'mechanical/params/mechanical.json'
bp = a.root / 'mechanical/params/boards.json'
mtext = mp.read_text(encoding='utf-8')
btext = bp.read_text(encoding='utf-8')
fe = lambda v: f'{v:g}'  # noqa: E731
# structural edits of boards.json (PWR and PWR_B carry the same L lines): the band grows down by E, two more F45 holes
OL = '"outline": [[0, 0], [136, 0], [136, 35], [42, 35], [42, 110], [0, 110]]'
RC = '"rects": [[0, 0, 136, 35], [0, 35, 42, 75]]'
HO = '"holes": [[4, 6], [132, 6], [132, 31], [46, 31], [4, 106], [38, 106], [38, 56]]'
assert btext.count(OL) == 2 and btext.count(RC) == 2 and btext.count(HO) == 2
btext = btext.replace(OL, f'"outline": [[0, {fe(-E)}], [136, {fe(-E)}], [136, 35], [42, 35], [42, 110], [0, 110]]')
btext = btext.replace(RC, f'"rects": [[0, {fe(-E)}, 136, {fe(35 + E)}], [0, 35, 42, 75]]')
btext = btext.replace(HO, HO[:-1] + f', [4, {fe(-E + 6)}], [132, {fe(-E + 6)}]]')
m = json.loads(mtext)
b = json.loads(btext)
if '_growth_w2_pwrj_f2env' in m['outer']:
    raise SystemExit('env_slab: mechanical.json already carries the F2ENV slab (outer._growth_w2_pwrj_f2env)')
log = []


def r(v):
    return round(v, 4)


def up(v):
    return r(v + E)


m['outer']['h'] = up(m['outer']['h'])
gp = m['display']['glass_pocket']
gp[1] = up(gp[1])
for p in m['display']['clamp_bosses']:
    p[1] = up(p[1])
for enc in m['hmi']['encoders'].values():
    enc['c'][1] = up(enc['c'][1])
m['hmi']['buttons']['rows_y'] = [up(v) for v in m['hmi']['buttons']['rows_y']]   # the whole HMI column moves with CTRL
for k in ('status_led', 'piezo_port'):
    m['front_face_small'][k]['c'][1] = up(m['front_face_small'][k]['c'][1])
m['top_face']['hood_hinge']['axis_y'] = up(m['top_face']['hood_hinge']['axis_y'])
for grp in ('ports', 'panel'):
    for p in m['right_face'].get(grp, []):
        p['y'] = up(p['y'])
m['left_face']['exhaust']['y'] = [up(v) for v in m['left_face']['exhaust']['y']]
rf = m['rear_face']
rf['tripod']['c'][1] = up(rf['tripod']['c'][1])
rf['hatch']['rect'][1] = up(rf['hatch']['rect'][1])
for p in rf['hatch']['screws']:
    p[1] = up(p[1])
if 'f101_access' in rf['hatch']:
    rf['hatch']['f101_access']['place'][1] = up(rf['hatch']['f101_access']['place'][1])
for k in ('path1_intake', 'path1_exhaust'):
    rf[k]['rect'][1] = up(rf[k]['rect'][1])
for p in rf['strap_lugs']:
    p[1] = up(p[1])
rf['strap_slots']['y'] = [up(v) for v in rf['strap_slots']['y']]
rf['t7_gland']['c'][1] = up(rf['t7_gland']['c'][1])
for p in m['closure']['bosses']:
    if p[1] >= Y_C:
        p[1] = up(p[1])
pl = m['plate']
pl['main'][3] = up(pl['main'][3])            # lower edge stays on the tray rib
for mb in pl['mount_bosses']:
    if mb['c'][1] >= Y_C:
        mb['c'][1] = up(mb['c'][1])
    else:
        log.append(f'plate boss {mb["c"]} stays (plate extension)')
pl['riser_window'][1] = up(pl['riser_window'][1])
for q in pl.get('notches_right', []):        # HDMI FPC notch moves with the chain
    q[1] = up(q[1])
for q in pl.get('notches', []):
    q[1] = up(q[1])
for bpnt in pl['bond_points']:
    bpnt['c'][1] = up(bpnt['c'][1])
for sl in pl['slots']:
    if sl['rect'][1] >= Y_C:
        sl['rect'][1] = up(sl['rect'][1])
    else:
        log.append(f'slot {sl["id"]} stays {sl["rect"]}')
for it in m['layout']['items']:
    if 'box' not in it:
        continue
    bx = it['box']
    if it['id'] in STAY_ITEMS:
        log.append(f'stay {it["id"]} {bx}')
    elif bx[1] >= Y_C or it['id'] in MOVE_LOW or bx[1] + bx[4] > Y_C + 10:
        bx[1] = up(bx[1])
    else:
        log.append(f'NOT HANDLED {it["id"]} {bx}')
for mt in m['module_mounts']['mounts']:
    if mt['item'] in STAY_ITEMS:
        log.append(f'module mount of {mt["item"]} stays')
        continue
    if mt['on'] == 'top_wall':      # [x, z] coordinates in the top wall: only the seat plane y moves
        mt['seat_y'] = up(mt['seat_y'])
        continue
    for k in ('screws', 'rests', 'spigots', 'standoffs'):
        for p in mt.get(k, []):
            p[1] = up(p[1])
    for k in ('pad', 'pocket'):
        if k in mt:
            mt[k][1] = up(mt[k][1])
    if 'seat_y' in mt:
        mt['seat_y'] = up(mt['seat_y'])
m['rf_bay']['rect'][1] = up(m['rf_bay']['rect'][1])
m['angles']['right']['y'] = [up(v) for v in m['angles']['right']['y']]
m['angles']['right']['holes_y'] = [up(v) for v in m['angles']['right']['holes_y']]
m['lime_pedestal']['rect'][1] = up(m['lime_pedestal']['rect'][1])
m['fins']['y'] = [up(v) for v in m['fins']['y']]
m['q6a_mount']['origin'][1] = up(m['q6a_mount']['origin'][1])
for v in m['vents']:
    if 'y' in v and v['y'] >= Y_C:
        v['y'] = up(v['y'])
    elif 'y' in v:
        log.append(f'vent {v["id"]} stays at y {v["y"]}')
for seg in m['hdmi_route']['segments']:
    for pt in seg['points']:
        pt[1] = up(pt[1])

B = b['boards']
for bid in ('PWR', 'PWR_B', 'RF', 'CTRL'):
    B[bid]['place']['origin'][1] = up(B[bid]['place']['origin'][1])
for k, v in B['ENC']['place_at'].items():
    v[1] = up(v[1])
for bid in ('PWR', 'PWR_B'):
    for ez in B[bid]['edge_zones']:
        if ez['edge'] == 'right' and ez['span'] == [0, 35]:
            ez['span'] = [r(-E), 35]
mt_, nm = jpatch.patch(mtext, m)
bt_, nb = jpatch.patch(btext, b)
mp.write_bytes(mt_.encode('utf-8'))
bp.write_bytes(bt_.encode('utf-8'))
log.append(f'numbers changed: mechanical.json {nm}, boards.json {nb}')
print('\n'.join(log))
