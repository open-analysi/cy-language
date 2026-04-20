"""Type environment for tracking variable types during inference.

This module provides the TypeEnvironment class which tracks the types of variables
as they are assigned during type inference.
"""

from typing import Any


class TypeEnvironment:
    """Tracks variable types during type inference.

    Maintains a mapping from variable names to their inferred types
    (as JSON Schema). Used by TypeInferenceEngine to track type information
    as it walks the execution plan.
    """

    def __init__(self) -> None:
        """Initialize empty type environment."""
        self._types: dict[str, dict[str, Any]] = {}  # var_name -> JSON Schema

    def set_type(self, var_name: str, type_schema: dict[str, Any]) -> None:
        """Set or update the type for a variable.

        Args:
            var_name: Variable name (without $ prefix)
            type_schema: JSON Schema dict representing the type
        """
        self._types[var_name] = type_schema

    def get_type(self, var_name: str) -> dict[str, Any] | None:
        """Get the type for a variable.

        Args:
            var_name: Variable name (without $ prefix)

        Returns:
            JSON Schema dict if variable has known type, None otherwise
        """
        return self._types.get(var_name)

    def has_type(self, var_name: str) -> bool:
        """Check if a variable has a known type.

        Args:
            var_name: Variable name (without $ prefix)

        Returns:
            True if variable type is known, False otherwise
        """
        return var_name in self._types

    def copy(self) -> "TypeEnvironment":
        """Create a shallow copy of this type environment.

        Returns:
            New TypeEnvironment with same variable types
        """
        new_env = TypeEnvironment()
        new_env._types = dict(self._types)
        return new_env

    def merge(self, other: "TypeEnvironment") -> "TypeEnvironment":
        """Merge two type environments (for control flow branches).

        When a variable exists in both environments with different types,
        creates a union type. Used for if/else branches.

        Args:
            other: Another TypeEnvironment to merge with

        Returns:
            New TypeEnvironment containing merged types
        """
        merged = TypeEnvironment()

        # Add all variables from self
        for var_name, type_schema in self._types.items():
            merged._types[var_name] = type_schema

        # Merge variables from other
        for var_name, other_type_schema in other._types.items():
            if var_name in merged._types:
                # Variable exists in both - check if types are the same
                if merged._types[var_name] == other_type_schema:
                    # Same type - keep as is
                    pass
                else:
                    # Different types - create union
                    merged._types[var_name] = self._create_union_type(
                        merged._types[var_name], other_type_schema
                    )
            else:
                # Variable only in other - add it
                merged._types[var_name] = other_type_schema

        return merged

    def _create_union_type(
        self, type1: dict[str, Any], type2: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a union type from two types, handling existing unions.

        Args:
            type1: First type schema
            type2: Second type schema

        Returns:
            Union type schema with unique types
        """
        # Collect all types (flatten existing unions)
        types = []

        # Add types from type1
        if "oneOf" in type1:
            types.extend(type1["oneOf"])
        else:
            types.append(type1)

        # Add types from type2
        if "oneOf" in type2:
            types.extend(type2["oneOf"])
        else:
            types.append(type2)

        # Remove duplicates while preserving order
        unique_types = []
        for t in types:
            if t not in unique_types:
                unique_types.append(t)

        # If only one unique type, return it directly
        if len(unique_types) == 1:
            result: dict[str, Any] = unique_types[0]
            return result

        return {"oneOf": unique_types}

    def to_dict(self) -> dict[str, dict[str, Any]]:
        """Export environment to dict for debugging/serialization.

        Returns:
            Dict mapping variable names to their type schemas
        """
        return dict(self._types)

    def __str__(self) -> str:
        """String representation for debugging."""
        return f"TypeEnvironment({len(self._types)} variables)"

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return f"TypeEnvironment(_types={self._types!r})"
