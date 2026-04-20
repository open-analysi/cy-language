"""
Integration tests for indexed access functionality.

These tests cover end-to-end scenarios and real-world usage patterns
discovered during validation.
"""

from cy_language import Cy


class TestToolsWithIndexedAccess:
    """Test indexed access integration with tool calls."""

    def test_tool_arguments_with_indexed_access(self):
        """Test using indexed values as tool arguments."""
        tools = {
            "add": lambda a, b: a + b,
            "multiply": lambda a, b: a * b,
            "concat": lambda *args: "-".join(str(arg) for arg in args),
        }
        interpreter = Cy(tools=tools)

        program = """
        numbers = [10, 20, 30, 40, 50]
        words = ["hello", "world", "test"]

        total = add(numbers[0], numbers[4])
        product = multiply(numbers[1], numbers[2])
        text = concat(words[0], words[1])

        output = "Sum: ${total}, Product: ${product}, Text: ${text}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Sum: 60, Product: 600, Text: hello-world"'

    def test_chained_access_in_tool_calls(self):
        """Test chained indexed access in tool arguments."""
        tools = {
            "format_user": lambda name, age: f"{name} ({age} years old)",
            "calculate": lambda a, b, c: a + b * c,
        }
        interpreter = Cy(tools=tools)

        program = """
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ],
            "numbers": [[1, 2], [3, 4], [5, 6]]
        }

        users = data["users"]
        first_user = users[0]
        user_name = first_user["name"]
        user_age = first_user["age"]
        user_info = format_user(user_name, user_age)

        numbers = data["numbers"]
        first_row = numbers[0]
        second_row = numbers[1]
        third_row = numbers[2]
        calc_result = calculate(first_row[0], second_row[1], third_row[0])

        output = "User: ${user_info}, Calculation: ${calc_result}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"User: Alice (30 years old), Calculation: 21"'  # 1 + 4 * 5


class TestComplexDataStructures:
    """Test indexed access with complex, realistic data structures."""

    def test_employee_management_system(self):
        """Test employee management system pattern from validation."""
        interpreter = Cy()
        program = '''
        company = {
            "departments": {
                "engineering": {
                    "employees": [
                        {"name": "Alice", "skills": ["Python", "React"], "level": "Senior"},
                        {"name": "Bob", "skills": ["Java", "Spring"], "level": "Mid"}
                    ],
                    "budget": 500000
                },
                "marketing": {
                    "employees": [
                        {"name": "Carol", "skills": ["Analytics", "Design"], "level": "Senior"}
                    ],
                    "budget": 200000
                }
            }
        }

        departments = company["departments"]
        engineering = departments["engineering"]
        eng_employees = engineering["employees"]
        eng_lead = eng_employees[0]
        eng_lead_name = eng_lead["name"]
        eng_skills = eng_lead["skills"]
        eng_lead_skill = eng_skills[0]
        eng_budget = engineering["budget"]

        marketing = departments["marketing"]
        marketing_employees = marketing["employees"]
        marketing_lead = marketing_employees[0]
        marketing_employee = marketing_lead["name"]

        output = """
        Engineering Lead: ${eng_lead_name}
        Primary Skill: ${eng_lead_skill}
        Department Budget: ${eng_budget}
        Marketing Team: ${marketing_employee}
        """
        return output
        '''
        result = interpreter.run(program)
        assert "Engineering Lead: Alice" in result
        assert "Primary Skill: Python" in result
        assert "Department Budget: 500000" in result
        assert "Marketing Team: Carol" in result

    def test_api_response_processing(self):
        """Test processing API-like response data."""
        interpreter = Cy()
        program = """
        api_response = {
            "status": "success",
            "data": {
                "users": [
                    {
                        "id": 1,
                        "profile": {
                            "personal": {"name": "Alice", "age": 30},
                            "professional": {"title": "Engineer", "company": "TechCorp"}
                        },
                        "activities": [
                            {"type": "login", "timestamp": "2024-01-01"},
                            {"type": "update", "timestamp": "2024-01-02"}
                        ]
                    }
                ]
            },
            "metadata": {"total": 1, "page": 1}
        }

        data = api_response["data"]
        users = data["users"]
        user = users[0]
        profile = user["profile"]
        personal = profile["personal"]
        professional = profile["professional"]
        name = personal["name"]
        title = professional["title"]
        activities = user["activities"]
        last_activity_obj = activities[1]
        last_activity = last_activity_obj["type"]
        metadata = api_response["metadata"]
        total_users = metadata["total"]

        output = "User: ${name} (${title}), Last Activity: ${last_activity}, Total: ${total_users}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"User: Alice (Engineer), Last Activity: update, Total: 1"'


class TestPerformanceAndScalability:
    """Test indexed access with larger data structures."""

    def test_large_array_access(self):
        """Test indexed access with larger arrays."""
        interpreter = Cy()
        # Create a program with a reasonably large array
        numbers = list(range(100))
        program = f"""
        numbers = {numbers}
        first = numbers[0]
        middle = numbers[50]
        last = numbers[99]
        output = "First: ${{first}}, Middle: ${{middle}}, Last: ${{last}}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First: 0, Middle: 50, Last: 99"'

    def test_deeply_nested_structure(self):
        """Test deeply nested structure access."""
        interpreter = Cy()
        program = """
        nested = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "data": ["deep", "value", "here"]
                            }
                        }
                    }
                }
            }
        }

        deep_value = nested["level1"]["level2"]["level3"]["level4"]["level5"]["data"][1]
        output = "Deep value: ${deep_value}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Deep value: value"'


class TestRealWorldExampleValidation:
    """Test the exact patterns from our validation examples."""

    def test_example_real_world_pattern(self):
        """Test the pattern from example_real_world.cy."""
        interpreter = Cy()
        program = '''
        users = [
            {"name": "Alice Johnson", "dept": "Engineering", "projects": ["API", "Database"], "salary": 95000},
            {"name": "Bob Smith", "dept": "Marketing", "projects": ["Campaign", "Analytics"], "salary": 72000},
            {"name": "Carol Davis", "dept": "Engineering", "projects": ["Frontend", "Mobile"], "salary": 88000}
        ]

        engineering_team = [
            {"name": "Alice Johnson", "projects": ["API", "Database"], "salary": 95000},
            {"name": "Carol Davis", "projects": ["Frontend", "Mobile"], "salary": 88000}
        ]

        top_engineer = engineering_team[0]
        top_eng_name = top_engineer["name"]
        top_eng_salary = top_engineer["salary"]
        top_eng_projects = top_engineer["projects"]
        top_project = top_eng_projects[0]

        second_engineer = engineering_team[1]
        second_eng_name = second_engineer["name"]

        latest_hire_user = users[2]
        latest_hire_name = latest_hire_user["name"]

        output = """
        Top Engineer: ${top_eng_name}
        Primary Project: ${top_project}
        Salary: ${top_eng_salary}
        Team Projects: ${top_eng_projects|csv}
        Latest Hire: ${latest_hire_name}
        Focus: Both ${top_eng_name} and ${second_eng_name}
        """
        return output
        '''
        result = interpreter.run(program)

        assert "Top Engineer: Alice Johnson" in result
        assert "Primary Project: API" in result
        assert "Salary: 95000" in result
        assert "Team Projects: API,Database" in result
        assert "Latest Hire: Carol Davis" in result
        assert "Focus: Both Alice Johnson and Carol Davis" in result

    def test_validation_array_indexing_functionality(self):
        """Test the exact pattern from validation_tests.py."""
        tools = {"add": lambda a, b: a + b, "multiply": lambda a, b: a * b}
        interpreter = Cy(tools=tools)

        program = '''
        numbers = [10, 20, 30, 40, 50]
        data = {"users": ["Alice", "Bob", "Carol"], "scores": [95, 87, 92]}

        first_number = numbers[0]
        last_number = numbers[4]
        sum_result = add(first_number, last_number)

        first_user = data["users"][0]
        user_score = data["scores"][0]

        output = """
        Array Indexing Examples:
        - First number: ${first_number}
        - Last number: ${last_number}
        - Sum of first and last: ${sum_result}
        - Top user: ${first_user} (score: ${user_score})
        """
        return output
        '''
        result = interpreter.run(program)

        assert "First number: 10" in result
        assert "Last number: 50" in result
        assert "Sum of first and last: 60" in result
        assert "Top user: Alice" in result
        assert "score: 95" in result

    def test_validation_nested_indexing(self):
        """Test the nested indexing pattern from validation."""
        interpreter = Cy()
        program = """
        matrix = [["a", "b"], ["c", "d"], ["e", "f"]]
        nested_data = {"level1": {"level2": {"items": [1, 2, 3, 4]}}}

        element = matrix[1][0]
        deep_value = nested_data["level1"]["level2"]["items"][2]

        output = "Matrix element [1][0]: ${element}, Deep nested value: ${deep_value}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Matrix element [1][0]: c, Deep nested value: 3"'


class TestErrorHandlingIntegration:
    """Test error handling in integration scenarios."""

    def test_oob_propagation_in_tools(self):
        """Test that list OOB returns null and propagates through tool calls."""
        tools = {"process": lambda x: f"processed: {x}"}
        interpreter = Cy(tools=tools)

        program = """
        data = ["a", "b", "c"]
        result = process(data[10])  # Out of bounds → null
        output = "Result: ${result}"
        return output
        """
        result = interpreter.run(program)
        assert "processed: None" in result

    def test_partial_success_with_valid_and_oob_access(self):
        """Test program with both valid and OOB indexed access."""
        interpreter = Cy()

        # This should work for valid access
        program_valid = """
        data = {"items": [1, 2, 3]}
        valid = data["items"][0]
        output = "Valid: ${valid}"
        return output
        """
        result = interpreter.run(program_valid)
        assert result == '"Valid: 1"'

        # OOB returns null (consistent with dict missing key)
        program_oob = """
        data = {"items": [1, 2, 3]}
        invalid = data["items"][10]
        output = "Invalid: ${invalid}"
        return output
        """
        result = interpreter.run(program_oob)
        assert result == '"Invalid: null"'
