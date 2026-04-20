# Example 8: List of structs with CSV override
records = [
  { "id": 1, "name": "alice", "score": 92 },
  { "id": 2, "name": "bob",   "score": 87 },
]

output = """
Audit summary
-------------
Raw table (CSV):

records|csv
"""
return output
