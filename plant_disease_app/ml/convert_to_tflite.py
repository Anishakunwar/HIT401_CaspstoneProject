import tensorflow as tf

model = tf.keras.models.load_model("lime_classifier.keras")

converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.optimizations = [tf.lite.Optimize.DEFAULT]
tflite_model = converter.convert()

with open("lime_classifier_quantized.tflite", "wb") as f:
    f.write(tflite_model)

print("Saved lime_classifier_quantized.tflite")