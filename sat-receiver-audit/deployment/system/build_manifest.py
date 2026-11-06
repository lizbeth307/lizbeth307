#!/usr/bin/env python3
"""Generate an OPEN build manifest for deploy.py verify-build from an installed prefix.

The walk is deploy.build_inventory, the one verify_build itself compares, so every regular
file gets its SHA-256, an internal directory link "symlink:<target>", every .so file an
allowed_modules entry, and the same refusals apply (external symlink, special file, known
TX tool or plugin, Lime runtime). The output is always status OPEN with OPEN evidence: a
reviewer attaches the source-audit and TX-negative-test reports (inside the prefix), sets
both to PASS after reading them and flips status to REVIEWED. This tool never writes PASS
or REVIEWED. Build it after the venvs exist (python3 -m venv --copies), since they change
the file list (software/DEPLOYMENT.md).
"""
import argparse
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import deploy  # noqa: E402


def generate(prefix, reports=None):
    """Manifest dict for prefix. reports maps source_audit / tx_negative_tests to a report path
    relative to the prefix: its SHA-256 is recorded, the status stays OPEN."""
    root = Path(prefix).resolve(strict=True)
    files, modules = deploy.build_inventory(root)
    if not files:
        raise deploy.DeploymentError("prefix holds no files")
    manifest = {"schema_version": 1, "status": "OPEN", "files": files, "allowed_modules": sorted(modules)}
    for name in ("source_audit", "tx_negative_tests"):
        relative = (reports or {}).get(name)
        report = {"path": None, "sha256": None}
        if relative is not None:
            path = (root / relative).resolve()
            if Path(relative).is_absolute() or not path.is_relative_to(root) or not path.is_file():
                raise deploy.DeploymentError(name + " report must be a file inside the prefix")
            if path.relative_to(root).as_posix() not in files:
                raise deploy.DeploymentError(name + " report is not part of the walked prefix")
            report = {"path": path.relative_to(root).as_posix(), "sha256": files[path.relative_to(root).as_posix()]}
        manifest[name] = {"status": "OPEN", "report": report}
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--prefix", type=Path, required=True, help="installed tree, e.g. /opt/srrx")
    parser.add_argument("--output", type=Path, required=True, help="new file outside the prefix")
    parser.add_argument("--source-audit-report", help="report path relative to the prefix")
    parser.add_argument("--tx-negative-tests-report", help="report path relative to the prefix")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        if output.exists() or output.is_relative_to(args.prefix.resolve()):
            raise deploy.DeploymentError("output must be a new file outside the prefix")
        manifest = generate(args.prefix, {"source_audit": args.source_audit_report,
                                          "tx_negative_tests": args.tx_negative_tests_report})
        with output.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    except (OSError, ValueError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps({"status": "OPEN_MANIFEST_WRITTEN", "files": len(manifest["files"]),
                      "allowed_modules": len(manifest["allowed_modules"]), "output": str(output),
                      "next": "review, attach PASS evidence, set REVIEWED by hand"}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
