from database.db import HashDatabase

db = HashDatabase()
db.setup()

db.insert_many([
    {
        "sha256": "64167e0c3b86189e9beef535310eb6d2ca85bafb96de140b80fd147844e1591f",
        "malware_name": "Developer.Test.Threat",
        "source": "Developer"
    }
])

print("✅ Test threat added successfully!")
print("Total hashes:", db.total_hashes())