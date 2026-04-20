"""Grammar definition for the Cy language."""


def get_grammar() -> str:
    """Return the EBNF grammar for the Cy language.

    Returns:
        str: The EBNF grammar definition
    """
    return r"""
        start: statement*

        statement: assignment
                | conditional_statement
                | while_loop_statement
                | for_in_statement
                | return_statement
                | break_statement
                | continue_statement
                | try_catch_statement
                | function_call_statement

        function_call_statement: function_call

        assignment: IDENTIFIER compound_op expression
                 | indexed_assignment
                 | field_assignment

        indexed_assignment: indexed_access compound_op expression

        field_assignment: field_access compound_op expression

        compound_op: COMPOUND_ASSIGN_OP | "="

        // Control flow statements
        conditional_statement: IF "(" expression ")" "{" statement* "}" elif_clause* [else_clause]
        elif_clause: ELIF "(" expression ")" "{" statement* "}"
        else_clause: ELSE "{" statement* "}"

        while_loop_statement: WHILE "(" expression ")" "{" statement* "}"

        for_in_statement: FOR "(" IDENTIFIER IN expression ")" "{" statement* "}"

        return_statement: RETURN expression

        break_statement: BREAK
        continue_statement: CONTINUE

        // Try/catch/finally statements
        try_catch_statement: TRY "{" statement* "}" catch_clause+ [finally_clause]
        catch_clause: CATCH "(" IDENTIFIER ")" "{" statement* "}"
        finally_clause: FINALLY "{" statement* "}"

        expression: null_coalesce

        // Null coalescing operator (lowest precedence)
        null_coalesce: boolean_or (NULL_COALESCE boolean_or)*

        // Boolean operations
        boolean_or: boolean_and (OR boolean_and)*
        boolean_and: boolean_not (AND boolean_not)*
        boolean_not: NOT comparison | comparison

        // Comparison operations
        comparison: arithmetic ((EQUAL | NOT_EQUAL | LESS_EQUAL | GREATER_EQUAL | LESS_THAN | GREATER_THAN | IN) arithmetic)*

        // Arithmetic operations (higher precedence than comparisons)
        arithmetic: term
        term: multiplicative ((PLUS | MINUS) multiplicative)*
        multiplicative: factor ((MULTIPLY | DIVIDE | MODULO) factor)*
        factor: (PLUS | MINUS) factor | atom

        // Atomic expressions (highest precedence)
        atom: primary

        primary: string
               | single_quoted_string
               | multiline_string
               | list_comprehension
               | list
               | dictionary
               | conditional_expr
               | function_call
               | indexed_access
               | field_access
               | IDENTIFIER
               | value
               | "(" expression ")"

        // List comprehension expression: [expr for(x in items)] or [expr for(x in items) if(cond)]
        list_comprehension: "[" expression FOR "(" IDENTIFIER IN expression ")" IF "(" expression ")" "]"
                          | "[" expression FOR "(" IDENTIFIER IN expression ")" "]"

        // Conditional expression (ternary-like)
        conditional_expr: IF "(" expression ")" "{" expression "}" elif_expr_clause* ELSE "{" expression "}"
        elif_expr_clause: ELIF "(" expression ")" "{" expression "}"

        multiline_string: TRIPLE_QUOTED_STRING

        string: DOUBLE_QUOTED_STRING

        single_quoted_string: SINGLE_QUOTED_STRING

        list: "[" list_items? "]"

        list_items: expression ("," expression)* ","?

        dictionary: "{" dict_items? "}"

        dict_items: dict_item ("," dict_item)* ","?

        dict_item: string ":" expression

        function_call: function_name "(" [arguments] ")"

        function_name: IDENTIFIER | namespaced_identifier
        namespaced_identifier: IDENTIFIER NAMESPACE_SEP IDENTIFIER (NAMESPACE_SEP IDENTIFIER)?

        arguments: positional_args | named_args | mixed_args

        positional_args: expression ("," expression)*

        named_args: named_arg ("," named_arg)*

        mixed_args: mixed_args_pos_first

        mixed_args_pos_first: expression ("," expression)* "," named_arg ("," named_arg)*

        named_arg: IDENTIFIER "=" expression

        // Array/list indexing (supports chaining: arr[0][1][2])
        indexed_access: (IDENTIFIER | function_call | field_access | indexed_access) "[" expression "]"

        // Field access with dot notation
        field_access: (IDENTIFIER | function_call) "." field_path

        field_path: IDENTIFIER ("." IDENTIFIER)*

        // Simple values like numbers, booleans, etc.
        value: NUMBER
             | "True" -> true
             | "False" -> false
             | "null" -> null

        // VARIABLE token removed - interpolation handled by DOUBLE_QUOTED_STRING

        // Numbers (integers and floats)
        NUMBER: /[0-9]+(\.[0-9]+)?/

        // Keywords must come BEFORE IDENTIFIER to have precedence
        // Control flow keywords
        IF: "if"
        ELIF: "elif"
        ELSE: "else"
        WHILE: "while"
        FOR: "for"
        IN: "in"
        RETURN: "return"
        BREAK: "break"
        CONTINUE: "continue"
        TRY: "try"
        CATCH: "catch"
        FINALLY: "finally"

        // Boolean operators
        AND: "and"
        OR: "or"
        NOT: "not"

        // Null coalescing operator
        NULL_COALESCE: "??"

        // Function/tool names and field identifiers
        IDENTIFIER: /[a-zA-Z][a-zA-Z0-9_]*/

        // Double quoted strings for variable interpolation
        DOUBLE_QUOTED_STRING: /"([^"\\]|\\.)*"/

        // Single quoted strings for dictionary keys in interpolation
        SINGLE_QUOTED_STRING: /'([^'\\]|\\.)*'/

        // Triple quoted strings for multiline strings
        // This pattern matches triple quotes followed by any content (including newlines)
        // and then closing triple quotes
        TRIPLE_QUOTED_STRING: /\"\"\"((?:.|\n)*?)\"\"\"/

        // Comments start with #
        COMMENT: /#[^\n]*/

        // Newlines are ignored after processing
        _NEWLINE: /\n/

        // Namespace separator
        NAMESPACE_SEP: "::"

        // Arithmetic operators
        PLUS: "+"
        MINUS: "-"
        MULTIPLY: "*"
        DIVIDE: "/"
        MODULO: "%"

        // Comparison operators
        EQUAL: "=="
        NOT_EQUAL: "!="
        LESS_EQUAL: "<="
        GREATER_EQUAL: ">="
        LESS_THAN: "<"
        GREATER_THAN: ">"

        // Compound assignment operators (defined last, after all other operators)
        // Note: "=" is NOT included here to avoid conflicts with == in expressions
        COMPOUND_ASSIGN_OP: "+=" | "-=" | "*=" | "/=" | "%="

        // Whitespace and newlines are ignored
        %import common.WS
        %ignore WS
        %ignore COMMENT
    """
