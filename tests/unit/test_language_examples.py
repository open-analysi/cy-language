"""Tests for the Cy language examples from the design document."""

import json

from cy_language import Cy


def test_example_1_variable_assignment():
    """Test Example 1: Variable assignment + interpolation."""
    interpreter = Cy()

    program = """
    name = "Alice"
    output = "Hi ${name}!"
    return output
    """

    result = interpreter.run(program)
    assert result == '"Hi Alice!"'


def test_example_2_list_printing():
    """Test Example 2: List printing with default markdown printer."""
    # Create interpreter with markdown mode (bullet points)
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    fruits = ["apple", "banana", "cherry",]
    output = "Fruits:\\n${fruits}"
    return output
    """

    result = interpreter.run(program)
    assert "Fruits:" in result
    assert "- apple" in result
    assert "- banana" in result
    assert "- cherry" in result


def test_example_3_struct_access():
    """Test Example 3: Struct access using dot notation."""
    interpreter = Cy()

    program = """
    user = { "id": 7, "name": "Bob" }
    output = "User #${user.id}: ${user.name}"
    return output
    """

    result = interpreter.run(program)
    assert result == '"User #7: Bob"'


def test_example_4_tool_calling():
    """Test Example 4: Tool call with positional arguments."""
    # Create a simple add function
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)

    program = """
    total = add(3, 4)
    output = "3 + 4 = ${total}"
    return output
    """

    result = interpreter.run(program)
    assert result == '"3 + 4 = 7"'


def test_example_5_escaping():
    """Test Example 5: Escaping ${} and $ in strings."""
    interpreter = Cy()

    program = r"""
    output = "Show me \${notAVar} and \$100"
    return output
    """

    result = interpreter.run(program)
    assert result == '"Show me ${notAVar} and $100"'


def test_example_6_multiline_string():
    """Test Example 6: Multiline string with interpolation."""
    interpreter = Cy()

    program = """
    name = "Eve"
    output = \"\"\"
Hello ${name},

This is a multiline string.
\"\"\"
    return output
    """

    result = json.loads(interpreter.run(program))
    assert "Hello Eve," in result
    assert "This is a multiline string." in result
    # Make sure there's a blank line in between
    assert "\n\n" in result


def test_example_7_xml_printer_hint():
    """Test Example 7: XML printer hint using per-expression override."""
    # Set default interpolation mode to markdown
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    items = ["a", "b"]
    output = "<items>${items|xml}</items>"
    return output
    """

    result = interpreter.run(program)
    assert "<items>" in result
    assert "<item>a</item>" in result
    assert "<item>b</item>" in result
    assert "</items>" in result


def test_example_8_csv_override():
    """Test Example 8: List of structs with CSV override."""
    # Set default interpolation mode to markdown
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    # List of structs example with a CSV override
    records = [
      { "id": 1, "name": "alice", "score": 92 },
      { "id": 2, "name": "bob",   "score": 87 },
    ]

    output = \"\"\"
Audit summary
-------------
Raw table (CSV):

${records|csv}
\"\"\"
    return output
    """

    result = interpreter.run(program)
    assert "Audit summary" in result
    assert "-------------" in result
    assert "Raw table (CSV):" in result
    assert "id,name,score" in result
    assert "1,alice,92" in result
    assert "2,bob,87" in result


# Re-enabled: Testing if field access on function results now works
def test_example_9_external_tools_variables():
    """Test Example 9: With external Tools/Directives and Variables."""
    # Create mock tools and variables for the test
    tools = {
        "alert_to_text": lambda alert: (
            f"{alert.get('title', '')}: {alert.get('description', '')}"
        ),
        "semantic_search": lambda db, query, k=10: {
            "semantic": [f"similar alert {i + 1}" for i in range(k)]
        },
    }

    variables = {"alert_db": "alerts_vector_db"}

    interpreter = Cy(tools=tools, variables=variables, interpolation_mode="markdown")

    program = """
alert = input
alert_semantic = alert_to_text(alert) # Takes an alert and makes it a string that can be easily used for semantic similarity matching in a vector database. The return type is "String"
similar_alert_corpus = semantic_search(alert_db, alert_semantic).semantic # A list of Strings that represent the details of each of the most similar alerts we found.

output = \"\"\"
Here is a new alert:
${alert_semantic}

Here is a list of alerts that are similar:
${similar_alert_corpus}

Let's use the similar alerts to identify the disposition of the new alert.
Be conservative, if the results are mixed, it's ok to say Unknown.

Return a JSON.
{
  "disposition": <add response here>
  "explanation": <add your reasoning here>
}
\"\"\"
return output
    """

    # Create a sample alert
    alert = {
        "title": "Suspicious Login",
        "description": "Multiple failed login attempts detected from unusual IP address",
    }

    result = json.loads(interpreter.run(program, alert))

    assert "Here is a new alert:" in result
    assert (
        "Suspicious Login: Multiple failed login attempts detected from unusual IP address"
        in result
    )
    assert "Here is a list of alerts that are similar:" in result
    assert "- similar alert 1" in result
    assert "- similar alert 10" in result  # Should have 10 similar alerts
    assert "Let's use the similar alerts to identify the disposition" in result
    assert "Return a JSON." in result
    assert '"disposition":' in result
    assert '"explanation":' in result


def test_example_10_factorial_calculator():
    """Test Example 10: Factorial calculator with control flow and mathematics.

    Updated: control flow now uses current syntax.
    """
    variables = {"n": 5}
    interpreter = Cy(variables=variables)

    program = """
x = n
fact = 1

if (x > 0) {
    while (x > 1) {
        fact = fact * x
        x = x - 1
    }
    output = "Factorial of ${n} is ${fact}"
} else {
    output = "${n} is not a positive number"
}
return output
"""

    result = interpreter.run(program)
    assert result == '"Factorial of 5 is 120"'


def test_example_10_factorial_calculator_edge_cases():
    """Test Example 10 with edge cases: zero, negative, and one.

    Updated: control flow now uses current syntax.
    """
    # Test case 1: Zero input
    variables = {"n": 0}
    interpreter = Cy(variables=variables)

    program = """
x = n
fact = 1

if (x > 0) {
    while (x > 1) {
        fact = fact * x
        x = x - 1
    }
    output = "Factorial of ${n} is ${fact}"
} else {
    output = "${n} is not a positive number"
}
return output
"""

    result = interpreter.run(program)
    assert result == '"0 is not a positive number"'

    # Test case 2: Negative input
    variables = {"n": -3}
    interpreter = Cy(variables=variables)
    result = interpreter.run(program)
    assert result == '"-3 is not a positive number"'

    # Test case 3: One input
    variables = {"n": 1}
    interpreter = Cy(variables=variables)
    result = interpreter.run(program)
    assert result == '"Factorial of 1 is 1"'

    # Test case 4: Large number
    variables = {"n": 6}
    interpreter = Cy(variables=variables)
    result = interpreter.run(program)
    assert result == '"Factorial of 6 is 720"'


def test_example_10_feature_integration():
    """Test that Example 10 demonstrates all language features working together.

    Updated: all control flow and syntax uses current conventions.
    """
    variables = {"n": 4}
    interpreter = Cy(variables=variables)

    program = """
x = n
fact = 1

if (x > 0) {
    while (x > 1) {
        fact = fact * x
        x = x - 1
    }
    output = "Factorial of ${n} is ${fact}"
} else {
    output = "${n} is not a positive number"
}
return output
"""

    result = interpreter.run(program)
    assert result == '"Factorial of 4 is 24"'

    # Verify this program exercises all key language features:
    # ✅ Variable assignment: x = n
    # ✅ Mathematics: fact * x, x - 1
    # ✅ Comparison: x > 0, x > 1
    # ✅ Control flow: if/else conditional
    # ✅ Loops: while loop with condition
    # ✅ Variable modification in loops: fact = fact * x
    # ✅ String interpolation: "Factorial of ${n} is ${fact}"
    # ✅ Return statement: return output
