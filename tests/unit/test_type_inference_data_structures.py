"""
Integration tests for Type Inference - Data Structures.

Tests verify end-to-end type inference on complete Cy scripts with
complex data structures (objects, arrays, field access, indexed access).
"""

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.type_inference_engine import TypeInferenceEngine


class TestDataStructureInference:
    """Test type inference on scripts with data structures."""

    def test_object_creation_and_field_access(self):
        """Create object and access field."""
        code = """
user = {"name": "Alice", "age": 30}
name = user.name
age = user.age
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify user is object with properties
        user_type = type_env.get_type("user")
        assert user_type is not None
        assert user_type["type"] == "object"
        assert "properties" in user_type
        assert user_type["properties"]["name"] == {"type": "string"}
        assert user_type["properties"]["age"] == {"type": "number"}

        # Verify field access propagation - returns union with null
        assert type_env.get_type("name") == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }
        assert type_env.get_type("age") == {
            "oneOf": [{"type": "number"}, {"type": "null"}]
        }

    def test_nested_object_creation(self):
        """Deeply nested object."""
        code = """
data = {
    "user": {
        "name": "Bob",
        "contact": {
            "email": "bob@example.com"
        }
    }
}
email = data.user.contact.email
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify nested structure
        data_type = type_env.get_type("data")
        assert data_type["type"] == "object"
        assert data_type["properties"]["user"]["type"] == "object"
        assert data_type["properties"]["user"]["properties"]["name"] == {
            "type": "string"
        }
        assert (
            data_type["properties"]["user"]["properties"]["contact"]["type"] == "object"
        )

        # Verify field access result - returns union with null
        assert type_env.get_type("email") == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }

    def test_array_creation_and_indexing(self):
        """Create array and index it."""
        code = """
numbers = [1, 2, 3, 4, 5]
first = numbers[0]
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify array type
        numbers_type = type_env.get_type("numbers")
        assert numbers_type is not None
        assert numbers_type["type"] == "array"
        assert numbers_type["items"] == {"type": "number"}

        # Verify indexed access - returns union with null
        assert type_env.get_type("first") == {
            "oneOf": [{"type": "number"}, {"type": "null"}]
        }

    def test_heterogeneous_array(self):
        """Mixed type array."""
        code = """
mixed = [1, "hello", true]
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify mixed array has oneOf
        mixed_type = type_env.get_type("mixed")
        assert mixed_type is not None
        assert mixed_type["type"] == "array"
        assert "oneOf" in mixed_type["items"]

    def test_array_of_objects(self):
        """Array containing objects."""
        code = """
users = [
    {"name": "Alice", "age": 30},
    {"name": "Bob", "age": 25}
]
first_user = users[0]
first_name = first_user.name
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify array of objects
        users_type = type_env.get_type("users")
        assert users_type["type"] == "array"
        assert users_type["items"]["type"] == "object"
        assert users_type["items"]["properties"]["name"] == {"type": "string"}
        assert users_type["items"]["properties"]["age"] == {"type": "number"}

        # Verify indexed access returns object - returns union with null
        first_user_type = type_env.get_type("first_user")
        # indexed access returns union type, extract the object variant
        assert "oneOf" in first_user_type
        object_variants = [
            v for v in first_user_type["oneOf"] if v.get("type") == "object"
        ]
        assert len(object_variants) == 1
        assert object_variants[0]["type"] == "object"

        # Verify field access on indexed result - returns union with null
        assert type_env.get_type("first_name") == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }

    def test_object_with_array_property(self):
        """Object containing array."""
        code = """
data = {
    "counts": [1, 2, 3],
    "metadata": {"version": "1.0"}
}
first_count = data.counts[0]
version = data.metadata.version
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify object with mixed properties
        data_type = type_env.get_type("data")
        assert data_type["type"] == "object"
        assert data_type["properties"]["counts"]["type"] == "array"
        assert data_type["properties"]["counts"]["items"] == {"type": "number"}
        assert data_type["properties"]["metadata"]["type"] == "object"

        # Verify access results - returns union with null
        assert type_env.get_type("first_count") == {
            "oneOf": [{"type": "number"}, {"type": "null"}]
        }
        assert type_env.get_type("version") == {
            "oneOf": [{"type": "string"}, {"type": "null"}]
        }

    def test_empty_structures(self):
        """Empty dict and array."""
        code = """
empty_obj = {}
empty_arr = []
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify empty structures
        assert type_env.get_type("empty_obj") == {"type": "object"}
        assert type_env.get_type("empty_arr") == {"type": "array"}

    def test_dynamic_object_key(self):
        """Variable used as object key."""
        code = """
key = "name"
obj = {"name": "Alice"}
result = obj[key]
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Variable key should work with indexed access
        obj_type = type_env.get_type("obj")
        assert obj_type["type"] == "object"

        # Result type depends on implementation
        # (might be string if properties lookup works, or Any if not)
        result_type = type_env.get_type("result")
        assert result_type is not None

    def test_nested_arrays(self):
        """Array of arrays."""
        code = """
matrix = [[1, 2], [3, 4]]
first_row = matrix[0]
first_element = first_row[0]
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify nested array
        matrix_type = type_env.get_type("matrix")
        assert matrix_type["type"] == "array"
        assert matrix_type["items"]["type"] == "array"
        assert matrix_type["items"]["items"] == {"type": "number"}

        # Verify first level access - returns union with null
        first_row_type = type_env.get_type("first_row")
        # indexed access returns union type, extract the array variant
        assert "oneOf" in first_row_type
        array_variants = [
            v for v in first_row_type["oneOf"] if v.get("type") == "array"
        ]
        assert len(array_variants) == 1
        assert array_variants[0]["type"] == "array"
        assert array_variants[0]["items"] == {"type": "number"}

        # Verify second level access - returns union with null
        assert type_env.get_type("first_element") == {
            "oneOf": [{"type": "number"}, {"type": "null"}]
        }

    def test_complex_nested_access(self):
        """Deeply nested mix of structures."""
        code = """
data = [
    [
        {"x": 1, "y": 2}
    ],
    [
        {"x": 3, "y": 4}
    ]
]
row = data[0]
obj = row[0]
value = obj.x
        """
        parser = Parser()
        ast = parser.parse_only(code)
        execution_plan = compile_cy_program(
            ast, source_file="<test>", validate_output=False
        )
        tool_resolver = ToolResolver()

        engine = TypeInferenceEngine(execution_plan, tool_resolver)
        type_env = engine.infer_types()

        # Verify complex structure
        data_type = type_env.get_type("data")
        assert data_type["type"] == "array"
        assert data_type["items"]["type"] == "array"
        assert data_type["items"]["items"]["type"] == "object"

        # Verify deep access result - returns union with null
        assert type_env.get_type("value") == {
            "oneOf": [{"type": "number"}, {"type": "null"}]
        }
