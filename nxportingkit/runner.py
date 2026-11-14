"""Runs a port's steps in order and reports in the event protocol OpSheet.qml renders:
plan, step (run|ok|skip|fail), log, progress, done."""
import os
import shutil
import threading
import time

from . import gamefile, net, settings
from .steps import REGISTRY, Skip, StepError
from .steps.context import Ctx


def preflight(port: dict, game: str, out_dir: str) -> str | None:
    """Returns a message when the run cannot start, else None."""
    if port.get("blocked"):
        return "This port " + port["blocked"] + "."
    if port["status"] == "soon" or not port["steps"]:
        return "This port is not ready to install yet."
    g = gamefile.inspect(game, port.get("input", {}))
    if not g["ok"]:
        return g["error"]
    if any(s.get("type") == "pack_nsp" for s in port["steps"]) and not settings.keys_present():
        return "Add your prod.keys in Settings first."
    need = int(float(port.get("disk_gb", 0)) * (1 << 30))
    if need:
        try:
            os.makedirs(out_dir, exist_ok=True)
            from . import paths
            for label, where in (("output", out_dir), ("work", paths.work_dir())):
                free = shutil.disk_usage(where).free
                if free < need:
                    return (f"Not enough free space on the {label} drive: about {need / 2**30:.0f} GB needed, "
                            f"{free / 2**30:.1f} GB free.")
        except OSError:
            pass
    return None


def group_steps(steps: list) -> list:
    """Consecutive steps with the same title show as one line: [[title, first_index, last_index], ...]."""
    groups: list = []
    for i, s in enumerate(steps):
        t = s.get("title", s["type"])
        if groups and groups[-1][0] == t:
            groups[-1][2] = i
        else:
            groups.append([t, i, i])
    return groups


def run_port(port: dict, game: str, out_dir: str, emit, cancel: threading.Event) -> bool:
    ctx = Ctx(port, game, out_dir, emit, cancel)
    g = gamefile.inspect(game, port.get("input", {}))
    if g.get("path"):                       # a package found inside a chosen folder
        ctx.game = g["path"]
    steps = port["steps"]
    groups = group_steps(steps)
    of = {i: gi for gi, grp in enumerate(groups) for i in range(grp[1], grp[2] + 1)}
    emit({"type": "plan", "steps": [grp[0] for grp in groups]})
    net.clear_dir(ctx.work)
    os.makedirs(out_dir, exist_ok=True)
    started = time.time()
    for i, s in enumerate(steps):
        gi = of[i]
        if i == groups[gi][1]:
            emit({"type": "step", "i": gi, "state": "run"})
        try:
            REGISTRY[s["type"]](s, ctx)
            if i == groups[gi][2]:
                emit({"type": "step", "i": gi, "state": "ok"})
        except Skip:
            if i == groups[gi][2]:
                emit({"type": "step", "i": gi, "state": "skip"})
        except StepError as e:
            emit({"type": "step", "i": gi, "state": "fail"})
            emit({"type": "done", "ok": False, "message": str(e)})
            return False
        except Exception as e:  # noqa: BLE001
            emit({"type": "step", "i": gi, "state": "fail"})
            emit({"type": "log", "text": f"{type(e).__name__}: {e}"})
            emit({"type": "done", "ok": False, "message": "Something went wrong. Open Details to see more."})
            return False
    shutil.rmtree(ctx.work, ignore_errors=True)
    nsp = ctx.vars.get("nsp")
    emit({"type": "done", "ok": True, "message": "Done. Your NSP is ready.", "path": nsp or out_dir})
    return True
