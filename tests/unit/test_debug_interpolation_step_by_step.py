"""
Step by step debug of interpolation parsing.
"""

from cy_language import Cy


class TestInterpolationStepByStep:
    """Debug interpolation parsing step by step."""

    def test_simple_interpolation_works(self):
        """Confirm simple interpolation works."""
        interpreter = Cy()
        program = '''
        name = "Alice"
        output = """Hello ${name}!"""
        return output
        '''
        result = interpreter.run(program)
        print(f"Simple interpolation result: '{result}'")
        assert "Alice" in result

    def test_single_quote_indexed_access_works(self):
        """Confirm single quote indexed access works in double quotes."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice"}
        output = "User: ${data['name']}"
        return output
        """
        result = interpreter.run(program)
        print(f"Single quote result: '{result}'")
        assert "Alice" in result

    def test_double_quote_indexed_access_debug(self):
        """Debug why double quote indexed access doesn't work."""
        interpreter = Cy()
        program = '''
        data = {"name": "Alice"}
        output = """User: ${data["name"]}"""
        return output
        '''
        result = interpreter.run(program)
        print(f"Double quote result: '{result}'")
        print(f"Length: {len(result)}")
        print(f"Repr: {result!r}")

        # Let's see if it's doing ANY interpolation
        if "Alice" in result:
            print("SUCCESS: Interpolation worked!")
        else:
            print("FAILURE: No interpolation happened")
            print("Checking if the literal template is returned...")
            if "${data[" in result:
                print("Issue: Template returned literally without processing")
