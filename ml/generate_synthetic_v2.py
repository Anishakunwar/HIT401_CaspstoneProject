"""
Richer synthetic non-photo negatives for the not_citrus class: search-UI
screenshots, bar/line charts, tables, flowcharts, slides and app mockups, in
phone-portrait and desktop-landscape sizes, light and dark, with green
accents so "green" alone doesn't read as citrus.
"""

import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent / "data" / "not_citrus"
COUNT = 600
SIZES = [(390, 844), (360, 780), (800, 600), (1024, 576), (600, 800), (1280, 720), (500, 500)]
WORDS = ["lime", "search", "results", "images", "news", "maps", "data", "model", "train", "score",
         "class", "input", "output", "server", "client", "queue", "cache", "report", "sales", "users",
         "growth", "total", "average", "region", "north", "south", "week", "month", "profit", "cost",
         "settings", "profile", "home", "about", "contact", "login", "pricing", "features", "docs", "help"]
FONT_PATHS = [r"C:\Windows\Fonts\arial.ttf", r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\calibri.ttf"]
PALETTES = [
    [(224, 242, 233), (198, 232, 214), (160, 200, 180)],
    [(232, 240, 254), (200, 220, 250), (150, 180, 230)],
    [(253, 236, 214), (250, 214, 170), (230, 170, 110)],
    [(240, 240, 240), (215, 215, 215), (170, 170, 170)],
    [(236, 226, 250), (210, 190, 240), (170, 140, 210)],
    [(210, 240, 190), (160, 215, 120), (110, 170, 70)],
]


def font(size):
    for p in FONT_PATHS:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def words(n):
    return " ".join(random.choice(WORDS) for _ in range(n))


def base(w, h, dark):
    bg = (28, 30, 36) if dark else random.choice([(255, 255, 255), (250, 250, 250), (246, 248, 250), (252, 251, 247)])
    fg = (235, 235, 240) if dark else (40, 40, 45)
    sub = (150, 150, 160) if dark else (110, 110, 120)
    return Image.new("RGB", (w, h), bg), bg, fg, sub


def search_ui(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    d.rounded_rectangle([w * 0.12, h * 0.03, w * 0.95, h * 0.03 + h * 0.06], radius=int(h * 0.03), fill=pal[0], outline=pal[2])
    d.ellipse([w * 0.16, h * 0.043, w * 0.16 + h * 0.025, h * 0.043 + h * 0.025], outline=fg, width=2)
    d.text((w * 0.24, h * 0.045), random.choice(WORDS), fill=fg, font=font(max(12, int(h * 0.028))))
    x = w * 0.08
    for t in ["ALL", "IMAGES", "NEWS", "MAPS"][: random.randint(3, 4)]:
        d.text((x, h * 0.13), t, fill=fg, font=font(max(11, int(h * 0.022))))
        x += w * 0.22
    d.line([0, h * 0.17, w, h * 0.17], fill=sub)
    y = h * 0.2
    while y < h - h * 0.08:
        c = random.choice([(120, 200, 80), (60, 120, 200), (230, 130, 50), (150, 150, 150)])
        d.ellipse([w * 0.07, y, w * 0.07 + h * 0.045, y + h * 0.045], fill=c)
        d.text((w * 0.2, y), words(random.randint(2, 4)).title(), fill=fg, font=font(max(12, int(h * 0.024))))
        d.text((w * 0.2, y + h * 0.032), "https://www." + random.choice(WORDS) + ".com", fill=sub, font=font(max(10, int(h * 0.02))))
        y += h * 0.1
    return img


def bar_chart(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    d.text((w * 0.06, h * 0.04), words(3).title(), fill=fg, font=font(max(14, int(h * 0.04))))
    x0, y0, x1, y1 = w * 0.1, h * 0.15, w * 0.94, h * 0.85
    d.line([x0, y1, x1, y1], fill=sub, width=2)
    d.line([x0, y0, x0, y1], fill=sub, width=2)
    n = random.randint(4, 9)
    bw = (x1 - x0) / (n * 1.6)
    for i in range(n):
        bh = random.uniform(0.15, 0.95) * (y1 - y0)
        bx = x0 + (i + 0.5) * (x1 - x0) / n
        d.rectangle([bx - bw / 2, y1 - bh, bx + bw / 2, y1], fill=pal[2] if i % 3 else pal[1])
        d.text((bx - bw / 2, y1 + 4), random.choice(WORDS)[:5], fill=sub, font=font(max(9, int(h * 0.02))))
    return img


def line_chart(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = w * 0.1, h * 0.12, w * 0.94, h * 0.85
    for k in range(5):
        y = y0 + k * (y1 - y0) / 4
        d.line([x0, y, x1, y], fill=(70, 70, 78) if dark else (225, 225, 230))
    for c in random.sample([(60, 160, 90), (60, 110, 200), (220, 110, 50), (150, 80, 180)], random.randint(1, 3)):
        pts = [(x0 + i * (x1 - x0) / 10, random.uniform(y0, y1)) for i in range(11)]
        d.line(pts, fill=c, width=3)
        for p in pts:
            d.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=c)
    return img


def table(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    cols, rows = random.randint(3, 5), random.randint(6, 14)
    cw, rh = w * 0.9 / cols, min(h * 0.85 / rows, 46)
    d.rectangle([w * 0.05, h * 0.05, w * 0.95, h * 0.05 + rh], fill=pal[1])
    for r in range(rows):
        for c in range(cols):
            t = random.choice(WORDS) if (r == 0 or c == 0) else str(random.randint(1, 999))
            d.text((w * 0.05 + c * cw + 6, h * 0.05 + r * rh + rh * 0.25), t, fill=fg, font=font(max(11, int(rh * 0.4))))
        d.line([w * 0.05, h * 0.05 + (r + 1) * rh, w * 0.95, h * 0.05 + (r + 1) * rh], fill=sub)
    return img


def flowchart(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    vertical = random.random() < 0.6
    n = random.randint(3, 6)
    bw, bh = (w * 0.5, h * 0.11) if vertical else (w * 0.16, h * 0.2)
    centers = []
    for i in range(n):
        if vertical:
            cx, cy = w / 2, h * 0.08 + bh / 2 + i * (h * 0.84 / n)
        else:
            cx, cy = w * 0.08 + bw / 2 + i * (w * 0.86 / n), h / 2 + random.randint(-40, 40)
        d.rounded_rectangle([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], radius=8, fill=random.choice(pal[:2]), outline=pal[2], width=2)
        d.text((cx - bw / 2 + 8, cy - bh * 0.3), words(2).title(), fill=fg, font=font(max(11, int(min(bw, bh) * 0.28))))
        d.text((cx - bw / 2 + 8, cy + bh * 0.05), words(3), fill=sub, font=font(max(9, int(min(bw, bh) * 0.2))))
        centers.append((cx, cy))
    for a, b in zip(centers, centers[1:]):
        if vertical:
            d.line([a[0], a[1] + bh / 2, b[0], b[1] - bh / 2], fill=sub, width=2)
            d.polygon([(b[0], b[1] - bh / 2), (b[0] - 5, b[1] - bh / 2 - 9), (b[0] + 5, b[1] - bh / 2 - 9)], fill=sub)
        else:
            d.line([a[0] + bw / 2, a[1], b[0] - bw / 2, b[1]], fill=sub, width=2)
            d.polygon([(b[0] - bw / 2, b[1]), (b[0] - bw / 2 - 9, b[1] - 5), (b[0] - bw / 2 - 9, b[1] + 5)], fill=sub)
    return img


def slide(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    d.rectangle([0, 0, w, h * 0.16], fill=pal[2])
    d.text((w * 0.05, h * 0.04), words(3).title(), fill=(255, 255, 255), font=font(max(16, int(h * 0.07))))
    y = h * 0.25
    while y < h * 0.9:
        d.ellipse([w * 0.06, y + 6, w * 0.06 + 10, y + 16], fill=pal[2])
        d.text((w * 0.1, y), words(random.randint(3, 7)), fill=fg, font=font(max(12, int(h * 0.04))))
        y += h * 0.11
    return img


def app_mockup(w, h, dark):
    img, bg, fg, sub = base(w, h, dark)
    d = ImageDraw.Draw(img)
    pal = random.choice(PALETTES)
    d.rectangle([0, 0, w, h * 0.09], fill=pal[2])
    d.text((w * 0.05, h * 0.025), words(2).title(), fill=(255, 255, 255), font=font(max(14, int(h * 0.035))))
    y = h * 0.13
    while y < h * 0.8:
        d.rounded_rectangle([w * 0.05, y, w * 0.95, y + h * 0.12], radius=12, fill=pal[0], outline=pal[1])
        d.text((w * 0.09, y + h * 0.02), words(2).title(), fill=fg, font=font(max(12, int(h * 0.03))))
        d.text((w * 0.09, y + h * 0.07), words(4), fill=sub, font=font(max(10, int(h * 0.022))))
        y += h * 0.15
    d.rounded_rectangle([w * 0.2, h * 0.88, w * 0.8, h * 0.88 + h * 0.07], radius=20, fill=pal[2])
    d.text((w * 0.42, h * 0.9), random.choice(WORDS).title(), fill=(255, 255, 255), font=font(max(12, int(h * 0.03))))
    return img


MAKERS = [search_ui, bar_chart, line_chart, table, flowchart, flowchart, slide, app_mockup]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(COUNT):
        random.seed(10_000 + i)
        w, h = random.choice(SIZES)
        img = random.choice(MAKERS)(w, h, random.random() < 0.25)
        img.save(OUT_DIR / f"synthetic2_{i:06d}.jpg", "JPEG", quality=random.choice([80, 88, 92]))
    print(f"Generated {COUNT} synthetic2 images in {OUT_DIR}")


if __name__ == "__main__":
    main()
