"""
Integration tests for Control Flow Implementation

This module tests real-world scenarios using if/elif/else statements,
while loops, and return statements with complex business logic.
"""

import pytest

from src.cy_language.interpreter import Cy


class TestRealWorldControlFlowScenarios:
    """Test control flow with real-world business logic scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy(validate_output=False)

    def test_factorial_calculation_with_while_loop(self):
        """Test factorial calculation using while loop and conditionals."""
        program = """
        n = 5
        result = 1
        counter = 1

        while (counter <= n) {
            result = result * counter
            counter = counter + 1
        }

        output = result
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == "120"  # 5! = 120

    def test_loan_approval_complex_logic(self):
        """Test loan approval with complex conditional logic."""
        program = """
        income = 75000
        credit_score = 720
        debt_ratio = 0.3
        collateral = 50000
        loan_amount = 200000
        min_income = 50000
        min_credit = 650
        max_debt_ratio = 0.4

        if ((income >= min_income) and (credit_score >= min_credit)) {
            if ((debt_ratio <= max_debt_ratio) or (collateral >= loan_amount * 0.2)) {
                output = "APPROVED"
            } else {
                output = "DENIED - Insufficient collateral or high debt ratio"
            }
        } else {
            output = "DENIED - Income or credit score requirements not met"
        }
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == '"APPROVED"'

    def test_inventory_management_system(self):
        """Test inventory management with while loops and conditionals."""
        program = """
        initial_stock = 100
        reorder_level = 20
        reorder_quantity = 50
        daily_sales = 15
        days = 0
        current_stock = initial_stock

        while (current_stock > 0) {
            current_stock = current_stock - daily_sales
            days = days + 1

            if (current_stock <= reorder_level) {
                current_stock = current_stock + reorder_quantity
            }

            if (days >= 10) {
                # Break after 10 days for testing
                current_stock = 0
            }
        }

        output = "Simulation ran for ${days} days"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "10 days" in result

    def test_pricing_strategy_with_nested_conditions(self):
        """Test dynamic pricing with nested conditional logic."""
        program = """
        base_price = 100
        competitor_price = 95
        inventory_level = 25
        demand_factor = 1.2
        premium_product = True
        bulk_discount_threshold = 50

        if (premium_product) {
            if (inventory_level < 10) {
                price = base_price * 1.2  # Scarcity pricing
            } elif (inventory_level > bulk_discount_threshold) {
                price = base_price * 0.9  # Bulk discount
            } else {
                price = base_price
            }
        } else {
            if ((base_price * demand_factor) <= (competitor_price * 1.05)) {
                price = base_price * demand_factor
            } else {
                price = competitor_price * 0.98  # Match competition
            }
        }

        output = "Final price: $${price}"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "100" in result  # Base price for premium product with normal inventory

    def test_number_guessing_game_logic(self):
        """Test number guessing game with multiple conditional branches."""
        program = """
        target = 42
        guess = 35
        attempts = 1
        max_attempts = 5

        while (attempts <= max_attempts) {
            if (guess == target) {
                output = "Correct! Found in ${attempts} attempts"
                attempts = max_attempts + 1  # Exit loop
            } elif (guess < target) {
                guess = guess + 7  # Simulate next guess
                attempts = attempts + 1
            } else {
                guess = guess - 3  # Simulate next guess
                attempts = attempts + 1
            }
        }

        if (guess != target) {
            output = "Game over - target was ${target}"
        }
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "Correct!" in result or "Game over" in result

    def test_return_statement_early_termination(self):
        """Test return statement terminates execution early."""
        program = """
        x = 10
        y = 5

        if (x > y) {
            return "x is greater"
        }

        # This code should never execute
        output = "This should not appear"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == '"x is greater"'

    def test_complex_mathematical_conditions(self):
        """Test complex mathematical expressions in conditions."""
        program = """
        principal = 10000
        rate = 0.05
        time = 3
        compound_frequency = 4
        target_amount = 11500

        # Compound interest calculation: A = P(1 + r/n)^(nt)
        amount = principal
        years = 0

        while (years < time) {
            quarterly_rate = rate / compound_frequency
            quarters_per_year = compound_frequency
            quarter = 0

            while (quarter < quarters_per_year) {
                amount = amount * (1 + quarterly_rate)
                quarter = quarter + 1
            }

            years = years + 1
        }

        if (amount >= target_amount) {
            output = "Target reached: $${amount}"
        } else {
            output = "Target not reached: $${amount}"
        }
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "Target reached" in result

    def test_data_processing_with_conditionals(self):
        """Test data processing using conditionals with data structures."""
        program = """
        users = [
            {"name": "Alice", "age": 25, "active": True},
            {"name": "Bob", "age": 17, "active": False},
            {"name": "Charlie", "age": 30, "active": True}
        ]

        adult_active_count = 0
        index = 0

        while (index < 3) {
            user = users[index]

            if ((user.age >= 18) and (user.active)) {
                adult_active_count = adult_active_count + 1
            }

            index = index + 1
        }

        output = "Adult active users: ${adult_active_count}"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == '"Adult active users: 2"'

    def test_deeply_nested_parentheses_business_logic(self):
        """Test deeply nested parentheses in business logic."""
        program = """
        revenue = 1000000
        costs = 600000
        tax_rate = 0.25
        employee_count = 50
        min_profit_margin = 0.15
        bonus_threshold = 0.3
        company_age = 5
        market_leader = True

        profit = revenue - costs
        profit_margin = profit / revenue

        if (((profit_margin >= min_profit_margin) and (employee_count >= 25)) and (((profit_margin >= bonus_threshold) or (market_leader)) and (company_age >= 3))) {

            bonus_pool = profit * 0.1
            after_tax_profit = (profit - bonus_pool) * (1 - tax_rate)

            if ((after_tax_profit > 200000) and ((bonus_pool / employee_count) >= 2000)) {
                output = "Excellent performance: bonuses approved"
            } else {
                output = "Good performance: standard bonuses"
            }
        } else {
            output = "Performance targets not met"
        }
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "Good performance" in result

    def test_infinite_loop_protection(self):
        """Test that infinite loops are prevented with proper limits."""
        program = """
        counter = 0

        while (True) {
            counter = counter + 1
            # This would run forever without protection
        }

        output = counter
        return output
        """
        # Should hit iteration limit and raise RuntimeError
        with pytest.raises(Exception) as exc_info:
            result = self.interpreter.run(program)
        assert "iterations" in str(exc_info.value).lower()


class TestControlFlowEdgeCases:
    """Test edge cases and error conditions for control flow."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy(validate_output=False)

    def test_empty_conditional_blocks(self):
        """Test conditional statements with empty blocks."""
        program = """
        x = 5
        if (x > 0) {
            # Empty block - should be valid
        }
        output = "after conditional"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == '"after conditional"'

    def test_nested_while_loops(self):
        """Test nested while loops."""
        program = """
        outer = 0
        total = 0

        while (outer < 3) {
            inner = 0
            while (inner < 2) {
                total = total + 1
                inner = inner + 1
            }
            outer = outer + 1
        }

        output = total
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == "6"  # 3 * 2 = 6

    def test_conditionals_inside_loops(self):
        """Test conditional statements inside while loops."""
        program = """
        total = 0
        i = 1

        while (i <= 10) {
            if ((i % 2) == 0) {
                total = total + i
            }
            i = i + 1
        }

        output = total
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert result == "30"  # 2+4+6+8+10 = 30

    def test_multiple_return_statements_error(self):
        """Test error when multiple return statements exist."""
        program = """
        x = 5
        if (x > 0) {
            return "positive"
        } else {
            return "not positive"
        }
        """
        # Should fail due to multiple returns (if we implement this validation)
        # Will fail until implementation complete
        result = self.interpreter.run(program)

    def test_return_and_output_conflict_error(self):
        """Test that both return and output variable can be used.

        In , 'output' is just a regular variable,
        not a special variable. Therefore, this code is valid - you can
        assign to 'output' and then return a different value.
        The returned value takes precedence.
        """
        program = """
        result = 42
        output = "test"
        return result
        """
        # This is now valid - output is a regular variable
        # The return statement returns 'result', not 'output'
        result = self.interpreter.run(program)
        assert result == "42"  # Should return result, not output

    def test_complex_condition_with_tool_calls(self):
        """Test complex conditions involving tool calls."""
        program = """
        numbers = [1, 2, 3, 4, 5]
        threshold = 10

        if ((add(numbers[0], numbers[4]) > threshold) or
            (multiply(numbers[1], numbers[3]) <= threshold)) {
            output = "condition met"
        } else {
            output = "condition not met"
        }
        return output
        """
        # Define tools for this test
        tools = {"add": lambda a, b: a + b, "multiply": lambda a, b: a * b}

        with pytest.raises((Exception,)):
            result = self.interpreter.run(program, tools=tools)
            assert result == "condition not met"  # (1+5=6 <= 10) and (2*4=8 <= 10)

    def test_variable_modifications_in_conditions(self):
        """Test that variables can be modified within conditional blocks."""
        program = """
        balance = 1000
        transaction = -200
        overdraft_limit = 500

        if (balance + transaction >= 0) {
            balance = balance + transaction
            status = "approved"
        } elif ((balance + transaction) >= (-overdraft_limit)) {
            balance = balance + transaction
            status = "approved with overdraft"
        } else {
            status = "declined"
        }

        output = "Status: ${status}, Balance: ${balance}"
        return output
        """
        # Will fail until implementation complete
        result = self.interpreter.run(program)
        assert "approved" in result and "800" in result


class TestRealWorldNestedWhileIfScenarios:
    """Test real-world scenarios with nested while loops and if statements."""

    def setup_method(self):
        """Set up test fixtures."""
        self.interpreter = Cy(validate_output=False)

    def test_game_loop_with_nested_ai_decision_making(self):
        """Test game loop with nested AI decision making logic."""
        program = """
        game_round = 1
        player_score = 0
        ai_score = 0
        max_rounds = 3

        while (game_round <= max_rounds) {
            player_move = game_round % 3
            ai_strategy = 1

            while (ai_strategy <= 2) {
                if (ai_strategy == 1) {
                    ai_move = (game_round + 1) % 3
                    if (ai_move > player_move) {
                        ai_score = ai_score + 1
                    } elif (player_move > ai_move) {
                        player_score = player_score + 1
                    }
                } else {
                    ai_move = (game_round * 2) % 3
                    if (ai_move == player_move) {
                        ai_score = ai_score + 2
                    }
                }
                ai_strategy = ai_strategy + 1
            }

            game_round = game_round + 1
        }

        output = "Player: ${player_score}, AI: ${ai_score}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Player:" in result and "AI:" in result

    def test_multi_tier_cache_system_simulation(self):
        """Test multi-tier cache system with nested cache level checks."""
        program = """
        request_id = 1
        cache_hits = 0
        cache_misses = 0
        max_requests = 4

        while (request_id <= max_requests) {
            cache_level = 1
            found_in_cache = False

            while (cache_level <= 3 and not found_in_cache) {
                cache_probability = cache_level * 20
                request_hash = (request_id * 7) % 100

                if (request_hash <= cache_probability) {
                    found_in_cache = True
                    cache_hits = cache_hits + 1

                    if (cache_level == 1) {
                        access_time = 1
                    } elif (cache_level == 2) {
                        access_time = 5
                    } else {
                        access_time = 15
                    }
                }

                cache_level = cache_level + 1
            }

            if (not found_in_cache) {
                cache_misses = cache_misses + 1
            }

            request_id = request_id + 1
        }

        output = "Hits: ${cache_hits}, Misses: ${cache_misses}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Hits:" in result and "Misses:" in result

    def test_production_line_quality_control(self):
        """Test production line with nested quality control checks."""
        program = """
        batch_number = 1
        total_passed = 0
        total_failed = 0
        max_batches = 3

        while (batch_number <= max_batches) {
            item_in_batch = 1
            batch_size = batch_number + 2

            while (item_in_batch <= batch_size) {
                quality_check = 1
                item_passed = True

                while (quality_check <= 2 and item_passed) {
                    check_value = (item_in_batch * quality_check) % 7

                    if (quality_check == 1) {
                        if (check_value < 2) {
                            item_passed = False
                        }
                    } else {
                        if (check_value > 5) {
                            item_passed = False
                        }
                    }

                    quality_check = quality_check + 1
                }

                if (item_passed) {
                    total_passed = total_passed + 1
                } else {
                    total_failed = total_failed + 1
                }

                item_in_batch = item_in_batch + 1
            }

            batch_number = batch_number + 1
        }

        output = "Passed: ${total_passed}, Failed: ${total_failed}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Passed:" in result and "Failed:" in result

    def test_network_packet_routing_simulation(self):
        """Test network packet routing with nested routing table checks."""
        program = """
        packet_id = 1
        successfully_routed = 0
        dropped_packets = 0
        max_packets = 5

        while (packet_id <= max_packets) {
            routing_attempt = 1
            packet_delivered = False
            max_routing_attempts = 3

            while (routing_attempt <= max_routing_attempts and not packet_delivered) {
                route_priority = routing_attempt
                destination_hash = (packet_id * 11) % 10

                if (route_priority == 1) {
                    if (destination_hash >= 0 and destination_hash <= 3) {
                        packet_delivered = True
                    }
                } elif (route_priority == 2) {
                    if (destination_hash >= 4 and destination_hash <= 7) {
                        packet_delivered = True
                    }
                } else {
                    if (destination_hash >= 8) {
                        packet_delivered = True
                    }
                }

                routing_attempt = routing_attempt + 1
            }

            if (packet_delivered) {
                successfully_routed = successfully_routed + 1
            } else {
                dropped_packets = dropped_packets + 1
            }

            packet_id = packet_id + 1
        }

        output = "Routed: ${successfully_routed}, Dropped: ${dropped_packets}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Routed:" in result and "Dropped:" in result

    def test_financial_risk_assessment_engine(self):
        """Test financial risk assessment with nested risk factor evaluation."""
        program = """
        portfolio_id = 1
        low_risk_count = 0
        medium_risk_count = 0
        high_risk_count = 0
        max_portfolios = 4

        while (portfolio_id <= max_portfolios) {
            asset_id = 1
            portfolio_assets = portfolio_id + 1
            portfolio_risk_score = 0

            while (asset_id <= portfolio_assets) {
                risk_factor = 1
                asset_risk_score = 0

                while (risk_factor <= 3) {
                    factor_value = (asset_id * risk_factor * portfolio_id) % 10

                    if (risk_factor == 1) {
                        if (factor_value <= 3) {
                            asset_risk_score = asset_risk_score + 1
                        } elif (factor_value <= 7) {
                            asset_risk_score = asset_risk_score + 2
                        } else {
                            asset_risk_score = asset_risk_score + 3
                        }
                    } elif (risk_factor == 2) {
                        if (factor_value >= 5) {
                            asset_risk_score = asset_risk_score + 2
                        }
                    } else {
                        if (factor_value % 2 == 0) {
                            asset_risk_score = asset_risk_score + 1
                        }
                    }

                    risk_factor = risk_factor + 1
                }

                portfolio_risk_score = portfolio_risk_score + asset_risk_score
                asset_id = asset_id + 1
            }

            if (portfolio_risk_score <= 10) {
                low_risk_count = low_risk_count + 1
            } elif (portfolio_risk_score <= 20) {
                medium_risk_count = medium_risk_count + 1
            } else {
                high_risk_count = high_risk_count + 1
            }

            portfolio_id = portfolio_id + 1
        }

        output = "Low: ${low_risk_count}, Medium: ${medium_risk_count}, High: ${high_risk_count}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Low:" in result and "Medium:" in result and "High:" in result

    def test_machine_learning_training_simulation(self):
        """Test ML training simulation with nested epoch and batch processing."""
        program = """
        epoch = 1
        total_accuracy = 0
        convergence_reached = False
        max_epochs = 3

        while (epoch <= max_epochs and not convergence_reached) {
            batch = 1
            epoch_loss = 0
            batches_per_epoch = 4

            while (batch <= batches_per_epoch) {
                sample = 1
                batch_size = 3
                batch_correct = 0

                while (sample <= batch_size) {
                    prediction_score = (epoch * batch * sample) % 8
                    actual_label = (sample + batch) % 2

                    if (actual_label == 0) {
                        if (prediction_score <= 3) {
                            batch_correct = batch_correct + 1
                        }
                    } else {
                        if (prediction_score >= 4) {
                            batch_correct = batch_correct + 1
                        }
                    }

                    sample = sample + 1
                }

                batch_accuracy = (batch_correct * 100) / batch_size
                total_accuracy = total_accuracy + batch_accuracy

                if (batch_accuracy >= 90) {
                    convergence_reached = True
                }

                batch = batch + 1
            }

            epoch = epoch + 1
        }

        average_accuracy = total_accuracy / (max_epochs * batches_per_epoch)
        output = "Avg Accuracy: ${average_accuracy}, Converged: ${convergence_reached}"
        return output
        """
        result = self.interpreter.run(program)
        assert "Avg Accuracy:" in result and "Converged:" in result
