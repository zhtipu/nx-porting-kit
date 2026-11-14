"""Settings and the stored prod.keys."""
import getpass
import json
import os
import re
import shutil
import subprocess

from . import paths
from .fsutil import safe_replace

DEFAULTS = {
    "output_dir": "",
    "check_catalog": True,
}


def load() -> dict:
    data = dict(DEFAULTS)
    try:
        with open(paths.settings_file(), "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except (OSError, ValueError):
        pass
    if not data["output_dir"]:
        data["output_dir"] = os.path.join(os.path.expanduser("~"), "Documents", "NX Porting Kit")
    return data


def save(data: dict) -> None:
    keep = {k: data[k] for k in DEFAULTS if k in data}
    tmp = paths.settings_file() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(keep, f, indent=2)
    safe_replace(tmp, paths.settings_file())


# ---- prod.keys -------------------------------------------------------------------------------------------------
def keys_path() -> str:
    return os.path.join(paths.secure_dir(), "prod.keys")


def keys_present() -> bool:
    return os.path.isfile(keys_path())


def _looks_like_prod_keys(text: str) -> bool:
    names = set(re.findall(r"^\s*([a-z0-9_]+)\s*=", text, re.M | re.I))
    return "header_key" in names and any(n.startswith("master_key_") for n in names)


def import_keys(src: str) -> tuple[bool, str]:
    """Copies the user's own prod.keys into the secure folder. Never prints or returns key material."""
    try:
        with open(src, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read(2_000_000)
    except OSError as e:
        return False, f"Could not read that file ({e.strerror})."
    if not _looks_like_prod_keys(text):
        return False, "That does not look like a prod.keys file."
    dest = keys_path()
    shutil.copyfile(src, dest)
    _lock_down(dest)
    return True, "Keys saved. NX Porting Kit keeps its own copy and never shows it."


def _user_sid() -> str | None:
    try:
        out = subprocess.run(["whoami", "/user", "/fo", "csv", "/nh"], capture_output=True, text=True,
                             creationflags=0x08000000).stdout
    except OSError:
        return None
    m = re.search(r"S-1-[0-9-]+", out)
    return m.group(0) if m else None


def _lock_down(path: str) -> None:
    """Only this Windows user (and SYSTEM) may read the keys copy. Granted by SID, then read back: if the file
    is not readable afterwards the change is undone, so a bad ACL can never lock the user out of their own keys."""
    if os.name != "nt":
        os.chmod(path, 0o600)
        return
    sid = _user_sid()
    folder = os.path.dirname(path)
    if not sid:
        return
    run = lambda *a: subprocess.run(["icacls", *a], capture_output=True, check=False, creationflags=0x08000000)  # noqa: E731
    run(folder, "/grant:r", f"*{sid}:(OI)(CI)F", "*S-1-5-18:(OI)(CI)F")
    run(folder, "/inheritance:r")
    try:
        with open(path, "rb") as f:
            f.read(1)
    except OSError:
        run(folder, "/reset", "/t")


def remove_keys() -> None:
    try:
        os.remove(keys_path())
    except OSError:
        pass
