"""
Generates synthetic screenshot/diagram-like images for the not_citrus class.

The not_citrus class only had cat/dog photos, which share nothing visually
with flat, geometric, non-photographic content (UI screenshots, diagrams,
charts). This fills that specific gap so the model has something to
recognize a diagram against, instead of defaulting to whichever class it
saw most.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).parent / "data" / "not_citrus"
COUNT = 400
SIZE = (400, 400)

LIGHT_BG = [(255, 255, 255), (245, 245, 245), (250, 248, 240), (240, 245, 250)]
BOX_COLORS = [(230, 230, 230), (200, 220, 240), (220, 240, 220), (240, 220, 200), (210, 210, 230)]
LINE_COLORS = [(100, 100, 100), (80, 120, 160), (60, 60, 60), (120, 80, 80)]
WORDS = ["Data", "Train", "Model", "Convert", "Input", "Output", "Process",
         "Class A", "Class B", "Step 1", "Step 2", "Flow", "API", "Server",
         "Client", "Queue", "Cache", "Result", "Score", "Layer"]


def random_diagram(seed):
    random.seed(seed)
    img = Image.new("RGB", SIZE, random.choice(LIGHT_BG))
    draw = ImageDraw.Draw(img)

    num_boxes = random.randint(2, 6)
    box_color = random.choice(BOX_COLORS)
    line_color = random.choice(LINE_COLORS)

    positions = []
    for _ in range(num_boxes):
        w, h = random.randint(60, 140), random.randint(40, 80)
        x = random.randint(10, SIZE[0] - w - 10)
        y = random.randint(10, SIZE[1] - h - 10)
        draw.rounded_rectangle([x, y, x + w, y + h], radius=8,
                                fill=box_color, outline=line_color, width=2)
        positions.append((x + w // 2, y + h // 2))
        if random.random() < 0.7:
            draw.text((x + 8, y + h // 2 - 6), random.choice(WORDS), fill=line_color)

    # connecting arrows/lines between some boxes
    for i in range(len(positions) - 1):
        if random.random() < 0.8:
            draw.line([positions[i], positions[i + 1]], fill=line_color, width=2)

    if random.random() < 0.5:
        draw.line([(0, random.randint(0, SIZE[1])), (SIZE[0], random.randint(0, SIZE[1]))],
                   fill=(220, 220, 220), width=1)

    return img


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(COUNT):
        img = random_diagram(i)
        img.save(OUT_DIR / f"synthetic_{i:06d}.jpg", "JPEG", quality=90)
    print(f"Generated {COUNT} synthetic diagram images in {OUT_DIR}")


if __name__ == "__main__":
    main()
