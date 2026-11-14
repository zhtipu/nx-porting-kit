"""pack_nsp: turn a loader, a game and its files into an installable NSP with hacBrewPack and the user's keys."""
import glob
import os
import re
import shutil

from .. import net, nsp, paths, settings
from . import StepError, step
from .filesystem import _transfer
from .tool import find_tool, run


def _safe_name(s: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "", s).strip()


@step("pack_nsp")
def pack_nsp(s: dict, ctx) -> None:
    meta = ctx.port.get("nsp") or {}
    for k in ("title", "title_id", "publisher"):
        if not meta.get(k):
            raise StepError("This port does not say how to name its NSP.")
    if not re.fullmatch(r"[0-9A-Fa-f]{16}", meta["title_id"]):
        raise StepError("This port has an invalid title ID.")
    if not settings.keys_present():
        raise StepError("prod.keys is not set up yet. Add it in Settings.")
    exe = find_tool("hacbrewpack")
    if not exe:
        raise StepError("A required component is missing. Reinstall NX Porting Kit.")

    exefs, romfs = s.get("exefs", {}), s.get("romfs", [])
    stage = os.path.join(ctx.work, "nsp_stage")
    net.clear_dir(stage)
    for d in ("exefs", "romfs", "control", "out"):
        os.makedirs(os.path.join(stage, d), exist_ok=True)

    for key, name in (("main", "main"), ("npdm", "main.npdm")):
        src = ctx.path(exefs[key])
        if not os.path.isfile(src):
            raise StepError("The loader files are missing.")
        shutil.copyfile(src, os.path.join(stage, "exefs", name))   # hacbrewpack edits the npdm in place
    total = 0
    for item in romfs:
        src = ctx.path(item["from"])
        if not os.path.isfile(src):
            raise StepError(f"Missing file for the NSP: {os.path.basename(src)}")
        _transfer(src, os.path.join(stage, "romfs", item["to"]), False)
        total += os.path.getsize(src)
    ctx.log(f"NSP contents: {len(romfs)} files, {total / 1e6:.0f} MB")

    icon = ctx.path(s["icon"]) if s.get("icon") else os.path.join(ctx.port["_dir"], ctx.port.get("icon", "icon.png"))
    if not os.path.isfile(icon):
        raise StepError("The port has no icon for the HOME Menu.")
    nsp.write_control(os.path.join(stage, "control"), icon, meta["title"], meta["publisher"],
                      meta.get("version") or ctx.port.get("version", "1.0.0"), meta["title_id"])

    ctx.log("Packing the NSP. This takes a few minutes for a large game.")
    ctx.progress(-1, "Packing")
    run([exe, "--keyset", settings.keys_path(), "--titleid", meta["title_id"].lower(), "--exefsdir", "exefs",
         "--romfsdir", "romfs", "--controldir", "control", "--nologo", "--nspdir", "out", "--ncadir", "nca",
         "--tempdir", "temp", "--backupdir", "backup"], stage, ctx, "hacBrewPack")

    built = glob.glob(os.path.join(stage, "out", "*.nsp"))
    if not built:
        raise StepError("Packing finished but no NSP came out. Check that prod.keys is complete and current.")
    os.makedirs(ctx.out, exist_ok=True)
    version = _safe_name(str(meta.get("version") or ctx.port.get("version", "1.0.0")))
    final = os.path.join(ctx.out, f"{_safe_name(meta['title'])} [{meta['title_id'].upper()}][v{version}].nsp")
    if os.path.exists(final):
        os.remove(final)
    shutil.move(built[0], final)
    ctx.vars["nsp"] = final
    ctx.log(f"NSP ready: {final} ({os.path.getsize(final) / 1e6:.0f} MB)")
    shutil.rmtree(stage, ignore_errors=True)
