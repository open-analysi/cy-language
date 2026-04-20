"""Comprehensive integration tests for strict_input validation.

Tests strict_input with tools, external variables, conditionals, loops,
and try/catch to ensure complete coverage of real-world scenarios.

Following TDD: Tests written with full Cy syntax verification.
"""

import pytest

from cy_language import Cy, analyze_types


class TestStrictInputWithTools:
    """Test strict_input validation with tool calls."""

    def test_strict_input_with_valid_tool_call(self):
        """strict_input: Valid input field used in tool call."""
        script = """
ip = input["ip_address"]
result = virustotal_ip_report(ip)
return result
"""
        schema = {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string"},
                "timestamp": {"type": "number"},
            },
        }

        # Should NOT raise - ip_address exists in schema
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {}  # virustotal_ip_report returns Any (not registered)

    def test_strict_input_with_invalid_field_in_tool_call(self):
        """strict_input: Invalid input field used in tool call raises."""
        script = """
domain = input["domain_name"]
result = virustotal_domain_report(domain)
return result
"""
        schema = {"type": "object", "properties": {"ip_address": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "domain_name" in error_msg.lower()
        assert "ip_address" in error_msg

    def test_strict_input_with_multiple_tool_calls(self):
        """strict_input: Multiple tool calls with different input fields."""
        script = """
ip = input["ip_address"]
hash = input["file_hash"]

ip_report = virustotal_ip_report(ip)
hash_report = virustotal_ip_report(hash)

combined = ip_report + hash_report
return combined
"""
        schema = {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string"},
                "file_hash": {"type": "string"},
            },
        }

        # Should NOT raise - both fields exist
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        # Returns Any since virustotal_ip_report not registered
        assert output_schema == {}


class TestStrictInputWithConditionals:
    """Test strict_input validation with if/elif/else."""

    def test_strict_input_in_if_condition(self):
        """strict_input: Field access in if condition."""
        script = """
if (input["priority"] == "high") {
    result = "urgent"
} else {
    result = "normal"
}
return result
"""
        schema = {"type": "object", "properties": {"priority": {"type": "string"}}}

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_missing_field_in_if_condition(self):
        """strict_input: Missing field in if condition raises."""
        script = """
if (input["severity"] == "critical") {
    result = "alert"
} else {
    result = "ignore"
}
return result
"""
        schema = {"type": "object", "properties": {"priority": {"type": "string"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "severity" in error_msg.lower()

    def test_strict_input_in_elif_branches(self):
        """strict_input: Field access in elif branches."""
        script = """
status = input["alert_status"]

if (status == "new") {
    action = "investigate"
} elif (status == "in_progress") {
    action = "monitor"
} elif (status == "resolved") {
    action = "archive"
} else {
    action = "unknown"
}
return action
"""
        schema = {"type": "object", "properties": {"alert_status": {"type": "string"}}}

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_different_fields_in_branches(self):
        """strict_input: Different input fields in different branches."""
        script = """
type = input["event_type"]

if (type == "login") {
    user = input["username"]
    result = "User login: " + user
} elif (type == "logout") {
    user = input["username"]
    result = "User logout: " + user
} else {
    msg = input["message"]
    result = "Event: " + msg
}
return result
"""
        schema = {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "username": {"type": "string"},
                "message": {"type": "string"},
            },
        }

        # Should NOT raise - all fields exist
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_missing_field_in_else_branch(self):
        """strict_input: Missing field in else branch raises."""
        script = """
type = input["event_type"]

if (type == "login") {
    user = input["username"]
    result = user
} else {
    # This field doesn't exist!
    desc = input["description"]
    result = desc
}
return result
"""
        schema = {
            "type": "object",
            "properties": {
                "event_type": {"type": "string"},
                "username": {"type": "string"},
            },
        }

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "description" in error_msg.lower()


class TestStrictInputWithLoops:
    """Test strict_input validation with for-in and while loops."""

    def test_strict_input_with_for_in_loop(self):
        """strict_input: Field access in for-in loop."""
        script = """
items = input["threat_indicators"]
count = 0

for (item in items) {
    count = count + 1
}

return count
"""
        schema = {
            "type": "object",
            "properties": {
                "threat_indicators": {"type": "array", "items": {"type": "string"}}
            },
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "number"}

    def test_strict_input_missing_field_in_for_loop(self):
        """strict_input: Missing field accessed in for loop raises."""
        script = """
items = input["ip_addresses"]

for (ip in items) {
    result = virustotal_ip_report(ip)
}

return "done"
"""
        schema = {"type": "object", "properties": {"domains": {"type": "array"}}}

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "ip_addresses" in error_msg.lower()

    def test_strict_input_with_while_loop(self):
        """strict_input: Field access in while loop."""
        script = """
max_count = input["max_iterations"]
counter = 0

while (counter < max_count) {
    counter = counter + 1
}

return counter
"""
        schema = {
            "type": "object",
            "properties": {"max_iterations": {"type": "number"}},
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "number"}

    def test_strict_input_nested_loops_with_fields(self):
        """strict_input: Nested loops accessing multiple input fields."""
        script = """
outer_items = input["categories"]
inner_items = input["items"]
count = 0

for (category in outer_items) {
    for (item in inner_items) {
        count = count + 1
    }
}

return count
"""
        schema = {
            "type": "object",
            "properties": {
                "categories": {"type": "array", "items": {"type": "string"}},
                "items": {"type": "array", "items": {"type": "string"}},
            },
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "number"}


class TestStrictInputWithTryCatch:
    """Test strict_input validation with try/catch blocks."""

    def test_strict_input_in_try_block(self):
        """strict_input: Field access in try block."""
        script = """
try {
    data = input["risky_field"]
    result = str(data)
} catch (error) {
    result = "error occurred"
}
return result
"""
        schema = {"type": "object", "properties": {"risky_field": {"type": "string"}}}

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_missing_field_in_try_block(self):
        """strict_input: Missing field in try block raises."""
        script = """
try {
    # This field doesn't exist!
    data = input["missing_field"]
    result = data
} catch (error) {
    result = "fallback"
}
return result
"""
        schema = {
            "type": "object",
            "properties": {"existing_field": {"type": "string"}},
        }

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "missing_field" in error_msg.lower()

    def test_strict_input_in_catch_block(self):
        """strict_input: Field access in catch block."""
        script = """
try {
    result = "success"
} catch (error) {
    fallback = input["fallback_value"]
    result = fallback
}
return result
"""
        schema = {
            "type": "object",
            "properties": {"fallback_value": {"type": "string"}},
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

    def test_strict_input_nested_try_catch(self):
        """strict_input: Nested try/catch with multiple field accesses."""
        script = """
try {
    outer_data = input["outer_field"]
    try {
        inner_data = input["inner_field"]
        result = outer_data + inner_data
    } catch (inner_error) {
        result = outer_data
    }
} catch (outer_error) {
    default = input["default_value"]
    result = default
}
return result
"""
        schema = {
            "type": "object",
            "properties": {
                "outer_field": {"type": "string"},
                "inner_field": {"type": "string"},
                "default_value": {"type": "string"},
            },
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}


class TestStrictInputWithCombinedScenarios:
    """Test strict_input with combinations of tools, conditionals, loops, try/catch."""

    def test_strict_input_workflow_composition(self):
        """strict_input: Real-world workflow with all constructs."""
        script = """
# Get input data
alerts = input["alerts"]
threshold = input["severity_threshold"]

high_count = 0
low_count = 0

# Process each alert
for (alert in alerts) {
    try {
        # Extract alert properties (would need nested access in real scenario)
        severity = alert

        if (severity > threshold) {
            # High severity - investigate
            high_count = high_count + 1
        } else {
            # Low severity - log only
            low_count = low_count + 1
        }
    } catch (error) {
        # Error handling
        low_count = low_count + 1
    }
}

return high_count + low_count
"""
        schema = {
            "type": "object",
            "properties": {
                "alerts": {"type": "array", "items": {"type": "number"}},
                "severity_threshold": {"type": "number"},
            },
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "number"}

    def test_strict_input_missing_field_in_complex_workflow(self):
        """strict_input: Complex workflow with missing field raises."""
        script = """
events = input["security_events"]

for (event in events) {
    try {
        # This field doesn't exist!
        priority = input["priority_level"]

        if (priority == "critical") {
            result = "alert"
        } else {
            result = "log"
        }
    } catch (error) {
        result = "error"
    }
}

return "done"
"""
        schema = {
            "type": "object",
            "properties": {"security_events": {"type": "array"}},
        }

        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "priority_level" in error_msg.lower()

    def test_strict_input_conditional_in_loop_with_tool(self):
        """strict_input: Conditional inside loop with tool call."""
        script = """
ips = input["ip_list"]
count = 0

for (ip in ips) {
    if (ip != "") {
        # Call tool with IP
        report = virustotal_ip_report(ip)
        count = count + 1
    } else {
        count = count + 1
    }
}

return count
"""
        schema = {
            "type": "object",
            "properties": {"ip_list": {"type": "array", "items": {"type": "string"}}},
        }

        # Should NOT raise
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "number"}


class TestStrictInputPermissiveMode:
    """Test that strict_input=False allows missing fields (backward compat)."""

    def test_permissive_mode_allows_missing_fields(self):
        """strict_input=False: Missing fields are allowed (default behavior)."""
        script = """
name = input["name"]
age = input["age"]
city = input["city"]
return {"name": name, "age": age, "city": city}
"""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        # Should NOT raise - permissive mode
        output_schema = analyze_types(script, input_schema=schema, strict_input=False)
        assert output_schema["type"] == "object"

    def test_permissive_mode_in_complex_script(self):
        """strict_input=False: Complex script with missing fields allowed."""
        script = """
items = input["items"]

for (item in items) {
    # This field doesn't exist in schema, but should be allowed
    metadata = input["metadata"]

    if (metadata != null) {
        result = "has metadata"
    } else {
        result = "no metadata"
    }
}

return result
"""
        schema = {"type": "object", "properties": {"items": {"type": "array"}}}

        # Should NOT raise - permissive mode
        output_schema = analyze_types(script, input_schema=schema, strict_input=False)
        assert output_schema == {"type": "string"}


class TestStrictInputWithCyInterpreter:
    """Test strict_input with Cy interpreter (runtime + type checking)."""

    def test_cy_interpreter_strict_input_valid(self):
        """Cy interpreter with strict_input and valid input."""
        script = """
ip = input["ip_address"]
return "Processing: " + ip
"""
        schema = {"type": "object", "properties": {"ip_address": {"type": "string"}}}

        # First, verify type checking passes
        output_schema = analyze_types(script, input_schema=schema, strict_input=True)
        assert output_schema == {"type": "string"}

        # Now run it
        cy = Cy(check_types=False)
        result = cy.run(script, input_data={"ip_address": "192.168.1.1"})
        assert result == '"Processing: 192.168.1.1"'

    def test_cy_interpreter_strict_input_invalid(self):
        """Cy interpreter with strict_input catches errors at validation time."""
        script = """
domain = input["domain_name"]
return "Processing: " + domain
"""
        schema = {"type": "object", "properties": {"ip_address": {"type": "string"}}}

        # Type checking should fail
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, input_schema=schema, strict_input=True)

        error_msg = str(exc_info.value)
        assert "domain_name" in error_msg.lower()
        assert "ip_address" in error_msg

    def test_cy_with_check_types_auto_derives_schema(self):
        """Cy(check_types=True) auto-derives schema from input_data.

        Schema auto-derived from input_data still returns nullable types.
        Nullable operations require ?? operator.
        """
        # Use ?? operator for nullable indexed access
        script = """
name = input["name"] ?? ""
age = input["age"] ?? 0
return "Hello " + name
"""

        cy = Cy(check_types=True)

        # This should work - schema auto-derived from input_data
        result = cy.run(script, input_data={"name": "Alice", "age": 30})
        assert result == '"Hello Alice"'

        # Type errors caught at compile time
        with pytest.raises(TypeError):
            # name + age (string + number) should fail at compile time
            bad_script = """
name = input["name"] ?? ""
age = input["age"] ?? 0
result = name + age
return result
"""
            cy.run(bad_script, input_data={"name": "Alice", "age": 30})
