"""Draws the NX Porting Kit icon: a Joy-Con pair in Switch neon blue and neon red on a charcoal squircle.
Supersampled 2x. Writes assets/icon.png (1024) and assets/icon.ico (16 to 256)."""
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
S = 2048
K = S / 1024
px = lambda v: int(round(v * K))

BLUE, RED = (0, 195, 227), (255, 69, 84)          # Joy-Con neon blue and neon red
BLUE_D, RED_D = (0, 150, 180), (214, 40, 58)      # shaded edge of each
INK = (24, 26, 32)
TOP, BOT = (58, 62, 72), (30, 32, 38)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


bg = Image.new("RGB", (S, S))
d = ImageDraw.Draw(bg)
for y in range(S):
    d.line([(0, y), (S, y)], fill=lerp(TOP, BOT, y / S))
hl = Image.new("L", (S, S), 0)
ImageDraw.Draw(hl).ellipse([px(-200), px(-320), px(820), px(480)], fill=46)
bg = Image.composite(Image.new("RGB", (S, S), (120, 128, 148)), bg, hl.filter(ImageFilter.GaussianBlur(px(90))))

mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).rounded_rectangle([px(24), px(24), px(1000), px(1000)], radius=px(228), fill=255)

glyph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
g = ImageDraw.Draw(glyph)


def joycon(x0, x1, color, edge, left):
    y0, y1, r = 214, 810, 118
    g.rounded_rectangle([px(x0), px(y0), px(x1), px(y1)], radius=px(r), fill=edge)
    g.rounded_rectangle([px(x0), px(y0), px(x1 - 10), px(y1 - 14)], radius=px(r), fill=color)
    rail = (x1 - 70, x1) if left else (x0, x0 + 70)
    g.rectangle([px(rail[0]), px(y0 + 130), px(rail[1]), px(y1 - 130)], fill=color)


joycon(236, 486, BLUE, BLUE_D, True)
joycon(538, 788, RED, RED_D, False)

# left: stick (ring) and minus
g.ellipse([px(303), px(330), px(427), px(454)], fill=INK)
g.ellipse([px(325), px(352), px(405), px(432)], fill=BLUE)
g.rounded_rectangle([px(322), px(626), px(408), px(650)], radius=px(12), fill=INK)
# right: stick and four buttons
g.ellipse([px(607), px(330), px(719), px(442)], fill=INK)
g.ellipse([px(627), px(350), px(699), px(422)], fill=RED)
for dx, dy in ((0, -52), (0, 52), (-52, 0), (52, 0)):
    g.ellipse([px(663 + dx - 26), px(640 + dy - 26), px(663 + dx + 26), px(640 + dy + 26)], fill=INK)

shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
shadow.putalpha(glyph.split()[3].filter(ImageFilter.GaussianBlur(px(16))).point(lambda v: int(v * 0.45)))
icon = Image.alpha_composite(Image.alpha_composite(bg.convert("RGBA"), ImageChops.offset(shadow, 0, px(12))), glyph)
icon.putalpha(mask)

os.makedirs(OUT, exist_ok=True)
big = icon.resize((1024, 1024), Image.LANCZOS)
big.save(os.path.join(OUT, "icon.png"))
big.save(os.path.join(OUT, "icon.ico"), sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
print("saved")
