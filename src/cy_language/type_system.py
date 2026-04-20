"""Type system for Cy language static type inference.

This module provides type representations and JSON Schema conversion
for the Cy language type inference system.
"""

from typing import Any, ClassVar, Union


class CyType:
    """Base class for all Cy type representations."""

    def to_json_schema(self) -> dict[str, Any]:
        """Convert this type to JSON Schema format.

        Returns:
            JSON Schema dict representing this type
        """
        raise NotImplementedError("Subclass must implement to_json_schema()")

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "CyType":
        """Create a CyType from JSON Schema format.

        Args:
            schema: JSON Schema dict

        Returns:
            CyType instance representing the schema
        """
        # Dispatch based on schema structure
        if not schema or schema == {}:
            return AnyType()
        if "oneOf" in schema:
            return UnionType.from_json_schema(schema)
        if "type" in schema:
            type_val = schema["type"]
            if type_val == "object":
                return ObjectType.from_json_schema(schema)
            if type_val == "array":
                return ArrayType.from_json_schema(schema)
            if type_val in {"number", "string", "boolean", "null"}:
                return PrimitiveType.from_json_schema(schema)
        raise ValueError(f"Cannot determine CyType from schema: {schema}")

    def is_compatible_with(self, other: "CyType") -> bool:
        """Check if this type is compatible with another type.

        Args:
            other: Another CyType to check compatibility with

        Returns:
            True if this type is compatible with other
        """
        raise NotImplementedError("Subclass must implement is_compatible_with()")


class PrimitiveType(CyType):
    """Represents primitive types: number, string, boolean, null."""

    VALID_TYPES: ClassVar[set[str]] = {"number", "string", "boolean", "null"}

    def __init__(self, type_name: str):
        """Initialize primitive type.

        Args:
            type_name: One of "number", "string", "boolean", "null"
        """
        if type_name not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid primitive type: {type_name}. Must be one of {self.VALID_TYPES}"
            )
        self.type_name = type_name

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        return {"type": self.type_name}

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "PrimitiveType":
        """Create from JSON Schema format."""
        if "type" not in schema:
            raise ValueError("Schema must have 'type' field")
        return cls(schema["type"])

    def is_compatible_with(self, other: CyType) -> bool:
        """Check type compatibility."""
        if isinstance(other, AnyType):
            return True
        if isinstance(other, PrimitiveType):
            return self.type_name == other.type_name
        if isinstance(other, UnionType):
            # Check if this type is one of the union options
            return any(self.is_compatible_with(t) for t in other.types)
        return False

    def __str__(self) -> str:
        return f"PrimitiveType({self.type_name})"

    def __repr__(self) -> str:
        return f"PrimitiveType(type_name={self.type_name!r})"


class ObjectType(CyType):
    """Represents object/dict types with properties."""

    def __init__(
        self, properties: dict[str, CyType], required: list[str] | None = None
    ):
        """Initialize object type.

        Args:
            properties: Dict mapping property names to their types
            required: List of required property names
        """
        if not isinstance(properties, dict):
            raise TypeError("properties must be a dict")
        self.properties = properties
        self.required = required or []

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                name: prop_type.to_json_schema()
                for name, prop_type in self.properties.items()
            },
        }
        if self.required:
            schema["required"] = self.required
        return schema

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "ObjectType":
        """Create from JSON Schema format."""
        if schema.get("type") != "object":
            raise ValueError("Schema must have type='object'")

        properties = {}
        if "properties" in schema:
            for name, prop_schema in schema["properties"].items():
                properties[name] = CyType.from_json_schema(prop_schema)

        required = schema.get("required", [])
        return cls(properties, required)

    def is_compatible_with(self, other: CyType) -> bool:
        """Check type compatibility."""
        if isinstance(other, AnyType):
            return True
        if isinstance(other, ObjectType):
            # Check if all required properties of other exist in self
            for req_prop in other.required:
                if req_prop not in self.properties:
                    return False
                # Check property type compatibility
                if not self.properties[req_prop].is_compatible_with(
                    other.properties[req_prop]
                ):
                    return False
            return True
        if isinstance(other, UnionType):
            return any(self.is_compatible_with(t) for t in other.types)
        return False

    def __str__(self) -> str:
        return f"ObjectType(properties={list(self.properties.keys())})"

    def __repr__(self) -> str:
        return f"ObjectType(properties={self.properties!r}, required={self.required!r})"


class ArrayType(CyType):
    """Represents array/list types."""

    def __init__(self, items: CyType | None = None):
        """Initialize array type.

        Args:
            items: Type of array items (None = any type)
        """
        if items is not None and not isinstance(items, CyType):
            raise TypeError("items must be a CyType or None")
        self.items = items

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        schema: dict[str, Any] = {"type": "array"}
        if self.items is not None:
            schema["items"] = self.items.to_json_schema()
        return schema

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "ArrayType":
        """Create from JSON Schema format."""
        if schema.get("type") != "array":
            raise ValueError("Schema must have type='array'")

        items = None
        if "items" in schema:
            items = CyType.from_json_schema(schema["items"])

        return cls(items)

    def is_compatible_with(self, other: CyType) -> bool:
        """Check type compatibility."""
        if isinstance(other, AnyType):
            return True
        if isinstance(other, ArrayType):
            # If both have items, check compatibility
            if self.items is not None and other.items is not None:
                return self.items.is_compatible_with(other.items)
            # If one has items and the other doesn't, still compatible
            return True
        if isinstance(other, UnionType):
            return any(self.is_compatible_with(t) for t in other.types)
        return False

    def __str__(self) -> str:
        return f"ArrayType(items={self.items})"

    def __repr__(self) -> str:
        return f"ArrayType(items={self.items!r})"


class UnionType(CyType):
    """Represents union of multiple possible types."""

    def __init__(self, types: list[CyType]):
        """Initialize union type.

        Args:
            types: List of possible types
        """
        if not isinstance(types, list) or len(types) == 0:
            raise ValueError("types must be a non-empty list")
        self.types = types

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        return {"oneOf": [t.to_json_schema() for t in self.types]}

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "UnionType":
        """Create from JSON Schema format."""
        if "oneOf" not in schema:
            raise ValueError("Schema must have 'oneOf' field for union types")

        types = [CyType.from_json_schema(s) for s in schema["oneOf"]]
        return cls(types)

    def is_compatible_with(self, other: CyType) -> bool:
        """Check type compatibility."""
        if isinstance(other, AnyType):
            return True
        if isinstance(other, UnionType):
            # All of our types must be compatible with at least one of other's types
            return all(
                any(t.is_compatible_with(ot) for ot in other.types) for t in self.types
            )
        # If other is not a union, check if any of our types is compatible
        return any(t.is_compatible_with(other) for t in self.types)

    def __str__(self) -> str:
        return f"UnionType({len(self.types)} types)"

    def __repr__(self) -> str:
        return f"UnionType(types={self.types!r})"


class AnyType(CyType):
    """Represents the 'any' type (accepts anything)."""

    def to_json_schema(self) -> dict[str, Any]:
        """Convert to JSON Schema format."""
        return {}

    @classmethod
    def from_json_schema(cls, schema: dict[str, Any]) -> "AnyType":
        """Create from JSON Schema format."""
        # Empty schema {} represents any type
        return cls()

    def is_compatible_with(self, other: CyType) -> bool:
        """Check type compatibility."""
        # AnyType is compatible with everything
        return True

    def __str__(self) -> str:
        return "AnyType"

    def __repr__(self) -> str:
        return "AnyType()"


def python_type_to_json_schema(python_type: Any) -> dict[str, Any]:
    """Convert Python type hint to JSON Schema format.

    Supports: int, str, bool, None, List, Dict, Union, Optional, Any

    Args:
        python_type: Python type from typing module or builtin

    Returns:
        JSON Schema dict representing the type

    Example:
        >>> python_type_to_json_schema(int)
        {"type": "number"}
        >>> python_type_to_json_schema(List[str])
        {"type": "array", "items": {"type": "string"}}
    """
    from typing import get_args, get_origin

    # Handle None type
    if python_type is type(None):
        return {"type": "null"}

    # Handle basic types
    if python_type is int or python_type is float:
        return {"type": "number"}
    if python_type is str:
        return {"type": "string"}
    if python_type is bool:
        return {"type": "boolean"}
    if python_type is list:
        return {"type": "array"}
    if python_type is dict:
        return {"type": "object"}

    # Handle Any
    if python_type is Any:
        return {}

    # Handle generic types (List[T], Dict[K, V], Union, Optional)
    origin = get_origin(python_type)
    args = get_args(python_type)

    if origin is list:
        if args:
            items_schema = python_type_to_json_schema(args[0])
            return {"type": "array", "items": items_schema}
        return {"type": "array"}

    if origin is dict:
        if len(args) >= 2:
            # Dict[str, T] - value type is args[1]
            value_schema = python_type_to_json_schema(args[1])
            return {"type": "object", "additionalProperties": value_schema}
        return {"type": "object"}

    if origin is Union:
        return _union_type_to_json_schema(args)

    # Handle Python 3.10+ union syntax (X | Y)
    import types

    if isinstance(python_type, types.UnionType):
        return _union_type_to_json_schema(get_args(python_type))

    # Fallback for unsupported types - return Any
    return {}


def _union_type_to_json_schema(args: tuple) -> dict[str, Any]:
    """Convert Union type arguments to JSON Schema format."""
    schemas = [python_type_to_json_schema(arg) for arg in args]

    # Deduplicate schemas (e.g., Union[int, float] -> both are {"type": "number"})
    unique_schemas = []
    seen: set[str] = set()
    for schema in schemas:
        schema_str = str(sorted(schema.items()))
        if schema_str not in seen:
            seen.add(schema_str)
            unique_schemas.append(schema)

    # If only one unique schema remains, return it directly (not a union)
    if len(unique_schemas) == 1:
        return unique_schemas[0]

    return {"oneOf": unique_schemas}
