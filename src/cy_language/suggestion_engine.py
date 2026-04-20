"""Suggestion engine for tool names and error fixes.

This module provides utilities for suggesting similar tool names and
generating fix suggestions for various error types.
"""

from typing import Any


class SuggestionEngine:
    """Generates suggestions for tool names and error fixes."""

    def __init__(self, tools: dict[str, Any] | None = None):
        """Initialize suggestion engine with available tools.

        Args:
            tools: Dictionary of available tool names to their metadata
        """
        self.tools = tools or {}

    def suggest_similar_tools(
        self, tool_name: str, max_suggestions: int = 3
    ) -> list[str]:
        """Suggest similar tool names for a not-found tool.

        Args:
            tool_name: The tool name that wasn't found
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of similar tool names (FQNs if applicable)
        """
        if not self.tools:
            return []

        # Check if the tool_name has namespaces
        has_namespace = "::" in tool_name
        tool_parts = tool_name.split("::")
        last_part = tool_parts[-1] if tool_parts else tool_name

        # Get all available tool names
        candidates = list(self.tools.keys())
        suggestions = []

        # If no namespace, compare against just the last part of candidates
        if not has_namespace:
            # Build a list of (full_name, last_part) tuples
            candidate_tuples = []
            for candidate in candidates:
                candidate_parts = candidate.split("::")
                candidate_last = candidate_parts[-1]
                candidate_tuples.append((candidate, candidate_last))

            # Find matches based on last part only
            matches = []
            for full_name, last_part_cand in candidate_tuples:
                distance = self.levenshtein_distance(last_part, last_part_cand)
                if distance <= 3:  # More lenient for partial matches
                    matches.append((full_name, distance))

            # Sort by distance
            matches.sort(key=lambda x: x[1])

            # Add to suggestions
            for match, _ in matches[:max_suggestions]:
                suggestions.append(match)

        else:
            # Has namespace, so compare full names
            # First, try exact matches with different namespaces
            for candidate in candidates:
                candidate_parts = candidate.split("::")
                if candidate_parts[-1] == last_part:
                    suggestions.append(candidate)
                    if len(suggestions) >= max_suggestions:
                        return suggestions

            # Then, find close matches based on edit distance
            close_matches = self._find_closest_matches(
                tool_name, candidates, max_distance=5
            )

            # Add close matches to suggestions
            for match, _distance in close_matches:
                if match not in suggestions:
                    suggestions.append(match)
                    if len(suggestions) >= max_suggestions:
                        break

        return suggestions[:max_suggestions]

    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance between strings
        """
        # Handle empty strings
        if not s1:
            return len(s2)
        if not s2:
            return len(s1)

        # Create distance matrix
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # Initialize base cases
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j

        # Fill the matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i - 1] == s2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],  # deletion
                        dp[i][j - 1],  # insertion
                        dp[i - 1][j - 1],  # substitution
                    )

        return dp[m][n]

    def suggest_type_fix(self, error_type: str, context: dict[str, Any]) -> str | None:
        """Suggest fixes for type errors.

        Args:
            error_type: Type of type error (nullable, mismatch, etc.)
            context: Context information about the error

        Returns:
            Suggestion string or None if no suggestion available
        """
        if error_type == "type_mismatch":
            from_type = context.get("from", "")
            to_type = context.get("to", "")
            expression = context.get("expression", "value")

            # Suggest conversion functions
            if from_type == "string" and to_type == "number":
                return f"Try converting the string to a number: int({expression}) or float({expression})"
            if from_type == "number" and to_type == "string":
                return f"Try converting the number to a string: str({expression})"
            if from_type == "any" and to_type in ["string", "number", "boolean"]:
                return f"Ensure the value is of type {to_type} or use type conversion: {to_type}({expression})"
            return f"Cannot directly convert from {from_type} to {to_type}. Consider restructuring the data."

        if error_type == "nullable":
            expression = context.get("expression", "value")
            expected_type = context.get("expected_type", "string")
            return self.suggest_nullable_fix(expression, expected_type)

        return None

    def suggest_nullable_fix(self, expression: str, expected_type: str) -> str:
        """Suggest fix for nullable type errors using ?? operator.

        Args:
            expression: The nullable expression
            expected_type: The expected non-nullable type

        Returns:
            Suggestion with example using ?? operator
        """
        # Determine appropriate default value based on type
        default_values = {
            "string": '""',
            "number": "0",
            "boolean": "False",
            "list": "[]",
            "dict": "{}",
            "any": "null",
        }

        default = default_values.get(expected_type.lower(), '""')

        # Create suggestion with ?? operator
        suggestion = (
            f"Use the null-coalescing operator ?? to provide a default value:\n"
            f"  {expression} ?? {default}\n"
            f"This will use {default} if {expression} is null."
        )

        return suggestion

    def _find_closest_matches(
        self, target: str, candidates: list[str], max_distance: int = 3
    ) -> list[tuple[str, int]]:
        """Find closest string matches using edit distance.

        Args:
            target: Target string to match
            candidates: List of candidate strings
            max_distance: Maximum edit distance to consider

        Returns:
            List of (candidate, distance) tuples sorted by distance
        """
        matches = []

        for candidate in candidates:
            distance = self.levenshtein_distance(target, candidate)
            if distance <= max_distance:
                matches.append((candidate, distance))

        # Sort by distance (ascending)
        matches.sort(key=lambda x: x[1])

        return matches

    def suggest_fix_for_pattern(
        self, pattern_type: str, matched_text: str
    ) -> str | None:
        """Suggest fix for a known error pattern.

        Args:
            pattern_type: Type of pattern (lowercase_bool, symbol_operator, etc.)
            matched_text: The actual text that matched the pattern

        Returns:
            Fix suggestion or None
        """
        pattern_fixes = {
            "lowercase_bool": {
                "true": "Replace 'true' with 'True'",
                "false": "Replace 'false' with 'False'",
            },
            "symbol_operator": {
                "&&": "Replace '&&' with 'and'",
                "||": "Replace '||' with 'or'",
                "!": "Replace '!' with 'not'",
            },
            "range_function": {
                "range": "range() is a native function in Cy. Syntax: range(stop), range(start, stop), or range(start, stop, step)"
            },
            # break/continue are now supported as loop control statements
        }

        if pattern_type in pattern_fixes:
            fixes = pattern_fixes[pattern_type]
            if matched_text in fixes:
                return fixes[matched_text]
            # For patterns with a single fix
            if len(fixes) == 1:
                return next(iter(fixes.values()))

        return None
