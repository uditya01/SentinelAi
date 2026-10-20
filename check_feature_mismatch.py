import json
import lightgbm as lgb
from pathlib import Path
from ai.ember_feature_extractor import EmberFeatureExtractor

root = Path("ai/dataset/ember_dataset_2018_2/ember2018")
model_path = root / "model.txt"
sample_path = root / "train_features_1.jsonl"

with sample_path.open("r", encoding="utf-8") as f:
    sample = next(json.loads(line) for line in f if line.strip())

features = EmberFeatureExtractor().extract(sample)
model = lgb.Booster(model_file=str(model_path))

print("Custom features including label:", len(features))
print("Custom features excluding label:", len(features) - 1)
print("Active model expected features:", model.num_feature())
print("Sample label:", sample.get("label"))
print("First 20 feature names:", list(features.keys())[:20])
