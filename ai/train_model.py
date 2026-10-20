"""
Sentinel AI
LightGBM Malware Model Training

Part 1
----------------------------------------
• Dataset validation
• JSONL streaming
• Feature loading
• Dataset statistics
• Progress bars
"""

from pathlib import Path
import json
import logging
from typing import List, Tuple

import numpy as np
from tqdm import tqdm


# ==========================================================
# CONFIGURATION
# ==========================================================

DATASET_DIR = Path(
    "ai/dataset/ember_dataset_2018_2/ember2018"
)

TRAIN_FILES = [
    "train_features_0.jsonl",
    "train_features_1.jsonl",
    "train_features_2.jsonl",
    "train_features_3.jsonl",
    "train_features_4.jsonl",
    "train_features_5.jsonl",
]

TEST_FILE = "test_features.jsonl"

MODEL_OUTPUT = Path("ai/models")

MODEL_OUTPUT.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


# ==========================================================
# DATASET VALIDATION
# ==========================================================

def validate_dataset() -> None:

    logging.info("Checking dataset...")

    if not DATASET_DIR.exists():
        raise FileNotFoundError(
            f"Dataset folder not found:\n{DATASET_DIR}"
        )

    missing = []

    for file in TRAIN_FILES:

        if not (DATASET_DIR / file).exists():
            missing.append(file)

    if not (DATASET_DIR / TEST_FILE).exists():
        missing.append(TEST_FILE)

    if missing:

        raise FileNotFoundError(
            f"Missing files:\n{missing}"
        )

    logging.info("Dataset verified successfully.")


# ==========================================================
# JSONL STREAM
# ==========================================================

def stream_jsonl(file_path: Path):

    with open(file_path, "r", encoding="utf-8") as f:

        for line in f:

            yield json.loads(line)


# ==========================================================
# FEATURE EXTRACTION
# ==========================================================

def extract_features(record: dict):

    """
    Converts one EMBER sample
    into numerical features.
    """

    if "label" not in record:
        return None, None

    label = record["label"]

    features = []

    for key, value in record.items():

        if key == "label":
            continue

        if isinstance(value, (int, float)):
            features.append(float(value))

        elif isinstance(value, list):

            for item in value:

                if isinstance(item, (int, float)):
                    features.append(float(item))

    return np.asarray(features, dtype=np.float32), label


# ==========================================================
# LOAD DATASET
# ==========================================================

def load_training_data() -> Tuple[np.ndarray, np.ndarray]:

    logging.info("Loading training dataset...")

    X = []
    y = []

    total_files = len(TRAIN_FILES)

    for index, filename in enumerate(TRAIN_FILES):

        path = DATASET_DIR / filename

        logging.info(
            f"[{index+1}/{total_files}] Reading {filename}"
        )

        for record in tqdm(
            stream_jsonl(path),
            desc=filename,
            unit="samples"
        ):

            features, label = extract_features(record)

            if features is None:
                continue

            X.append(features)
            y.append(label)

    logging.info("Training dataset loaded.")

    return np.array(X), np.array(y)


# ==========================================================
# DATASET SUMMARY
# ==========================================================

def dataset_summary(labels):

    benign = int(np.sum(labels == 0))
    malware = int(np.sum(labels == 1))

    print("\n===============================")
    print(" SENTINEL AI DATASET SUMMARY")
    print("===============================")

    print(f"Total Samples : {len(labels):,}")
    print(f"Benign Files  : {benign:,}")
    print(f"Malware Files : {malware:,}")

    print("===============================\n")


# ==========================================================
# MAIN
# ==========================================================

def main():

    validate_dataset()

    X, y = load_training_data()

    dataset_summary(y)

    print("Feature Matrix Shape :", X.shape)

    print("Dataset Ready.")

    print("Proceed to Part 2 (Training).")


if __name__ == "__main__":
    main()