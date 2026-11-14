"""App updates from the app's own GitHub releases.

A release tagged vX.Y.Z carries NXPortingKit.zip (the folder PyInstaller makes) and, optionally, NXPortingKit.zip.sha256.
Update flow (installed build only): download, check the hash, unpack beside the app, then a tiny PowerShell script
waits for the app to exit, copies the new files over the old and starts the app again.
"""
import os
import re
import subprocess
import sys
import urllib.request
import zipfile

from . import net, paths

REPO = "zhtipu/nx-porting-kit"
ASSET = "NXPortingKit.zip"


def _ver(s: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"[0-9]+", str(s))[:4])


def frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def check() -> dict:
    """{ok, available, version, notes, can_install, error}"""
    if os.environ.get("NXPK_OFFLINE"):
        return {"ok": False, "available": False, "error": "Offline mode."}
    tag, notes, has_asset = "", "", True
    try:
        rel = net.get_json(f"https://api.github.com/repos/{REPO}/releases/latest", timeout=8)
        tag = rel.get("tag_name", "")
        notes = (rel.get("body") or "").strip()[:600]
        has_asset = any(a.get("name") == ASSET for a in rel.get("assets", []))
    except net.NetError:
        try:                                   # the anonymous API can be rate limited: use the plain redirect
            tag = net.latest_tag(REPO)
        except net.NetError:
            return {"ok": False, "available": False, "error": "Could not check for updates right now."}
    newer = _ver(tag) > _ver(paths.APP_VERSION)
    return {"ok": True, "available": bool(newer and has_asset), "version": tag.lstrip("v"),
            "notes": notes, "can_install": frozen(), "error": ""}


def download_and_apply(progress, cancel=None) -> None:
    """Downloads the newest release and starts the swap script. The caller then quits the app."""
    if not frozen():
        raise net.NetError("Updating is not available in this build.")
    sha = None
    try:
        with urllib.request.urlopen(net.release_asset_url(REPO, "latest", ASSET + ".sha256"), timeout=15) as r:
            m = re.search(r"[0-9a-fA-F]{64}", r.read().decode("ascii", "ignore"))
            sha = m.group(0) if m else None
    except Exception:  # noqa: BLE001  (the hash file is optional)
        pass
    zpath = os.path.join(paths.cache_dir(), "NXPortingKit-update.zip")
    net.download(net.release_asset_url(REPO, "latest", ASSET), zpath, progress, cancel, sha)

    new_dir = os.path.join(paths.cache_dir(), "update_new")
    net.clear_dir(new_dir)
    base = os.path.abspath(new_dir)
    with zipfile.ZipFile(zpath) as zf:
        for info in zf.infolist():
            target = os.path.abspath(os.path.join(base, info.filename))
            if target != base and not target.startswith(base + os.sep):
                raise net.NetError("The update file is not safe to unpack. Nothing was changed.")
        zf.extractall(new_dir)
    src = new_dir
    if not os.path.isfile(os.path.join(src, "NXPortingKit.exe")):
        subdirs = [d for d in os.listdir(new_dir) if os.path.isdir(os.path.join(new_dir, d))]
        if len(subdirs) == 1:
            src = os.path.join(new_dir, subdirs[0])
    if not os.path.isfile(os.path.join(src, "NXPortingKit.exe")):
        raise net.NetError("The update file does not contain the app.")

    install = os.path.dirname(sys.executable)
    script = os.path.join(paths.cache_dir(), "apply_update.ps1")
    with open(script, "w", encoding="utf-8") as f:
        f.write(
            f"try {{ Wait-Process -Id {os.getpid()} -Timeout 60 -ErrorAction SilentlyContinue }} catch {{}}\n"
            f"Start-Sleep -Milliseconds 400\n"
            f"robocopy '{src}' '{install}' /E /NFL /NDL /NJH /NJS /NP | Out-Null\n"
            f"Start-Process -FilePath '{os.path.join(install, 'NXPortingKit.exe')}'\n")
    subprocess.Popen(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden",
                      "-File", script], creationflags=0x08000000 | 0x00000008, close_fds=True)
