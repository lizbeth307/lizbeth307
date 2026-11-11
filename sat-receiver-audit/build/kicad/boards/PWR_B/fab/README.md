# Файли виробництва плати PWR_B

**NOT RELEASED: model/CI only; bench gates OPEN.** Це вихід CI/моделі (`pcb/fab_export.py` у `sr-rx-pcb`, KiCad 10.0.7), а не випуск для фабрики: статус специфікації — `MODEL_NOT_FOR_FABRICATION`; жодні апаратні чи стендові ворота цим не закриваються.

Каталог повністю генерує `python3 pcb/fab_export.py --board PWR_B`; вручну не редагувати. `--check` перегенеровує набір у тимчасовому каталозі й порівнює побайтово (KiCad ставить дати, абсолютні шляхи й рядок збірки — їх нормалізовано, правила в `manifest.json`), а також запускає `PWR_B.kicad_jobset` цього набору (ті самі байти, що в коміті; вихід — у `fab-jobset-raw` тимчасової копії плати) і порівнює його вихід із прямим експортом.

| Файл | Що це |
|---|---|
| `gerber/` | Gerber X2 (атрибути X2 і нетліста, розширення Protel), по файлу на шар; `.gbrjob` — файл завдання Gerber |
| `drill/` | Excellon: PTH і NPTH окремо (мм, десятковий формат, абсолютний початок, alternate для овальних) і карти свердлінь Gerber X2 |
| `PWR_B.ipc356` | нетліст IPC-D-356 для електротесту (усі кола з контактними майданчиками) |
| `assembly/PWR_B-bom-jlc.csv` | BOM для JLC PCBA: Comment, Designator, Footprint, LCSC Part # + кількості на плату й на партію |
| `assembly/PWR_B-cpl-jlc.csv` | CPL для JLC: Designator, Mid X, Mid Y (мм, початок посадкового місця KiCad), Layer (Top/Bottom), Rotation (сирий кут KiCad) |
| `assembly/PWR_B-cpl-rotation-offsets.csv` | таблиця поправок кута для JLC за посадковими місцями: порожня, TBD |
| `assembly/PWR_B-instances.csv` | відповідність шаблонних позначень плати позначенням графа для кожного екземпляра |
| `assembly/PWR_B-pos-kicad.csv` | сирий файл позицій KiCad (CSV, мм, обидва боки, без DNP) |
| `PWR_B-fab-notes.pdf` | примітки для фабрики: контур і отвори, шари й товщина, стек, імпеданс (лише RF), кількість |
| `PWR_B.kicad_jobset` | набір завдань KiCad 10.0.7 з тими самими параметрами експорту (для ручного відтворення) |
| `manifest.json` | sha256 кожного файла, хеші входів, команди, правила нормалізації, перевірки повноти |

## Замовлення

- Плат: 1 = екземпляри (PWRB ×1) + запасні 0; усі однакові й збираються однаково.
- Gerber і свердління: заархівувати `gerber/` і `drill/` разом під час замовлення (архів не комітиться, бо zip має мітки часу).
- Mid X / Mid Y у CPL — початок посадкового місця KiCad, тоді як JLC визначає їх як центр компонента (сторінка CPL JLC, прочитано 2026-11-07); кут — сирий кут KiCad. Поправки кута й центру для кожного посадкового місця — TBD, у CI не перевіряються: кожну деталь перевіряє той, хто замовляє, у переглядачі JLC перед оплатою (крок збирання; у build/21 його додає власник STEPS).
- Позиції BOM з TBD: B2B1, C274,C275,C276,C277,C283,C285,C287,C2911,C2912.
  - B2B1 (B2B placeholder: Samtec QTH-060-01-L-D-A pending): TBD: pilot_placeholder, no graph ref and no MPN yet; replaced by graph ref of the Samtec QTH-060-01-L-D-A (pcb/partition-spec.json b2b.mpn.pwr_b) once its land pattern is read and vendored (GR-4 / PCB-PWRA / PCB-PWRB lineage), keeping this pin map.
  - C274,C275,C276,C277,C283,C285,C287,C2911,C2912 (C1608X7R1H104K080AA): TBD: build/10-jlc-bom.csv row has no LCSC code.
- Заглушка `B2B1` (Connector_Hirose_FX8:Hirose_FX8-120P-SV_2x60_P0.6mm): її замінить graph ref of the Samtec QTH-060-01-L-D-A (pcb/partition-spec.json b2b.mpn.pwr_b) once its land pattern is read and vendored (GR-4 / PCB-PWRA / PCB-PWRB lineage), keeping this pin map; доти набір не для виробництва.

## Що цей набір не доводить (OPEN)

- that the schematic is right
- current capacity or temperature rise beyond the chosen class widths
- impedance, RF loss or isolation, EMC or signal integrity
- creepage beyond the encoded clearances
- that the enclosure fits (only outline and hole checks; heights are not checked here)
- that the fab's DFM accepts the board, or that CPL rotations are right
- that the land patterns match the purchased MPNs
- any function: hardware and bench gates stay OPEN

## Джерела (прочитано 2026-11-07)

- https://jlcpcb.com/help/article/bill-of-materials-for-pcb-assembly — required BOM columns Comment, Designator, Footprint; .csv/.xls/.xlsx; designators are upper-cased by JLC
- https://jlcpcb.com/help/article/pick-place-file-for-pcb-assembly — CPL columns Designator, Mid X, Mid Y (mm, component centroid), Layer (Top/Bottom), Rotation (degrees, positive counter-clockwise); the page names no coordinate origin and no rotation offsets
- https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad — BOM Comment, Designator, Footprint, LCSC Part #; KiCad pos Ref/PosX/PosY/Rot/Side become Designator/Mid X/Mid Y/Rotation/Layer
- https://jlcpcb.com/help/article/how-to-generate-gerber-and-drill-files-in-kicad-8 — layers F/B.Cu (+ inner), F/B.Paste, F/B.Silkscreen, F/B.Mask, Edge.Cuts; Protel extensions; subtract soldermask from silkscreen; drill: alternate oval mode, absolute origin, millimetres, decimal zeros, drill map recommended
- https://jlcpcb.com/capabilities/pcb-capabilities — FR-4; thickness 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm, tolerance +/-10 % for >= 1.0 mm; 2-layer outer copper 1/2/2.5/3.5/4.5 oz; impedance control listed from 4 layers, standard +/-10 %
- https://docs.kicad.org/10.0/en/cli/cli.html — options of pcb export gerbers/drill/ipcd356/pos and jobset run
- https://gitlab.com/kicad/code/kicad/-/tree/10.0.7/common/jobs — jobset JSON keys: job_export_pcb_plot.cpp, job_export_pcb_gerber(s).cpp, job_export_pcb_drill.cpp, job_export_pcb_pos.cpp, job_export_pcb_ipcd356.cpp, job.cpp, jobset.cpp, jobs_output_folder.cpp; Gerber header lines: pcbnew/pcbplot.cpp AddGerberX2Header, common/plotters/GERBER_plotter.cpp
- https://gitlab.com/kicad/code/kicad/-/blob/10.0.7/pcbnew/exporters/export_d356.cpp — IPC-D-356 signal names: the upper-cased sanitised net name when <= 14 characters and unique, otherwise an alias M + 4 base-36 digits declared as P NNAME with the case-kept name (last 58 characters); test record types 307/317/327/367
