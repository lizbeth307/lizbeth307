"""Create OPEN acceptance templates or provision from a fully accepted record."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
from .commissioning import acceptance_template, load_acceptance_bound

# Per-unit host name (build/15 «Ім'я хоста (W2 SYS-HOST)»). The acceptance record allows the same
# characters (srrx.commissioning.load_acceptance); an RFC 1123 label allows only [a-z0-9-], at most
# 63 characters (RFC 1035 2.3.4), no hyphen at either end. DNS names are case-insensitive (RFC 4343),
# so lower-casing is not a loss; any other change, or a cut to fit 63, appends 6 hex of SHA-256 of
# the lower-cased id. The name is therefore a function of lower(id) alone, lossy ids included.
UNIT_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{3,79}")
HOST_LABEL = re.compile(r"[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?")
HOST_PREFIX = "srrx-"
HOST_SUFFIX_HEX = 6
HOST_FILES = ("hostname", "hosts")


def hostname_for(unit_id):
    """'srrx-' + lower(id) with every run outside [a-z0-9] as one '-', ends trimmed; if that is lossy
    or longer than 63, the slug is cut and '-' + the first 6 hex of SHA-256(lower(id)) appended."""
    if type(unit_id) is not str or not UNIT_ID.fullmatch(unit_id):
        raise ValueError("invalid hardware unit ID for a host name")
    lowered = unit_id.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    name = HOST_PREFIX + slug
    if slug != lowered or len(name) > 63:
        keep = 63 - len(HOST_PREFIX) - 1 - HOST_SUFFIX_HEX
        name = (HOST_PREFIX + slug[:keep].rstrip("-") + "-"
                + hashlib.sha256(lowered.encode("ascii")).hexdigest()[:HOST_SUFFIX_HEX])
    if not HOST_LABEL.fullmatch(name):  # unreachable for a valid id; kept as the contract
        raise ValueError("host name is not an RFC 1123 label: " + name)
    return name


def host_files(unit_id):
    """/etc/hostname (hostname(5): one newline-terminated name) and /etc/hosts as the Debian installer
    writes it, with the 127.0.1.1 line for the unit name (Debian Reference 5.1.1)."""
    name = hostname_for(unit_id)
    return {"hostname": name + "\n",
            "hosts": ("127.0.0.1\tlocalhost\n127.0.1.1\t" + name + "\n\n"
                      "# The following lines are desirable for IPv6 capable hosts\n"
                      "::1\tlocalhost ip6-localhost ip6-loopback\nff02::1\tip6-allnodes\nff02::2\tip6-allrouters\n")}


def provision(acceptance_path, project, output, host_identity=False):
    project, output = Path(project), Path(output)
    # One read is both validated and hashed: qualification_record names exactly
    # the accepted bytes, even if the file is rewritten concurrently. labd
    # recomputes the same digest from /etc/srrx/acceptance.json at start.
    accepted, record_hash = load_acceptance_bound(acceptance_path, project)
    cal = accepted["battery_adc"]["record"]
    path = project / "firmware/pico/calibration.py"
    spec = importlib.util.spec_from_file_location("srrx_provision_calibration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.validate(cal, accepted["pico_serial"])
    record = module.seal({"v": 1, "revision": module.REVISION,
        "serial": accepted["pico_serial"], "calibration_crc32": cal["crc32"],
        "hardware_commissioned": True, "qualification_record": record_hash}, commissioning=True)
    # host_identity ('provision prepare'): /etc/hostname and /etc/hosts of the accepted unit too,
    # written with the pair; a refused unit id stops here, before any output exists.
    hosts = host_files(accepted["hardware_unit_id"].strip()) if host_identity else {}
    # No output directory/file is created until all acceptance validation passes.
    output.mkdir(parents=True, exist_ok=True)
    staged = [((output / name).with_suffix(".tmp"), output / name, json.dumps(value, indent=2) + "\n")
              for name, value in (("calibration.json", cal), ("commissioning.json", record))]
    staged += [(output / (name + ".tmp"), output / name, text) for name, text in hosts.items()]
    try:
        # Every file is fsynced before any replaces the old set: a staging
        # error keeps the previous files; only back-to-back renames remain.
        for stage, target, text in staged:
            with open(stage, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
        for stage, target, text in staged:
            os.replace(stage, target)
    finally:
        for stage, target, text in staged:
            stage.unlink(missing_ok=True)
    if hasattr(os, "O_DIRECTORY"):  # POSIX: persist the renames.
        fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    summary = {"unit": accepted["hardware_unit_id"], "serial": accepted["pico_serial"],
               "acceptance_sha256": record_hash, "files": ["calibration.json", "commissioning.json"] + list(hosts)}
    if hosts:
        summary["hostname"] = hosts["hostname"].strip()
    return summary


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
        print(json.dumps(provision(args.acceptance, args.project, args.output, host_identity=True)))


if __name__ == "__main__":
    main()
