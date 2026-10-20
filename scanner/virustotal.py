import os
import time
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()


class VirusTotalUploader:
    """
    Handles uploading unknown files to VirusTotal
    and retrieving their analysis results.
    """

    BASE_URL = "https://www.virustotal.com/api/v3"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("VT_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "VirusTotal API key not found. "
                "Please set VT_API_KEY in your .env file."
            )

  

    def upload_file(self, file_path):
        """
        Upload a file to VirusTotal.

        Returns
        -------
        analysis_id : str | None
        """

        if not os.path.exists(file_path):
            print("[VT] File does not exist.")
            return None

        print(f"\n🌐 Uploading {os.path.basename(file_path)} to VirusTotal...")

        with open(file_path, "rb") as f:
            file_data = f.read()

        boundary = "----SentinelAIBoundary"

        body = []

        body.append(f"--{boundary}".encode())
        body.append(
            (
                f'Content-Disposition: form-data; '
                f'name="file"; filename="{os.path.basename(file_path)}"\r\n'
                f"Content-Type: application/octet-stream\r\n"
            ).encode()
        )

        body.append(file_data)

        body.append(f"\r\n--{boundary}--\r\n".encode())

        payload = b"\r\n".join(body)

        request = urllib.request.Request(
            f"{self.BASE_URL}/files",
            data=payload,
            method="POST",
            headers={
                "x-apikey": self.api_key,
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        )

        try:

            with urllib.request.urlopen(request, timeout=60) as response:

                result = json.loads(response.read().decode())

                analysis_id = result["data"]["id"]

                print("✓ Upload successful")
                print("Analysis ID:", analysis_id)

                return analysis_id

        except urllib.error.HTTPError as e:

            print(f"[VT] HTTP Error {e.code}")

            try:
                print(e.read().decode())
            except Exception:
                pass

            return None

        except Exception as e:

            print("[VT]", e)

            return None