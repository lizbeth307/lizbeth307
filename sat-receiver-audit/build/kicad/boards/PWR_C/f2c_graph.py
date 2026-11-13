#!/usr/bin/env python3
"""W2 PWRJ-F2C probe: the graph edits of the F2-C variant (PWR-C front-slab board). Standard library only.

  python -I build/kicad/boards/PWR_C/f2c_graph.py          apply the edits to design/E1.json, E2.json and E5.json
  python -I build/kicad/boards/PWR_C/f2c_graph.py --check  exit 1 unless the graph already carries them

What the probe changes in the graph, and why (pwr-decision fallback F2-C; PWR-C+R proposal W-C1/W-C2):
- S06/S07 are deleted: the INA228 5832 (U102) and the Pololu #2813 (U106) modules sit on PWR-C, next to the battery
  front end, so their PWR-A signal headers J110 (X06S1) and J111 (X07S1) are marked dnp.
- The two Mini-Fit Jr. 2x1 headers of S06/S07 (same part 0039288020, LCSC C490534) become the PWR-A ends of harness W-C1
  (PWR-A <-> PWR-C): J107 contacts 1 GND, 2 E1_SW (E1_SW now comes from the #2813 on PWR-C; it was S07 from the rear
  wall; pin 2 and the scripted E1_SW rise stay where they are), J106 contacts 1 GND, 2 LAB5 (the feed of the E5 IMU 5 V
  switch U553 and C552, which move to PWR-C; one Mini-Fit Jr. contact behind the 4 A F102 of LAB5).
- The E1/E5 signals of the moved groups leave S02 on PWR-B: J202.1 CHG_INHIBIT, J202.2 E1_BAT_ADC, J203.8/.9 I2C0,
  J203.10/.11 IMU_RX/TX, J203.12 INA228_ALERT, J203.17 PICO_OFF and J203.19 PWR_BUTTON become reserve contacts. They
  run PWR-C <-> CTRL on harness W-C2 (a PWR-C header, pilot placeholder on the PWR_C probe spec) to the same CTRL
  contacts J306/J307, so design/E3.json is unchanged. They no longer cross the B2B: run pcb/write_b2b_graph.py and
  pcb/prepare.py afterwards.
- The JST PH headers that move to PWR-C (J109, J112, J113, J507) become side entry (S2B/S4B-PH-K-S, footprints already
  in the project library, the PWR-B and CTRL parts): PWR-C takes parts of 6.5 mm or less, and a vertical PH header with
  its plug is 8.0 mm. The Mini-Fit Jr. / Micro-Fit headers J105, J108, J114, J115 keep their graph footprints in the
  probe (their solder-wire lands need new library footprints: OPEN for the GR package).
Probe only (never merged): the harness tables (tools/assembly_data.py HEADERS/SEGMENTS), parts.json refs, build/16 and
the CAD refreeze are not updated; a GR package does that if F2-C is adopted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
E1 = ROOT / 'design/E1.json'
E2 = ROOT / 'design/E2.json'
E5 = ROOT / 'design/E5.json'
TAG = 'W2 PWRJ-F2C probe'
DNP = ('J110', 'J111')
S02_OFF = {'J202': ('1', '2'), 'J203': ('8', '9', '10', '11', '12', '17', '19')}
W_C1 = {'J107': ([('1', 'GND'), ('2', 'E1_SW')], 'X07J1-PWR: Molex Mini-Fit Jr. 2×1, верхній вхід, W-C1 (E1_SW з PWR-C)'),
        'J106': ([('1', 'GND'), ('2', 'LAB5')], 'X06J1-PWR: Molex Mini-Fit Jr. 2×1, верхній вхід, W-C1 (LAB5 на PWR-C)')}
SIDE = {'J109': ('Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal', 'S2B-PH-K-S(LF)(SN)'),
        'J113': ('Connector_JST:JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal', 'S2B-PH-K-S(LF)(SN)'),
        'J112': ('Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal', 'S4B-PH-K-S(LF)(SN)'),
        'J507': ('Connector_JST:JST_PH_S4B-PH-K_1x04_P2.00mm_Horizontal', 'S4B-PH-K-S(LF)(SN)')}
NOTE_SIDE = (f'{TAG}: роз’єм стоїть на PWR-C (деталі до 6.5 мм), тому бічний вхід JST PH S*B-PH-K-S замість '
             'вертикального B*B (з вилкою 8.0 мм).')
NOTE_DNP = (f'{TAG}: S06/S07 видалено (F2-C): модулі INA228 5832 (U102) і Pololu #2813 (U106) стоять на PWR-C біля '
            'входу батареї, тож цей роз’єм не встановлюється (dnp).')
NOTE_WC1 = {'J107': f'{TAG}: кінець PWR-A джгута W-C1 до PWR-C: E1_SW з #2813 на PWR-C (раніше S07 із задньої стінки); '
                    'контакти 1 GND, 2 E1_SW.',
            'J106': f'{TAG}: кінець PWR-A джгута W-C1 до PWR-C: LAB5 для U553/C552 (група E5 «Сервіс і зовнішні шини» на '
                    'PWR-C) за запобіжником F102 4 A; контакти 1 GND, 2 LAB5.'}


def note(c, text):
    notes = c.setdefault('notes', [])
    if text not in notes:
        notes.append(text)


def text(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def apply(e1, e2, e5):
    c1 = {c['ref']: c for c in e1['components']}
    for ref in DNP:
        c1[ref]['dnp'] = True
        note(c1[ref], NOTE_DNP)
    for ref, (pins, value) in W_C1.items():
        j = c1[ref]
        j['value'] = value
        j['pins'] = [{'number': n, 'name': net, 'type': 'passive', 'net': net} for n, net in pins]
        note(j, NOTE_WC1[ref])
    c5 = {c['ref']: c for c in e5['components']}
    for ref, (fp, mpn) in SIDE.items():
        c = c1.get(ref) or c5[ref]
        c['footprint'], c['mpn'] = fp, mpn
        c.pop('lcsc', None)
        c['value'] = c['value'].replace('верхній вхід', 'бічний вхід')
        note(c, NOTE_SIDE)
    c2 = {c['ref']: c for c in e2['components']}
    for ref, pins in S02_OFF.items():
        for p in c2[ref]['pins']:
            if p['number'] in pins:
                number = p['number']
                p.clear()
                p.update({'number': number, 'name': 'NC', 'type': 'no_connect', 'nc': True})
        note(c2[ref], f'{TAG}: сигнали E1/E5 перенесених на PWR-C груп (контакти {", ".join(pins)}) виходять з S02: вони '
                      'йдуть PWR-C ↔ CTRL джгутом W-C2 до тих самих контактів J306/J307; тут ці контакти — резерв.')


def main(argv):
    check = '--check' in argv
    e1 = json.loads(E1.read_text(encoding='utf-8'))
    e2 = json.loads(E2.read_text(encoding='utf-8'))
    e5 = json.loads(E5.read_text(encoding='utf-8'))
    old1, old2, old5 = text(e1), text(e2), text(e5)
    apply(e1, e2, e5)
    new1, new2, new5 = text(e1), text(e2), text(e5)
    if check:
        ok = new1 == old1 and new2 == old2 and new5 == old5
        print('f2c_graph:', 'graph carries the F2-C edits' if ok else 'graph lacks the F2-C edits')
        return 0 if ok else 1
    E1.write_text(new1, encoding='utf-8', newline='\n')
    E2.write_text(new2, encoding='utf-8', newline='\n')
    E5.write_text(new5, encoding='utf-8', newline='\n')
    print('f2c_graph: wrote design/E1.json, design/E2.json and design/E5.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
