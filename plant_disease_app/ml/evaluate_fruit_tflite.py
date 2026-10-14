"""Evaluate the exported TFLite model on the held-out Fruits-360 Test split."""

import json
from pathlib import Path

import numpy as np
import tensorflow as tf

ROOT = Path(__file__).parent
TEST_DIR = ROOT / "data" / "prepared" / "Test"
MODEL_PATH = ROOT.parent / "assets" / "fruit_classifier_quantized.tflite"
BATCH = 32

dataset = tf.keras.utils.image_dataset_from_directory(
    TEST_DIR, image_size=(224, 224), batch_size=BATCH, shuffle=False,
)
classes = dataset.class_names
interpreter = tf.lite.Interpreter(model_path=str(MODEL_PATH), num_threads=4)
input_info = interpreter.get_input_details()[0]
interpreter.resize_tensor_input(input_info["index"], [BATCH, 224, 224, 3], strict=False)
interpreter.allocate_tensors()
input_index = interpreter.get_input_details()[0]["index"]
output_index = interpreter.get_output_details()[0]["index"]

confusion = np.zeros((len(classes), len(classes)), dtype=np.int64)
for images, labels in dataset:
    count = int(images.shape[0])
    batch = np.zeros((BATCH, 224, 224, 3), dtype=np.float32)
    batch[:count] = images.numpy()
    interpreter.set_tensor(input_index, batch)
    interpreter.invoke()
    predictions = interpreter.get_tensor(output_index)[:count].argmax(axis=1)
    for actual, predicted in zip(labels.numpy(), predictions):
        confusion[int(actual), int(predicted)] += 1

class_accuracy = {
    name: float(confusion[index, index] / max(1, confusion[index].sum()))
    for index, name in enumerate(classes)
}
result = {
    "classes": classes,
    "test_images": int(confusion.sum()),
    "test_accuracy": float(np.trace(confusion) / max(1, confusion.sum())),
    "class_accuracy": class_accuracy,
    "confusion_matrix": confusion.tolist(),
}
(ROOT / "fruit_classifier_tflite_metrics.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
