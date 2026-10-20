"""
config.py

Central configuration for Sentinel AI.

All paths, model settings, training parameters,
and scan configuration are defined here.

Author: Sentinel AI
"""

import os


# ==========================================================
# PROJECT PATHS
# ==========================================================

# ai/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Project root (SentinelAi/)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))

# Dataset
DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "ember_dataset_2018_2",
    "ember2018"
)

# Models
MODELS_DIR = os.path.join(BASE_DIR, "models")

MODEL_PATH = os.path.join(
    MODELS_DIR,
    "sentinel_ai_model.pkl"
)

MODEL_INFO_PATH = os.path.join(
    MODELS_DIR,
    "model_info.json"
)

# Logs (for future use)
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")


# ==========================================================
# DATASET SETTINGS
# ==========================================================

TRAIN_FILE_PREFIX = "train_features_"
TEST_FILE_NAME = "test_features.jsonl"

TRAIN_FILE_EXTENSION = ".jsonl"

RANDOM_STATE = 42

TEST_SIZE = 0.20


# ==========================================================
# LIGHTGBM PARAMETERS
# ==========================================================

LIGHTGBM_PARAMS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "boosting_type": "gbdt",
    "learning_rate": 0.05,
    "num_leaves": 64,
    "max_depth": -1,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "verbosity": -1,
    "seed": RANDOM_STATE,
}


NUM_BOOST_ROUNDS = 500

EARLY_STOPPING_ROUNDS = 30


# ==========================================================
# SCAN SETTINGS
# ==========================================================

SUPPORTED_EXTENSIONS = {
    ".exe",
    ".dll",
    ".sys",
    ".scr",
    ".com",
    ".ocx",
    ".drv",
}

MAX_FILE_SIZE_MB = 500


# ==========================================================
# MALWARE THRESHOLD
# ==========================================================

MALWARE_THRESHOLD = 0.50


# ==========================================================
# LOGGING
# ==========================================================

LOG_LEVEL = "INFO"


# ==========================================================
# AUTO CREATE REQUIRED DIRECTORIES
# ==========================================================

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)