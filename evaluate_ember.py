
import os
import numpy as np
import lightgbm as lgb
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)

DATA_DIR = r"ai\dataset\ember_dataset_2018_2\ember2018"
MODEL_PATH = os.path.join(DATA_DIR, "model.txt")
BATCH_SIZE = 5000

print("Loading saved LightGBM model...")
model = lgb.Booster(model_file=MODEL_PATH)

print("Model trees:", model.num_trees())
print("Model features:", model.num_feature())

# EMBER vectorized features are float32.
X_path = os.path.join(DATA_DIR, "X_test.dat")
y_path = os.path.join(DATA_DIR, "y_test.dat")

X = np.memmap(X_path, dtype=np.float32, mode="r")
y = np.memmap(y_path, dtype=np.float32, mode="r")

n_features = model.num_feature()

if X.size % n_features != 0:
    raise ValueError(
        f"X_test.dat has {X.size} values, which is not divisible "
        f"by the model's {n_features} features. Check the feature layout."
    )

n_samples = X.size // n_features

if y.size != n_samples:
    raise ValueError(
        f"Test feature rows ({n_samples}) don't match labels ({y.size})."
    )

X = X.reshape(n_samples, n_features)

print("Test samples:", n_samples)
print("Evaluating in batches...")

all_probs = []

for start in range(0, n_samples, BATCH_SIZE):
    end = min(start + BATCH_SIZE, n_samples)
    batch = np.asarray(X[start:end], dtype=np.float32)
    all_probs.append(model.predict(batch))
    print(f"Processed {end:,} / {n_samples:,}")

probs = np.concatenate(all_probs)
labels = np.asarray(y)

# EMBER labels: 0 = benign, 1 = malicious, -1 = unlabeled.
mask = labels != -1
y_true = labels[mask].astype(np.int32)
y_pred = (probs[mask] >= 0.5).astype(np.int32)

if len(y_true) == 0:
    raise ValueError("No labeled test samples were found.")

print("\n=== EMBER TEST RESULTS ===")
print("Labeled samples:", len(y_true))
print(f"Accuracy:  {accuracy_score(y_true, y_pred):.4f}")
print(f"Precision: {precision_score(y_true, y_pred, zero_division=0):.4f}")
print(f"Recall:    {recall_score(y_true, y_pred, zero_division=0):.4f}")
print(f"F1-score:  {f1_score(y_true, y_pred, zero_division=0):.4f}")

print("\nConfusion matrix (rows=true, columns=predicted):")
print(confusion_matrix(y_true, y_pred, labels=[0, 1]))

print("\nClassification report:")
print(classification_report(
    y_true,
    y_pred,
    labels=[0, 1],
    target_names=["Benign", "Malicious"],
    zero_division=0,
))

print("Evaluation finished.")
