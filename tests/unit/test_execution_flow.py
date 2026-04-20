"""Tests to verify try/catch execution flow - only correct branches execute."""

from cy_language import Cy


class TestTryCatchExecutionFlow:
    """Test that try/catch uses conditional execution, not all-branch execution."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cy = Cy()

    def test_success_path_skips_catch(self):
        """Test that successful try block skips catch block entirely."""
        program = """
        try_executed = False
        catch_executed = False
        finally_executed = False

        try {
            try_executed = True
            result = "success"
        } catch (e) {
            catch_executed = True
            result = "error"
        } finally {
            finally_executed = True
        }

        output = "try:${try_executed},catch:${catch_executed},finally:${finally_executed},result:${result}"
        return output
        """
        result = self.cy.run(program)
        assert "try:True,catch:False,finally:True,result:success" in result

    def test_exception_skips_remaining_try_statements(self):
        """Test that exception immediately stops try block execution."""
        program = """
        try_start = False
        try_after_exception = False
        catch_executed = False

        try {
            try_start = True
            x = 1 / 0  # Exception occurs here
            try_after_exception = True  # This should NEVER execute
        } catch (e) {
            catch_executed = True
        }

        output = "start:${try_start},after:${try_after_exception},catch:${catch_executed}"
        return output
        """
        result = self.cy.run(program)
        assert "start:True,after:False,catch:True" in result

    def test_catch_only_executes_on_exception(self):
        """Test that catch block only runs when there's an exception."""
        program = """
        # Test successful case - catch should not execute
        success_try = False
        success_catch = False

        try {
            success_try = True
            value = 42
        } catch (e) {
            success_catch = True
        }

        # Test exception case - catch should execute
        error_try = False
        error_catch = False

        try {
            error_try = True
            value = 1 / 0
        } catch (e) {
            error_catch = True
        }

        output = "success_try:${success_try},success_catch:${success_catch},error_try:${error_try},error_catch:${error_catch}"
        return output
        """
        result = self.cy.run(program)
        assert (
            "success_try:True,success_catch:False,error_try:True,error_catch:True"
            in result
        )

    def test_finally_always_executes(self):
        """Test that finally block executes in both success and error cases."""
        program = """
        results = []

        # Test 1: Success case
        try {
            value = 42
        } catch (e) {
            value = "error"
        } finally {
            results = results + ["finally1"]
        }

        # Test 2: Exception case
        try {
            value = 1 / 0
        } catch (e) {
            value = "caught"
        } finally {
            results = results + ["finally2"]
        }

        output = "results:${results|csv}"
        return output
        """
        result = self.cy.run(program)
        assert "finally1" in result
        assert "finally2" in result

    def test_nested_execution_isolation(self):
        """Test that inner try/catch doesn't affect outer execution unless exception propagates."""
        program = """
        outer_try = False
        outer_catch = False
        inner_try = False
        inner_catch = False
        after_inner = False

        try {
            outer_try = True

            # Inner try/catch handles its own exception
            try {
                inner_try = True
                x = 1 / 0  # Exception handled by inner catch
            } catch (inner_e) {
                inner_catch = True
            }

            # This should execute because inner exception was handled
            after_inner = True

        } catch (outer_e) {
            # This should NOT execute because no exception reaches outer
            outer_catch = True
        }

        output = "outer_try:${outer_try},outer_catch:${outer_catch},inner_try:${inner_try},inner_catch:${inner_catch},after_inner:${after_inner}"
        return output
        """
        result = self.cy.run(program)
        assert (
            "outer_try:True,outer_catch:False,inner_try:True,inner_catch:True,after_inner:True"
            in result
        )

    def test_exception_propagates_when_not_handled(self):
        """Test that unhandled inner exceptions propagate to outer catch."""
        program = """
        outer_try = False
        outer_catch = False
        inner_try = False
        after_inner = False

        try {
            outer_try = True

            # Inner try without catch - exception will propagate
            inner_try = True
            x = 1 / 0  # This will propagate to outer catch

            # This should NOT execute
            after_inner = True

        } catch (outer_e) {
            # This SHOULD execute because inner exception propagated
            outer_catch = True
        }

        output = "outer_try:${outer_try},outer_catch:${outer_catch},inner_try:${inner_try},after_inner:${after_inner}"
        return output
        """
        result = self.cy.run(program)
        assert (
            "outer_try:True,outer_catch:True,inner_try:True,after_inner:False" in result
        )

    def test_multiple_statements_execution_order(self):
        """Test execution order and that only executed statements affect variables."""
        program = """
        counter = 0
        steps = []

        try {
            counter = counter + 1
            steps = steps + ["try1"]

            if (counter == 1) {
                counter = counter + 1
                steps = steps + ["try2"]
                x = 1 / 0  # Exception here
            }

            # These should NOT execute
            counter = counter + 1
            steps = steps + ["try3_never"]

        } catch (e) {
            counter = counter + 1
            steps = steps + ["catch"]
        } finally {
            counter = counter + 1
            steps = steps + ["finally"]
        }

        output = "counter:${counter},steps:${steps|csv}"
        return output
        """
        result = self.cy.run(program)
        # counter should be 4 (1+1+1+1), steps should not include "try3_never"
        assert "counter:4" in result
        assert "try1" in result
        assert "try2" in result
        assert "catch" in result
        assert "finally" in result
        assert "try3_never" not in result

    def test_variable_mutations_only_in_executed_branches(self):
        """Test that variables are only modified in branches that actually execute."""
        program = """
        # Initialize tracking variables
        success_marker = "initial"
        error_marker = "initial"

        # Test 1: Success case - only try should modify variables
        try {
            success_marker = "try_executed"
        } catch (e) {
            success_marker = "catch_executed"  # Should NOT happen
        }

        # Test 2: Error case - only catch should modify variables
        try {
            error_marker = "try_started"
            x = 1 / 0
            error_marker = "try_completed"  # Should NOT happen
        } catch (e) {
            error_marker = "catch_executed"
        }

        output = "success:${success_marker},error:${error_marker}"
        return output
        """
        result = self.cy.run(program)
        assert "success:try_executed,error:catch_executed" in result

    def test_complex_nested_flow_with_counters(self):
        """Test complex nested execution flow with detailed counter tracking."""
        program = """
        # Use separate variables instead of nested dictionary access in interpolation
        outer_try_count = 0
        inner1_try_count = 0
        inner1_catch_count = 0
        inner2_try_count = 0
        inner2_catch_count = 0
        outer_catch_count = 0
        finally_count = 0

        try {
            outer_try_count = outer_try_count + 1

            # First inner try/catch - will succeed
            try {
                inner1_try_count = inner1_try_count + 1
                value1 = 42
            } catch (e1) {
                inner1_catch_count = inner1_catch_count + 1
            }

            # Second inner try/catch - will fail but be handled
            try {
                inner2_try_count = inner2_try_count + 1
                value2 = 1 / 0
            } catch (e2) {
                inner2_catch_count = inner2_catch_count + 1
            }

            # This should execute because all inner exceptions were handled
            final_value = "outer_completed"

        } catch (outer_e) {
            outer_catch_count = outer_catch_count + 1
        } finally {
            finally_count = finally_count + 1
        }

        output = "outer_try:${outer_try_count},inner1_try:${inner1_try_count},inner1_catch:${inner1_catch_count},inner2_try:${inner2_try_count},inner2_catch:${inner2_catch_count},outer_catch:${outer_catch_count},finally:${finally_count}"
        return output
        """
        result = self.cy.run(program)
        # Expected: outer_try:1, inner1_try:1, inner1_catch:0, inner2_try:1, inner2_catch:1, outer_catch:0, finally:1
        assert (
            "outer_try:1,inner1_try:1,inner1_catch:0,inner2_try:1,inner2_catch:1,outer_catch:0,finally:1"
            in result
        )
