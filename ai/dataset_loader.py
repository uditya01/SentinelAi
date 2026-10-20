"""
dataset_loader.py

Loads the EMBER dataset and converts every JSON
record into a flat numerical feature dictionary.

Author: Sentinel AI
"""

import json
import logging
import os

import pandas as pd
from tqdm import tqdm

from config import (
    DATASET_DIR,
    TRAIN_FILE_PREFIX,
    TRAIN_FILE_EXTENSION,
)

from ember_feature_extractor import EmberFeatureExtractor

logger = logging.getLogger(__name__)


class DatasetLoader:

    def __init__(self):

        self.extractor = EmberFeatureExtractor()

    def get_training_files(self):

        files = sorted([
            os.path.join(DATASET_DIR, f)
            for f in os.listdir(DATASET_DIR)
            if f.startswith(TRAIN_FILE_PREFIX)
            and f.endswith(TRAIN_FILE_EXTENSION)
        ])

        if not files:
            raise FileNotFoundError(
                f"No training files found in {DATASET_DIR}"
            )

        return files

    def load_dataset(self):

        files = self.get_training_files()

        logger.info("Loading EMBER dataset...")

        rows = []

        for filepath in tqdm(files):

            with open(filepath, "r", encoding="utf-8") as f:

                for line in f:

                    if not line.strip():
                        continue

                    sample = json.loads(line)

                    feature_dict = self.extractor.extract(sample)

                    rows.append(feature_dict)

        logger.info("Loaded %d samples", len(rows))

        df = pd.DataFrame(rows)

        y = df["label"]

        X = df.drop(columns=["label"])

        logger.info("Feature Matrix Shape : %s", X.shape)

        logger.info("Labels Shape : %s", y.shape)

        return X, y


if __name__ == "__main__":

    logging.basicConfig(level=logging.INFO)

    loader = DatasetLoader()

    X, y = loader.load_dataset()

    print()

    print(X.head())

    print()

    print(y.head())