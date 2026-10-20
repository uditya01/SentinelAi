import hashlib
from typing import Optional


CHUNK_SIZE = 65536  


def compute_sha256(file_path: str) -> tuple[Optional[str], Optional[str]]:
   
    try:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                h.update(chunk)
        return h.hexdigest(), None

    except PermissionError:
        return None, "Permission denied"
    except FileNotFoundError:
        return None, "File not found"
    except OSError as e:
        return None, str(e)


def is_known_malicious(sha256: str, known_hashes: set[str]) -> bool:
    
    return sha256.lower() in known_hashes