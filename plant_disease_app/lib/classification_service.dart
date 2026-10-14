import 'dart:io';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

class ClassificationResult {
  final String label;
  final double confidence;
  ClassificationResult(this.label, this.confidence);
}

class ClassificationService {
  late final Interpreter _interpreter;
  late final IsolateInterpreter _isolateInterpreter;
  // Keep this order identical to the alphabetic class order in ml/train.py.
  static const List<String> _classNames = [
    'apple', 'banana', 'lime', 'not_fruit', 'other_citrus', 'other_fruit'
  ];

  Future<void> loadModel() async {
    _interpreter =
        await Interpreter.fromAsset('assets/fruit_classifier_quantized.tflite');
    _isolateInterpreter =
        await IsolateInterpreter.create(address: _interpreter.address);
  }

  Future<ClassificationResult> classify(File imageFile) async {
    final bytes = await imageFile.readAsBytes();
    final image = img.decodeImage(bytes);
    if (image == null) {
      throw Exception('Could not decode image');
    }

    // Transparent PNGs (such as product cutouts) have black RGB values in
    // fully transparent pixels. Flatten them onto white so the model sees
    // the same kind of background used by its training images.
    final opaqueImage = image.hasAlpha
        ? (img.Image(width: image.width, height: image.height, numChannels: 3)
          ..clear(img.ColorRgb8(255, 255, 255)))
        : image;
    if (image.hasAlpha) {
      img.compositeImage(opaqueImage, image);
    }
    final resized = img.copyResize(opaqueImage, width: 224, height: 224);

    final input = List.generate(
      1,
      (_) => List.generate(
        224,
        (y) => List.generate(
          224,
          (x) {
            // Raw 0-255 values on purpose — the model's own preprocess_input
            // layer (baked in at training time) normalizes internally.
            // Normalizing again here double-scales the input and breaks
            // classification.
            final pixel = resized.getPixel(x, y);
            return [
              pixel.r.toDouble(),
              pixel.g.toDouble(),
              pixel.b.toDouble(),
            ];
          },
        ),
      ),
    );

    final output = List.generate(1, (_) => List.filled(_classNames.length, 0.0));

    await _isolateInterpreter.run(input, output);

    final scores = output[0];
    var classIndex = 0;
    for (var i = 1; i < scores.length; i++) {
      if (scores[i] > scores[classIndex]) {
        classIndex = i;
      }
    }
    final confidence = scores[classIndex];

    // Lime and other citrus are closely related classes. Use their combined
    // probability as a stricter gate so a weak citrus guess is reported as
    // uncertain instead of being treated as citrus (and sent to the leaf
    // disease model).
    const limeIndex = 2;
    const otherCitrusIndex = 4;
    const minCitrusConfidence = 0.70;
    final isCitrus = classIndex == limeIndex || classIndex == otherCitrusIndex;
    final citrusConfidence = scores[limeIndex] + scores[otherCitrusIndex];
    if (isCitrus && citrusConfidence < minCitrusConfidence) {
      return ClassificationResult('uncertain', citrusConfidence);
    }

    return ClassificationResult(_classNames[classIndex], confidence);
  }
}
