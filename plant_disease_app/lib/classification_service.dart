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
  static const List<String> _classNames = ['lime', 'not_citrus', 'other_citrus'];

  Future<void> loadModel() async {
    _interpreter =
        await Interpreter.fromAsset('assets/lime_classifier_quantized.tflite');
    _isolateInterpreter =
        await IsolateInterpreter.create(address: _interpreter.address);
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

    final output = List.generate(1, (_) => List.filled(3, 0.0));

    await _isolateInterpreter.run(input, output);

    final scores = output[0];
    var classIndex = 0;
    for (var i = 1; i < scores.length; i++) {
      if (scores[i] > scores[classIndex]) {
        classIndex = i;
      }
    }
    final confidence = scores[classIndex];

    return ClassificationResult(_classNames[classIndex], confidence);
  }
}
