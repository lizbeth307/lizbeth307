"""LimeSuiteNG 37cb183 TX audit part 1 (deployment/recipes/limesuiteng/TX-AUDIT.md) against the exact
upstream fixtures and the reviewed RX-only patch: every cited anchor stands at its line, every
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


# TX audit part 2 (W2 SW-LIME-2): sections F-M of TX-AUDIT.md, the three part-2 patch targets and the
# reviewed export lists (recipes/limesuiteng/exports.json) behind the recipe's export_count checks.
PART2_ROW = re.compile(r"^\| ([F-M]-\d\d) \| (.+?) \| ([^|`]+?):(\d+) \| `([^`]+)` \| (\S+) \| (.+) \|$")
PART2_VERDICTS = {"blocked", "reachable→patched", "internal-only", "no-TX", "open"}
PART2_TARGETS = ("src/boards/BoardSupportLoader.in.cpp", "src/boards/CMakeLists.txt", "src/boards/LimeSDR_Micro/LA9310_TRX.cpp")
EXPORTS = HERE / "recipes/limesuiteng/exports.json"
LIB_FILE = "usr/lib/aarch64-linux-gnu/liblimesuiteng.so.0.3-1"
SOAPY_FILE = "usr/lib/aarch64-linux-gnu/SoapySDR/modules0.8/liblimesuitengSupport.so"
LIME_NAME = re.compile(r"^_Z(?:T[VIS])?NK?4lime(\d+)")


def part2_rows():
    rows = []
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        match = PART2_ROW.match(line)
        if match:
            rows.append(dict(zip(("id", "entry", "file", "line", "anchor", "verdict", "note"), match.groups())))
    return rows


def section_l():
    text = AUDIT.read_text(encoding="utf-8")
    return text[text.index("### L. "):text.index("### M. ")]


def lime_names(symbols):
    """The lime-namespace names (classes and free functions) the mangled symbols define."""
    names = set()
    for symbol in symbols:
        match = LIME_NAME.match(symbol)
        if match:
            names.add(symbol[match.end():match.end() + int(match.group(1))])
    return names


class LimeTxAuditPartTwoTests(unittest.TestCase):
    def test_part_two_rows_parse_with_known_verdicts(self):
        text = AUDIT.read_text(encoding="utf-8")
        self.assertIn("## Частина II", text)
        table_lines = [line for line in text.splitlines() if re.match(r"^\| [F-M]-\d\d \|", line)]
        rows = part2_rows()
        self.assertEqual(len(rows), len(table_lines))
        self.assertGreaterEqual(len(rows), 50)
        self.assertEqual(len({row["id"] for row in rows}), len(rows))
        for row in rows:
            self.assertIn(row["verdict"], PART2_VERDICTS, row["id"])
        self.assertEqual({row["id"][0] for row in rows}, set("FGHIJKLM"))
        self.assertNotIn("REVIEWED.**", text)

    def test_part_two_anchors_stand_at_their_lines(self):
        trees = [FIXTURE]
        if os.environ.get("SRRX_LIMESUITENG_TREE"):  # an unpacked locked archive checks every row
            trees.append(Path(os.environ["SRRX_LIMESUITENG_TREE"]))
        checked = 0
        for row in part2_rows():
            for tree in trees:
                path = tree / row["file"]
                if not path.is_file():
                    continue
                lines = path.read_text(encoding="utf-8").split("\n")
                self.assertIn(row["anchor"], lines[int(row["line"]) - 1], "%s %s:%s" % (row["id"], row["file"], row["line"]))
                checked += 1
                break
        self.assertGreaterEqual(checked, len(part2_rows()) if len(trees) > 1 else 6)

    def test_part_two_patched_rows_are_guarded_or_gone_after_the_patch(self):
        targets = set(json.loads((HERE / "patches/target-hashes.json").read_text(encoding="utf-8"))["limesuiteng"])
        self.assertLessEqual(set(PART2_TARGETS), targets)
        with tempfile.TemporaryDirectory() as tmp:
            tree = patched_tree(Path(tmp))
            patched = [row for row in part2_rows() if row["verdict"] == "reachable→patched"]
            self.assertGreaterEqual(len(patched), 4)
            for row in patched:
                self.assertIn(row["file"], targets, row["id"])
                text = (tree / row["file"]).read_text(encoding="utf-8")
                if "::" in row["anchor"] and row["anchor"].endswith(("(", ")")):  # a C++ definition: each one is guarded
                    start = text.find(row["anchor"])
                    self.assertNotEqual(start, -1, row["id"])
                    while start != -1:
                        self.assertIn("SRRX_RX_ONLY", body(text, row["anchor"], start), row["id"])
                        start = text.find(row["anchor"], start + 1)
                else:  # a statement: the patch removed it
                    self.assertNotIn(row["anchor"].strip(), [line.strip() for line in text.split("\n")], row["id"])

    def test_part_one_open_rows_name_their_part_two_closure(self):
        notes = {row["id"]: row["note"] for row in audit_rows()}
        self.assertIn("G-06", notes["B-41"])
        self.assertIn("M-01", notes["E-05"])
        ids = {row["id"] for row in part2_rows()}
        self.assertLessEqual({"G-05", "G-06", "J-01", "M-01", "M-02", "F-09", "K-01", "K-02", "H-05"}, ids)


class LimeTxPartTwoGuardTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        tree = patched_tree(Path(cls.tmp.name))
        cls.files = {name: (tree / name).read_text(encoding="utf-8") for name in PART2_TARGETS}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_micro_stream_rejects_tx_setup_and_transmit(self):
        trx = self.files["src/boards/LimeSDR_Micro/LA9310_TRX.cpp"]
        setup = body(trx, "OpStatus LA9310_TRX::Setup(const StreamConfig& cfg)")
        guard = setup.index("if (needTx)\n        return ReportError(OpStatus::NotSupported")
        self.assertLess(guard, setup.index("mConfig = cfg;"))
        self.assertLess(guard, setup.index("TxSetup()"))
        start, seen = trx.find("uint32_t LA9310_TRX::Transmit("), 0
        while start != -1:
            transmit = body(trx, "uint32_t LA9310_TRX::Transmit(", start)
            self.assertTrue(first_statement(transmit).startswith("return 0;"))
            self.assertNotIn("StreamTxTemplate", transmit)
            seen += 1
            start = trx.find("uint32_t LA9310_TRX::Transmit(", start + 1)
        self.assertEqual(seen, 3)
        upstream = (FIXTURE / "src/boards/LimeSDR_Micro/LA9310_TRX.cpp").read_text(encoding="utf-8")
        self.assertEqual(upstream.count("return StreamTxTemplate(samples, count, meta, chrono::microseconds("), 3)

    def test_only_the_micro_board_and_its_factory_are_built(self):
        def pcie_block(text):
            block = text[text.index("if(LIMESUITENG_PCIE)\n") + len("if(LIMESUITENG_PCIE)\n"):]
            block = block[:block.index("endif()")]
            return [line.strip() for line in block.split("\n") if line.strip() and not line.strip().startswith("#")]
        self.assertEqual(pcie_block(self.files["src/boards/CMakeLists.txt"]),
                         ["target_sources(limesuiteng PRIVATE DeviceFactoryLA9310.cpp)", "add_subdirectory(LimeSDR_Micro)"])
        upstream = pcie_block((FIXTURE / "src/boards/CMakeLists.txt").read_text(encoding="utf-8"))
        self.assertLessEqual({"add_subdirectory(LimeSDR_X3)", "add_subdirectory(LimeSDR_XTRX)", "add_subdirectory(MMX8)",
                              "add_subdirectory(sSDR)"}, set(upstream))
        loader = [line.strip() for line in body(self.files["src/boards/BoardSupportLoader.in.cpp"], "void __loadBoardSupport()").split("\n")]
        self.assertNotIn("__loadDeviceFactoryPCIe();", loader)
        self.assertIn("__loadDeviceFactoryLA9310();", loader)
        self.assertNotRegex(self.files["src/boards/BoardSupportLoader.in.cpp"], r"@\w+@|\$\{")  # configure_file substitutes nothing new


class LimeExportAllowlistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exports = json.loads(EXPORTS.read_text(encoding="utf-8"))
        cls.recipe = json.loads(RECIPE.read_text(encoding="utf-8"))

    def test_lists_are_the_reviewed_draft(self):
        self.assertEqual((self.exports["kind"], self.exports["status"], self.exports["hardware_ready"]),
                         ("srrx_limesuiteng_export_allowlist", "AUDIT_DRAFT_CI_CHECKED", False))
        self.assertEqual(set(self.exports["files"]), {LIB_FILE, SOAPY_FILE})
        for entry in self.exports["files"].values():
            self.assertEqual(entry["defined"], sorted(set(entry["defined"])))
        imports = self.exports["files"][SOAPY_FILE]["imports_from_liblimesuiteng"]
        self.assertEqual(imports, sorted(set(imports)))
        self.assertLessEqual(set(imports), set(self.exports["files"][LIB_FILE]["defined"]))

    def test_recipe_export_counts_follow_the_lists_and_cover_every_symbol(self):
        counts = [c for c in self.recipe["checks"] if c["kind"] == "export_count"]
        self.assertGreaterEqual(len(counts), 20)
        for check in counts:
            symbols = self.exports["files"][check["file"]]["defined"]
            self.assertEqual(sum(s.startswith(check["prefix"]) for s in symbols), check["equals"], check["prefix"])
        for name, entry in self.exports["files"].items():
            prefixes = {c["prefix"] for c in counts if c["file"] == name}
            self.assertIn("_Z", prefixes, name)
            self.assertEqual(set(s for s in entry["defined"] if not s.startswith("_Z")) - prefixes, set(), name)
        for name in ("LMS7002M", "LimeSDR_Micro", "MCU_BD", "LA9310_PCIe", "LA9310_IQStreamer", "VSPA_mailbox", "LimePCIe"):
            self.assertIn("_ZN4lime%d%s" % (len(name), name), {c["prefix"] for c in counts if c["file"] == LIB_FILE})

    def test_every_exported_lime_name_is_reviewed_in_section_l(self):
        text = section_l()
        names = lime_names(self.exports["files"][LIB_FILE]["defined"])
        self.assertGreaterEqual(len(names), 40)
        for name in sorted(names):
            self.assertRegex(text, r"`%s`|\b%s\b" % (re.escape(name), re.escape(name)), name)
        for symbol in self.exports["files"][LIB_FILE]["defined"]:
            if not symbol.startswith("_Z"):
                self.assertIn(symbol, AUDIT.read_text(encoding="utf-8"))

    def test_soapy_module_reaches_no_raw_access_class(self):
        forbidden = next(c["substrings"] for c in self.recipe["checks"]
                         if c["kind"] == "forbid_strings" and c["file"] == SOAPY_FILE)
        for name in ("LMS7002M", "LimeSDR_Micro", "MCU_BD", "LA9310", "LA9310_PCIe", "LA9310_IQStreamer", "LA9310_FW_Impl",
                     "VSPA_mailbox", "PHYTimer", "PHYTimerControl", "LimePCIe"):
            self.assertIn("%d%s" % (len(name), name), forbidden, name)
        entry = self.exports["files"][SOAPY_FILE]
        for symbol in entry["imports_from_liblimesuiteng"] + entry["defined"]:
            for text in forbidden:
                self.assertNotIn(text.lower(), symbol.lower(), symbol)
        self.assertEqual(lime_names(entry["imports_from_liblimesuiteng"]),
                         {"DeviceHandle", "DeviceRegistry", "StreamConfig", "Timespec", "ToEnumClass", "ToString",
                          "registerLogHandler", "GetLastErrorMessage", "GetLastErrorMessageCString"})
        removed = next(c["substrings"] for c in self.recipe["checks"] if c["kind"] == "forbid_strings" and c["file"] == LIB_FILE)
        for board in ("LimeSDR_X3", "LimeSDR_XTRX", "LimeSDR_MMX8", "sSDR", "DeviceFactoryPCIe"):
            self.assertIn("N4lime%d%sE" % (len(board), board), removed)


# W2 SW-LIME-2 review fixes: the whole export count of each file is pinned (a new extern "C" export
# fails the build too), section H names both kernel modules of drivers/linux/la9310_limesdr, and
# recipes/limesuiteng/export_lists.py rebuilds exports.json from the CI .deb files.
EXPORT_LISTS = HERE / "recipes/limesuiteng/export_lists.py"


def load_export_lists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("srrx_lime_export_lists", EXPORT_LISTS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tiny_elf(symbols):
    """A little-endian ELF64 file with one .dynsym: [(name, defined)]."""
    import struct
    dynstr = b"\0" + b"".join(name.encode() + b"\0" for name, _ in symbols)
    entries, offset = [bytes(24)], 1
    for name, defined in symbols:
        entries.append(struct.pack("<IBBHQQ", offset, 0x12, 0, 12 if defined else 0, 0, 0))
        offset += len(name) + 1
    dynsym, shstr = b"".join(entries), b"\0.dynstr\0.dynsym\0.shstrtab\0"
    at_dynsym = 64 + len(dynstr)
    at_shstr = at_dynsym + len(dynsym)
    shoff = at_shstr + len(shstr)
    header = b"\x7fELF\x02\x01\x01" + bytes(9) + struct.pack("<HHIQQQIHHHHHH", 3, 183, 1, 0, 0, shoff, 0, 64, 0, 0, 64, 4, 3)

    def section(name, kind, at, size, link, entsize):
        return struct.pack("<IIQQQQIIQQ", name, kind, 0, 0, at, size, link, 0, 1, entsize)
    return (header + dynstr + dynsym + shstr + section(0, 0, 0, 0, 0, 0) + section(1, 3, 64, len(dynstr), 0, 0)
            + section(9, 11, at_dynsym, len(dynsym), 1, 24) + section(17, 3, at_shstr, len(shstr), 0, 0))


def tiny_deb(files):
    """An ar .deb with debian-binary and a data.tar.xz holding {path: bytes} as ./path."""
    import io
    import tarfile
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:xz") as tar:
        for path, content in files.items():
            info = tarfile.TarInfo("./" + path)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    out = b"!<arch>\n"
    for name, content in (("debian-binary", b"2.0\n"), ("data.tar.xz", data.getvalue())):
        out += ("%-16s%-12d%-6d%-6d%-8s%-10d`\n" % (name, 0, 0, 0, "100644", len(content))).encode() + content
        out += b"\n" if len(content) % 2 else b""
    return out


class LimeExportTotalTests(unittest.TestCase):
    def test_each_file_pins_its_whole_export_count(self):
        exports = json.loads(EXPORTS.read_text(encoding="utf-8"))
        recipe = json.loads(RECIPE.read_text(encoding="utf-8"))
        for name, entry in exports["files"].items():
            totals = [c for c in recipe["checks"] if c["kind"] == "export_count" and c["file"] == name and c["prefix"] == ""]
            self.assertEqual(len(totals), 1, name)
            self.assertEqual(totals[0]["equals"], len(entry["defined"]), name)
        self.assertEqual({len(e["defined"]) for e in exports["files"].values()}, {753, 14})

    def test_section_h_names_the_uart_module_and_its_tty_node(self):
        text = AUDIT.read_text(encoding="utf-8")
        section = text[text.index("### H. "):text.index("### I. ")]
        for name in ("la9310_uart_module", "ttyLA9310_UART", "la9310-uart", "dialout"):
            self.assertIn(name, section, name)
        rows = {row["id"]: row for row in part2_rows()}
        self.assertEqual((rows["H-06"]["file"], rows["H-06"]["verdict"]), ("drivers/linux/la9310_limesdr/la9310_uart.c", "open"))
        for row_id in ("F-12", "G-11", "K-04"):  # no compiled caller: blocked by the document's own definition
            self.assertEqual(rows[row_id]["verdict"], "blocked", row_id)


class LimeExportListsScriptTests(unittest.TestCase):
    def setUp(self):
        self.script = load_export_lists()

    def test_lists_come_from_the_deb_dynsym(self):
        lib = tiny_deb({self.script.LIB_FILE: tiny_elf([("_ZN4lime4TypeEv", True), ("c_entry", True), ("memcpy", False)])})
        soapy = tiny_deb({self.script.SOAPY_FILE: tiny_elf([("_ZNSt4copyEv", True), ("_ZN4lime4TypeEv", False),
                                                            ("strlen", False)])})
        self.assertEqual(self.script.lists([soapy, lib]),
                         {self.script.LIB_FILE: {"defined": ["_ZN4lime4TypeEv", "c_entry"]},
                          self.script.SOAPY_FILE: {"defined": ["_ZNSt4copyEv"], "imports_from_liblimesuiteng": ["_ZN4lime4TypeEv"]}})
        with self.assertRaises(ValueError):
            self.script.lists([lib])  # the module is missing
        with self.assertRaises(ValueError):
            self.script.lists([lib, lib, soapy])  # the library twice

    def test_differences_name_every_added_and_removed_symbol(self):
        exports = json.loads(EXPORTS.read_text(encoding="utf-8"))
        same = {path: {key: entry[key] for key in ("defined", "imports_from_liblimesuiteng") if key in entry}
                for path, entry in exports["files"].items()}
        self.assertEqual(self.script.differences(exports, same), [])
        changed = json.loads(json.dumps(same))
        changed[LIB_FILE]["defined"] = changed[LIB_FILE]["defined"][1:] + ["srrx_raw_write"]
        diff = self.script.differences(exports, changed)
        self.assertIn("+ %s defined srrx_raw_write" % LIB_FILE, diff)
        self.assertEqual(len(diff), 2)

    def test_exports_json_is_in_the_format_write_produces(self):
        text = EXPORTS.read_text(encoding="utf-8")
        self.assertEqual(json.dumps(json.loads(text), indent=2, ensure_ascii=False) + "\n", text)
        self.assertIn("export_lists.py", json.loads(text)["source"])


if __name__ == "__main__":
    unittest.main()
