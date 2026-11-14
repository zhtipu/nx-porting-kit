"""File helpers."""
import os
import shutil


def safe_replace(src: str, dst: str) -> None:
    """os.replace, with a copy-and-delete fallback.

    On some Windows setups os.replace inside AppData\\Local fails with WinError 17 ("cannot move the file to a
    different disk drive") even for two paths in one folder. shutil.move copes with that."""
    try:
        os.replace(src, dst)
    except OSError:
        if os.path.exists(dst):
            os.remove(dst)
        shutil.move(src, dst)
