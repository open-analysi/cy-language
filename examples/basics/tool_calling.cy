# Example 4: Tool calls with positional and named arguments
numbers = [3, 4, 5]
total = sum(numbers)
count = len(numbers)
output = "Sum of ${numbers|csv} = ${total} (${count} items)"
return output
