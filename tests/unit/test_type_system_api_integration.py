"""Integration tests for Clean Slate Type System API Redesign.

Tests verify end-to-end workflows with the new analyze_types() API and
Cy(check_types=True) integration.

Following TDD: All tests should FAIL initially.
"""

import contextlib

import pytest

from cy_language import Cy, analyze_types, data_to_schema


class TestCyRunWithCheckTypes:
    """Test Cy.run() with check_types=True integration."""

    def test_cy_run_check_types_true_valid_code(self):
        """Test that Cy(check_types=True).run() executes valid code."""
        code = """
name = (input.name ?? "")
return "Hello " + name
"""
        input_data = {"name": "Alice"}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"Hello Alice"'

    def test_cy_run_check_types_true_invalid_code(self):
        """Test that Cy(check_types=True).run() raises error on invalid code.

        Nullable types require explicit handling with ??
        """
        code = """
result = input.age + input.name
return result
"""
        input_data = {"age": 30, "name": "Alice"}

        cy = Cy(check_types=True)

        # Operations on nullable types require ?? operator
        with pytest.raises(TypeError) as exc:
            cy.run(code, input_data=input_data)
        assert "nullable" in str(exc.value).lower()

    def test_cy_run_check_types_false_skips_validation(self):
        """Test that Cy(check_types=False).run() skips validation."""
        code = """
x = 5
y = "text"
result = x + y
return result
"""

        cy = Cy(check_types=False)  # Default behavior

        # Should not raise TypeError during compilation
        # May fail at runtime, but that's different
        from cy_language.errors import RuntimeError as CyRuntimeError

        with contextlib.suppress(CyRuntimeError):
            cy.run(code, input_data=None)

    def test_cy_run_auto_derives_input_schema(self):
        """Test that input_schema is automatically derived from input_data."""
        code = """
name = (input.name ?? "")
age = (input.age ?? 0)
return "Name: " + name + ", Age: " + str(age)
"""
        input_data = {"name": "Bob", "age": 25}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        # Should execute successfully with auto-derived schema
        assert "Name: Bob" in result  # JSON string includes the content
        assert "Age: 25" in result

    @pytest.mark.asyncio
    async def test_cy_run_async_check_types_true(self):
        """Test async version: Cy(check_types=True).run_async()."""
        code = """
name = (input.name ?? "")
return "Hello " + name
"""
        input_data = {"name": "Charlie"}

        cy = await Cy.create_async(check_types=True)
        result = await cy.run_async(code, input_data=input_data)

        assert result == '"Hello Charlie"'

    @pytest.mark.asyncio
    async def test_cy_run_async_invalid_code(self):
        """Test async version with invalid code raises error.

        Operations on nullable types require explicit handling.
        """
        code = """
result = input.name + input.age
return result
"""
        input_data = {"name": "Alice", "age": 30}

        cy = await Cy.create_async(check_types=True)

        # Operations on nullable types require ?? operator
        with pytest.raises(TypeError) as exc:
            await cy.run_async(code, input_data=input_data)
        assert "nullable" in str(exc.value).lower()


class TestAutoSchemaDerivation:
    """Test auto-derivation of input schemas from data."""

    def test_auto_derive_simple_object(self):
        """Input data: simple object with name and age."""
        code = """
name = (input.name ?? "")
age = (input.age ?? 0)
return name + " is " + str(age)
"""
        input_data = {"name": "Alice", "age": 30}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"Alice is 30"'

    def test_auto_derive_nested_object(self):
        """Input data: nested object structure."""
        code = """
name = (input.user.name ?? "")
return "User: " + name
"""
        input_data = {"user": {"name": "Bob", "roles": ["admin"]}}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"User: Bob"'

    def test_auto_derive_array(self):
        """Input data: array of numbers."""
        code = """
items = (input.items ?? [])
first = (items[0] ?? 0)
return first
"""
        input_data = {"items": [1, 2, 3]}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == "1"

    def test_auto_derive_with_none_input_data(self):
        """Input data: None (no input provided)."""
        code = """
x = 5
return x + 10
"""

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=None)

        assert result == "15"


class TestWorkflows:
    """Test complete workflows with type checking."""

    def test_development_workflow(self):
        """Simulate dev workflow: check types, then run.

        Use strict_input=True to ensure type inference works correctly
        with input schema. Otherwise field access returns Any | null unions.
        """
        code = """
name = input.name
age = input.age
return "Name: " + name + ", Age: " + str(age)
"""
        sample_input = {"name": "Alice", "age": 30}

        # Step 1: Check types explicitly with strict_input
        input_schema = data_to_schema(sample_input)
        # strict_input=True needed for precise type inference
        output_schema = analyze_types(code, input_schema, strict_input=True)
        assert output_schema == {"type": "string"}

        # Step 2: Run in production without type checking (faster)
        cy = Cy(check_types=False)
        result = cy.run(code, input_data=sample_input)
        assert "Name: Alice" in result  # JSON string includes the content

    def test_production_workflow(self):
        """Simulate production: skip type checking for performance."""
        code = """
return "Result: " + str((input.value ?? 0) * 2)
"""
        input_data = {"value": 21}

        cy = Cy(check_types=False)
        result = cy.run(code, input_data=input_data)

        assert result == '"Result: 42"'

    def test_safety_first_workflow(self):
        """Simulate safety-first: always validate.

        Operations on nullable types require explicit handling.
        """
        code = """
return "Hello " + (input.name ?? "")
"""
        input_data = {"name": "Alice"}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"Hello Alice"'

        # Try invalid code
        invalid_code = """
return input.name + input.age
"""
        invalid_data = {"name": "Bob", "age": 25}

        # Operations on nullable types require ?? operator
        with pytest.raises(TypeError) as exc:
            cy.run(invalid_code, input_data=invalid_data)
        assert "nullable" in str(exc.value).lower()


class TestMixedScenarios:
    """Test mixed scenarios and edge cases."""

    def test_valid_code_with_complex_input(self):
        """Complex input schema with nested objects and arrays."""
        code = """
users = (input.users ?? [])
first_user = (users[0] ?? {})
name = (first_user.name ?? "")
return "First user: " + name
"""
        input_data = {
            "users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        }

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"First user: Alice"'

    def test_multiple_executions_same_interpreter(self):
        """Create one Cy(check_types=True) instance, run multiple scripts.

        With nullable field access, must use ?? for operations.
        """
        cy = Cy(check_types=True)

        # First execution
        result1 = cy.run("return (input.x ?? 0) + 5", input_data={"x": 10})
        assert result1 == "15"

        # Second execution with different input
        result2 = cy.run('return (input.name ?? "")', input_data={"name": "Test"})
        assert result2 == '"Test"'

        # Third execution with type error
        # Operations on nullable types require ?? operator
        with pytest.raises(TypeError) as exc:
            cy.run("return input.a + input.b", input_data={"a": 5, "b": "text"})
        assert "nullable" in str(exc.value).lower()

    def test_type_checking_with_conditionals(self):
        """Type checking with conditional branches."""
        code = """
if ((input.value ?? 0) > 10) {
    result = "high"
} else {
    result = "low"
}
return result
"""
        input_data = {"value": 15}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == '"high"'

    def test_type_checking_with_loops(self):
        """Type checking with loops."""
        code = """
items = (input.items ?? [])
total = 0
for (item in items) {
    total = total + (item ?? 0)
}
return total
"""
        input_data = {"items": [1, 2, 3, 4, 5]}

        cy = Cy(check_types=True)
        result = cy.run(code, input_data=input_data)

        assert result == "15"
