"""Parameter loading. JSON only, so the generators need no YAML parser."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARAMS = ROOT / "params"


def load(name):
    return json.loads((PARAMS / name).read_text(encoding="utf-8"))


class Params:
    """All parameter files of one build, loaded once."""

    def __init__(self):
        self.mech = load("mechanical.json")
        self.parts = load("parts.json")["parts"]
        self.boards = load("boards.json")
        self.antennas = load("antennas.json")
        self.imu = load("imu_pack.json")
        self.vendor = load("vendor-models.json")

    @property
    def outer(self):
        o = self.mech["outer"]
        return o["w"], o["h"], o["d"]

    def files(self):
        """Parameter files with their bytes, for the manifest."""
        return {p.name: p.read_bytes() for p in sorted(PARAMS.glob("*.json"))}
