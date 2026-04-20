"""
Test deep chained indexed assignment patterns like $a[$b][$c][$d] = value.
"""

from cy_language import Cy


class TestDeepChainedAssignment:
    """Test deep chained indexed assignment patterns."""

    def test_four_level_chained_assignment(self):
        """Test 4-level deep chained assignment: $a[$b][$c][$d] = value."""
        interpreter = Cy()
        program = """
        # Create deep nested structure
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "items": [0, 0, 0]
                    }
                }
            }
        }
        
        # Test 4-level assignment
        data["level1"]["level2"]["level3"]["items"][2] = 42
        
        output = "Deep value: ${data['level1']['level2']['level3']['items'][2]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Deep value: 42"'

    def test_variable_based_deep_chaining(self):
        """Test deep chaining with variables as indices."""
        interpreter = Cy()
        program = """
        storage = {
            "servers": {
                "prod": {
                    "logs": ["old", "current", "archive"]
                }
            }
        }
        
        env = "servers"
        server = "prod" 
        log_type = "logs"
        index = 1
        
        # Assign using all variables
        storage[env][server][log_type][index] = "updated"
        
        output = "Updated log: ${storage['servers']['prod']['logs'][1]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Updated log: updated"'

    def test_mixed_list_dict_deep_assignment(self):
        """Test mixed list and dictionary deep assignment."""
        interpreter = Cy()
        program = """
        complex = [
            {
                "users": [
                    {"name": "alice", "scores": [10, 20, 30]},
                    {"name": "bob", "scores": [15, 25, 35]}
                ]
            }
        ]
        
        # Deep assignment: list -> dict -> list -> dict -> list
        complex[0]["users"][1]["scores"][2] = 100
        
        output = "Bob's third score: ${complex[0]['users'][1]['scores'][2]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Bob\'s third score: 100"'

    def test_expression_in_deep_chaining(self):
        """Test using expressions in deep chained assignment."""
        interpreter = Cy()
        program = """
        matrix = [
            [{"values": [1, 2, 3]}, {"values": [4, 5, 6]}],
            [{"values": [7, 8, 9]}, {"values": [10, 11, 12]}]
        ]
        
        row = 1
        col = 0
        val_index = 2
        
        # Use expressions in the assignment
        matrix[row][col]["values"][val_index] = matrix[0][1]["values"][0] * 10
        
        output = "Updated value: ${matrix[1][0]['values'][2]}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Updated value: 40"'

    def test_six_level_assignment(self):
        """Test extremely deep 6-level assignment."""
        interpreter = Cy()
        program = """
        deep = {
            "a": {
                "b": {
                    "c": {
                        "d": {
                            "e": [{"f": "original"}]
                        }
                    }
                }
            }
        }
        
        # 6-level assignment
        deep["a"]["b"]["c"]["d"]["e"][0]["f"] = "changed"
        
        output = "Six levels deep: ${deep['a']['b']['c']['d']['e'][0]['f']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Six levels deep: changed"'

    def test_mixed_variable_literal_chaining(self):
        """Test mixed variable and literal chaining: $a[$b]["data"][$d]."""
        interpreter = Cy()
        program = """
        store = {
            "cache": {
                "data": [{"status": "old"}, {"status": "current"}]
            },
            "temp": {
                "data": [{"status": "temp1"}, {"status": "temp2"}]
            }
        }
        
        section = "cache"
        index = 1
        
        # Mixed: variable, literal string, variable
        store[section]["data"][index]["status"] = "updated"
        
        output = "Mixed access result: ${store['cache']['data'][1]['status']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Mixed access result: updated"'

    def test_complex_mixed_patterns(self):
        """Test complex mixed patterns with expressions."""
        interpreter = Cy()
        program = """
        config = {
            "db1": {"connections": [{"host": "old1"}, {"host": "old2"}]},
            "db2": {"connections": [{"host": "old3"}, {"host": "old4"}]}
        }
        
        db_name = "db1"
        conn_index = 0
        
        # Mixed: variable, literal, expression, literal
        config[db_name]["connections"][conn_index + 0]["host"] = "new-host"
        
        output = "Complex mixed: ${config['db1']['connections'][0]['host']}"
        return output
        """
        result = interpreter.run(program)
        assert result == '"Complex mixed: new-host"'
