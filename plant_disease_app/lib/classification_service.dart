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
  static const List<String> _classNames = ['lime', 'other_citrus'];

  Future<void> loadModel() async {
    _interpreter =
        await Interpreter.fromAsset('assets/lime_classifier_quantized.tflite');
  }

  Future<ClassificationResult> classify(File imageFile) async {
    final bytes = await imageFile.readAsBytes();
    final image = img.decodeImage(bytes);
    if (image == null) {
      throw Exception('Could not decode image');
    }

    final resized = img.copyResize(image, width: 224, height: 224);

    final input = List.generate(
      1,
      (_) => List.generate(
        224,
        (y) => List.generate(
          224,
          (x) {
            final pixel = resized.getPixel(x, y);
            return [
              (pixel.r / 127.5) - 1.0,
              (pixel.g / 127.5) - 1.0,
              (pixel.b / 127.5) - 1.0,
            ];
          },
        ),
      ),
    );

    final output = List.generate(1, (_) => List.filled(1, 0.0));

    _interpreter.run(input, output);

    final score = output[0][0];
    final classIndex = score > 0.5 ? 1 : 0;
    final confidence = classIndex == 1 ? score : 1 - score;

    return ClassificationResult(_classNames[classIndex], confidence);
  }
}
