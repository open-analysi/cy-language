"""
Tests for the Cy JSON I/O contract and run_native() API.

The Cy interpreter has two output modes:
- run() / run_async() → returns valid JSON string (language-agnostic contract)
- run_native() / run_native_async() → returns Python objects (convenience for Python callers)

All run() output is valid JSON parseable by json.loads() in any language.
"""

import json

from cy_language import Cy


class TestJsonOutputContract:
    """run() returns valid JSON for ALL types."""

    def setup_method(self):
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_dict_returns_json_object(self):
        result = self.cy.run('return {"name": "test", "value": 42}')
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {"name": "test", "value": 42}

    def test_dict_uses_double_quotes(self):
        result = self.cy.run('return {"a": 1}')
        assert '"a"' in result  # JSON double quotes, not Python single quotes
        assert "'" not in result

    def test_list_returns_json_array(self):
        result = self.cy.run("return [1, 2, 3]")
        assert json.loads(result) == [1, 2, 3]

    def test_int_returns_json_number(self):
        result = self.cy.run("return 42")
        assert result == "42"
        assert json.loads(result) == 42

    def test_float_returns_json_number(self):
        result = self.cy.run("return 3.14")
        assert result == "3.14"
        assert json.loads(result) == 3.14

    def test_true_returns_json_true(self):
        result = self.cy.run("return True")
        assert result == "true"

    def test_false_returns_json_false(self):
        result = self.cy.run("return False")
        assert result == "false"

    def test_null_returns_json_null(self):
        result = self.cy.run("return null")
        assert result == "null"

    def test_string_returns_json_string(self):
        """String returns are JSON-encoded (with quotes)."""
        result = self.cy.run('return "hello"')
        assert result == '"hello"'
        assert json.loads(result) == "hello"

    def test_string_with_special_chars_is_escaped(self):
        result = self.cy.run(r'return "line1\nline2"')
        parsed = json.loads(result)
        assert parsed == "line1\nline2"

    def test_nested_structure_is_valid_json(self):
        program = """
data = {"list": [1, True, null], "nested": {"key": "value"}}
return data
"""
        result = self.cy.run(program)
        parsed = json.loads(result)
        assert parsed["list"] == [1, True, None]
        assert parsed["nested"]["key"] == "value"

    def test_all_outputs_parseable_by_json_loads(self):
        """Every return type produces valid JSON."""
        programs = [
            'return "hello"',
            "return 42",
            "return 3.14",
            "return True",
            "return False",
            "return null",
            "return [1, 2, 3]",
            'return {"a": 1}',
        ]
        for prog in programs:
            result = self.cy.run(prog)
            json.loads(result)  # Should not raise

    def test_no_return_produces_empty_string(self):
        cy_no_val = Cy(validate_output=False)
        cy_no_val.show_enhanced_errors = False
        result = cy_no_val.run("x = 5")
        assert result == ""

    def test_interpolated_string_returns_json_string(self):
        program = """
name = "Alice"
return "Hello ${name}"
"""
        result = self.cy.run(program)
        assert json.loads(result) == "Hello Alice"


class TestRunNativeTypes:
    """run_native() returns native Python objects (convenience for Python callers)."""

    def setup_method(self):
        self.cy = Cy()
        self.cy.show_enhanced_errors = False

    def test_return_dict_is_dict(self):
        result = self.cy.run_native('return {"name": "test", "value": 42}')
        assert isinstance(result, dict)
        assert result["name"] == "test"
        assert result["value"] == 42

    def test_return_nested_dict(self):
        program = """
data = {"name": "test", "active": True, "extra": null}
enriched = {"original": data, "added_field": "new_value"}
return enriched
"""
        result = self.cy.run_native(program)
        assert isinstance(result, dict)
        assert result["original"]["name"] == "test"
        assert result["original"]["active"] is True
        assert result["original"]["extra"] is None
        assert result["added_field"] == "new_value"

    def test_return_list_is_list(self):
        result = self.cy.run_native("return [1, 2, 3]")
        assert isinstance(result, list)
        assert result == [1, 2, 3]

    def test_return_int_is_int(self):
        result = self.cy.run_native("return 42")
        assert isinstance(result, int)
        assert result == 42

    def test_return_float_is_float(self):
        result = self.cy.run_native("return 3.14")
        assert isinstance(result, float)
        assert result == 3.14

    def test_return_bool_is_bool(self):
        assert self.cy.run_native("return True") is True
        assert self.cy.run_native("return False") is False

    def test_return_null_is_none(self):
        result = self.cy.run_native("return null")
        assert result is None

    def test_return_string_stays_string(self):
        result = self.cy.run_native('return "hello"')
        assert isinstance(result, str)
        assert result == "hello"

    def test_dict_field_access_after_return(self):
        """Reproduces the original bug: field access on returned dict."""
        program = """
alert = {"source_category": "Firewall", "title": "SQL Injection"}
return alert
"""
        result = self.cy.run_native(program)
        assert result["source_category"] == "Firewall"
        assert result["title"] == "SQL Injection"

    def test_no_return_produces_none(self):
        cy_no_val = Cy(validate_output=False)
        cy_no_val.show_enhanced_errors = False
        result = cy_no_val.run_native("x = 5")
        assert result is None
