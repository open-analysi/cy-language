"""Algorithmic correctness tests for the Cy language.

Each test implements a well-known algorithm purely in Cy and validates
its output against a known-correct Python reference.  A failure means
the Cy runtime produced an incorrect result — i.e. a language bug.

Algorithms covered:
  - Bubble sort
  - Selection sort
  - Insertion sort
  - Binary search (iterative)
  - Fibonacci (iterative)
  - FizzBuzz
  - Two-sum (brute force)
  - Matrix transpose
  - Caesar cipher (encode + decode)
  - Frequency counter
  - Manual list reversal
  - GCD (Euclidean, iterative)
  - Palindrome check
  - Running / cumulative sum
  - Sieve of Eratosthenes (iterative)
  - Flatten nested lists (one level)
"""

from __future__ import annotations

import math

import pytest

from cy_language import Cy

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def cy() -> Cy:
    """Return a fresh Cy interpreter with native functions."""
    import cy_language.native_functions  # noqa: F401 — registers builtins
    from cy_language.ui.tools import default_registry

    return Cy(tools=default_registry.get_tools_dict())


def run(program: str, input_data=None):
    """Run a Cy program and return a native Python result."""
    return cy().run_native(program, input_data=input_data)


# ===================================================================
# Sorting
# ===================================================================


class TestBubbleSort:
    """Bubble sort using indexed assignment (in-place swap)."""

    PROGRAM = """\
arr = input.arr
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
        i = n
    } else {
        i += 1
    }
}
return arr
"""

    @pytest.mark.parametrize(
        "arr",
        [
            [],
            [1],
            [1, 2, 3],
            [3, 2, 1],
            [5, 3, 8, 6, 2],
            [4, 4, 4, 4],
            [-3, 0, -1, 2, -5],
            [10, 9, 8, 7, 6, 5, 4, 3, 2, 1],
            [1, 1, 2, 2, 3, 3],
        ],
    )
    def test_sorts_correctly(self, arr):
        result = run(self.PROGRAM, {"arr": list(arr)})
        assert result == sorted(arr)


class TestSelectionSort:
    """Selection sort — find minimum of unsorted region, swap to front."""

    PROGRAM = """\
arr = input.arr
n = len(arr)
i = 0
while (i < n) {
    min_idx = i
    j = i + 1
    while (j < n) {
        if (arr[j] < arr[min_idx]) {
            min_idx = j
        }
        j += 1
    }
    if (min_idx != i) {
        tmp = arr[i]
        arr[i] = arr[min_idx]
        arr[min_idx] = tmp
    }
    i += 1
}
return arr
"""

    @pytest.mark.parametrize(
        "arr",
        [
            [],
            [1],
            [2, 1],
            [5, 3, 8, 6, 2],
            [9, 7, 5, 3, 1],
            [1, 1, 1],
        ],
    )
    def test_sorts_correctly(self, arr):
        result = run(self.PROGRAM, {"arr": list(arr)})
        assert result == sorted(arr)


class TestInsertionSort:
    """Insertion sort — shift elements right to make room for key."""

    PROGRAM = """\
arr = input.arr
n = len(arr)
i = 1
while (i < n) {
    key = arr[i]
    j = i - 1
    while (j >= 0 and arr[j] > key) {
        arr[j + 1] = arr[j]
        j -= 1
    }
    arr[j + 1] = key
    i += 1
}
return arr
"""

    @pytest.mark.parametrize(
        "arr",
        [
            [],
            [42],
            [1, 2, 3, 4, 5],
            [5, 4, 3, 2, 1],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [-1, -5, 0, 3, -2],
        ],
    )
    def test_sorts_correctly(self, arr):
        result = run(self.PROGRAM, {"arr": list(arr)})
        assert result == sorted(arr)


# ===================================================================
# Searching
# ===================================================================


class TestBinarySearch:
    """Iterative binary search on a sorted array."""

    PROGRAM = """\
arr = input.arr
target = input.target
low = 0
high = len(arr) - 1
found = -1

while (low <= high and found == -1) {
    mid = int((low + high) / 2)
    if (arr[mid] == target) {
        found = mid
    } elif (arr[mid] < target) {
        low = mid + 1
    } else {
        high = mid - 1
    }
}
return found
"""

    def test_finds_element(self):
        assert run(self.PROGRAM, {"arr": [1, 3, 5, 7, 9], "target": 5}) == 2

    def test_finds_first_element(self):
        assert run(self.PROGRAM, {"arr": [1, 3, 5, 7, 9], "target": 1}) == 0

    def test_finds_last_element(self):
        assert run(self.PROGRAM, {"arr": [1, 3, 5, 7, 9], "target": 9}) == 4

    def test_not_found(self):
        assert run(self.PROGRAM, {"arr": [1, 3, 5, 7, 9], "target": 4}) == -1

    def test_empty_array(self):
        assert run(self.PROGRAM, {"arr": [], "target": 1}) == -1

    def test_single_element_found(self):
        assert run(self.PROGRAM, {"arr": [42], "target": 42}) == 0

    def test_single_element_not_found(self):
        assert run(self.PROGRAM, {"arr": [42], "target": 7}) == -1


# ===================================================================
# Number theory / math
# ===================================================================


class TestFibonacci:
    """Iterative Fibonacci sequence generation."""

    PROGRAM = """\
n = input.n
if (n <= 0) {
    return []
}
if (n == 1) {
    return [0]
}
fibs = [0, 1]
i = 2
while (i < n) {
    next_val = fibs[i - 1] + fibs[i - 2]
    fibs = fibs + [next_val]
    i += 1
}
return fibs
"""

    @pytest.mark.parametrize(
        ("n", "expected"),
        [
            (0, []),
            (1, [0]),
            (2, [0, 1]),
            (5, [0, 1, 1, 2, 3]),
            (10, [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]),
        ],
    )
    def test_fibonacci(self, n, expected):
        assert run(self.PROGRAM, {"n": n}) == expected


class TestGCD:
    """Greatest Common Divisor — Euclidean algorithm (iterative)."""

    PROGRAM = """\
a = input.a
b = input.b
while (b != 0) {
    temp = b
    b = a % b
    a = temp
}
return a
"""

    @pytest.mark.parametrize(
        ("a", "b"),
        [
            (12, 8),
            (100, 75),
            (17, 13),
            (0, 5),
            (7, 0),
            (48, 18),
            (1, 1),
            (1071, 462),
        ],
    )
    def test_gcd(self, a, b):
        assert run(self.PROGRAM, {"a": a, "b": b}) == math.gcd(a, b)


class TestSieveOfEratosthenes:
    """Sieve of Eratosthenes — find all primes up to n.

    Uses a list of booleans (0/1) since Cy has no dedicated bool arrays.
    """

    PROGRAM = """\
n = input.n
if (n < 2) {
    return []
}

# Build sieve: 1 = potentially prime, 0 = composite
sieve = []
i = 0
while (i <= n) {
    if (i < 2) {
        sieve = sieve + [0]
    } else {
        sieve = sieve + [1]
    }
    i += 1
}

# Mark composites
p = 2
while (p * p <= n) {
    if (sieve[p] == 1) {
        multiple = p * p
        while (multiple <= n) {
            sieve[multiple] = 0
            multiple += p
        }
    }
    p += 1
}

# Collect primes
primes = []
i = 2
while (i <= n) {
    if (sieve[i] == 1) {
        primes = primes + [i]
    }
    i += 1
}
return primes
"""

    @pytest.mark.parametrize(
        ("n", "expected"),
        [
            (1, []),
            (2, [2]),
            (10, [2, 3, 5, 7]),
            (20, [2, 3, 5, 7, 11, 13, 17, 19]),
            (30, [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]),
        ],
    )
    def test_primes(self, n, expected):
        assert run(self.PROGRAM, {"n": n}) == expected


# ===================================================================
# Classic interview / puzzle problems
# ===================================================================


class TestFizzBuzz:
    """FizzBuzz for 1..n."""

    PROGRAM = """\
n = input.n
result = []
i = 1
while (i <= n) {
    if (i % 15 == 0) {
        result = result + ["FizzBuzz"]
    } elif (i % 3 == 0) {
        result = result + ["Fizz"]
    } elif (i % 5 == 0) {
        result = result + ["Buzz"]
    } else {
        result = result + [str(i)]
    }
    i += 1
}
return result
"""

    def test_fizzbuzz_15(self):
        expected = [
            "1",
            "2",
            "Fizz",
            "4",
            "Buzz",
            "Fizz",
            "7",
            "8",
            "Fizz",
            "Buzz",
            "11",
            "Fizz",
            "13",
            "14",
            "FizzBuzz",
        ]
        assert run(self.PROGRAM, {"n": 15}) == expected

    def test_fizzbuzz_zero(self):
        assert run(self.PROGRAM, {"n": 0}) == []


class TestTwoSum:
    """Two-sum: find indices of two numbers that add to target."""

    PROGRAM = """\
nums = input.nums
target = input.target
n = len(nums)
found = False
result = [-1, -1]

i = 0
while (i < n and not found) {
    j = i + 1
    while (j < n and not found) {
        if (nums[i] + nums[j] == target) {
            result = [i, j]
            found = True
        }
        j += 1
    }
    i += 1
}
return result
"""

    def test_basic(self):
        assert run(self.PROGRAM, {"nums": [2, 7, 11, 15], "target": 9}) == [0, 1]

    def test_middle(self):
        assert run(self.PROGRAM, {"nums": [3, 2, 4], "target": 6}) == [1, 2]

    def test_not_found(self):
        assert run(self.PROGRAM, {"nums": [1, 2, 3], "target": 100}) == [-1, -1]

    def test_negatives(self):
        assert run(self.PROGRAM, {"nums": [-1, -2, -3, -4], "target": -6}) == [1, 3]


class TestPalindrome:
    """Check if a string is a palindrome (case-insensitive).

    Uses string indexing (s[i]) to access individual characters.
    """

    PROGRAM = """\
s = lowercase(input.s)
n = len(s)
is_palindrome = True
i = 0
while (i < int(n / 2) and is_palindrome) {
    if (s[i] != s[n - 1 - i]) {
        is_palindrome = False
    }
    i += 1
}
return is_palindrome
"""

    @pytest.mark.parametrize(
        ("s", "expected"),
        [
            ("racecar", True),
            ("Racecar", True),
            ("hello", False),
            ("a", True),
            ("ab", False),
            ("aba", True),
            ("abba", True),
        ],
    )
    def test_palindrome(self, s, expected):
        assert run(self.PROGRAM, {"s": s}) == expected


# ===================================================================
# Data manipulation
# ===================================================================


class TestMatrixTranspose:
    """Transpose an MxN matrix."""

    PROGRAM = """\
matrix = input.matrix
rows = len(matrix)
cols = len(matrix[0])

# Build transposed matrix (cols x rows)
transposed = []
c = 0
while (c < cols) {
    row = []
    r = 0
    while (r < rows) {
        row = row + [matrix[r][c]]
        r += 1
    }
    transposed = transposed + [row]
    c += 1
}
return transposed
"""

    def test_square(self):
        m = [[1, 2], [3, 4]]
        expected = [[1, 3], [2, 4]]
        assert run(self.PROGRAM, {"matrix": m}) == expected

    def test_rectangular(self):
        m = [[1, 2, 3], [4, 5, 6]]
        expected = [[1, 4], [2, 5], [3, 6]]
        assert run(self.PROGRAM, {"matrix": m}) == expected

    def test_single_row(self):
        m = [[1, 2, 3]]
        expected = [[1], [2], [3]]
        assert run(self.PROGRAM, {"matrix": m}) == expected

    def test_single_column(self):
        m = [[1], [2], [3]]
        expected = [[1, 2, 3]]
        assert run(self.PROGRAM, {"matrix": m}) == expected


class TestFrequencyCounter:
    """Count occurrences of each item (like collections.Counter)."""

    PROGRAM = """\
items = input.items
counts = {}
for (item in items) {
    key = str(item)
    if (counts[key] == null) {
        counts[key] = 1
    } else {
        counts[key] += 1
    }
}
return counts
"""

    def test_basic(self):
        result = run(self.PROGRAM, {"items": ["a", "b", "a", "c", "b", "a"]})
        assert result == {"a": 3, "b": 2, "c": 1}

    def test_numbers_as_string_keys(self):
        result = run(self.PROGRAM, {"items": [1, 2, 1, 3, 2, 1]})
        assert result == {"1": 3, "2": 2, "3": 1}

    def test_empty(self):
        result = run(self.PROGRAM, {"items": []})
        assert result == {}

    def test_single(self):
        result = run(self.PROGRAM, {"items": ["x"]})
        assert result == {"x": 1}


class TestManualReverse:
    """Reverse a list manually (without the built-in reverse())."""

    PROGRAM = """\
arr = input.arr
n = len(arr)
i = 0
while (i < int(n / 2)) {
    j = n - 1 - i
    tmp = arr[i]
    arr[i] = arr[j]
    arr[j] = tmp
    i += 1
}
return arr
"""

    @pytest.mark.parametrize(
        "arr",
        [
            [],
            [1],
            [1, 2],
            [1, 2, 3],
            [1, 2, 3, 4],
            [1, 2, 3, 4, 5],
        ],
    )
    def test_reverse(self, arr):
        result = run(self.PROGRAM, {"arr": list(arr)})
        assert result == list(reversed(arr))


class TestCumulativeSum:
    """Compute cumulative (running) sum of a list."""

    PROGRAM = """\
arr = input.arr
result = []
total = 0
for (val in arr) {
    total += val
    result = result + [total]
}
return result
"""

    @pytest.mark.parametrize(
        ("arr", "expected"),
        [
            ([], []),
            ([1], [1]),
            ([1, 2, 3], [1, 3, 6]),
            ([5, -3, 2, 10], [5, 2, 4, 14]),
        ],
    )
    def test_cumsum(self, arr, expected):
        assert run(self.PROGRAM, {"arr": arr}) == expected


class TestFlattenOneLevel:
    """Flatten a list of lists by one level."""

    PROGRAM = """\
nested = input.nested
flat = []
for (sublist in nested) {
    for (item in sublist) {
        flat = flat + [item]
    }
}
return flat
"""

    def test_basic(self):
        result = run(self.PROGRAM, {"nested": [[1, 2], [3, 4], [5]]})
        assert result == [1, 2, 3, 4, 5]

    def test_empty_sublists(self):
        result = run(self.PROGRAM, {"nested": [[], [1], []]})
        assert result == [1]

    def test_single(self):
        result = run(self.PROGRAM, {"nested": [[42]]})
        assert result == [42]

    def test_empty(self):
        result = run(self.PROGRAM, {"nested": []})
        assert result == []


# ===================================================================
# String manipulation
# ===================================================================


class TestCaesarCipher:
    """Caesar cipher encode and decode (uppercase letters only)."""

    ENCODE_PROGRAM = """\
text = uppercase(input.text)
shift = input.shift
alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
result = []
idx = 0
while (idx < len(text)) {
    ch = text[idx]
    if (ch >= "A" and ch <= "Z") {
        # Find position in alphabet
        pos = -1
        k = 0
        while (k < 26 and pos == -1) {
            if (alphabet[k] == ch) {
                pos = k
            }
            k += 1
        }
        new_pos = (pos + shift) % 26
        result = result + [alphabet[new_pos]]
    } else {
        result = result + [ch]
    }
    idx += 1
}
return join(result, "")
"""

    def test_encode_basic(self):
        result = run(self.ENCODE_PROGRAM, {"text": "HELLO", "shift": 3})
        assert result == "KHOOR"

    def test_encode_wrap(self):
        result = run(self.ENCODE_PROGRAM, {"text": "XYZ", "shift": 3})
        assert result == "ABC"

    def test_encode_with_spaces(self):
        result = run(self.ENCODE_PROGRAM, {"text": "HELLO WORLD", "shift": 1})
        assert result == "IFMMP XPSME"

    def test_roundtrip(self):
        encoded = run(self.ENCODE_PROGRAM, {"text": "SECRET", "shift": 7})
        decoded = run(self.ENCODE_PROGRAM, {"text": encoded, "shift": 26 - 7})
        assert decoded == "SECRET"


# ===================================================================
# More advanced: composing patterns
# ===================================================================


class TestMinMax:
    """Find min and max without using built-in min()/max()."""

    PROGRAM = """\
arr = input.arr
n = len(arr)
if (n == 0) {
    return {"min": null, "max": null}
}
current_min = arr[0]
current_max = arr[0]
i = 1
while (i < n) {
    if (arr[i] < current_min) {
        current_min = arr[i]
    }
    if (arr[i] > current_max) {
        current_max = arr[i]
    }
    i += 1
}
return {"min": current_min, "max": current_max}
"""

    def test_basic(self):
        result = run(self.PROGRAM, {"arr": [3, 1, 4, 1, 5, 9, 2, 6]})
        assert result == {"min": 1, "max": 9}

    def test_single(self):
        result = run(self.PROGRAM, {"arr": [42]})
        assert result == {"min": 42, "max": 42}

    def test_negatives(self):
        result = run(self.PROGRAM, {"arr": [-5, -1, -10, -3]})
        assert result == {"min": -10, "max": -1}

    def test_empty(self):
        result = run(self.PROGRAM, {"arr": []})
        assert result == {"min": None, "max": None}


class TestDotProduct:
    """Dot product of two vectors."""

    PROGRAM = """\
a = input.a
b = input.b
n = len(a)
total = 0
i = 0
while (i < n) {
    total += a[i] * b[i]
    i += 1
}
return total
"""

    def test_basic(self):
        assert run(self.PROGRAM, {"a": [1, 2, 3], "b": [4, 5, 6]}) == 32

    def test_zeros(self):
        assert run(self.PROGRAM, {"a": [0, 0, 0], "b": [1, 2, 3]}) == 0

    def test_single(self):
        assert run(self.PROGRAM, {"a": [3], "b": [7]}) == 21


class TestMatrixMultiply:
    """Matrix multiplication of two 2D matrices."""

    PROGRAM = """\
a = input.a
b = input.b
rows_a = len(a)
cols_a = len(a[0])
cols_b = len(b[0])

result = []
i = 0
while (i < rows_a) {
    row = []
    j = 0
    while (j < cols_b) {
        cell = 0
        k = 0
        while (k < cols_a) {
            cell += a[i][k] * b[k][j]
            k += 1
        }
        row = row + [cell]
        j += 1
    }
    result = result + [row]
    i += 1
}
return result
"""

    def test_2x2(self):
        a = [[1, 2], [3, 4]]
        b = [[5, 6], [7, 8]]
        expected = [[19, 22], [43, 50]]
        assert run(self.PROGRAM, {"a": a, "b": b}) == expected

    def test_identity(self):
        a = [[1, 0], [0, 1]]
        b = [[5, 6], [7, 8]]
        assert run(self.PROGRAM, {"a": a, "b": b}) == b

    def test_rectangular(self):
        a = [[1, 2, 3], [4, 5, 6]]  # 2x3
        b = [[7, 8], [9, 10], [11, 12]]  # 3x2
        expected = [[58, 64], [139, 154]]  # 2x2
        assert run(self.PROGRAM, {"a": a, "b": b}) == expected


class TestCountingSort:
    """Counting sort for non-negative integers within a known range."""

    PROGRAM = """\
arr = input.arr
if (len(arr) == 0) {
    return []
}

# Find max value
max_val = arr[0]
i = 1
while (i < len(arr)) {
    if (arr[i] > max_val) {
        max_val = arr[i]
    }
    i += 1
}

# Build count array
counts = []
i = 0
while (i <= max_val) {
    counts = counts + [0]
    i += 1
}

# Count occurrences
for (val in arr) {
    counts[val] += 1
}

# Build sorted output
result = []
i = 0
while (i <= max_val) {
    j = 0
    while (j < counts[i]) {
        result = result + [i]
        j += 1
    }
    i += 1
}
return result
"""

    @pytest.mark.parametrize(
        "arr",
        [
            [],
            [0],
            [3, 1, 4, 1, 5, 9, 2, 6],
            [0, 0, 0],
            [5, 5, 5, 1, 1],
            [0, 1, 2, 3, 4, 5],
        ],
    )
    def test_sorts_correctly(self, arr):
        result = run(self.PROGRAM, {"arr": list(arr)})
        assert result == sorted(arr)
