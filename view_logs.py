from threat_log.threat_log import ThreatLog

log = ThreatLog()

for row in log.get_logs():
    print(dict(row))