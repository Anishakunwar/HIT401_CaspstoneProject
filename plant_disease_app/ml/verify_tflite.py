import tensorflow as tf

DATA_DIR = "data"
IMG_SIZE = (224, 224)
BATCH_SIZE = 32

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATA_DIR,
    validation_split=0.2,
    subset="validation",
    seed=123,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
)

# --- Evaluate the original Keras model ---
keras_model = tf.keras.models.load_model("lime_classifier.keras")
keras_loss, keras_acc = keras_model.evaluate(val_ds)
print(f"Keras model accuracy: {keras_acc:.4f}")

# --- Evaluate the quantized TFLite model ---
interpreter = tf.lite.Interpreter(model_path="lime_classifier_quantized.tflite")
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

correct = 0
total = 0

for images, labels in val_ds:
    for i in range(images.shape[0]):
        img = tf.expand_dims(images[i], axis=0)
        interpreter.set_tensor(input_details[0]["index"], img)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])
        prediction = 1 if output[0][0] > 0.5 else 0
        if prediction == labels[i].numpy():
            correct += 1
        total += 1

tflite_acc = correct / total
print(f"TFLite (quantized) model accuracy: {tflite_acc:.4f}")
print(f"Difference: {abs(keras_acc - tflite_acc):.4f}")