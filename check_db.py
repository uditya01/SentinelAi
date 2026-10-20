from database.db import HashDatabase

db = HashDatabase()
db.setup()

sha = "64167e0c3b86189e9beef535310eb6d2ca85bafb96de140b80fd147844e1591f"

result = db.lookup(sha)

print(result)
