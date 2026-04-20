# Cy Language Tutorial

Cy is a scripting language designed for AI to write and humans to read. This tutorial covers the language syntax — for embedding Cy in Python, see the [README](../README.md#python-api).

## Language Design Philosophy

Cy combines familiar syntax from multiple languages:

- **Python-style**: Comments (`#`), variable assignments, data structures (lists `[]`, dictionaries `{}`), function calls `func(args)`, and logical operators (`and`, `or`, `not`)
- **Bash-style**: String interpolation with `${expr}` syntax
- **C-style**: Code blocks with curly braces `{}`

This combination creates a familiar yet unique syntax optimized for scripting and data processing.

## 1. Basic Syntax and Variables

Variables in Cy work like Python - clean and simple:

```cy
# Variable assignments (Python-style)
name = "Alice"
age = 30
is_active = True    # Use True/False (capitalized)

# Variables in programs
user_type = "premium"
discount = 0.15

# Lists and dictionaries (Python-style)
fruits = ["apple", "banana", "cherry"]
user = {
    "name": "Alice",
    "age": 30,
    "hobbies": ["reading", "coding"]
}

# Reserved literals cannot be reassigned
# ❌ True = "invalid"     # Error: Cannot assign to reserved literal
# ❌ False = "invalid"    # Error: Cannot assign to reserved literal
# ❌ null = "invalid"     # Error: Cannot assign to reserved literal
```

**Compound assignment** operators update a variable in place:

```cy
count = 10
count += 5     # count = 15
count *= 2     # count = 30

items = [1, 2]
items += [3]   # items = [1, 2, 3]

name = "Hello"
name += " World"  # name = "Hello World"
```

All five operators are supported: `+=`, `-=`, `*=`, `/=`, `%=`.

**Important:** Programs must end with a `return` statement to produce output:
```cy
name = "Alice"
return "Hello ${name}!"  # Required!
```

## 2. String Interpolation

Use `${...}` to insert variable values into strings (Bash-style):

```cy
# Basic interpolation
name = "Alice"
age = 30
greeting = "Hello ${name}!"
message = "User ${name} is ${age} years old"

# Object property access
user = {"name": "Alice", "email": "alice@example.com"}
info = "Contact: ${user.name} at ${user.email}"

# Multiline strings with interpolation
report = """
Dear ${name},
Your account is active.
Best regards, The Team
"""

# Advanced: Complex expressions in interpolation
data = {"users": [{"name": "Alice"}]}
output = """User: ${data["users"][0]["name"]}"""

# Enhanced interpolation with complex expressions
items = ["apple", "banana", "cherry"]
multiplier = 2.5
result = "Processing item ${(len(items) * multiplier) / 2 + 11.1}"

# Function calls and boolean logic in interpolation
age = 25
score = 85
status = "User is ${age >= 18 and score > 80}"

# Multiline expressions with whitespace handling
nested_data = {"config": {"settings": {"max_items": 100}}}
report = """
Configuration Summary:
${
    nested_data["config"]["settings"]["max_items"] * 2
}
"""
```

## 3. Data Structure Access

Two syntax options for accessing data:

```cy
user = {
    "name": "Alice",
    "contact": {"email": "alice@example.com"},
    "scores": [85, 92, 78]
}

# Outside interpolation - both work for objects
name = user.name              # Dot notation
name = user["name"]           # Bracket notation
first_score = user["scores"][0]  # Brackets for lists

# Inside interpolation ${} - use dot notation for objects
output = "User: ${user.name}, Email: ${user.contact.email}"
output2 = "First score: ${user.scores[0]}"
```

**Field assignment** with dot notation — including auto-creation of intermediate dicts:

```cy
alert = {}
alert.severity = "high"              # same as alert["severity"] = "high"
alert.enrichment.geo.country = "US"  # auto-creates intermediate dicts

return alert
# {"severity": "high", "enrichment": {"geo": {"country": "US"}}}
```

## 3.1. Null Safety and the `??` Operator

All field and index access in Cy is **null-safe** — missing fields and out-of-bounds indices return `null` instead of crashing:

```cy
alert = {"user": {"name": "Alice"}}

# Deep access — returns null, never errors
dept = alert.user.department.name   # null (department doesn't exist)
city = alert.user.address.city      # null

# Bracket notation is also null-safe
score = alert["metadata"]["risk_score"]  # null

# List out-of-bounds returns null
items = ["a", "b"]
third = items[5]   # null (not an error)
```

The **`??` (null-coalescing) operator** provides defaults for `null` only — unlike `or`, which replaces all falsy values:

```cy
alert = {"source_ip": "10.0.0.1", "count": 0, "tags": []}

# ?? only replaces null
ip = alert.source_ip ?? "0.0.0.0"    # "10.0.0.1" (not null, kept)
count = alert.count ?? 0              # 0 (the actual value, not replaced)
tags = alert.tags ?? []               # [] (the actual value, not replaced)
missing = alert.severity ?? "low"     # "low" (field is null)

# vs 'or' — replaces all falsy values (0, "", [], {})
count_bad = alert.count or 99         # 99 (0 is falsy — wrong!)

# Chain ?? for multiple fallbacks
city = alert.billing_city ?? alert.shipping_city ?? "Unknown"
```

**When to use which:**
- Use `??` when `0`, `""`, or `[]` are valid values you want to keep
- Use `or` when you want a default for anything falsy

## 4. Mathematical and Logical Operations

```cy
# Math operations
sum = 10 + 5
product = 4 * 3
ratio = amount / balance

# Comparison operators
is_large = amount > 1000
is_equal = x == y

# Logical operators (use English words, not symbols)
needs_review = is_large and ratio > 0.3
is_valid = not is_error
either = option1 or option2

# Membership operator — works on lists, dicts, and strings
allowed = ["admin", "editor"]
has_access = "admin" in allowed       # True
is_missing = not ("viewer" in allowed)  # True (use not() for negation)

config = {"debug": True, "env": "prod"}
has_debug = "debug" in config         # True (checks keys)

greeting = "Hello World"
has_hello = "Hello" in greeting       # True (substring check)
```

## 5. Control Flow

```cy
# If/elif/else statements
score = 85
grade = "F"
if (score >= 90) {
    grade = "A"
} elif (score >= 80) {
    grade = "B"
} else {
    grade = "C"
}

# Conditional expressions (ternary-like syntax)
# Returns a value based on condition - perfect for assignments
score = 85
grade = if (score >= 90) { "A" } elif (score >= 80) { "B" } else { "C" }

# Create union types when branches return different types
flag = True
value = if (flag) { 42 } else { "text" }  # Type: number | string

# Use in arithmetic or other expressions
x = 5
result = (if (x > 3) { 10 } else { 20 }) + 5  # result = 15

# Nested conditional expressions
age = 25
category = if (age < 13) { "child" } elif (age < 18) { "teen" } else { if (age < 65) { "adult" } else { "senior" } }

# For-in loops
items = [1, 2, 3, 4, 5]
results = []
for (item in items) {
    processed = item * 2
    results = results + [processed]  # + operator for list concatenation
}

# Nested for-in loops
matrix_result = []
for (row in [[1, 2], [3, 4]]) {
    for (col in row) {
        matrix_result = matrix_result + [col * 10]
    }
}

# For-in with conditionals
numbers = [1, 2, 3, 4, 5, 6]
evens = []
for (num in numbers) {
    if (num % 2 == 0) {
        evens = evens + [num]
    }
}

# List comprehensions — concise transform/filter
users = [
    {"name": "Alice", "role": "admin"},
    {"name": "Bob", "role": "user"},
    {"name": "Carol", "role": "admin"}
]
names = [u.name for(u in users)]                           # ["Alice", "Bob", "Carol"]
admins = [u.name for(u in users) if(u.role == "admin")]    # ["Alice", "Carol"]

nums = [1, 2, 3, 4, 5]
doubled = [n * 2 for(n in nums)]                           # [2, 4, 6, 8, 10]
evens = [n for(n in nums) if(n % 2 == 0)]                  # [2, 4]

# Use in expressions
admin_count = len([u for(u in users) if(u.role == "admin")])

# Numeric iteration with range()
for (i in range(0, 5)) {
    log("Iteration ${i}")   # 0, 1, 2, 3, 4
}

# While loops
counter = 0
total = 0
while (counter < 5) {
    total = total + counter
    counter = counter + 1
}

# Return statements (exit early)
value = 10
if (value < 0) {
    return "Error: negative value"
}
output = "Value is positive: ${value}"
```

### List Comprehensions

Concise syntax for transforming and filtering lists in a single expression:

```cy
users = [
    {"name": "Alice", "role": "admin", "score": 95},
    {"name": "Bob", "role": "user", "score": 72},
    {"name": "Carol", "role": "admin", "score": 88}
]

# Extract a field
names = [u.name for(u in users)]
# ["Alice", "Bob", "Carol"]

# Filter + extract
admin_names = [u.name for(u in users) if(u.role == "admin")]
# ["Alice", "Carol"]

# Transform values
doubled = [u.score * 2 for(u in users)]
# [190, 144, 176]

# With tool calls
upper_names = [str::uppercase(u.name) for(u in users)]
# ["ALICE", "BOB", "CAROL"]

# Combine with len() for counting
admin_count = len([u for(u in users) if(u.role == "admin")])
# 2
```

## 6. Error Handling

Cy supports comprehensive try/catch/finally blocks for robust error handling:

```cy
# Basic error handling
result = "success"
try {
    value = 10 / 0
} catch (e) {
    result = "Error: ${e}"
}
output = result  # "Error: Line 3, Col 17: Division by zero"

# Multiple error types
errors = []
try {
    x = undefined_variable
} catch (e) {
    errors = errors + ["${e}"]
}

try {
    result = some_tool()
} catch (e) {
    errors = errors + ["${e}"]
}

# Try/catch with finally
cleanup_done = False
try {
    data = risky_operation()
} catch (e) {
    output = "Failed: ${e}"
} finally {
    cleanup_done = True  # Always executes
}

# Nested error handling for fallbacks
result = ""
try {
    result = primary_method()
} catch (e1) {
    try {
        result = fallback_method()
    } catch (e2) {
        result = "All methods failed"
    }
}
```

## 6.1. Static Type Checking (Optional)

Cy includes an optional static type checker that catches type errors at compile-time, before your code runs. This helps catch bugs early and makes your code more reliable.

### Enabling Type Checking

Type checking is **disabled by default** for backward compatibility. Enable it by passing `check_types=True`:

<!-- py-test: skip -->
```python
from cy_language.interpreter import Cy

# Enable type checking
cy = Cy(check_types=True)

# Now type errors are caught at compile-time!
code = """
a = 5
b = "text"
result = a + b  # ERROR: Cannot add number and string
return result
"""

cy.run(code)  # Raises CompilerError before execution
```

### What Gets Type Checked

The type checker validates:

- **Arithmetic operations**: `+`, `-`, `*`, `/`, `%`
- **Comparisons**: `<`, `>`, `<=`, `>=`, `==`, `!=`
- **Boolean operations**: `and`, `or`, `not`
- **Field access**: `obj.field`
- **Indexed access**: `array[0]`, `obj["key"]`
- **Conditionals**: `if`/`elif`/`else` blocks
- **Loops**: `while` loops

### Type Checking Examples

**Arithmetic Type Errors:**
```cy
# ❌ Type error - can't add number and string
x = 5
y = "hello"
result = x + y  # ERROR: Cannot add number and string

# ✅ Valid - same types
a = 10
b = 20
sum = a + b     # OK - both numbers

name = "Hello "
greeting = name + "World"  # OK - both strings
```

**Field Access Type Errors:**
```cy
# ❌ Type error - field doesn't exist
user = {"name": "Alice", "age": 30}
email = user.email  # ERROR: Field 'email' not found. Available: name, age

# ✅ Valid - field exists
name = user.name    # OK - field exists
age = user.age      # OK - field exists
```

**Literal String Key Checking:**
```cy
# The type checker validates literal string keys at compile-time
data = {"status": "active", "count": 42}

# ✅ Valid - key exists
status = data["status"]     # OK
count = data["count"]       # OK

# ❌ Type error - key doesn't exist
missing = data["missing"]   # ERROR: Key 'missing' not found

# ⚠️ Variable keys can't be checked at compile-time
key = "missing"
value = data[key]          # No compile-time error (runtime check only)
```

**Consistency between x.field and x["field"]:**
```cy
# Both notations behave the same for literal keys!
obj = {"a": 1, "b": 2}

# Both work
val1 = obj.a      # ✅ OK - field access
val2 = obj["a"]   # ✅ OK - literal key access

# Both fail
bad1 = obj.missing      # ❌ ERROR - field not found
bad2 = obj["missing"]   # ❌ ERROR - key not found
```

### Python-like Truthy/Falsy

Cy allows **any type** in conditionals and loops, just like Python. This makes conditionals more natural and flexible:

```cy
# All these are valid with type checking enabled!

# Falsy values (evaluate to false)
if (null) { return "yes" }     # Won't execute - null is falsy
if (0) { return "yes" }        # Won't execute - 0 is falsy
if ("") { return "yes" }       # Won't execute - empty string is falsy

# Truthy values (evaluate to true)
if (5) { return "yes" }        # Executes - non-zero number is truthy
if ("hello") { return "yes" }  # Executes - non-empty string is truthy

# Common patterns
count = 10
while (count) {                # Executes while count != 0
    count = count - 1
}

data = ""
if (data) {
    log("Has data: ${data}")   # Only runs if data is non-empty
}
```

**Truthy/Falsy Summary:**
- **Falsy**: `null`, `0`, `""` (empty string)
- **Truthy**: Everything else (non-zero numbers, non-empty strings, objects, arrays)

### Error Messages

Type errors show clear messages with line and column numbers:

```cy
# This code has type errors:
x = 5
y = "text"
result = x + y
```

**Error Message:**
```
Type checking failed:
Line 3, Col 10: Cannot add number and string
```

### Multiple Errors Collected

The type checker finds **all errors at once**, not just the first one:

```cy
# Multiple errors
error1 = 5 + "text"      # Type error
error2 = "hello" - 10    # Type error
```

**Error Message:**
```
Type checking failed:
Line 2, Col 10: Cannot add number and string
Line 3, Col 10: Cannot subtract number from string
```

### When to Use Type Checking

**Use `check_types=True` when:**
- Building production workflows
- Working with complex data transformations
- Want to catch errors early in development
- Need extra confidence in code correctness

**Use `check_types=False` (default) when:**
- Prototyping quickly
- Working with very dynamic data
- Need maximum flexibility
- Backward compatibility with existing code

### Type Checking with Dynamic Data

The type checker gracefully handles input data (which has unknown types at compile-time):

```cy
# Input data has unknown types - type checker allows it
suspicious_ip = input["ip"]      # OK - input type unknown
score = input["score"]           # OK - input type unknown

# But once types are known, they're validated
result = score + 10              # OK if score is a number
```

Type checking is **smart** - it validates what it can verify at compile-time while allowing flexibility for runtime data.

### Tool Type Validation

Native tools like `len()`, `str()`, `int()` now have proper type signatures. With `check_types=True`, tool return types are validated:

```cy
# ✅ Valid - len() returns number
items = [1, 2, 3]
count = len(items)      # count is number
total = count * 10      # OK: number * number

# ❌ Type error caught before execution!
count = len(items)
message = "Count: " + count  # Error: Can't add string + number (need str(count))

# ✅ Fixed with explicit conversion
message = "Count: " + str(count)  # OK: string + string
```

This enables **type-safe workflow composition** - chain multiple scripts knowing tool outputs are validated.

### Integration Tools with Type Safety

Type validation extends to **custom integration tools** (like VirusTotal, Shodan, threat intelligence APIs). When you register Python functions with type hints, Cy automatically extracts their signatures for both parameter and return type validation.

#### Registering Integration Tools

<!-- py-test: skip -->
```python
from cy_language import Cy
from cy_language.tool_registry_builder import export_app_tools, build_tool_registry

# Define integration tools with type hints
def virustotal_ip_reputation(ip_address: str) -> dict:
    """Get IP reputation from VirusTotal."""
    # Call VirusTotal API...
    return {
        "ip": ip_address,
        "malicious_score": 8,
        "reputation": "suspicious",
        "detections": 5
    }

def shodan_host_lookup(ip: str, detailed: bool = False) -> dict:
    """Look up host information in Shodan."""
    # Call Shodan API...
    return {
        "ip": ip,
        "ports": [80, 443, 22],
        "os": "Linux",
        "country": "US"
    }

# Register tools with FQN (Fully Qualified Name)
app_tools = {
    "app::virustotal::ip_reputation": virustotal_ip_reputation,
    "app::shodan::host_lookup": shodan_host_lookup
}

# Use with type checking enabled
cy = Cy(check_types=True, tools=app_tools)
```

#### Type-Safe Workflows with Integration Tools

```cy
target_ip = "8.8.8.8"

# Call integration tools - return types are validated
vt_data = app::virustotal::ip_reputation(ip_address=target_ip)
shodan_data = app::shodan::host_lookup(ip=target_ip)

# Extract fields - type inference knows vt_data is an object
malicious_score = vt_data.malicious_score  # Type: any (from object field)

# Type checking prevents invalid operations
bad_concat = vt_data + " is suspicious"  # ❌ TypeError: cannot add object and string

# Valid operations pass
report = {
    "ip": target_ip,
    "vt_score": malicious_score,
    "shodan_ports": shodan_data.ports
}
return report
```

#### Static Analysis for Workflow Composition

The `analyze_types()` API works with integration tools to validate workflows **without executing them**:

<!-- py-test: skip -->
```python
from cy_language import analyze_types
from cy_language.tool_registry_builder import build_tool_registry

# Build registry from your app manager
class AppManager:
    def get_all_tools(self):
        return {
            "app::virustotal::ip_reputation": virustotal_ip_reputation,
            "app::shodan::host_lookup": shodan_host_lookup
        }

app_manager = AppManager()
registry = build_tool_registry(
    include_native=True,
    app_manager=app_manager
)

# Task A: Analyze IP with VirusTotal
task_a_script = """
ip = input.ip_address
vt_result = app::virustotal::ip_reputation(ip_address=ip)
return vt_result
"""

task_a_input = {"type": "object", "properties": {"ip_address": {"type": "string"}}}
task_a_output = analyze_types(task_a_script, task_a_input, tool_registry=registry)
# Returns: {"type": "object"} - from virustotal_ip_reputation return type

# Task B: Use Task A's output
task_b_script = """
score = input.malicious_score
if (score > 7) {
    risk = "HIGH"
} else {
    risk = "LOW"
}
return {"risk": risk, "score": score}
"""

# Validate Task B using Task A's output as input
task_b_output = analyze_types(task_b_script, task_a_output, tool_registry=registry)
# ✅ Workflow validated at design-time, BEFORE executing any API calls!
```

**Note:** Native tools (`len`, `str`, etc.) are **automatically available** in `analyze_types()` - you don't need to include them in `tool_registry`. The `tool_registry` parameter is only for adding custom/integration tools. Scripts can call `len([1,2,3])` even if you only pass app tools.

<!-- py-test: skip -->
```python
# Simplified: Just pass app tools (native tools are automatic)
from cy_language.tool_signature import ToolRegistry

app_tools_dict = {"app::virustotal::ip_reputation": {...}}
tool_registry = ToolRegistry.from_dict(app_tools_dict)

analyze_types(script, input_schema, tool_registry=tool_registry)
# ✅ Both app::virustotal::ip_reputation AND len() are available!
```

#### Benefits for Integration Workflows

1. **Catch errors before API calls**: Type errors detected at compile-time, not after expensive API requests
2. **Automatic signature extraction**: Type hints → parameter/return type validation
3. **Workflow composition**: Chain tasks with guaranteed type compatibility
4. **FQN support**: Tools keep their namespace (e.g., `app::virustotal::ip_reputation`)
5. **Optional parameters**: Default values automatically detected

<!-- py-test: skip -->
```python
# Example: Prevent costly mistakes
script = """
ip = "192.168.1.1"
vt_data = app::virustotal::ip_reputation(ip_address=ip)

# ERROR caught at compile-time (before calling VirusTotal API):
combined = vt_data + " analysis"  # ❌ TypeError: cannot add object and string

return combined
"""

try:
    cy.run(script)  # Type error raised BEFORE calling VirusTotal
except TypeError as e:
    print(f"Workflow invalid: {e}")
    # Fix the workflow before wasting API quota
```

This is especially valuable for security/threat intelligence workflows where API calls may be rate-limited, costly, or time-sensitive.

#### Advanced: Merging Tool Registries

For more control over which tool sources to include, you can use the **`.merge()`** method to combine multiple `ToolRegistry` objects:

<!-- py-test: skip -->
```python
from cy_language.tool_registry_builder import (
    export_native_tools,
    export_app_tools,
    export_custom_tools
)

# Start with native tools (len, str, etc.)
registry = export_native_tools()

# Merge integration tools from app manager
app_registry = export_app_tools(app_manager)
registry.merge(app_registry)  # Combines registries

# Optionally merge custom tools
custom_tools = {"custom::tools::my_tool": my_function}
custom_registry = export_custom_tools(custom_tools)
registry.merge(custom_registry)

# Use the merged registry
output_schema = analyze_types(script, input_schema, tool_registry=registry)
```

**When to use manual merge vs `build_tool_registry()`:**

<!-- py-test: skip -->
```python
# ✅ Use build_tool_registry() for convenience (recommended)
registry = build_tool_registry(
    include_native=True,
    app_manager=app_manager,
    custom_tools=custom_tools
)
# Internally, this creates empty registry and merges all sources

# ✅ Use manual merge for fine control
registry = export_native_tools()  # Start with native only
if use_integration_tools:
    registry.merge(export_app_tools(app_manager))  # Conditionally add
# Don't add MCP tools in this example
```

**Key Functions:**

- `export_native_tools()` → Returns `ToolRegistry` with `native::tools::*` functions (len, str, etc.)
- `export_app_tools(app_manager)` → Returns `ToolRegistry` with `app::*` integration tools
- `export_custom_tools(tools_dict)` → Returns `ToolRegistry` from custom Python functions
- `build_tool_registry(...)` → Convenience function that merges all sources automatically

The `.merge()` method returns `self` for chaining:
<!-- py-test: skip -->
```python
registry = export_native_tools().merge(app_registry).merge(custom_registry)
```

### Type Analysis API

For programmatic type analysis, Cy provides the `analyze_types()` API that combines type inference and validation in a single pass:

<!-- py-test: skip -->
```python
from cy_language import analyze_types, data_to_schema

# Analyze code without input schema (uses Any type for input)
code = """
result = 5 + 10
return result
"""
schema = analyze_types(code)  # Returns: {"type": "number"}

# With input schema for precise validation
code = """
name = input.name
greeting = "Hello " + name
return greeting
"""
input_schema = data_to_schema({"name": "Alice", "age": 30})
schema = analyze_types(code, input_schema)  # Returns: {"type": "string"}

# Type errors raise TypeError
code = """
result = 5 + "text"  # Invalid operation!
return result
"""
try:
    schema = analyze_types(code)
except TypeError as e:
    print(e)  # "Type validation failed:\nLine 2: cannot add number and string..."
```

**Key Features:**
- **Single-pass**: Validates types AND infers output schema in one call
- **Raises TypeError**: Invalid operations throw exceptions with line numbers
- **Works with/without input**: Provide `input_schema` for validation, or omit for flexibility
- **Any type escape hatch**: Unknown types (like input without schema) skip validation

### Strict Input Validation for Workflow Composition

When composing workflows (Task A → Task B), field mismatches between task outputs and inputs cause runtime failures. The `strict_input` parameter catches these errors at validation time:

<!-- py-test: skip -->
```python
from cy_language import analyze_types

# Task A produces this output
task_a_output = {
    "type": "object",
    "properties": {
        "threat_score": {"type": "number"},
        "country": {"type": "string"},
        "ip": {"type": "string"}
    }
}

# Task B with a TYPO in field name
task_b_code = """
score = input["threat_score"]
country = input["coutry"]  # TYPO: should be "country"!
return "Threat from " + country + ": " + str(score)
"""

# Permissive mode (default): Typo goes unnoticed
schema = analyze_types(task_b_code, task_a_output, strict_input=False)
# ✅ Passes (but will fail at runtime!)

# Strict mode: Typo caught at validation time
try:
    schema = analyze_types(task_b_code, task_a_output, strict_input=True)
except TypeError as e:
    print(e)
    # TypeError: Type validation failed:
    # Line 3: field 'coutry' not found in input schema. Available fields: threat_score, country, ip
```

**Benefits:**
- **Early detection**: Catches field mismatches before workflow execution
- **Helpful errors**: Lists all available fields in the schema
- **Typo prevention**: Catches common typos like "coutry" instead of "country"
- **Contract enforcement**: Ensures Task B actually gets what Task A provides
- **Backward compatible**: `strict_input=False` by default for existing code

**When to use strict_input:**
- ✅ Validating workflow composition (Task A → Task B → Task C)
- ✅ Ensuring API contract compliance
- ✅ Catching field name typos early
- ❌ Exploratory development with unknown schemas

## 7. Function/Tool Calls

Cy supports multiple types of function calls with a namespace system:

```cy
# Namespace System - Organize tools with Fully Qualified Names (FQNs)

# Native functions - can use short names or FQNs
count = len([1, 2, 3])                       # Short name (resolves to native::tools::len)
count = native::tools::len([1, 2, 3])        # Explicit FQN

# Standalone function calls
log("Processing data")                       # Works as statement!
log("Item: ${item}")                         # In loops, conditionals, try/catch

# App namespace tools
result = app::test::test1("data")            # App-level tools
analysis = app::demo::greet("World")         # Custom app functionality

# Archetype namespace tools
processed = arc::example::analyze("data")    # Archetype-based tools

# Regular tool calls (must be registered)
sum = add(5, 3)                              # Positional args
result = calculate(amount=100, rate=0.05)    # Named args (use =, not :)
result = calculate(100, rate=0.05)           # Mixed: positional first, then named

# MCP calls (requires async setup) - always use FQN
math_result = mcp::demo::add(a=10, b=15)
ip_reputation = mcp::virustotal::virustotal_ip_reputation(ip="8.8.8.8")

# Ambiguity handling - detects conflicts at compile time
# If both app::tools::process and native::tools::process exist:
# ✅ app::tools::process(data)    # Explicit FQN - works
# ✅ native::tools::process(data)  # Explicit FQN - works
# ❌ process(data)                 # Ambiguous - compile error with helpful message
```

## 7.1. Native Functions Reference

Cy provides 40+ built-in functions organized by domain. All are available without imports. Here are the most commonly used ones:

### Data Functions

**`len(arg)`** - Returns the length of a string, list, or dict
```cy
my_list = ["apple", "banana", "cherry"]
count = len(my_list)              # Returns: 3

text = "Hello"
chars = len(text)                 # Returns: 5

data = {"name": "Alice", "age": 30}
fields = len(data)                # Returns: 2
```

**`sum(items)`** - Sums all numbers in a list
```cy
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)              # Returns: 15

scores = [85, 92, 78]
average = sum(scores) / len(scores)  # Calculate average
```

**`str(value)`** - Converts a value to a string
```cy
num = 42
text = str(num)                   # Returns: "42"

# Useful for concatenation without interpolation
result = "The answer is " + str(num)  # "The answer is 42"

# Works with any type
data = [1, 2, 3]
text = str(data)                  # "[1, 2, 3]"
```

### JSON Functions

**`from_json(json_string)`** - Parses JSON string to structured data
```cy
json_text = '{"name": "Alice", "age": 30}'
user = from_json(json_text)
output = "User: ${user.name}, Age: ${user.age}"  # User: Alice, Age: 30

# Handles lists too
json_array = '["apple", "banana", "cherry"]'
fruits = from_json(json_array)
count = len(fruits)               # Returns: 3
```

**`to_json(data, [indent])`** - Converts data structure to JSON string
```cy
user = {"name": "Bob", "age": 25}
json_output = to_json(user)       # '{"name": "Bob", "age": 25}'

# Pretty-print with indentation
pretty = to_json(user, 2)         # Formatted with 2-space indent
output = "User data:\n${pretty}"
```

### String Functions

**`uppercase(text)`** / **`lowercase(text)`** — case conversion:
```cy
name = "alice"
upper_name = uppercase(name)      # "ALICE"
lower_name = lowercase("BOB")    # "bob"

# Also available as str::uppercase(), str::lowercase()
```

**`split(text, delimiter)`** / **`join(items, separator)`** — split and join:
```cy
# Split a string into a list
parts = split("a,b,c", ",")      # ["a", "b", "c"]
words = split("hello world")     # ["hello", "world"] (default: space)

# Join a list into a string
csv = join(["apple", "banana"], ", ")   # "apple, banana"
path = join(["home", "user"], "/")      # "home/user"
```

All string functions — also available with `str::` prefix:

| Function | Description |
|----------|-------------|
| `str::uppercase(text)` | Convert to uppercase |
| `str::lowercase(text)` | Convert to lowercase |
| `str::split(text, delimiter=" ")` | Split string into list |
| `str::replace(text, old, new)` | Replace substrings |
| `str::trim(text)` | Remove leading/trailing whitespace |
| `startswith(text, prefix)` | Check if string starts with prefix |
| `endswith(text, suffix)` | Check if string ends with suffix |
| `join(items, sep=", ")` | Join list into string |
| `strip_markdown(text)` | Remove markdown code block fences |

### Type Conversion

| Function | Description |
|----------|-------------|
| `str(value)` | Convert to string |
| `int(value)` | Convert to integer |
| `num(value)` | Convert to float |
| `bool(value)` | Convert to boolean |

### List & Math Functions

```cy
numbers = [5, 3, 8, 1, 9]

minimum = min(numbers)              # 1
maximum = max(numbers)              # 9
total = sum(numbers)                # 26
absolute = abs(-42)                 # 42
rounded = round(3.14159, 2)        # 3.14

sorted_list = list::sort(numbers)   # [1, 3, 5, 8, 9]
reversed_list = list::reverse(numbers)  # [9, 1, 8, 3, 5]
first_three = take(numbers, 3)      # [5, 3, 8]
indices = list::range(0, 5)         # [0, 1, 2, 3, 4]
```

| Function | Description |
|----------|-------------|
| `len(value)` | Length of string, list, or dict |
| `sum(items)` | Sum a list of numbers |
| `min(items)` / `max(items)` | Minimum / maximum value |
| `abs(value)` | Absolute value |
| `round(value, decimals=0)` | Round a number |
| `list::sort(items)` | Sort list ascending |
| `list::reverse(items)` | Reverse list |
| `take(items, n)` | First n elements |
| `list::range(start, end, step=1)` | Generate number sequence |

### Dictionary Functions

| Function | Description |
|----------|-------------|
| `keys(data)` | Dictionary keys as list |
| `values(data)` | Dictionary values as list |

### Time & Date Functions

All timestamps are ISO 8601 format with timezone.

```cy
now = time::now()
one_hour_ago = time::subtract_duration(now, "1h")
next_week = time::add_duration(now, "7d")
```

| Function | Description |
|----------|-------------|
| `time::now(timezone="UTC")` | Current timestamp |
| `time::add_duration(ts, duration)` | Add duration (e.g., `"1h"`, `"7d"`) |
| `time::subtract_duration(ts, duration)` | Subtract duration |
| `time::duration_between(start, end)` | Duration between two timestamps |
| `time::parse_duration(duration)` | Parse duration string to seconds |
| `time::format_duration(seconds)` | Format seconds to human-readable |
| `time::compare(ts1, op, ts2)` | Compare timestamps (`"<"`, `">"`, etc.) |
| `time::from_epoch(seconds)` | Unix epoch → ISO 8601 |
| `time::to_epoch(timestamp)` | ISO 8601 → Unix epoch |

### Network, URL & Regex Functions

| Function | Description |
|----------|-------------|
| `net::is_ipv4(ip)` | Check if valid IPv4 address |
| `net::is_ipv6(ip)` | Check if valid IPv6 address |
| `net::is_ip(ip)` | Check if valid IP (either version) |
| `url::encode(text)` | Percent-encode URL component |
| `url::decode(text)` | Decode percent-encoded string |
| `regex::match(pattern, text)` | Returns True if pattern matches |
| `regex::extract(pattern, text)` | Returns first match or null |

### Logging

**`log(message)`** — writes to stderr, doesn't affect the return value:

```cy
log("Processing started")
items = ["a", "b", "c"]
for (item in items) {
    log("Processing: ${item}")
}
output = "Processed ${len(items)} items"
```

### Complete Example with Native Functions

```cy
# Parse JSON data
json_input = '{"users": [{"name": "alice", "score": 85}, {"name": "bob", "score": 92}]}'
data = from_json(json_input)

# Process data
users = data.users
user_count = len(users)
log("Processing ${user_count} users")

# Calculate statistics
scores = []
names = []
for (user in users) {
    scores = scores + [user.score]
    names = names + [uppercase(user.name)]
    log("Processed user: ${user.name}")
}

total_score = sum(scores)
average = total_score / user_count

# Build result
result = {
    "total_users": user_count,
    "names": join(names, " & "),
    "average_score": average,
    "total_score": total_score
}

# Output as formatted JSON
output = to_json(result, 2)
# Logs go to stderr, output returns as result
```

## 8. Interpolation Modes and Output

```cy
items = ["apple", "banana", "cherry"]
user = {"name": "Alice", "age": 30}

# Format data structures in different ways
csv_output = "CSV: ${items|csv}"
xml_output = "<data>${user|xml}</data>"

# Programs must set output to return results
output = "Processed: ${user.name} is ${user.age} years old"
```

> **Note:** Modern Cy requires a `return` statement. The `output` variable pattern shown above is legacy — always use `return` instead.

## 9. Real-World Examples

### Parallel Processing with For-In Loops

```cy
# Automatically parallelizes when iterations are independent
api_endpoints = ["users", "posts", "comments", "likes"]
api_results = []

# This loop automatically runs in parallel if enabled
for (endpoint in api_endpoints) {
    data = fetch_api(endpoint)  # Each API call is independent
    api_results = api_results + [data]
}

# Processing multiple items with transformations
items = [
    {"id": 1, "value": 100},
    {"id": 2, "value": 200},
    {"id": 3, "value": 300}
]

enriched_items = []
for (item in items) {
    # Independent operations - automatically parallelized
    details = get_item_details(item["id"])
    score = calculate_score(item["value"])

    enriched = {
        "id": item["id"],
        "value": item["value"],
        "details": details,
        "score": score
    }
    enriched_items = enriched_items + [enriched]
}
```

### Basic Data Processing

```cy
# Clean variable assignment syntax
user = {
    "name": "Alice",
    "email": "alice@example.com",
    "scores": [85, 92, 78]
}

# Calculate average
total = user["scores"][0] + user["scores"][1] + user["scores"][2]
average = total / 3

# Determine status
status = "Standard"
if (average >= 90) {
    status = "Excellent"
} elif (average >= 80) {
    status = "Good"
}

needs_review = average < 70 or status == "Standard"

output = """
# User Performance Report
Name: ${user.name}
Email: ${user.email}
Status: ${status}
Average Score: ${average}
Needs Review: ${needs_review}
Scores: ${user.scores|csv}
"""
```

### Advanced Security Analysis with Dynamic Data

```cy
suspicious_ip = input["ip"]
alert_context = input["context"]

# Initialize risk tracking with indexed assignment
ip_risk_scores = {}
ip_risk_scores[suspicious_ip] = 0

# Get reputation data from VirusTotal via MCP
vt_report = mcp::virustotal::virustotal_ip_reputation(ip=suspicious_ip)

malicious_count = vt_report["malicious"]
total_engines = vt_report["total"]

# Calculate and store risk score using indexed assignment
detection_ratio = 0
if (total_engines > 0) {
    detection_ratio = malicious_count / total_engines
}
ip_risk_scores[suspicious_ip] = detection_ratio * 100

# Determine threat level
threat_level = "Low"
if (malicious_count >= 5) {
    threat_level = "Critical"
} elif (malicious_count >= 2) {
    threat_level = "High"
}

output = {
    "ip_address": suspicious_ip,
    "threat_level": threat_level,
    "risk_score": ip_risk_scores[suspicious_ip],
    "recommended_action": threat_level == "Critical" and "BLOCK_IMMEDIATELY" or "MONITOR"
}
```

### Complex E-commerce Example

For a comprehensive e-commerce order processing example demonstrating advanced patterns, see [`examples/complex_example_debugged.cy`](examples/complex_example_debugged.cy). This example shows proper techniques for:
- Handling nested data structures
- Step-by-step calculations
- Complex business logic
- Error handling patterns

## Common Mistakes and FAQ

### ❌ Wrong Syntax → ✅ Correct Syntax

**Comments (Python-style):**

<!-- cy-test: expect-error -->
```cy
// This is wrong
```

```cy
# This is correct
age = 30  # Correct
```

**Boolean literals:**

```cy
# ❌ WRONG — lowercase booleans are treated as undefined variables
flag = true
flag = false
```

```cy
# ✅ CORRECT — capitalized booleans
flag = True
flag = False
```

**Variable assignment:**

```cy
name = "Alice"         # Clean syntax (recommended)
```

<!-- cy-test: expect-error -->
```cy
# ❌ Semicolons are not valid syntax
age = 25; name = "Bob"
```

```cy
# ❌ Reserved literals cannot be reassigned (caught at compile time)
# True = "invalid"    # CompilerError
# null = "test"       # CompilerError
```

**Logical operators:**

<!-- cy-test: expect-error -->
```cy
# ❌ Symbol operators cause syntax errors
result = a && b
```

```cy
# ✅ Use English words
result = a and b
result = a or b
result = not a
```

**Function arguments:**

```cy
# ✅ Positional args
result = func(1, 2)
```

```cy
# ✅ Named args (use =, not :)
result = func(a=1, b=2)
```

```cy
# ✅ Mixed: positional first, then named
result = func(1, b=2)
```

<!-- cy-test: expect-error -->
```cy
# ❌ Named before positional is not allowed
result = func(a=1, 2)
```

<!-- cy-test: expect-error -->
```cy
# ❌ Colon-style named args are not valid
result = func(arg: value)
```

**The + operator is universal:**

```cy
sum = a + b                 # Numbers: addition
msg = "Hello " + name       # Strings: concatenation
combined = [1, 2] + [3, 4]  # Lists: concatenation
# ❌ bad = "text" + 123     # Mixed types: runtime error
```

**Ternary operator:**

<!-- cy-test: expect-error -->
```cy
# ❌ JavaScript-style ternary not supported
status = age >= 18 ? "adult" : "minor"
```

```cy
# ✅ Use conditional expression
status = if (age >= 18) { "adult" } else { "minor" }
```

**Enhanced Interpolation:**
```cy
# Complex expressions work in interpolation
output = "Sum: ${add(5, 3)}"           # Function calls work!
output = "Result: ${a + b * 2}"        # Math expressions work!
output = "Status: ${age >= 18 and score > 80}"  # Boolean logic works!

# Multiline expressions with proper whitespace handling
result = """
Complex calculation: ${
    (len(items) * multiplier) / 2 + 11.1
}
"""

# Mixed function calls and data access
report = "User ${users[0]['name']} has ${len(users)} friends"

# Can also extract to variables for readability
sum = add(5, 3)                        # Works for simple cases
output = "Sum: ${sum}"
```

**Standalone Function Calls:**
```cy
# Function calls work as standalone statements
log("Starting process")                # Works as statement!
for (item in items) {
    log("Processing: ${item}")          # Works in loops!
}

# Cleaner syntax for side effects
log("Starting...")                     # Perfect for logging
notify_user("Task complete")           # Perfect for notifications
log_event("User login")                # Perfect for auditing
```

**Indexed Assignment:**
```cy
dict[key] = value                      # Dictionary key assignment
dict["key"] = value                    # Direct key assignment
data["users"][index] = user            # Nested assignment
scores[player] = points                # Variable key assignment
matrix[0][1] = "X"                     # Multi-dimensional assignment
```

**Comments in object literals:**
```cy
# Comments work inside structures (on their own line or after values)
obj = {
    "key": "value",  # inline comment
    "another": 42    # another comment
}

arr = [
    1, 2, 3  # items in a list
]
```

**Null/None values:**

```cy
# ❌ None/nil are not Cy keywords (they parse as undefined variables)
# Use null (lowercase) which is the Cy null literal
data = null              # This is the correct null literal

# ✅ Correct null checks
if (data == null) { }    # Check for null explicitly
if (not data) { }        # Falsy check (null, 0, "" are all falsy)
if (data == "") { }      # Check for empty string specifically
```

### Common Error Messages

**"Tool not found"** - All 40+ native functions (`len`, `sum`, `str`, `split`, `replace`, `range`, `sort`, `min`, `max`, `from_json`, `to_json`, `log`, etc.) are always available. For other tools, you need to register them:
<!-- py-test: skip -->
```python
# Native functions work automatically - no imports needed!
cy = Cy()
cy.run('output = "Count: ${len([1, 2, 3])}"')  # Works!

# For additional tools (LLM, custom tools), register them:
import cy_language.native_functions
from cy_language.ui.tools import default_registry
interpreter = Cy(tools=default_registry.get_tools_dict())
```

**"Cannot index object of type NoneType"** - You're trying to access `input` without providing input data.

**`in` operator** — Cy supports membership testing on lists, dicts (checks keys), and strings (substring check): `if ("admin" in roles) { ... }`. For negation, use `not ("x" in list)` instead of `not in`.

**"Index out of range"** - Cy is null-safe: out-of-bounds list access returns `null` instead of raising an error. However, indexed *assignment* (`list[i] = value`) requires the index to be within bounds.

**"`None` not found" or "Unexpected token"** - Cy uses `null` (lowercase), not Python's `None`. Write `data = null` for null values, and use `??` for null defaults: `value = data ?? "fallback"`.

### Setup Requirements

**For LLM functions:** Set `OPENAI_API_KEY` environment variable and import LLM functions:
<!-- py-test: skip -->
```python
import os
import cy_language.llm_functions
os.environ['OPENAI_API_KEY'] = 'your_key_here'
```

**For MCP tools:** Requires async setup:
<!-- py-test: skip -->
```python
async def main():
    mcp_servers = {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}
    interpreter = await Cy.create_async(mcp_servers=mcp_servers)
    result = await interpreter.run_async(program)
```

## 10. Parallel Execution

Cy automatically parallelizes independent async operations for dramatic speedups:

```cy
# These three operations run in parallel automatically!
user_data = fetch_user(id=123)    # All three
posts = fetch_posts(id=123)       # execute
friends = fetch_friends(id=123)   # simultaneously

# Sequential when there are dependencies
token = login(user, pass)         # Must complete first
data = fetch(token=token)         # Needs token
result = process(data=data)       # Needs data
```

Enable in Python:
<!-- py-test: skip -->
```python
# Sequential: ~3 seconds
interpreter = await Cy.create_async(tools=tools, enable_parallel=False)

# Parallel: ~1 second (3x faster!)
interpreter = await Cy.create_async(tools=tools, enable_parallel=True)

# Control threshold (default=2)
interpreter = await Cy.create_async(
    tools=tools,
    enable_parallel=True,
    parallel_threshold=3  # Need 3+ operations to parallelize
)

# Output validation (default=True)
# Ensures all code paths set output or use return
interpreter = Cy(validate_output=True)   # Compile-time validation (recommended)
interpreter = Cy(validate_output=False)  # Disable for analysis/testing
```

**Best for:** API calls, database queries, file I/O operations
**Note:** Loops and conditionals create barriers - operations inside can't parallelize with outside operations

### Output Validation

By default, Cy validates at compile time that all code paths include a `return` statement:

<!-- py-test: skip -->
```python
# With validation (default)
cy = Cy(validate_output=True)

# This fails at compile time — no return statement
# cy.run('x = 5')  # CompilerError: No return statement found

# This works
cy.run('return 5')

# Disable for analysis or testing
cy_analyzer = Cy(validate_output=False)
```

## Key Takeaways

1. **Mix of familiar syntax:** Python-style `#` comments and data structures, clean variable names, C-style `{}`
2. **Clean variables:** Use simple `name = "Alice"` syntax - no dollar signs needed except in interpolation
3. **Direct code:** Programs start directly with code, no version pragma needed
4. **Essential patterns:** Always use `return` to produce output, use `True`/`False`, prefer readable code structure
5. **Null safety:** All field/index access returns `null` on missing data — never crashes. Use `??` for null-only defaults
6. **Membership testing:** `"admin" in roles` works on lists, dicts (keys), and strings (substrings). Negate with `not ("x" in list)`
7. **Conditional Expressions:** Ternary-like syntax `if (cond) { val1 } elif (cond2) { val2 } else { val3 }` with automatic union type inference
8. **For-in loops:** Modern `for (item in items) { }` syntax with automatic parallelization
9. **List Comprehensions:** Concise `[expr for(x in items) if(cond)]` for transforming and filtering lists
10. **Enhanced Interpolation:** Complex expressions, function calls, and math work in `${}`
11. **Exception Handling:** Use `try`/`catch`/`finally` for robust error recovery
12. **Parallel Execution:** Independent async operations automatically run in parallel for 2-3x speedups
13. **Namespace System:** Organize tools with FQNs like `app::test::tool()` or use short names
14. **Standalone Calls:** Function calls work as statements - perfect for `log()` and logging
15. **Native Functions:** 40+ built-in functions organized by domain — data (`len`, `sum`), strings (`split`, `replace`, `trim`, `uppercase`), JSON (`from_json`, `to_json`), math (`abs`, `min`, `max`, `round`), time (`now`, `add_duration`), iteration (`range`), and more. Always available, no setup needed. LLM and MCP tools require registration.
16. **Static Type Checking:** Optional compile-time validation with `check_types=True` - catches errors before runtime with Python-like truthy/falsy semantics
17. **Debugging:** Start simple, test with basic data, build complexity gradually

Start with variable assignments and string interpolation, then gradually add control flow and tool integration as needed!

For more examples, see the `examples/` directory in this repository.
