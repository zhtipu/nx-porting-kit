"""unzip and copy: plain file steps."""
import os
import shutil
import zipfile

from . import StepError, step
from .fetch import safe_extract


@step("unzip")
def unzip(s: dict, ctx) -> None:
    src, dest = ctx.path(s["src"]), ctx.path(s["dest"])
    if not os.path.isfile(src):
        raise StepError("A file an earlier step should have made is missing.")
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(src) as zf:
        n = safe_extract(zf, dest, strip=int(s.get("strip", 0)))
    ctx.log(f"Unpacked {n} files")


def _transfer(src: str, dst: str, move: bool) -> None:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst):
        os.remove(dst)
    if move:
        shutil.move(src, dst)
        return
    try:
        os.link(src, dst)           # big game packs: no second copy when both are on one drive
    except OSError:
        shutil.copyfile(src, dst)


@step("copy")
def copy(s: dict, ctx) -> None:
    pairs = s.get("files") or [{"from": s["from"], "to": s["to"]}]
    for p in pairs:
        src, dst = ctx.path(p["from"]), ctx.path(p["to"])
        if not os.path.isfile(src):
            raise StepError(f"Missing file: {os.path.basename(src)}")
        _transfer(src, dst, bool(s.get("move")))
        ctx.log(f"{os.path.basename(src)} -> {os.path.relpath(dst, ctx.work) if dst.startswith(ctx.work) else dst}")
