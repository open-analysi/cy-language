"""
Unit tests for Type System.

Tests verify that CyType classes correctly represent types and
serialize to/from JSON Schema format.
"""

import pytest

from cy_language.type_system import (
    AnyType,
    ArrayType,
    CyType,
    ObjectType,
    PrimitiveType,
    UnionType,
)


class TestPrimitiveType:
    """Test PrimitiveType class."""

    def test_primitive_type_number_to_json_schema(self):
        """Verify PrimitiveType('number') serializes to {'type': 'number'}."""
        ptype = PrimitiveType("number")
        schema = ptype.to_json_schema()
        assert schema == {"type": "number"}

    def test_primitive_type_string_to_json_schema(self):
        """Verify PrimitiveType('string') serializes to {'type': 'string'}."""
        ptype = PrimitiveType("string")
        schema = ptype.to_json_schema()
        assert schema == {"type": "string"}

    def test_primitive_type_boolean_to_json_schema(self):
        """Verify PrimitiveType('boolean') serializes to {'type': 'boolean'}."""
        ptype = PrimitiveType("boolean")
        schema = ptype.to_json_schema()
        assert schema == {"type": "boolean"}

    def test_primitive_type_null_to_json_schema(self):
        """Verify PrimitiveType('null') serializes to {'type': 'null'}."""
        ptype = PrimitiveType("null")
        schema = ptype.to_json_schema()
        assert schema == {"type": "null"}

    def test_primitive_type_invalid_type_name(self):
        """Verify error when creating PrimitiveType with invalid type."""
        with pytest.raises((ValueError, NotImplementedError)):
            ptype = PrimitiveType("invalid_type")
            # If constructor doesn't validate, serialization should fail
            ptype.to_json_schema()


class TestObjectType:
    """Test ObjectType class."""

    def test_object_type_simple_properties(self):
        """Verify ObjectType with simple properties serializes correctly."""
        obj_type = ObjectType(
            properties={
                "name": PrimitiveType("string"),
                "age": PrimitiveType("number"),
            },
            required=["name", "age"],
        )
        schema = obj_type.to_json_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["name"] == {"type": "string"}
        assert schema["properties"]["age"] == {"type": "number"}
        assert set(schema["required"]) == {"name", "age"}

    def test_object_type_nested_properties(self):
        """Verify ObjectType with nested objects serializes correctly."""
        nested_obj = ObjectType(
            properties={"city": PrimitiveType("string")}, required=["city"]
        )
        obj_type = ObjectType(
            properties={"name": PrimitiveType("string"), "address": nested_obj},
            required=["name"],
        )
        schema = obj_type.to_json_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert schema["properties"]["address"]["type"] == "object"

    def test_object_type_required_fields(self):
        """Verify ObjectType includes required fields in schema."""
        obj_type = ObjectType(
            properties={
                "required_field": PrimitiveType("string"),
                "optional_field": PrimitiveType("number"),
            },
            required=["required_field"],
        )
        schema = obj_type.to_json_schema()

        assert "required" in schema
        assert "required_field" in schema["required"]
        assert "optional_field" not in schema["required"]

    def test_object_type_invalid_properties(self):
        """Verify error when properties are not dict."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            obj_type = ObjectType(properties="invalid")  # Should be dict
            obj_type.to_json_schema()


class TestArrayType:
    """Test ArrayType class."""

    def test_array_type_with_items(self):
        """Verify ArrayType with item type serializes to {'type': 'array', 'items': {...}}."""
        arr_type = ArrayType(items=PrimitiveType("number"))
        schema = arr_type.to_json_schema()

        assert schema["type"] == "array"
        assert schema["items"] == {"type": "number"}

    def test_array_type_empty(self):
        """Verify ArrayType without item type serializes to {'type': 'array'}."""
        arr_type = ArrayType()
        schema = arr_type.to_json_schema()

        assert schema["type"] == "array"
        # items field may be absent or empty

    def test_array_type_invalid_items(self):
        """Verify error when items is not a valid type."""
        with pytest.raises((TypeError, ValueError, NotImplementedError)):
            arr_type = ArrayType(items="invalid")  # Should be CyType
            arr_type.to_json_schema()


class TestUnionType:
    """Test UnionType class."""

    def test_union_type_two_types(self):
        """Verify UnionType with 2 types uses {'oneOf': [...]}."""
        union = UnionType([PrimitiveType("number"), PrimitiveType("string")])
        schema = union.to_json_schema()

        assert "oneOf" in schema
        assert len(schema["oneOf"]) == 2
        assert {"type": "number"} in schema["oneOf"]
        assert {"type": "string"} in schema["oneOf"]

    def test_union_type_multiple_types(self):
        """Verify UnionType with 3+ types works correctly."""
        union = UnionType(
            [PrimitiveType("number"), PrimitiveType("string"), PrimitiveType("boolean")]
        )
        schema = union.to_json_schema()

        assert "oneOf" in schema
        assert len(schema["oneOf"]) == 3


class TestAnyType:
    """Test AnyType class."""

    def test_any_type_to_json_schema(self):
        """Verify AnyType serializes to {} (accepts anything)."""
        any_type = AnyType()
        schema = any_type.to_json_schema()

        assert schema == {}


class TestTypeDeserialization:
    """Test from_json_schema() methods."""

    def test_type_from_json_schema_primitive(self):
        """Verify deserialization of primitive types."""
        schema = {"type": "string"}
        cy_type = CyType.from_json_schema(schema)

        assert isinstance(cy_type, PrimitiveType)
        assert cy_type.type_name == "string"

    def test_type_from_json_schema_object(self):
        """Verify deserialization of object types."""
        schema = {
            "type": "object",
            "properties": {"name": {"type": "string"}},
            "required": ["name"],
        }
        cy_type = CyType.from_json_schema(schema)

        assert isinstance(cy_type, ObjectType)
        assert "name" in cy_type.properties

    def test_type_from_json_schema_array(self):
        """Verify deserialization of array types."""
        schema = {"type": "array", "items": {"type": "number"}}
        cy_type = CyType.from_json_schema(schema)

        assert isinstance(cy_type, ArrayType)
        assert cy_type.items is not None

    def test_type_from_json_schema_union(self):
        """Verify deserialization of union types (oneOf)."""
        schema = {"oneOf": [{"type": "string"}, {"type": "number"}]}
        cy_type = CyType.from_json_schema(schema)

        assert isinstance(cy_type, UnionType)
        assert len(cy_type.types) == 2

    def test_from_json_schema_invalid_format(self):
        """Verify error when JSON Schema format is invalid."""
        with pytest.raises((ValueError, KeyError, NotImplementedError)):
            CyType.from_json_schema({"invalid": "schema"})


class TestTypeCompatibility:
    """Test is_compatible_with() methods."""

    def test_number_compatible_with_number(self):
        """Verify number type is compatible with itself."""
        num1 = PrimitiveType("number")
        num2 = PrimitiveType("number")

        assert num1.is_compatible_with(num2)

    def test_number_not_compatible_with_string(self):
        """Verify number type incompatible with string."""
        num = PrimitiveType("number")
        string = PrimitiveType("string")

        assert not num.is_compatible_with(string)

    def test_object_compatible_with_superset(self):
        """Verify object with fewer required fields is compatible."""
        # Object requiring only 'name' should be compatible with object providing 'name' and 'age'
        obj1 = ObjectType(
            properties={"name": PrimitiveType("string")}, required=["name"]
        )
        obj2 = ObjectType(
            properties={
                "name": PrimitiveType("string"),
                "age": PrimitiveType("number"),
            },
            required=["name", "age"],
        )

        assert obj2.is_compatible_with(obj1)  # obj2 provides everything obj1 needs

    def test_array_compatible_with_same_items(self):
        """Verify arrays with same item type are compatible."""
        arr1 = ArrayType(items=PrimitiveType("number"))
        arr2 = ArrayType(items=PrimitiveType("number"))

        assert arr1.is_compatible_with(arr2)

    def test_union_compatible_when_subset(self):
        """Verify union type compatibility logic."""
        # Union of [string, number] should be compatible with just string
        union = UnionType([PrimitiveType("string"), PrimitiveType("number")])
        string = PrimitiveType("string")

        # Union can accept string (it's one of the options)
        assert string.is_compatible_with(union)

    def test_any_compatible_with_everything(self):
        """Verify AnyType is compatible with all types."""
        any_type = AnyType()
        string = PrimitiveType("string")
        number = PrimitiveType("number")

        assert string.is_compatible_with(any_type)
        assert number.is_compatible_with(any_type)
        assert any_type.is_compatible_with(string)
