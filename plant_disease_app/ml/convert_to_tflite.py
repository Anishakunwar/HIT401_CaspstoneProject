from pathlib import Path

import tensorflow as tf

ROOT = Path(__file__).parent
model = tf.keras.models.load_model(ROOT / "fruit_classifier.keras")

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open(ROOT.parent / "assets" / "fruit_classifier_quantized.tflite", "wb") as f:
    f.write(tflite_model)

print("Saved", ROOT.parent / "assets" / "fruit_classifier_quantized.tflite")
