#!/usr/bin/env python3
"""Check independent contact-level contracts and the ideal HF relay network.

The relay calculation is a DC/ideal-contact topology test. It does not establish
RF insertion loss, impedance matching, contact bounce or isolation.
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def main():
    graphs = [json.loads(p.read_text()) for p in sorted((BASE / "design").glob("E[1-5].json"))]
    comps = {c["ref"]: c for g in graphs for c in g["components"]}
    def node(ref, pin):
        return next(p.get("net") for p in comps[ref]["pins"] if str(p["number"]) == str(pin))
    # Locked reference: Radxa GPIO documentation, Daly protected/raw returns,
    # and Adafruit JP pad numbering. These are independent of page generation.
    header = {1:"3V3_Q6A",2:"VCC_5V_PERI",3:"INA228_ALERT",4:"VCC_5V_PERI",5:"MCP_INT",8:"UART5_TX",10:"UART5_RX",13:"I2C0_SDA",15:"I2C0_SCL",16:"UART6_TX",17:"3V3_Q6A",18:"UART6_RX",27:"I2C2_SDA",28:"I2C2_SCL",29:"UART7_RX",32:"UART7_TX",40:"SAFE_BOOT"}
    for pin, net in header.items():
        assert node("J301", pin) == net, ("Radxa header",pin,node("J301",pin),net)
    assert node("J301", 7) == node("U304", "P1.5"), "LC76G PPS must reach Q6A pin7"
    assert node("U101", "B-") == node("U101", "B0") == "E1_CELL0"
    assert node("U101", "P-") == "GND"
    assert node("U101", "B-") != node("U101", "P-")
    assert comps["J102"].get("dnp"), "Unqualified external balance connector must remain DNP"
    # Watchdog reset must remain a MOS-isolated bridge between Pico and Q6A
    # domains. Firmware timing/heartbeat and loss of Pico power are not tested.
    assert node("U305", 22) == node("R393", 1) == node("R395", 2)
    assert node("U305", 36) == node("R395", 1)
    assert node("R393", 2) == node("Q306", 1) == node("R394", 1)
    assert node("Q306", 2) == node("R394", 2) == "GND"
    assert {node(ref, 18) for ref in ("U301", "U302", "U303")} == {node("Q306", 3)}
    # OVP node is a clampable safe-enable signal, not a pulled-up fault input.
    for c in comps.values():
        if c.get("kind") == "resistor" and len(c["pins"]) == 2:
            ns = {p.get("net") for p in c["pins"]}
            assert ns != {"OVP_LNB_N", "3V3_Q6A"}, "Unsafe OVP enable pull-up"
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
                ns = [p.get("net") for p in comps[ref]["pins"]]
                signal = next(n for n in ns if n != "GND")
                if find(signal) == find(net):
                    loads.append(ref)
            effective[port] = loads
        if (k1,k2) == (0,0):
            assert effective == {"HF":["R417"],"VHF":["R418"],"HFP":["R419"]}, effective
            assert len({find(n) for n in ports.values()}) == 3
        elif k1:
            assert find(ports["HFP"]) == find(ports["HF"])
            assert find(ports["HFP"]) != find(ports["VHF"])
            assert effective["HFP"] == [] and effective["VHF"] == ["R418"]
        else:
            assert find(ports["HFP"]) == find(ports["VHF"])
            assert find(ports["HFP"]) != find(ports["HF"])
            assert effective["HFP"] == [] and effective["HF"] == ["R417"]
        relay_results.append({"K1":k1,"K2":k2,"terminations":effective})
    report = {"status":"PASS","radxa_gpio_contract":"PASS","raw_battery_negative_isolated_from_protected_return":"PASS","external_balance_DNP":"PASS","MCP_reset_domain_isolated_path":"PASS","no_OVP_enable_pullup":"PASS","relay_ideal_contact_states":relay_results,"limitations":"Ideal contacts only; RF loss/isolation and physical BMS/charger topology remain acceptance gates. State11 is forbidden by the firmware contract. Reset-path wiring does not prove firmware heartbeat/timing or coverage of Pico power loss."}
    (BASE / "verification/electrical-invariants.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("Electrical invariant checks: PASS (GPIO, BMS returns, OVP, relay 00/10/01)")


if __name__ == "__main__":
    main()
