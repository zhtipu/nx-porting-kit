"""Downloads. GitHub release assets and archives, SHA-256 checked, cached by name."""
import hashlib
import json
import os
import re
import shutil
import urllib.request

from . import paths
from .fsutil import safe_replace

UA = "NXPortingKit/" + paths.APP_VERSION
CHUNK = 1 << 20


class NetError(RuntimeError):
    pass


def _dev_overrides() -> dict:
    """NXPK_DEV_ASSETS=<json file> maps "owner/repo/asset" to a local file, for testing without publishing."""
    p = os.environ.get("NXPK_DEV_ASSETS")
    if not p:
        return {}
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def dev_override(key: str):
    path = _dev_overrides().get(key)
    return path if path and os.path.isfile(path) else None


def get_json(url: str, timeout: float = 8.0):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        raise NetError(f"Could not reach {_host(url)} ({type(e).__name__}).") from e


def _host(url: str) -> str:
    m = re.match(r"https?://([^/]+)", url)
    return m.group(1) if m else url


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(CHUNK)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def download(url: str, dest: str, progress=None, cancel=None, sha256: str | None = None) -> str:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(req, timeout=20) as r, open(tmp, "wb") as f:
            total = int(r.headers.get("Content-Length") or 0)
            done = 0
            while True:
                if cancel and cancel.is_set():
                    raise NetError("Cancelled.")
                b = r.read(CHUNK)
                if not b:
                    break
                f.write(b)
                h.update(b)
                done += len(b)
                if progress and total:
                    progress(done / total)
    except NetError:
        _rm(tmp)
        raise
    except Exception as e:  # noqa: BLE001
        _rm(tmp)
        raise NetError(f"Download failed from {_host(url)} ({type(e).__name__}).") from e
    if sha256 and h.hexdigest().lower() != sha256.lower():
        _rm(tmp)
        raise NetError("The downloaded file does not match its published checksum. Nothing was used.")
    safe_replace(tmp, dest)
    return dest


def _rm(p: str) -> None:
    try:
        os.remove(p)
    except OSError:
        pass


def release_asset_url(repo: str, tag: str, asset: str) -> str:
    api = f"https://api.github.com/repos/{repo}/releases/" + ("latest" if tag in ("", "latest") else f"tags/{tag}")
    rel = get_json(api)
    for a in rel.get("assets", []):
        if a.get("name") == asset:
            return a["browser_download_url"]
    raise NetError(f"{repo} has no release file named {asset}.")


def fetch_cached(key: str, resolve_url, dest_name: str, progress=None, cancel=None, sha256=None) -> str:
    """Returns a local path. A dev override wins; then the cache (when the checksum matches); then the network."""
    local = dev_override(key)
    if local:
        return local
    dest = os.path.join(paths.cache_dir(), re.sub(r"[^A-Za-z0-9._-]+", "_", key) + "__" + dest_name)
    if os.path.isfile(dest) and sha256 and sha256_file(dest).lower() == sha256.lower():
        return dest
    return download(resolve_url(), dest, progress, cancel, sha256)


def clear_dir(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)
