
import hashlib
from pathlib import Path
from scanner.threat_checker import ThreatChecker

# Create a harmless test file
test_file = Path("SENTINEL_AI_LOCAL_DB_DEMO.txt")
test_file.write_text(
    "Sentinel AI local database detection demo.\n",
    encoding="utf-8"
)

# Calculate the file's SHA-256 hash
sha256 = hashlib.sha256(test_file.read_bytes()).hexdigest()
print(f"Demo file: {test_file.resolve()}")
print(f"SHA-256: {sha256}")

# Insert its hash into the local threat database
checker = ThreatChecker(use_virustotal=False)
checker.add_to_local_db(
    sha256,
    malware_name="DEMO_KNOWN_HASH",
    source="manual_demo"
)

# Verify that the local database recognizes it
result = checker.check_local(sha256)
print(f"Verdict: {result.verdict if result else 'NOT FOUND'}")
print(f"Source: {result.source if result else 'NONE'}")
print(f"Name: {result.malware_name if result else 'NONE'}")
