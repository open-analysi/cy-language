"""Tests for Python-like syntax changes."""

import json

import pytest

from cy_language import Cy
from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.parser import Parser


class TestPythonCommentSyntax:
    """Test Python-style # comments."""

    def test_hash_comment_basic(self):
        """Test that basic # comments work."""
        program = """
# This is a comment
x = 5
output = "Value: ${x}"
return output
"""
        interpreter = Cy()
        result = interpreter.run(program)
        assert result == '"Value: 5"'

    def test_no_pragma_needed(self):
        """Test that programs work without version pragma."""
        program = """
name = "Alice"
output = "Hello, ${name}"
return output
"""
        interpreter = Cy()
        result = interpreter.run(program)
        assert result == '"Hello, Alice"'

    def test_double_slash_in_string(self):
        """Test that // inside strings remains unchanged."""
        program = """
url = "http://example.com"
path = "//network/share"
output = "URL: ${url}, Path: ${path}"
return output
"""
        interpreter = Cy()
        result = interpreter.run(program)
        assert result == '"URL: http://example.com, Path: //network/share"'


class TestCommentsInComplexStructures:
    """Test comments in multiline structures."""

    def test_comment_in_multiline_string(self):
        """Test comments within and around multiline strings."""
        program = '''
text = """Line 1
# This should NOT be a comment
Line 3"""  # But this should be a comment
output = text
return output
'''
        interpreter = Cy()
        result = interpreter.run(program)
        decoded = json.loads(result)
        expected = """Line 1
# This should NOT be a comment
Line 3"""
        assert decoded == expected

    def test_comment_in_multiline_list(self):
        """Test comments within multiline list definitions."""
        program = """
items = [
    "item1",  # comment about item1
    "item2",  # comment about item2
    "item3"   # comment about item3
]  # end of list
output = "Items: ${items}"
return output
"""
        interpreter = Cy()
        result = interpreter.run(program)
        # Should create list without being affected by comments
        assert "item1" in result
        assert "item2" in result
        assert "item3" in result

    def test_comment_in_multiline_dict(self):
        """Test comments within multiline dictionary definitions."""
        program = """
config = {
    "host": "localhost",  # development server
    "port": 8080,         # default port
    "debug": True         # enable debug mode
}  # configuration complete
output = "Host: ${config.host}, Port: ${config.port}"
return output
"""
        interpreter = Cy()
        result = interpreter.run(program)
        assert result == '"Host: localhost, Port: 8080"'

    def test_comment_in_multiline_function_call(self):
        """Test comments within multiline function calls."""

        # Define a test function
        def test_func(data, threshold=0.5, mode="strict"):
            return f"Processed with threshold={threshold}, mode={mode}"

        program = """
input_data = "test"
result = test_func(
    data=input_data,      # raw data
    threshold=0.5,         # confidence threshold
    mode="strict"          # processing mode
)  # returns processed results
output = result
return output
"""
        interpreter = Cy(tools={"test_func": test_func})
        result = interpreter.run(program)
        assert result == '"Processed with threshold=0.5, mode=strict"'


class TestGrammarChanges:
    """Test grammar-level changes."""

    def test_comment_syntax_change(self):
        """Test that # is recognized as comment in grammar."""
        parser = Parser()
        # This should parse without errors
        program = """
# Comment line
x = 1
"""
        ast = parser.parse_only(program)
        assert ast is not None


class TestUpdateExistingBehavior:
    """Test that existing comment syntax no longer works as comments."""

    def test_double_slash_not_comment(self):
        """Test that // is no longer treated as a comment."""
        program = """
// This should not be a comment anymore
x = 5
output = "Value: ${x}"
return output
"""
        interpreter = Cy()
        # This should fail because // is not valid syntax anymore
        with pytest.raises((CySyntaxError, Exception)):
            interpreter.run(program)
