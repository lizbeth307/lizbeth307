# Sheet graph interchange (root generates KiCad and exports)
Each agent owns E#.json and E#-review.md ONLY. JSON:
{
 "sheet":"E3", "title":"Ukrainian title", "sources":[{"url":"official URL","note":"what was verified"}],
 "notes":["sheet-level engineering notes"],
 "components":[
  {"ref":"U301","value":"MCP23017-E/SO","kind":"ic","group":"I2C expanders", "source":"STACK §5.2 + official URL", "status":"verified|design|module|TBD", "footprint":"optional verified KiCad footprint", "description":"optional", "notes":["..."],
   "pins":[{"number":"9","name":"VDD","net":"3V3_Q6A","type":"power_in"}, {"number":"1","name":"GPB0","net":"EN_LNB","type":"bidirectional"}, {"number":"14","name":"NC","nc":true,"type":"no_connect"}]
  }
 ],
 "open_items":[{"id":"E3-01","description":"...","blocking":true,"resolve":"exact measurement/doc needed","stack":"§5.2; §8.1 (UART7)","refs":["J301"]}],
 "drawing_notes":[{"id":"N-E3-01","refs":["R301"],"stack":"§5.2","text":"short visible note, e.g. why a value is TBD and which gate closes it"}],
 "decisions":[{"id":"R-E3-01","description":"engineering assignment chosen here, not originally verified hardware","source":"reason"}]
}
Every open item and drawing note needs `stack` (the STACK.md section and bench gate it rests on) and `refs` (parts on this sheet it concerns). The generator prints it as a framed note directly before the first of those parts, so it appears on the page that shows them; a missing `stack`, an unknown ref or a note that is not placed fails generation.
Values that STACK leaves open are written as `RILIM TBD (start 56.2k 1%)` / `OVLO TBD (start …)`: the drawing must not present a starting value as the specified one.
Reference designators: E1 100–199, E2 200–299, E3 300–399, E4 400–499 plus the documented DC-detector extension 4400–4499, E5 500–599. The generator rejects anything else.
Kinds: module, ic, connector, resistor, capacitor, inductor, diode, nfet, pfet, relay, fuse, switch, battery, net_tie, testpoint.
Allowed pin electrical types match KiCad: input, output, bidirectional, tri_state, passive, free, unspecified, power_in, power_out, open_collector, open_emitter, no_connect.
Every pin needs a unique number within its component. For commercial modules/cables where contact numbers are not documented: use meaningful logical identifiers e.g. VIN, GND, RF; status module, description explicitly says functional interface, no implied physical pin numbers; never assign arbitrary physical numbering.
Local standard two-pin passives numbers 1/2. Diode: choose physical package documented; if unsure module logical A/K. Fully list physical pins on ICs including NC and exposed pad. Do not silently omit decoupling/required bias parts. If cannot resolve, put a blocking open item.
Root renders net labels on stubs and electrically connects identical canonical nets. No unsupported pin strings such as GPx(TBD) shared between multiple nets. Leave unknown contacts unconnected or assign a justified DESIGN pinout if a new harness/unused GPIO is under our control; record decisions explicitly. Never call design choice verified existing hardware.
Canonical shared net names:
 GND, CHASSIS, 3V3_Q6A, LAB5, LNA4V5, J21, DISP12, AUX12, LNB13V2, BONI13V8, LIME3V3, VCC_3V3_MKEY, VCC_5V_PERI, AON3V3;
 I2C0_SDA,I2C0_SCL,I2C2_SDA,I2C2_SCL,I2CB_SDA,I2CB_SCL,MCP_INT,INA228_ALERT;
 EN_LABPORT,EN_AUX12,EN_RTLA,EN_RTLB,EN_HFP,EN_LNA1,EN_LNA2,EN_LNA3,EN_LNA4,EN_LNB,EN_BONI,EN_LIME3V3,EN_T7;
 FAULT_LABPORT,FAULT_RTLA,FAULT_RTLB,FAULT_HFP,FAULT_LNA1,FAULT_LNA2,FAULT_LNA3,FAULT_LNA4,FLT_LIME3V3,FLT_LNB,FLT_BONI,PG_LNB,PG_BONI;
 VBUS_RTLA,VBUS_RTLB,VBUS_HFP,VBUS_LABPORT;
 SW_RTLA_A,SW_RTLA_B,SW_RTLB_A,SW_RTLB_B,SW_LIME_A,SW_LIME_B,K1_ON,K2_ON;
 DCS_UHF,DCS_LBAND,DCS_HF,PTC_AUX,SLED_DET;
 UART5_TX,UART5_RX,UART6_TX,UART6_RX,UART7_TX,UART7_RX,IMU_TX,IMU_RX,PWR_ON_KEY,GNSS_ANT,SAFE_BOOT;
 RTLA_DM,RTLA_DP,RTLB_DM,RTLB_DP,HFP_DM,HFP_DP.
Own local nets: prefix sheet ID to avoid accidental global connections (e.g. E2_ILIM201). Canonical rail/control and intentional RF links shared names above unchanged. Flag any interface needing agreement to root.
Ownership E1 = pack/BMS/charge/main converters/AON/monitor; E2 = protected branches incl LNA1-4 current switches and RTL-B VBUS, LNB/Boni conditioning; E3 = Q6A 40pin/MCP/HMI/GNSS/control; E4 = RF paths + relay drivers, no duplicate LNA1-4 power switches; E5 = USB/VBUS RTLA/HFP/LABPORT/T7, external cable interfaces/display.
Receiver modules drawn once: E4 owns RF-facing RTL-A/B/HF+/Lime components with USB power/data exposed as canonical nets; E5 owns USB cabling and host/hub. Q6A use E3 40-pin connector + E5 ports functional connector blocks, not duplicate full SBC.
