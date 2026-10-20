import json
from pathlib import Path

import ember
import lightgbm as lgb
import numpy as np
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix, classification_report

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "ai" / "dataset" / "ember_dataset_2018_2" / "ember2018"
MODEL = DATA / "model.txt"
TEST = DATA / "test_features.jsonl"
SAMPLES_PER_CLASS = 100000

print("Loading existing model...")
model = lgb.Booster(model_file=str(MODEL))
extractor = ember.PEFeatureExtractor(2)
print("Model features:", model.num_feature())

X, y = [], []
counts = {0: 0, 1: 0}

print("Reading test records and extracting a balanced sample...")
with TEST.open("r", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        label = record.get("label")
        if label not in (0, 1) or counts[label] >= SAMPLES_PER_CLASS:
            continue
        vector = extractor.process_raw_features(record)
        if vector.shape != (model.num_feature(),) or not np.isfinite(vector).all():
            raise ValueError(f"Invalid feature vector for {record.get('sha256')}")
        X.append(vector)
        y.append(label)
        counts[label] += 1
        if all(counts[c] >= SAMPLES_PER_CLASS for c in (0, 1)):
            break

print("Samples:", counts)
if not all(counts[c] == SAMPLES_PER_CLASS for c in (0, 1)):
    raise RuntimeError("Could not collect enough samples for both classes.")

print("Predicting...")
scores = model.predict(np.asarray(X, dtype=np.float32))
predictions = (scores >= 0.90).astype(int)

print("\n=== EMBER MODEL SAMPLE EVALUATION ===")
print("Samples:", len(y))
print("Accuracy:", round(accuracy_score(y, predictions), 4))
print("Precision:", round(precision_score(y, predictions, zero_division=0), 4))
print("Recall:", round(recall_score(y, predictions, zero_division=0), 4))
print("F1-score:", round(f1_score(y, predictions, zero_division=0), 4))
print("Confusion matrix [ [TN, FP], [FN, TP] ]:")
print(confusion_matrix(y, predictions))
print("\nClassification report:")
print(classification_report(y, predictions, target_names=["Benign", "Malware"], zero_division=0))
print("NOTE: This is a balanced 2,000-record sample, not the full test-set result.")
print("NOTE: LIEF version differs from the version used to compute EMBER v2 features.")
