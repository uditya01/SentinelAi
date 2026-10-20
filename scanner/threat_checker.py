
from hashlib import sha256
import os
import sys
import json
import time
import urllib.request
import urllib.error
from scanner.models import ThreatInfo, CLEAN, THREAT, SUSPICIOUS, UNKNOWN
from scanner.ml_detector import predict_file
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import HashDatabase
from scanner.models import ThreatInfo, CLEAN, THREAT, SUSPICIOUS, UNKNOWN


VT_API_URL = "https://www.virustotal.com/api/v3/files/{}"
VT_RATE_LIMIT = 4  
VT_MIN_INTERVAL = 60 / VT_RATE_LIMIT  


VT_THREAT_THRESHOLD = 5


class ThreatChecker:

    def __init__(
    self,
    vt_api_key: Optional[str] = None,
    db_path: Optional[str] = None,
    use_virustotal: bool = True,
    abort_flag=None,
    ):
        self.abort_flag = abort_flag or (lambda: False)
        self.vt_api_key = vt_api_key or os.environ.get("VT_API_KEY", "")
        self.use_virustotal = use_virustotal and bool(self.vt_api_key)
        self._last_vt_call = 0.0
        

        kwargs = {"db_path": db_path} if db_path else {}
        self.db = HashDatabase(**kwargs)
        self.db.setup()

   
    def check(self, sha256: str, file_path: Optional[str] = None) -> ThreatInfo:
        """
        Check the local database, VirusTotal, and EMBER when applicable.
        Unknown or unavailable results are never automatically marked clean.
        """
        if self.abort_flag():
            return ThreatInfo(verdict=UNKNOWN, source="")

        if not sha256:
            return ThreatInfo(verdict=UNKNOWN, source="")

        sha256 = sha256.lower()

      
        try:
            result = self.check_local(sha256)
        except Exception as e:
            print(f"[threat_checker] Local lookup failed: {e}")
            result = None

        if self.abort_flag():
            return ThreatInfo(verdict=UNKNOWN, source="")

        if result is not None and result.verdict == THREAT:
            return result

        
        vt_result = None
        # Line 73: Add this debug print
        print(
            f"[VT DEBUG] enabled={self.use_virustotal}, "
            f"key_present={bool(self.vt_api_key)}, "
            f"cancelled={self.abort_flag()}"
        )

        # Line 73: Add this debug print
        print(
            f"[VT DEBUG] enabled={self.use_virustotal}, "
            f"key_present={bool(self.vt_api_key)}, "
            f"cancelled={self.abort_flag()}"
        )

        if self.use_virustotal:
            if self.abort_flag():
                return ThreatInfo(verdict=UNKNOWN, source="")

            vt_result = self._check_virustotal(sha256)

            if vt_result is not None and vt_result.verdict in (THREAT, SUSPICIOUS):
                return vt_result

        
        if self.abort_flag():
            return ThreatInfo(verdict=UNKNOWN, source="")

        ml_result = None
        if file_path:
            try:
                prediction = predict_file(file_path)
                score = prediction["score"]

                print(f"[threat_checker] EMBER score for {file_path}: " f"{score:.6f}")

                #
                if score >= 0.90:
                    ml_result = ThreatInfo(
                        verdict=SUSPICIOUS,
                        source="ember_lightgbm",
                        malware_name="High EMBER malicious-class score",
                        ml_score=score,
                    )

            except (OSError, ValueError, RuntimeError, ImportError) as e:
                print(f"[threat_checker] EMBER unavailable for this file: {e}")
            except Exception as e:
                print(f"[threat_checker] EMBER prediction failed: {e}")

        if ml_result is not None:
            return ml_result

        if vt_result is not None and vt_result.verdict == CLEAN:
            return vt_result

        
        return ThreatInfo(
            verdict=UNKNOWN,
            source="ember_lightgbm" if file_path else "",
        )

    def add_to_local_db(
        self, sha256: str, malware_name: str = "", source: str = "manual"
    ):
        """Manually add a hash to the local database."""
        self.db.insert_many(
            [
                {
                    "sha256": sha256,
                    "malware_name": malware_name,
                    "source": source,
                }
            ]
        )


    def check_local(self, sha256: str) -> Optional[ThreatInfo]:
        try:
            sha256 = sha256.lower()
            row = self.db.lookup(sha256)

            print("=" * 60)
            print("LOCAL DATABASE CHECK")
            print(f"SHA256: {sha256}")
            print(f"Lookup Result: {row}")
            print("=" * 60)

            # No match
            if row is None:
                return None

            # Match found
            print("✓ LOCAL DATABASE MATCH FOUND!")

            return ThreatInfo(
                verdict="THREAT",
                source="local_db",
                malware_name=row.get("malware_name", "Malware"),
                detection_count=1,
                total_engines=1,
            )

        except Exception as e:
            print(f"[threat_checker] Local DB error: {e}")
            return None

    def _check_virustotal(self, sha256: str) -> Optional[ThreatInfo]:
        print("[VT DEBUG] Entering VirusTotal check")

        
        if self.abort_flag() or not self._wait_for_rate_limit():
            return None

        
        if self.abort_flag():
            return None

        url = VT_API_URL.format(sha256)
        req = urllib.request.Request(
            url,
            headers={
                "x-apikey": self.vt_api_key,
                "Accept": "application/json",
            },
        )

        try:
            
            if self.abort_flag():
                return None

            print("\n🌐 Checking VirusTotal...")
            print("SHA256:", sha256)

            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            print("✓ VirusTotal response received")
        except urllib.error.HTTPError as e:
            if e.code == 404:
               
                return ThreatInfo(verdict=UNKNOWN, source="virustotal")
            print(f"[threat_checker] VT HTTP error {e.code}: {e.reason}")
            return None
        except Exception as e:
            print(f"[threat_checker] VT request failed: {e}")
            return None
        finally:
            self._last_vt_call = time.time()

        return self._parse_vt_response(data)

    def _parse_vt_response(self, data: dict) -> ThreatInfo:
        try:
            stats = data["data"]["attributes"]["last_analysis_stats"]
            results = data["data"]["attributes"].get("last_analysis_results", {})

            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            total = sum(stats.values())
            flagged = malicious + suspicious
            print(f"VirusTotal detections: {flagged}/{total}")

            
            names = [
                v.get("result", "")
                for v in results.values()
                if v.get("category") in ("malicious", "suspicious") and v.get("result")
            ]
            malware_name = _most_common(names) or "Unknown Malware"

            if malicious >= VT_THREAT_THRESHOLD:
                verdict = THREAT
            elif flagged >= 2:
                verdict = SUSPICIOUS
            else:
                verdict = CLEAN
            print("Verdict:", verdict)
            return ThreatInfo(
                verdict=verdict,
                source="virustotal",
                malware_name=malware_name if verdict != CLEAN else "",
                detection_count=flagged,
                total_engines=total,
            )

        except (KeyError, TypeError) as e:
            print(f"[threat_checker] VT parse error: {e}")
            return ThreatInfo(verdict=UNKNOWN, source="virustotal")

    def _wait_for_rate_limit(self) -> bool:
        """Wait for the VirusTotal rate limit, allowing cancellation."""
        while True:
            if self.abort_flag():
                return False

            elapsed = time.time() - self._last_vt_call
            remaining = VT_MIN_INTERVAL - elapsed

            if remaining <= 0:
                return True

            time.sleep(min(0.2, remaining))

def _most_common(lst: list[str]) -> str:
    if not lst:
        return ""
    return max(set(lst), key=lst.count)
