"""
Variable normalization system for optional $ syntax in assignments.

This module provides utilities to normalize variable names, converting both
$name and name forms to a canonical representation for storage and lookup.
"""

from typing import Any


class VariableNormalizer:
    """Handles canonical variable name normalization for optional $ syntax."""

    @staticmethod
    def normalize_name(name: str) -> str:
        """Convert both $name and name to canonical 'name' form.

        Args:
            name: Variable name that may or may not have $ prefix

        Returns:
            Normalized name without $ prefix

        Examples:
            normalize_name("$name") -> "name"
            normalize_name("name") -> "name"
            normalize_name("$user_id") -> "user_id"
            normalize_name("$") -> "" (edge case)
        """
        if name.startswith("$"):
            # Handles both "$name" -> "name" and "$" -> ""
            return name[1:]
        return name

    @staticmethod
    def is_reserved_literal(name: str) -> bool:
        """Check if name is a reserved literal that cannot be used as variable.

        Args:
            name: Variable name to check (normalized, without $ prefix)

        Returns:
            True if the name is a reserved literal

        Examples:
            is_reserved_literal("True") -> True
            is_reserved_literal("false") -> True
            is_reserved_literal("None") -> True
            is_reserved_literal("user_name") -> False
        """
        # Clearly problematic literals
        reserved_literals = {
            "True",
            "False",  # Boolean literals that behave strangely as variables
            "None",  # Python-style null
            "true",
            "false",  # Lowercase boolean literals
            "null",  # Cy null literal
        }

        return name in reserved_literals

    @staticmethod
    def is_reserved_keyword(name: str) -> bool:
        """Check if name is a reserved keyword that cannot be used as variable.

        Args:
            name: Variable name to check (normalized, without $ prefix)

        Returns:
            True if the name is a reserved keyword
        """
        # Reserved keywords that cannot be used as variable names
        reserved_keywords = {
            # Control flow keywords
            "if",
            "elif",
            "else",
            "while",
            "return",
            "try",
            "catch",
            "finally",
            # Boolean operators
            "and",
            "or",
            "not",
        }
        return name in reserved_keywords

    @staticmethod
    def is_reserved_function(name: str, available_tools: dict[str, Any]) -> bool:
        """Check if normalized name conflicts with function names.

        Args:
            name: Variable name to check (may have $ prefix)
            available_tools: Dictionary of available tool/function names

        Returns:
            True if the normalized name conflicts with a function

        Examples:
            is_reserved_function("len", {}) -> True (built-in function)
            is_reserved_function("$len", {}) -> True (normalized to "len")
            is_reserved_function("add", {"add": func}) -> True (custom tool)
        """
        normalized = VariableNormalizer.normalize_name(name)

        # Built-in functions that cannot be overridden
        builtin_functions = {
            "len",
            "debug_print",
            "json_string_to_struct",
            "llm_run",
            "llm_evaluate_results",
            "llm_give_feedback",
            "llm_revise_task",
        }

        if normalized in builtin_functions:
            return True

        # Check custom tools/functions
        return bool(available_tools and normalized in available_tools)
