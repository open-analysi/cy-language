"""
Integration tests for Workflow Chain Type Validation.

Tests demonstrate how type checking validates data flow through
multiple Cy scripts in a chain. Tests use scripts created via
cy-script-assistant MCP to show realistic workflow composition.

Tests include:
- 1 positive case: Types align correctly through 3-script chain
- 4 negative cases: Type mismatches caught by static analysis

Note: Impact:
- Field access now returns union types (T | null)
- Tests updated to handle oneOf schemas
"""

import pytest

from cy_language import analyze_types


def get_type_from_schema(schema):
    """
    Extract the primary type from a schema, handling union types.

    Field access returns union types like:
    {"oneOf": [{"type": "string"}, {"type": "null"}]}

    This helper extracts the non-null type.
    """
    if "type" in schema:
        return schema["type"]
    if "oneOf" in schema:
        # Find the non-null type in the union
        for variant in schema["oneOf"]:
            if variant.get("type") != "null":
                return variant["type"]
        # If all are null, return null
        return "null"
    # Unknown/any type
    return None


class TestWorkflowChainPositive:
    """Test workflow chain with correct type alignment."""

    def test_three_script_chain_types_align_correctly(self):
        """
        Positive case: 3 scripts chain together with proper types.

        Flow:
        1. IP Analysis: {ip: string} → {ip: string, ip_length: number, formatted_ip: string}
        2. Risk Scoring: uses ip_length to calculate risk_score
        3. Classification: uses risk_score to classify threat level
        """
        # Script 1: IP Analysis
        script_1 = """
formatted = str(input.ip)
length = len(formatted)

output = {
  "ip": input.ip,
  "ip_length": length,
  "formatted_ip": formatted
}
return output
"""

        # Script 2: Risk Scoring
        script_2 = """
ip_len = input.ip_length
base_score = ip_len * 2

risk_multiplier = 1.5
risk_score = base_score * risk_multiplier

output = {
  "ip": input.ip,
  "risk_score": risk_score,
  "base_score": base_score
}
return output
"""

        # Script 3: Classification
        script_3 = """
score = input.risk_score

if (score > 30) {
  classification = "HIGH"
} elif (score > 15) {
  classification = "MEDIUM"
} else {
  classification = "LOW"
}

threat_level = str(classification)

output = {
  "ip": input.ip,
  "risk_score": score,
  "classification": classification,
  "threat_description": threat_level
}
return output
"""

        # Analyze Script 1
        input_schema_1 = {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
            "required": ["ip"],
        }

        # Use strict_input=True for workflow validation to get precise types
        output_schema_1 = analyze_types(
            script_1,
            input_schema=input_schema_1,
            strict_input=True,
        )

        # Verify Script 1 output has correct types
        assert output_schema_1["type"] == "object"
        assert "properties" in output_schema_1
        # With strict_input, field access returns base types
        assert get_type_from_schema(output_schema_1["properties"]["ip"]) == "string"
        assert (
            get_type_from_schema(output_schema_1["properties"]["ip_length"]) == "number"
        )
        assert (
            get_type_from_schema(output_schema_1["properties"]["formatted_ip"])
            == "string"
        )

        # Analyze Script 2 using Script 1's output as input
        # strict_input=True ensures input field access returns precise types
        output_schema_2 = analyze_types(
            script_2,
            input_schema=output_schema_1,
            strict_input=True,
        )

        # Verify Script 2 output has correct types
        assert get_type_from_schema(output_schema_2["properties"]["ip"]) == "string"
        assert (
            get_type_from_schema(output_schema_2["properties"]["risk_score"])
            == "number"
        )
        assert (
            get_type_from_schema(output_schema_2["properties"]["base_score"])
            == "number"
        )

        # Analyze Script 3 using Script 2's output as input
        output_schema_3 = analyze_types(
            script_3,
            input_schema=output_schema_2,
            strict_input=True,
        )

        # Verify Script 3 output has correct types
        assert get_type_from_schema(output_schema_3["properties"]["ip"]) == "string"
        assert (
            get_type_from_schema(output_schema_3["properties"]["risk_score"])
            == "number"
        )
        assert (
            get_type_from_schema(output_schema_3["properties"]["classification"])
            == "string"
        )
        assert (
            get_type_from_schema(output_schema_3["properties"]["threat_description"])
            == "string"
        )

        # Success! All three scripts chain together with proper type validation


class TestWorkflowChainNegative:
    """Test workflow chain with type mismatches."""

    def test_script_2_expects_number_but_gets_string(self):
        """
        Negative case 1: Script 2 expects ip_length as number but gets string.
        Type checking should catch this mismatch.

        strict_input=True needed for type checking to catch mismatches.
        """
        # Modified Script 1 that incorrectly outputs ip_length as string
        script_1_bad = """
formatted = str(input.ip)
length = str(len(formatted))  # BUG: Converting to string

output = {
  "ip": input.ip,
  "ip_length": length,  # This is now string, not number!
  "formatted_ip": formatted
}
return output
"""

        # Script 2 expects ip_length to be number for arithmetic
        script_2 = """
ip_len = input.ip_length
base_score = ip_len * 2  # ERROR: Can't multiply string * number

output = {
  "ip": input.ip,
  "risk_score": base_score
}
return output
"""

        # Analyze Script 1 - should succeed
        input_schema_1 = {
            "type": "object",
            "properties": {"ip": {"type": "string"}},
            "required": ["ip"],
        }

        output_schema_1 = analyze_types(
            script_1_bad,
            input_schema=input_schema_1,
            strict_input=True,
        )

        # ip_length is now string (incorrect)
        assert output_schema_1["properties"]["ip_length"]["type"] == "string"

        # Analyze Script 2 with bad input - should raise TypeError
        # strict_input=True enables type checking on input fields
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                script_2,
                input_schema=output_schema_1,
                strict_input=True,
            )

        error_msg = str(exc_info.value)
        assert "multiply" in error_msg.lower() or "cannot" in error_msg.lower()

    def test_script_3_expects_number_but_gets_string(self):
        """
        Negative case 2: Script 3 expects risk_score as number but gets string.
        Comparison with number should fail type checking.

        strict_input=True needed for type checking.
        """
        # Modified Script 2 that incorrectly outputs risk_score as string
        script_2_bad = """
base_score = 50
risk_score = str(base_score)  # BUG: Converting to string

output = {
  "ip": input.ip,
  "risk_score": risk_score  # This is string, not number!
}
return output
"""

        # Script 3 expects risk_score to be number for comparison
        script_3 = """
score = input.risk_score

if (score > 30) {  # ERROR: Can't compare string > number
  classification = "HIGH"
} else {
  classification = "LOW"
}

output = {
  "classification": classification
}
return output
"""

        # Analyze Script 2
        input_schema_2 = {"type": "object", "properties": {"ip": {"type": "string"}}}

        output_schema_2 = analyze_types(
            script_2_bad,
            input_schema=input_schema_2,
            strict_input=True,
        )

        # risk_score is string (incorrect)
        assert output_schema_2["properties"]["risk_score"]["type"] == "string"

        # Analyze Script 3 with bad input - should raise TypeError
        # strict_input=True enables type checking
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                script_3,
                input_schema=output_schema_2,
                strict_input=True,
            )

        error_msg = str(exc_info.value)
        assert "compare" in error_msg.lower() or "cannot" in error_msg.lower()

    def test_arithmetic_on_string_field_caught(self):
        """
        Negative case 3: Script tries to do arithmetic on string field.
        Type checking should prevent this.

        strict_input=True needed for type checking.
        """
        script_bad = """
ip_str = input.ip  # This is a string
length = len(ip_str)  # This is number

result = ip_str * 2  # ERROR: Can't multiply string by number (repeats string)

output = {
  "result": result
}
return output
"""

        input_schema = {"type": "object", "properties": {"ip": {"type": "string"}}}

        # This should raise TypeError - string * number is not allowed in strict mode
        # strict_input=True enables type checking
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                script_bad,
                input_schema=input_schema,
                strict_input=True,
            )

        error_msg = str(exc_info.value)
        assert "multiply" in error_msg.lower() or "cannot" in error_msg.lower()

    def test_string_concatenation_without_conversion_caught(self):
        """
        Negative case 4: Script tries to concatenate number with string.
        Type checking should require explicit str() conversion.

        strict_input=True needed for type checking.
        """
        script_bad = """
score = input.risk_score  # This is a number
prefix = "Risk: "  # This is a string

message = prefix + score  # ERROR: Can't add string + number

output = {
  "message": message
}
return output
"""

        input_schema = {
            "type": "object",
            "properties": {"risk_score": {"type": "number"}},
        }

        # This should raise TypeError
        # strict_input=True enables type checking
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                script_bad,
                input_schema=input_schema,
                strict_input=True,
            )

        error_msg = str(exc_info.value)
        assert "add" in error_msg.lower() or "cannot" in error_msg.lower()

        # Show the correct way with str() conversion
        script_good = """
score = input.risk_score
prefix = "Risk: "

message = prefix + str(score)  # Correct: Explicit conversion

output = {
  "message": message
}
return output
"""

        output_schema = analyze_types(
            script_good,
            input_schema=input_schema,
            strict_input=True,
        )

        # Should succeed with correct type
        assert output_schema["properties"]["message"]["type"] == "string"


class TestWorkflowChainWithTools:
    """Test workflow chains that use native tools with type validation."""

    def test_tool_return_types_validated_in_chain(self):
        """
        Test that native tool return types are validated in workflow chains.
        This demonstrates the Bug #1 fix for tool return type validation.
        """
        # Script 1: Uses len() tool
        script_1 = """
items = input.items
count = len(items)  # len() returns number

output = {
  "item_count": count
}
return output
"""

        # Script 2: Uses count for calculation
        script_2 = """
count = input.item_count
multiplier = 10
total = count * multiplier  # Valid: number * number

output = {
  "total": total
}
return output
"""

        # Analyze chain
        input_schema_1 = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "string"}}},
        }

        output_schema_1 = analyze_types(
            script_1,
            input_schema=input_schema_1,
            strict_input=True,  # Use strict_input for workflow validation
        )

        # len() returns number, so item_count should be number
        assert output_schema_1["properties"]["item_count"]["type"] == "number"

        # Script 2 should succeed
        output_schema_2 = analyze_types(
            script_2,
            input_schema=output_schema_1,
            strict_input=True,  # Use strict_input for workflow validation
        )

        assert output_schema_2["properties"]["total"]["type"] == "number"

        # Success! Tool return types validated correctly in chain

    def test_tool_type_mismatch_caught_in_chain(self):
        """
        Test that tool type mismatches are caught in chains.
        Demonstrates type validation catching errors early.
        """
        # Script that tries to use len() result as string
        script_bad = """
items = input.items
count = len(items)  # Returns number

message = "Count: " + count  # ERROR: Can't add string + number

output = {
  "message": message
}
return output
"""

        input_schema = {
            "type": "object",
            "properties": {"items": {"type": "array", "items": {"type": "number"}}},
        }

        # Should raise TypeError
        with pytest.raises(TypeError) as exc_info:
            analyze_types(
                script_bad,
                input_schema=input_schema,
            )

        error_msg = str(exc_info.value)
        assert "add" in error_msg.lower() or "cannot" in error_msg.lower()
