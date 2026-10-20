
from scanner.hash_utils import compute_sha256
from scanner.threat_checker import ThreatChecker

file_path = "sentinel_test_copy.txt"

sha256, error = compute_sha256(file_path)

if error:
    print("Hashing error:", error)
else:
    print("File:", file_path)
    print("SHA-256:", sha256)

    checker = ThreatChecker(use_virustotal=False)
    result = checker.check(sha256, file_path=file_path)

    print("Verdict:", result.verdict)
    print("Source:", result.source)
    print("Threat name:", result.malware_name)
