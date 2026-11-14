"""fetch: pull a file from the port's GitHub (a release asset, or a repository archive)."""
import os
import shutil
import zipfile

from .. import net
from . import StepError, step

ALLOWED_REPO_OWNERS = None   # any public GitHub repo the manifest names; hosts are fixed to github.com below


def safe_extract(zf: zipfile.ZipFile, dest: str, strip: int = 0, select=None) -> int:
    n = 0
    base = os.path.abspath(dest)
    for info in zf.infolist():
        if info.is_dir():
            continue
        parts = info.filename.split("/")[strip:]
        if not parts or not parts[-1]:
            continue
        rel = "/".join(parts)
        if select and not any(rel.startswith(p) for p in select):
            continue
        target = os.path.abspath(os.path.join(base, *parts))
        if not (target == base or target.startswith(base + os.sep)):
            raise StepError("The archive has a file that would land outside its folder. Nothing was extracted.")
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with zf.open(info) as src, open(target, "wb") as out:
            shutil.copyfileobj(src, out, 1 << 20)
        n += 1
    return n


@step("fetch")
def fetch(s: dict, ctx) -> None:
    source = s.get("source", "release")
    repo = s.get("repo", "")
    if source not in ("release", "archive") or "/" not in repo:
        raise StepError("This port's download step is malformed.")
    dest = ctx.path(s["dest"])
    sha = s.get("sha256")
    prog = lambda v: ctx.progress(v, os.path.basename(dest))  # noqa: E731

    if source == "release":
        asset, tag = s["asset"], s.get("tag", "latest")
        ctx.log(f"Downloading {asset} from github.com/{repo}")
        path = net.fetch_cached(f"{repo}/{asset}", lambda: net.release_asset_url(repo, tag, asset), asset,
                                prog, ctx.cancel, sha)
    else:
        ref = s.get("ref", "main")
        ctx.log(f"Downloading source of github.com/{repo} ({ref})")
        key = f"{repo}@{ref}"
        path = net.fetch_cached(key, lambda: f"https://github.com/{repo}/archive/{ref}.zip", "src.zip", prog,
                                ctx.cancel, sha)

    if source == "archive" or s.get("unzip"):
        os.makedirs(dest, exist_ok=True)
        with zipfile.ZipFile(path) as zf:
            n = safe_extract(zf, dest, strip=int(s.get("strip", 1 if source == "archive" else 0)))
        ctx.log(f"Unpacked {n} files")
    else:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copyfile(path, dest)
    ctx.progress(-1, "")
