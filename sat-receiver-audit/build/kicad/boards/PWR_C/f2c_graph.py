#!/usr/bin/env python3
"""W2 F2C-FALLBACK (GR-F2C): the graph edits of F2-C, the third power board PWR-C. Standard library only.

  python -I build/kicad/boards/PWR_C/f2c_graph.py          apply the edits to design/E1.json, E2.json and E5.json
  python -I build/kicad/boards/PWR_C/f2c_graph.py --check  exit 1 unless the graph already carries them

Gate G1 fired for PWR-A on 6 layers (build/15, W2 PWR-L6-ROUTE), so the synthesis fallback F2-C is adopted (W2 PWR-L6
synthesis, package F2C-FALLBACK; probe source origin/wip/w2-pwrj-f2c 23337c1a, build/kicad/boards/PWR_C/f2c_graph.py there).
What this script changes in the graph, and why:
- S06/S07 are deleted: the INA228 and the Pololu #2813 sit on PWR-C next to the battery front end, so their PWR-A signal
  headers J110 (X06S1) and J111 (X07S1) leave the graph.
- U102 becomes the bare INA228AIDGSR on PWR-C with its shunt R101 (Bourns CRA2512-FZ-R015ELF, read 2026-11-22) and its VS
  decoupling C101/C102 as board parts: the Adafruit 5832 breakout stood 10.1 mm with its terminal block, above the 6.5 mm
  height limit of PWR-C. U106 (#2813) is soldered flush onto a land of its 20 holes (SR_RX_Custom:Pololu_2813_psw03b).
  The MPN, manufacturer, LCSC and footprint fields come from design/parts/parts.json through tools/build_parts.py.
- The two Mini-Fit Jr. 2x1 headers of S06/S07 (same part 0039288020) become the PWR-A ends of harness S42 (W-C1, PWR-A
  <-> PWR-C): J107 contacts 1 GND, 2 E1_SW (E1_SW comes from the #2813 on PWR-C) and J106 contacts 1 GND, 2 LAB5 (the
  feed of the E5 IMU 5 V switch U553 and C552, which move to PWR-C). Both GND contacts carry the return of the PWR-A/PWR-B
  loads to the pack, which now enters at J105 on PWR-C. The PWR-C ends are the solder-wire lands J119 (GND, E1_SW; mate
  of J107) and J118 (GND, LAB5; mate of J106), 18 AWG.
- The E1/E5 signals of the moved groups leave S02 on PWR-B: J202.1 CHG_INHIBIT, J202.2 E1_BAT_ADC, J203.8/.9 I2C0,
  J203.10/.11 IMU_RX/TX, J203.12 INA228_ALERT, J203.17 PICO_OFF and J203.19 PWR_BUTTON become reserve contacts. They run
  PWR-C <-> CTRL on harness branch S02C (W-C2) from J120 (JST PHD 2x5 side entry) to the same CTRL contacts J306/J307,
  so design/E3.json is unchanged. They no longer cross the B2B: pcb/write_b2b_graph.py and pcb/prepare.py follow.
- PWR-C takes parts of 6.5 mm or less: the JST PH headers that move there (J109, J112, J113, J507) become side entry
  (S2B/S4B-PH-K-S, as on CTRL), and the Mini-Fit / Micro-Fit headers J105, J108, J114, J115 (12.8 / 9.9 mm) become
  KiCad 10.0.7 Connector_Wire SolderWire-1sqmm lands for 18 AWG wire (J108 loses its reserve contact 4: 1x03).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
E1 = ROOT / 'design/E1.json'
E2 = ROOT / 'design/E2.json'
E5 = ROOT / 'design/E5.json'
TAG = 'W2 F2C-FALLBACK (GR-F2C)'
SRC = 'W2 F2C-FALLBACK (GR-F2C): build/kicad/boards/PWR_C/f2c_graph.py; tools/assembly_data.py HEADERS'
DELETE = ('J110', 'J111')
S02_OFF = {'J202': ('1', '2'), 'J203': ('8', '9', '10', '11', '12', '17', '19')}
GROUP_HDR = "Роз'єми джгутів PWR"


def pin(number, net, name=None):
    if net is None:
        return {'number': number, 'name': 'NC', 'type': 'passive', 'nc': True}
    return {'number': number, 'name': name or net, 'type': 'passive', 'net': net}


WIRE_NOTE = ('Мідний майданчик під провід (W2 F2C-FALLBACK, GR-F2C) на PWR-C, купувати нічого: PWR-C бере деталі до 6.5 мм, а '
             'вертикальні Mini-Fit Jr. / Micro-Fit стоять 12.8 / 9.9 мм. Провід до 18 AWG (Alpha Wire 5857: 19/30, жила 1.27 мм) '
             'паяється в отвір посадкового місця KiCad 10.0.7 SolderWire 1 мм² (D 1.4 мм, отвір 1.75 мм, крок 5.4 мм); номери '
             'контактів = контакти джгута (tools/assembly_data.py HEADERS).')
# ref -> (value, pins or None to keep, note)
E1_HEADERS = {
    'J105': ('X05C1-PWRC: майданчики проводів 18 AWG, S05', None, WIRE_NOTE + ' S05 від майданчика J117 носійної плати PACK_FUSE.'),
    'J108': ('X10C1-PWRC: майданчики проводів 18 AWG, S10', [pin('1', 'GND'), pin('2', 'E1_N'), pin('3', 'E1_USB_PD_SAFE')],
             WIRE_NOTE + ' Резервний контакт 4 вилки Mini-Fit Jr. 2×2 знято (лунка 1×03).'),
    'J114': ('X11C1-PWRC: майданчики проводів 18 AWG, S11', None, WIRE_NOTE),
    'J115': ('X12C1-PWRC: майданчики проводів 18 AWG, S12', None, WIRE_NOTE),
    'J109': ('X05S1-PWRC: JST PH 2, бічний вхід, S05', None, None),
    'J112': ('X10S1-PWRC: JST PH 4, бічний вхід, S10', None, None),
    'J113': ('X11S1-PWRC: JST PH 2, бічний вхід, S11', None, None),
    'J107': ('X42J1-PWR: Molex Mini-Fit Jr. 2×1, верхній вхід, S42 (W-C1, E1_SW)', [pin('1', 'GND'), pin('2', 'E1_SW')],
             f'{TAG}: кінець PWR-A джгута S42 (W-C1) до PWR-C: E1_SW з #2813 U106 на PWR-C (раніше S07 до задньої стінки); '
             'контакти 1 GND, 2 E1_SW; GND несе повернення навантажень PWR-A/PWR-B до паку (вхід S05 тепер на PWR-C, J105).'),
    'J106': ('X42J2-PWR: Molex Mini-Fit Jr. 2×1, верхній вхід, S42 (W-C1, LAB5)', [pin('1', 'GND'), pin('2', 'LAB5')],
             f'{TAG}: кінець PWR-A джгута S42 (W-C1) до PWR-C: LAB5 за запобіжником F102 4 A для U553/C552 (група E5 «Сервіс і '
             'зовнішні шини» на PWR-C); контакти 1 GND, 2 LAB5.'),
}
SIDE_NOTE = (f'{TAG}: роз’єм стоїть на PWR-C (деталі до 6.5 мм), тому бічний вхід JST PH S*B-PH-K-S замість вертикального '
             'B*B (з розеткою 8.0 мм).')
NEW_E1 = [
    # J118 pairs with J106 and J119 with J107 (tools/build_assembly_docs.py pairs the S42 GND wires by ref order: J106.1 - J118.1,
    # J107.1 - J119.1), so each Mini-Fit Jr. 2x1 housing of W-C1 lands on one 2-land site of PWR-C, feed and return together
    {'ref': 'J118', 'value': 'X42C2-PWRC: майданчики проводів 18 AWG, S42 (W-C1, LAB5)', 'kind': 'connector', 'group': GROUP_HDR,
     'source': SRC, 'status': 'design', 'pins': [pin('1', 'GND'), pin('2', 'LAB5')],
     'notes': [WIRE_NOTE + ' Кінець PWR-C джгута S42 (W-C1) від J106 на PWR-A: LAB5 для U553/C552 і повернення GND (пара J106 ↔ J118).']},
    {'ref': 'J119', 'value': 'X42C1-PWRC: майданчики проводів 18 AWG, S42 (W-C1, E1_SW)', 'kind': 'connector', 'group': GROUP_HDR,
     'source': SRC, 'status': 'design', 'pins': [pin('1', 'GND'), pin('2', 'E1_SW')],
     'notes': [WIRE_NOTE + ' Кінець PWR-C джгута S42 (W-C1) до J107 на PWR-A: E1_SW з VOUT #2813 U106 і повернення GND (пара J107 ↔ J119).']},
    {'ref': 'J120', 'value': 'S02C-PWRC-SIG: JST PHD 2×5, боковий вхід, S02C (W-C2)', 'kind': 'connector', 'group': GROUP_HDR,
     'source': SRC, 'status': 'design',
     'pins': [pin('1', 'I2C0_SCL'), pin('2', 'I2C0_SDA'), pin('3', 'INA228_ALERT'), pin('4', 'IMU_RX'), pin('5', 'IMU_TX'),
              pin('6', 'E1_BAT_ADC'), pin('7', 'CHG_INHIBIT'), pin('8', 'PICO_OFF'), pin('9', 'PWR_BUTTON'), pin('10', None)],
     'notes': [f'{TAG}: кінець PWR-C гілки S02C (W-C2) джгута S02: 9 сигналів E1/E5 груп на PWR-C до тих самих контактів '
               'J306.1/.2 і J307.8–12/.17/.19 на CTRL, що й раніше через PWR-B J202/J203 (E3 не змінюється). Контакт 10 — резерв. '
               'GND у гілці немає: на J306/J307 вільного контакту немає (як у S02B), повернення — через GND S02 і S42 (OPEN: '
               'огляд шляху повернення).']},
]
U102_NOTES = [
    f'{TAG}: мікросхема INA228AIDGSR стоїть на PWR-C поруч із шунтом R101 (раніше — деталь модуля Adafruit 5832 на задній '
    'стінці з джгутом S06, який видалено). A0/A1 на GND задають адресу 0x40. VS (AON3V3) — з C101 100 нФ і C102 10 мкФ біля '
    'виводу 6. IN+/IN− — лінії Кельвіна від внутрішніх країв майданчиків R101; VBUS — з батарейного боку шунта (E1_SHUNT_P).',
    'SHUNT_CAL калібрувати на 0.5/2/4 A; ADCRANGE=0; continuous CHARGE/ENERGY. Драйвер ina238 не прив’язувати.',
    'TI DGS0010A має JEDEC MO-187 BA, 3×3 mm, pitch 0.5 mm. Реальний стандартний KiCad MSOP-10 ID обрано замість неіснуючого '
    'VSSOP-10 ID. Bundled KiCad 10.0.7 має IPC pads 1.5×0.35 mm / centers 4.2 mm; TI example 1.45×0.3 mm / centers 4.4 mm. Це '
    'альтернативний land pattern; до випуску перевірити toe/heel та технологію пайки.',
]
R101_NOTES = [
    f'{TAG}: шунт на PWR-C замість R1 модуля Adafruit 5832. Bourns CRA2512-FZ-R015ELF: 15 мОм ±1 %, ±50 ppm/°C, 3 Вт при '
    '70 °C зі зниженням до нуля при 170 °C, корпус 6.40 × 3.20 × 0.90 мм (даташит CRA2512 REV. 07/26, '
    'https://www.bourns.com/docs/product-datasheets/cra.pdf, прочитано 2026-11-22). При 4.6 A: 69 мВ і 0.317 Вт; при 7.5 A: '
    '0.844 Вт (MODEL). Кельвін-вимір: IN+/IN− від внутрішніх країв майданчиків. Рекомендований майданчик Bourns (A 4.0, B 2.1, '
    'L 4.1 мм) проти KiCad R_2512_6332Metric — перевірити до випуску (OPEN).',
]
CAP_NOTE = f'{TAG}: розв’язка VS U102 на PWR-C біля виводу 6 (номінали C1/C2 модуля Adafruit 5832, що їх тут замінено).'
U106_NOTE = (f'{TAG}: модуль лежить урівень на PWR-C (зазор ≤1 мм, MODEL: 1.0 + 1.57 + 2.4 = 4.97 мм проти межі 6.5 мм) на '
             'штирях 0.1 in обох рядів (16 отворів ⌀1.02) і з’єднаний з платою також у великих отворах VIN/GND/GND/VOUT '
             '(4 × ⌀2.18, крок 5.00) перемичками 18 AWG: Pololu радить для струму понад 5 A великі отвори або обидва отвори '
             '0.1 in на вузол (https://www.pololu.com/product/2813, прочитано 2026-11-22), тут — обидва. Отвори за кресленням '
             'psw03b (12.01.2016, https://www.pololu.com/file/0J1102/big-pushbutton-power-switch-with-reverse-voltage-protection-'
             'dimension-diagram.pdf, прочитано 2026-11-22; вигляд знизу з підписами): ряд VIN — VIN, VIN, GND, GND, ON, OFF, CTRL, '
             'GND; ряд VOUT — VOUT, VOUT, GND, GND, B, A, A, GND; великі — VIN, GND, GND, VOUT. Допустимий струм штиря гребінки не '
             'прочитано — TBD.')
SHEET_NOTE_OLD = 'U102, R101, C101 і C102 є деталізацією наявного Adafruit #5832.'
SHEET_NOTE_NEW = (f'{TAG}: U102 (INA228AIDGSR), шунт R101, C101 і C102 — деталі плати PWR-C (F2-C), модуль Adafruit #5832 більше '
                  'не потрібен. A0/A1 з’єднано з GND для 0x40. Pololu #2813 U106 впаяно на майданчик PWR-C; S06/S07 видалено.')


def note(c, text):
    notes = c.setdefault('notes', [])
    if text not in notes:
        notes.append(text)


def text(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def apply(e1, e2, e5):
    e1['components'] = [c for c in e1['components'] if c['ref'] not in DELETE]
    c1 = {c['ref']: c for c in e1['components']}
    for ref, (value, pins, nt) in E1_HEADERS.items():
        c = c1[ref]
        c['value'] = value
        c['source'] = SRC
        if pins is not None:
            c['pins'] = pins
        if nt:
            c['notes'] = [nt]
        elif ref in ('J109', 'J112', 'J113'):
            note(c, SIDE_NOTE)
    have = {c['ref']: i for i, c in enumerate(e1['components'])}
    at = have['J115'] + 1
    for k, new in enumerate(NEW_E1):
        if new['ref'] in have:  # refs of an earlier run take the current definition in place (the fields that
            e1['components'][have[new['ref']]].update(json.loads(json.dumps(new)))  # tools/build_parts.py writes stay)
        else:
            e1['components'].insert(at + k, json.loads(json.dumps(new)))
    u102 = c1['U102']
    u102.update({'value': 'INA228AIDGSR', 'status': 'design', 'notes': list(U102_NOTES)})
    r101 = c1['R101']
    r101.update({'value': '15 mΩ 1% 3 W 2512 (Bourns CRA2512-FZ-R015ELF)', 'status': 'design',
                 'source': 'https://www.bourns.com/docs/product-datasheets/cra.pdf', 'notes': list(R101_NOTES)})
    for ref, value in (('C101', '100nF X7R 10V (VS U102)'), ('C102', '10uF X7R 10V (VS U102)')):
        c1[ref].update({'value': value, 'status': 'design', 'source': 'https://www.ti.com/lit/ds/symlink/ina228.pdf; ' + TAG,
                        'notes': [CAP_NOTE]})
    u106 = c1['U106']
    u106['value'] = 'Pololu #2813 (Big Pushbutton Power Switch HP) на майданчику PWR-C'
    note(u106, U106_NOTE)
    e1['notes'] = [SHEET_NOTE_NEW if n.startswith(SHEET_NOTE_OLD) else n for n in e1['notes']]
    j507 = next(c for c in e5['components'] if c['ref'] == 'J507')
    j507['value'] = 'X32S1-PWRC: JST PH 4, бічний вхід, S32'
    j507['source'] = SRC
    note(j507, SIDE_NOTE)
    c2 = {c['ref']: c for c in e2['components']}
    for ref, nums in S02_OFF.items():
        c = c2[ref]
        c['pins'] = [pin(p['number'], None) if p['number'] in nums else p for p in c['pins']]
        note(c, f'{TAG}: сигнали E1/E5 груп на PWR-C (контакти {", ".join(nums)}) виходять з S02: вони йдуть PWR-C ↔ CTRL '
                f'гілкою S02C (W-C2, J120) до тих самих контактів J306/J307; тут ці контакти — резерв.')


def main(argv):
    check = '--check' in argv
    e1 = json.loads(E1.read_text(encoding='utf-8'))
    e2 = json.loads(E2.read_text(encoding='utf-8'))
    e5 = json.loads(E5.read_text(encoding='utf-8'))
    old = (text(e1), text(e2), text(e5))
    apply(e1, e2, e5)
    new = (text(e1), text(e2), text(e5))
    if check:
        ok = new == old
        print('f2c_graph:', 'graph carries the F2-C edits' if ok else 'graph lacks the F2-C edits')
        return 0 if ok else 1
    for path, body in zip((E1, E2, E5), new):
        path.write_text(body, encoding='utf-8', newline='\n')
    print('f2c_graph: wrote design/E1.json, design/E2.json and design/E5.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
