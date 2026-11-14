import os
import sys

HERE = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)


def main():
    args = sys.argv[1:]
    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QIcon
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtQuickControls2 import QQuickStyle
    from PySide6.QtWidgets import QApplication, QFileDialog

    from nxportingkit.bridge import Bridge
    from PySide6.QtCore import QObject, Slot

    class Dialogs(QObject):
        @Slot(str, result=str)
        def pickFolder(self, start):
            return QFileDialog.getExistingDirectory(None, "Choose a folder", start or "")

        @Slot(str, str, result=str)
        def pickFile(self, title, filt):
            path, _ = QFileDialog.getOpenFileName(None, title, "", filt or "All files (*)")
            return path

    QQuickStyle.setStyle("Basic")
    app = QApplication(sys.argv)
    app.setApplicationName("NX Porting Kit")
    icon = os.path.join(HERE, "assets", "icon.ico")
    if os.path.isfile(icon):
        app.setWindowIcon(QIcon(icon))

    engine = QQmlApplicationEngine()
    bridge, dialogs = Bridge(), Dialogs()
    ctx = engine.rootContext()
    ctx.setContextProperty("bridge", bridge)
    ctx.setContextProperty("dialogs", dialogs)
    ctx.setContextProperty("startPage", int(args[args.index("--page") + 1]) if "--page" in args else 0)
    ctx.setContextProperty("startGame", args[args.index("--game") + 1] if "--game" in args else "")
    engine.warnings.connect(lambda ws: [print(w.toString(), file=sys.stderr) for w in ws])
    engine.load(QUrl.fromLocalFile(os.path.join(HERE, "qml", "Main.qml")))
    if not engine.rootObjects():
        return 1

    if "--shot" in args:
        out = args[args.index("--shot") + 1]
        delay = int(args[args.index("--delay") + 1]) if "--delay" in args else 3500
        win = engine.rootObjects()[0]

        def grab():
            win.grabWindow().save(out)
            app.quit()
        QTimer.singleShot(delay, grab)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
