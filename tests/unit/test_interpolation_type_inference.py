"""
Unit tests for string interpolation type inference.

Tests verify that analyze_types() correctly handles InterpolationNode
and infers string types for interpolated strings.
"""

import pytest

from cy_language import analyze_types


class TestInterpolationBasics:
    """Test basic string interpolation type inference."""

    def test_simple_interpolation(self):
        """Test simple variable interpolation."""
        script = """
        name = "Alice"
        greeting = "Hello ${name}"
        return greeting
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_number(self):
        """Test interpolation with number variable."""
        script = """
        age = 30
        message = "Age is ${age}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_multiple_interpolations(self):
        """Test multiple variables in one string."""
        script = """
        first = "Alice"
        last = "Smith"
        full_name = "${first} ${last}"
        return full_name
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_expression(self):
        """Test interpolation with arithmetic expression."""
        script = """
        a = 5
        b = 10
        result = "Sum is ${a + b}"
        return result
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_nested_object_interpolation(self):
        """Test interpolation with object field access."""
        script = """
        user = {"name": "Alice", "age": 30}
        info = "User ${user.name} is ${user.age} years old"
        return info
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_in_object(self):
        """Test interpolation used in object property."""
        script = """
        name = "Alice"
        user = {
            "greeting": "Hello ${name}",
            "message": "Welcome"
        }
        return user
        """

        result = analyze_types(script)
        assert result["type"] == "object"
        assert "properties" in result
        assert result["properties"]["greeting"]["type"] == "string"

    def test_interpolation_in_list(self):
        """Test interpolation used in list elements."""
        script = """
        name = "Alice"
        messages = [
            "Hello ${name}",
            "Welcome ${name}",
            "Goodbye ${name}"
        ]
        return messages
        """

        result = analyze_types(script)
        assert result["type"] == "array"
        assert result["items"]["type"] == "string"


class TestInterpolationWithInputSchema:
    """Test interpolation with input schema."""

    def test_interpolation_with_input_field(self):
        """Test interpolation using input fields."""
        script = """
        ip = input["ip_address"]
        message = "Analyzing IP: ${ip}"
        return message
        """

        input_schema = {
            "type": "object",
            "properties": {"ip_address": {"type": "string"}},
        }

        result = analyze_types(script, input_schema=input_schema)
        assert result == {"type": "string"}

    def test_interpolation_with_multiple_input_fields(self):
        """Test interpolation with multiple input fields."""
        script = """
        ip = input["ip"]
        context = input["context"]
        prompt = "Analyze IP ${ip} in context: ${context}"
        return prompt
        """

        input_schema = {
            "type": "object",
            "properties": {"ip": {"type": "string"}, "context": {"type": "string"}},
        }

        result = analyze_types(script, input_schema=input_schema)
        assert result == {"type": "string"}

    def test_interpolation_in_workflow_composition(self):
        """Test interpolation in workflow composition scenario."""
        script = """
        ip = input["ip_address"]
        score = input["reputation_score"]

        summary = "IP ${ip} has reputation score ${score}"

        return {
            "ip": ip,
            "score": score,
            "summary": summary
        }
        """

        input_schema = {
            "type": "object",
            "properties": {
                "ip_address": {"type": "string"},
                "reputation_score": {"type": "number"},
            },
        }

        result = analyze_types(script, input_schema=input_schema)
        assert result["type"] == "object"
        assert result["properties"]["summary"]["type"] == "string"


class TestInterpolationTypeValidation:
    """Test type validation with interpolation (when check_types is enabled)."""

    def test_interpolation_with_undefined_variable(self):
        """Test interpolation with undefined variable.

        Undefined variables in interpolation are now caught at compile time
        when check_types=True, which is the correct behavior.
        """
        script = """
        greeting = "Hello ${undefined_var}"
        return greeting
        """

        # Undefined variable is caught at compile time
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script)
        assert "undefined_var" in str(exc_info.value).lower()

    def test_interpolation_with_tool_call(self):
        """Test interpolation with tool call result."""
        script = """
        x = 5
        length = len([1, 2, 3])
        message = "X is ${x}, length is ${length}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}


class TestInterpolationComplexCases:
    """Test complex interpolation scenarios."""

    def test_multiline_string_interpolation(self):
        """Test interpolation in multiline strings."""
        script = '''
        name = "Alice"
        age = 30
        bio = """
Name: ${name}
Age: ${age}
Status: Active
"""
        return bio
        '''

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_nested_interpolations_in_conditionals(self):
        """Test interpolation inside conditional branches."""
        script = """
        score = 85
        if (score > 80) {
            message = "High score: ${score}"
        } else {
            message = "Low score: ${score}"
        }
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_function_call(self):
        """Test interpolation with function call result."""
        script = """
        text = "hello world"
        upper = str(text)
        message = "Uppercase: ${upper}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_output_in_workflow(self):
        """Test real-world workflow pattern: LLM prompt construction."""
        script = '''
        ip_address = input["ip"]
        context = input["context"]
        previous_findings = input["findings"]

        # Construct LLM prompt using interpolation
        llm_prompt = """
Analyze the following IP address:
IP: ${ip_address}
Context: ${context}
Previous Findings: ${previous_findings}

Provide a security assessment.
"""

        return {
            "ip": ip_address,
            "prompt": llm_prompt
        }
        '''

        input_schema = {
            "type": "object",
            "properties": {
                "ip": {"type": "string"},
                "context": {"type": "string"},
                "findings": {"type": "string"},
            },
        }

        result = analyze_types(script, input_schema=input_schema)
        assert result["type"] == "object"
        assert result["properties"]["prompt"]["type"] == "string"


class TestInterpolationEdgeCases:
    """Test edge cases for interpolation."""

    def test_empty_interpolation(self):
        """Test interpolation with empty expressions (edge case)."""
        script = """
        text = "plain text"
        return text
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_null(self):
        """Test interpolation with null values."""
        script = """
        value = null
        message = "Value: ${value}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_boolean(self):
        """Test interpolation with boolean values."""
        script = """
        flag = true
        message = "Flag is ${flag}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}

    def test_interpolation_with_list_element(self):
        """Test interpolation with list indexing."""
        script = """
        items = ["apple", "banana", "cherry"]
        first = items[0]
        message = "First item is ${first}"
        return message
        """

        result = analyze_types(script)
        assert result == {"type": "string"}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
