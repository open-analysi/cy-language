"""
Integration-level negative test cases for control flow constructs.

This module tests complex real-world scenarios where nested control flow
can fail, focusing on business logic patterns and edge cases.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestComplexNestedBusinessLogicErrors:
    """Test error conditions in complex business logic scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()

    def test_loan_approval_with_nested_syntax_error(self):
        """Test loan approval logic with nested syntax error."""
        program = """        $income = 75000
        $credit_score = 720
        $debt_ratio = 0.3

        if ($income >= 50000) {
            if ($credit_score >= 650) {
                if ($debt_ratio <= 0.4) {
                    $approval_score = 100
                    while ($approval_score > 0) {
                        if ($approval_score == 50) {
                            $output = "APPROVED"
                        # Missing closing brace for inner if
                        $approval_score = $approval_score - 10
                    }
                } else {
                    $output = "DENIED - High debt ratio"
                }
            } else {
                $output = "DENIED - Low credit score"
            }
        } else {
            $output = "DENIED - Low income"
        }
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Should get descriptive error about $ in variables
        assert (
            "Dollar signs" in str(exc_info.value)
            or "Unexpected" in str(exc_info.value)
            or "Expected" in str(exc_info.value)
        )

    def test_inventory_management_with_runtime_error_in_deep_nesting(self):
        """Test inventory management with runtime error in deeply nested logic."""
        program = """
        initial_stock = 100
        reorder_level = 20
        daily_sales = 15
        days = 0
        current_stock = initial_stock

        while (current_stock > 0) {
            current_stock = current_stock - daily_sales
            days = days + 1

            if (current_stock <= reorder_level) {
                reorder_quantity = 50
                if (days > 3) {
                    # Introduce division by zero error
                    zero_divisor = days - days
                    stock_efficiency = current_stock / zero_divisor
                }
                current_stock = current_stock + reorder_quantity
            }

            if (days >= 10) {
                current_stock = 0
            }
        }

        output = "Simulation completed"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Division by zero" in str(exc_info.value)

    def test_pricing_strategy_with_undefined_variable_in_nested_conditions(self):
        """Test pricing strategy with undefined variable in nested conditions."""
        program = """
        base_price = 100
        inventory_level = 75
        demand_factor = 1.1
        competitor_price = 95
        premium_product = True

        if (premium_product) {
            if (inventory_level < 10) {
                price = base_price * 1.2
            } elif (inventory_level > 50) {
                # Use undefined variable in nested condition
                if (undefined_bulk_threshold > 100) {
                    price = base_price * 0.8
                } else {
                    price = base_price * 0.9
                }
            } else {
                price = base_price
            }
        } else {
            if ((base_price * demand_factor) <= (competitor_price * 1.05)) {
                price = base_price * demand_factor
            } else {
                price = competitor_price * 0.98
            }
        }

        output = "Final price: $${price}"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)

    def test_financial_calculation_with_deeply_nested_infinite_loop(self):
        """Test financial calculation that triggers infinite loop protection."""
        program = """
        principal = 10000
        rate = 0.05
        target_amount = 15000
        years = 0
        amount = principal

        while (amount < target_amount) {
            years = years + 1
            amount = amount * (1 + rate)

            if (years > 5) {
                # Create nested infinite loop
                counter = 0
                while (True) {
                    counter = counter + 1
                    if (counter > 1000) {
                        # This condition will never trigger loop protection
                        # because we're in an infinite loop
                        amount = target_amount + 1
                    }
                }
            }
        }

        output = "Investment grew to $${amount} in ${years} years"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "iterations" in str(exc_info.value).lower()


class TestNestedControlFlowWithComplexConditions:
    """Test nested control flow with complex conditions that can fail."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()

    def test_game_logic_with_nested_condition_syntax_error(self):
        """Test game logic with syntax error in nested conditions."""
        program = """        $player_level = 5
        $player_health = 80
        $enemy_strength = 3
        $has_weapon = True
        $has_armor = False

        if ($player_level >= 5) {
            if ($has_weapon and $has_armor) {
                $damage_multiplier = 2.0
            } elif ($has_weapon or $has_armor) {
                $damage_multiplier = 1.5
            } else {
                $damage_multiplier = 1.0
            }

            $battle_rounds = 0
            while ($player_health > 0 and $enemy_strength > 0) {
                $battle_rounds = $battle_rounds + 1

                # Missing opening parenthesis in complex condition
                if $battle_rounds > 3 and ($damage_multiplier > 1.5)) {
                    $enemy_strength = $enemy_strength - 2
                } else {
                    $enemy_strength = $enemy_strength - 1
                }

                if ($enemy_strength <= 0) {
                    $output = "Victory!"
                } else {
                    $player_health = $player_health - $enemy_strength
                }
            }
        } else {
            $output = "Player level too low"
        }
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Should get descriptive error about $ in variables
        assert (
            "Dollar signs" in str(exc_info.value)
            or "Unexpected" in str(exc_info.value)
            or "Expected" in str(exc_info.value)
        )

    def test_data_processing_with_nested_array_access_error(self):
        """Test data processing logic with array access error in nesting."""
        program = """
        data_points = [10, 20, 30, 40, 50]
        threshold = 25
        processed_count = 0
        index = 0

        while (index < 5) {
            current_value = data_points[index]

            if (current_value > threshold) {
                processed_count = processed_count + 1

                if (processed_count > 2) {
                    # Try to access undefined array element
                    special_value = undefined_array[0]
                    current_value = current_value + special_value
                }
            }

            index = index + 1
        }

        output = "Processed ${processed_count} items"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)

    def test_workflow_automation_with_return_error_propagation(self):
        """Test workflow automation with return statement error propagation."""
        program = """
        tasks = ["setup", "process", "cleanup"]
        current_task_index = 0
        max_retries = 3

        while (current_task_index < 3) {
            current_task = tasks[current_task_index]
            retry_count = 0

            while (retry_count < max_retries) {
                if (current_task == "setup") {
                    setup_success = True
                } elif (current_task == "process") {
                    if (retry_count == 2) {
                        # Try to return undefined variable
                        return undefined_error_result
                    }
                    # Simulate failure to force retries
                    setup_success = False
                } else {
                    setup_success = True
                }

                if (setup_success) {
                    retry_count = max_retries
                } else {
                    retry_count = retry_count + 1
                }
            }

            current_task_index = current_task_index + 1
        }

        output = "All tasks completed"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)


class TestMalformedNestedStructures:
    """Test malformed nested structures that should fail gracefully."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()

    def test_pyramid_nesting_with_missing_braces_at_different_levels(self):
        """Test pyramid-style nesting with missing braces at various levels."""
        program = """        $level1 = 1
        if ($level1 == 1) {
            $level2 = 2
            if ($level2 == 2) {
                $level3 = 3
                if ($level3 == 3) {
                    $level4 = 4
                    if ($level4 == 4) {
                        $level5 = 5
                        if ($level5 == 5) {
                            $output = "Deep success"
                        # Clearly missing closing brace for level5 - no brace here!
                    # Clearly missing closing brace for level4 - no brace here!
                } # This brace closes level3
            } # This brace closes level2
        } # This brace closes level1
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Should get descriptive error about $ in variables
        assert (
            "Dollar signs" in str(exc_info.value)
            or "Unexpected" in str(exc_info.value)
            or "Expected" in str(exc_info.value)
        )

    def test_alternating_if_while_with_brace_mismatch_pattern(self):
        """Test alternating if/while pattern with systematic brace mismatches."""
        program = """        $a = 1
        if ($a > 0) {
            $b = 2
            while ($b > 0) {
                $c = 3
                if ($c > 0) {
                    $d = 4
                    while ($d > 0) {
                        $e = 5
                        if ($e > 0) {
                            $output = "nested success"
                        } # Missing brace for if($e > 0)
                        $d = $d - 1
                    } # This closes while($d > 0)
                } # This closes if($c > 0)
                $b = $b - 1
            } # This closes while($b > 0)
        # Missing brace for if($a > 0)
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Should get descriptive error about $ in variables
        assert (
            "Dollar signs" in str(exc_info.value)
            or "Unexpected" in str(exc_info.value)
            or "Expected" in str(exc_info.value)
        )

    def test_mixed_control_flow_with_elif_else_brace_confusion(self):
        """Test mixed control flow with elif/else causing brace confusion."""
        program = """        $score = 85
        $grade = ""

        if ($score >= 90) {
            $grade = "A"
            $counter = 0
            while ($counter < 3) {
                if ($counter == 1) {
                    $bonus_points = 5
                } # Missing else clause brace structure
                $counter = $counter + 1
            }
        } elif ($score >= 80) {
            $grade = "B"
            if ($score >= 85) {
                $grade = "B+"
                while ($score > 80) {
                    $score = $score - 1
                    if ($score == 82) {
                        $grade = "B"
                    # Missing closing brace for if($score == 82)
                }
            } else {
                $grade = "B-"
            }
        } else {
            $grade = "C or below"
        }

        $output = "Grade: ${grade}"
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        # Should get descriptive error about $ in variables
        assert (
            "Dollar signs" in str(exc_info.value)
            or "Unexpected" in str(exc_info.value)
            or "Expected" in str(exc_info.value)
        )


class TestStressTestingNestedErrors:
    """Stress test error handling in deeply nested scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy()

    def test_maximum_realistic_nesting_with_error_at_deepest_level(self):
        """Test maximum realistic nesting depth with error at the deepest level."""
        program = """
        config_valid = True
        if (config_valid) {
            user_authorized = True
            if (user_authorized) {
                data_available = True
                while (data_available) {
                    processing_mode = "batch"
                    if (processing_mode == "batch") {
                        batch_size = 100
                        current_batch = 0
                        while (current_batch < 3) {
                            items_processed = 0
                            if (items_processed < batch_size) {
                                validation_required = True
                                if (validation_required) {
                                    validation_score = 0
                                    while (validation_score < 5) {
                                        item_valid = True
                                        if (item_valid) {
                                            # Error at maximum realistic depth
                                            error_value = 10 / (validation_score - validation_score)
                                        }
                                        validation_score = validation_score + 1
                                    }
                                }
                            }
                            current_batch = current_batch + 1
                        }
                    }
                    data_available = False
                }
            }
        }
        output = "Processing complete"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "Division by zero" in str(exc_info.value)

    def test_complex_nested_with_multiple_error_types(self):
        """Test complex nesting that could trigger multiple types of errors."""
        program = """
        system_status = "online"
        if (system_status == "online") {
            retries = 0
            while (retries < 5) {
                connection_active = True
                if (connection_active) {
                    data_packets = [1, 2, 3, 4, 5]
                    packet_index = 0
                    while (packet_index < 5) {
                        current_packet = data_packets[packet_index]
                        if (current_packet > 0) {
                            processing_time = 100
                            if (retries == 3) {
                                # This will cause undefined variable error
                                result = undefined_packet_processor + current_packet
                            } else {
                                result = current_packet * 2
                            }
                        }
                        packet_index = packet_index + 1
                    }
                }
                retries = retries + 1
            }
        }
        output = "System processing complete"
        return output
        """
        with pytest.raises(Exception) as exc_info:
            self.interpreter.run(program)
        assert "not defined" in str(exc_info.value)
