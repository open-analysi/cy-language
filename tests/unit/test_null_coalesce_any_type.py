"""Unit tests for (Any | null) ?? T → T type inference.

improves type precision for the null coalescing operator when used with
(Any | null) types (commonly from dictionary access without schema).

Key Rule: (Any | null) ?? T → T (use the default value's type for better precision)
"""

import pytest

from cy_language import analyze_types


class TestAnyNullCoalesceWithString:
    """Test (Any | null) ?? string → string"""

    def test_dict_access_with_string_default(self):
        """Dict access returns (Any | null), default is string → result is string."""
        script = """
data = {"name": "Alice"}
title = data["title"] ?? "Unknown"
return title
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_string_default_used_in_concatenation(self):
        """String result from ?? can be used in string operations."""
        script = """
data = {"name": "Alice"}
title = data["title"] ?? "Unknown"
msg = "Title: " + title
return msg
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_string_default_in_interpolation(self):
        """String result from ?? works in string interpolation."""
        script = """
data = {"name": "Alice"}
title = data["title"] ?? "Unknown"
msg = "Title is: ${title}"
return msg
"""
        result = analyze_types(script)
        assert result == {"type": "string"}


class TestAnyNullCoalesceWithNumber:
    """Test (Any | null) ?? number → number"""

    def test_dict_access_with_numeric_default(self):
        """Dict access with numeric default returns number."""
        script = """
data = {"score": 95}
malicious_count = data["malicious"] ?? 0
return malicious_count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_numeric_default_used_in_math(self):
        """Numeric result from ?? can be used in math operations."""
        script = """
data = {"score": 95}
malicious_count = data["malicious"] ?? 0
total = malicious_count + 10
return total
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_multiple_numeric_defaults_in_math(self):
        """Multiple dict accesses with numeric defaults work in calculations."""
        script = """
data = {"a": 1}
malicious = data["malicious"] ?? 0
suspicious = data["suspicious"] ?? 0
harmless = data["harmless"] ?? 0
total = malicious + suspicious + harmless
return total
"""
        result = analyze_types(script)
        assert result == {"type": "number"}


class TestAnyNullCoalesceWithBoolean:
    """Test (Any | null) ?? boolean → boolean"""

    def test_dict_access_with_boolean_default(self):
        """Dict access with boolean default returns boolean."""
        script = """
data = {"enabled": True}
is_public = data["is_public"] ?? False
return is_public
"""
        result = analyze_types(script)
        assert result == {"type": "boolean"}

    def test_boolean_default_in_conditional(self):
        """Boolean result from ?? works in conditionals."""
        script = """
data = {"enabled": True}
is_public = data["is_public"] ?? False
result = if (is_public) { "public" } else { "private" }
return result
"""
        result = analyze_types(script)
        assert result == {"type": "string"}


class TestAnyNullCoalesceWithArray:
    """Test (Any | null) ?? array → array"""

    def test_dict_access_with_array_default(self):
        """Dict access with array default returns array."""
        script = """
data = {"items": [1, 2, 3]}
entries = data["entries"] ?? []
return entries
"""
        result = analyze_types(script)
        assert result["type"] == "array"

    def test_array_default_used_with_len(self):
        """Array result from ?? can be used with len()."""
        script = """
data = {"items": [1, 2, 3]}
entries = data["entries"] ?? []
count = len(entries)
return count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_array_default_with_typed_elements(self):
        """Array default with specific element type."""
        script = """
data = {"names": ["Alice"]}
tags = data["tags"] ?? ["default", "tag"]
return tags
"""
        result = analyze_types(script)
        assert result["type"] == "array"
        assert result["items"]["type"] == "string"


class TestAnyNullCoalesceWithDict:
    """Test (Any | null) ?? dict → dict"""

    def test_dict_access_with_dict_default(self):
        """Dict access with dict default returns dict."""
        script = """
data = {"user": {"name": "Alice"}}
enrichments = data["enrichments"] ?? {}
return enrichments
"""
        result = analyze_types(script)
        assert result["type"] == "object"

    def test_dict_default_used_with_len(self):
        """Dict result from ?? can be used with len()."""
        script = """
data = {"user": {"name": "Alice"}}
enrichments = data["enrichments"] ?? {}
count = len(enrichments)
return count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}


class TestAnyNullCoalesceChaining:
    """Test chained ?? operators with (Any | null) types"""

    def test_chain_two_any_null_then_string(self):
        """(Any | null) ?? (Any | null) ?? string → string"""
        script = """
data1 = {"a": 1}
data2 = {"b": 2}
value = data1["x"] ?? data2["y"] ?? "default"
return value
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_chain_two_any_null_then_number(self):
        """(Any | null) ?? (Any | null) ?? number → number"""
        script = """
data1 = {"a": 1}
data2 = {"b": 2}
value = data1["x"] ?? data2["y"] ?? 0
return value
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_chain_any_null_with_null_final(self):
        """(Any | null) ?? null → null (edge case - not used in practice)"""
        script = """
data = {"a": 1}
value = data["x"] ?? null
return value
"""
        result = analyze_types(script)
        # Edge case: ?? null effectively returns null (removes non-null from left)
        # This pattern doesn't appear in real code - just accessing data["x"] would be equivalent
        assert result == {"type": "null"}


class TestAnyNullCoalesceEdgeCases:
    """Test edge cases for (Any | null) ?? T"""

    def test_both_sides_any_null(self):
        """(Any | null) ?? (Any | null) → (Any | null)"""
        script = """
data1 = {"a": 1}
data2 = {"b": 2}
value = data1["x"] ?? data2["y"]
return value
"""
        result = analyze_types(script)
        # When both sides are (Any | null), result is still (Any | null)
        assert "oneOf" in result

    def test_any_null_with_union_default(self):
        """(Any | null) ?? (string | number) → (string | number)"""
        script = """
data = {"a": 1}
flag = True
default = if (flag) { "text" } else { 42 }
value = data["x"] ?? default
return value
"""
        result = analyze_types(script)
        # Default is (string | number), so result should be that union
        assert "oneOf" in result
        types = [t.get("type") for t in result["oneOf"]]
        assert "string" in types
        assert "number" in types


class TestRealWorldPatterns:
    """Test real-world patterns from actual Cy scripts"""

    def test_virustotal_pattern(self):
        """Real pattern from virustotal_file_hash_reputation_analysis.cy"""
        script = """
reputation_summary = {"malicious": 5, "suspicious": 2}
malicious_count = reputation_summary["malicious"] ?? 0
suspicious_count = reputation_summary["suspicious"] ?? 0
harmless_count = reputation_summary["harmless"] ?? 0
undetected_count = reputation_summary["undetected"] ?? 0
total_engines = malicious_count + suspicious_count + harmless_count + undetected_count
return total_engines
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_alert_analysis_pattern(self):
        """Real pattern from ad_ldap_user_lookup.cy"""
        script = """
alert = {"title": "Security Alert", "severity": "high"}
alert_title = alert["title"] ?? "Unknown Alert"
alert_severity = alert["severity"] ?? "unknown"
alert_source_vendor = alert["source_vendor"] ?? "Unknown Vendor"
analysis_prompt = "Alert: ${alert_title}, Severity: ${alert_severity}, Vendor: ${alert_source_vendor}"
return analysis_prompt
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_array_membership_pattern(self):
        """Real pattern from ad_ldap_privileged_user_check.cy"""
        script = """
attributes = {"cn": "Alice"}
member_of = attributes["memberOf"] ?? []
group_count = len(member_of)
return group_count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_enrichments_pattern(self):
        """Real pattern from alert_detailed_analysis.cy"""
        script = """
alert = {"title": "Test"}
existing_enrichments = alert["enrichments"] ?? {}
enrichments_count = len(existing_enrichments)
return enrichments_count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}


class TestBackwardCompatibility:
    """Ensure existing behavior is preserved for non-(Any | null) cases"""

    def test_regular_nullable_with_default(self):
        """(string | null) ?? string → string (existing behavior)"""
        script = """
data = {"name": "Alice"}
name = data.name ?? "Unknown"
return name
"""
        # This uses field access (not indexed), so type is based on known schema
        result = analyze_types(script)
        # Should still work correctly
        assert result == {"type": "string"}

    def test_number_nullable_with_default(self):
        """(number | null) ?? number → number (existing behavior)"""
        script = """
items = [1, 2, 3]
first = items[0] ?? 0
return first
"""
        result = analyze_types(script)
        assert result == {"type": "number"}


class TestDenullifiedOperations:
    """Test that denullified values work correctly in operations"""

    def test_denullified_numbers_in_math(self):
        """Denullified numbers should work in math operations."""
        script = """
data = {"a": 1, "b": 2}
x = data["x"] ?? 0
y = data["y"] ?? 0
total = x + y
return total
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_denullified_strings_in_concatenation(self):
        """Denullified strings should work in string operations."""
        script = """
data = {"first": "Alice"}
first = data["first"] ?? "Unknown"
last = data["last"] ?? "User"
full_name = first + " " + last
return full_name
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_mixed_types_denullified_should_fail(self):
        """Denullifying to different types should cause type errors when mixed."""
        script = """
data = {"a": 1}
x = data["x"] ?? 0
y = data["y"] ?? "string"
result = x + y
return result
"""
        # Should fail because x is number, y is string
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)
        error_msg = str(exc_info.value).lower()
        assert "cannot add" in error_msg and (
            "number" in error_msg and "string" in error_msg
        )

    def test_denullified_boolean_in_conditional(self):
        """Denullified booleans should work in conditionals."""
        script = """
data = {"enabled": True}
is_active = data["is_active"] ?? False
result = if (is_active) { "active" } else { "inactive" }
return result
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_multiple_denullified_numbers_calculation(self):
        """Complex math with multiple denullified numbers."""
        script = """
stats = {"malicious": 5, "suspicious": 2}
malicious = stats["malicious"] ?? 0
suspicious = stats["suspicious"] ?? 0
harmless = stats["harmless"] ?? 0
undetected = stats["undetected"] ?? 0
total = (malicious * 10) + (suspicious * 5) + harmless + undetected
return total
"""
        result = analyze_types(script)
        assert result == {"type": "number"}


class TestDenullifiedToolParameters:
    """Test denullified values passed to typed tool parameters"""

    def test_denullified_correct_type_to_tool(self):
        """Denullified value with correct type should work."""
        script = """
data = {"ip": "8.8.8.8"}
ip_addr = data["ip"] ?? "0.0.0.0"
result = app::test::string_param(value=ip_addr)
return result
"""

        tool_registry = {
            "app::test::string_param": {
                "parameters": {"value": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }

        result = analyze_types(script, tool_registry=tool_registry)
        assert result == {"type": "string"}

    def test_denullified_wrong_type_to_tool(self):
        """Denullified value with wrong type should fail."""
        script = """
data = {"count": 42}
count = data["count"] ?? "zero"
result = app::test::int_param(value=count)
return result
"""

        tool_registry = {
            "app::test::int_param": {
                "parameters": {"value": {"type": "number"}},
                "return_type": {"type": "number"},
            }
        }

        # Should fail because count is string, but tool expects number
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=tool_registry)
        error_msg = str(exc_info.value)
        assert "type" in error_msg.lower() or "mismatch" in error_msg.lower()

    def test_denullified_multiple_params(self):
        """Multiple denullified values as tool parameters."""
        script = """
data = {"name": "Alice"}
name = data["name"] ?? "Unknown"
age = data["age"] ?? 0
active = data["active"] ?? True
result = app::test::multi_param(name=name, age=age, active=active)
return result
"""

        tool_registry = {
            "app::test::multi_param": {
                "parameters": {
                    "name": {"type": "string"},
                    "age": {"type": "number"},
                    "active": {"type": "boolean"},
                },
                "return_type": {"type": "string"},
            }
        }

        result = analyze_types(script, tool_registry=tool_registry)
        assert result == {"type": "string"}

    def test_not_denullified_should_fail(self):
        """Nullable value without ?? should fail when passed to tool."""
        script = """
data = {"ip": "8.8.8.8"}
ip_addr = data["ip"]
result = app::test::string_param(value=ip_addr)
return result
"""

        tool_registry = {
            "app::test::string_param": {
                "parameters": {"value": {"type": "string"}},
                "return_type": {"type": "string"},
            }
        }

        # Should fail because ip_addr is (Any | null), not string
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=tool_registry)
        # The error should mention type issues
        error_msg = str(exc_info.value).lower()
        assert "type" in error_msg or "parameter" in error_msg


class TestNullableToolReturns:
    """Test handling of nullable return values from tools"""

    def test_tool_returns_nullable_with_denullification(self):
        """Tool that might return null, denullified."""
        script = """
result = app::test::maybe_null()
safe_result = result ?? "default"
return safe_result
"""

        tool_registry = {
            "app::test::maybe_null": {
                "parameters": {},
                "return_type": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            }
        }

        result = analyze_types(script, tool_registry=tool_registry)
        assert result == {"type": "string"}

    def test_tool_returns_nullable_used_directly_should_fail(self):
        """Tool that might return null, used without ??."""
        script = """
result = app::test::maybe_null()
final = "Value: " + result
return final
"""

        tool_registry = {
            "app::test::maybe_null": {
                "parameters": {},
                "return_type": {"oneOf": [{"type": "string"}, {"type": "null"}]},
            }
        }

        # Should fail because result is (string | null) but used directly
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=tool_registry)
        assert (
            "nullable" in str(exc_info.value).lower()
            or "null" in str(exc_info.value).lower()
        )

    def test_chained_tool_calls_with_denullification(self):
        """Chain tool calls with nullable returns."""
        script = """
x = app::test::maybe_int()
safe_x = x ?? 0
y = app::test::maybe_int()
safe_y = y ?? 0
total = safe_x + safe_y
return total
"""

        tool_registry = {
            "app::test::maybe_int": {
                "parameters": {},
                "return_type": {"oneOf": [{"type": "number"}, {"type": "null"}]},
            }
        }

        result = analyze_types(script, tool_registry=tool_registry)
        assert result == {"type": "number"}

    def test_tool_nullable_return_gets_string_type(self):
        """Tool returns (number | null), denullified with string gets string type."""
        script = """
count = app::test::maybe_int()
safe_count = count ?? "zero"
return safe_count
"""

        tool_registry = {
            "app::test::maybe_int": {
                "parameters": {},
                "return_type": {"oneOf": [{"type": "number"}, {"type": "null"}]},
            }
        }

        # (number | null) ?? string → (number | string) using standard ?? logic
        # This is NOT the (Any | null) optimization (which only affects (Any | null) ?? T)
        result = analyze_types(script, tool_registry=tool_registry)
        assert "oneOf" in result  # Should be a union
        types = [t.get("type") for t in result["oneOf"]]
        assert "number" in types and "string" in types


class TestComplexDenullificationScenarios:
    """Test complex real-world scenarios with denullification"""

    def test_mixed_denullified_and_literal_values(self):
        """Mix denullified and literal values in calculations."""
        script = """
data = {"base": 100}
multiplier = data["multiplier"] ?? 2
bonus = 50
total = (data["value"] ?? 0) * multiplier + bonus
return total
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_denullified_in_nested_conditionals(self):
        """Denullified values in nested if/else."""
        script = """
data = {"score": 85}
score = data["score"] ?? 0
grade = if (score >= 90) {
    "A"
} else {
    if (score >= 80) { "B" } else { "C" }
}
return grade
"""
        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_denullified_array_operations(self):
        """Denullified arrays in operations."""
        script = """
data = {"items": [1, 2, 3]}
items = data["items"] ?? []
count = len(items)
return count
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_denullified_dict_operations(self):
        """Denullified dicts in operations."""
        script = """
data = {"metadata": {"a": 1}}
metadata = data["metadata"] ?? {}
size = len(metadata)
return size
"""
        result = analyze_types(script)
        assert result == {"type": "number"}

    def test_string_interpolation_with_denullified(self):
        """String interpolation with denullified values."""
        script = """
data = {"name": "Alice"}
name = data["name"] ?? "Unknown"
age = data["age"] ?? 0
message = "User ${name} is ${age} years old"
return message
"""
        result = analyze_types(script)
        assert result == {"type": "string"}
