"""Tests for the Cy language grammar."""

import pytest
from lark import Lark, ParseError

from cy_language.grammar import get_grammar


def test_grammar_exists():
    """Test that the grammar is defined."""
    grammar = get_grammar()
    assert grammar is not None
    assert isinstance(grammar, str)
    assert len(grammar) > 0


def test_parse_variable_assignment():
    """Test parsing variable assignment."""
    grammar = get_grammar()
    parser = Lark(grammar, start="assignment", parser="lalr")

    # Test basic variable assignment
    parser.parse('name = "Alice"')

    # Test variable assignment with braces (not used in assignment anymore)
    parser.parse('name = "Alice"')


def test_parse_comment():
    """Test parsing comments."""
    grammar = get_grammar()
    parser = Lark(grammar, start="statement", parser="lalr")

    # Test basic comment - comments are now ignored at lexer level
    # So we can't parse just a comment as a statement
    # Instead, test that comments are properly ignored
    parser.parse("x = 5  # This is a comment")


def test_parse_statement_with_comment():
    """Test parsing a statement with a comment."""
    grammar = get_grammar()
    parser = Lark(grammar, parser="lalr")

    # Test comment after statement
    parser.parse('name = "Alice"\n# This is a comment')


def test_parse_invalid_syntax():
    """Test that invalid syntax raises errors."""
    from lark.exceptions import UnexpectedCharacters

    grammar = get_grammar()
    parser = Lark(grammar, start="assignment", parser="lalr")

    # Test missing equals sign
    with pytest.raises((ParseError, UnexpectedCharacters)):
        parser.parse('name "Alice"')

    # Test invalid variable name
    with pytest.raises((ParseError, UnexpectedCharacters)):
        parser.parse('123 = "Alice"')


def test_parse_full_program():
    """Test parsing a complete program."""
    grammar = get_grammar()
    parser = Lark(grammar, parser="lalr")

    program = """
    # Variable assignment example
    name = "Alice"
    output = "Hello ${name}!"
    return output
    """

    tree = parser.parse(program)
    assert tree is not None
