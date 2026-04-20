"""
Fast unit tests for quote variation handling in interpolation.
"""

from cy_language import Cy


class TestQuoteVariationsInterpolation:
    """Test that interpolation works with both single and double quote variations."""

    def test_single_quotes_in_double_quote_string(self):
        """Test single quotes inside double-quoted string."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        output = "User: ${data['name']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"User: Alice"'

    def test_double_quotes_in_triple_quote_string(self):
        """Test double quotes inside triple-quoted string."""
        interpreter = Cy()
        program = '''
        data = {"name": "Alice"}
        output = """User: ${data["name"]}"""
        return output
        '''
        result = interpreter.run(program)
        assert result == '"User: Alice"'

    def test_mixed_quotes_in_triple_quote_string(self):
        """Test mixed quote types in same triple-quoted string."""
        interpreter = Cy()
        program = '''
        data = {"name": "Alice", "scores": [85, 90]}
        output = """Name: ${data["name"]}, Score: ${data['scores'][0]}"""
        return output
        '''
        result = interpreter.run(program)
        assert "Alice" in result
        assert "85" in result

    def test_nested_bracket_access_with_double_quotes(self):
        """Test nested bracket access with double quotes."""
        interpreter = Cy()
        program = '''
        users = [{"profile": {"name": "Bob"}}]
        output = """User: ${users[0]["profile"]["name"]}"""
        return output
        '''
        result = interpreter.run(program)
        assert result == '"User: Bob"'

    def test_chained_access_mixed_quotes(self):
        """Test chained access with mixed quote types."""
        interpreter = Cy()
        program = '''
        data = {"users": [{"name": "Charlie"}]}
        output = """Name: ${data["users"][0]["name"]}"""
        return output
        '''
        result = interpreter.run(program)
        assert result == '"Name: Charlie"'

    def test_both_quote_styles_same_template(self):
        """Test both quote styles referencing same data in one template."""
        interpreter = Cy()
        program = '''
        person = {"first": "John", "last": "Doe"}
        output = """${person["first"]} ${person['last']}"""
        return output
        '''
        result = interpreter.run(program)
        assert result == '"John Doe"'

    def test_quote_style_equivalence(self):
        """Test that both quote styles produce identical results."""
        interpreter = Cy()

        # Single quote version
        program1 = """
        data = {"key": "value1"}
        output = "${data['key']}"
        return output
        """
        result1 = interpreter.run(program1)

        # Double quote version in triple quotes
        program2 = '''
        data = {"key": "value1"}
        output = """${data["key"]}"""
        return output
        '''
        result2 = interpreter.run(program2)

        assert result1 == result2 == '"value1"'

    def test_numeric_index_quote_independence(self):
        """Test that numeric indices work regardless of surrounding quotes."""
        interpreter = Cy()
        program = '''
        items = ["first", "second"]
        output = """Item: ${items[0]}"""
        return output
        '''
        result = interpreter.run(program)
        assert result == '"Item: first"'
