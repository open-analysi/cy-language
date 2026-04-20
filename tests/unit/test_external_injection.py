"""Tests for external tools and variables injection in the Cy language."""

from cy_language import Cy


def test_external_variables_injection():
    """Test injecting external variables into the Cy program."""
    # Create variables to inject
    variables = {
        "user_name": "Alice",
        "admin_role": "yes",  # Using string instead of boolean
        "scores": [95, 87, 92],
        "user_data": {"id": 12345, "email": "alice@example.com"},
    }

    # Create the interpreter with external variables
    interpreter = Cy(variables=variables)

    program = """
    output = "User: ${user_name}\\nAdmin: ${admin_role}\\nScores: ${scores}\\nEmail: ${user_data.email}\\nID: ${user_data.id}"
    return output
    """

    result = interpreter.run(program)
    assert "User: Alice" in result
    assert "Admin: yes" in result
    assert "Scores: " in result
    assert "- 95" in result
    assert "- 87" in result
    assert "- 92" in result
    assert "Email: alice@example.com" in result
    assert "ID: 12345" in result


def test_external_tools_injection():
    """Test providing external tools to the Cy interpreter."""

    # Define some mock tools
    def add(a, b):
        return a + b

    def multiply(a, b):
        return a * b

    def greeting(name):
        return f"Hello, {name}!"

    def format_list(items):
        return ", ".join([str(item) for item in items])

    # Create tools dictionary
    tools = {
        "add": add,
        "multiply": multiply,
        "greeting": greeting,
        "format_list": format_list,
    }

    # Create the interpreter with tools
    interpreter = Cy(tools=tools)

    program = """
    num1 = 5
    num2 = 7
    total = add(num1, num2)
    product = multiply(num1, num2)
    message = greeting("Alice")
    numbers = [1, 2, 3, 4, 5]
    formatted = format_list(numbers)
    
    output = "Sum: ${total}\\nProduct: ${product}\\nMessage: ${message}\\nFormatted List: ${formatted}"
    return output
    """

    result = interpreter.run(program)
    assert "Sum: 12" in result
    assert "Product: 35" in result
    assert "Message: Hello, Alice!" in result
    assert "Formatted List: 1, 2, 3, 4, 5" in result


def test_external_variables_with_complex_structures():
    """Test injecting complex nested structures as external variables."""
    # Create complex nested variables
    variables = {
        "company": {
            "name": "Acme Inc.",
            "departments": [
                {
                    "name": "Engineering",
                    "employees": [
                        {"name": "Alice", "role": "Developer"},
                        {"name": "Bob", "role": "QA"},
                    ],
                },
                {
                    "name": "Marketing",
                    "employees": [
                        {"name": "Charlie", "role": "Manager"},
                        {"name": "Dana", "role": "Specialist"},
                    ],
                },
            ],
        }
    }

    # Create the interpreter with complex variables
    interpreter = Cy(variables=variables)

    # Extract nested elements first, then access their properties
    program = """
    dept1 = company["departments"][0]
    dept2 = company["departments"][1]
    emp1_1 = dept1["employees"][0]
    emp1_2 = dept1["employees"][1]
    emp2_1 = dept2["employees"][0]
    emp2_2 = dept2["employees"][1]

    output = "Company: ${company.name}\\n\\nDepartments:\\n- ${dept1.name}\\n  * ${emp1_1.name}: ${emp1_1.role}\\n  * ${emp1_2.name}: ${emp1_2.role}\\n\\n- ${dept2.name}\\n  * ${emp2_1.name}: ${emp2_1.role}\\n  * ${emp2_2.name}: ${emp2_2.role}"
    return output
    """

    result = interpreter.run(program)
    assert "Company: Acme Inc." in result
    assert "Departments:" in result
    assert "- Engineering" in result
    assert "* Alice: Developer" in result
    assert "* Bob: QA" in result
    assert "- Marketing" in result
    assert "* Charlie: Manager" in result
    assert "* Dana: Specialist" in result


def test_combination_tools_and_vars():
    """Test using both external tools and variables together."""

    # Define some tools
    def calculate_total(items):
        return sum(items)

    def format_user(user_data):
        return f"{user_data['name']} ({user_data['email']})"

    # Create tools dictionary
    tools = {"calculate_total": calculate_total, "format_user": format_user}

    # Create variables to inject
    variables = {
        "user": {"name": "Alice Smith", "email": "alice@example.com"},
        "prices": [10.99, 24.50, 5.75],
    }

    # Create the interpreter with both tools and variables
    interpreter = Cy(tools=tools, variables=variables)

    program = """
    total = calculate_total(prices)
    user_display = format_user(user)
    
    output = "User: ${user_display}\\nItems: ${prices}\\nTotal: ${total}"
    return output
    """

    result = interpreter.run(program)
    assert "User: Alice Smith (alice@example.com)" in result
    assert "Items: " in result
    assert "- 10.99" in result
    assert "- 24.5" in result
    assert "- 5.75" in result
    assert "Total: 41.24" in result
