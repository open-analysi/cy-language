"""
Unit tests for module exports.

These tests verify that DependencyAnalyzer and PlanVisualizer can be imported
from the cy_language package, unblocking the MCP server project.
"""

import pytest


class TestModuleExports:
    """Test that required modules are exported from cy_language package."""

    def test_dependency_analyzer_import(self):
        """Test that DependencyAnalyzer can be imported successfully."""
        from cy_language import DependencyAnalyzer

        assert DependencyAnalyzer is not None
        assert hasattr(DependencyAnalyzer, "__name__")

    def test_plan_visualizer_import(self):
        """Test that PlanVisualizer can be imported successfully."""
        from cy_language import PlanVisualizer

        assert PlanVisualizer is not None
        assert hasattr(PlanVisualizer, "__name__")

    def test_both_imports_in_all(self):
        """Test that both classes are in __all__ list."""
        from cy_language import __all__

        assert "DependencyAnalyzer" in __all__
        assert "PlanVisualizer" in __all__

    def test_dependency_analyzer_instantiation(self):
        """Test that DependencyAnalyzer can be instantiated."""
        from cy_language import DependencyAnalyzer

        analyzer = DependencyAnalyzer()
        assert analyzer is not None

    def test_plan_visualizer_instantiation(self):
        """Test that PlanVisualizer can be instantiated."""
        from cy_language import PlanVisualizer

        visualizer = PlanVisualizer()
        assert visualizer is not None

    def test_import_nonexistent_class(self):
        """Test that importing non-existent class raises ImportError."""
        with pytest.raises(ImportError):
            from cy_language import NonExistentClass  # noqa: F401
