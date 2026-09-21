"""
Downloads real diagrams, charts, screenshots and slides from Wikimedia Commons
(freely licensed). Most go to data/not_citrus for training; every 25th image is
held out into the independent test set (Desktop/testset/not_citrus).
"""

import io
import time
from pathlib import Path

import requests
from PIL import Image

H = {"User-Agent": "HIT401-student-project/1.0 (educational dataset)"}
API = "https://commons.wikimedia.org/w/api.php"
TRAIN_DIR = Path(__file__).parent / "data" / "not_citrus"
TEST_DIR = Path(r"C:\Users\adhik\OneDrive\Desktop\testset\not_citrus")
QUERIES = ["flowchart diagram", "software architecture diagram", "bar chart", "line graph chart",
           "screenshot user interface", "website screenshot", "infographic", "UML diagram",
           "mind map", "presentation slide", "data table statistics chart", "network diagram"]
PER_QUERY = 30


def to_rgb_jpeg(content):
    im = Image.open(io.BytesIO(content))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def main():
    TRAIN_DIR.mkdir(parents=True, exist_ok=True)
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    seen, idx, train_n, test_n = set(), 0, 0, 0
    for q in QUERIES:
        r = requests.get(API, headers=H, timeout=30, params={
            "action": "query", "generator": "search", "gsrsearch": f"filetype:bitmap {q}",
            "gsrnamespace": 6, "gsrlimit": PER_QUERY, "prop": "imageinfo",
            "iiprop": "url|mime", "iiurlwidth": 640, "format": "json"})
        pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
        for p in pages:
            ii = p.get("imageinfo", [{}])[0]
            if ii.get("mime") not in ("image/jpeg", "image/png") or p["title"] in seen:
                continue
            seen.add(p["title"])
            for attempt in range(3):
                try:
                    d = requests.get(ii["thumburl"], headers=H, timeout=30)
                    if d.status_code == 429:
                        time.sleep(5 * (attempt + 1))
                        continue
                    d.raise_for_status()
                    im = to_rgb_jpeg(d.content)
                    if idx % 25 == 0:
                        im.save(TEST_DIR / f"nonphoto_{test_n:02d}.jpg", "JPEG", quality=90)
                        test_n += 1
                    else:
                        im.save(TRAIN_DIR / f"commons_np_{train_n:05d}.jpg", "JPEG", quality=90)
                        train_n += 1
                    idx += 1
                    break
                except Exception:
                    time.sleep(1)
            time.sleep(0.6)
    print(f"train: {train_n}  held-out test: {test_n}")


if __name__ == "__main__":
    main()
