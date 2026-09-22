import 'dart:io';
import 'package:image/image.dart' as img;
import 'package:tflite_flutter/tflite_flutter.dart';

class DiseaseResult {
  final String label; // canker | healthy | hlb | other
  final double confidence;
  DiseaseResult(this.label, this.confidence);
}

/// Stage 2: leaf disease check. Trained on single leaves photographed on a
/// plain background, so "other" means "this isn't that kind of photo".
class DiseaseService {
  late final Interpreter _interpreter;
  late final IsolateInterpreter _isolateInterpreter;
  static const List<String> _classNames = ['canker', 'healthy', 'hlb', 'other'];

  Future<void> loadModel() async {
    _interpreter =
        await Interpreter.fromAsset('assets/disease_classifier_quantized.tflite');
    _isolateInterpreter =
        await IsolateInterpreter.create(address: _interpreter.address);
  }

  Future<DiseaseResult> classify(File imageFile) async {
    final bytes = await imageFile.readAsBytes();
    final image = img.decodeImage(bytes);
    if (image == null) {
      throw Exception('Could not decode image');
    }

    final resized = img.copyResize(image, width: 224, height: 224);

    // Raw 0-255 values: the model normalizes internally (same as Stage 1).
    final input = List.generate(
      1,
      (_) => List.generate(
        224,
        (y) => List.generate(224, (x) {
          final pixel = resized.getPixel(x, y);
          return [pixel.r.toDouble(), pixel.g.toDouble(), pixel.b.toDouble()];
        }),
      ),
    );

    final output = List.generate(1, (_) => List.filled(_classNames.length, 0.0));
    await _isolateInterpreter.run(input, output);

    final scores = output[0];
    var best = 0;
    for (var i = 1; i < scores.length; i++) {
      if (scores[i] > scores[best]) best = i;
    }
    return DiseaseResult(_classNames[best], scores[best]);
  }
}
