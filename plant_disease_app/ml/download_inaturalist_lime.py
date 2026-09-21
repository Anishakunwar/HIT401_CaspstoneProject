"""
Downloads extra lime images (Persian/Tahiti lime, Citrus x latifolia) directly
from the iNaturalist API into data/lime/. Uses up to 2 photos per observation.
"""

import io
import time
from pathlib import Path

import requests
from PIL import Image

API = "https://api.inaturalist.org/v1/observations"
OUT_DIR = Path(__file__).parent / "data" / "lime"
TAXON = "Citrus latifolia"


def photo_urls():
    page = 1
    while True:
        r = requests.get(API, params={
            "taxon_name": TAXON, "photos": "true",
            "quality_grade": "research,needs_id",
            "per_page": 100, "page": page,
        }, timeout=30)
        r.raise_for_status()
        results = r.json().get("results", [])
        if not results:
            return
        for obs in results:
            for p in obs.get("photos", [])[:2]:
                yield p["url"].replace("square", "large")
        page += 1
        time.sleep(1)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    saved = 0
    for i, url in enumerate(photo_urls()):
        try:
            resp = requests.get(url, timeout=20)
            resp.raise_for_status()
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            img.save(OUT_DIR / f"persian_lime_{i:06d}.jpg", "JPEG", quality=90)
            saved += 1
        except Exception:
            pass
        time.sleep(0.2)
    print(f"Saved {saved} Persian lime images to {OUT_DIR}")


if __name__ == "__main__":
    main()
