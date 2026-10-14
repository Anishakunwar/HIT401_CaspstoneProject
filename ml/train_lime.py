import tensorflow as tf

DATA_DIR = "data"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="training",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

print("Classes found:", train_ds.class_names)

preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input

IMG_SHAPE = IMG_SIZE + (3,)

base_model = tf.keras.applications.MobileNetV2(
    input_shape=IMG_SHAPE,
    include_top=False,
    weights="imagenet",
)
base_model.trainable = False

data_augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.1),
    tf.keras.layers.RandomZoom(0.1),
])

inputs = tf.keras.Input(shape=IMG_SHAPE)
x = data_augmentation(inputs)
x = preprocess_input(x)
x = base_model(x, training=False)
x = tf.keras.layers.GlobalAveragePooling2D()(x)
outputs = tf.keras.layers.Dense(3, activation="softmax")(x)
model = tf.keras.Model(inputs, outputs)

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

model.summary()

checkpoint = tf.keras.callbacks.ModelCheckpoint(
    "lime_classifier.keras",
    save_best_only=True,
    monitor="val_accuracy",
    mode="max",
)

# Class sizes are uneven (lime is the smallest class), so weight each
# class's loss inversely to how many images it has. (Earlier removed this
# on a wrong theory that it caused the diagram misclassification — it
# didn't; removing it just broke lime recognition without fixing the
# diagram. Restored, with counts updated for the added synthetic images.)
import pathlib
data_dir = pathlib.Path(DATA_DIR)
class_counts_named = {
    d.name: len(list(d.glob("*.jpg")))
    for d in sorted(data_dir.iterdir()) if d.is_dir()
}
ordered_names = sorted(class_counts_named.keys())
class_counts = {i: class_counts_named[name] for i, name in enumerate(ordered_names)}
total = sum(class_counts.values())
class_weight = {i: total / (len(class_counts) * count) for i, count in class_counts.items()}
print("Class counts:", class_counts_named)
print("Class weights:", class_weight)

EPOCHS = 10

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    class_weight=class_weight,
    callbacks=[checkpoint],
)

print("Best model saved as lime_classifier.keras")