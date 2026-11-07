"""LimeSuiteNG 37cb183 TX audit part 1 (deployment/recipes/limesuiteng/TX-AUDIT.md) against the exact
upstream fixtures and the RX-only patch: every cited anchor stands at its line, every
reachable entry point is guarded after the patch, and the guard code compiles and rejects TX.
CI evidence only; the audit stays AUDIT_DRAFT_CI_CHECKED and the Lime runtime stays blocked."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

import vendor_patch  # noqa: E402

AUDIT = HERE / "recipes/limesuiteng/TX-AUDIT.md"
RECIPE = HERE / "recipes/limesuiteng/recipe.json"
FIXTURE = HERE / "upstream-fixtures/limesuiteng"
PATCH = HERE / "patches/limesuiteng-rx-only.patch"
VERDICTS = {"blocked", "reachable→patched", "internal-only", "no-TX", "open→part-II"}
ROW = re.compile(r"^\| ([A-E]-\d\d) \| (.+?) \| ([^|`]+?):(\d+) \| `([^`]+)` \| (\S+) \| (.+) \|$")
GUARD_MARKS = ("SRRX_RX_ONLY", "srrxRejectTx(direction")


def body(text, signature, start=0):
    begin = text.index("{", text.index(signature, start)) + 1
    depth, index = 1, begin
    while depth:
        depth += {"{": 1, "}": -1}.get(text[index], 0)
        index += 1
    return text[begin:index - 1]


def first_statement(text):
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", text, flags=re.S).strip()


def audit_rows():
    rows = []
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        match = ROW.match(line)
        if match:
            rows.append(dict(zip(("id", "entry", "file", "line", "anchor", "verdict", "note"), match.groups())))
    return rows


def patched_tree(root):
    vendor_patch.apply_to_copy("limesuiteng", FIXTURE, root / "patched", fixture=True)
    return root / "patched"


def compile_and_run(test, code, root, name):
    source = root / (name + ".cpp")
    source.write_text(code, encoding="utf-8")
    built = subprocess.run(["g++", "-std=c++20", "-Wall", "-Werror", str(source), "-o", str(root / name)],
                           capture_output=True, text=True)
    test.assertEqual(built.returncode, 0, built.stderr[-2000:])
    ran = subprocess.run([str(root / name)], capture_output=True, text=True)
    test.assertEqual(ran.returncode, 0, ran.stderr[-2000:])


class LimeTxAuditDocumentTests(unittest.TestCase):
    def test_every_row_parses_with_a_known_verdict(self):
        text = AUDIT.read_text(encoding="utf-8")
        self.assertIn("**Статус: AUDIT_DRAFT_CI_CHECKED.**", text)
        table_lines = [line for line in text.splitlines() if re.match(r"^\| [A-E]-\d\d \|", line)]
        rows = audit_rows()
        self.assertEqual(len(rows), len(table_lines))
        self.assertGreaterEqual(len(rows), 90)
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        for row in rows:
            self.assertIn(row["verdict"], VERDICTS, row["id"])
        self.assertEqual({row["id"][0] for row in rows}, set("ABCDE"))

    def test_cited_anchors_stand_at_their_lines(self):
        trees = [FIXTURE]
        if os.environ.get("SRRX_LIMESUITENG_TREE"):  # an unpacked locked archive checks every row
            trees.append(Path(os.environ["SRRX_LIMESUITENG_TREE"]))
        checked = 0
        for row in audit_rows():
            for tree in trees:
                path = tree / row["file"]
                if not path.is_file():
                    continue
                lines = path.read_text(encoding="utf-8").split("\n")
                self.assertIn(row["anchor"], lines[int(row["line"]) - 1], "%s %s:%s" % (row["id"], row["file"], row["line"]))
                checked += 1
                break
        self.assertGreaterEqual(checked, 60)

    def test_reachable_entry_points_are_guarded_after_the_patch(self):
        targets = set(json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8"))["limesuiteng"])
        with tempfile.TemporaryDirectory() as tmp:
            tree = patched_tree(Path(tmp))
            for row in audit_rows():
                if row["verdict"] != "reachable→patched":
                    continue
                self.assertIn(row["file"], targets, row["id"])
                text = (tree / row["file"]).read_text(encoding="utf-8")
                start = text.find(row["anchor"])
                while start != -1:  # the anchor is gone, or every definition it names is guarded
                    guarded = body(text, row["anchor"], start)
                    self.assertTrue(any(mark in guarded for mark in GUARD_MARKS), row["id"])
                    start = text.find(row["anchor"], start + 1)

    def test_patch_targets_hashes_and_fixtures_agree(self):
        touched = {line[len("+++ b/"):] for line in PATCH.read_text(encoding="utf-8").splitlines() if line.startswith("+++ b/")}
        hashes = json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8"))["limesuiteng"]
        self.assertEqual(touched, set(hashes))
        for relative, entry in hashes.items():
            self.assertEqual(vendor_patch.digest(FIXTURE / relative), entry["before_sha256"], relative)

    def test_recipe_keeps_the_audited_build_surface(self):
        data = json.loads(RECIPE.read_text(encoding="utf-8"))
        options = data["cmake"]["options"]
        for name in ("BUILD_LEGACYAPI", "BUILD_CLI", "BUILD_GUI", "BUILD_PLUGINS_AMARISOFT", "BUILD_PLUGINS_GNURADIO",
                     "BUILD_PLUGINS_HDSDR", "BUILD_DRIVERS", "LIMESUITENG_USB_FX3", "LIMESUITENG_USB_FTDI", "LIMEPCIE_DKMS"):
            self.assertEqual(options[name], "OFF", name)
        for name in ("LIMESUITENG_PCIE", "LIMESUITENG_LA9310", "BUILD_PLUGINS_SOAPYSDR"):
            self.assertEqual(options[name], "ON", name)
        self.assertEqual(data["source"], {"patch": "deployment/patches/limesuiteng-rx-only.patch"})
        forbidden = next(check["globs"] for check in data["checks"] if check["kind"] == "forbid_paths")
        self.assertLessEqual({"usr/bin/*", "*legacyapi*", "*LimeSuite.h", "*firmware*", "*.ko"}, set(forbidden))


class LimeTxGuardTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        tree = patched_tree(Path(cls.tmp.name))
        cls.files = {name: (tree / name).read_text(encoding="utf-8") for name in json.loads(
            (HERE / "patches/target-hashes.json").read_text(encoding="utf-8"))["limesuiteng"]}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def first(self, name, signature):
        return first_statement(body(self.files[name], signature))

    def test_soapy_setters_reject_tx_and_raw_writes_throw(self):
        settings = "plugins/soapysdr/Settings.cpp"
        for signature in ("void Soapy_limesuiteng::setAntenna(", "void Soapy_limesuiteng::setDCOffsetMode(",
                          "void Soapy_limesuiteng::setDCOffset(", "void Soapy_limesuiteng::setIQBalance(",
                          "void Soapy_limesuiteng::setGain(const int direction, const size_t channel, const double value)",
                          "void Soapy_limesuiteng::setGain(const int direction, const size_t channel, const std::string& name",
                          "void Soapy_limesuiteng::setFrequency(int direction", "void Soapy_limesuiteng::setFrequency(const int direction,",
                          "void Soapy_limesuiteng::setSampleRate(", "void Soapy_limesuiteng::setBandwidth(",
                          "void Soapy_limesuiteng::writeSetting(const int direction"):
            self.assertTrue(self.first(settings, signature).startswith("srrxRejectTx(direction, "), signature)
        for signature in ("void Soapy_limesuiteng::writeRegister(const std::string& name", "void Soapy_limesuiteng::writeRegister(const unsigned addr",
                          "void Soapy_limesuiteng::writeGPIO(", "void Soapy_limesuiteng::writeGPIODir("):
            self.assertTrue(self.first(settings, signature).startswith("throw std::runtime_error("), signature)
        self.assertTrue(self.first(settings, "void Soapy_limesuiteng::writeSetting(const std::string& key").startswith(
            "if (!srrxRxSetting(key) && !srrxTxOffField(key, value))"))
        per_channel = first_statement(body(self.files[settings], "void Soapy_limesuiteng::writeSetting(const int direction"))
        self.assertIn("if (!srrxRxChannelSetting(key) && !srrxTxOffField(key, value))", per_channel.split("const TRXDir dir", 1)[0])
        text = self.files[settings]
        constructor = text[text.index("Soapy_limesuiteng::Soapy_limesuiteng("):text.index("Soapy_limesuiteng::~Soapy_limesuiteng(")]
        self.assertIn("sdrDevice->EnableChannel(socIndex, TRXDir::Tx, channel, false);", constructor)
        self.assertNotIn("TRXDir::Tx, channel, true", constructor)

    def test_native_write_firmware_and_plugin_entries_return_at_once(self):
        micro, base = "src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp", "src/boards/LMS7002M_SDRDevice.cpp"
        for signature in ("OpStatus LimeSDR_Micro::UploadMemory(", "OpStatus LimeSDR_Micro::MemoryWrite(",
                          "OpStatus LimeSDR_Micro::WriteSerialNumber(", "OpStatus LimeSDR_Micro::OEMTest(",
                          "OpStatus LimeSDR_Micro::I2CWrite(", "OpStatus LimeSDR_Micro::UploadTxWaveform("):
            self.assertTrue(self.first(micro, signature).startswith("return OpStatus::NotSupported;"), signature)
        self.assertTrue(self.first(micro, "ICSR* LimeSDR_Micro::getICSR()").startswith("return nullptr;"))
        self.assertTrue(self.first("src/boards/LimeSDR_Micro/calibrations.cpp", "OpStatus LimeSDR_Micro::CalibrateTx()").startswith(
            "return OpStatus::NotSupported;"))
        self.assertTrue(self.first(base, "OpStatus LMS7002M_SDRDevice::LoadConfig(").startswith("return OpStatus::NotSupported;"))
        self.assertTrue(self.first(base, "void* LMS7002M_SDRDevice::GetInternalChip(").startswith("throw std::logic_error("))
        plugin = "src/API/LimePlugin.cpp"
        for signature in ("int LimePlugin_Init(", "int LimePlugin_Setup(", "static int LimePlugin_Write("):
            self.assertTrue(self.first(plugin, signature).startswith("return -1;"), signature)
        self.assertTrue(self.first(plugin, "void LimePlugin_SetTxGain(").startswith("return;"))
        # The RX/TX path switch keeps its write, straight to the protocol, while public I2CWrite is closed.
        path = body(self.files[micro], "OpStatus LimeSDR_Micro::LMSSetPath(")
        self.assertIn("LMS64CProtocol::I2C_Write(*mSerialPort, i2c_expander_address, gpiob_addr, 1, &value, 1);", path)
        self.assertNotIn("    I2CWrite(", path)

    def test_init_leaves_txen_cleared(self):
        init = body(self.files["src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp"], "static OpStatus InitLMS7002M(")
        values = [int(v, 16) for v in re.findall(r"values\.push_back\((0x[0-9A-F]{4})\)", init)]
        self.assertEqual(values, [0xFFF3, 0xFFF1])
        self.assertTrue(all(v & 0x000C == 0 for v in values))  # TXEN_A bit 2, TXEN_B bit 3
        self.assertEqual([v & 0x3 for v in values], [0x3, 0x1])  # MAC: A&B, then A, as upstream
        upstream = body((FIXTURE / "src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp").read_text(encoding="utf-8"), "static OpStatus InitLMS7002M(")
        self.assertEqual(re.findall(r"values\.push_back\((0x[0-9A-F]{4})\)", upstream), ["0xFFFF", "0xFFFD"])


@unittest.skipUnless(shutil.which("g++"), "host C++ compiler unavailable")
class LimeTxGuardCompileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.tree = patched_tree(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, name):
        return (self.tree / name).read_text(encoding="utf-8")

    def test_soapy_allowlists_compile_and_reject_tx(self):
        settings = self.read("plugins/soapysdr/Settings.cpp")
        helpers = settings[settings.index("static void srrxRejectTx("):settings.index("/*******************************************************************\n * Constructor/destructor")]
        code = ("#include <cassert>\n#include <stdexcept>\n#include <string>\nconstexpr int SOAPY_SDR_TX = 0, SOAPY_SDR_RX = 1;\n" + helpers +
                'static bool rejects(int direction) { try { srrxRejectTx(direction, "probe"); } catch (const std::runtime_error&) { return true; } return false; }\n'
                "int main() {\n"
                "    assert(rejects(SOAPY_SDR_TX) && rejects(2) && rejects(-1) && !rejects(SOAPY_SDR_RX));\n"
                '    assert(srrxTxOffField("TXEN_A", "0") && srrxTxOffField("TXEN_B", "0"));\n'
                '    for (const char* v : {"1", "00", " 0", "", "0x0"}) assert(!srrxTxOffField("TXEN_A", v) && !srrxTxOffField("TXEN_B", v));\n'
                '    for (const char* k : {"RXEN_A", "PD_TXPAD_TRF", "MAC", "txen_a"}) assert(!srrxTxOffField(k, "0"));\n'
                '    for (const char* k : {"RXTSP_CONST", "CALIBRATE_RX", "ENABLE_RX_GFIR_LPF", "DISABLE_RX_GFIR_LPF", "RXTSG_NCO", "OVERSAMPLING"}) assert(srrxRxSetting(k));\n'
                '    for (const char* k : {"TXTSP_CONST", "CALIBRATE_TX", "ENABLE_TX_GFIR_LPF", "DISABLE_TX_GFIR_LPF", "TXTSG_NCO", "SAVE_CONFIG",\n'
                '                          "LOAD_CONFIG", "TXEN_A", "CALIBRATE", "TSP_CONST"}) assert(!srrxRxSetting(k));\n'
                '    for (const char* k : {"TSP_CONST", "CALIBRATE_RX", "CALIBRATE", "ENABLE_GFIR_LPF", "DISABLE_GFIR_LPF", "TSG_NCO"}) assert(srrxRxChannelSetting(k));\n'
                '    for (const char* k : {"CALIBRATE_TX", "TXEN_A", "TXEN_B", "LOAD_CONFIG", "SAVE_CONFIG", "G_PAD_TRF", "OVERSAMPLING"}) assert(!srrxRxChannelSetting(k));\n'
                "    return 0;\n}\n")
        compile_and_run(self, code, self.root, "soapy_guards")

    def test_micro_guards_compile_and_pass_only_rx_and_tx_off(self):
        micro = self.read("src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp")
        helper = micro[micro.index("static bool TxOffWrite("):micro.index("} // namespace limesdrmicro")]
        write_guard = body(micro, "OpStatus LimeSDR_Micro::WriteRegister(").split("return mLMSChips", 1)[0]
        spi_guard = body(micro, "OpStatus LimeSDR_Micro::SPI(").split("return lmsSPI", 1)[0]
        configure_guard = body(micro, "OpStatus LimeSDR_Micro::Configure(").split("OpStatus status;", 1)[1].split("if (!fw)", 1)[0]
        clock_guard = body(micro, "OpStatus LimeSDR_Micro::SetClockFreq(").split("auto& chip", 1)[0]
        custom_guard = body(micro, "OpStatus LimeSDR_Micro::CustomParameterWrite(").split("return LMS64CProtocol", 1)[0]
        antenna_guard = body(micro, "OpStatus LimeSDR_Micro::SetAntenna(").split("return LMSSetPath", 1)[0]
        upstream = (FIXTURE / "src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp").read_text(encoding="utf-8")
        self.assertRegex(upstream, r'cp_vctcxo_dac = \{ "VCTCXO DAC \(volatile\)"s, 0, ')
        code = ("#include <cassert>\n#include <cstdint>\n#include <map>\n#include <string>\n#include <vector>\n"
                "enum class OpStatus { Success, NotSupported };\n"
                "enum CalibrationFlag { NONE = 0, DCIQ = (1 << 0), FILTER = (1 << 1) };\n"
                "enum class TRXDir : bool { Rx, Tx };\n"
                "struct LMS7002M { enum class ClockID : uint8_t { CLK_REFERENCE = 0, CLK_SXR = 1, CLK_SXT = 2, CLK_CGEN = 3, CLK_RXTSP = 4, CLK_TXTSP = 5 }; };\n"
                "struct CustomParameterIO { int32_t id; double value; std::string units; };\n"
                "struct Direction { bool enabled = false; uint32_t calibrate = NONE; struct { bool enabled = false; } testSignal;\n"
                "    double centerFrequency = 0; std::map<int, double> gain; };\n"
                "struct ChannelConfig { Direction rx, tx; };\nstruct SDRConfig { ChannelConfig channel[2]; };\n"
                "namespace limesdrmicro {\nstruct Parameter { int32_t id; };\nconst Parameter cp_vctcxo_dac{ 0 };\n" + helper + "}\n"
                "OpStatus writeRegister(unsigned int address, unsigned int value) {" + write_guard + "return OpStatus::Success; }\n"
                "OpStatus spi(const uint32_t* MOSI, uint32_t count) {" + spi_guard + "return OpStatus::Success; }\n"
                "OpStatus configure(const SDRConfig& cfg) {" + configure_guard + "return OpStatus::Success; }\n"
                "OpStatus setClockFreq(uint8_t clk_id) {" + clock_guard + "return OpStatus::Success; }\n"
                "OpStatus customParameterWrite(const std::vector<CustomParameterIO>& parameters) {" + custom_guard + "return OpStatus::Success; }\n"
                "OpStatus setAntenna(TRXDir trx) {" + antenna_guard + "return OpStatus::Success; }\n"
                "int main() {\n    const OpStatus S = OpStatus::Success, NS = OpStatus::NotSupported;\n"
                "    assert(writeRegister(0x0020, 0xFFF1) == S && writeRegister(0x0020, 0x0000) == S);\n"
                "    for (unsigned v : {0xFFFDu, 0xFFF5u, 0xFFF9u, 0x0004u, 0x0008u}) assert(writeRegister(0x0020, v) == NS);\n"
                "    for (unsigned a : {0x0021u, 0x0100u, 0x0103u, 0x0200u, 0x011Cu, 0x0000u}) assert(writeRegister(a, 0) == NS);\n"
                "    const uint32_t reads[] = { 0x00200000u, 0x01000000u }; assert(spi(reads, 2) == S);\n"
                "    const uint32_t txoff[] = { (1u << 31) | (0x0020u << 16) | 0xFFF1u }; assert(spi(txoff, 1) == S);\n"
                "    const uint32_t txon[] = { 0x00200000u, (1u << 31) | (0x0020u << 16) | 0xFFFDu }; assert(spi(txon, 2) == NS);\n"
                "    const uint32_t other[] = { (1u << 31) | (0x0100u << 16) }; assert(spi(other, 1) == NS);\n"
                "    SDRConfig rx; rx.channel[0].rx.enabled = true; rx.channel[0].rx.centerFrequency = 1.7e9; assert(configure(rx) == S);\n"
                "    for (int c = 0; c < 2; ++c) {\n"
                "        SDRConfig a = rx; a.channel[c].tx.calibrate = DCIQ; assert(configure(a) == NS);\n"
                "        SDRConfig b = rx; b.channel[c].tx.testSignal.enabled = true; assert(configure(b) == NS);\n"
                "        SDRConfig d = rx; d.channel[c].tx.centerFrequency = 1e9; assert(configure(d) == NS);\n"
                "        SDRConfig e = rx; e.channel[c].tx.gain[0] = 10; assert(configure(e) == NS);\n    }\n"
                "    assert(setClockFreq(static_cast<uint8_t>(LMS7002M::ClockID::CLK_SXT)) == NS);\n"
                "    for (auto id : {LMS7002M::ClockID::CLK_REFERENCE, LMS7002M::ClockID::CLK_SXR, LMS7002M::ClockID::CLK_CGEN})\n"
                "        assert(setClockFreq(static_cast<uint8_t>(id)) == S);\n"
                '    assert(customParameterWrite({{0, 1000.0, ""}}) == S);\n'
                '    assert(customParameterWrite({{0, 1000.0, ""}, {1, 0.0, ""}}) == NS && customParameterWrite({{7, 0.0, ""}}) == NS);\n'
                "    assert(setAntenna(TRXDir::Tx) == NS && setAntenna(TRXDir::Rx) == S);\n"
                "    return 0;\n}\n")
        compile_and_run(self, code, self.root, "micro_guards")

    def test_base_device_guards_compile_and_pass_only_rx_and_tx_off(self):
        base = self.read("src/boards/LMS7002M_SDRDevice.cpp")
        helper = base[base.index("static bool SrrxTxOffWrite("):base.index("OpStatus LMS7002M_SDRDevice::EnableChannel(")]
        guards = {
            "enable": body(base, "OpStatus LMS7002M_SDRDevice::EnableChannel(").split("if (moduleIndex >= mLMSChips.size())", 1)[0],
            "frequency": body(base, "OpStatus LMS7002M_SDRDevice::SetFrequency(").split("lime::LMS7002M* lms", 1)[0],
            "lpf": body(base, "OpStatus LMS7002M_SDRDevice::SetLowPassFilter(").split("auto& lms", 1)[0],
            "gain": body(base, "OpStatus LMS7002M_SDRDevice::SetGain(").split("auto& device", 1)[0],
            "write": body(base, "OpStatus LMS7002M_SDRDevice::WriteRegister(").split("if (useFPGA)\n        return WriteFPGARegister", 1)[0],
            "name": body(base, "OpStatus LMS7002M_SDRDevice::SetParameter(uint8_t moduleIndex, uint8_t channel, const std::string& parameterKey").split("auto& lms", 1)[0],
            "bits": body(base, "uint8_t moduleIndex, uint8_t channel, uint16_t address, uint8_t msb, uint8_t lsb, uint16_t value)").split("auto& lms", 1)[0],
        }
        code = ("#include <cassert>\n#include <cstdint>\n#include <string>\n"
                "enum class OpStatus { Success, NotSupported };\nenum class TRXDir : bool { Rx, Tx };\n"
                "enum class eGainTypes : uint8_t { LNA, LoopbackLNA, PGA, TIA, PAD, LoopbackPAD, IAMP, PA, UNKNOWN, GENERIC = UNKNOWN };\n" + helper +
                "OpStatus enableChannel(TRXDir trx, bool enable) {" + guards["enable"] + "return OpStatus::Success; }\n"
                "OpStatus setFrequency(TRXDir trx) {" + guards["frequency"] + "return OpStatus::Success; }\n"
                "OpStatus setLowPassFilter(TRXDir trx) {" + guards["lpf"] + "return OpStatus::Success; }\n"
                "OpStatus setGain(TRXDir direction, eGainTypes gain) {" + guards["gain"] + "return OpStatus::Success; }\n"
                "OpStatus writeRegister(unsigned int address, unsigned int value, bool useFPGA) {" + guards["write"] + "return OpStatus::Success; }\n"
                "OpStatus setParameter(const std::string& parameterKey, uint16_t value) {" + guards["name"] + "return OpStatus::Success; }\n"
                "OpStatus setParameterBits(uint16_t address, uint8_t msb, uint8_t lsb, uint16_t value) {" + guards["bits"] + "return OpStatus::Success; }\n"
                "int main() {\n    const OpStatus S = OpStatus::Success, NS = OpStatus::NotSupported;\n"
                "    assert(enableChannel(TRXDir::Tx, true) == NS && enableChannel(TRXDir::Tx, false) == S && enableChannel(TRXDir::Rx, true) == S);\n"
                "    assert(setFrequency(TRXDir::Tx) == NS && setFrequency(TRXDir::Rx) == S);\n"
                "    assert(setLowPassFilter(TRXDir::Tx) == NS && setLowPassFilter(TRXDir::Rx) == S);\n"
                "    for (auto g : {eGainTypes::LNA, eGainTypes::LoopbackLNA, eGainTypes::PGA, eGainTypes::TIA, eGainTypes::UNKNOWN})\n"
                "        assert(setGain(TRXDir::Rx, g) == S && setGain(TRXDir::Tx, g) == NS);\n"
                "    for (auto g : {eGainTypes::PAD, eGainTypes::LoopbackPAD, eGainTypes::IAMP, eGainTypes::PA}) assert(setGain(TRXDir::Rx, g) == NS);\n"
                "    assert(writeRegister(0x0020, 0xFFF1, false) == S && writeRegister(0x0020, 0xFFF1, true) == NS);\n"
                "    assert(writeRegister(0x0020, 0xFFFD, false) == NS && writeRegister(0x0103, 0, false) == NS);\n"
                '    assert(setParameter("TXEN_A", 0) == S && setParameter("TXEN_B", 0) == S && setParameter("TXEN_A", 1) == NS);\n'
                '    assert(setParameter("PD_TXPAD_TRF", 0) == NS && setParameter("MAC", 1) == NS && setParameter("RXEN_A", 0) == NS);\n'
                "    assert(setParameterBits(0x0020, 2, 2, 0) == S && setParameterBits(0x0020, 3, 3, 0) == S && setParameterBits(0x0020, 3, 2, 0) == S);\n"
                "    assert(setParameterBits(0x0020, 2, 2, 1) == NS && setParameterBits(0x0020, 4, 2, 0) == NS && setParameterBits(0x0020, 1, 0, 0) == NS);\n"
                "    assert(setParameterBits(0x0020, 2, 3, 0) == NS && setParameterBits(0x0021, 2, 2, 0) == NS);\n"
                "    return 0;\n}\n")
        compile_and_run(self, code, self.root, "base_guards")



class LimeTxReviewFixTextTests(unittest.TestCase):
    """Review fixes R1-R4 of SW-LIME-1: Configure also rejects the TX band/switch and the TX LPF, the
    device-wide Soapy writeSetting forwards the per-channel RX keys as upstream did, and the audit keeps
    the RX calibration with TX powered down OPEN for the bench."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        tree = patched_tree(Path(cls.tmp.name))
        cls.micro = (tree / "src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp").read_text(encoding="utf-8")
        cls.settings = (tree / "plugins/soapysdr/Settings.cpp").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_configure_rejects_tx_path_and_lpf_before_any_chip_access(self):
        configure = body(self.micro, "OpStatus LimeSDR_Micro::Configure(")
        guard = configure.split('"Firmware is not loaded");', 1)[1].split("auto& rfsoc", 1)[0]
        self.assertIn("if (cfg.channel[c].tx.path != 0 || cfg.channel[c].tx.lpf != 0)", guard)
        self.assertIn("return OpStatus::NotSupported;", guard)
        self.assertLess(configure.index("tx.path != 0"), configure.index("InitLMS7002M("))
        self.assertLess(configure.index("tx.path != 0"), configure.index("LMSSetPath(TRXDir::Tx"))

    def test_device_wide_setting_forwards_only_per_channel_rx_keys(self):
        guard = body(self.settings, "void Soapy_limesuiteng::writeSetting(const std::string& key").split("const size_t channelCount", 1)[0]
        self.assertTrue(first_statement(guard).startswith("if (!srrxRxSetting(key) && !srrxTxOffField(key, value))"))
        self.assertIn("if (!srrxRxChannelSetting(key))", guard)
        self.assertIn("throw std::runtime_error(", guard)
        upstream = (FIXTURE / "plugins/soapysdr/Settings.cpp").read_text(encoding="utf-8")
        self.assertIn("            writeSetting(SOAPY_SDR_RX, channel, key, value);", upstream.split("\n")[957])

    def test_audit_records_calibration_with_tx_off_as_open(self):
        text = AUDIT.read_text(encoding="utf-8")
        remainder = text.split("## Залишки та OPEN", 1)[1].split("## Перевірки", 1)[0]
        item = next(line for line in remainder.splitlines() if line.startswith("8. "))
        for needle in ("OPEN", "CALIBRATE_RX", "rx.calibrate=DCIQ", "EnableChannel(Tx, false)", "TXEN = 0"):
            self.assertIn(needle, item)
        self.assertIn("lms7002m.c:195-197", text)
        self.assertIn("`setReferenceClockRate`", text)
        self.assertIn("Device.cpp:589", text)
        self.assertNotIn("не змінено.", text.split("## Що лишається дозволеним", 1)[1].split("## Залишки", 1)[0])
        self.assertNotIn("REVIEWED.**", text)


@unittest.skipUnless(shutil.which("g++"), "host C++ compiler unavailable")
class LimeTxReviewFixCompileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        cls.tree = patched_tree(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, name):
        return (self.tree / name).read_text(encoding="utf-8")

    def test_device_wide_soapy_setting_guard_compiles_and_passes_rx_keys_only(self):
        settings = self.read("plugins/soapysdr/Settings.cpp")
        helpers = settings[settings.index("static void srrxRejectTx("):settings.index("/*******************************************************************\n * Constructor/destructor")]
        guard = body(settings, "void Soapy_limesuiteng::writeSetting(const std::string& key").split("const size_t channelCount", 1)[0]
        code = ("#include <cassert>\n#include <stdexcept>\n#include <string>\nconstexpr int SOAPY_SDR_TX = 0, SOAPY_SDR_RX = 1;\n" + helpers +
                "static bool accepted(const std::string& key, const std::string& value) {\n"
                "    try {" + guard + "} catch (const std::runtime_error&) { return false; }\n"
                "    // as upstream (Settings.cpp:958), an unlisted key goes on per channel with the RX direction\n"
                "    if (!srrxRxSetting(key) && !srrxTxOffField(key, value)) {\n"
                '        srrxRejectTx(SOAPY_SDR_RX, "probe");\n'
                "        assert(srrxRxChannelSetting(key));\n    }\n    return true;\n}\n"
                "int main() {\n"
                '    for (const char* k : {"RXTSP_CONST", "CALIBRATE_RX", "ENABLE_RX_GFIR_LPF", "DISABLE_RX_GFIR_LPF", "RXTSG_NCO", "OVERSAMPLING",\n'
                '                          "TSP_CONST", "CALIBRATE", "ENABLE_GFIR_LPF", "DISABLE_GFIR_LPF", "TSG_NCO"}) assert(accepted(k, "1"));\n'
                '    assert(accepted("TXEN_A", "0") && accepted("TXEN_B", "0"));\n'
                '    for (const char* k : {"TXTSP_CONST", "CALIBRATE_TX", "ENABLE_TX_GFIR_LPF", "DISABLE_TX_GFIR_LPF", "TXTSG_NCO", "SAVE_CONFIG",\n'
                '                          "LOAD_CONFIG", "G_PAD_TRF", "PD_TXPAD_TRF", "MAC", "calibrate"}) assert(!accepted(k, "0"));\n'
                '    assert(!accepted("TXEN_A", "1") && !accepted("TXEN_B", "1"));\n'
                "    return 0;\n}\n")
        compile_and_run(self, code, self.root, "soapy_device_setting_guard")

    def test_configure_tx_path_and_lpf_guard_compiles_and_rejects(self):
        micro = self.read("src/boards/LimeSDR_Micro/LimeSDR_Micro.cpp")
        guard = body(micro, "OpStatus LimeSDR_Micro::Configure(").split('"Firmware is not loaded");', 1)[1].split("auto& rfsoc", 1)[0]
        code = ("#include <cassert>\n#include <cstdint>\n#include <initializer_list>\n#include <limits>\n"
                "enum class OpStatus { Success, NotSupported };\n"
                "struct Direction { double lpf = 0; uint8_t path = 0; };\n"
                "struct ChannelConfig { Direction rx, tx; };\nstruct SDRConfig { ChannelConfig channel[2]; };\n"
                "OpStatus configure(const SDRConfig& cfg) {" + guard + "return OpStatus::Success; }\n"
                "int main() {\n    const OpStatus S = OpStatus::Success, NS = OpStatus::NotSupported;\n"
                "    SDRConfig rx; rx.channel[0].rx.path = 2; rx.channel[0].rx.lpf = 5e6; rx.channel[1].rx.path = 3; assert(configure(rx) == S);\n"
                "    for (int c = 0; c < 2; ++c) {\n"
                "        for (uint8_t p : {1, 2, 3}) { SDRConfig a = rx; a.channel[c].tx.path = p; assert(configure(a) == NS); }\n"
                "        for (double l : {5e6, 1.0, -1.0, std::numeric_limits<double>::quiet_NaN()}) { SDRConfig b = rx; b.channel[c].tx.lpf = l; assert(configure(b) == NS); }\n    }\n"
                "    return 0;\n}\n")
        compile_and_run(self, code, self.root, "configure_tx_path_lpf_guard")


if __name__ == "__main__":
    unittest.main()
