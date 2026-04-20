"""
Comprehensive tests for try-catch bug report investigation.

This test file investigates the claims in CY_TRY_CATCH_BUG_REPORT.md:
1. Variables assigned in try blocks don't persist
2. Catch blocks execute even when no error occurs
3. Dictionary access within try-catch fails mysteriously

These tests aim to either:
- Reproduce the bug with a minimal test case
- Prove the bug doesn't exist in the core implementation
- Identify specific edge cases that trigger the behavior
"""

from cy_language import Cy


class TestTryCatchVariablePersistence:
    """Test Group 1: Variable assignments in try blocks should persist."""

    def test_simple_variable_assignment_in_try(self):
        """Test that basic variable assignment in try block persists."""
        program = """
result = False
try {
    result = True
} catch (e) {
    result = False
}
output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Variable assigned in try block should persist"

    def test_variable_assignment_with_condition_in_try(self):
        """Test variable assignment inside conditional within try block."""
        program = """
result = False
x = 10
try {
    if (x == 10) {
        result = True
    }
} catch (e) {
    result = False
}
output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Variable assigned in try>if should persist"

    def test_dictionary_assignment_in_try(self):
        """Test dictionary assignment in try block persists."""
        program = """
user_details = {}
try {
    user_details = {"name": "Alice", "email": "alice@example.com"}
} catch (e) {
    user_details = {}
}
output = user_details
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "Alice" in output, "Dictionary assigned in try should persist"
        assert "alice@example.com" in output, (
            "Dictionary assigned in try should persist"
        )

    def test_multiple_variables_in_try(self):
        """Test multiple variable assignments in try block."""
        program = """
var1 = False
var2 = False
var3 = False
try {
    var1 = True
    var2 = True
    var3 = True
} catch (e) {
    var1 = False
}
output = {"var1": var1, "var2": var2, "var3": var3}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "true" in output, "Multiple variables in try should persist"
        # All three should be true
        assert output.count("true") == 3, "All variables should be true"


class TestTryCatchDictionaryAccess:
    """Test Group 2: Dictionary access within try-catch blocks."""

    def test_dictionary_access_no_error(self):
        """Test accessing existing dictionary key in try block."""
        program = """
test_data = {"value": 42}
result = False
try {
    val = test_data["value"]
    if (val == 42) {
        result = True
    }
} catch (e) {
    result = False
}
output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Dictionary access should succeed without error"

    def test_nested_dictionary_access_in_try(self):
        """Test nested dictionary access similar to bug report."""
        program = """
user_result = {
    "data": {
        "entries": [
            {
                "attributes": {
                    "cn": ["jdoe"],
                    "mail": ["jdoe@example.com"]
                }
            }
        ]
    }
}

user_found = False
try {
    entries = user_result["data"]["entries"]
    if (len(entries) > 0) {
        user_found = True
    }
} catch (e) {
    user_found = False
}

output = user_found
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", (
            "Nested dictionary access should succeed and persist variable"
        )

    def test_dictionary_access_with_assignment_in_try(self):
        """Test the exact pattern from the bug report."""
        program = """
user_result = {
    "data": {
        "entries": [
            {
                "attributes": {
                    "cn": ["jdoe"],
                    "mail": ["jdoe@example.com"]
                },
                "dn": "cn=jdoe,ou=users,dc=example,dc=com"
            }
        ]
    },
    "total_objects": 1
}

user_found = False
user_details = {}

try {
    entries = user_result["data"]["entries"]
    if (len(entries) > 0) {
        user_found = True
        entry = entries[0]
        user_details = {
            "username": entry["attributes"]["cn"][0],
            "email": entry["attributes"]["mail"][0]
        }
    }
} catch (e) {
    user_found = False
}

output = {"user_found": user_found, "user_details": user_details}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "true" in output, "user_found should be true"
        assert "jdoe" in output, "username should be in user_details"
        assert "jdoe@example.com" in output, "email should be in user_details"


class TestTryCatchErrorConditions:
    """Test Group 3: Verify catch block only executes on actual errors."""

    def test_catch_block_does_not_execute_on_success(self):
        """Verify catch block doesn't run when no error occurs."""
        program = """
catch_executed = False
try_executed = False

try {
    try_executed = True
} catch (e) {
    catch_executed = True
}

output = {"try": try_executed, "catch": catch_executed}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert '"try": true' in output, "Try block should execute"
        assert '"catch": false' in output, "Catch block should NOT execute"

    def test_catch_block_executes_on_error(self):
        """Verify catch block DOES execute on actual error."""
        program = """
catch_executed = False

try {
    x = 10 / 0  # Division by zero
} catch (e) {
    catch_executed = True
}

output = catch_executed
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Catch block should execute on error"

    def test_catch_block_receives_error_variable(self):
        """Verify catch block receives error information."""
        program = """
error_message = ""

try {
    x = 10 / 0
} catch (e) {
    error_message = "caught"
}

output = error_message
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == '"caught"', "Catch block should execute and set variable"


class TestTryCatchBugReportMinimalReproduction:
    """Test Group 4: Exact minimal reproduction from bug report."""

    def test_bug_report_minimal_case(self):
        """The exact minimal test case from the bug report."""
        program = """
test_data = {"value": 42}

# Test 1: Without try-catch
result_without = False
if (test_data["value"] == 42) {
    result_without = True
}

# Test 2: With try-catch
result_with = False
try {
    if (test_data["value"] == 42) {
        result_with = True
    }
} catch (e) {
    result_with = False
}

output = {
    "without_try_catch": result_without,
    "with_try_catch": result_with
}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)

        # Both should be True
        assert '"without_try_catch": true' in output, "Without try-catch should be true"
        assert '"with_try_catch": true' in output, (
            "With try-catch should ALSO be true - if this fails, bug is confirmed"
        )

    def test_bug_report_full_scenario(self):
        """Full scenario from bug report with simulated LDAP result."""
        program = """
# Simulate LDAP query result
user_result = {
    "data": {
        "entries": [
            {
                "attributes": {
                    "cn": ["jdoe"],
                    "mail": ["jdoe@example.com"]
                },
                "dn": "cn=jdoe,ou=users,dc=example,dc=com"
            }
        ]
    },
    "total_objects": 1
}

# The pattern from the bug report
user_found = False
user_details = {}

try {
    entries = user_result["data"]["entries"]
    if (len(entries) > 0) {
        user_found = True
        entry = entries[0]
        user_details = {
            "username": entry["attributes"]["cn"][0],
            "email": entry["attributes"]["mail"][0]
        }
    }
} catch (e) {
    user_found = False
}

# Check if user was found
if (not user_found) {
    output = {
        "user_found": False,
        "message": "User not found"
    }
} else {
    output = {
        "user_found": True,
        "user_details": user_details
    }
}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)

        # Should find the user
        assert '"user_found": true' in output, (
            "Should find user - if false, bug is confirmed"
        )
        assert "jdoe" in output, "Should have username"
        assert "jdoe@example.com" in output, "Should have email"


class TestTryCatchEdgeCases:
    """Test Group 5: Edge cases that might trigger the reported behavior."""

    def test_nested_try_catch(self):
        """Test nested try-catch blocks."""
        program = """
outer_result = False
inner_result = False

try {
    outer_result = True
    try {
        inner_result = True
    } catch (inner_e) {
        inner_result = False
    }
} catch (outer_e) {
    outer_result = False
}

output = {"outer": outer_result, "inner": inner_result}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert '"outer": true' in output, "Outer should be true"
        assert '"inner": true' in output, "Inner should be true"

    def test_try_catch_in_loop(self):
        """Test try-catch inside loop (from existing test)."""
        program = """
items = [1, 2, 0, 4]
results = []
for (item in items) {
    try {
        result = 10 / item
        results = results + [result]
    } catch (e) {
        results = results + ["error"]
    }
}
output = results
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "10" in output, "First division should succeed"
        assert "5" in output, "Second division should succeed"
        assert "error" in output, "Third division should catch error"
        assert "2.5" in output, "Fourth division should succeed"


class TestTryCatchWithEmptyResults:
    """Test Group 6: Empty results that might be confused with errors."""

    def test_empty_list_not_error(self):
        """Test that empty results don't trigger catch block."""
        program = """
user_result = {
    "data": {
        "entries": []
    },
    "total_objects": 0
}

user_found = False
catch_executed = False

try {
    entries = user_result["data"]["entries"]
    if (len(entries) > 0) {
        user_found = True
    }
} catch (e) {
    catch_executed = True
    user_found = False
}

output = {"user_found": user_found, "catch_executed": catch_executed}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert '"user_found": false' in output, "Should be false (no users found)"
        assert '"catch_executed": false' in output, (
            "Catch should NOT execute - empty list is not an error"
        )

    def test_zero_length_is_not_error(self):
        """Test that len() returning 0 doesn't trigger catch."""
        program = """
empty_data = []
length_result = -1
catch_triggered = False

try {
    length_result = len(empty_data)
} catch (e) {
    catch_triggered = True
}

output = {"length": length_result, "catch": catch_triggered}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert '"length": 0' in output, "Length should be 0"
        assert '"catch": false' in output, "Catch should not trigger"

    def test_false_condition_not_error(self):
        """Test that false conditionals don't prevent variable persistence."""
        program = """
data = {"value": 10}
result = False

try {
    if (data["value"] == 999) {  # This is false, but not an error
        result = True
    }
    # result should still be False, not because of catch
} catch (e) {
    result = "error"
}

output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "false", "Should be false from initial value, not from catch"


class TestTryCatchWithObjectOperations:
    """Test Group 7: Specific object/dictionary operations that might fail."""

    def test_array_access_in_try(self):
        """Test array indexing in try block."""
        program = """
arr = [1, 2, 3]
result = False

try {
    val = arr[0]
    if (val == 1) {
        result = True
    }
} catch (e) {
    result = False
}

output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Array access should succeed"

    def test_deeply_nested_object_access(self):
        """Test very deep nesting like in LDAP result."""
        program = """
deep = {
    "level1": {
        "level2": {
            "level3": {
                "level4": {
                    "value": [42]
                }
            }
        }
    }
}

found = False
try {
    val = deep["level1"]["level2"]["level3"]["level4"]["value"][0]
    if (val == 42) {
        found = True
    }
} catch (e) {
    found = False
}

output = found
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "true", "Deep nesting access should succeed"

    def test_mixed_operations_in_try(self):
        """Test multiple different operations in try block."""
        program = """
data = {
    "users": [
        {"name": "Alice", "scores": [90, 85, 95]},
        {"name": "Bob", "scores": [80, 75, 85]}
    ]
}

success = False
alice_avg = 0

try {
    users = data["users"]
    alice = users[0]
    scores = alice["scores"]
    total = scores[0] + scores[1] + scores[2]
    alice_avg = total / 3
    if (alice_avg >= 85) {
        success = True
    }
} catch (e) {
    success = False
}

output = {"success": success, "avg": alice_avg}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert '"success": true' in output, "Should succeed"
        assert "90" in output, "Should calculate average correctly"


class TestTryCatchWithNotOperator:
    """Test Group 8: Testing 'not' operator with try-catch (from bug report pattern)."""

    def test_not_operator_with_try_catch_variable(self):
        """Test the exact 'if (not user_found)' pattern from bug report."""
        program = """
user_found = False

try {
    user_found = True
} catch (e) {
    user_found = False
}

# Bug report uses this pattern
if (not user_found) {
    output = "FAIL"
} else {
    output = "SUCCESS"
}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == '"SUCCESS"', (
            "not operator should work correctly with try-catch variable"
        )

    def test_not_operator_with_conditional_assignment(self):
        """Test 'not' with conditional assignment in try block."""
        program = """
data = {"exists": True}
found = False

try {
    if (data["exists"]) {
        found = True
    }
} catch (e) {
    found = False
}

result = ""
if (not found) {
    result = "NOT_FOUND"
} else {
    result = "FOUND"
}

output = result
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == '"FOUND"', (
            "Should be FOUND after try-catch with 'not' operator"
        )

    def test_early_exit_with_not_pattern(self):
        """Test early exit pattern from bug report."""
        program = """
entries = [1, 2, 3]
user_found = False

try {
    if (len(entries) > 0) {
        user_found = True
    }
} catch (e) {
    user_found = False
}

# Early exit pattern from bug report
if (not user_found) {
    output = {"status": "not_found"}
} else {
    output = {"status": "found", "count": len(entries)}
}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "found" in output, "Status should be found"
        assert "3" in output, "Count should be 3"


class TestTryCatchWithMultipleConditions:
    """Test Group 9: Multiple nested conditions in try-catch."""

    def test_multiple_if_statements_in_try(self):
        """Test multiple sequential if statements in try block."""
        program = """
data = {"a": 1, "b": 2, "c": 3}
a_ok = False
b_ok = False
c_ok = False

try {
    if (data["a"] == 1) {
        a_ok = True
    }
    if (data["b"] == 2) {
        b_ok = True
    }
    if (data["c"] == 3) {
        c_ok = True
    }
} catch (e) {
    a_ok = False
}

output = {"a": a_ok, "b": b_ok, "c": c_ok}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        # All three should be True
        assert output.count("true") == 3, "All three conditions should be true"

    def test_nested_if_with_multiple_assignments(self):
        """Test nested if with multiple variable assignments."""
        program = """
user_result = {
    "data": {
        "entries": [
            {"attributes": {"mail": ["test@example.com"], "cn": ["testuser"]}}
        ]
    }
}

email = ""
username = ""
success = False

try {
    entries = user_result["data"]["entries"]
    if (len(entries) > 0) {
        entry = entries[0]
        if (entry["attributes"]) {
            email = entry["attributes"]["mail"][0]
            username = entry["attributes"]["cn"][0]
            success = True
        }
    }
} catch (e) {
    success = False
}

output = {"email": email, "username": username, "success": success}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "test@example.com" in output, "Email should be extracted"
        assert "testuser" in output, "Username should be extracted"
        assert '"success": true' in output, "Success should be true"


class TestTryCatchVariableReassignment:
    """Test Group 10: Variable reassignment patterns in try-catch."""

    def test_reassignment_in_try_persists(self):
        """Test that reassigning existing variable in try persists."""
        program = """
status = "initial"

try {
    status = "processing"
    status = "completed"
} catch (e) {
    status = "error"
}

output = status
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == '"completed"', "Final reassignment should persist"

    def test_reassignment_in_nested_blocks(self):
        """Test reassignment in nested if inside try."""
        program = """
value = 0

try {
    value = 1
    if (True) {
        value = 2
        if (True) {
            value = 3
        }
    }
} catch (e) {
    value = -1
}

output = value
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert output == "3", "Deepest reassignment should persist"

    def test_multiple_variables_reassignment(self):
        """Test multiple variables being reassigned in try."""
        program = """
a = 1
b = 2
c = 3

try {
    a = 10
    b = 20
    c = 30
} catch (e) {
    a = -1
    b = -1
    c = -1
}

output = {"a": a, "b": b, "c": c}
return output
"""
        interpreter = Cy()
        output = interpreter.run(program)
        assert "10" in output, "a should be 10"
        assert "20" in output, "b should be 20"
        assert "30" in output, "c should be 30"


# Summary test to run all scenarios
def test_try_catch_bug_investigation_summary():
    """
    Meta-test: If this passes, we can provide a comprehensive report.

    This test documents what we're testing:
    1. Variable persistence in try blocks
    2. Dictionary access in try blocks
    3. Catch block execution only on errors
    4. Exact bug report scenarios
    5. Edge cases
    6. Complex object operations

    If ALL tests pass, the bug may be:
    - Environment-specific (Backend-Y, MCP, async execution)
    - Related to specific tool call results
    - A race condition in async execution
    - Not a core try-catch bug

    If ANY test fails, we've reproduced the bug in core Cy.
    """
    # This test is just for documentation
    assert True, "See test file for comprehensive try-catch investigation"
