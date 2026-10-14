"""Fetch and group Fruits-360 into balanced fruit-scanner classes.

Dataset: https://github.com/fruits-360/fruits-360-100x100
License: CC BY-SA 4.0. See ml/FRUITS360_ATTRIBUTION.md.
"""

import random
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
SOURCE = DATA / "fruits-360-100x100"
PREPARED = DATA / "prepared"
REPOSITORY = "https://github.com/fruits-360/fruits-360-100x100.git"
CLASS_NAMES = ["apple", "banana", "lime", "not_fruit", "other_citrus", "other_fruit"]
LIMITS = {"Training": 2500, "Test": 1000}

CITRUS = ("lemon", "meyer lemon", "orange", "mandarine", "clementine", "grapefruit",
          "pomelo", "tangelo", "kumquat", "kumsquat")
FRUIT_PREFIXES = (
    "apricot", "avocado", "blackberr", "blueberr", "cactus fruit", "cantaloupe",
    "carambola", "cherry", "cherimoya", "coco", "date", "fig", "gooseberry",
    "grape", "guava", "huckleberry", "kiwi", "kaki", "lychee", "mango", "mangostan",
    "maracuja", "melon", "mulberry", "nectarine", "passion fruit", "papaya", "peach",
    "pear", "pepino", "physalis", "pitahaya", "plum", "pomegranate", "quince",
    "rambutan", "raspberry", "redcurrant", "salak", "strawberry", "tamarillo", "watermelon",
)


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=SOURCE, text=True).strip()


def output_label(name: str) -> str:
    value = name.casefold()
    if value.startswith("apple"):
        return "apple"
    if value.startswith("banana"):
        return "banana"
    if value == "lime" or value.startswith(("lime ", "limes ")):
        return "lime"
    if any(value.startswith(item) for item in CITRUS):
        return "other_citrus"
    if any(value.startswith(item) for item in FRUIT_PREFIXES):
        return "other_fruit"
    return "not_fruit"


def ensure_source() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    if not (SOURCE / ".git").exists():
        subprocess.run([
            "git", "clone", "--depth", "1", "--filter=blob:none", "--no-checkout",
            REPOSITORY, str(SOURCE),
        ], check=True)

    names = run("git", "ls-tree", "-d", "--name-only", "HEAD:Training").splitlines()
    selected = [name for name in names if output_label(name) in CLASS_NAMES]
    if not selected:
        raise RuntimeError("No class folders found in the Fruits-360 Training directory")
    paths = [f"Training/{name}" for name in selected]
    paths.extend(f"Test/{name}" for name in selected)
    subprocess.run(["git", "sparse-checkout", "set", "--cone", *paths], cwd=SOURCE, check=True)
    subprocess.run(["git", "checkout"], cwd=SOURCE, check=True)


def build_split(split: str, limit: int) -> dict[str, int]:
    source_dir = SOURCE / split
    groups: dict[str, list[tuple[str, list[Path]]]] = {name: [] for name in CLASS_NAMES}
    for folder in sorted(path for path in source_dir.iterdir() if path.is_dir()):
        label = output_label(folder.name)
        files = sorted(folder.glob("*.jpg"))
        if files:
            groups[label].append((folder.name, files))

    randomizer = random.Random(20261012 + (0 if split == "Training" else 1))
    out_root = PREPARED / split
    if out_root.exists():
        shutil.rmtree(out_root)
    counts: dict[str, int] = {}
    for label, sources in groups.items():
        if not sources:
            raise RuntimeError(f"No source folders found for class {label} in {split}")
        for _, files in sources:
            randomizer.shuffle(files)
        positions = [0] * len(sources)
        chosen: list[tuple[str, Path]] = []
        while len(chosen) < limit:
            advanced = False
            for index, (source_name, files) in enumerate(sources):
                if positions[index] < len(files) and len(chosen) < limit:
                    chosen.append((source_name, files[positions[index]]))
                    positions[index] += 1
                    advanced = True
            if not advanced:
                break

        target = out_root / label
        target.mkdir(parents=True, exist_ok=True)
        for index, (source_name, source_file) in enumerate(chosen):
            safe_source = "_".join(source_name.casefold().split())
            shutil.copy2(source_file, target / f"{safe_source}_{index:05d}.jpg")
        counts[label] = len(chosen)
    return counts


def main() -> None:
    ensure_source()
    train_counts = build_split("Training", LIMITS["Training"])
    test_counts = build_split("Test", LIMITS["Test"])
    print("Training images:", train_counts)
    print("Test images:", test_counts)
    print("Prepared data:", PREPARED)


if __name__ == "__main__":
    main()
