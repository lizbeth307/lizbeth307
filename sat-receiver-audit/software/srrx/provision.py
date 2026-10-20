"""Create OPEN acceptance templates or provision from a fully accepted record."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from .commissioning import acceptance_template, load_acceptance


def provision(acceptance_path, project, output):
    project, output = Path(project), Path(output)
    accepted = load_acceptance(acceptance_path, project)
    cal = accepted["battery_adc"]["record"]
    path = project / "firmware/pico/calibration.py"
    spec = importlib.util.spec_from_file_location("srrx_provision_calibration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate(cal, accepted["pico_serial"])
    record_hash = hashlib.sha256(Path(acceptance_path).read_bytes()).hexdigest()
    record = module.seal({"v": 1, "revision": module.REVISION,
        "serial": accepted["pico_serial"], "calibration_crc32": cal["crc32"],
        "hardware_commissioned": True, "qualification_record": record_hash}, commissioning=True)
    # No output directory/file is created until all acceptance validation passes.
    output.mkdir(parents=True, exist_ok=True)
    for name, value in [("calibration.json", cal), ("commissioning.json", record)]:
        target = output / name
        stage = target.with_suffix(".tmp")
        stage.write_text(json.dumps(value, indent=2) + "\n")
        stage.replace(target)
    return {"unit": accepted["hardware_unit_id"], "serial": accepted["pico_serial"],
            "acceptance_sha256": record_hash, "files": ["calibration.json", "commissioning.json"]}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, default=Path(__file__).resolve().parents[2])
    sub = p.add_subparsers(dest="op", required=True)
    template = sub.add_parser("template")
    template.add_argument("--output", type=Path, required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--acceptance", type=Path, required=True)
    prepare.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    if args.op == "template":
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(acceptance_template(args.project), ensure_ascii=False, indent=2) + "\n")
        print("OPEN template written; hardware remains blocked")
    else:
        print(json.dumps(provision(args.acceptance, args.project, args.output)))


if __name__ == "__main__":
    main()
