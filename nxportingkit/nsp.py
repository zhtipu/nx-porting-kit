"""Control data for an NSP: the 256x256 baseline JPEG icon and control.nacp, in pure Python.

The NACP starts from a template (resources/nacp_template.bin: a known-good file with every per-game field cleared)
and the fields the HOME Menu needs are written directly: name and publisher in all 16 language slots, display
version, American English in the language flag, and the title ID in PresenceGroupId, SaveDataOwnerId,
LocalCommunicationId[0] and AddOnContentBaseId (+0x1000).
"""
import io
import os
import struct

from PIL import Image

from . import paths


def make_icon(src: str, dest: str) -> None:
    img = Image.open(src)
    sizes = getattr(img, "info", {}).get("sizes")
    if sizes:
        try:
            img.size = max(sizes, key=lambda s: s[0] * s[1])
        except Exception:  # noqa: BLE001
            pass
    img = img.convert("RGBA")
    canvas = Image.new("RGB", img.size, (0, 0, 0))
    canvas.paste(img, mask=img.split()[3])
    canvas = canvas.resize((256, 256), Image.LANCZOS)
    buf = io.BytesIO()
    canvas.save(buf, "JPEG", quality=95, progressive=False, optimize=False, subsampling=0)
    with open(dest, "wb") as f:
        f.write(buf.getvalue())


def make_nacp(title: str, publisher: str, version: str, title_id: str) -> bytes:
    with open(paths.bundled("resources", "nacp_template.bin"), "rb") as f:
        d = bytearray(f.read())
    name = title.encode("utf-8")[:0x1FF]
    pub = publisher.encode("utf-8")[:0xFF]
    for lang in range(12):          # nacptool fills the 12 languages the console has
        base = lang * 0x300
        d[base:base + 0x200] = name.ljust(0x200, b"\0")
        d[base + 0x200:base + 0x300] = pub.ljust(0x100, b"\0")
    d[0x3060:0x3070] = version.encode("ascii", "ignore")[:15].ljust(16, b"\0")
    tid = int(title_id, 16)
    struct.pack_into("<I", d, 0x302C, 1)
    struct.pack_into("<Q", d, 0x3038, tid)
    struct.pack_into("<Q", d, 0x3070, tid + 0x1000)
    struct.pack_into("<Q", d, 0x3078, tid)
    struct.pack_into("<Q", d, 0x30B0, tid)
    return bytes(d)


def write_control(folder: str, icon_src: str, title: str, publisher: str, version: str, title_id: str) -> None:
    os.makedirs(folder, exist_ok=True)
    make_icon(icon_src, os.path.join(folder, "icon_AmericanEnglish.dat"))
    with open(os.path.join(folder, "control.nacp"), "wb") as f:
        f.write(make_nacp(title, publisher, version, title_id))
