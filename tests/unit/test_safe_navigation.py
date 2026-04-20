"""
Safe Navigation Tests

Comprehensive testing of:
- Python-like 'or' operator returning values (not booleans)
- Field access returning null for missing keys
- Indexed access returning null for missing keys
- Safe navigation in string interpolations
- Mixed dot and bracket notation
"""

import json

import pytest

from cy_language import Cy


class TestOrOperatorValueSemantics:
    """Test that 'or' returns actual values, not boolean True/False."""

    def test_or_returns_first_truthy_value(self):
        """Test: x or y returns first truthy value"""
        code = 'result = "hello" or "default"\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == '"hello"'

    def test_or_returns_second_if_first_falsy(self):
        """Test: null or default returns default"""
        code = 'result = null or "default"\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_or_with_zero_returns_second(self):
        """Test: 0 or 42 returns 42 (0 is falsy)"""
        code = "result = 0 or 42\nreturn result"
        cy = Cy()
        result = cy.run(code)
        assert result == "42"  # Cy serializes numbers to strings

    def test_or_with_empty_string_returns_second(self):
        """Test: empty string or default returns default"""
        code = 'result = "" or "default"\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_or_with_false_returns_second(self):
        """Test: False or True returns True"""
        code = "result = False or True\nreturn result"
        cy = Cy()
        result = cy.run(code)
        assert result == "true"

    def test_or_with_multiple_values(self):
        """Test: null or 0 or '' or 'found' returns 'found'"""
        code = 'result = null or 0 or "" or "found"\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == '"found"'

    def test_or_returns_last_if_all_falsy(self):
        """Test: all falsy values returns last one"""
        code = "result = null or 0 or False\nreturn result"
        cy = Cy()
        result = cy.run(code)
        assert result == "false"

    def test_and_returns_first_falsy(self):
        """Test: 'and' returns first falsy value"""
        code = 'result = "hello" and 0 and "world"\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == "0"

    def test_and_returns_last_if_all_truthy(self):
        """Test: 'and' returns last value if all truthy"""
        code = 'result = "hello" and "world" and 42\nreturn result'
        cy = Cy()
        result = cy.run(code)
        assert result == "42"


class TestFieldAccessReturnsNull:
    """Test that field access returns null for missing keys (dot notation)."""

    def test_field_access_returns_null_for_missing_key(self):
        """Test: obj.missing returns null"""
        code = """
obj = {"name": "Alice"}
result = obj.missing
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_nested_field_access_returns_null(self):
        """Test: obj.user.missing returns null"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj.user.missing
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_deeply_nested_stops_at_first_null(self):
        """Test: obj.missing.also.still returns null at first missing"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj.missing.also_missing.still_missing
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_field_access_on_null_returns_null(self):
        """Test: null.field returns null"""
        code = """
obj = null
result = obj.field
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_mixed_existing_and_missing_fields(self):
        """Test: Mix of existing and missing fields"""
        code = """
obj = {"user": {"name": "Alice", "age": 30}}
existing = obj.user.name
missing = obj.user.address
return {"existing": existing, "missing": missing}
"""
        cy = Cy()
        result = cy.run(code)
        assert json.loads(result) == {"existing": "Alice", "missing": None}


class TestIndexedAccessReturnsNull:
    """Test that indexed access returns null for missing keys (bracket notation)."""

    def test_indexed_access_returns_null_for_missing_key(self):
        """Test: obj['missing'] returns null"""
        code = """
obj = {"name": "Alice"}
result = obj["missing"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_nested_indexed_access_returns_null(self):
        """Test: obj['user']['missing'] returns null"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj["user"]["missing"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_deeply_nested_indexed_access(self):
        """Test: deeply nested indexed access with missing keys"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj["missing"]["also"]["still"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_indexed_access_on_null_returns_null(self):
        """Test: null['field'] returns null"""
        code = """
obj = null
result = obj["field"]
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"


class TestMixedNotation:
    """Test mixing dot and bracket notation.

    Mixed notation is not supported due to parser limitation.
    These tests verify that mixed notation raises clear syntax errors.
    """

    def test_dot_then_bracket_notation(self):
        """Test: obj.user['data'].name raises clear syntax error"""
        code = """
obj = {"user": {"data": {"name": "Alice"}}}
result = obj.user["data"].name
return result
"""
        cy = Cy()
        with pytest.raises(Exception) as exc_info:
            cy.run(code)
        # With enhanced errors, we get a SyntaxError for mixed notation
        error_str = str(exc_info.value)
        assert "SyntaxError" in error_str or "Syntax" in error_str

    def test_bracket_then_dot_notation(self):
        """Test: obj['user'].data['name'] raises clear syntax error"""
        code = """
obj = {"user": {"data": {"name": "Alice"}}}
result = obj["user"].data["name"]
return result
"""
        cy = Cy()
        with pytest.raises(Exception) as exc_info:
            cy.run(code)
        # With enhanced errors, we get a SyntaxError for mixed notation
        error_str = str(exc_info.value)
        assert "SyntaxError" in error_str or "Syntax" in error_str

    def test_mixed_with_missing_field(self):
        """Test: mixed notation raises clear syntax error"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj.user["missing"].field
return result
"""
        cy = Cy()
        with pytest.raises(Exception) as exc_info:
            cy.run(code)
        # With enhanced errors, we get a SyntaxError for mixed notation
        error_str = str(exc_info.value)
        assert "SyntaxError" in error_str or "Syntax" in error_str


class TestSafeNavigationWithOrDotNotation:
    """Test safe navigation pattern with 'or' operator (dot notation)."""

    def test_simple_field_with_or(self):
        """Test: obj.missing or 'default' returns default"""
        code = """
obj = {"name": "Alice"}
result = obj.missing or "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_nested_field_with_or(self):
        """Test: obj.user.address or 'Unknown' returns Unknown"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj.user.address or "Unknown"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Unknown"'

    def test_deeply_nested_with_or(self):
        """Test: deeply nested missing field with or"""
        code = """
alert = {"enrichments": {"network": {"ip": "1.2.3.4"}}}
result = alert.enrichments.network.details.source_ip or "0.0.0.0"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"0.0.0.0"'

    def test_existing_field_with_or_returns_value(self):
        """Test: existing field with or returns the actual value"""
        code = """
obj = {"name": "Alice"}
result = obj.name or "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Alice"'

    def test_multiple_or_defaults(self):
        """Test: multiple or clauses"""
        code = """
obj = {}
result = obj.a or obj.b or obj.c or "fallback"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"fallback"'


class TestSafeNavigationWithOrBracketNotation:
    """Test safe navigation with 'or' operator (bracket notation)."""

    def test_indexed_with_or(self):
        """Test: obj['missing'] or 'default'"""
        code = """
obj = {"name": "Alice"}
result = obj["missing"] or "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_nested_indexed_with_or(self):
        """Test: obj['user']['address'] or 'Unknown'"""
        code = """
obj = {"user": {"name": "Alice"}}
result = obj["user"]["address"] or "Unknown"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Unknown"'

    def test_deeply_nested_indexed_with_or(self):
        """Test: deeply nested indexed access with or"""
        code = """
alert = {"enrichments": {}}
result = alert["enrichments"]["network"]["source_ip"] or "0.0.0.0"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"0.0.0.0"'


class TestSafeNavigationInInterpolations:
    """Test safe navigation inside string interpolations."""

    def test_interpolation_with_missing_field(self):
        """Test: interpolation with missing field and or"""
        code = """
obj = {"name": "Alice"}
result = "User: ${obj.user or 'Unknown'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"User: Unknown"'

    def test_interpolation_with_nested_missing(self):
        """Test: deeply nested in interpolation"""
        code = """
alert = {"title": "Test"}
result = "IP: ${alert.enrichments.network.source_ip or '0.0.0.0'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"IP: 0.0.0.0"'

    def test_interpolation_with_bracket_notation(self):
        """Test: bracket notation in interpolation"""
        code = """
obj = {}
result = "Value: ${obj['missing'] or 'N/A'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Value: N/A"'

    def test_interpolation_with_existing_field(self):
        """Test: existing field in interpolation"""
        code = """
obj = {"name": "Alice"}
result = "Name: ${obj.name or 'Unknown'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Name: Alice"'

    def test_multiple_interpolations_with_or(self):
        """Test: multiple interpolations with or"""
        code = """
alert = {"title": "Alert"}
result = "Alert: ${alert.title}, IP: ${alert.ip or 'N/A'}, Score: ${alert.score or 0}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Alert: Alert, IP: N/A, Score: 0"'

    def test_interpolation_with_mixed_notation(self):
        """Test: mixed dot/bracket in interpolation raises syntax error"""
        code = """
obj = {"user": {}}
result = "City: ${obj.user['address'].city or 'Unknown'}"
return result
"""
        cy = Cy()
        with pytest.raises(Exception) as exc_info:
            cy.run(code)
        # Parser error - either "Mixed notation" or "Invalid expression syntax"
        assert "syntax" in str(exc_info.value).lower() or "Mixed" in str(exc_info.value)

    def test_interpolation_deeply_nested_path(self):
        """Test: very deeply nested path in interpolation"""
        code = """
alert = {}
result = "Source: ${alert.enrichments.virustotal.data.attributes.reputation or 'clean'}"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Source: clean"'


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_accessing_field_on_non_dict_type_returns_null(self):
        """Test: - accessing field on number returns null (safe navigation)"""
        code = """
value = 42
result = value.field
return result
"""
        cy = Cy()
        result = cy.run(code)
        # Returns None (serialized as "None") instead of raising error
        assert result == "null"

    def test_null_propagates_through_entire_chain(self):
        """Test: null propagates through long chain"""
        code = """
obj = null
result = obj.a.b.c.d.e
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "null"

    def test_empty_dict_field_access(self):
        """Test: empty dict nested access with or"""
        code = """
obj = {}
result = obj.a.b.c or "default"
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"default"'

    def test_or_with_complex_expressions(self):
        """Test: or with multiple object accesses"""
        code = """
obj1 = {}
obj2 = {"value": 100}
result = obj1.missing or obj2.value or 0
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == "100"

    def test_nested_or_expressions(self):
        """Test: nested or expressions"""
        code = """
obj = {}
result = (obj.a or obj.b) or (obj.c or "final")
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"final"'


class TestEdgeCaseFalsyValues:
    """Test edge case: 'or' with falsy but valid values.

    WARNING: 'or' uses Python truthiness semantics.
    This means valid values like 0, [], {} are considered falsy
    and will be replaced by the 'or' default!

    This is EXPECTED BEHAVIOR (Python compatibility), but can be surprising.
    """

    def test_or_with_zero_replaces_zero(self):
        """Test: 0 is falsy, so 'or' replaces it (may be surprising!)"""
        code = """
data = {"age": 0}
age = data.age or 99
return age
"""
        cy = Cy()
        result = cy.run(code)
        # WARNING: 0 is falsy, so it gets replaced with 99!
        # This might NOT be what you want if 0 is a valid value
        assert result == "99"

    def test_or_with_empty_array_replaces_it(self):
        """Test: [] is falsy, so 'or' replaces it (may be surprising!)"""
        code = """
data = {"items": []}
items = data.items or ["default"]
return items
"""
        cy = Cy()
        result = cy.run(code)
        # WARNING: Empty array [] is falsy, so it gets replaced!
        assert json.loads(result) == ["default"]

    def test_or_with_empty_object_replaces_it(self):
        """Test: {} is falsy, so 'or' replaces it (may be surprising!)"""
        code = """
data = {"config": {}}
config = data.config or {"default": True}
return config
"""
        cy = Cy()
        result = cy.run(code)
        # WARNING: Empty object {} is falsy, so it gets replaced!
        assert json.loads(result) == {"default": True}

    def test_or_with_empty_string_replaces_it(self):
        """Test: empty string is falsy (usually desired behavior)"""
        code = """
data = {"name": ""}
name = data.name or "Anonymous"
return name
"""
        cy = Cy()
        result = cy.run(code)
        # Empty string → "Anonymous" is usually what we want
        assert result == '"Anonymous"'

    def test_workaround_explicit_null_check(self):
        """Test: Workaround for 0 being valid - explicit null check"""
        code = """
data = {"count": 0}
count = data.count
if (count == null) {
    count = 99
}
return count
"""
        cy = Cy()
        result = cy.run(code)
        # Explicit null check preserves 0 as valid value
        assert result == "0"

    def test_or_with_missing_key_replaces_null(self):
        """Test: null (missing key) IS what 'or' should replace"""
        code = """
data = {}
value = data.missing or "default"
return value
"""
        cy = Cy()
        result = cy.run(code)
        # This is the main use case: null → default
        assert result == '"default"'


class TestProductionScenarios:
    """Test production-like scenarios from real tasks."""

    def test_alert_enrichment_pattern(self):
        """Test: typical alert enrichment access pattern"""
        code = """
alert = {
    "title": "Suspicious Activity",
    "enrichments": {}
}
vt_score = alert.enrichments.virustotal.score or 0
abuse_score = alert.enrichments.abuseipdb.score or 0
result = {"vt": vt_score, "abuse": abuse_score}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert json.loads(result) == {"vt": 0, "abuse": 0}

    def test_user_lookup_pattern(self):
        """Test: LDAP user lookup pattern with fallbacks"""
        code = """
user = {
    "username": "jdoe",
    "attributes": {"mail": "jdoe@example.com"}
}
display_name = user.attributes.displayName or user.username or "Unknown"
email = user.attributes.mail or "no-email@example.com"
result = {"name": display_name, "email": email}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert json.loads(result) == {"name": "jdoe", "email": "jdoe@example.com"}

    def test_network_data_pattern(self):
        """Test: network event with multiple fallback fields"""
        code = """
event = {
    "timestamp": "2025-01-01",
    "network": {}
}
source_ip = event.network.source_ip or event.src_ip or "0.0.0.0"
dest_ip = event.network.dest_ip or event.dst_ip or "0.0.0.0"
result = {"src": source_ip, "dst": dest_ip}
return result
"""
        cy = Cy()
        result = cy.run(code)
        assert json.loads(result) == {"src": "0.0.0.0", "dst": "0.0.0.0"}

    def test_safe_navigation_in_string_interpolation(self):
        """Test: Safe navigation works within string interpolation - returns 'null' not error"""
        code = """
y = {"a": 2, "b": {"c": 3}}

# y.b.c exists and is 3, but 3.s doesn't exist - should return "null"
x = "${y.b.c.s}"

return x
"""
        cy = Cy()
        result = cy.run(code)
        # y.b.c exists and is 3, but 3.s doesn't exist - should return "null"
        assert result == '"null"'

    def test_safe_navigation_chain_in_interpolation(self):
        """Test: Multiple levels of missing fields in interpolation"""
        code = """
data = {"user": {"name": "Alice"}}

# user.address doesn't exist, so address.street.number also doesn't exist
message = "Address: ${data.user.address.street.number}"

return message
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Address: null"'

    def test_existing_path_in_interpolation(self):
        """Test: Existing nested path in interpolation works normally"""
        code = """
y = {"a": 2, "b": {"c": 3}}

message = "Value: ${y.b.c}"

return message
"""
        cy = Cy()
        result = cy.run(code)
        assert result == '"Value: 3"'

    def test_safe_navigation_on_primitives(self):
        """Test: Accessing fields on primitive types returns null"""
        code = """
# Accessing field on number
number = 42
num_field = number.foo  # Returns null, not error

# Accessing field on string
text = "hello"
text_field = text.bar  # Returns null, not error

# Accessing field on boolean
flag = True
flag_field = flag.baz  # Returns null, not error

# Accessing field on array
arr = [1, 2, 3]
arr_field = arr.qux  # Returns null, not error

result = {
    "num": num_field,
    "text": text_field,
    "flag": flag_field,
    "arr": arr_field
}

return result
"""
        cy = Cy()
        result = cy.run(code)
        parsed = json.loads(result)
        # All should be None (null)
        assert parsed == {"num": None, "text": None, "flag": None, "arr": None}
