from pathlib import Path
from functools import lru_cache

import numpy as np
import lightgbm as lgb
import ember

PROJECT_ROOT = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    PROJECT_ROOT / "ai" / "dataset" / "ember_dataset_2018_2" / "ember2018" / "model.txt"
)

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB


@lru_cache(maxsize=1)
def _load_detector():
    """Load the trained model and feature extractor once."""
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"EMBER model not found at: {MODEL_PATH}")

    model = lgb.Booster(model_file=str(MODEL_PATH))
    extractor = ember.PEFeatureExtractor(2)

    if extractor.dim != model.num_feature():
        raise ValueError(
            f"Feature mismatch: extractor={extractor.dim}, "
            f"model={model.num_feature()}"
        )

    return model, extractor


def predict_file(file_path: str) -> dict:
    """
    Return the EMBER model score for a supported Windows PE file.

    The score is a model prediction, not proof that a file is malicious
    or safe. Unsupported files and extraction failures raise exceptions.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    size = path.stat().st_size
    if size <= 0:
        raise ValueError("File is empty.")

    if size > MAX_FILE_SIZE:
        raise ValueError("File exceeds the 100 MB analysis limit.")

    bytez = path.read_bytes()

    if not bytez.startswith(b"MZ"):
        raise ValueError("File is not a Windows PE executable.")

    model, extractor = _load_detector()

    features = extractor.feature_vector(bytez)
    features = np.asarray(features, dtype=np.float32).reshape(1, -1)

    if features.shape[1] != model.num_feature():
        raise ValueError(
            f"Feature mismatch: got {features.shape[1]}, "
            f"expected {model.num_feature()}"
        )

    score = float(model.predict(features)[0])

    return {
        "score": score,
        "model": "EMBER LightGBM",
        "features": int(features.shape[1]),
    }
