from scanner.virustotal import VirusTotalUploader

vt = VirusTotalUploader()

analysis = vt.upload_file(r"C:\Users\udity\Downloads\eicar.com")

print(analysis)