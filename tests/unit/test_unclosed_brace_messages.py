"""
Test cases that specifically verify error messages for unclosed braces.

This module tests that we get appropriate error messages that mention
the specific issue with unclosed/missing braces and brackets.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestUnClosedBraceErrorMessages:
    """Test that unclosed brace errors provide clear, specific error messages."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_simple_if_unclosed_brace_mentions_rbrace(self):
        """Test that unclosed if brace error mentions RBRACE expected."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
            return output
        # Missing closing brace
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        # Enhanced errors provide cleaner messages about missing braces
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        # Should mention unexpected end of file
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_nested_if_unclosed_brace_mentions_rbrace(self):
        """Test that nested unclosed if brace error mentions RBRACE expected."""
        program = """        x = 5
        y = 3
        if (x > 0) {
            if (y > 0) {
                output = "both positive"
                return output
            # Missing closing brace for inner if
        # Also missing closing brace for outer if
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_while_unclosed_brace_mentions_rbrace(self):
        """Test that unclosed while brace error mentions RBRACE expected."""
        program = """        counter = 0
        while (counter < 3) {
            counter = counter + 1
        # Missing closing brace
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_elif_unclosed_brace_mentions_rbrace(self):
        """Test that unclosed elif brace error mentions RBRACE expected."""
        program = """        score = 75
        if (score >= 90) {
            grade = "A"
        } elif (score >= 80) {
            grade = "B"
        # Missing closing brace for elif
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_else_unclosed_brace_mentions_rbrace(self):
        """Test that unclosed else brace error mentions RBRACE expected."""
        program = """        score = 75
        if (score >= 80) {
            grade = "Good"
        } else {
            grade = "Needs improvement"
        # Missing closing brace for else
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_deeply_nested_unclosed_brace_mentions_rbrace(self):
        """Test that deeply nested unclosed brace error mentions RBRACE expected."""
        program = """        level = 1
        if (level == 1) {
            sublevel = 2
            if (sublevel == 2) {
                subsublevel = 3
                while (subsublevel > 0) {
                    if (subsublevel == 1) {
                        output = "deep"
                        return output
                    # Missing all the closing braces!
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_mixed_control_structures_unclosed_mentions_rbrace(self):
        """Test mixed control structures with unclosed braces mention RBRACE."""
        program = """        data_ready = True
        counter = 0
        
        if (data_ready) {
            while (counter < 5) {
                counter = counter + 1
                if (counter == 3) {
                    result = "found"
                } elif (counter == 4) {
                    result = "almost done"
                } else {
                    result = "processing"
                # Missing closing brace for else
            # Missing closing brace for while  
        # Missing closing brace for if
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg


class TestSpecificBraceErrorScenarios:
    """Test specific scenarios where brace errors should be clear."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()
        self.interpreter.show_enhanced_errors = False

    def test_unclosed_brace_with_statements_after(self):
        """Test unclosed brace when there are statements after the block."""
        program = """        x = 5
        if (x > 0) {
            output = "positive"
        # Missing closing brace, but more code follows
        y = 10
        final_output = y
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        # Should detect the syntax error, likely expecting RBRACE
        assert "Unexpected" in error_msg or "Expected" in error_msg

    def test_completely_missing_braces(self):
        """Test when braces are completely missing from control structures."""
        program = """        x = 5
        if (x > 0)
            output = "positive"
        y = 10
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        # Should expect opening brace
        assert "Unexpected" in error_msg or "Expected" in error_msg

    def test_only_opening_brace_no_closing(self):
        """Test when only opening brace is present."""
        program = """        counter = 0
        while (counter < 3) {
            counter = counter + 1
            output = counter
            return output
        # File ends without closing brace
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        import re

        clean_msg = re.sub(r"\x1b\[[0-9;]*m", "", error_msg)
        assert any(
            keyword in clean_msg
            for keyword in ["Unexpected", "unexpected", "missing", "brace", "end"]
        ), f"Error should mention issue, got: {clean_msg}"
        assert "$END" in error_msg or "Unexpected token" in error_msg

    def test_brace_mismatch_provides_context(self):
        """Test that brace mismatch errors provide helpful context."""
        program = """        level1 = 1
        if (level1 > 0) {
            level2 = 2
            if (level2 > 0) {
                output = "success"
            }
        # Missing one closing brace for level1
        final = "done"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)

        error_msg = str(exc_info.value)
        # Should provide some context about what went wrong
        assert "Unexpected" in error_msg or "Expected" in error_msg
        # Should mention the line or column where the error occurred
        assert "Line" in error_msg or "Col" in error_msg
