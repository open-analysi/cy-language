"""
Tests for indexed assignment functionality that work with current interpolation system.
Uses single quotes in interpolation to avoid parsing issues.
"""

from cy_language import Cy


class TestWorkingIndexedAssignment:
    """Test indexed assignment patterns that work with current parser."""

    def test_dict_assignment_with_single_quote_interpolation(self):
        """Test dictionary assignment with single quotes in interpolation."""
        interpreter = Cy()
        program = """
        data = {"name": "Alice", "age": 30}
        data["city"] = "NYC"
        data["age"] = 31
        output = "Name: ${data['name']}, Age: ${data['age']}, City: ${data['city']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice, Age: 31, City: NYC"'

    def test_list_assignment_basic(self):
        """Test basic list assignment."""
        interpreter = Cy()
        program = """
        arr = ["a", "b", "c"]
        arr[0] = "x"
        arr[2] = "z"
        output = "Array: ${arr[0]}, ${arr[1]}, ${arr[2]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Array: x, b, z"'

    def test_variable_index_assignment(self):
        """Test assignment using variable as index."""
        interpreter = Cy()
        program = """
        scores = {"alice": 85, "bob": 90}
        player = "alice"
        new_score = 95
        scores[player] = new_score
        output = "Alice: ${scores['alice']}, Bob: ${scores['bob']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Alice: 95, Bob: 90"'

    def test_expression_as_value_assignment(self):
        """Test assignment with expressions as values."""
        interpreter = Cy()
        program = """
        data = {"base": 100}
        data["calculated"] = data["base"] * 2 + 50
        output = "Base: ${data['base']}, Calculated: ${data['calculated']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Base: 100, Calculated: 250"'

    def test_ip_risk_score_original_pattern(self):
        """Test the original use case: $ip_risk_scores[$source_ip] = $anomaly_score."""
        interpreter = Cy()
        program = """
        ip_risk_scores = {}
        source_ip = "192.168.1.100"
        anomaly_score = 85.5
        ip_risk_scores[source_ip] = anomaly_score
        
        another_ip = "10.0.0.1"
        another_score = 42.0
        ip_risk_scores[another_ip] = another_score
        
        output = "IP ${source_ip}: ${ip_risk_scores[$source_ip]}, IP ${another_ip}: ${ip_risk_scores[$another_ip]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"IP 192.168.1.100: 85.5, IP 10.0.0.1: 42.0"'
