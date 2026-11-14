"""One QObject exposed to QML as `bridge`. Fast calls return JSON; slow work runs on a daemon thread."""
import json
import os
import subprocess
import threading

from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from . import catalog, gamefile, paths, runner, settings, updater


def _j(o):
    return json.dumps(o)


class Bridge(QObject):
    opEvent = Signal(str)
    busyChanged = Signal()
    catalogChecked = Signal(str)     # {ok,new,updated,error,manual}
    updateInfo = Signal(str)
    updateProgress = Signal(float)
    updateFailed = Signal(str)
    quitForUpdate = Signal()
    toast = Signal(str, str)

    def __init__(self):
        super().__init__()
        self._busy = False
        self._cancel = threading.Event()
        self._ports = {p["id"]: p for p in catalog.load_all()}

    # ---- library ----
    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Slot(result=str)
    def library(self):
        self._ports = {p["id"]: p for p in catalog.load_all()}
        return _j([catalog.public_view(p) for p in self._ports.values()])

    @Slot(bool)
    def refreshCatalog(self, manual):
        def work():
            r = catalog.refresh_remote(force=manual)
            r["manual"] = manual
            self.catalogChecked.emit(_j(r))
        threading.Thread(target=work, daemon=True).start()

    @Slot()
    def checkUpdate(self):
        threading.Thread(target=lambda: self.updateInfo.emit(_j(updater.check())), daemon=True).start()

    @Slot()
    def installUpdate(self):
        def work():
            try:
                updater.download_and_apply(lambda v: self.updateProgress.emit(v))
                self.quitForUpdate.emit()
            except Exception as e:  # noqa: BLE001
                self.updateFailed.emit(str(e) or "The update failed. Nothing was changed.")
        threading.Thread(target=work, daemon=True).start()

    @Slot(str, result=str)
    def inspectGame(self, args_json):
        a = json.loads(args_json)
        p = self._ports.get(a["id"])
        if not p:
            return _j({"ok": False, "error": "Unknown game."})
        g = gamefile.inspect(a["path"], p.get("input", {}))
        return _j({k: v for k, v in g.items() if k != "path"})

    # ---- settings and keys ----
    @Slot(result=str)
    def settingsState(self):
        st = settings.load()
        return _j({"output_dir": st["output_dir"], "keys": settings.keys_present(),
                   "check_catalog": st["check_catalog"],
                   "version": paths.APP_VERSION, "home": paths.home()})

    @Slot(str, result=str)
    def saveSettings(self, data_json):
        st = settings.load()
        st.update(json.loads(data_json))
        settings.save(st)
        return self.settingsState()

    @Slot(str, result=str)
    def importKeys(self, path):
        ok, msg = settings.import_keys(path)
        return _j({"ok": ok, "message": msg})

    @Slot()
    def removeKeys(self):
        settings.remove_keys()

    @Slot()
    def openNotices(self):
        path = paths.bundled("resources", "NOTICES.txt")
        if os.path.isfile(path):
            os.startfile(path)  # noqa: S606

    @Slot(str)
    def openUrl(self, url):
        """Only the author's GitHub pages open from the app."""
        if url == "https://github.com/zhtipu" or url.startswith("https://github.com/zhtipu/"):
            QDesktopServices.openUrl(QUrl(url))

    @Slot(str)
    def reveal(self, path):
        path = os.path.normpath(path)
        if os.path.isfile(path):
            subprocess.Popen(["explorer", "/select,", path])
        elif os.path.isdir(path):
            os.startfile(path)  # noqa: S606

    # ---- install ----
    @Slot(str, bool, result=str)
    def start(self, args_json, dry):
        a = json.loads(args_json)
        p = self._ports.get(a["id"])
        if not p:
            return _j({"ok": False, "error": "Unknown game."})
        out_dir = a.get("out") or settings.load()["output_dir"]
        err = runner.preflight(p, a["path"], out_dir)
        if err:
            return _j({"ok": False, "error": err})
        if self._busy:
            return _j({"ok": False, "error": "Another install is running."})
        self._busy = True
        self._cancel.clear()
        self.busyChanged.emit()

        def emit(ev):
            self.opEvent.emit(_j(ev))

        def work():
            try:
                if dry:
                    emit({"type": "plan", "steps": [t for t, _, _ in runner.group_steps(p["steps"])]})
                    emit({"type": "log", "text": "Preview only: nothing is downloaded or written."})
                    emit({"type": "done", "ok": True, "message": "The steps above would run in this order."})
                else:
                    runner.run_port(p, a["path"], out_dir, emit, self._cancel)
            finally:
                self._busy = False
                self.busyChanged.emit()
        threading.Thread(target=work, daemon=True).start()
        return _j({"ok": True})

    @Slot()
    def cancel(self):
        self._cancel.set()
