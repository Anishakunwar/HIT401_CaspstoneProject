from __future__ import annotations

from pathlib import Path

import tensorflow as tf

ROOT = Path(__file__).parent
PROJECT_ROOT = ROOT.parent
ASSETS_DIR = PROJECT_ROOT / "assets"


def _convert_model(keras_path: Path, tflite_path: Path) -> None:
    model = tf.keras.models.load_model(keras_path)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path.parent.mkdir(parents=True, exist_ok=True)
    tflite_path.write_bytes(tflite_model)

    print("Saved", tflite_path)


def main() -> None:
    # Convert whichever local checkpoints are present.
    candidates = [
        (ROOT / "fruit_classifier.keras", ASSETS_DIR / "fruit_classifier_quantized.tflite"),
        (ROOT / "lime_classifier.keras", ASSETS_DIR / "lime_classifier_quantized.tflite"),
    ]

    converted_any = False
    for keras_path, tflite_path in candidates:
        if keras_path.exists():
            _convert_model(keras_path, tflite_path)
            converted_any = True

    if not converted_any:
        raise SystemExit(
            "No Keras checkpoints found. Expected one of: "
            f"{', '.join(str(p) for p, _ in candidates)}"
        )


if __name__ == "__main__":
    main()
