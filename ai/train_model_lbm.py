"""
train_model_lbm.py

Sentinel AI
LightGBM Training Pipeline

Part 1
"""

import json
import logging
import os
import time
from datetime import datetime

import joblib
import lightgbm as lgb
import pandas as pd

from sklearn.model_selection import train_test_split

from dataset_loader import DatasetLoader

from config import (
    MODEL_PATH,
    MODEL_INFO_PATH,
    LIGHTGBM_PARAMS,
    NUM_BOOST_ROUNDS,
    RANDOM_STATE,
    TEST_SIZE,
)

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("SentinelAI")

# ============================================================
# DATASET
# ============================================================


def load_dataset():

    logger.info("=" * 60)
    logger.info("Loading EMBER Dataset")
    logger.info("=" * 60)

    start = time.time()

    loader = DatasetLoader()

    X, y = loader.load_dataset()

    logger.info("Dataset Loaded Successfully")

    logger.info("Samples : %d", len(y))

    logger.info("Features : %d", X.shape[1])

    logger.info("Time : %.2f sec", time.time() - start)

    return X, y


# ============================================================
# TRAIN / VALIDATION SPLIT
# ============================================================


def split_dataset(X, y):

    logger.info("Creating Train/Test Split...")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y
    )

    logger.info("Training Samples : %d", len(y_train))

    logger.info("Validation Samples : %d", len(y_test))

    return X_train, X_test, y_train, y_test


# ============================================================
# LIGHTGBM DATASET
# ============================================================


def build_lgb_dataset(X_train, X_test, y_train, y_test):

    logger.info("Building LightGBM Dataset...")

    train_set = lgb.Dataset(
        X_train,
        label=y_train
    )

    valid_set = lgb.Dataset(
        X_test,
        label=y_test
    )

    return train_set, valid_set


# ============================================================
# MAIN
# ============================================================


def main():

    X, y = load_dataset()

    X_train, X_test, y_train, y_test = split_dataset(X, y)

    train_set, valid_set = build_lgb_dataset(
        X_train,
        X_test,
        y_train,
        y_test
    )

    logger.info("Everything Loaded Successfully.")

    logger.info("Proceed to Part 2 (Training)")


if __name__ == "__main__":
    main()