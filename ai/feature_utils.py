"""
feature_utils.py

Utility functions for Sentinel AI Feature Extraction.

Author: Sentinel AI
"""

import hashlib
import math
import os


# --------------------------------------------------
# HASHES
# --------------------------------------------------

def calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file."""

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def calculate_md5(file_path: str) -> str:
    """Calculate MD5 hash."""

    md5 = hashlib.md5()

    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)

    return md5.hexdigest()


# --------------------------------------------------
# FILE SIZE
# --------------------------------------------------

def get_file_size(file_path: str) -> int:
    """Return file size in bytes."""

    return os.path.getsize(file_path)




def get_extension(file_path: str) -> str:
    """Return lowercase file extension."""

    return os.path.splitext(file_path)[1].lower()



def calculate_entropy(file_path: str) -> float:
    """
    Shannon entropy.

    High entropy usually indicates
    packed or encrypted executables.
    """

    with open(file_path, "rb") as f:
        data = f.read()

    if len(data) == 0:
        return 0.0

    frequency = [0] * 256

    for byte in data:
        frequency[byte] += 1

    entropy = 0.0

    for count in frequency:

        if count == 0:
            continue

        probability = count / len(data)

        entropy -= probability * math.log2(probability)

    return entropy


def basic_file_info(file_path: str) -> dict:
    """
    Returns common information about a file.
    """

    return {
        "path": file_path,
        "size": get_file_size(file_path),
        "extension": get_extension(file_path),
        "sha256": calculate_sha256(file_path),
        "md5": calculate_md5(file_path),
        "entropy": calculate_entropy(file_path),
    }