from winotify import Notification, audio


class NotificationManager:

    def threat_detected(self, malware_name, file_path):

        toast = Notification(
            app_id="Sentinel AI",
            title="🛡 Threat Detected",
            msg=f"{malware_name}\n\nFile has been quarantined successfully.",
        )

        toast.set_audio(audio.Default, loop=False)
        toast.show()

    def scan_completed(self, scanned, threats):

        toast = Notification(
            app_id="Sentinel AI",
            title="Scan Complete",
            msg=f"Scanned: {scanned}\nThreats Found: {threats}",
        )

        toast.show()