import os
import re
import threading

from .. import paths, settings


class Ctx:
    """Everything a step may touch. Paths a manifest names are resolved here and must stay inside the run's
    work folder or the chosen output folder."""

    def __init__(self, port: dict, game: str, out_dir: str, emit, cancel: threading.Event | None = None):
        self.port = port
        self.game = game
        self.out = out_dir
        self.work = os.path.join(paths.work_dir(), port["id"])
        self.emit = emit
        self.cancel = cancel or threading.Event()
        self.vars: dict = {}

    # ---- output ----
    def log(self, text: str) -> None:
        self.emit({"type": "log", "text": text})

    def progress(self, value: float, label: str = "") -> None:
        self.emit({"type": "progress", "value": value, "label": label})

    # ---- templating ----
    def fmt(self, s):
        if not isinstance(s, str):
            return s
        table = {"work": self.work, "out": self.out, "game": self.game, "keys": settings.keys_path(),
                 **{k: str(v) for k, v in self.vars.items()}}

        def sub(m):
            k = m.group(1)
            if k not in table:
                raise KeyError(f"unknown name {{{k}}} in port.json")
            return table[k]
        return re.sub(r"\{([A-Za-z0-9_]+)\}", sub, s)

    def path(self, rel: str) -> str:
        """A path from a manifest: relative paths live in the work folder; {out}/... in the output folder."""
        p = os.path.normpath(os.path.join(self.work, self.fmt(rel)))
        roots = [os.path.normcase(os.path.abspath(r)) for r in (self.work, self.out)]
        ap = os.path.normcase(os.path.abspath(p))
        if not any(ap == r or ap.startswith(r + os.sep) for r in roots):
            raise ValueError("a port tried to use a path outside its folders")
        return p

    def check_cancel(self) -> None:
        if self.cancel.is_set():
            from . import StepError
            raise StepError("Cancelled.")
