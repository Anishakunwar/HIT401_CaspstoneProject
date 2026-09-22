"""
Stage 2 v2: leaf disease classifier with an input-validity class.

Classes (alphabetical): canker, healthy, hlb, other
  hlb   = dataset's "Citrus greening" + "Yellow dragon" (Huanglongbing)
  other = NOT a plain-background single-leaf photo (field photos of trees,
          fruit, animals, screenshots...) taken from the Stage 1 data, so the
          model can refuse instead of defaulting to a disease label.

Validation is split by CONTIGUOUS BLOCKS of the dataset's capture sequence
(consecutive photos are often the same leaf) to reduce near-duplicate leakage.

Run from the ml/ folder:  python disease/train_disease_v2.py
"""

import glob
import io
import os
import random
import re
import shutil
import zipfile

import numpy as np
import tensorflow as tf
from PIL import Image

ZIP = r"C:\Users\adhik\disease_data\Sweetorange.zip"
DATA = os.path.join("disease", "data2")
SOURCES = {"Citrus canker": ("canker", "canker"), "Citrus greening": ("greening", "hlb"),
           "Yellow dragon": ("yellow_dragon", "hlb"), "Healthy leaf": ("healthy", "healthy")}
CLASS_NAMES = ["canker", "healthy", "hlb", "other"]
OTHER_FROM = {"lime": 300, "other_citrus": 200, "not_citrus": 300}  # images sampled from Stage 1 data
IMG_SIZE = (224, 224)
BATCH, EPOCHS, SEED = 32, 15, 123

# --- Build data2/<class>/ (disease classes keep their sequence number in the name) ---
shutil.rmtree(DATA, ignore_errors=True)
for cls in CLASS_NAMES:
    os.makedirs(os.path.join(DATA, cls), exist_ok=True)
z = zipfile.ZipFile(ZIP)
for src, (prefix, cls) in SOURCES.items():
    for n in z.namelist():
        if n.startswith(f"Sweetorange/Original Image/{src}/") and n.lower().endswith((".jpg", ".jpeg")):
            idx = int(re.search(r"(\d+)\.jpe?g$", n, re.I).group(1))
            im = Image.open(io.BytesIO(z.read(n))).convert("RGB")
            im.thumbnail((640, 640))
            im.save(os.path.join(DATA, cls, f"{prefix}__{idx:04d}.jpg"), "JPEG", quality=90)
rng = random.Random(SEED)
for folder, k in OTHER_FROM.items():
    files = sorted(glob.glob(os.path.join("data", folder, "*.jpg")))
    for f in rng.sample(files, k):
        shutil.copy(f, os.path.join(DATA, "other", f"{folder}__{os.path.basename(f)}"))

# --- Split: contiguous blocks for disease classes, random for "other" ---
train_p, train_l, val_p, val_l = [], [], [], []
counts = {}
for ci, cls in enumerate(CLASS_NAMES):
    files = sorted(glob.glob(os.path.join(DATA, cls, "*.jpg")))
    counts[ci] = len(files)
    if cls == "other":
        rng.shuffle(files)
        cut = int(len(files) * 0.8)
        tr, va = files[:cut], files[cut:]
    else:
        def key(p):
            b = os.path.basename(p)
            return (b.split("__")[0], int(b.split("__")[1][:4]))
        files.sort(key=key)
        tr, va = [], []
        for i, p in enumerate(files):
            (va if (i // 20) % 5 == 0 else tr).append(p)  # every 5th block of 20 consecutive photos
    train_p += tr; train_l += [ci] * len(tr); val_p += va; val_l += [ci] * len(va)
print("Class counts:", {CLASS_NAMES[i]: n for i, n in counts.items()})
print("train:", len(train_p), "val:", len(val_p))


def load(path, label):
    img = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
    return tf.image.resize(img, IMG_SIZE), label


def make_ds(paths, labels, shuffle):
    ds = tf.data.Dataset.from_tensor_slices((paths, labels))
    if shuffle:
        ds = ds.shuffle(len(paths), seed=SEED)
    return ds.map(load, num_parallel_calls=tf.data.AUTOTUNE).batch(BATCH).prefetch(tf.data.AUTOTUNE)


train_ds, val_ds = make_ds(train_p, train_l, True), make_ds(val_p, val_l, False)

base = tf.keras.applications.MobileNetV2(input_shape=IMG_SIZE + (3,), include_top=False, weights="imagenet")
base.trainable = False
augment = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal_and_vertical"),
    tf.keras.layers.RandomRotation(0.25),
    tf.keras.layers.RandomZoom(0.15),
    tf.keras.layers.RandomBrightness(0.15),
    tf.keras.layers.RandomContrast(0.15),
])
inputs = tf.keras.Input(shape=IMG_SIZE + (3,))
x = augment(inputs)
x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
x = base(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
x = tf.keras.layers.Dropout(0.2)(x)
outputs = tf.keras.layers.Dense(4, activation="softmax")(x)
model = tf.keras.Model(inputs, outputs)
model.compile(optimizer="adam", loss="sparse_categorical_crossentropy", metrics=["accuracy"])

total = sum(counts.values())
class_weight = {i: total / (len(counts) * n) for i, n in counts.items()}
print("Class weights:", class_weight)
ckpt = tf.keras.callbacks.ModelCheckpoint(
    os.path.join("disease", "disease_classifier_v2.keras"), save_best_only=True, monitor="val_accuracy", mode="max")
model.fit(train_ds, validation_data=val_ds, epochs=EPOCHS, class_weight=class_weight, callbacks=[ckpt])

best = tf.keras.models.load_model(os.path.join("disease", "disease_classifier_v2.keras"))
pred = best.predict(val_ds, verbose=0).argmax(axis=1)
truth = np.array(val_l)
cm = np.zeros((4, 4), int)
for t, p in zip(truth, pred):
    cm[t][p] += 1
print("classes:", CLASS_NAMES)
print("rows=true, cols=predicted\n", cm)
for i, n in enumerate(CLASS_NAMES):
    print(f"{n}: recall {cm[i][i] / cm[i].sum() * 100:.1f}%  ({cm[i][i]}/{cm[i].sum()})")
print(f"overall val accuracy (block split): {(pred == truth).mean() * 100:.1f}%")
for src in ("greening", "yellow_dragon"):
    idx = [i for i, p in enumerate(val_p) if os.path.basename(p).startswith(src + "__")]
    print(f"  hlb source {src}: {sum(pred[i] == truth[i] for i in idx)}/{len(idx)} correct")


# --- Near-duplicate leakage diagnostic (dHash distance val -> train) ---
def dhash(p):
    g = np.array(Image.open(p).convert("L").resize((17, 16)), dtype=np.int16)
    return (g[:, 1:] > g[:, :-1]).flatten()


disease_tr = [p for p, l in zip(train_p, train_l) if l != 3]
disease_va = [p for p, l in zip(val_p, val_l) if l != 3]
H_tr = np.array([dhash(p) for p in disease_tr])
H_va = np.array([dhash(p) for p in disease_va])
mind = np.array([(H_tr != h).sum(axis=1).min() for h in H_va])
print(f"leakage check: val images with a near-duplicate in train (dHash dist <= 12/256): {(mind <= 12).sum()}/{len(mind)}")

# --- Convert to quantized TFLite and verify ---
conv = tf.lite.TFLiteConverter.from_keras_model(best)
conv.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_path = os.path.join("disease", "disease_classifier_v2_quantized.tflite")
open(tflite_path, "wb").write(conv.convert())
it = tf.lite.Interpreter(model_path=tflite_path)
it.allocate_tensors()
i0, o0 = it.get_input_details()[0]["index"], it.get_output_details()[0]["index"]
ok = 0
for xb, yb in val_ds:
    for img, y in zip(xb.numpy(), yb.numpy()):
        it.set_tensor(i0, img[None].astype(np.float32))
        it.invoke()
        ok += int(it.get_tensor(o0)[0].argmax() == y)
print(f"tflite size: {os.path.getsize(tflite_path)}  TFLite val accuracy: {ok / len(val_p) * 100:.1f}%  (Keras {(pred == truth).mean() * 100:.1f}%)")
