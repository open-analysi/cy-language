"""
Test suite for InterpolationExpressionParser functionality.
"""

from src.cy_language.compiler import InterpolationExpressionParser
from src.cy_language.execution_plan import VariableNode


class TestInterpolationExpressionParser:
    """Test the InterpolationExpressionParser class."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = InterpolationExpressionParser()

    def test_parse_simple_variable_interpolation(self):
        """Test parsing of simple $var patterns."""
        template = "Hello $name!"
        variables, hints = self.parser.parse_interpolation_expression(template)

        assert len(variables) == 1
        assert isinstance(variables[0], VariableNode)
        assert variables[0].variable_name == "name"
        assert len(hints) == 0

    def test_parse_braced_variable_interpolation(self):
        """Test parsing of ${var} patterns."""
        template = "Hello ${user_name}!"
        variables, hints = self.parser.parse_interpolation_expression(template)

        assert len(variables) == 1
        assert isinstance(variables[0], VariableNode)
        assert variables[0].variable_name == "user_name"
