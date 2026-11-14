"""Where NX Porting Kit keeps things. Set NXPK_HOME to move all of it (tests use this, never the real folder)."""
import os
import sys

APP_VERSION = "1.0.0"
APP_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def home() -> str:
    root = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    base = os.environ.get("NXPK_HOME") or os.path.join(root, "NX Porting Kit")
    os.makedirs(base, exist_ok=True)
    return base


def sub(name: str) -> str:
    p = os.path.join(home(), name)
    os.makedirs(p, exist_ok=True)
    return p


def ports_dir() -> str:      # downloaded or user-added ports (each a folder with port.json)
    return sub("ports")


def cache_dir() -> str:      # downloaded release assets, kept between runs
    return sub("cache")


def work_dir() -> str:       # scratch space for one run, emptied at the start of the next
    return sub("work")


def secure_dir() -> str:     # prod.keys lives here, readable by this Windows user only
    return sub("secure")


def tools_dir() -> str:      # tools the user or a port dropped in (node.exe, hacbrewpack.exe)
    return sub("tools")


def settings_file() -> str:
    return os.path.join(home(), "settings.json")


def bundled(*parts: str) -> str:
    return os.path.join(APP_DIR, *parts)
