"""inventory.json refresh: graph-derived fields only; partition/model/coverage fields are never written."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("srrx_refresh_inventory", PROJECT / "deployment/module_lab/refresh_inventory.py")
refresh = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(refresh)


class RefreshInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="srrx-inventory-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.text = refresh.INVENTORY.read_bytes().decode("utf-8")
        for relative in json.loads(self.text)["source_snapshots"]:
            (self.root / relative).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJECT / relative, self.root / relative)
        self.inventory = self.root / "inventory.json"
        self.inventory.write_bytes(self.text.encode("utf-8"))

    def main(self, *extra):
        with contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            code = refresh.main(["--project", str(self.root), "--inventory", str(self.inventory), *extra])
        return code, out.getvalue() + err.getvalue()

    def edit(self, sheet, change):
        path = self.root / "design" / (sheet + ".json")
        graph = json.loads(path.read_text(encoding="utf-8"))
        change({c["ref"]: c for c in graph["components"]}, graph)
        path.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")

    def test_committed_inventory_is_current(self):
        new, changed = refresh.refresh(PROJECT, refresh.strict_json(self.text))
        self.assertEqual(changed, [], "inventory.json is stale: run python3 deployment/module_lab/refresh_inventory.py")
        self.assertEqual(refresh.encode(new), self.text)

    def test_graph_edit_rewrites_only_the_copied_fields(self):
        def change(comps, graph):
            comps["C109"]["value"] = "100µF35VlowESR (refresh fixture)"
            comps["U108"]["notes"] = ["Refresh fixture note."]
            comps["U108"].pop("description", None)
            graph["open_items"][0]["description"] = "Refresh fixture gate text."
        self.edit("E1", change)
        before = json.loads(self.text)
        self.assertEqual(self.main("--check")[0], 1)
        self.assertEqual(self.inventory.read_bytes().decode("utf-8"), self.text, "--check must not write")
        code, output = self.main()
        self.assertEqual(code, 0, output)
        written = self.inventory.read_bytes().decode("utf-8")
        after = json.loads(written)
        self.assertEqual(written, json.dumps(after, ensure_ascii=False, indent=2) + "\n")
        self.assertEqual(self.main("--check")[0], 0)
        u108 = next(x for x in after["subinterfaces"] if x["ref"] == "U108")
        self.assertEqual((u108["source_notes"], u108["source_description"]), (["Refresh fixture note."], ""))
        e1 = [a for a in after["assemblies"] if a["sheet"] == "E1"]
        self.assertTrue(all(a["sheet_hardware_gates"][0]["description"] == "Refresh fixture gate text." for a in e1))
        self.assertIn({"ref": "C109", "kind": "capacitor", "value": "100µF35VlowESR (refresh fixture)", "status": "design"},
                      next(a for a in e1 if "C109" in a["refs"])["passive_parameters"])
        self.assertNotEqual(after["source_snapshots"]["design/E1.json"], before["source_snapshots"]["design/E1.json"])
        self.assertEqual(after["source_snapshots"]["design/E1.json"], refresh.snapshot(self.root / "design/E1.json"))
        self.assertEqual(after["source_snapshots"]["STACK.md"], refresh.snapshot(self.root / "STACK.md"))
        # Hand-maintained partition, model and coverage fields are byte-identical.
        for key in ("catalogue_only_entities", "catalogue_source_index", "unknown_or_non_software_interfaces",
                    "critical_constraints", "implementation_coverage_status", "purpose", "source_priority"):
            self.assertEqual(after[key], before[key], key)
        for old, new in zip(before["subinterfaces"] + before["assemblies"], after["subinterfaces"] + after["assemblies"]):
            for key in ("module_id", "refs", "interface_family", "interface_signals", "configuration_from_source", "pinout_status",
                        "pinout_gate", "coverage_constraints", "protocol_fidelity_boundary", "model_boundary",
                        "required_model_behaviors", "protocol_or_special_subinterfaces", "commercial_or_functional_module_refs"):
                self.assertEqual(old.get(key), new.get(key), key)

    def test_changed_ref_set_or_class_is_refused_without_writing(self):
        added = lambda comps, graph: graph["components"].append(
            {"ref": "R1999", "value": "10k", "kind": "resistor", "group": "LAB5", "status": "design", "source": "fixture",
             "pins": [{"number": "1", "name": "1", "type": "passive", "net": "GND"}, {"number": "2", "name": "2", "type": "passive", "nc": True}]})
        removed = lambda comps, graph: graph["components"].remove(comps["C109"])
        reclassed = lambda comps, graph: comps["C109"].update(kind="ic")
        regrouped = lambda comps, graph: comps["C109"].update(group="Refresh fixture split")
        renamed = lambda comps, graph: [p.update(net="E1_CELL1_RENAMED") for p in comps["BT101"]["pins"] if p.get("net") == "E1_CELL1"]
        for change, message in ((added, "ref set changed"), (removed, "ref set changed"), (reclassed, "class changed"),
                                (regrouped, "spans graph groups"), (renamed, "interface_signals of BT101")):
            with self.subTest(message=message):
                saved = (self.root / "design/E1.json").read_bytes()
                self.edit("E1", change)
                with self.assertRaisesRegex(refresh.RefreshError, message):
                    refresh.refresh(self.root, json.loads(self.text))
                code, output = self.main()
                self.assertEqual((code, "REFUSED" in output), (2, True))
                self.assertEqual(self.inventory.read_bytes().decode("utf-8"), self.text)
                (self.root / "design/E1.json").write_bytes(saved)

    def test_guard_refuses_any_hand_maintained_change(self):
        old = json.loads(self.text)
        for mutate in (lambda inv: inv["subinterfaces"][0]["coverage_constraints"].append("x"),
                       lambda inv: inv["assemblies"][0]["model_boundary"].upper(),
                       lambda inv: inv["assemblies"][0].update(model_boundary="changed"),
                       lambda inv: inv["scope"].update(detailed_subinterfaces=0),
                       lambda inv: inv["catalogue_only_entities"].pop(),
                       lambda inv: inv["subinterfaces"][0]["sources"].append({"path": "x"})):
            new = copy.deepcopy(old)
            mutate(new)
            if new == old:
                continue
            with self.subTest(mutate=mutate), self.assertRaisesRegex(refresh.RefreshError, "refused|count changed"):
                refresh.guard(old, new)


if __name__ == "__main__":
    unittest.main()
