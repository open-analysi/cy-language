"""
Edge case tests for nested while loops with if statements.

This module tests specific edge cases and boundary conditions that can occur
when combining while loops with if statements in nested patterns.
"""

from src.cy_language.interpreter import Cy


class TestNestedWhileIfEdgeCases:
    """Test edge cases and boundary conditions for nested while-if patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()

    def test_empty_conditional_blocks_in_while_loop(self):
        """Test while loop containing if statements with empty blocks."""
        program = """        counter = 1
        processed = 0
        
        while (counter <= 3) {
            if (counter == 1) {
                # Empty if block - should be valid
            } elif (counter == 2) {
                processed = processed + 1
            } else {
                # Empty else block - should be valid
            }
            counter = counter + 1
        }
        
        output = processed
        return output
        """
        result = self.interpreter.run(program)
        assert result == "1"

    def test_while_loop_with_all_empty_conditional_branches(self):
        """Test while loop where all conditional branches are empty."""
        program = """        iterations = 0
        max_iter = 2
        
        while (iterations < max_iter) {
            if (iterations == 0) {
                # Empty first branch
            } elif (iterations == 1) {
                # Empty second branch  
            } else {
                # Empty final branch
            }
            iterations = iterations + 1
        }
        
        output = iterations
        return output
        """
        result = self.interpreter.run(program)
        assert result == "2"

    def test_nested_while_with_single_iteration_each(self):
        """Test nested while loops that each execute exactly once."""
        program = """        outer_count = 0
        inner_count = 0
        total_executions = 0
        
        while (outer_count < 1) {
            inner_iteration = 0
            while (inner_iteration < 1) {
                if (True) {
                    total_executions = total_executions + 1
                }
                inner_iteration = inner_iteration + 1
            }
            inner_count = inner_count + inner_iteration
            outer_count = outer_count + 1
        }
        
        output = "Outer: ${outer_count}, Inner: ${inner_count}, Total: ${total_executions}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"Outer: 1, Inner: 1, Total: 1"'

    def test_while_with_immediate_termination_condition(self):
        """Test while loop with condition that immediately becomes false."""
        program = """        should_run = True
        execution_count = 0
        
        while (should_run) {
            execution_count = execution_count + 1
            if (execution_count == 1) {
                should_run = False
            }
        }
        
        output = execution_count
        return output
        """
        result = self.interpreter.run(program)
        assert result == "1"

    def test_deeply_nested_with_early_boolean_termination(self):
        """Test deeply nested structure with early boolean-based termination."""
        program = """        level1 = 1
        found_target = False
        search_depth = 0
        
        while (level1 <= 2 and not found_target) {
            level2 = 1
            while (level2 <= 2 and not found_target) {
                level3 = 1
                while (level3 <= 2 and not found_target) {
                    search_depth = search_depth + 1
                    if (level1 == 2 and level2 == 1 and level3 == 2) {
                        found_target = True
                    }
                    level3 = level3 + 1
                }
                level2 = level2 + 1
            }
            level1 = level1 + 1
        }
        
        output = "Depth: ${search_depth}, Found: ${found_target}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"Depth: 6, Found: True"'

    def test_variable_scope_in_nested_while_if(self):
        """Test variable scope behavior in nested while-if structures."""
        program = """        global_counter = 0
        outer_loop = 1
        
        while (outer_loop <= 2) {
            local_to_outer = outer_loop * 10
            inner_loop = 1
            
            while (inner_loop <= 2) {
                if (inner_loop == 1) {
                    local_to_if = local_to_outer + inner_loop
                    global_counter = global_counter + local_to_if
                } else {
                    local_to_else = local_to_outer + inner_loop
                    global_counter = global_counter + local_to_else
                }
                inner_loop = inner_loop + 1
            }
            outer_loop = outer_loop + 1
        }
        
        output = global_counter
        return output
        """
        result = self.interpreter.run(program)
        assert result == "66"  # (10+1)+(10+2)+(20+1)+(20+2) = 11+12+21+22 = 66

    def test_nested_while_with_zero_iterations(self):
        """Test nested while loops where inner loop has zero iterations."""
        program = """        outer = 1
        outer_executions = 0
        inner_executions = 0
        
        while (outer <= 2) {
            outer_executions = outer_executions + 1
            
            inner = 5
            while (inner < 5) {
                if (inner == 999) {
                    inner_executions = inner_executions + 1
                }
                inner = inner + 1
            }
            
            outer = outer + 1
        }
        
        output = "Outer: ${outer_executions}, Inner: ${inner_executions}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"Outer: 2, Inner: 0"'

    def test_alternating_nested_conditions_with_counters(self):
        """Test alternating nested conditions with multiple counters."""
        program = """        phase = 1
        type_a_count = 0
        type_b_count = 0
        type_c_count = 0
        
        while (phase <= 3) {
            item = 1
            while (item <= phase) {
                if (phase == 1) {
                    if (item % 2 == 1) {
                        type_a_count = type_a_count + 1
                    } else {
                        type_b_count = type_b_count + 1
                    }
                } elif (phase == 2) {
                    if (item <= 1) {
                        type_b_count = type_b_count + 1
                    } else {
                        type_c_count = type_c_count + 1
                    }
                } else {
                    if (item == 2) {
                        type_a_count = type_a_count + 1
                    } else {
                        type_c_count = type_c_count + 1
                    }
                }
                item = item + 1
            }
            phase = phase + 1
        }
        
        output = "A:${type_a_count}, B:${type_b_count}, C:${type_c_count}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"A:2, B:1, C:3"'

    def test_nested_boolean_condition_evaluation_order(self):
        """Test evaluation order of complex boolean conditions in nested loops."""
        program = """        x = 1
        y = 1
        evaluation_count = 0
        match_count = 0
        equal_count = 0
        other_count = 0
        
        while (x <= 2) {
            while (y <= 2) {
                evaluation_count = evaluation_count + 1
                
                if ((x == 1 and y == 2) or (x == 2 and y == 1)) {
                    match_count = match_count + 1
                } elif (x == y) {
                    equal_count = equal_count + 1
                } else {
                    other_count = other_count + 1
                }
                
                y = y + 1
            }
            y = 1
            x = x + 1
        }
        
        output = "Eval:${evaluation_count} Match:${match_count} Equal:${equal_count} Other:${other_count}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"Eval:4 Match:2 Equal:2 Other:0"'

    def test_nested_while_with_modulo_boundary_conditions(self):
        """Test nested while loops with modulo operations at boundaries."""
        program = """        dividend = 1
        boundary_hits = 0
        zero_remainders = 0
        
        while (dividend <= 6) {
            divisor = 1
            while (divisor <= 3) {
                remainder = dividend % divisor
                
                if (remainder == 0) {
                    zero_remainders = zero_remainders + 1
                    if (divisor == dividend) {
                        boundary_hits = boundary_hits + 1
                    }
                }
                
                divisor = divisor + 1
            }
            dividend = dividend + 1
        }
        
        output = "Zeros: ${zero_remainders}, Boundaries: ${boundary_hits}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"Zeros: 11, Boundaries: 3"'

    def test_maximum_nesting_with_minimal_operations(self):
        """Test maximum reasonable nesting depth with minimal operations per level."""
        program = """        l1 = 1
        depth_counter = 0
        
        while (l1 <= 1) {
            l2 = 1
            while (l2 <= 1) {
                l3 = 1
                while (l3 <= 1) {
                    l4 = 1
                    while (l4 <= 1) {
                        l5 = 1
                        while (l5 <= 1) {
                            if (l1 + l2 + l3 + l4 + l5 == 5) {
                                depth_counter = depth_counter + 1
                            }
                            l5 = l5 + 1
                        }
                        l4 = l4 + 1
                    }
                    l3 = l3 + 1
                }
                l2 = l2 + 1
            }
            l1 = l1 + 1
        }
        
        output = depth_counter
        return output
        """
        result = self.interpreter.run(program)
        assert result == "1"

    def test_nested_while_with_conditional_value_mapping(self):
        """Test nested while loops with conditional value mapping logic."""
        program = """        word_part = 1
        pattern_a_count = 0
        pattern_e_count = 0
        pattern_x_count = 0
        
        while (word_part <= 3) {
            char_code = 1
            while (char_code <= 2) {
                combined_value = word_part * 10 + char_code
                
                if (combined_value == 11 or combined_value == 22) {
                    pattern_a_count = pattern_a_count + 1
                } elif (combined_value == 12 or combined_value == 32) {
                    pattern_e_count = pattern_e_count + 1
                } else {
                    pattern_x_count = pattern_x_count + 1
                }
                
                char_code = char_code + 1
            }
            word_part = word_part + 1
        }
        
        output = "A: ${pattern_a_count}, E: ${pattern_e_count}, X: ${pattern_x_count}"
        return output
        """
        result = self.interpreter.run(program)
        assert result == '"A: 2, E: 2, X: 2"'
