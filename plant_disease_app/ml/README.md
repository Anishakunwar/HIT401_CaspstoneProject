# Fruit classifier training

This pipeline trains the app's six output classes: `apple`, `banana`, `lime`, `not_fruit`, `other_citrus`, and `other_fruit`.

## Train and export

From the `plant_disease_app` directory, run:

```sh
python3.12 -m venv ml/.venv
ml/.venv/bin/pip install -r ml/requirements.txt
ml/.venv/bin/python ml/prepare_fruits360.py
ml/.venv/bin/python ml/train.py
ml/.venv/bin/python ml/convert_to_tflite.py
ml/.venv/bin/python ml/evaluate_fruit_tflite.py
```

The prepare step downloads the official Fruits-360 100x100 repository, groups its class folders into the six app labels, and samples up to 2,500 training and 1,000 held-out images per label. The source dataset and prepared images stay under ignored `ml/data/`; the generated Keras checkpoint stays local. The exported TFLite model is written to `assets/fruit_classifier_quantized.tflite`.

The model was evaluated on 4,811 images from the dataset's held-out `Test` split. It scored 90.7% overall. Per-class results are in `fruit_classifier_tflite_metrics.json`; Keras training evaluation is in `fruit_classifier_metrics.json`.

## Limits

Fruits-360 contains isolated produce on a white background and groups all vegetables, nuts, seeds, and mushrooms into `not_fruit`. It does not train the model to reject arbitrary photos such as people, pets, or outdoor scenes, and results on ordinary camera backgrounds may be substantially worse than the held-out score. The disease model is only run for lime and other-citrus predictions.

Dataset source, license, and attribution are recorded in [FRUITS360_ATTRIBUTION.md](FRUITS360_ATTRIBUTION.md). Keep that attribution with redistributed model artifacts.
