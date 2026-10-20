
from pathlib import Path
import numpy as np
import ember
import lightgbm as lgb

MODEL_PATH = Path(
    "ai/dataset/ember_dataset_2018_2/ember2018/model.txt"
)

# Load the trained model
model = lgb.Booster(model_file=str(MODEL_PATH))
extractor = ember.PEFeatureExtractor(2)

# Ask for a PE file to test
file_path = input("Enter the path to a Windows .exe or .dll file: ")
path = Path(file_path.strip().strip('"'))

if not path.is_file():
    raise FileNotFoundError(f"File not found: {path}")

# Read bytes and extract EMBER features
bytez = path.read_bytes()
features = extractor.feature_vector(bytez)

# Validate feature dimensions
features = np.asarray(features, dtype=np.float32).reshape(1, -1)

print("Feature shape:", features.shape)
print("Expected features:", model.num_feature())

if features.shape[1] != model.num_feature():
    raise ValueError("Feature count does not match the model!")

# Predict
probability = float(model.predict(features)[0])

print(f"Model malicious-class score: {probability:.6f}")
print("Feature extraction and prediction completed.")
