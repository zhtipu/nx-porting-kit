"""tool: run one of the few programs a port may use, on files inside its work folder.

Only the names below can run. A manifest cannot launch an arbitrary program: it can only give these tools
their arguments. Progress: any output line ending in "NN %" moves the progress bar.
"""
import os
import re
import shutil
import subprocess
import sys
import threading

from .. import paths
from . import StepError, step

NO_WINDOW = 0x08000000 if os.name == "nt" else 0
PCT = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*%\s*$")
TOOLS = {"node": "node.exe", "hacbrewpack": "hacbrewpack.exe"}


def find_tool(name: str) -> str | None:
    exe = TOOLS[name]
    candidates = [os.path.join(paths.tools_dir(), exe), paths.bundled("tools", exe),
                  paths.bundled("tools", name, exe)]
    if name == "hacbrewpack":
        candidates.append(os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), "Carafe", exe))
    for c in candidates:
        if os.path.isfile(c):
            return c
    return shutil.which(name)


def run(cmd: list, cwd: str, ctx, label: str = "") -> list:
    """Runs cmd, streams its output to the log, returns the last lines. Honors cancel."""
    tail: list = []
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                            encoding="utf-8", errors="replace", creationflags=NO_WINDOW)

    def watch():
        while proc.poll() is None:
            if ctx.cancel.wait(0.3):
                proc.terminate()
                return
    threading.Thread(target=watch, daemon=True).start()
    assert proc.stdout
    for line in proc.stdout:
        line = line.rstrip()
        if not line:
            continue
        tail = (tail + [line])[-12:]
        m = PCT.search(line)
        if m:
            ctx.progress(min(float(m.group(1)), 100) / 100, label)
        ctx.log(line)
    code = proc.wait()
    ctx.check_cancel()
    if code:
        raise StepError(f"{label or os.path.basename(cmd[0])} stopped with code {code}. Last output: "
                        + " | ".join(tail[-3:]))
    ctx.progress(-1, "")
    return tail


@step("tool")
def tool(s: dict, ctx) -> None:
    name = s.get("name")
    if name not in TOOLS:
        raise StepError("This game needs a newer version of NX Porting Kit.")
    exe = find_tool(name)
    if not exe:
        raise StepError("A required component is missing. Reinstall NX Porting Kit.")
    cwd = ctx.path(s.get("cwd", "."))
    args = [ctx.fmt(a) for a in s.get("args", [])]
    ctx.log(f"{name} {' '.join(os.path.basename(a) if os.path.isabs(a) else a for a in args)}")
    run([exe, *args], cwd, ctx, s.get("title", name))
    for need in s.get("expect", []):
        if not os.path.exists(ctx.path(need)):
            raise StepError(f"The tool finished but did not produce {need}.")
