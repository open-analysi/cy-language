"""
Test triple-quoted string interpolation with double quotes.
"""

import pytest

from cy_language import Cy


class TestTripleQuoteInterpolation:
    """Test triple-quoted string interpolation behavior."""

    def test_triple_quote_with_double_quotes_should_work(self):
        """Test that triple quotes support double quotes in interpolation."""
        interpreter = Cy()
        program = '''
        data = {"name": "Alice", "age": 30}
        output = """
        User: ${data["name"]}
        Age: ${data["age"]}
        """
        return output
        '''
        result = interpreter.run(program)
        # Should work and contain the interpolated values
        assert "Alice" in result
        assert "30" in result

    def test_triple_quote_with_nested_access(self):
        """Test triple quotes with complex nested access."""
        interpreter = Cy()
        program = '''
        users = [{"profile": {"name": "Alice"}}, {"profile": {"name": "Bob"}}]
        output = """
        First user: ${users[0]["profile"]["name"]}
        Second user: ${users[1]["profile"]["name"]}
        """
        return output
        '''
        result = interpreter.run(program)
        assert "Alice" in result
        assert "Bob" in result

    def test_regular_double_quotes_should_still_fail(self):
        """Test that regular double quotes still fail (expected behavior)."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        output = "Name: ${data["name"]}"
        return output
        """
        # This should still fail with syntax error
        with pytest.raises(Exception):
            interpreter.run(program)

    def test_single_quotes_still_work_in_regular_strings(self):
        """Test that single quotes still work in regular strings."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        output = "Name: ${data['name']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice"'

    def test_triple_quote_mixed_quotes(self):
        """Test triple quotes with mixed quote types."""
        interpreter = Cy()
        program = '''
        data = {"name": "Alice", "scores": [85, 90]}
        output = """
        Name: ${data["name"]} (using double quotes)
        First score: ${data['scores'][0]} (using single quotes)
        """
        return output
        '''
        result = interpreter.run(program)
        assert "Alice" in result
        assert "85" in result
