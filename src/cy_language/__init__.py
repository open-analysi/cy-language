"""Cy language interpreter for programmable directives."""

from importlib.metadata import version

from cy_language import native_functions  # noqa: F401
from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.errors import ExecutionPaused
from cy_language.execution_plan import ExecutionCheckpoint
from cy_language.interpreter import Cy
from cy_language.plan_visualization import PlanVisualizer
from cy_language.script_analysis_api import analyze_script
from cy_language.tool_registry_builder import (
    build_tool_registry,
    export_mcp_tools,
    export_native_tools,
)
from cy_language.tool_signature import ToolRegistry, ToolSignature
from cy_language.type_analysis_api import analyze_types, data_to_schema

__version__ = version("cy-language")
__all__ = [
    "Cy",
    "DependencyAnalyzer",
    "ExecutionCheckpoint",
    "ExecutionPaused",
    "PlanVisualizer",
    "ToolRegistry",
    "ToolSignature",
    "analyze_script",
    "analyze_types",
    "build_tool_registry",
    "data_to_schema",
    "export_mcp_tools",
    "export_native_tools",
]
