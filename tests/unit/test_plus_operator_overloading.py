"""
Unit tests for Universal `+` Operator Overloading.

Tests the overloaded `+` operator that handles:
- Numeric addition (int + int, float + float, int + float)
- String concatenation (str + str)
- List concatenation (list + list)
- Type validation errors for mixed types
"""

import pytest

from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.interpreter import Cy


class TestNumericAddition:
    """Test + operator for numeric addition."""

    def test_add_positive_integers(self):
        """Test basic integer addition: 1 + 2 returns 3"""
        program = """
        result = 1 + 2
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 3"'

    def test_add_negative_integers(self):
        """Test negative integer addition: (-5) + (-3) returns -8"""
        program = """
        a = -5
        b = -3
        result = a + b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: -8"'

    def test_add_mixed_sign_integers(self):
        """Test mixed sign addition: 10 + (-5) returns 5"""
        program = """
        a = 10
        b = -5
        result = a + b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 5"'

    def test_add_zero(self):
        """Test addition with zero: 0 + 5 and 5 + 0"""
        program = """
        result1 = 0 + 5
        result2 = 5 + 0
        output = "${result1},${result2}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"5,5"'

    def test_add_floats(self):
        """Test float addition: 1.5 + 2.5 returns 4.0"""
        program = """
        result = 1.5 + 2.5
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 4.0"'

    def test_add_negative_floats(self):
        """Test negative float addition: (-1.5) + (-2.5) returns -4.0"""
        program = """
        a = -1.5
        b = -2.5
        result = a + b
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: -4.0"'

    def test_add_float_precision(self):
        """Test float precision: 0.1 + 0.2 returns 0.30000000000000004"""
        program = """
        result = 0.1 + 0.2
        output = "${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # Python float precision issue
        assert "0.3" in result

    def test_add_int_and_float(self):
        """Test mixed numeric types: 1 + 2.5 returns 3.5"""
        program = """
        result = 1 + 2.5
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 3.5"'

    def test_add_float_and_int(self):
        """Test mixed numeric types: 2.5 + 1 returns 3.5"""
        program = """
        result = 2.5 + 1
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 3.5"'

    def test_chain_numeric_addition(self):
        """Test chaining numeric addition: 1 + 2 + 3 + 4 returns 10"""
        program = """
        result = 1 + 2 + 3 + 4
        output = "Result: ${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"Result: 10"'

    def test_chain_float_addition(self):
        """Test chaining float addition: 1.1 + 2.2 + 3.3 returns 6.6"""
        program = """
        result = 1.1 + 2.2 + 3.3
        output = "${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "6.6" in result


class TestStringConcatenation:
    """Test + operator for string concatenation."""

    def test_concat_simple_strings(self):
        """Test basic string concatenation: 'a' + 'b' returns 'ab'"""
        program = """
        result = "a" + "b"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"ab"'

    def test_concat_with_spaces(self):
        """Test string concatenation with spaces: 'hello' + ' ' + 'world'"""
        program = """
        result = "hello" + " " + "world"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"hello world"'

    def test_concat_empty_string_left(self):
        """Test concatenation with empty string on left: '' + 'test'"""
        program = """
        result = "" + "test"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"test"'

    def test_concat_empty_string_right(self):
        """Test concatenation with empty string on right: 'test' + ''"""
        program = """
        result = "test" + ""
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"test"'

    def test_concat_both_empty(self):
        """Test concatenation of two empty strings: '' + ''"""
        program = """
        result = "" + ""
        output = "${result}MARKER"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"MARKER"'

    def test_concat_numeric_strings(self):
        """Test numeric string concatenation: '123' + '456' returns '123456' (NOT 579!)"""
        program = """
        result = "123" + "456"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"123456"'

    def test_concat_string_zero(self):
        """Test string zero concatenation: '0' + '0' returns '00'"""
        program = """
        result = "0" + "0"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"00"'

    def test_concat_with_newlines(self):
        """Test concatenation with newline characters"""
        program = """
        result = "line1\\n" + "line2"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"line1\\nline2"'

    def test_concat_with_quotes(self):
        """Test concatenation with escaped quotes"""
        program = """
        result = "He said \\"hi\\"" + " to me"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"He said \\"hi\\" to me"'

    def test_chain_string_concat(self):
        """Test chaining string concatenation: 'a' + 'b' + 'c' + 'd'"""
        program = """
        result = "a" + "b" + "c" + "d"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"abcd"'

    def test_chain_words(self):
        """Test chaining word concatenation with spaces"""
        program = """
        result = "one" + " " + "two" + " " + "three"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert result == '"one two three"'


class TestListConcatenation:
    """Test + operator for list concatenation."""

    def test_concat_number_lists(self):
        """Test number list concatenation: [1,2] + [3,4] returns [1,2,3,4]"""
        program = """
        result = [1, 2] + [3, 4]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        assert "[1, 2, 3, 4]" in result

    def test_concat_string_lists(self):
        """Test string list concatenation: ['a','b'] + ['c','d']"""
        program = """
        result = ["a", "b"] + ["c", "d"]
        output = "${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # Check for list elements
        assert "a" in result and "b" in result and "c" in result and "d" in result

    def test_concat_mixed_type_lists(self):
        """Test mixed type list concatenation: [1,'a'] + [True,[]]"""
        program = """
        result = [1, "a"] + [True, []]
        output = "${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # Should contain all elements
        assert "1" in result and "a" in result and "True" in result

    def test_concat_empty_left(self):
        """Test empty list on left: [] + [1,2]"""
        program = """
        result = [] + [1, 2]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        assert "[1, 2]" in result

    def test_concat_empty_right(self):
        """Test empty list on right: [1,2] + []"""
        program = """
        result = [1, 2] + []
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        assert "[1, 2]" in result

    def test_concat_both_empty(self):
        """Test two empty lists: [] + []"""
        program = """
        result = [] + []
        output = "${result}"
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        assert "[]" in result

    def test_concat_nested_lists(self):
        """Test nested list concatenation: [[1,2]] + [[3,4]]"""
        program = """
        result = [[1, 2]] + [[3, 4]]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        # Should preserve nesting with both nested lists present
        assert "[1, 2]" in result and "[3, 4]" in result

    def test_concat_preserves_nesting(self):
        """Test nesting is preserved: [1,[2,3]] + [[4,5],6]"""
        program = """
        result = [1, [2, 3]] + [[4, 5], 6]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        # Check structure is preserved
        assert "[2, 3]" in result and "[4, 5]" in result
        assert "1" in result and "6" in result

    def test_chain_list_concat(self):
        """Test chaining list concatenation: [1] + [2] + [3] + [4]"""
        program = """
        result = [1] + [2] + [3] + [4]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        assert "[1, 2, 3, 4]" in result

    def test_chain_multiple_elements(self):
        """Test chaining with multiple elements: [1,2] + [3,4] + [5,6]"""
        program = """
        result = [1, 2] + [3, 4] + [5, 6]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        result = cy.run(program)
        # When output directly, lists render as Python list syntax
        assert "[1, 2, 3, 4, 5, 6]" in result


class TestTypeValidationErrors:
    """Test type validation errors for mixed types with + operator."""

    def test_error_string_plus_int(self):
        """Test error: '1' + 1 raises CyRuntimeError"""
        program = """
        result = "1" + 1
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        # Check error message mentions both types
        error_msg = str(exc_info.value)
        assert "str" in error_msg or "string" in error_msg.lower()
        assert "int" in error_msg or "number" in error_msg.lower()

    def test_error_int_plus_string(self):
        """Test error: 1 + '1' raises CyRuntimeError"""
        program = """
        result = 1 + "1"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "str" in error_msg or "string" in error_msg.lower()

    def test_error_string_plus_float(self):
        """Test error: '1.5' + 1.5 raises CyRuntimeError"""
        program = """
        result = "1.5" + 1.5
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "str" in error_msg or "string" in error_msg.lower()

    def test_error_message_string_number(self):
        """Test error message quality for string + number"""
        program = """
        a = "hello"
        b = 42
        result = a + b
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        # Error should mention both types
        assert "str" in error_msg or "string" in error_msg.lower()
        assert "int" in error_msg or "number" in error_msg.lower()

    def test_error_list_plus_string(self):
        """Test error: [1] + 'a' raises CyRuntimeError"""
        program = """
        result = [1] + "a"
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "list" in error_msg.lower() or "array" in error_msg.lower()

    def test_error_string_plus_list(self):
        """Test error: 'a' + [1] raises CyRuntimeError"""
        program = """
        result = "a" + [1]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "str" in error_msg or "string" in error_msg.lower()
        assert "list" in error_msg.lower() or "array" in error_msg.lower()

    def test_error_list_plus_number(self):
        """Test error: [1] + 1 raises CyRuntimeError"""
        program = """
        result = [1] + 1
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "list" in error_msg.lower() or "array" in error_msg.lower()

    def test_error_number_plus_list(self):
        """Test error: 1 + [1] raises CyRuntimeError"""
        program = """
        result = 1 + [1]
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        assert "int" in error_msg or "number" in error_msg.lower()

    def test_error_message_list_mismatch(self):
        """Test error message for list type mismatch"""
        program = """
        a = [1, 2, 3]
        b = "not a list"
        result = a + b
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        # Should mention both types
        assert "list" in error_msg.lower() or "array" in error_msg.lower()
        assert "str" in error_msg or "string" in error_msg.lower()

    def test_error_message_helpful(self):
        """Test error message includes helpful guidance"""
        program = """
        result = "text" + 123
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        # Should suggest same type requirement
        assert "same type" in error_msg.lower() or "both" in error_msg.lower()

    def test_error_message_includes_types(self):
        """Test error shows actual types (e.g., 'str and int')"""
        program = """
        a = "hello"
        b = 42
        result = a + b
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        error_msg = str(exc_info.value)
        # Should show both type names
        has_str = "str" in error_msg or "string" in error_msg.lower()
        has_int = "int" in error_msg or "number" in error_msg.lower()
        assert has_str and has_int

    def test_error_includes_line_number(self):
        """Test error includes correct line number"""
        program = """
        a = "text"
        b = 123
        result = a + b
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        # Error should have line information
        error = exc_info.value
        assert hasattr(error, "line_number") or "line" in str(error).lower()

    def test_error_includes_column(self):
        """Test error includes correct column number"""
        program = """
        result = "text" + 123
        output = result
        return output
        """

        cy = Cy()
        cy.show_enhanced_errors = False
        with pytest.raises(CyRuntimeError) as exc_info:
            cy.run(program)

        # Error should have column/position information
        error = exc_info.value
        assert (
            hasattr(error, "col")
            or hasattr(error, "column")
            or hasattr(error, "column_number")
        )
