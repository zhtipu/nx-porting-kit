"""The game library.

Three sources, merged by id (later wins):
  1. ports bundled with the app            <app>/ports/<id>/port.json
  2. the catalog on GitHub (games.json)    each entry points at a port.json; cached under ports/<id>/
  3. ports the user dropped in             %LOCALAPPDATA%/NX Porting Kit/ports/<id>/port.json

Adding a game never touches the app: add a folder with a port.json (or a catalog entry that points at one).
A port may need a newer app than the one running (it names a step type the app does not know, or says
`requires_app`). Such a port still shows in the library, flagged "needs update".
"""
import json
import os

from . import net, paths, settings
from .steps import KNOWN_STEPS

STATUSES = ("stable", "beta", "soon")
CATALOG_URL = "https://raw.githubusercontent.com/zhtipu/nx-porting-kit-catalog/main/games.json"  # built in, never shown


def _ver(s: str) -> tuple:
    out = []
    for part in str(s).split("."):
        try:
            out.append(int(part))
        except ValueError:
            out.append(0)
    return tuple(out)


def _read(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _validate(m: dict) -> dict:
    """Fills defaults and records why a port cannot run here (m['blocked'])."""
    m.setdefault("name", m.get("id", "?"))
    m.setdefault("status", "stable")
    if m["status"] not in STATUSES:
        m["status"] = "beta"
    m.setdefault("steps", [])
    m.setdefault("tagline", "")
    m.setdefault("accent", "")
    reasons = []
    if _ver(m.get("requires_app", "0")) > _ver(paths.APP_VERSION):
        reasons.append(f"needs NX Porting Kit {m['requires_app']} or newer")
    unknown = sorted({s.get("type", "?") for s in m["steps"]} - KNOWN_STEPS)
    if unknown:
        reasons.append("uses a step this version does not have (" + ", ".join(unknown) + ")")
    m["blocked"] = "; ".join(reasons)
    return m


def _load_folder(root: str, out: dict) -> None:
    if not os.path.isdir(root):
        return
    for name in sorted(os.listdir(root)):
        folder = os.path.join(root, name)
        m = _read(os.path.join(folder, "port.json"))
        if not isinstance(m, dict) or not m.get("id"):
            continue
        m["_dir"] = folder
        out[m["id"]] = _validate(m)


def refresh_remote(force: bool = False) -> dict:
    """Fetches games.json and the port.json of each entry into ports/<id>/.
    Returns {ok, new: [names], updated: [names], error}. `force` ignores the auto-check setting (the button)."""
    if os.environ.get("NXPK_OFFLINE"):
        return {"ok": False, "new": [], "updated": [], "error": "Offline mode."}
    if not force and not settings.load().get("check_catalog"):
        return {"ok": True, "new": [], "updated": [], "error": ""}
    try:
        cat = net.get_json(CATALOG_URL, timeout=6)
    except net.NetError:
        return {"ok": False, "new": [], "updated": [],
                "error": "Could not reach the game list. Check your connection and try again."}
    known = {p["id"]: p.get("version", "") for p in load_all()}
    new, updated = [], []
    for g in cat.get("games", []):
        gid, url = g.get("id"), g.get("manifest_url")
        if not gid or not url:
            continue
        try:
            m = net.get_json(url, timeout=8)
        except net.NetError:
            continue
        folder = os.path.join(paths.ports_dir(), gid)
        os.makedirs(folder, exist_ok=True)
        if m.get("icon_url"):
            ext = os.path.splitext(m["icon_url"])[1] or ".png"
            try:
                net.download(m["icon_url"], os.path.join(folder, "icon" + ext))
                m["icon"] = "icon" + ext
            except net.NetError:
                pass
        with open(os.path.join(folder, "port.json"), "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2)
        name = m.get("name", gid)
        if gid not in known:
            new.append(name)
        elif known[gid] != m.get("version", ""):
            updated.append(name)
    return {"ok": True, "new": new, "updated": updated, "error": ""}


def load_all() -> list:
    found: dict = {}
    _load_folder(paths.bundled("ports"), found)
    _load_folder(paths.ports_dir(), found)
    return sorted(found.values(), key=lambda m: (m.get("order", 100), m["name"].lower()))


def public_view(m: dict) -> dict:
    """What the UI gets: no step internals, an icon URL it can show."""
    icon = ""
    if m.get("icon"):
        p = os.path.join(m["_dir"], m["icon"])
        if os.path.isfile(p):
            icon = "file:///" + p.replace("\\", "/")
    return {
        "id": m["id"], "name": m["name"], "tagline": m["tagline"], "status": m["status"],
        "version": m.get("version", ""), "accent": m["accent"], "icon": icon, "blocked": m["blocked"],
        "input": m.get("input", {}), "about": m.get("about", ""), "notes": m.get("notes", []),
        "outputs": m.get("outputs_help", ""),
        "steps": [t for t, _, _ in __import__("nxportingkit.runner", fromlist=["x"]).group_steps(m["steps"])],
        "needs_keys": any(s.get("type") == "pack_nsp" for s in m["steps"]),
    }
