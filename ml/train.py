"""Train the six-class fruit classifier from the prepared Fruits-360 data."""

import json
from pathlib import Path

import tensorflow as tf

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data" / "prepared"
TRAIN_DIR = DATA_DIR / "Training"
TEST_DIR = DATA_DIR / "Test"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 8
CLASS_NAMES = ["apple", "banana", "lime", "not_fruit", "other_citrus", "other_fruit"]

for directory in (TRAIN_DIR, TEST_DIR):
    missing = [name for name in CLASS_NAMES if not list((directory / name).glob("*.jpg"))]
    if missing:
        raise SystemExit(f"Missing training data in {directory}: {', '.join(missing)}")

train_ds = tf.keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=0.15, subset="training", seed=123,
    image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="int",
)
val_ds = tf.keras.utils.image_dataset_from_directory(
    TRAIN_DIR, validation_split=0.15, subset="validation", seed=123,
    image_size=IMG_SIZE, batch_size=BATCH_SIZE, label_mode="int",
)
test_ds = tf.keras.utils.image_dataset_from_directory(
    TEST_DIR, image_size=IMG_SIZE, batch_size=BATCH_SIZE, shuffle=False,
    label_mode="int",
)

if train_ds.class_names != CLASS_NAMES:
    raise SystemExit(f"Unexpected class order: {train_ds.class_names}")

AUTOTUNE = tf.data.AUTOTUNE
train_ds = train_ds.prefetch(AUTOTUNE)
val_ds = val_ds.prefetch(AUTOTUNE)
test_ds = test_ds.prefetch(AUTOTUNE)

counts = {name: len(list((TRAIN_DIR / name).glob("*.jpg"))) for name in CLASS_NAMES}
total = sum(counts.values())
class_weight = {
    index: total / (len(CLASS_NAMES) * counts[name])
    for index, name in enumerate(CLASS_NAMES)
}
print("Class counts:", counts, flush=True)

best_model = ROOT / "fruit_classifier.keras"
if best_model.exists():
    # Continue from the local checkpoint when refining data labels. This also
    # avoids downloading ImageNet weights again on subsequent training runs.
    model = tf.keras.models.load_model(best_model)
else:
    preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input
    base_model = tf.keras.applications.MobileNetV2(
        input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet"
    )
    base_model.trainable = False

    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.08),
        tf.keras.layers.RandomZoom(0.12),
    ])
    inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
    x = augmentation(inputs)
    x = preprocess_input(x)
    x = base_model(x, training=False)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = tf.keras.layers.Dense(len(CLASS_NAMES), activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)

model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])
callbacks = [
    tf.keras.callbacks.ModelCheckpoint(best_model, save_best_only=True, monitor="val_accuracy", mode="max"),
    tf.keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=2, restore_best_weights=True),
]
model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, class_weight=class_weight,
          callbacks=callbacks, verbose=2)

model = tf.keras.models.load_model(best_model)
test_loss, test_accuracy = model.evaluate(test_ds, verbose=0)
results = {"classes": CLASS_NAMES, "test_loss": float(test_loss), "test_accuracy": float(test_accuracy), "train_counts": counts}
(ROOT / "fruit_classifier_metrics.json").write_text(json.dumps(results, indent=2) + "\n")
print("Official held-out test accuracy:", f"{test_accuracy:.4f}", flush=True)
