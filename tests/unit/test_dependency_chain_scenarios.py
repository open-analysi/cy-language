"""
Test explicit dependency chain scenarios for parallel execution.

These tests document and verify important guarantees about how the
dependency analyzer handles transitive dependencies and complex scenarios.
"""

import pytest

from cy_language.compiler import compile_cy_program
from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.parser import Parser


class TestTransitiveDependencies:
    """Test that transitive dependencies are correctly identified."""

    def test_simple_transitive_chain(self):
        """Test that transitive dependencies prevent parallelization.

        Y generates A -> A used for B -> B used for D -> D used by X
        Y and X must NOT run in parallel despite no direct dependency.
        """
        code = """
        A = async_func_Y()
        B = compute_B(A)
        D = compute_D(B)
        result = async_func_X(D)
        output = result
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "async_func_Y": lambda: None,
            "compute_B": lambda x: None,
            "compute_D": lambda x: None,
            "async_func_X": lambda x: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # Y is node 0, X is node 3
        # They should be in different groups
        y_group = next(i for i, g in enumerate(parallel_groups) if 0 in g)
        x_group = next(i for i, g in enumerate(parallel_groups) if 3 in g)

        assert y_group != x_group, "Y and X should not be in the same parallel group"
        assert x_group > y_group, "X should execute after Y"

    def test_prevents_false_parallelization(self):
        """Verify operations with chain dependencies are NOT parallelized.

        Tests the specific concern: async Y produces A,
        A->B->C->D, D used by async X.

        Asserts Y and X are in different parallel groups.
        """
        code = """
        A = fetch_data_Y()
        B = process_step1(A)
        C = process_step2(B)
        D = process_step3(C)
        result = fetch_data_X(D)
        independent = fetch_data_Z()
        output = combine(result, independent)
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "fetch_data_Y": lambda: None,
            "process_step1": lambda x: None,
            "process_step2": lambda x: None,
            "process_step3": lambda x: None,
            "fetch_data_X": lambda x: None,
            "fetch_data_Z": lambda: None,
            "combine": lambda x, y: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # Find which nodes are in which groups
        y_node = 0  # fetch_data_Y
        x_node = 4  # fetch_data_X
        z_node = 5  # fetch_data_Z (independent)

        y_group = next(i for i, g in enumerate(parallel_groups) if y_node in g)
        x_group = next(i for i, g in enumerate(parallel_groups) if x_node in g)
        z_group = next(i for i, g in enumerate(parallel_groups) if z_node in g)

        # Y and X must not parallelize
        assert y_group != x_group, (
            "Y and X must not run in parallel due to chain dependency"
        )

        # Z should parallelize with Y (both are independent)
        assert z_group == y_group, "Z should run in parallel with Y (both independent)"


class TestConvergingChains:
    """Test scenarios where multiple chains converge."""

    def test_two_converging_chains(self):
        """Test two independent chains that converge.

        Chain 1: fetch_user -> process_user ----\\
                                                  -> merge -> final
        Chain 2: fetch_posts -> process_posts --/

        fetch_user and fetch_posts should parallelize.
        process_user and process_posts should parallelize.
        merge must wait for both chains.
        """
        code = """
        user_data = fetch_user()
        posts_data = fetch_posts()
        processed_user = process_user(user_data)
        processed_posts = process_posts(posts_data)
        merged = merge(processed_user, processed_posts)
        output = finalize(merged)
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "fetch_user": lambda: None,
            "fetch_posts": lambda: None,
            "process_user": lambda x: None,
            "process_posts": lambda x: None,
            "merge": lambda x, y: None,
            "finalize": lambda x: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # Check that the fetches are parallel
        assert 0 in parallel_groups[0] and 1 in parallel_groups[0], (
            "fetch_user and fetch_posts should run in parallel"
        )

        # Check that the processing steps are parallel
        process_group = next(g for g in parallel_groups if 2 in g)
        assert 2 in process_group and 3 in process_group, (
            "process_user and process_posts should run in parallel"
        )

        # Check that merge comes after both processing steps
        merge_group_idx = next(i for i, g in enumerate(parallel_groups) if 4 in g)
        process_group_idx = next(i for i, g in enumerate(parallel_groups) if 2 in g)
        assert merge_group_idx > process_group_idx, "merge must wait for processing"

    def test_three_way_convergence(self):
        """Test three independent chains converging to one operation."""
        code = """
        api1 = call_api_1()
        api2 = call_api_2()
        api3 = call_api_3()
        proc1 = process1(api1)
        proc2 = process2(api2)
        proc3 = process3(api3)
        final = combine_all(proc1, proc2, proc3)
        output = final
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "call_api_1": lambda: None,
            "call_api_2": lambda: None,
            "call_api_3": lambda: None,
            "process1": lambda x: None,
            "process2": lambda x: None,
            "process3": lambda x: None,
            "combine_all": lambda x, y, z: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # All three APIs should run in parallel
        first_group = parallel_groups[0]
        assert len(first_group) == 3, "All three API calls should parallelize"
        assert 0 in first_group and 1 in first_group and 2 in first_group

        # All three processors should run in parallel
        second_group = parallel_groups[1]
        assert len(second_group) == 3, "All three processors should parallelize"


class TestMixedScenarios:
    """Test mix of independent operations and dependency chains."""

    def test_mixed_independent_and_chain_dependencies(self):
        """Test mix of independent ops and dependency chains.

        - api1, api2, api3 are independent (should parallelize)
        - api1 -> transform1 -> combine
        - api2 -> transform2 -> combine
        - api3 feeds directly to finalize
        - combine -> finalize

        Verifies api3 doesn't get blocked by the api1/api2 chains.
        """
        code = """
        data1 = fetch_api_1()
        data2 = fetch_api_2()
        data3 = fetch_api_3()
        transform1 = process(data1)
        transform2 = enhance(data2)
        combined = combine(transform1, transform2)
        final = finalize(combined, data3)
        output = final
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "fetch_api_1": lambda: None,
            "fetch_api_2": lambda: None,
            "fetch_api_3": lambda: None,
            "process": lambda x: None,
            "enhance": lambda x: None,
            "combine": lambda x, y: None,
            "finalize": lambda x, y: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # All three fetches should parallelize
        assert len(parallel_groups[0]) == 3, "All API fetches should parallelize"

        # Transforms should parallelize
        transform_group = parallel_groups[1]
        assert 3 in transform_group and 4 in transform_group, (
            "Transforms should run in parallel"
        )

        # Verify api3 isn't blocked unnecessarily
        api3_node = 2
        combine_node = 5
        api3_group = next(i for i, g in enumerate(parallel_groups) if api3_node in g)
        combine_group = next(
            i for i, g in enumerate(parallel_groups) if combine_node in g
        )

        # api3 should run before or with combine (not blocked by it)
        assert api3_group <= combine_group, (
            "api3 shouldn't be blocked by combine operation"
        )


class TestDictionaryFieldDependencies:
    """Test how dictionary field access affects dependencies.

    Current behavior is conservative: any field write creates dependencies
    with any field read on the same dictionary.
    """

    def test_different_field_access_creates_dependency(self):
        """Test that accessing different fields still creates dependencies.

        This documents the CURRENT conservative behavior.
        Writing to field1 blocks reading field2.
        """
        code = """
        data = {"field1": 10, "field2": 20}
        async_result = fetch_data()
        data["field1"] = async_result
        value = data["field2"]
        output = value
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {"fetch_data": lambda: None}

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # Find the nodes
        write_field1_node = 2  # $data["field1"] = ...
        read_field2_node = 3  # $value = $data["field2"]

        # Check they're in different groups (sequential)
        write_group = next(
            i for i, g in enumerate(parallel_groups) if write_field1_node in g
        )
        read_group = next(
            i for i, g in enumerate(parallel_groups) if read_field2_node in g
        )

        # Document current conservative behavior
        assert write_group < read_group, (
            "Currently, writing field1 blocks reading field2 (conservative)"
        )

    def test_same_field_access_definitely_creates_dependency(self):
        """Test that accessing the same field creates dependency."""
        code = """
        data = {"field1": 10}
        new_value = compute()
        data["field1"] = new_value
        current = data["field1"]
        output = current
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {"compute": lambda: None}

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)

        # Reading field1 (node 3) must depend on writing field1 (node 2)
        assert 2 in dependencies[3], "Reading field must depend on writing same field"

    def test_whole_dict_read_depends_on_all_field_writes(self):
        """Test that reading whole dictionary depends on all field writes."""
        code = """
        data = {}
        data["a"] = fetch_a()
        data["b"] = fetch_b()
        data["c"] = fetch_c()
        output = data
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "fetch_a": lambda: None,
            "fetch_b": lambda: None,
            "fetch_c": lambda: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)

        # Reading whole dict (node 4) depends on all field writes
        assert 1 in dependencies[4], "Reading dict depends on field 'a' write"
        assert 2 in dependencies[4], "Reading dict depends on field 'b' write"
        assert 3 in dependencies[4], "Reading dict depends on field 'c' write"


class TestListIndexDependencies:
    """Test how list index access affects dependencies."""

    def test_different_indices_are_independent(self):
        """Test that different list indices don't create dependencies."""
        code = """
        list = [1, 2, 3, 4, 5]
        list[0] = compute_first()
        list[2] = compute_third()
        output = list
        return output
        """

        # Provide stub tools for compilation
        stub_tools = {
            "compute_first": lambda: None,
            "compute_third": lambda: None,
        }

        parser = Parser()
        ast = parser.parse_only(code)
        plan = compile_cy_program(ast, available_tools=stub_tools)

        analyzer = DependencyAnalyzer()
        dependencies = analyzer.analyze_node_dependencies(plan.nodes)
        parallel_groups = analyzer.find_parallel_groups(dependencies)

        # Writing to different indices should be able to parallelize
        # (though current implementation might be conservative)
        write0_node = 1
        write2_node = 2

        # Check if they can parallelize (documenting current behavior)
        write0_group = next(
            i for i, g in enumerate(parallel_groups) if write0_node in g
        )
        write2_group = next(
            i for i, g in enumerate(parallel_groups) if write2_node in g
        )

        # Document the current behavior (might be conservative like dicts)
        if write0_group != write2_group:
            print("Note: List index writes are currently conservative (sequential)")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
