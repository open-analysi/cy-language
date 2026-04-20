"""
Unit tests for TypeEnvironment.

Tests verify that TypeEnvironment correctly stores, retrieves, and
manages variable type information during type inference.
"""

from cy_language.type_environment import TypeEnvironment


class TestBasicOperations:
    """Test basic TypeEnvironment operations."""

    def test_set_and_get_type(self):
        """Set a variable type and retrieve it."""
        env = TypeEnvironment()
        env.set_type("x", {"type": "number"})

        result = env.get_type("x")
        assert result == {"type": "number"}

    def test_get_unknown_variable(self):
        """Get type for variable that was never set."""
        env = TypeEnvironment()

        result = env.get_type("unknown")
        assert result is None

    def test_has_type_returns_true(self):
        """Check has_type for known variable."""
        env = TypeEnvironment()
        env.set_type("x", {"type": "string"})

        assert env.has_type("x") is True

    def test_has_type_returns_false(self):
        """Check has_type for unknown variable."""
        env = TypeEnvironment()

        assert env.has_type("unknown") is False

    def test_overwrite_variable_type(self):
        """Update an existing variable's type."""
        env = TypeEnvironment()
        env.set_type("x", {"type": "number"})
        env.set_type("x", {"type": "string"})

        result = env.get_type("x")
        assert result == {"type": "string"}

    def test_multiple_variables(self):
        """Store types for multiple variables."""
        env = TypeEnvironment()
        env.set_type("x", {"type": "number"})
        env.set_type("y", {"type": "string"})
        env.set_type("z", {"type": "boolean"})

        assert env.get_type("x") == {"type": "number"}
        assert env.get_type("y") == {"type": "string"}
        assert env.get_type("z") == {"type": "boolean"}


class TestSerialization:
    """Test TypeEnvironment serialization."""

    def test_to_dict_empty(self):
        """Export empty environment."""
        env = TypeEnvironment()

        result = env.to_dict()
        assert result == {}

    def test_to_dict_with_variables(self):
        """Export environment with variables."""
        env = TypeEnvironment()
        env.set_type("x", {"type": "number"})
        env.set_type("y", {"type": "string"})

        result = env.to_dict()
        assert result == {"x": {"type": "number"}, "y": {"type": "string"}}


class TestEnvironmentMerging:
    """Test merging TypeEnvironments."""

    def test_merge_non_overlapping(self):
        """Merge environments with different variables."""
        env1 = TypeEnvironment()
        env1.set_type("x", {"type": "number"})

        env2 = TypeEnvironment()
        env2.set_type("y", {"type": "string"})

        merged = env1.merge(env2)

        assert merged.has_type("x")
        assert merged.has_type("y")
        assert merged.get_type("x") == {"type": "number"}
        assert merged.get_type("y") == {"type": "string"}

    def test_merge_same_types(self):
        """Merge environments with same variable, same type."""
        env1 = TypeEnvironment()
        env1.set_type("x", {"type": "number"})

        env2 = TypeEnvironment()
        env2.set_type("x", {"type": "number"})

        merged = env1.merge(env2)

        # Same type should remain the same
        assert merged.get_type("x") == {"type": "number"}

    def test_merge_different_types(self):
        """Merge environments with same variable, different types."""
        env1 = TypeEnvironment()
        env1.set_type("x", {"type": "number"})

        env2 = TypeEnvironment()
        env2.set_type("x", {"type": "string"})

        merged = env1.merge(env2)

        # Different types should create union
        result = merged.get_type("x")
        assert "oneOf" in result
        assert {"type": "number"} in result["oneOf"]
        assert {"type": "string"} in result["oneOf"]

    def test_merge_preserves_original(self):
        """Verify merge doesn't modify original environments."""
        env1 = TypeEnvironment()
        env1.set_type("x", {"type": "number"})

        env2 = TypeEnvironment()
        env2.set_type("y", {"type": "string"})

        merged = env1.merge(env2)

        # Original environments should be unchanged
        assert env1.has_type("x")
        assert not env1.has_type("y")
        assert env2.has_type("y")
        assert not env2.has_type("x")

        # Merged should have both
        assert merged.has_type("x")
        assert merged.has_type("y")


class TestNegativeCases:
    """Test edge cases and negative scenarios."""

    def test_set_type_with_empty_name(self):
        """Try to set type for empty variable name."""
        env = TypeEnvironment()

        # Should handle gracefully - either error or store with empty name
        env.set_type("", {"type": "number"})
        # Test passes if no exception raised

    def test_set_type_with_invalid_schema(self):
        """Set type with non-dict schema."""
        env = TypeEnvironment()

        # Should handle gracefully - either validate or accept
        env.set_type("x", "not a dict")  # type: ignore
        # Test passes if no exception raised or appropriate error
