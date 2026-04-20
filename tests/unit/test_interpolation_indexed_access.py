"""
Tests for indexed access specifically in string interpolation.

These tests cover the critical issue discovered during validation where
${arr[0]} syntax wasn't working in string interpolation.
"""

from cy_language import Cy


class TestBasicInterpolationIndexedAccess:
    """Test basic indexed access in string interpolation."""

    def test_simple_list_interpolation(self):
        """Test basic list indexing in interpolation: ${arr[0]}."""
        interpreter = Cy()
        program = """
        arr = ["apple", "banana", "cherry"]
        output = "First fruit: ${arr[0]}, Last fruit: ${arr[2]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First fruit: apple, Last fruit: cherry"'

    def test_simple_dict_interpolation(self):
        """Test basic dictionary indexing in interpolation: ${obj["key"]}."""
        interpreter = Cy()
        program = """
        user = {"name": "Alice", "age": 30, "role": "Engineer"}
        name = user["name"]
        age = user["age"]
        role = user["role"]
        output = "User ${name} is ${age} years old and works as ${role}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"User Alice is 30 years old and works as Engineer"'

    def test_string_char_interpolation(self):
        """Test string character indexing in interpolation."""
        interpreter = Cy()
        program = """
        word = "Hello"
        output = "First letter: ${word[0]}, Last letter: ${word[4]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First letter: H, Last letter: o"'


class TestChainedInterpolationAccess:
    """Test chained indexed access in interpolation - the critical validation issue."""

    def test_dict_to_list_interpolation(self):
        """Test chained dictionary to list access in interpolation."""
        interpreter = Cy()
        program = """
        data = {"users": ["Alice", "Bob", "Carol"], "scores": [95, 87, 92]}
        top_user = data["users"][0]
        top_score = data["scores"][0]
        output = "Top user: ${top_user} with score ${top_score}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Top user: Alice with score 95"'

    def test_multidimensional_interpolation(self):
        """Test multi-dimensional array access in interpolation."""
        interpreter = Cy()
        program = """
        matrix = [["a", "b"], ["c", "d"], ["e", "f"]]
        output = "Matrix elements: ${matrix[0][0]}, ${matrix[1][0]}, ${matrix[2][1]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Matrix elements: a, c, f"'

    def test_deep_nested_interpolation(self):
        """Test deep nested access in interpolation."""
        interpreter = Cy()
        program = """
        config = {"db": {"settings": {"hosts": ["primary", "backup"]}}}
        primary_host = config["db"]["settings"]["hosts"][0]
        output = "Primary host: ${primary_host}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Primary host: primary"'

    def test_real_world_employee_interpolation(self):
        """Test the employee data pattern from validation in interpolation."""
        interpreter = Cy()
        program = """
        employees = [
            {"name": "Alice", "projects": ["API", "Database"]},
            {"name": "Bob", "projects": ["UI", "Testing"]}
        ]
        emp_name = employees[0]["name"]
        project1 = employees[0]["projects"][0]
        project2 = employees[0]["projects"][1]
        output = "Employee ${emp_name} works on ${project1} and ${project2}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Employee Alice works on API and Database"'


class TestMixedAccessInterpolation:
    """Test complex access patterns using separate operations for interpolation."""

    def test_field_then_index_interpolation(self):
        """Test field access then indexing in separate steps for interpolation."""
        interpreter = Cy()
        program = """
        data = {"items": ["x", "y", "z"], "metadata": {"count": 3}}
        items = data["items"]
        first_item = items[0]
        metadata = data["metadata"]
        count = metadata["count"]
        output = "First item: ${first_item}, Count: ${count}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First item: x, Count: 3"'

    def test_index_then_field_interpolation(self):
        """Test indexing then field access in separate steps for interpolation."""
        interpreter = Cy()
        program = """
        users = [{"name": "Alice", "status": "active"}, {"name": "Bob", "status": "inactive"}]
        user1 = users[0]
        user2 = users[1]
        name1 = user1["name"]
        status1 = user1["status"]
        name2 = user2["name"]
        status2 = user2["status"]
        output = "User: ${name1} (${status1}), User: ${name2} (${status2})"
        return output
        """
        result = interpreter.run(program)
        assert result == '"User: Alice (active), User: Bob (inactive)"'

    def test_complex_nested_interpolation(self):
        """Test complex nested patterns using step-by-step access."""
        interpreter = Cy()
        program = """
        app = {
            "users": [
                {"profile": {"settings": {"theme": "dark"}}},
                {"profile": {"settings": {"theme": "light"}}}
            ]
        }
        users = app["users"]
        user1 = users[0]
        user2 = users[1]
        profile1 = user1["profile"]
        profile2 = user2["profile"]
        settings1 = profile1["settings"]
        settings2 = profile2["settings"]
        theme1 = settings1["theme"]
        theme2 = settings2["theme"]
        output = "Themes: ${theme1} and ${theme2}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Themes: dark and light"'


class TestInterpolationWithFormatHints:
    """Test indexed access combined with format hints."""

    def test_indexed_list_with_csv_format(self):
        """Test ${arr[0]|csv} - indexed access with format hint."""
        interpreter = Cy()
        program = """
        data = [["a", "b", "c"], ["x", "y", "z"]]
        output = "First row: ${data[0]|csv}, Second row: ${data[1]|csv}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"First row: a,b,c, Second row: x,y,z"'

    def test_indexed_dict_with_xml_format(self):
        """Test indexed dict access with format hint."""
        interpreter = Cy()
        program = """
        data = {"items": ["apple", "banana"], "numbers": [1, 2, 3]}
        items = data["items"]
        output = "Items: ${items|xml}"
        return output
        """
        result = interpreter.run(program)
        expected = '"Items:   <item>apple</item>\\n  <item>banana</item>"'
        assert result == expected

    def test_chained_access_with_format_hint(self):
        """Test complex chained access with format hint."""
        interpreter = Cy()
        program = """
        teams = {
            "engineering": [
                {"members": ["Alice", "Bob"], "projects": ["API", "DB"]},
                {"members": ["Carol"], "projects": ["UI"]}
            ]
        }
        eng_teams = teams["engineering"]
        first_team = eng_teams[0]
        projects = first_team["projects"]
        output = "Team 1 projects: ${projects|csv}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Team 1 projects: API,DB"'


class TestRealWorldInterpolationPatterns:
    """Test real-world patterns from validation examples."""

    def test_company_report_pattern(self):
        """Test the company report pattern from example_real_world.cy."""
        interpreter = Cy()
        program = """
        engineering_team = [
            {"name": "Alice", "projects": ["API", "Database"]},
            {"name": "Carol", "projects": ["Frontend", "Mobile"]}
        ]
        users = [{"name": "Alice"}, {"name": "Bob"}, {"name": "Carol"}]
        
        top_eng = engineering_team[0]
        top_eng_name = top_eng["name"]
        latest_hire = users[2]
        latest_name = latest_hire["name"]
        top_projects = top_eng["projects"]
        second_eng = engineering_team[1]
        second_name = second_eng["name"]

        output = \"\"\"
        Top Engineer: ${top_eng_name}
        Latest Hire: ${latest_name}
        Team Projects: ${top_projects|xml}
        Focus: ${top_eng_name} and ${second_name}
        \"\"\"
        return output
        """
        result = interpreter.run(program)
        assert "Top Engineer: Alice" in result
        assert "Latest Hire: Carol" in result
        assert "<item>API</item>" in result
        assert "<item>Database</item>" in result
        assert "Focus: Alice and Carol" in result

    def test_data_analysis_pattern(self):
        """Test data analysis pattern with nested structures."""
        interpreter = Cy()
        program = """
        sales_data = {
            "Q1": {"months": [{"sales": 1000}, {"sales": 1200}, {"sales": 1100}]},
            "Q2": {"months": [{"sales": 1300}, {"sales": 1400}, {"sales": 1250}]}
        }
        q1_data = sales_data["Q1"]
        q1_months = q1_data["months"]
        q1_peak_month = q1_months[1]
        q1_peak = q1_peak_month["sales"]
        
        q2_data = sales_data["Q2"]
        q2_months = q2_data["months"]
        q2_peak_month = q2_months[1]
        q2_peak = q2_peak_month["sales"]

        output = "Q1 Peak: ${q1_peak}, Q2 Peak: ${q2_peak}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Q1 Peak: 1200, Q2 Peak: 1400"'


class TestDesignDecisionValidation:
    """Test that design decisions about $var vs ${...} are correctly implemented."""

    def test_simple_variable_no_indexing(self):
        """Test that ${arr}[0] is treated as ${arr} + literal [0] (by design)."""
        interpreter = Cy()
        program = """
        arr = ["a", "b", "c"]
        output = "Result: ${arr}[0]"
        return output
        """
        result = interpreter.run(program)
        # Should be markdown-formatted array + literal [0]
        expected = '"Result: - a\\n- b\\n- c[0]"'
        assert result == expected

    def test_braced_syntax_required_for_indexing(self):
        """Test that ${arr[0]} syntax is required for actual indexing."""
        interpreter = Cy()
        program = """
        arr = ["a", "b", "c"]
        simple = "${arr}[0]"
        correct = "${arr[0]}"
        output = "Simple: ${simple}, Correct: ${correct}"
        return output
        """
        result = interpreter.run(program)
        # Simple should show markdown-formatted array + literal [0], correct should show indexed value
        assert "Simple: - a\\n- b\\n- c[0]" in result
        assert "Correct: a" in result

    def test_consistency_with_field_access_design(self):
        """Test that indexed access follows same design as field access."""
        interpreter = Cy()
        program = """
        obj = {"field": ["value1", "value2"]}

        obj_field = obj["field"]
        first_value = obj_field[0]

        simple_field = "${obj_field}"
        correct_index = "${first_value}"

        output = "Field: ${simple_field}, Index: ${correct_index}"
        return output
        """
        result = interpreter.run(program)
        assert "Field: - value1\\n- value2" in result
        assert "Index: value1" in result
