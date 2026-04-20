# Example: Using various native tools
text = "Hello, World!"
uppercase_text = uppercase(text)
lowercase_text = lowercase(text)

numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
count = len(numbers)
joined = join(numbers, " + ")

json_data = to_json({"name": "Alice", "scores": numbers}, 2)
parsed = from_json('{"x": 10, "y": 20}')
parsed_sum = parsed.x + parsed.y

output = """
Original text: ${text}
Uppercase: ${uppercase_text}
Lowercase: ${lowercase_text}

Numbers: ${numbers|csv}
Sum: ${total}
Count: ${count}
Joined: ${joined}

JSON output:
${json_data}

Parsed sum: ${parsed_sum}
"""
return output
