"""
Comprehensive tests for indexed assignment functionality.

Tests for the new indexed assignment syntax: $dict[$key] = $value
This follows TDD approach - these tests will fail initially and pass as we implement the feature.
"""

import pytest

from cy_language import Cy
from cy_language.errors import InterpolationError


class TestBasicIndexedAssignment:
    """Test basic indexed assignment patterns."""

    def test_dict_string_key_assignment(self):
        """Test basic dictionary assignment with string keys."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"name": "Alice", "age": 30}
        data["city"] = "NYC"
        data["age"] = 31
        output = "Name: ${data['name']}, Age: ${data['age']}, City: ${data['city']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Name: Alice, Age: 31, City: NYC"'

    def test_list_numeric_index_assignment(self):
        """Test basic list assignment with numeric indices."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
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
        interpreter.show_enhanced_errors = False
        program = """
        scores = {"alice": 85, "bob": 90}
        player = "alice"
        new_score = 95
        scores[player] = new_score
        output = "Alice's score: ${scores['alice']}, Bob's score: ${scores['bob']}"
        return output
        """
        result = interpreter.run(program)
        assert result == "\"Alice's score: 95, Bob's score: 90\""

    def test_expression_as_value_assignment(self):
        """Test assignment with expressions as values."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"base": 100}
        data["calculated"] = data["base"] * 2 + 50
        output = "Base: ${data['base']}, Calculated: ${data['calculated']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Base: 100, Calculated: 250"'


class TestChainedIndexedAssignment:
    """Test chained indexed assignment patterns."""

    def test_nested_dict_assignment(self):
        """Test assignment to nested dictionary structure."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        user = {"profile": {"settings": {"theme": "light"}}}
        user["profile"]["settings"]["theme"] = "dark"
        user["profile"]["settings"]["language"] = "en"
        output = "Theme: ${user['profile']['settings']['theme']}, Lang: ${user['profile']['settings']['language']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Theme: dark, Lang: en"'

    def test_multidimensional_array_assignment(self):
        """Test assignment to multi-dimensional arrays."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        matrix = [["a", "b"], ["c", "d"]]
        matrix[0][1] = "X"
        matrix[1][0] = "Y"
        output = "Matrix: [${matrix[0][0]}, ${matrix[0][1]}], [${matrix[1][0]}, ${matrix[1][1]}]"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Matrix: [a, X], [Y, d]"'

    def test_mixed_dict_list_assignment(self):
        """Test assignment to mixed dictionary and list structures."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"users": [{"name": "Alice"}, {"name": "Bob"}]}
        data["users"][0]["age"] = 25
        data["users"][1]["age"] = 30
        output = "Alice: ${data['users'][0]['age']}, Bob: ${data['users'][1]['age']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Alice: 25, Bob: 30"'


class TestRealWorldPatterns:
    """Test real-world usage patterns for indexed assignment."""

    def test_ip_risk_score_pattern(self):
        """Test the original use case: $ip_risk_scores[$source_ip] = $anomaly_score."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
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

    def test_inventory_update_pattern(self):
        """Test inventory update pattern."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        inventory = {"apples": 50, "bananas": 30}
        item = "apples"
        sold = 5
        inventory[item] = inventory[item] - sold
        inventory["oranges"] = 25
        
        output = "Apples: ${inventory['apples']}, Bananas: ${inventory['bananas']}, Oranges: ${inventory['oranges']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Apples: 45, Bananas: 30, Oranges: 25"'

    def test_config_update_pattern(self):
        """Test configuration update pattern."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        config = {
            "database": {"host": "localhost", "port": 5432},
            "cache": {"ttl": 3600}
        }
        
        config["database"]["host"] = "prod-db.example.com"
        config["database"]["ssl"] = True
        config["cache"]["ttl"] = 7200
        config["features"] = {"logging": True, "metrics": False}
        
        output = "DB Host: ${config['database']['host']}, TTL: ${config['cache']['ttl']}, SSL: ${config['database']['ssl']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"DB Host: prod-db.example.com, TTL: 7200, SSL: True"'


class TestIndexedAssignmentErrorHandling:
    """Test error conditions for indexed assignment."""

    def test_assign_to_nonexistent_dict_key_creates_key(self):
        """Test that assigning to nonexistent dict key creates the key."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        data = {"a": 1}
        data["b"] = 2
        output = "A: ${data['a']}, B: ${data['b']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"A: 1, B: 2"'

    def test_list_index_out_of_bounds_assignment(self):
        """Test list index out of bounds assignment should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        arr[5] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(InterpolationError, match="Index out of range"):
            interpreter.run(program)

    def test_assign_to_invalid_index_type(self):
        """Test assignment with invalid index type should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        arr = ["a", "b", "c"]
        key = "invalid"
        arr[key] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(InterpolationError, match="List index must be an integer"):
            interpreter.run(program)

    def test_assign_to_non_indexable_type(self):
        """Test assignment to non-indexable type should fail."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        number = 42
        number[0] = "x"
        output = "Done"
        return output
        """
        with pytest.raises(
            InterpolationError, match="Cannot assign to index of type int"
        ):
            interpreter.run(program)

    def test_assign_to_string_should_fail(self):
        """Test that assigning to string indices should fail (strings are immutable)."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        text = "hello"
        text[0] = "H"
        output = "Done"
        return output
        """
        with pytest.raises(
            InterpolationError, match="Cannot assign to index of immutable type str"
        ):
            interpreter.run(program)


class TestToolIntegration:
    """Test indexed assignment with tool calls."""

    def test_tool_result_in_indexed_assignment(self):
        """Test using tool results in indexed assignment."""
        tools = {"calculate_score": lambda base, bonus: base + bonus}
        interpreter = Cy(tools=tools)
        interpreter.show_enhanced_errors = False

        program = """
        scores = {"alice": 0, "bob": 0}
        player = "alice"
        scores[player] = calculate_score(85, 10)
        scores["bob"] = calculate_score(90, 5)
        
        output = "Alice: ${scores['alice']}, Bob: ${scores['bob']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Alice: 95, Bob: 95"'

    def test_indexed_assignment_in_control_flow(self):
        """Test indexed assignment within control flow structures."""
        interpreter = Cy()
        interpreter.show_enhanced_errors = False
        program = """
        scores = {}
        players = ["alice", "bob", "carol"]
        counter = 0
        
        while (counter < 3) {
            player = players[counter]
            scores[player] = 80 + counter * 5
            counter = counter + 1
        }
        
        output = "Alice: ${scores['alice']}, Bob: ${scores['bob']}, Carol: ${scores['carol']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Alice: 80, Bob: 85, Carol: 90"'
