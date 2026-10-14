import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'classification_service.dart';
import 'disease_service.dart';

void main() {
  runApp(const PlantDiseaseApp());
}

class PlantDiseaseApp extends StatelessWidget {
  const PlantDiseaseApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Plant Disease Scanner',
      theme: ThemeData(
        colorSchemeSeed: Colors.green,
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}

// Changed from StatelessWidget to StatefulWidget — we now need to
// remember the captured photo so we can display it (that's "state").
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ImagePicker _picker = ImagePicker();
  File? _capturedImage; // null until the user takes/picks a photo
  final ClassificationService _classifier = ClassificationService();
  ClassificationResult? _result;
  bool _isClassifying = false;

  final DiseaseService _disease = DiseaseService();
  DiseaseResult? _diseaseResult;
  bool _diseaseReady = false;

  @override
  void initState() {
    super.initState();
    _classifier.loadModel();
    _loadDisease();
  }

  // The disease model is optional: if it fails to load, Stage 1 still works.
  Future<void> _loadDisease() async {
    try {
      await _disease.loadModel();
      _diseaseReady = true;
    } catch (_) {
      _diseaseReady = false;
    }
  }

  Future<void> _getImage(ImageSource source) async {
    final pickedFile = await _picker.pickImage(
      source: source,
      imageQuality: 90,
    );
    if (pickedFile == null) return; // user cancelled

    final imageFile = File(pickedFile.path);

    setState(() {
      _capturedImage = imageFile;
      _result = null;
      _diseaseResult = null;
      _isClassifying = true;
    });

    // Check the leaf model before deciding this is a fruit. The fruit model's
    // `not_fruit` class also includes leaves, so it must not gate leaf scans.
    DiseaseResult? disease;
    if (_diseaseReady) {
      try {
        disease = await _disease.classify(imageFile);
      } catch (_) {
        disease = null;
      }
    }
    final result = await _classifier.classify(imageFile);

    setState(() {
      _result = result;
      _diseaseResult = disease;
      _isClassifying = false;
    });
  }

  static const double _minDiseaseConfidence = 0.80;

  String? _diseaseText() {
    final d = _diseaseResult;
    if (d == null || d.label == 'other') return null;
    if (d.confidence < _minDiseaseConfidence) {
      if (_result?.label != 'not_fruit') return null;
      return 'Leaf check: inconclusive. Try a sharper close-up of a single '
          'leaf on plain paper.';
    }
    final pct = (d.confidence * 100).toStringAsFixed(0);
    const report = 'This is not a diagnosis — report suspected canker or '
        'greening (HLB) to your local biosecurity authority.';
    switch (d.label) {
      case 'canker':
        return 'Leaf check: possible citrus canker ($pct%). $report';
      case 'hlb':
        return 'Leaf check: possible greening / HLB ($pct%). $report';
      default:
        return 'Leaf check: no sign of canker or greening ($pct%).';
    }
  }

  static const double _minConfidence = 0.60;

  String _labelName(String label) {
    switch (label) {
      case 'uncertain':
        return 'uncertain';
      case 'lime':
        return 'lime';
      case 'other_citrus':
        return 'other citrus';
      case 'apple':
        return 'apple';
      case 'banana':
        return 'banana';
      case 'other_fruit':
        return 'another fruit';
      default:
        return 'not a fruit';
    }
  }

  String _statusText() {
    if (_isClassifying) return 'Analyzing...';
    if (_result == null) return 'Take a photo of a fruit or citrus leaf to identify it';

    final disease = _diseaseResult;
    if (disease != null &&
        disease.label != 'other' &&
        disease.confidence >= _minDiseaseConfidence) {
      return 'Citrus leaf detected';
    }
    if (_result!.label == 'not_fruit' &&
        disease != null &&
        disease.label != 'other') {
      return 'Possible citrus leaf — leaf check inconclusive';
    }

    final confidencePct = (_result!.confidence * 100).toStringAsFixed(1);

    if (_result!.label == 'uncertain') {
      return 'Not sure this is citrus ($confidencePct% combined citrus score). '
          'Try a clear close-up of one fruit on a plain background.';
    }

    // Below this the model is close to guessing; say so instead of showing
    // a label that could easily be wrong.
    if (_result!.confidence < _minConfidence) {
      return 'Not sure — try a clearer, closer photo '
          '(best guess: ${_labelName(_result!.label)}, $confidencePct%)';
    }

    switch (_result!.label) {
      case 'lime':
        return 'Looks like a lime ($confidencePct% confidence)';
      case 'other_citrus':
        return 'This is citrus, but doesn\'t look like a lime ($confidencePct% confidence)';
      case 'apple':
        return 'Looks like an apple ($confidencePct% confidence)';
      case 'banana':
        return 'Looks like a banana ($confidencePct% confidence)';
      case 'other_fruit':
        return 'Looks like another fruit ($confidencePct% confidence)';
      default: // 'not_fruit'
        return 'This doesn\'t look like a fruit ($confidencePct% confidence)';
    }
  }

// Ashish Testing
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Plant Disease Scanner'),
        centerTitle: true,
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Shows the captured photo once there is one, otherwise the leaf icon.
              _capturedImage == null
                  ? Icon(Icons.eco_outlined,
                      size: 96, color: Colors.green.shade600)
                  : ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.file(
                        _capturedImage!,
                        height: 220,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
              const SizedBox(height: 20),
              Text(
                _capturedImage == null
                    ? 'Scan fruit or a citrus leaf'
                    : 'Photo captured',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                _statusText(),
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey.shade600,
                    ),
                textAlign: TextAlign.center,
              ),
              if (_diseaseText() != null) ...[
                const SizedBox(height: 12),
                Text(
                  _diseaseText()!,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Colors.green.shade800,
                      ),
                  textAlign: TextAlign.center,
                ),
              ],
              const SizedBox(height: 40),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.camera_alt),
                  label: const Text('Take Photo'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  onPressed: () => _getImage(ImageSource.camera),
                ),
              ),
              const SizedBox(height: 12),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.photo_library_outlined),
                  label: const Text('Choose from Gallery'),
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                  onPressed: () => _getImage(ImageSource.gallery),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
