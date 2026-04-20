"""Tests for union type inference in traditional if/else statements.

This tests that when a variable is assigned different types in different
branches of an if/else statement, the variable gets a union type.
"""

import pytest

from cy_language import analyze_types
from cy_language.compiler import PlanCompiler
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_inference_engine import TypeInferenceEngine


class TestConditionalStatementUnionTypes:
    """Test union type creation for variables assigned in if/else branches."""

    def setup_method(self):
        """Setup test fixtures."""
        self.parser = Parser()
        self.tool_resolver = ToolResolver()
        self.compiler = PlanCompiler(tool_resolver=self.tool_resolver)

    def test_simple_if_else_different_types(self):
        """Variable assigned different types in if/else gets union type."""
        code = """
x = 0
if (True) {
    x = 1
} else {
    x = "a"
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_if_else_same_type_no_union(self):
        """Variable assigned same type in both branches stays that type."""
        code = """
x = 0
if (True) {
    x = 1
} else {
    x = 2
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert x_type == {"type": "number"}

    def test_elif_branches_create_union(self):
        """Multiple elif branches with different types create union."""
        code = """
score = 75
grade = "F"
if (score >= 90) {
    grade = "A"
} elif (score >= 80) {
    grade = "B"
} elif (score >= 70) {
    grade = 100
} else {
    grade = "F"
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        grade_type = type_env.get_type("grade")
        assert "oneOf" in grade_type
        types_in_union = [t.get("type") for t in grade_type["oneOf"]]
        assert "string" in types_in_union
        assert "number" in types_in_union

    def test_variable_not_in_conditional_unchanged(self):
        """Variables not assigned in conditional keep original type."""
        code = """
x = 10
y = "hello"
if (True) {
    x = 20
} else {
    x = 30
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert x_type == {"type": "number"}

        y_type = type_env.get_type("y")
        assert y_type == {"type": "string"}

    def test_variable_assigned_only_in_some_branches(self):
        """Variable assigned in some branches gets union with initial type."""
        code = """
x = 10
if (True) {
    x = "changed"
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        # x could be number (initial) or string (from if branch)
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union

    def test_nested_conditionals_union_types(self):
        """Nested conditionals correctly merge types."""
        code = """
x = 0
if (True) {
    if (True) {
        x = "nested"
    } else {
        x = 42
    }
} else {
    x = False
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "string" in types_in_union
        assert "number" in types_in_union
        assert "boolean" in types_in_union

    def test_multiple_variables_in_branches(self):
        """Multiple variables assigned in branches get correct types."""
        code = """
a = 1
b = "x"
if (True) {
    a = "changed"
    b = 100
} else {
    a = 2
    b = "y"
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        a_type = type_env.get_type("a")
        assert "oneOf" in a_type
        a_types = [t.get("type") for t in a_type["oneOf"]]
        assert "string" in a_types
        assert "number" in a_types

        b_type = type_env.get_type("b")
        assert "oneOf" in b_type
        b_types = [t.get("type") for t in b_type["oneOf"]]
        assert "string" in b_types
        assert "number" in b_types

    def test_union_with_boolean(self):
        """Union types work with boolean values."""
        code = """
x = True
if (True) {
    x = 42
} else {
    x = False
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "boolean" in types_in_union
        assert "number" in types_in_union

    def test_union_with_arrays(self):
        """Union types work with array types."""
        code = """
x = [1, 2, 3]
if (True) {
    x = "text"
} else {
    x = [4, 5, 6]
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert "oneOf" in x_type
        # Should contain array and string types
        has_string = any(t.get("type") == "string" for t in x_type["oneOf"])
        has_array = any(t.get("type") == "array" for t in x_type["oneOf"])
        assert has_string
        assert has_array

    def test_union_with_objects(self):
        """Union types work with object types."""
        code = """
x = {"a": 1}
if (True) {
    x = {"b": "text"}
} else {
    x = {"a": 2}
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        # Different object structures create union
        assert "oneOf" in x_type

    def test_three_way_union(self):
        """Union type with three different types."""
        code = """
x = 1
if (True) {
    x = "string"
} elif (True) {
    x = False
} else {
    x = 42
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "string" in types_in_union
        assert "boolean" in types_in_union
        assert "number" in types_in_union
        assert len(x_type["oneOf"]) == 3

    def test_no_else_branch_creates_union(self):
        """If without else creates union with initial type."""
        code = """
x = 10
if (True) {
    x = "changed"
}
output = "done"
"""
        ast = self.parser.parse_only(code)
        plan = self.compiler.compile(ast)
        engine = TypeInferenceEngine(plan, self.tool_resolver)
        type_env = engine.infer_types()

        x_type = type_env.get_type("x")
        # Could be number (initial/no branch taken) or string (if taken)
        assert "oneOf" in x_type
        types_in_union = [t.get("type") for t in x_type["oneOf"]]
        assert "number" in types_in_union
        assert "string" in types_in_union


class TestIfElseSameBaseTypeMerge:
    """Test that when both if/else branches assign the same base type,
    the variable is recognized as that type by tool call type checking.

    Regression: When both branches assign objects with different property
    schemas, the merged type is oneOf[obj_a, obj_b]. The tool call validator
    must recognize this union as compatible with an expected "object" type.
    """

    def test_if_else_both_assign_object_compatible_with_object_param(self):
        """Both branches assign object type → variable compatible with object parameter."""
        script = """
condition = True
if (condition) {
    x = {"a": 1}
} else {
    x = {"b": 2}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        # Should NOT raise TypeError: both branches assign object,
        # so x is an object-union and is compatible with "object" param.
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    def test_if_else_both_assign_string_compatible_with_string_param(self):
        """Both branches assign string type → variable compatible with string parameter."""
        script = """
condition = True
if (condition) {
    msg = "hello"
} else {
    msg = "world"
}
result = my_tool(text=msg)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"text": {"type": "string"}},
                "return_type": {"type": "number"},
            }
        }
        # Both branches assign string, so msg is string — should pass
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "number"}

    def test_if_else_mixed_types_still_errors_for_wrong_param(self):
        """When branches assign different base types, passing to typed param still errors."""
        script = """
condition = True
if (condition) {
    x = {"a": 1}
} else {
    x = "a string"
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        # x could be object OR string, string is not compatible with object param
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=tool_registry)
        assert "data" in str(exc_info.value)

    def test_if_else_three_branches_same_base_type(self):
        """Three branches (if/elif/else) all assign object → compatible with object param."""
        script = """
condition = True
if (condition) {
    x = {"a": 1}
} elif (condition) {
    x = {"b": 2}
} else {
    x = {"c": 3}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        # All three branches assign object → should pass
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}


class TestIfElseNestedBranchTypeMerge:
    """Nested corner cases for if/else type merging.

    When nested if/else blocks all assign the same base type across every
    reachable leaf, the variable must still be recognized as that type by
    tool call type checking — even though the merged schema is a deeper
    oneOf nesting produced by recursive branch merging.
    """

    # ------------------------------------------------------------------ #
    # Nested if — all leaves same base type                               #
    # ------------------------------------------------------------------ #

    def test_nested_inner_if_else_both_object_outer_else_object(self):
        """Inner if/else both assign object; outer else also object → all object."""
        script = """
a = True
b = True
if (a) {
    if (b) {
        x = {"inner_if": 1}
    } else {
        x = {"inner_else": 2}
    }
} else {
    x = {"outer_else": 3}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    def test_nested_both_branches_contain_inner_if_else_all_object(self):
        """Both outer branches have their own nested if/else, all assign object."""
        script = """
a = True
b = True
if (a) {
    if (b) {
        x = {"path_aa": 1}
    } else {
        x = {"path_ab": 2}
    }
} else {
    if (b) {
        x = {"path_ba": 3}
    } else {
        x = {"path_bb": 4}
    }
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    def test_three_level_nesting_all_object_leaves(self):
        """Three levels of if/else, every leaf assigns object → compatible."""
        script = """
a = True
b = True
c = True
if (a) {
    if (b) {
        if (c) {
            x = {"deep_aaa": 1}
        } else {
            x = {"deep_aab": 2}
        }
    } else {
        x = {"mid_ab": 3}
    }
} else {
    x = {"top_b": 4}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    # ------------------------------------------------------------------ #
    # One leaf wrong type — must still raise                              #
    # ------------------------------------------------------------------ #

    def test_nested_one_leaf_wrong_type_still_errors(self):
        """Deep nesting where one leaf assigns a string → should still error."""
        script = """
a = True
b = True
if (a) {
    if (b) {
        x = {"ok": 1}
    } else {
        x = "wrong_type"
    }
} else {
    x = {"also_ok": 2}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        with pytest.raises(TypeError) as exc_info:
            analyze_types(script, tool_registry=tool_registry)
        assert "data" in str(exc_info.value)

    # ------------------------------------------------------------------ #
    # Asymmetric nesting — one flat branch, one nested branch             #
    # ------------------------------------------------------------------ #

    def test_flat_branch_vs_nested_branch_all_same_type(self):
        """One branch assigns directly, other has nested if/else — all object."""
        script = """
a = True
b = True
if (a) {
    x = {"flat": 1}
} else {
    if (b) {
        x = {"nested_if": 2}
    } else {
        x = {"nested_else": 3}
    }
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    # ------------------------------------------------------------------ #
    # Nested inside try/catch                                             #
    # ------------------------------------------------------------------ #

    def test_if_else_both_object_inside_try_block(self):
        """If/else inside try assigns object in both branches → compatible."""
        script = """
condition = True
try {
    if (condition) {
        x = {"try_if": 1}
    } else {
        x = {"try_else": 2}
    }
} catch (err) {
    x = {"catch_default": 0}
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}

    # ------------------------------------------------------------------ #
    # Multiple variables — only the one passed to the tool matters        #
    # ------------------------------------------------------------------ #

    def test_two_variables_nested_branches_one_passed_to_tool(self):
        """Two variables both assigned in nested branches; only one passed to tool."""
        script = """
a = True
b = True
if (a) {
    if (b) {
        x = {"x_inner_if": 1}
        y = "yes"
    } else {
        x = {"x_inner_else": 2}
        y = "no"
    }
} else {
    x = {"x_outer_else": 3}
    y = "maybe"
}
result = my_tool(data=x)
return result
"""
        tool_registry = {
            "my_tool": {
                "parameters": {"data": {"type": "object"}},
                "return_type": {"type": "string"},
            }
        }
        # x is always object across all paths; y is always string (not passed to tool)
        output = analyze_types(script, tool_registry=tool_registry)
        assert output == {"type": "string"}
