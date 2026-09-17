import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'classification_service.dart';

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

  @override
  void initState() {
    super.initState();
    _classifier.loadModel();
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
      _isClassifying = true;
    });

    final result = await _classifier.classify(imageFile);

    setState(() {
      _result = result;
      _isClassifying = false;
    });
  }

  String _statusText() {
    if (_isClassifying) return 'Analyzing...';
    if (_result == null) return 'Take a photo of a leaf and we\'ll check its health';

    final confidencePct = (_result!.confidence * 100).toStringAsFixed(1);
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
