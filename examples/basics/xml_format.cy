# Example 7: XML printer hint using per-expression override
items = ["a", "b"]
output = "<items>${items|xml}</items>"
return output
