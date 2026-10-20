"""Deterministic end-to-end simulation using the actual host/Pico wire codecs."""
import argparse
import json
from pathlib import Path
from .engine import Engine
from .hardware import SimHardware
from .link import SimLink


def run_scenario(project):
    hardware = SimHardware()
    hardware.set_inputs({n: False for n in hardware.inputs if n.startswith("DCS_")})
    link = SimLink(project)
    engine = Engine(hardware, link)
    now, snapshots = 0, []
    def advance(ms, renew=True):
        nonlocal now
        end = now + ms
        while now < end:
            now += 20
            engine.tick(now)
            if renew and engine.policy.armed and now % 1000 == 0:
                engine.request({"op": "lease", "value": {"ttl_ms": 5000}})
    def capture(label):
        status = engine.status()
        snapshots.append({"label": label, "at_ms": now, "pico_state": link.model.state,
            "last_reported_pico_state": status["pico"].get("state"),
            "reset": link.model.outputs["mcp_reset"], "armed": status["policy"]["armed"],
            "LNA2": hardware.outputs["EN_LNA2"], "error": status["last_error"]})
    try:
        engine.tick(now)
        assert engine.request({"op": "arm"})["ok"]
        advance(1800)
        assert engine.policy.armed
        assert engine.request({"op": "control", "name": "EN_LNA2", "value": True})["ok"]
        capture("active_bias")
        link.drop_link = True
        advance(1000)
        assert not hardware.outputs["EN_LNA2"] and link.model.outputs["mcp_reset"]
        capture("uart_lost")
        link.drop_link = False
        advance(1000)
        assert not engine.policy.armed and not hardware.outputs["EN_LNA2"]
        capture("link_restored_no_auto_rearm")
        assert engine.request({"op": "recover"})["ok"]
        advance(1800)
        assert engine.policy.armed and not hardware.outputs["EN_LNA2"]
        capture("explicit_recovery_outputs_off")
        engine.request({"op": "control", "name": "EN_LNA2", "value": True})
        engine.request({"op": "sim", "name": "FAULT_LNA2", "value": False})
        advance(200)
        assert not hardware.outputs["EN_LNA2"] and link.model.outputs["mcp_reset"]
        capture("fault_latched")
        return {"status": "PASS", "backend": "SIMULATION", "physical_tests_performed": False,
                "scenarios": snapshots, "encoded_wire": True}
    finally:
        engine.close()


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    report = run_scenario(args.project)
    data = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(data)
    print(data, end="")


if __name__ == "__main__":
    main()
