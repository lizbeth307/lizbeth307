"""Fetch pinned vendor STEP files (never committed) and cross-check the model envelopes against them."""
import hashlib
import io
import urllib.request
import zipfile
from pathlib import Path

STEP_NAMES = {
    "usb_stack": "484060001", "rj45": "LPJG0926HENL", "hdmi": "HDMI_1_2_5_1", "audio": "AUDIO-SMD_PJ-332D-6A_AUDIO-SMD__ASM",
    "usb_c": "USB-16PIN-TYPEC", "header40": "1555298", "j21_3p": "HDR-TH_3P-P2_54-V-M_PZ254V-11-0_ASM",
    "soc": "BGA1287", "lpddr5": "BGA315",
}


def sha256(b):
    return hashlib.sha256(b).hexdigest()


def fetch(P, cache, download=True):
    """Return {model id: Path to the verified STEP}. Raises on any hash mismatch."""
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    out = {}
    for m in P.vendor["models"]:
        z = cache / (m["id"] + ".zip")
        if not z.exists():
            if not download:
                raise FileNotFoundError(f"{z} missing and downloads are disabled")
            req = urllib.request.Request(m["url"], headers={"User-Agent": "srrx-mech/1"})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if sha256(data) != m["sha256"]:
                raise RuntimeError(f"{m['id']}: archive SHA-256 {sha256(data)} != pinned {m['sha256']}")
            z.write_bytes(data)
        data = z.read_bytes()
        if sha256(data) != m["sha256"]:
            raise RuntimeError(f"{m['id']}: cached archive SHA-256 mismatch")
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            member = zf.read(m["member"])
        if sha256(member) != m["member_sha256"]:
            raise RuntimeError(f"{m['id']}: member SHA-256 mismatch")
        stp = cache / (m["id"] + ".stp")
        if not stp.exists() or sha256(stp.read_bytes()) != m["member_sha256"]:
            stp.write_bytes(member)
        out[m["id"]] = stp
    return out


def _walk(node, acc):
    acc.append(node)
    for k in list(getattr(node, "children", []) or []):
        _walk(k, acc)
    return acc


def _finite(bb):
    return all(abs(v) < 1e4 for v in (bb.min.X, bb.min.Y, bb.min.Z, bb.max.X, bb.max.Y, bb.max.Z))


def q6a_fit(P, step_path, tol=0.25):
    from build123d import import_step
    shape = import_step(str(step_path))
    nodes = _walk(shape, [])
    board = None
    for s in shape.solids():
        bb = s.bounding_box()
        if _finite(bb) and 84.5 < bb.size.X < 85.5 and 55.5 < bb.size.Y < 56.5 and 1.4 < bb.size.Z < 1.8:
            board = bb
            break
    if board is None:
        return {"result": "FAIL", "reason": "board solid (85 x 56 x 1.6) not found in the STEP"}
    ox, oy, top = board.min.X, board.min.Y, board.max.Z
    q = P.parts["q6a"]
    res = {"board_origin_in_step": [round(ox, 2), round(oy, 2)], "board_size": [round(board.size.X, 2), round(board.size.Y, 2), round(board.size.Z, 2)],
           "items": {}}
    zmax, zmin = top, board.min.Z
    for s in shape.solids():
        bb = s.bounding_box()
        if _finite(bb):
            zmax, zmin = max(zmax, bb.max.Z), min(zmin, bb.min.Z)
    res["top_max_above_board"] = round(zmax - top, 2)
    res["bottom_max_below_board"] = round(board.min.Z - zmin, 2)
    ok = True
    for key, name in STEP_NAMES.items():
        node = next((n for n in nodes if name in (getattr(n, "label", "") or "") and _finite(n.bounding_box())), None)
        if node is None:
            res["items"][key] = {"result": "NOT FOUND"}
            ok = False
            continue
        bb = node.bounding_box()
        uv = [round(bb.min.X - ox, 2), round(bb.min.Y - oy, 2), round(bb.max.X - ox, 2), round(bb.max.Y - oy, 2)]
        h = round(bb.max.Z - top, 2)
        want = q["connectors"].get(key) or q.get(key)
        d = max(abs(a - b) for a, b in zip(uv, want["uv"])) if want else None
        dh = abs(h - want["top"]) if want else None
        good = want is not None and d <= tol and dh <= tol
        ok = ok and good
        res["items"][key] = {"uv_step": uv, "top_step": h, "uv_params": want["uv"] if want else None, "top_params": want["top"] if want else None,
                             "result": "PASS (model vs vendor STEP)" if good else "FAIL (model vs vendor STEP)"}
    good = abs(res["top_max_above_board"] - q["top_max"]) <= tol and res["bottom_max_below_board"] <= q["bottom_max"] + tol
    res["heights"] = "PASS (model vs vendor STEP)" if good else "FAIL (model vs vendor STEP)"
    res["soc_top"] = res["items"].get("soc", {}).get("top_step")
    res["lpddr5_top"] = res["items"].get("lpddr5", {}).get("top_step")
    res["result"] = "PASS (model vs vendor STEP)" if ok and good else "FAIL (model vs vendor STEP)"
    return res
