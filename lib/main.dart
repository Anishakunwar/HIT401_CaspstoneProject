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

    final result = await _classifier.classify(imageFile);

    // Stage 2 runs unless Stage 1 is confident this isn't citrus. It has its
    // own "other" class for photos that aren't a plain-background leaf, so
    // Stage 1's confidence isn't used to gate it further.
    final confidentlyNotCitrus =
        result.label == 'not_citrus' && result.confidence >= _minConfidence;
    DiseaseResult? disease;
    if (_diseaseReady && !confidentlyNotCitrus) {
      try {
        disease = await _disease.classify(imageFile);
      } catch (_) {
        disease = null;
      }
    }

    setState(() {
      _result = result;
      _diseaseResult = disease;
      _isClassifying = false;
    });
  }

  static const double _minDiseaseConfidence = 0.80;

  String? _diseaseText() {
    final d = _diseaseResult;
    if (d == null) return null;
    const howTo = 'For a disease check, place one leaf on plain white paper '
        'and take a close-up.';
    if (d.label == 'other') return 'Leaf check: $howTo';
    if (d.confidence < _minDiseaseConfidence) {
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
      case 'lime':
        return 'lime';
      case 'other_citrus':
        return 'other citrus';
      default:
        return 'not citrus';
    }
  }

  String _statusText() {
    if (_isClassifying) return 'Analyzing...';
    if (_result == null) return 'Take a photo of a leaf and we\'ll check its health';

    final confidencePct = (_result!.confidence * 100).toStringAsFixed(1);

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
      default: // 'not_citrus'
        return 'This doesn\'t look like a citrus plant at all ($confidencePct% confidence)';
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
                    ? 'Scan a plant for disease'
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
