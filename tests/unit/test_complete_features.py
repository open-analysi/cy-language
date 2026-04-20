"""Integration tests for the complete feature set of the Cy language."""

from cy_language import Cy


# Re-enabled: Testing if improvements fixed the interpolation issues
def test_complete_program():
    """Test a complete program using all major features."""
    # Define tools
    tools = {
        "add": lambda a, b: a + b,
        "get_user": lambda name: {
            "name": name,
            "age": 30 if name == "Alice" else 25,
            "hobbies": ["reading", "coding"]
            if name == "Alice"
            else ["gaming", "music"],
            "scores": [85, 92, 78] if name == "Alice" else [75, 88, 95],
            "contact": {
                "email": f"{name.lower()}@example.com",
                "phone": "123-456-7890",
            },
        },
    }

    # Create interpreter with markdown mode and custom item tag
    interpreter = Cy(tools=tools, interpolation_mode="markdown", item_tag="element")

    # Complex program using all major features
    program = """    # User data processing example

    # Get user data using tool
    user = get_user("Alice")

    # Calculate average score
    score1 = user.scores[0]  # This won't work yet - we would need list indexing
    total = add(user.scores[0], add(user.scores[1], user.scores[2]))
    count = 3
    average = total  # Simplified without division

    # Create a report object
    report = {
        "user_name": user.name,
        "user_email": user.contact.email,
        "average_score": average,
        "status": "active",
        "notes": ["Good performance", "Regular attendance"],
        "details": {
            "joined": "2023-01-15",
            "level": "Advanced"
        }
    }

    # Generate final report with different formatting options
    output = \"\"\"# User Report

## Basic Information
Name: ${user.name}
Email: ${user.contact.email}
Status: ${report.status}

## Performance
Average Score: ${report.average_score}
Notes:
${report.notes}

## Hobbies (CSV Format)
${user.hobbies|csv}

## Raw Data (XML Format)
<user_data>
${user|xml}
</user_data>
\"\"\"
    return output
    """

    result = interpreter.run(program)

    # Check all sections are present
    assert "# User Report" in result
    assert "## Basic Information" in result
    assert "Name: Alice" in result
    assert "Email: alice@example.com" in result
    assert "Status: active" in result

    assert "## Performance" in result
    assert "Average Score:" in result
    assert "Notes:" in result
    assert "- Good performance" in result
    assert "- Regular attendance" in result

    assert "## Hobbies (CSV Format)" in result
    assert "reading,coding" in result.replace(" ", "")

    assert "## Raw Data (XML Format)" in result
    assert "<user_data>" in result
    assert "<name>Alice</name>" in result.replace(" ", "")
    assert "<age>30</age>" in result.replace(" ", "")
    assert "<hobbies>" in result
    assert "<element>reading</element>" in result.replace(" ", "")
    assert "<element>coding</element>" in result.replace(" ", "")
    assert "</hobbies>" in result
    assert "<scores>" in result
    assert "<element>85</element>" in result.replace(" ", "")
    assert "<element>92</element>" in result.replace(" ", "")
    assert "<element>78</element>" in result.replace(" ", "")
    assert "</scores>" in result
    assert "<contact>" in result
    assert "<email>alice@example.com</email>" in result.replace(" ", "")
    assert "<phone>123-456-7890</phone>" in result.replace(" ", "")
    assert "</contact>" in result
    assert "</user_data>" in result


def test_example_program_from_design_doc_3():
    """Test example program 3 (Struct access) from the language design doc."""
    interpreter = Cy()

    program = """
    user = { "id": 7, "name": "Bob" }
    output = "User #${user.id}: ${user.name}"
    return output
    """

    result = interpreter.run(program)
    assert result == '"User #7: Bob"'


def test_example_program_from_design_doc_4():
    """Test example program 4 (Tool call with positional args) from the language design doc."""
    tools = {"add": lambda a, b: a + b}
    interpreter = Cy(tools=tools)

    program = """
    total = add(3, 4)
    output = "3 + 4 = ${total}"
    return output
    """

    result = interpreter.run(program)
    assert result == '"3 + 4 = 7"'


def test_example_program_from_design_doc_6():
    """Test example program 6 (Multiline string with interpolation) from the language design doc."""
    interpreter = Cy()

    # Using escaped newlines instead of triple quotes for now
    program = """
    name = "Eve"
    output = "Hello ${name},\\n\\nThis is a multiline string."
    return output
    """

    result = interpreter.run(program)
    assert "Hello Eve," in result
    assert "This is a multiline string." in result


def test_example_program_from_design_doc_7():
    """Test example program 7 (XML printer hint) from the language design doc."""
    interpreter = Cy(interpolation_mode="markdown")

    program = """
    items = ["a", "b"]
    output = "<items>${items|xml}</items>"
    return output
    """

    result = interpreter.run(program)
    assert "<items>" in result
    assert "<item>a</item>" in result.replace(" ", "")
    assert "<item>b</item>" in result.replace(" ", "")
    assert "</items>" in result


# Re-enabled: Testing if CSV formatting now works
def test_example_program_from_design_doc_8():
    """Test example program 8 (List of structs with CSV override) from the language design doc."""
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
    assert "Raw table (CSV):" in result
    assert "id,name,score" in result.replace(" ", "")
    assert "1,alice,92" in result.replace(" ", "")
    assert "2,bob,87" in result.replace(" ", "")
