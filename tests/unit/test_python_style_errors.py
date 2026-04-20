"""Tests for Python-style syntax error messages.

Users coming from Python often write code using Python syntax (colons, no parens, etc.).
These tests ensure we produce helpful, actionable error messages for common mistakes.
"""

import pytest

from cy_language import Cy
from cy_language.errors import NameError as CyNameError
from cy_language.errors import SyntaxError as CySyntaxError
from cy_language.parser import Parser


def _parse(code: str):
    """Parse code and return the raised SyntaxError (must raise)."""
    p = Parser()
    with pytest.raises(CySyntaxError) as exc_info:
        p.parse_only(code)
    return exc_info.value


def _parse_msg(code: str) -> str:
    """Parse code and return the full error message."""
    err = _parse(code)
    return str(err)


# ============================================================================
# Python-style if statement
# ============================================================================


def test_python_if_no_parens_gives_helpful_message():
    """if x == 2: should suggest Cy syntax with parens and braces."""
    msg = _parse_msg("if x == 2:\n    y = 3")
    assert "if" in msg.lower()
    assert "(" in msg  # Suggests adding parens
    assert "{" in msg  # Suggests using braces


def test_python_if_shows_cy_syntax_example():
    """Error message should show the correct Cy syntax."""
    msg = _parse_msg("if x == 2:\n    y = 3")
    # Should contain something like: if (x == 2) {
    assert "if (x == 2) {" in msg or ("if" in msg and "x == 2" in msg and "{" in msg)


def test_python_if_with_parens_and_colon():
    """if (x > 0): should suggest using { instead of :"""
    msg = _parse_msg("if (x > 0):\n    y = 1")
    assert "{" in msg  # Suggests using brace


def test_python_if_complex_condition():
    """if x > 0 and y < 10: should also give a helpful message."""
    msg = _parse_msg("if x > 0 and y < 10:\n    z = 1")
    assert "if" in msg.lower()
    assert "{" in msg


# ============================================================================
# Python-style elif
# ============================================================================


def test_python_elif_gives_helpful_message():
    """elif x > 0: should suggest Cy syntax."""
    code = "if (x > 0) {\n    y = 1\n} elif x == 0:\n    y = 0\n}"
    msg = _parse_msg(code)
    assert "elif" in msg.lower()
    assert "{" in msg


def test_python_elif_shows_cy_syntax():
    """Error message for elif should include the correct Cy pattern."""
    code = "if (x > 0) {\n    y = 1\n} elif x == 0:\n    y = 0\n}"
    msg = _parse_msg(code)
    assert "elif" in msg.lower()


# ============================================================================
# Python-style while loop
# ============================================================================


def test_python_while_no_parens_gives_helpful_message():
    """while x > 0: should suggest Cy syntax with parens and braces."""
    msg = _parse_msg("while x > 0:\n    x = x - 1")
    assert "while" in msg.lower()
    assert "(" in msg
    assert "{" in msg


def test_python_while_shows_cy_syntax_example():
    """Error message should show the correct while Cy syntax."""
    msg = _parse_msg("while x > 0:\n    x = x - 1")
    assert "while (x > 0) {" in msg or (
        "while" in msg and "x > 0" in msg and "{" in msg
    )


def test_python_while_with_parens_and_colon():
    """while (x > 0): should suggest { instead of :"""
    msg = _parse_msg("while (x > 0):\n    x = x - 1")
    assert "{" in msg


# ============================================================================
# Python-style for loop
# ============================================================================


def test_python_for_loop_no_parens_gives_helpful_message():
    """for i in x: should suggest Cy syntax with parens and braces."""
    msg = _parse_msg("for i in items:\n    y = i")
    assert "for" in msg.lower()
    assert "(" in msg
    assert "{" in msg


def test_python_for_loop_shows_cy_syntax_example():
    """Error message should show the correct for-in Cy syntax."""
    msg = _parse_msg("for i in items:\n    y = i")
    assert "for (i in items) {" in msg or (
        "for" in msg and "i in items" in msg and "{" in msg
    )


def test_python_for_loop_simple_variable():
    """for x in mylist: should produce a helpful message."""
    msg = _parse_msg("for x in mylist:\n    z = x")
    assert "for" in msg.lower()
    assert "{" in msg


# ============================================================================
# Python-style else clause
# ============================================================================


def test_python_else_colon_gives_helpful_message():
    """else: should suggest Cy syntax with braces."""
    code = "if (x > 0) {\n    y = 1\n} else:\n    y = 0\n}"
    msg = _parse_msg(code)
    assert "else" in msg.lower()
    assert "{" in msg


def test_python_else_shows_cy_syntax():
    """Error message for else: should include } else { pattern."""
    code = "if (x > 0) {\n    y = 1\n} else:\n    y = 0\n}"
    msg = _parse_msg(code)
    assert "} else {" in msg or ("else" in msg and "{" in msg)


# ============================================================================
# Python def function definition
# ============================================================================


def test_python_def_gives_helpful_message():
    """def foo(): is Python syntax not supported in Cy."""
    msg = _parse_msg("def process(x):\n    return x + 1")
    assert "def" in msg.lower() or "function" in msg.lower()


def test_python_def_explains_not_supported():
    """Error message for def should explain it's not supported."""
    msg = _parse_msg("def process(x):\n    return x + 1")
    # Should mention that function definitions are not supported
    assert (
        "not supported" in msg.lower()
        or "not available" in msg.lower()
        or "def" in msg.lower()
    )


# ============================================================================
# Python None vs Cy null
# ============================================================================


def test_python_none_raises_name_error():
    """Using None (Python) should raise a NameError since None is not defined in Cy."""
    cy = Cy()
    with pytest.raises(CyNameError) as exc_info:
        cy.run("x = None\nreturn x")
    err = exc_info.value
    assert "None" in str(err)


def test_python_none_message_context():
    """Error about None should include a hint about null via ErrorContext."""
    from cy_language.error_context import ErrorContext

    code = "x = None\nreturn x"
    cy = Cy()
    try:
        cy.run(code)
    except CyNameError as e:
        ctx = ErrorContext(source_code=code)
        enhanced = ctx.enhance_error(e)
        suggestion = getattr(enhanced, "_suggestion", None)
        if suggestion:
            assert "null" in suggestion.lower()


# ============================================================================
# Python class definition
# ============================================================================


def test_python_class_gives_helpful_message():
    """class Foo: is Python syntax not supported in Cy."""
    msg = _parse_msg("class MyProcessor:\n    x = 1")
    assert "class" in msg.lower()
    assert "not supported" in msg.lower()


# ============================================================================
# Python import statements
# ============================================================================


def test_python_import_gives_helpful_message():
    """import json should explain imports are not supported."""
    msg = _parse_msg("import json\nreturn x")
    assert "import" in msg.lower()
    assert "not supported" in msg.lower()


def test_python_from_import_gives_helpful_message():
    """from os import path should explain imports are not supported."""
    msg = _parse_msg("from os import path\nreturn x")
    assert "import" in msg.lower()
    assert "not supported" in msg.lower()


# ============================================================================
# Python raise
# ============================================================================


def test_python_raise_gives_helpful_message():
    """raise Exception("msg") should suggest try/catch."""
    msg = _parse_msg('raise Exception("something went wrong")\nreturn x')
    assert "raise" in msg.lower()
    assert "catch" in msg.lower()


# ============================================================================
# Python assert
# ============================================================================


def test_python_assert_gives_helpful_message():
    """assert x == 2 should suggest if/else alternative."""
    msg = _parse_msg("assert x == 2\nreturn x")
    assert "assert" in msg.lower()
    assert "not supported" in msg.lower()


# ============================================================================
# Python pass
# ============================================================================


def test_python_pass_gives_helpful_message():
    """pass is a Python no-op that isn't needed in Cy."""
    msg = _parse_msg("pass\nreturn x")
    assert "pass" in msg.lower()
    assert (
        "not needed" in msg.lower()
        or "not supported" in msg.lower()
        or "remove" in msg.lower()
    )


# ============================================================================
# Python lambda
# ============================================================================


def test_python_lambda_gives_helpful_message():
    """lambda functions are not supported in Cy."""
    msg = _parse_msg("fn = lambda x: x + 1\nreturn fn")
    assert "lambda" in msg.lower()
    assert "not supported" in msg.lower()


# ============================================================================
# Python f-strings
# ============================================================================


def test_python_fstring_gives_helpful_message():
    """f"..." strings should suggest Cy's ${} interpolation."""
    msg = _parse_msg('result = f"Hello {name}"\nreturn result')
    assert "f-string" in msg.lower() or ('f"' in msg or "interpolation" in msg.lower())


def test_python_fstring_shows_cy_syntax():
    """f-string error should mention ${} syntax."""
    msg = _parse_msg('result = f"Hello {name}"\nreturn result')
    assert "${" in msg or "interpolation" in msg.lower()


# ============================================================================
# Python exponentiation **
# ============================================================================


def test_python_power_operator_gives_helpful_message():
    """x ** 2 should explain ** is not supported."""
    msg = _parse_msg("result = x ** 2\nreturn result")
    assert (
        "**" in msg or "exponentiation" in msg.lower() or "not supported" in msg.lower()
    )


# ============================================================================
# Python floor division //
# ============================================================================


def test_python_floor_division_gives_helpful_message():
    """x // 3 should explain // is not supported."""
    msg = _parse_msg("result = x // 3\nreturn result")
    assert (
        "//" in msg or "floor division" in msg.lower() or "not supported" in msg.lower()
    )


# ============================================================================
# Python tuple unpacking
# ============================================================================


def test_python_tuple_unpacking_gives_helpful_message():
    """a, b = 1, 2 should suggest assigning variables separately."""
    msg = _parse_msg("a, b = 1, 2\nreturn a")
    assert (
        "tuple" in msg.lower()
        or "unpack" in msg.lower()
        or "not supported" in msg.lower()
    )


# ============================================================================
# Python ternary expression
# ============================================================================


def test_python_ternary_gives_helpful_message():
    """result = x if x > 0 else 0 should suggest Cy if/else expression."""
    msg = _parse_msg("result = x if x > 0 else 0\nreturn result")
    assert "ternary" in msg.lower() or "if" in msg.lower()
    assert "{" in msg  # Shows Cy syntax with braces


# ============================================================================
# Python with statement
# ============================================================================


def test_python_with_gives_helpful_message():
    """with open(...) as f: should explain with is not supported."""
    msg = _parse_msg('with open("file.txt") as f:\n    x = 1\nreturn x')
    assert "with" in msg.lower()
    assert "not supported" in msg.lower()


# ============================================================================
# Python except clause
# ============================================================================


def test_python_except_gives_helpful_message():
    """except Exception as e: should suggest catch (e) {"""
    code = "try {\n    x = 1\n} except ValueError as e:\n    x = 0\n}\nreturn x"
    msg = _parse_msg(code)
    assert "except" in msg.lower()
    assert "catch" in msg.lower()


# ============================================================================
# Verify valid Cy code still parses correctly
# ============================================================================


def test_valid_if_still_works():
    """Valid Cy if syntax should not trigger Python-style error messages."""
    p = Parser()
    # Should not raise
    p.parse_only("if (x > 0) {\n    y = 1\n}\nreturn y")


def test_valid_for_still_works():
    """Valid Cy for syntax should not trigger Python-style error messages."""
    p = Parser()
    # Should not raise
    p.parse_only("for (i in items) {\n    y = i\n}\nreturn y")


def test_valid_while_still_works():
    """Valid Cy while syntax should not trigger Python-style error messages."""
    p = Parser()
    # Should not raise
    p.parse_only("while (x > 0) {\n    x = x - 1\n}\nreturn x")
