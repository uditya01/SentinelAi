import json
import glob
from collections import Counter

files = sorted(glob.glob(
    "ai/dataset/ember_dataset_2018_2/ember2018/train_features_*.jsonl"
))
counts = Counter()
examples = {}

for path in files:
    with open(path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            label = repr(record.get("label"))
            counts[label] += 1
            examples.setdefault(label, (
                path, record.get("label"), record.get("avclass")
            ))

print("\n=== LABEL COUNTS ===")
for label, count in counts.most_common():
    print(f"{label}: {count:,}")

print("\n=== EXAMPLES ===")
for label, example in examples.items():
    print(f"{label}: {example}")
