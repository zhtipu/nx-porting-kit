"""Looks at what the user picked and says whether it is the game this port needs. Read-only, fast."""
import os
import struct

STFS_MAGICS = (b"CON ", b"LIVE", b"PIRS")


def read_stfs_header(path: str):
    try:
        with open(path, "rb") as f:
            head = f.read(0x600)
    except OSError:
        return None
    if len(head) < 0x500 or head[:4] not in STFS_MAGICS:
        return None
    title_id = struct.unpack(">I", head[0x360:0x364])[0]
    name = head[0x411:0x411 + 0x80].decode("utf-16-be", errors="ignore").split("\0")[0]
    return {"title_id": f"{title_id:08X}", "name": name}


def _walk(root: str, depth: int):
    root = os.path.abspath(root)
    base = root.count(os.sep)
    for d, dirs, files in os.walk(root):
        if d.count(os.sep) - base >= depth:
            dirs[:] = []
        yield d, files


def inspect(path: str, spec: dict) -> dict:
    """spec = the port's "input": {"title_ids": ["5841120C"], ...}. Returns {ok, kind, label, error}."""
    wanted = {t.upper() for t in spec.get("title_ids", [])}
    if not path or not os.path.exists(path):
        return {"ok": False, "error": "Pick the game's package file or its extracted folder."}

    if os.path.isfile(path):
        h = read_stfs_header(path)
        if not h:
            return {"ok": False, "error": "That is not an Xbox 360 content package."}
        if wanted and h["title_id"] not in wanted:
            return {"ok": False, "error": f"That package is {h['name'] or h['title_id']}, not this game."}
        return {"ok": True, "kind": "package", "label": h["name"] or os.path.basename(path)}

    other = []
    seen = 0
    for d, files in _walk(path, 3):
        if any(f.lower() == "default.xex" for f in files):
            return {"ok": True, "kind": "folder", "label": os.path.basename(d) or d}
        for f in files:
            if "." in f or seen > 256:
                continue
            full = os.path.join(d, f)
            try:
                if os.path.getsize(full) < 0xA000:
                    continue
            except OSError:
                continue
            seen += 1
            h = read_stfs_header(full)
            if not h:
                continue
            if not wanted or h["title_id"] in wanted:
                return {"ok": True, "kind": "package", "label": h["name"] or f, "path": full}
            other.append(h["name"] or h["title_id"])
    if other:
        return {"ok": False, "error": "This folder has " + ", ".join(sorted(set(other))[:3]) + " but not this game."}
    return {"ok": False, "error": "No game found there. Pick the package file or the folder that holds default.xex."}
