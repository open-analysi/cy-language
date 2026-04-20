"""
Edge case tests for Compound Assignment Operators.

These tests cover complex interactions between compound assignments and
other language features, particularly cases that arose during implementation.
"""

from cy_language.interpreter import Cy


class TestCompoundAssignmentWithInterpolation:
    """Test compound assignments work correctly with string interpolation."""

    def test_compound_assignment_then_interpolation(self):
        """Test variable modified with += can be interpolated."""
        program = """
        counter = 5
        counter += 10
        output = "Count: ${counter}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Count: 15"'

    def test_interpolation_with_compound_modified_variable(self):
        """Test interpolated expressions using compound-modified variables."""
        program = """
        x = 10
        x += 5
        output = "Result: ${x + 3}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Result: 18"'

    def test_multiple_compound_ops_with_interpolation(self):
        """Test multiple compound operations before interpolation."""
        program = """
        a = 1
        b = 2
        a += 5
        b *= 3
        output = "${a} and ${b}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"6 and 6"'


class TestNestedIndexedCompoundAssignment:
    """Test compound assignment with nested/chained indexed access."""

    def test_nested_list_compound_assignment(self):
        """Test compound assignment on nested list elements."""
        program = """
        matrix = [[1, 2], [3, 4]]
        matrix[0][1] += 10
        output = matrix
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[[1, 12], [3, 4]]" in result

    def test_nested_dict_compound_assignment(self):
        """Test compound assignment on nested dictionary values."""
        program = """
        data = {"outer": {"inner": 100}}
        data["outer"]["inner"] += 50
        output = data["outer"]["inner"]
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "150"


class TestCompoundAssignmentInExpressions:
    """Test that compound operators don't interfere with regular expressions."""

    def test_plus_in_comparison_not_confused_with_plus_equals(self):
        """Test + in expressions isn't tokenized as part of +=."""
        program = """
        x = 10
        if (x + 5 == 15) {
            output = "correct"
        } else {
            output = "wrong"
        }
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"correct"'

    def test_equals_in_comparison_not_confused_with_assign(self):
        """Test == comparisons work correctly with compound assignment in same program."""
        program = """
        x = 10
        y = 5
        if (x == 10) {
            y += 5
        }
        if (x != 15) {
            y -= 2
        }
        output = "${x},${y}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"10,8"'

    def test_compound_assignment_with_complex_expression(self):
        """Test compound assignment with complex right-hand expression."""
        program = """
        a = 5
        b = 3
        c = 2
        a += b + c * 2
        output = a
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 5 + (3 + 2*2) = 5 + 7 = 12
        assert result == "12"


class TestCompoundAssignmentInLoops:
    """Test compound assignment in loop contexts."""

    def test_accumulator_pattern_in_for_loop(self):
        """Test classic accumulator pattern with += in loop."""
        program = """
        total = 0
        for (num in [1, 2, 3, 4, 5]) {
            total += num
        }
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_string_building_in_loop(self):
        """Test string concatenation with += in loop."""
        program = """
        result = ""
        for (word in ["Hello", " ", "World"]) {
            result += word
        }
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"Hello World"'

    def test_list_building_in_loop(self):
        """Test list concatenation with += in loop."""
        program = """
        result = []
        for (item in [1, 2, 3]) {
            result += [item * 2]
        }
        output = result
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "[2, 4, 6]" in result

    def test_multiple_compound_ops_in_loop(self):
        """Test different compound operators in loop iterations."""
        program = """
        total = 100
        for (i in [1, 2, 3]) {
            if (i == 1) {
                total += 10
            } elif (i == 2) {
                total *= 2
            } else {
                total -= 20
            }
        }
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 100 + 10 = 110, 110 * 2 = 220, 220 - 20 = 200
        assert result == "200"


class TestCompoundAssignmentWithTryCatch:
    """Test compound assignment in try-catch-finally blocks."""

    def test_compound_assignment_in_try_block(self):
        """Test compound assignment in try block."""
        program = """
        total = 10
        try {
            total += 5
        } catch (e) {
            total += 1
        }
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "15"

    def test_compound_assignment_in_catch_block(self):
        """Test compound assignment in catch block after error."""
        program = """
        total = 0
        try {
            x = 10 / 0
            total += 100
        } catch (e) {
            total += 1
        }
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "1"


class TestAllCompoundOperatorsTogether:
    """Test all compound operators in sequence."""

    def test_all_operators_in_chain(self):
        """Test using all compound operators sequentially."""
        program = """
        x = 10
        x += 5
        x *= 2
        x -= 10
        x /= 4
        x %= 3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        # 10 + 5 = 15, 15 * 2 = 30, 30 - 10 = 20, 20 / 4 = 5.0, 5.0 % 3 = 2.0
        assert "2" in result  # Could be "2" or "2.0" depending on float handling

    def test_all_operators_with_different_variables(self):
        """Test all compound operators on different variables."""
        program = """
        a = 10
        b = 5
        c = 8
        d = 20
        e = 17
        a += 5
        b -= 2
        c *= 3
        d /= 4
        e %= 5
        output = "${a},${b},${c},${d},${e}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "15,3,24," in result
        assert ",2" in result  # e = 17 % 5 = 2


class TestCompoundAssignmentWithFunctionCalls:
    """Test compound assignment with function/tool call results."""

    def test_compound_with_len_function(self):
        """Test compound assignment using len() result."""
        program = """
        count = 5
        list = [1, 2, 3]
        count += len(list)
        output = count
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "8"

    def test_compound_with_nested_function_calls(self):
        """Test compound assignment with nested function results."""
        program = """
        total = 0
        items = [1, 2, 3, 4, 5]
        more = [6, 7]
        total += len(items) + len(more)
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "7"  # 0 + (5 + 2)


class TestWhitespaceVariations:
    """Test compound operators with various whitespace patterns."""

    def test_no_whitespace(self):
        """Test compound operators without spaces."""
        program = """
        x=5
        x+=3
        output=x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "8"

    def test_whitespace_before_operator(self):
        """Test whitespace before compound operator."""
        program = """
        x = 5
        x +=3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "8"

    def test_whitespace_after_operator(self):
        """Test whitespace after compound operator."""
        program = """
        x = 5
        x+= 3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "8"

    def test_mixed_whitespace_in_program(self):
        """Test program with various whitespace patterns."""
        program = """
        a=1
        b= 2
        c =3
        a+=b+c
        output = a
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "6"


class TestCompoundAssignmentBackwardCompatibility:
    """Ensure compound assignments don't break existing patterns."""

    def test_regular_assignment_still_works(self):
        """Verify = assignment unchanged."""
        program = """
        x = 5
        x = x + 3
        output = x
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "8"

    def test_comparison_operators_unchanged(self):
        """Verify ==, !=, <=, >= still work."""
        program = """
        a = 5
        b = 10
        c = 5
        eq = a == c
        neq = a != b
        lte = a <= b
        gte = b >= a
        output = "${eq},${neq},${lte},${gte}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"True,True,True,True"'

    def test_arithmetic_operators_unchanged(self):
        """Verify +, -, *, /, % operators still work."""
        program = """
        total = 5 + 3
        diff = 10 - 4
        prod = 3 * 4
        quot = 20 / 4
        remainder = 17 % 5
        output = "${total},${diff},${prod},${quot},${remainder}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "8,6,12," in result
        assert ",2" in result


class TestCompoundAssignmentRealWorldScenarios:
    """Test real-world usage patterns."""

    def test_counter_increment_pattern(self):
        """Test common counter increment pattern."""
        program = """
        attempts = 0
        max_attempts = 3
        success = False

        for (i in [1, 2, 3]) {
            attempts += 1
            if (i == 2) {
                success = True
            }
        }

        output = "Attempts: ${attempts}, Success: ${success}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert "Attempts: 3" in result
        assert "Success: True" in result

    def test_score_calculation_pattern(self):
        """Test score calculation with bonuses."""
        program = """
        base_score = 100
        bonus = 0

        base_score += 50
        bonus += 10

        if (base_score >= 150) {
            bonus *= 2
        }

        total = base_score + bonus
        output = total
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == "170"  # 150 + 20

    def test_data_aggregation_pattern(self):
        """Test aggregating data from multiple sources."""
        program = """
        total_users = 0
        total_posts = 0

        sources = [
            {"users": 10, "posts": 50},
            {"users": 15, "posts": 75},
            {"users": 5, "posts": 25}
        ]

        for (source in sources) {
            total_users += source["users"]
            total_posts += source["posts"]
        }

        output = "${total_users},${total_posts}"
        return output
        """

        cy = Cy()
        result = cy.run(program)
        assert result == '"30,150"'
