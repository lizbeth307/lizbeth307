#!/usr/bin/env python3
"""Check independent contact-level contracts and the ideal HF relay network.

The relay calculation is a DC/ideal-contact topology test. It does not establish
RF insertion loss, impedance matching, contact bounce or isolation.
"""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def require(condition, *detail):
    # Explicit checks, not assert: python -O must never turn a failure into PASS.
    if not condition:
        raise SystemExit("Electrical invariant FAIL: " + repr(detail))


def main(base=BASE):
    out = base / "verification/electrical-invariants.json"
    # A failed run must not leave an earlier PASS report behind.
    out.unlink(missing_ok=True)
    raw = {p: p.read_bytes() for p in sorted((base / "design").glob("E[1-5].json"))}
    graphs = [json.loads(data.decode("utf-8")) for data in raw.values()]
    comps = {c["ref"]: c for g in graphs for c in g["components"]}
    def node(ref, pin):
        net = next(p.get("net") for p in comps[ref]["pins"] if str(p["number"]) == str(pin))
        require(net, "Invariant contact has no net", ref, pin)
        return net
    def members(net):
        return {(r, str(p["number"])) for r, c in comps.items() for p in c["pins"] if p.get("net") == net}
    # Locked reference: Radxa GPIO documentation, Daly protected/raw returns,
    # and Adafruit JP pad numbering. These are independent of page generation.
    header = {1:"3V3_Q6A",2:"VCC_5V_PERI",3:"INA228_ALERT",4:"VCC_5V_PERI",5:"MCP_INT",8:"UART5_TX",10:"UART5_RX",13:"I2C0_SDA",15:"I2C0_SCL",16:"UART6_TX",17:"3V3_Q6A",18:"UART6_RX",27:"I2C2_SDA",28:"I2C2_SCL",29:"UART7_RX",32:"UART7_TX",40:"SAFE_BOOT"}
    for pin, net in header.items():
        require(node("J301", pin) == net, "Radxa header", pin, node("J301", pin), net)
    require(node("J301", 7) == node("U304", "P1.5"), "LC76G PPS must reach Q6A pin7")
    require(node("U101", "B-") == node("U101", "B0") == "E1_CELL0", "Daly B-/B0")
    require(node("U101", "P-") == "GND", "Daly P-")
    require(node("U101", "B-") != node("U101", "P-"), "Daly B-/P- merged")
    # Raw cell negative: nothing else (no 0R, strap or balance lead) may bridge it.
    cell = {("BT101", "-"), ("U101", "B-"), ("U101", "B0"), ("J102", "B0")}
    require(members("E1_CELL0") == cell, "Raw cell negative membership", sorted(members("E1_CELL0")))
    require(comps["J102"].get("dnp"), "Unqualified external balance connector must remain DNP")
    # Watchdog reset must remain a MOS-isolated bridge between Pico and Q6A
    # domains. Firmware timing/heartbeat and loss of Pico power are not tested.
    require(node("U305", 22) == node("R393", 1) == node("R395", 2), "Pico reset bridge")
    require(node("U305", 36) == node("R395", 1), "Pico reset pull")
    require(node("R393", 2) == node("Q306", 1) == node("R394", 1), "Q306 gate")
    require(node("Q306", 2) == node("R394", 2) == "GND", "Q306 source")
    require({node(ref, 18) for ref in ("U301", "U302", "U303")} == {node("Q306", 3)}, "MCP RESET drain")
    # OVP node is a clampable safe-enable signal, not a pulled-up fault input:
    # TPS3701 OUTB drives U212 EN/UVLO, R291 from EN_LNB and R292 to GND only.
    ovp = {("U212", "3"), ("U220", "6"), ("R291", "2"), ("R292", "1"), ("TP215", "1"), ("U303", "6")}
    require(members("OVP_LNB_N") == ovp, "OVP_LNB_N membership", sorted(members("OVP_LNB_N")))
    require(node("R291", 1) == "EN_LNB" and node("R292", 2) == "GND", "OVP divider ends")
    relay_results = []
    ports = {"HF": "E4_HF_BT", "VHF": "E4_P6", "HFP": "E4_HFP_ANT"}
    terminations = ["R417", "R418", "R419"]
    for k1, k2 in [(0,0),(1,0),(0,1)]:
        parents = {}
        def find(x):
            parents.setdefault(x,x)
            if parents[x] != x:
                parents[x] = find(parents[x])
            return parents[x]
        def union(a,b):
            parents[find(a)] = find(b)
        # Omron contact map, independent of the drawing's geometric layout.
        for ref,on in [("K401",k1),("K402",k2)]:
            union(node(ref,3),node(ref,4 if on else 2))
            union(node(ref,6),node(ref,5 if on else 7))
        effective = {}
        for port,net in ports.items():
            loads = []
            for ref in terminations:
                ns = [node(ref, p["number"]) for p in comps[ref]["pins"]]
                signal = next(n for n in ns if n != "GND")
                if find(signal) == find(net):
                    loads.append(ref)
            effective[port] = loads
        if (k1,k2) == (0,0):
            require(effective == {"HF":["R417"],"VHF":["R418"],"HFP":["R419"]}, effective)
            require(len({find(n) for n in ports.values()}) == 3, "relay 00 ports merged")
        elif k1:
            require(find(ports["HFP"]) == find(ports["HF"]), "relay 10 HFP-HF")
            require(find(ports["HFP"]) != find(ports["VHF"]), "relay 10 HFP-VHF")
            require(effective["HFP"] == [] and effective["VHF"] == ["R418"], effective)
        else:
            require(find(ports["HFP"]) == find(ports["VHF"]), "relay 01 HFP-VHF")
            require(find(ports["HFP"]) != find(ports["HF"]), "relay 01 HFP-HF")
            require(effective["HFP"] == [] and effective["HF"] == ["R417"], effective)
        relay_results.append({"K1":k1,"K2":k2,"terminations":effective})
    report = {"status":"PASS","input_sha256":{p.relative_to(base).as_posix(): hashlib.sha256(data).hexdigest() for p, data in raw.items()},"radxa_gpio_contract":"PASS","raw_battery_negative_isolated_from_protected_return":"PASS","external_balance_DNP":"PASS","MCP_reset_domain_isolated_path":"PASS","no_OVP_enable_pullup":"PASS","relay_ideal_contact_states":relay_results,"limitations":"Ideal contacts only; RF loss/isolation and physical BMS/charger topology remain acceptance gates. State11 is forbidden by the firmware contract. Reset-path wiring does not prove firmware heartbeat/timing or coverage of Pico power loss."}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n", encoding="utf-8", newline="\n")
    print("Electrical invariant checks: PASS (GPIO, BMS returns, OVP, relay 00/10/01)")


if __name__ == "__main__":
    main()
