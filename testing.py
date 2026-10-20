
from scanner.threat_checker import ThreatChecker

sha256 = "49826822D80F6C72E09359EB8A149F7AF993C446C2DBD7CA3A5996D60B948BE6"

checker = ThreatChecker(use_virustotal=False)

checker.add_to_local_db(
    sha256=sha256,
    malware_name="SENTINEL_DEMO_TEST",
    source="manual"
)

result = checker.check_local(sha256)

print("SHA-256:", sha256)
print("Database lookup:", result)
