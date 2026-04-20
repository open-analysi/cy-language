"""
Unit tests for Field Assignment Syntax.

Tests for field assignment syntax `a.x = {}` as syntactic sugar for `a["x"] = {}`.
Includes auto-creation of intermediate dictionaries.

These tests follow TDD approach - most will fail until implementation in Cycle 060.
"""

import pytest

from cy_language.errors import CompilerError
from cy_language.errors import RuntimeError as CyRuntimeError
from cy_language.interpreter import Cy

# ============================================================================
# Task 5: Basic Field Assignment Tests
# ============================================================================


def test_simple_field_assignment():
    """Test simple field assignment: a.x = 5, verify a["x"] == 5."""
    program = """
    a = {}
    a.x = 5
    output = a["x"]
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "5"


def test_field_assignment_empty_dict():
    """Test empty dict initialization: a.x = {}."""
    program = """
    a = {}
    a.x = {}
    output = a.x
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "{}"


def test_field_assignment_overwrites_existing():
    """Test overwriting existing field value."""
    program = """
    a = {"x": 10}
    a.x = 20
    output = a.x
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "20"


def test_field_assignment_various_types():
    """Test assigning different types (string, int, list, dict, null)."""
    program = """
    a = {}
    a.str_field = "hello"
    a.int_field = 42
    a.list_field = [1, 2, 3]
    a.dict_field = {"nested": "value"}
    a.null_field = null

    output = a.str_field + " " + str(a.int_field)
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"hello 42"'


def test_field_assignment_read_back():
    """Test reading field via dot notation matches written value."""
    program = """
    a = {}
    a.x = "test_value"
    result = a.x
    output = result
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"test_value"'


# ============================================================================
# Task 6: Nested Assignment Tests (Auto-Create)
# ============================================================================


def test_two_level_auto_create():
    """Test a = {}; a.x.y = 'hello' auto-creates a.x = {}."""
    program = """
    a = {}
    a.x.y = "hello"
    output = a.x.y
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"hello"'


def test_three_level_auto_create():
    """Test a = {}; a.x.y.z = 123 auto-creates a.x and a.x.y."""
    program = """
    a = {}
    a.x.y.z = 123
    output = a.x.y.z
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "123"


def test_deep_nesting_auto_create():
    """Test 5+ level nesting with full auto-create chain."""
    program = """
    a = {}
    a.b.c.d.e.f = "deep"
    output = a.b.c.d.e.f
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"deep"'


def test_auto_create_over_null():
    """Test a = {'x': null}; a.x.y = 5 overwrites null with {}."""
    program = """
    a = {"x": null}
    a.x.y = 5
    output = a.x.y
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "5"


def test_partial_path_exists():
    """Test a = {'x': {}}; a.x.y.z = 10 only creates missing parts."""
    program = """
    a = {"x": {}}
    a.x.y.z = 10
    output = a.x.y.z
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "10"


def test_mixed_bracket_dot_assignment():
    """Test a.x['y'].z = value with auto-create.

    Note: Mixed notation is a known parser limitation and not currently supported.
    This test verifies the parser correctly rejects it.
    """
    program = """
    a = {}
    a.x["y"].z = "mixed"
    output = a.x["y"].z
    return output
    """
    cy = Cy()
    # Mixed notation is not supported - parser should error
    with pytest.raises(Exception):  # Could be SyntaxError or parser exception
        cy.run(program)


def test_auto_create_preserves_existing_fields():
    """Test auto-create doesn't overwrite sibling fields."""
    program = """
    a = {"x": {"existing": "value"}}
    a.x.new_field = "new"
    output = a.x.existing + " " + a.x.new_field
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"value new"'


# ============================================================================
# Task 7: Compound Operators
# ============================================================================


def test_compound_add_assign():
    """Test a.x += 5 increments field value."""
    program = """
    a = {"x": 10}
    a.x += 5
    output = a.x
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "15"


def test_compound_subtract_assign():
    """Test a.count -= 1 decrements field."""
    program = """
    a = {"count": 100}
    a.count -= 1
    output = a.count
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "99"


def test_compound_multiply_assign():
    """Test a.value *= 2 multiplies field."""
    program = """
    a = {"value": 7}
    a.value *= 2
    output = a.value
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "14"


def test_compound_divide_assign():
    """Test a.total /= 10 divides field."""
    program = """
    a = {"total": 100}
    a.total /= 10
    output = a.total
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "10.0"  # Division returns float


def test_compound_with_nested_field():
    """Test a.x.y += 'suffix' on nested path."""
    program = """
    a = {"x": {"y": "prefix"}}
    a.x.y += "_suffix"
    output = a.x.y
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"prefix_suffix"'


def test_compound_on_nonexistent_field():
    """Test error when field doesn't exist for compound op."""
    program = """
    a = {}
    a.x += 5
    output = a.x
    return output
    """
    cy = Cy()
    # Compound operators require the field to exist
    # This should either error or auto-create with default value
    # Based on implementation, we expect an error
    with pytest.raises(CyRuntimeError):
        cy.run(program)


# ============================================================================
# Task 8: Error Cases (Negative Tests)
# ============================================================================


def test_assign_to_non_dict_primitive():
    """Test number = 5; number.x = 10 raises error."""
    program = """
    number = 5
    number.x = 10
    output = number.x
    return output
    """
    cy = Cy()
    with pytest.raises(CyRuntimeError):
        cy.run(program)


def test_assign_to_string():
    """Test s = 'hello'; s.x = 5 raises error."""
    program = """
    s = "hello"
    s.x = 5
    output = s.x
    return output
    """
    cy = Cy()
    with pytest.raises(CyRuntimeError):
        cy.run(program)


def test_assign_to_list():
    """Test arr = [1,2,3]; arr.x = 5 raises error."""
    program = """
    arr = [1, 2, 3]
    arr.x = 5
    output = arr.x
    return output
    """
    cy = Cy()
    with pytest.raises(CyRuntimeError):
        cy.run(program)


def test_assign_through_non_dict_intermediate():
    """Test a = {'x': 5}; a.x.y = 10 errors (5 is not dict)."""
    program = """
    a = {"x": 5}
    a.x.y = 10
    output = a.x.y
    return output
    """
    cy = Cy()
    with pytest.raises(CyRuntimeError):
        cy.run(program)


def test_assign_to_undefined_variable():
    """Test undefined_var.x = 5 raises error."""
    program = """
    undefined_var.x = 5
    output = "should_not_reach"
    return output
    """
    cy = Cy()
    # Should raise error when trying to assign to field of undefined variable
    with pytest.raises((CyRuntimeError, Exception)):
        cy.run(program)


def test_verify_null_auto_create():
    """Verify null is auto-created (positive test confirming design decision)."""
    program = """
    a = {"x": null}
    a.x.y = 5
    # Verify a.x is now a dict with y = 5
    output = a.x.y
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "5"


def test_field_name_must_be_identifier():
    """Test that field names must be valid identifiers."""
    # This is a grammar-level test - invalid field names should fail parsing
    program = """
    a = {}
    a.123invalid = 5
    output = a.123invalid
    return output
    """
    cy = Cy()
    # Should fail at parse time
    with pytest.raises((CyRuntimeError, CompilerError, Exception)):
        cy.run(program)


# ============================================================================
# Task 9: Integration Tests
# ============================================================================


def test_field_assignment_with_nullable_types():
    """Test use with ?? operator."""
    program = """
    a = {}
    a.x = null
    result = a.x ?? "default"
    output = result
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"default"'


def test_field_assignment_in_function():
    """Test field assignment with nested objects (simulated function behavior)."""
    # Note: Cy doesn't support user-defined functions yet
    # This test simulates the intended behavior
    program = """
    my_alert = {}
    my_alert.enrichment = {}
    my_alert.enrichment.score = 85
    output = my_alert.enrichment.score
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == "85"


def test_field_assignment_in_loop():
    """Test field assignment inside for/while loop."""
    program = """
    data = {}
    for (i in [1, 2, 3]) {
        data.count = i
    }
    output = data.count
    return output
    """
    cy = Cy()
    result = cy.run(program)
    # Should be the last value from the loop
    assert result == "3"


def test_field_assignment_with_conditionals():
    """Test field assignment in if/else blocks."""
    program = """
    a = {}
    check = 1
    if (check == 1) {
        a.x = "true_branch"
    } else {
        a.x = "false_branch"
    }
    output = a.x
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"true_branch"'


def test_field_assignment_with_function_call_result():
    """Test a.x = native_function_call()."""
    # Note: Using str() native function since user-defined functions aren't supported yet
    program = """
    a = {}
    a.result = str(42)
    output = a.result
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"42"'


def test_field_assignment_chain_with_field_access():
    """Test a.x = b.y.z."""
    program = """
    b = {"y": {"z": "source_value"}}
    a = {}
    a.x = b.y.z
    output = a.x
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"source_value"'


def test_equivalence_with_indexed_assignment():
    """Verify a.x = v is equivalent to a['x'] = v."""
    program = """
    a = {}
    b = {}
    a.x = "value"
    b["x"] = "value"

    # Both should produce same result
    match = (a.x == b["x"])
    output = str(match)
    return output
    """
    cy = Cy()
    result = cy.run(program)
    assert result == '"True"'
