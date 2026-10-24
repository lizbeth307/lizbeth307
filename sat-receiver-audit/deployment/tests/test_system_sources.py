"""deployment/system: device-tree overlays and their checker, pps-gpio DKMS, QNN runtime layout.

Synthetic DTBs, debs and modules only: the real merge, module build and deb layout run in
.github/workflows/sr-rx-system.yml on downloaded locked inputs (CI results, not bench)."""
import hashlib
import io
import json
import lzma
from pathlib import Path
import re
import struct
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "system"))
import fdt_check  # noqa: E402
import npu_layout  # noqa: E402
import pps_dkms  # noqa: E402

DT = HERE / "system/dt"


def fdt(nodes):
    """Minimal FDT v17 writer: {path: {prop: bytes}} with parents listed before children."""
    strings, offsets = bytearray(), {}

    def name_offset(name):
        if name not in offsets:
            offsets[name] = len(strings)
            strings.extend(name.encode() + b"\0")
        return offsets[name]

    def pad(block):
        block.extend(b"\0" * (-len(block) % 4))

    children = {}
    for path in nodes:
        if path != "/":
            children.setdefault(path.rsplit("/", 1)[0] or "/", []).append(path)
    body = bytearray()

    def emit(path):
        body.extend(struct.pack(">I", 1))
        body.extend(("" if path == "/" else path.rsplit("/", 1)[1]).encode() + b"\0")
        pad(body)
        for prop, value in nodes[path].items():
            body.extend(struct.pack(">III", 3, len(value), name_offset(prop)))
            body.extend(value)
            pad(body)
        for child in children.get(path, []):
            emit(child)
        body.extend(struct.pack(">I", 2))
    emit("/")
    body.extend(struct.pack(">I", 9))
    rsv = b"\0" * 16
    off_rsv, off_struct = 40, 40 + len(rsv)
    off_strings = off_struct + len(body)
    total = off_strings + len(strings)
    header = struct.pack(">10I", 0xD00DFEED, total, off_struct, off_strings, off_rsv, 17, 16, 0, len(strings), len(body))
    return header + rsv + bytes(body) + bytes(strings)


def s(text):
    return text.encode() + b"\0"


def u32(*values):
    return struct.pack(">%dI" % len(values), *values)


def merged_tree(pcie="okay"):
    """What fdtoverlay must produce for lab (pcie okay) or field (pcie disabled)."""
    q, t = fdt_check.QUP0, fdt_check.TLMM
    nodes = {"/": {"compatible": s("radxa,dragon-q6a") + s("qcom,qcm6490")}, "/aliases": {
        "serial0": s(q + "/serial@994000"), "serial1": s(q + "/serial@998000"), "serial2": s(q + "/serial@99c000")},
        "/chosen": {"bootargs": s("console=ttyMSM0")}, "/soc@0": {}, q: {}}
    for node in ("serial@998000", "serial@99c000", "i2c@980000", "i2c@988000"):
        nodes[q + "/" + node] = {"status": s("okay")}
    for node in ("i2c@980000", "i2c@988000"):
        nodes[q + "/" + node]["clock-frequency"] = u32(100000)
    for node in ("spi@998000", "i2c@998000", "spi@99c000", "i2c@99c000", "spi@980000", "serial@980000", "spi@988000", "serial@988000"):
        nodes[q + "/" + node] = {"status": s("disabled")}
    nodes[t] = {"phandle": u32(1)}
    for handle, state in enumerate(("qup-uart6-tx-state", "qup-uart6-rx-state", "qup-uart7-tx-state", "qup-uart7-rx-state"), 2):
        nodes[t + "/" + state] = {"phandle": u32(handle)}
    nodes[t + "/pps-gnss-default-state"] = {"phandle": u32(9), "pins": s("gpio96"), "function": s("gpio")}
    nodes[q + "/serial@998000"]["pinctrl-0"] = u32(2, 3)
    nodes[q + "/serial@99c000"]["pinctrl-0"] = u32(4, 5)
    nodes["/pps-gnss"] = {"compatible": s("pps-gpio"), "gpios": u32(1, 96, 0), "pinctrl-0": u32(9)}
    nodes[fdt_check.PCIE0] = {"status": s(pcie)}
    return nodes


class DeviceTreeTests(unittest.TestCase):
    def test_checker_accepts_the_expected_merge_per_profile(self):
        lab, field = fdt_check.parse(fdt(merged_tree("okay"))), fdt_check.parse(fdt(merged_tree("disabled")))
        self.assertEqual(fdt_check.check(lab, "lab"), [])
        self.assertEqual(fdt_check.check(field, "field"), [])
        self.assertTrue(any("pcie@1c00000" in p for p in fdt_check.check(lab, "field")))
        self.assertTrue(any("pcie@1c00000" in p for p in fdt_check.check(field, "lab")))

    def test_checker_reports_each_missing_overlay_effect(self):
        for change in ("uart6", "pinctrl", "clock", "alias", "pps", "spi6"):
            tree = merged_tree()
            q = fdt_check.QUP0
            if change == "uart6":
                tree[q + "/serial@998000"]["status"] = s("disabled")
            elif change == "pinctrl":
                tree[q + "/serial@998000"]["pinctrl-0"] = u32(2, 3, 4)  # CTS/RTS-style extra state
            elif change == "clock":
                tree[q + "/i2c@988000"]["clock-frequency"] = u32(400000)
            elif change == "alias":
                del tree["/aliases"]["serial2"]
            elif change == "pps":
                tree["/pps-gnss"]["gpios"] = u32(1, 97, 0)
            else:
                tree[q + "/spi@998000"]["status"] = s("okay")
            self.assertNotEqual(fdt_check.check(fdt_check.parse(fdt(tree)), "lab"), [], change)

    def test_diff_ignores_only_the_efi_owned_chosen_node(self):
        reference = fdt_check.parse(fdt(merged_tree()))
        booted = merged_tree()
        booted["/chosen"] = {"bootargs": s("console=ttyMSM0 root=PARTUUID=x"), "kaslr-seed": u32(0, 1)}
        self.assertEqual(fdt_check.diff(reference, fdt_check.parse(fdt(booted))), [])
        booted["/pps-gnss"]["gpios"] = u32(1, 96, 1)
        self.assertEqual(fdt_check.diff(reference, fdt_check.parse(fdt(booted))), ["/pps-gnss:gpios"])
        with self.assertRaises(fdt_check.FdtError):
            fdt_check.parse(b"\0" * 64)

    def test_overlay_sources_match_the_checker_and_the_copied_fragments(self):
        lab = (DT / "lab-q6a.dtso").read_text(encoding="utf-8")
        field = (DT / "field-q6a.dtso").read_text(encoding="utf-8")
        for text in (lab, field):
            self.assertTrue(text.startswith("// SPDX-License-Identifier: BSD-3-Clause\n"))
            self.assertIn("/dts-v1/;\n/plugin/;\n", text)
            self.assertNotRegex(text.split("*/", 1)[1], r"#include|metadata")
        for label in ("spi6", "i2c6", "uart6", "spi7", "i2c7", "uart7", "spi0", "i2c0", "uart0", "spi2", "i2c2", "uart2", "tlmm"):
            self.assertIn("\n&" + label + " {\n", lab)
        self.assertEqual(lab.count("clock-frequency = <100000>;"), 2)
        self.assertIn("pinctrl-0 = <&qup_uart6_tx>, <&qup_uart6_rx>;", lab)
        self.assertIn("pinctrl-0 = <&qup_uart7_tx>, <&qup_uart7_rx>;", lab)
        self.assertIn("gpios = <&tlmm 96 0>;", lab)
        self.assertIn('serial1 = "' + fdt_check.QUP0 + '/serial@998000";', lab)
        self.assertIn('serial2 = "' + fdt_check.QUP0 + '/serial@99c000";', lab)
        self.assertNotIn("pcie", lab.split("*/", 1)[1])
        self.assertIn("&pcie0 {\n\tstatus = \"disabled\";\n};", field)
        self.assertNotRegex(field.split("*/", 1)[1], r"gpio-hog")  # WIFI_PWR_EN line is TBD (W1-2)
        lock = json.loads((HERE / "system/system-sources.lock.json").read_text(encoding="utf-8"))
        self.assertIn(lock["radxa_overlays"]["commit"], lab)
        self.assertIn(lock["radxa_overlays"]["commit"], (DT / "LICENSE.radxa-overlays").read_text())
        self.assertEqual(len(lock["radxa_overlays"]["files"]), 4)
        sources = json.loads((HERE / "sources.lock.json").read_text(encoding="utf-8"))
        artifacts = {a["id"] for a in sources["artifacts"]}
        self.assertTrue(set(lock["kernel_artifacts"].values()) <= artifacts)


class PpsDkmsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-dkms-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_assembly_requires_the_locked_source_bytes(self):
        source = self.root / "pps-gpio.c"
        source.write_bytes(b"// not the radxa/kernel 559f4f9 file\n")
        with self.assertRaisesRegex(pps_dkms.DkmsError, "differs"):
            pps_dkms.assemble(source, self.root / "out")
        pin = dict(pps_dkms.lock(), sha256=hashlib.sha256(source.read_bytes()).hexdigest(), size=source.stat().st_size)
        with patch.object(pps_dkms, "lock", lambda: pin):
            result = pps_dkms.assemble(source, self.root / "out")
            with self.assertRaises(pps_dkms.DkmsError):
                pps_dkms.assemble(source, self.root / "out")  # never into an existing tree
        tree = Path(result["tree"])
        self.assertEqual(tree.name, "srrx-pps-gpio-1.2.0+lab1")
        self.assertEqual(sorted(p.name for p in tree.iterdir()), ["Makefile", "dkms.conf", "pps-gpio.c"])
        conf = (tree / "dkms.conf").read_text()
        self.assertIn('BUILT_MODULE_NAME[0]="pps-gpio"', conf)
        self.assertIn("CC=gcc-12", conf)
        self.assertIn("obj-m := pps-gpio.o", (tree / "Makefile").read_text())

    def test_lock_pins_the_documented_upstream_file(self):
        pin = pps_dkms.lock()
        self.assertEqual(pin["commit"][:7], "559f4f9")  # build/07 §5.2
        self.assertEqual(pin["path"], "drivers/pps/clients/pps-gpio.c")
        self.assertRegex(pin["sha256"], r"^[0-9a-f]{64}$")
        self.assertIn(pin["commit"], pin["url"])
        self.assertFalse(pin["committed"])
        self.assertFalse((HERE / "system/dkms/pps-gpio/pps-gpio.c").exists())

    def test_vermagic_is_read_from_the_module(self):
        module = self.root / "pps-gpio.ko"
        module.write_bytes(b"\x7fELF" + b"\0" * 60 + b"license=GPL\0vermagic=6.18.2-4-qcom SMP preempt mod_unload aarch64\0")
        self.assertEqual(pps_dkms.check_vermagic(module)["status"], "VERMAGIC_MATCHES")
        module.write_bytes(b"\x7fELF" + b"\0" * 60 + b"vermagic=7.0.11-7-qcom SMP preempt mod_unload aarch64\0")
        with self.assertRaises(pps_dkms.DkmsError):
            pps_dkms.check_vermagic(module)


def deb(members, compression="xz"):
    """ar archive with debian-binary, control.tar.xz and data.tar.<compression>."""
    raw = io.BytesIO()
    with tarfile.open(fileobj=raw, mode="w") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo("./" + name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    payload = lzma.compress(raw.getvalue()) if compression == "xz" else raw.getvalue()
    out = bytearray(b"!<arch>\n")
    for name, data in (("debian-binary", b"2.0\n"), ("control.tar.xz", lzma.compress(b"")),
                       ("data.tar." + compression if compression != "tar" else "data.tar", payload)):
        out += ("%-16s%-12s%-6s%-6s%-8s%-10s`\n" % (name, 0, 0, 0, 100644, len(data))).encode()
        out += data + (b"\n" if len(data) % 2 else b"")
    return bytes(out)


class NpuLayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-npu-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        real = npu_layout.load_lock()
        self.members = {name: ("synthetic " + name).encode() for name in real["install"]}
        self.members["usr/lib/aarch64-linux-gnu/libQnnHtpPrepare.so"] = b"excluded"
        data = deb(self.members)
        (self.root / "qnn.deb").write_bytes(data)
        self.lock = json.loads(json.dumps(real))
        self.lock["package"].update(sha256=hashlib.sha256(data).hexdigest(), size=len(data))
        for name, entry in self.lock["install"].items():
            entry.update(sha256=hashlib.sha256(self.members[name]).hexdigest(), size=len(self.members[name]))

    def test_layout_copies_exactly_the_pinned_runtime(self):
        record = npu_layout.layout(self.root / "out", deb=self.root / "qnn.deb", lock=self.lock)
        prefix = self.root / "out/opt/lab/npu/2.42"
        copied = sorted(p.relative_to(prefix).as_posix() for p in prefix.rglob("*") if p.is_file())
        self.assertEqual(copied, sorted(["LAYOUT.json"] + [e["dest"] for e in self.lock["install"].values()]))
        self.assertFalse(any("Prepare" in p for p in copied))
        self.assertEqual((prefix / "dsp/libQnnHtpV68Skel.so").read_bytes(), self.members["usr/lib/aarch64-linux-gnu/libQnnHtpV68Skel.so"])
        self.assertFalse(record["htp_executed"])
        unit = (self.root / "out/etc/systemd/system/inferd-htp.service").read_text()
        for line in ("User=labnpu", "SupplementaryGroups=fastrpc", "WatchdogSec=5", "MemoryMax=1G", "CPUAffinity=0-3",
                     "DevicePolicy=closed", "DeviceAllow=/dev/fastrpc-cdsp rw", "DeviceAllow=/dev/fastrpc-cdsp-secure rw",
                     "DeviceAllow=/dev/dma_heap/system rw", "IPAddressDeny=any", "OOMScoreAdjust=300",
                     'Environment="ADSP_LIBRARY_PATH=/opt/lab/npu/2.42/dsp;/usr/lib/dsp/cdsp"',
                     "Environment=LD_LIBRARY_PATH=/opt/lab/npu/2.42/lib", "Requires=fastrpc.service cdsprpcd.service"):
            self.assertIn(line, unit.splitlines())  # STACK.md:875
        self.assertNotIn("PrivateDevices", unit.split("[Service]")[1].replace("No PrivateDevices=", ""))
        self.assertNotIn("[Install]", unit)  # never enabled by a preset or by accident

    def test_tampered_inputs_are_refused(self):
        with self.assertRaisesRegex(npu_layout.LayoutError, "SHA-256"):
            npu_layout.layout(self.root / "a", deb=self.root / "qnn.deb", lock=dict(self.lock, package=dict(self.lock["package"], sha256="0" * 64)))
        changed = json.loads(json.dumps(self.lock))
        next(iter(changed["install"].values()))["sha256"] = "0" * 64
        with self.assertRaisesRegex(npu_layout.LayoutError, "differs"):
            npu_layout.layout(self.root / "b", deb=self.root / "qnn.deb", lock=changed)
        with self.assertRaises(npu_layout.LayoutError):
            npu_layout.layout(self.root / "c", lock=self.lock)
        installed = self.root / "installed"
        for name, data in self.members.items():
            (installed / name).parent.mkdir(parents=True, exist_ok=True)
            (installed / name).write_bytes(data)
        self.assertEqual(npu_layout.layout(self.root / "d", root=installed, lock=self.lock)["source"], "installed root")

    def test_real_lock_pins_the_documented_deb(self):
        lock = npu_layout.load_lock()
        self.assertEqual(lock["package"]["sha256"], "306fd647b88902d170831980ca68a31d77d77923534e2070783fbeca132a6e54")
        self.assertEqual(lock["package"]["size"], 44221844)  # STACK.md:867
        self.assertEqual(lock["prefix"], "opt/lab/npu/2.42")
        dests = {e["dest"] for e in lock["install"].values()}
        self.assertIn("lib/libQnnHtp.so", dests)
        self.assertIn("dsp/libQnnHtpV68Skel.so", dests)
        self.assertIn("usr/lib/aarch64-linux-gnu/libQnnHtpPrepare.so", lock["excluded"])


if __name__ == "__main__":
    unittest.main()
