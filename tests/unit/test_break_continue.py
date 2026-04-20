"""Comprehensive tests for break and continue statements.

Covers:
  - Basic break in while loops
  - Basic continue in while loops
  - Break in for-in loops
  - Continue in for-in loops
  - Nested loops: inner break doesn't affect outer
  - Nested loops: inner continue doesn't affect outer
  - Deeply nested loops (3 levels) with break at each level
  - Break inside if/elif/else branches
  - Continue inside if/elif/else branches
  - Break inside try/catch (finally still runs)
  - Continue inside try/catch
  - Break after accumulation (partial results preserved)
  - Continue with accumulator (skipped items excluded)
  - Break on first match (linear search pattern)
  - Continue to filter (filter pattern)
  - Nested for-in with break in inner loop
  - Nested for-in with continue in inner loop
  - Nested while-in-for and for-in-while combinations
  - Break/continue with indexed assignment
  - Compile-time: break outside loop is an error
  - Compile-time: continue outside loop is an error
"""

from __future__ import annotations

import pytest

from cy_language import Cy
from cy_language.errors import CompilerError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def cy() -> Cy:
    """Return a fresh Cy interpreter with native functions."""
    import cy_language.native_functions  # noqa: F401
    from cy_language.ui.tools import default_registry

    return Cy(tools=default_registry.get_tools_dict())


def run(program: str, input_data=None):
    return cy().run_native(program, input_data=input_data)


# ===================================================================
# Basic break
# ===================================================================


class TestBasicBreak:
    """Break in simple while and for-in loops."""

    def test_break_while_at_value(self):
        result = run("""\
i = 0
while (i < 100) {
    if (i == 5) {
        break
    }
    i += 1
}
return i
""")
        assert result == 5

    def test_break_while_first_iteration(self):
        result = run("""\
i = 0
while (i < 10) {
    break
    i += 1
}
return i
""")
        assert result == 0

    def test_break_while_never_triggers(self):
        """If condition never matches, loop runs to completion."""
        result = run("""\
i = 0
while (i < 5) {
    i += 1
}
return i
""")
        assert result == 5

    def test_break_for_in(self):
        result = run("""\
found = -1
for (item in [10, 20, 30, 40, 50]) {
    if (item == 30) {
        found = item
        break
    }
}
return found
""")
        assert result == 30

    def test_break_for_in_first_element(self):
        result = run("""\
count = 0
for (x in [1, 2, 3]) {
    break
    count += 1
}
return count
""")
        assert result == 0

    def test_break_for_in_preserves_accumulator(self):
        """Items before break are kept."""
        result = run("""\
collected = []
for (x in [1, 2, 3, 4, 5]) {
    if (x == 4) {
        break
    }
    collected = collected + [x]
}
return collected
""")
        assert result == [1, 2, 3]


# ===================================================================
# Basic continue
# ===================================================================


class TestBasicContinue:
    """Continue in simple while and for-in loops."""

    def test_continue_while_skip_odds(self):
        result = run("""\
evens = []
i = 0
while (i < 10) {
    i += 1
    if (i % 2 != 0) {
        continue
    }
    evens = evens + [i]
}
return evens
""")
        assert result == [2, 4, 6, 8, 10]

    def test_continue_while_skip_all(self):
        """Continue on every iteration — loop still terminates."""
        result = run("""\
count = 0
i = 0
while (i < 5) {
    i += 1
    continue
    count += 1
}
return {"i": i, "count": count}
""")
        assert result == {"i": 5, "count": 0}

    def test_continue_for_in_filter_odds(self):
        result = run("""\
odds = []
for (n in [1, 2, 3, 4, 5, 6, 7, 8]) {
    if (n % 2 == 0) {
        continue
    }
    odds = odds + [n]
}
return odds
""")
        assert result == [1, 3, 5, 7]

    def test_continue_for_in_skip_none(self):
        """No continues trigger — all items collected."""
        result = run("""\
all_items = []
for (x in [10, 20, 30]) {
    all_items = all_items + [x]
}
return all_items
""")
        assert result == [10, 20, 30]

    def test_continue_for_in_skip_all(self):
        """Continue on every iteration — empty result."""
        result = run("""\
collected = []
for (x in [1, 2, 3]) {
    continue
    collected = collected + [x]
}
return collected
""")
        assert result == []


# ===================================================================
# Nested loops — inner break/continue doesn't affect outer
# ===================================================================


class TestNestedLoops:
    """Inner loop break/continue must not leak to outer loop."""

    def test_inner_break_outer_continues(self):
        """Break in inner for-in; outer for-in runs all iterations."""
        result = run("""\
results = []
for (i in [1, 2, 3]) {
    for (j in [10, 20, 30, 40]) {
        if (j == 20) {
            break
        }
        results = results + [i * 100 + j]
    }
}
return results
""")
        # Inner loop breaks at j==20, so only j==10 per outer iteration
        assert result == [110, 210, 310]

    def test_inner_continue_outer_continues(self):
        """Continue in inner for-in; outer for-in runs all iterations."""
        result = run("""\
results = []
for (i in [1, 2, 3]) {
    for (j in [10, 20, 30]) {
        if (j == 20) {
            continue
        }
        results = results + [i * 100 + j]
    }
}
return results
""")
        # Inner loop skips j==20
        assert result == [110, 130, 210, 230, 310, 330]

    def test_outer_break_inner_unaffected(self):
        """Break in outer loop stops everything."""
        result = run("""\
results = []
outer_count = 0
for (i in [1, 2, 3, 4]) {
    if (i == 3) {
        break
    }
    for (j in [10, 20]) {
        results = results + [i * 100 + j]
    }
    outer_count += 1
}
return {"results": results, "outer_count": outer_count}
""")
        assert result == {
            "results": [110, 120, 210, 220],
            "outer_count": 2,
        }

    def test_outer_continue_inner_unaffected(self):
        """Continue in outer loop skips rest of outer body including inner loop."""
        result = run("""\
results = []
for (i in [1, 2, 3, 4]) {
    if (i == 2 or i == 4) {
        continue
    }
    for (j in [10, 20]) {
        results = results + [i * 100 + j]
    }
}
return results
""")
        # Outer skips i==2 and i==4
        assert result == [110, 120, 310, 320]

    def test_nested_while_loops(self):
        """Break in inner while, outer while continues."""
        result = run("""\
results = []
i = 0
while (i < 3) {
    j = 0
    while (j < 5) {
        if (j == 2) {
            break
        }
        results = results + [i * 10 + j]
        j += 1
    }
    i += 1
}
return results
""")
        assert result == [0, 1, 10, 11, 20, 21]

    def test_nested_for_in_while(self):
        """For-in outer, while inner with break."""
        result = run("""\
results = []
for (x in [100, 200, 300]) {
    y = 1
    while (y <= 10) {
        if (y > 3) {
            break
        }
        results = results + [x + y]
        y += 1
    }
}
return results
""")
        assert result == [101, 102, 103, 201, 202, 203, 301, 302, 303]

    def test_nested_while_for_in(self):
        """While outer, for-in inner with continue."""
        result = run("""\
results = []
i = 0
while (i < 3) {
    for (x in [1, 2, 3, 4]) {
        if (x % 2 == 0) {
            continue
        }
        results = results + [i * 10 + x]
    }
    i += 1
}
return results
""")
        assert result == [1, 3, 11, 13, 21, 23]


# ===================================================================
# Deeply nested (3 levels)
# ===================================================================


class TestDeeplyNested:
    """Three levels of nesting with break/continue at various levels."""

    def test_break_at_innermost(self):
        result = run("""\
results = []
for (a in [1, 2]) {
    for (b in [10, 20]) {
        for (c in [100, 200, 300]) {
            if (c == 200) {
                break
            }
            results = results + [a + b + c]
        }
    }
}
return results
""")
        # c breaks at 200, so only c=100 for each (a,b) combo
        # a=1,b=10: 111 | a=1,b=20: 121 | a=2,b=10: 112 | a=2,b=20: 122
        assert result == [111, 121, 112, 122]

    def test_continue_at_innermost(self):
        result = run("""\
results = []
for (a in [1, 2]) {
    for (b in [10, 20]) {
        for (c in [100, 200, 300]) {
            if (c == 200) {
                continue
            }
            results = results + [a + b + c]
        }
    }
}
return results
""")
        # c skips 200, keeps 100 and 300
        # a=1,b=10: 111,311 | a=1,b=20: 121,321 | a=2,b=10: 112,312 | a=2,b=20: 122,322
        assert result == [111, 311, 121, 321, 112, 312, 122, 322]

    def test_break_at_middle_level(self):
        result = run("""\
results = []
for (a in [1, 2]) {
    for (b in [10, 20, 30]) {
        if (b == 20) {
            break
        }
        for (c in [100, 200]) {
            results = results + [a + b + c]
        }
    }
}
return results
""")
        # b breaks at 20, so only b=10 per a
        # a=1,b=10: 111,211 | a=2,b=10: 112,212
        assert result == [111, 211, 112, 212]

    def test_mixed_break_continue_levels(self):
        """Continue at middle, break at inner."""
        result = run("""\
results = []
for (a in [1, 2]) {
    for (b in [10, 20, 30]) {
        if (b == 20) {
            continue
        }
        for (c in [100, 200, 300]) {
            if (c == 200) {
                break
            }
            results = results + [a + b + c]
        }
    }
}
return results
""")
        # b skips 20; c breaks at 200 (only c=100)
        # a=1,b=10: 111 | a=1,b=30: 131 | a=2,b=10: 112 | a=2,b=30: 132
        assert result == [111, 131, 112, 132]


# ===================================================================
# Break/continue inside conditionals
# ===================================================================


class TestBreakContinueInConditionals:
    """Break/continue inside if/elif/else branches."""

    def test_break_in_if(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x == 3) {
        break
    }
    result = result + [x]
}
return result
""")
        assert result == [1, 2]

    def test_break_in_elif(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x == 10) {
        result = result + [999]
    } elif (x == 3) {
        break
    }
    result = result + [x]
}
return result
""")
        assert result == [1, 2]

    def test_break_in_else(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x < 3) {
        result = result + [x]
    } else {
        break
    }
}
return result
""")
        assert result == [1, 2]

    def test_continue_in_if(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x == 3) {
        continue
    }
    result = result + [x]
}
return result
""")
        assert result == [1, 2, 4, 5]

    def test_continue_in_elif(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x == 10) {
        result = result + [999]
    } elif (x % 2 == 0) {
        continue
    }
    result = result + [x]
}
return result
""")
        assert result == [1, 3, 5]

    def test_continue_in_else(self):
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5]) {
    if (x <= 2) {
        result = result + [x * 10]
    } else {
        continue
    }
    result = result + [x]
}
return result
""")
        # x=1: if branch → [10, 1]; x=2: if branch → [20, 2]; x=3,4,5: else → continue
        assert result == [10, 1, 20, 2]


# ===================================================================
# Break/continue inside try/catch
# ===================================================================


class TestBreakContinueInTryCatch:
    """Break/continue inside try/catch — finally must still run."""

    def test_break_in_try_finally_runs(self):
        result = run("""\
log_entries = []
for (x in [1, 2, 3, 4, 5]) {
    try {
        if (x == 3) {
            break
        }
        log_entries = log_entries + ["processed_" + str(x)]
    } catch (e) {
        log_entries = log_entries + ["error"]
    } finally {
        log_entries = log_entries + ["finally_" + str(x)]
    }
}
return log_entries
""")
        assert result == [
            "processed_1",
            "finally_1",
            "processed_2",
            "finally_2",
            "finally_3",  # finally runs even though break fired
        ]

    def test_continue_in_try_finally_runs(self):
        result = run("""\
log_entries = []
for (x in [1, 2, 3, 4]) {
    try {
        if (x == 2 or x == 3) {
            continue
        }
        log_entries = log_entries + ["processed_" + str(x)]
    } catch (e) {
        log_entries = log_entries + ["error"]
    } finally {
        log_entries = log_entries + ["finally_" + str(x)]
    }
}
return log_entries
""")
        assert result == [
            "processed_1",
            "finally_1",
            "finally_2",  # continue fired, but finally still runs
            "finally_3",  # continue fired, but finally still runs
            "processed_4",
            "finally_4",
        ]


# ===================================================================
# Break/continue with indexed assignment
# ===================================================================


class TestBreakContinueWithIndexedAssign:
    """Break/continue interacting with indexed assignment."""

    def test_break_with_indexed_assign(self):
        """Build partial array, break before completion."""
        result = run("""\
arr = [0, 0, 0, 0, 0]
i = 0
while (i < 5) {
    if (i == 3) {
        break
    }
    arr[i] = i * i
    i += 1
}
return arr
""")
        assert result == [0, 1, 4, 0, 0]

    def test_continue_with_indexed_assign(self):
        """Skip certain indices via continue."""
        result = run("""\
arr = [0, 0, 0, 0, 0]
i = 0
while (i < 5) {
    if (i == 1 or i == 3) {
        i += 1
        continue
    }
    arr[i] = i * 10
    i += 1
}
return arr
""")
        assert result == [0, 0, 20, 0, 40]


# ===================================================================
# Algorithmic patterns using break/continue
# ===================================================================


class TestAlgorithmicPatterns:
    """Real algorithms that benefit from break/continue."""

    def test_linear_search_with_break(self):
        """Find first occurrence using break."""
        result = run("""\
items = ["apple", "banana", "cherry", "date", "elderberry"]
target = "cherry"
found_idx = -1
idx = 0
for (item in items) {
    if (item == target) {
        found_idx = idx
        break
    }
    idx += 1
}
return found_idx
""")
        assert result == 2

    def test_filter_with_continue(self):
        """Filter items using continue."""
        result = run("""\
numbers = [15, 3, 8, 22, 7, 41, 12, 5, 19, 2]
big_odds = []
for (n in numbers) {
    if (n < 10) {
        continue
    }
    if (n % 2 == 0) {
        continue
    }
    big_odds = big_odds + [n]
}
return big_odds
""")
        assert result == [15, 41, 19]

    def test_find_first_duplicate(self):
        """Find first duplicate using nested loop with break."""
        result = run("""\
items = [3, 1, 4, 1, 5, 9, 2, 6]
duplicate = -1
found = False
i = 0
while (i < len(items) and not found) {
    j = i + 1
    while (j < len(items)) {
        if (items[i] == items[j]) {
            duplicate = items[i]
            found = True
            break
        }
        j += 1
    }
    i += 1
}
return duplicate
""")
        assert result == 1

    def test_matrix_find_value(self):
        """Search a 2D matrix for a value, break out of inner loop."""
        result = run("""\
matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
]
target = 5
location = {"row": -1, "col": -1}
row = 0
while (row < len(matrix)) {
    col = 0
    while (col < len(matrix[row])) {
        if (matrix[row][col] == target) {
            location = {"row": row, "col": col}
            break
        }
        col += 1
    }
    row += 1
}
return location
""")
        assert result == {"row": 1, "col": 1}

    def test_process_until_sentinel(self):
        """Process items until a sentinel value."""
        result = run("""\
data = [10, 20, 30, -1, 40, 50]
total = 0
for (val in data) {
    if (val == -1) {
        break
    }
    total += val
}
return total
""")
        assert result == 60

    def test_skip_invalid_entries(self):
        """Skip null/invalid entries using continue."""
        result = run("""\
entries = [1, null, 3, null, 5, null, 7]
valid_sum = 0
count = 0
for (e in entries) {
    if (e == null) {
        continue
    }
    valid_sum += e
    count += 1
}
return {"sum": valid_sum, "count": count}
""")
        assert result == {"sum": 16, "count": 4}

    def test_bubble_sort_with_break(self):
        """Bubble sort using break for early exit (optimized)."""
        result = run("""\
arr = [5, 3, 8, 1, 2]
n = len(arr)
i = 0
while (i < n - 1) {
    swapped = False
    j = 0
    while (j < n - i - 1) {
        if (arr[j] > arr[j + 1]) {
            tmp = arr[j]
            arr[j] = arr[j + 1]
            arr[j + 1] = tmp
            swapped = True
        }
        j += 1
    }
    if (not swapped) {
        break
    }
    i += 1
}
return arr
""")
        assert result == [1, 2, 3, 5, 8]


# ===================================================================
# Compile-time validation
# ===================================================================


class TestCompileTimeErrors:
    """Break/continue outside a loop must be a compile-time error."""

    def test_break_outside_loop(self):
        with pytest.raises(CompilerError, match="break.*only.*inside.*loop"):
            run("break\nreturn 1")

    def test_continue_outside_loop(self):
        with pytest.raises(CompilerError, match="continue.*only.*inside.*loop"):
            run("continue\nreturn 1")

    def test_break_in_if_outside_loop(self):
        with pytest.raises(CompilerError, match="break.*only.*inside.*loop"):
            run("""\
if (True) {
    break
}
return 1
""")

    def test_continue_in_if_outside_loop(self):
        with pytest.raises(CompilerError, match="continue.*only.*inside.*loop"):
            run("""\
if (True) {
    continue
}
return 1
""")

    def test_break_inside_loop_is_valid(self):
        """Sanity: break inside loop compiles fine."""
        result = run("""\
for (x in [1, 2, 3]) {
    break
}
return "ok"
""")
        assert result == "ok"

    def test_break_in_finally_is_compile_error(self):
        """break inside finally would suppress in-flight control flow."""
        with pytest.raises(CompilerError, match="break.*cannot.*finally"):
            run("""\
for (x in [1, 2, 3]) {
    try {
        x = x + 1
    } catch (e) {
        x = 0
    } finally {
        break
    }
}
return 1
""")

    def test_continue_in_finally_is_compile_error(self):
        """continue inside finally would suppress in-flight control flow."""
        with pytest.raises(CompilerError, match="continue.*cannot.*finally"):
            run("""\
for (x in [1, 2, 3]) {
    try {
        x = x + 1
    } catch (e) {
        x = 0
    } finally {
        continue
    }
}
return 1
""")

    def test_break_in_try_body_is_valid(self):
        """break in try body (not finally) is fine."""
        result = run("""\
for (x in [1, 2, 3]) {
    try {
        break
    } catch (e) {
        x = 0
    }
}
return "ok"
""")
        assert result == "ok"

    def test_break_in_catch_body_is_valid(self):
        """break in catch body (not finally) is fine."""
        result = run("""\
for (x in [1, 2, 3]) {
    try {
        x = 1 / 0
    } catch (e) {
        break
    }
}
return "ok"
""")
        assert result == "ok"

    def test_continue_inside_loop_is_valid(self):
        """Sanity: continue inside loop compiles fine."""
        result = run("""\
for (x in [1, 2, 3]) {
    continue
}
return "ok"
""")
        assert result == "ok"

    def test_break_in_outer_finally_after_nested_try_catch_finally(self):
        """Nested try/catch/finally must not reset _in_finally for outer finally."""
        with pytest.raises(CompilerError, match="break.*cannot.*finally"):
            run("""\
for (x in [1, 2, 3]) {
    try {
        result = 1
    } catch (e) {
        a = 1
    } finally {
        try {
            b = 1
        } catch (e2) {
            c = 1
        } finally {
            d = 2
        }
        break
    }
}
return 1
""")

    def test_continue_in_outer_finally_after_nested_try_catch_finally(self):
        """Nested try/catch/finally must not reset _in_finally for outer finally."""
        with pytest.raises(CompilerError, match="continue.*cannot.*finally"):
            run("""\
for (x in [1, 2, 3]) {
    try {
        result = 1
    } catch (e) {
        a = 1
    } finally {
        try {
            b = 1
        } catch (e2) {
            c = 1
        } finally {
            d = 2
        }
        continue
    }
}
return 1
""")

    def test_break_in_catch_after_nested_finally_is_valid(self):
        """break in catch body (not finally) is valid even after nested finally."""
        result = run("""\
for (x in [1, 2, 3]) {
    try {
        result = 1
    } catch (e) {
        try {
            b = 1
        } catch (e2) {
            c = 1
        } finally {
            d = 2
        }
        break
    }
}
return "ok"
""")
        assert result == "ok"

    def test_break_in_for_loop_inside_finally_is_valid(self):
        """A loop inside finally is a fresh scope — break targets that loop."""
        result = run("""\
x = 0
try {
    x = 1
} catch (e) {
    x = 2
} finally {
    for (i in [10, 20, 30]) {
        if (i == 20) {
            break
        }
    }
}
return x
""")
        assert result == 1

    def test_continue_in_while_loop_inside_finally_is_valid(self):
        """A while loop inside finally is a fresh scope — continue targets it."""
        result = run("""\
total = 0
try {
    total = 100
} catch (e) {
    total = 0
} finally {
    i = 0
    while (i < 5) {
        i += 1
        if (i == 3) {
            continue
        }
        total += i
    }
}
return total
""")
        # total = 100 + (1+2+4+5) = 112  (skips 3)
        assert result == 112

    def test_break_after_try_catch_finally_block_is_valid(self):
        """break outside any finally block is valid even after nested finally."""
        result = run("""\
for (x in [1, 2, 3]) {
    try {
        result = 1
    } catch (e) {
        a = 1
    } finally {
        try {
            b = 1
        } catch (e2) {
            c = 1
        } finally {
            d = 2
        }
    }
    break
}
return "ok"
""")
        assert result == "ok"


# ===================================================================
# Edge cases
# ===================================================================


class TestEdgeCases:
    """Edge cases and corner scenarios."""

    def test_break_in_single_element_loop(self):
        result = run("""\
for (x in [42]) {
    break
}
return x
""")
        assert result == 42

    def test_continue_in_single_element_loop(self):
        result = run("""\
collected = []
for (x in [42]) {
    continue
    collected = collected + [x]
}
return collected
""")
        assert result == []

    def test_break_empty_loop(self):
        """Break in condition that never runs (empty list)."""
        result = run("""\
count = 0
for (x in []) {
    break
    count += 1
}
return count
""")
        assert result == 0

    def test_break_and_continue_same_loop(self):
        """Both break and continue in the same loop body."""
        result = run("""\
result = []
for (x in [1, 2, 3, 4, 5, 6, 7, 8]) {
    if (x % 2 == 0) {
        continue
    }
    if (x > 5) {
        break
    }
    result = result + [x]
}
return result
""")
        # Skip evens (continue), stop at 7 (break). Collect: 1, 3, 5
        assert result == [1, 3, 5]

    def test_break_with_while_condition_still_true(self):
        """Break exits even though condition is still true."""
        result = run("""\
i = 0
while (True) {
    if (i >= 3) {
        break
    }
    i += 1
}
return i
""")
        assert result == 3

    def test_nested_break_both_levels(self):
        """Break in both inner and outer loops, independently."""
        result = run("""\
results = []
i = 0
while (i < 10) {
    j = 0
    while (j < 10) {
        if (j >= 2) {
            break
        }
        results = results + [i * 10 + j]
        j += 1
    }
    if (i >= 3) {
        break
    }
    i += 1
}
return results
""")
        # j breaks at 2, i breaks at 3
        assert result == [0, 1, 10, 11, 20, 21, 30, 31]

    def test_continue_does_not_skip_for_in_iteration_advance(self):
        """Critical: continue in for-in must advance to next item, not repeat."""
        result = run("""\
visited = []
for (x in [10, 20, 30, 40]) {
    visited = visited + [x]
    continue
}
return visited
""")
        # All items visited even though continue fires every time
        assert result == [10, 20, 30, 40]
