"""
Downloads a Stage 1 "Lime vs Other Citrus" image dataset from GBIF occurrence records.

Usage:
    python download_dataset.py

Output layout (ready for keras image_dataset_from_directory / ImageDataGenerator):
    data/
      lime/
        finger_lime_000001.jpg
        key_lime_000001.jpg
        ...
      other_citrus/
        orange_000001.jpg
        lemon_000001.jpg
        mandarin_000001.jpg
        ...
"""

import io
import time
from pathlib import Path

import requests
from PIL import Image

GBIF_OCCURRENCE_SEARCH = "https://api.gbif.org/v1/occurrence/search"
PAGE_SIZE = 300
IMAGES_PER_SPECIES = 600
REQUEST_TIMEOUT = 15

DATA_DIR = Path(__file__).parent / "data"

# (GBIF taxonKey, species slug, target class)
SPECIES = [
    (8033094, "finger_lime", "lime"),           # Citrus australasica
    (3190164, "key_lime", "lime"),               # Citrus x aurantiifolia
    (3190158, "orange", "other_citrus"),          # Citrus sinensis
    (7647136, "lemon", "other_citrus"),           # Citrus limon
    (3190172, "mandarin", "other_citrus"),        # Citrus reticulata
]


def iter_image_urls(taxon_key: int):
    """Yields still-image URLs for a GBIF taxon, paging through occurrence search."""
    offset = 0
    seen = 0
    while seen < IMAGES_PER_SPECIES:
        params = {
            "taxonKey": taxon_key,
            "mediaType": "StillImage",
            "limit": PAGE_SIZE,
            "offset": offset,
        }

        payload = None
        for attempt in range(3):
            try:
                resp = requests.get(GBIF_OCCURRENCE_SEARCH, params=params, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                payload = resp.json()
                break
            except requests.RequestException as e:
                print(f"    GBIF search request failed (attempt {attempt + 1}/3): {e}")
                time.sleep(2 * (attempt + 1))

        if payload is None:
            print("    giving up on this page after 3 failed attempts")
            return

        results = payload.get("results", [])
        if not results:
            break

        for record in results:
            for media in record.get("media", []):
                if media.get("type") == "StillImage" and media.get("identifier"):
                    yield media["identifier"]
                    seen += 1
                    if seen >= IMAGES_PER_SPECIES:
                        return

        if payload.get("endOfRecords", True):
            break
        offset += PAGE_SIZE


def download_image(url: str, dest: Path) -> bool:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        img = Image.open(io.BytesIO(resp.content))
        img.verify()
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img.save(dest, "JPEG", quality=90)
        return True
    except Exception:
        return False


def main():
    for taxon_key, slug, class_label in SPECIES:
        out_dir = DATA_DIR / class_label
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n== {slug} (taxonKey={taxon_key}) -> {class_label} ==")
        saved = 0
        try:
            for i, url in enumerate(iter_image_urls(taxon_key)):
                dest = out_dir / f"{slug}_{i:06d}.jpg"
                if download_image(url, dest):
                    saved += 1
                    if saved % 50 == 0:
                        print(f"  saved {saved} images...")
                time.sleep(0.05)  # be polite to source servers
        except Exception as e:
            print(f"  ERROR on {slug}: {type(e).__name__} - {e}")
            print(f"  moving on to next species with {saved} images saved so far")

        print(f"  done: {saved} images saved to {out_dir}")


if __name__ == "__main__":
    main()
