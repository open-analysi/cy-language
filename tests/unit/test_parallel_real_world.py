"""
Integration tests for parallel execution with real-world scenarios.

Tests parallel execution with MCP servers and realistic use cases.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.interpreter import Cy
from cy_language.ui.tools import default_registry


class TestParallelRealWorld:
    """Test parallel execution with real-world scenarios."""

    @pytest.mark.asyncio
    async def test_real_mcp_server_calls(self):
        """Test parallel execution with actual MCP server operations."""
        # Mock MCP server responses
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {"name": "fetch_data", "description": "Fetch data", "schema": {}},
                {"name": "process_data", "description": "Process data", "schema": {}},
                {"name": "analyze_data", "description": "Analyze data", "schema": {}},
            ]
        }
        mock_response.raise_for_status.return_value = None

        with patch("httpx.AsyncClient") as mock_client:
            # Mock MCP initialization
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock MCP tool calls
            async def mock_mcp_call(tool_name, *args, **kwargs):
                await asyncio.sleep(0.5)  # Simulate network delay
                if tool_name == "mcp::api::fetch_data":
                    return {"data": "fetched"}
                if tool_name == "mcp::api::process_data":
                    return {"processed": True}
                if tool_name == "mcp::api::analyze_data":
                    return {"analysis": "complete"}
                return {}

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=lambda url, **kwargs: Mock(
                    json=Mock(
                        return_value={
                            "result": mock_mcp_call(
                                kwargs.get("json", {}).get("tool", "")
                            )
                        }
                    )
                )
            )

            # Create Cy with MCP and parallel execution
            mcp_config = {"api": {"base_url": "http://test-api", "mcp_id": "api"}}
            cy = await Cy.create_async(
                mcp_servers=mcp_config, enable_parallel=True, parallel_threshold=2
            )

            # Mock the actual MCP tool execution
            cy.mcp_manager.call_mcp_tool = AsyncMock(side_effect=mock_mcp_call)

            cy_code = """
            # Fetch data from multiple MCP endpoints (should run in parallel)
            data1 = mcp::api::fetch_data()
            data2 = mcp::api::process_data()
            data3 = mcp::api::analyze_data()

            output = {
                "fetch": data1,
                "process": data2,
                "analyze": data3
            }
            return output
            """

            start = time.time()
            result = await cy.run_async(cy_code)
            duration = time.time() - start

            # Should contain all results
            assert "fetched" in result
            assert "processed" in result
            assert "analysis" in result

            # Should run in parallel (~0.5s instead of 1.5s)
            # Generous margin for CI/system contention
            assert duration < 2.0, (
                f"MCP calls should run in parallel, took {duration:.2f}s"
            )

    @pytest.mark.asyncio
    async def test_data_processing_pipeline(self):
        """Test realistic data processing pipeline with mixed dependencies."""

        # Mock data sources and processing functions
        async def fetch_sales():
            await asyncio.sleep(0.3)
            return [100, 200, 300, 400]

        async def fetch_customers():
            await asyncio.sleep(0.3)
            return ["alice", "bob", "charlie"]

        async def fetch_products():
            await asyncio.sleep(0.3)
            return {"widget": 10, "gadget": 20}

        def process_sales(data):
            return {"total": sum(data), "count": len(data)}

        def segment_customers(data):
            return {"segments": len(data), "first": data[0] if data else None}

        def generate_report(sales, customers, products):
            return {
                "sales_total": sales["total"],
                "customer_segments": customers["segments"],
                "product_count": len(products),
            }

        tools = {
            "fetch_sales_api": AsyncMock(side_effect=fetch_sales),
            "fetch_customers_api": AsyncMock(side_effect=fetch_customers),
            "fetch_products_api": AsyncMock(side_effect=fetch_products),
            "process_sales": Mock(side_effect=process_sales),
            "segment_customers": Mock(side_effect=segment_customers),
            "generate_report": Mock(side_effect=generate_report),
        }

        cy_code = """
        # Fetch data from multiple sources (parallel)
        sales_data = fetch_sales_api()
        customer_data = fetch_customers_api()
        product_data = fetch_products_api()

        # Process data (some parallel, some sequential)
        sales_summary = process_sales(sales_data)
        customer_segments = segment_customers(customer_data)

        # Combine results (depends on previous)
        report = generate_report(sales_summary, customer_segments, product_data)
        output = report
        return output
        """

        # Test with parallel execution
        cy_parallel = await Cy.create_async(tools=tools, enable_parallel=True)

        start = time.time()
        result_parallel = await cy_parallel.run_async(cy_code)
        duration_parallel = time.time() - start

        # Verify correctness
        assert "sales_total" in result_parallel
        assert "1000" in result_parallel  # Sum of sales
        assert "customer_segments" in result_parallel
        assert "3" in result_parallel  # Number of customers

        # Reset mocks
        for tool in tools.values():
            if hasattr(tool, "reset_mock"):
                tool.reset_mock()

        # Test with sequential execution for comparison
        cy_sequential = await Cy.create_async(tools=tools, enable_parallel=False)

        start = time.time()
        result_sequential = await cy_sequential.run_async(cy_code)
        duration_sequential = time.time() - start

        # Results should be identical
        assert result_parallel == result_sequential

        # Parallel should be faster
        assert duration_parallel < duration_sequential
        # First phase (3 fetches) should run in parallel
        # Generous margins for CI/system contention
        assert duration_parallel < 1.5, (
            f"Parallel pipeline took {duration_parallel:.2f}s"
        )
        assert duration_sequential > 0.5, (
            f"Sequential pipeline took {duration_sequential:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_mixed_tool_types(self):
        """Test with different tool types (sync, async, CPU-bound, I/O-bound)."""
        import hashlib

        # Different types of operations
        async def io_bound_op(data):
            """Simulate I/O bound operation."""
            await asyncio.sleep(0.2)
            return f"io_{data}"

        def cpu_bound_op(data):
            """Simulate CPU-bound operation."""
            # Do some actual computation
            result = hashlib.md5(str(data).encode()).hexdigest()
            return result[:8]

        async def network_op(url):
            """Simulate network operation."""
            await asyncio.sleep(0.3)
            return f"response_from_{url}"

        def sync_transform(data):
            """Simple synchronous transformation."""
            return data.upper() if isinstance(data, str) else str(data)

        tools = {
            "io_read": AsyncMock(side_effect=io_bound_op),
            "cpu_process": Mock(side_effect=cpu_bound_op),
            "fetch_url": AsyncMock(side_effect=network_op),
            "transform": Mock(side_effect=sync_transform),
        }

        cy = await Cy.create_async(tools=tools, enable_parallel=True)

        cy_code = """
        # Mixed operation types that can run in parallel
        io_result = io_read("file1")
        cpu_result = cpu_process("data123")
        net_result = fetch_url("api.example.com")

        # Transform results (depends on previous)
        io_transformed = transform(io_result)
        net_transformed = transform(net_result)

        output = {
            "io": io_transformed,
            "cpu": cpu_result,
            "net": net_transformed
        }
        return output
        """

        start = time.time()
        result = await cy.run_async(cy_code)
        duration = time.time() - start

        # Verify all operations completed
        assert "IO_FILE1" in result
        assert "RESPONSE_FROM_API.EXAMPLE.COM" in result

        # Should complete in time of slowest async operation (~0.3s)
        # Generous margin for CI/system contention
        assert duration < 2.0, f"Mixed operations took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_api_aggregation_pattern(self):
        """Test common API aggregation pattern."""

        # Simulate different API endpoints with varying response times
        async def user_api():
            await asyncio.sleep(0.2)
            return {"id": 1, "name": "Alice", "role": "admin"}

        async def permissions_api(user_id):
            await asyncio.sleep(0.15)
            return ["read", "write", "delete"]

        async def settings_api(user_id):
            await asyncio.sleep(0.1)
            return {"theme": "dark", "notifications": True}

        async def activity_api(user_id):
            await asyncio.sleep(0.25)
            return {"last_login": "2024-01-15", "actions": 42}

        def merge_user_data(user, perms, settings, activity):
            return {
                **user,
                "permissions": perms,
                "settings": settings,
                "activity": activity,
            }

        tools = {
            "fetch_user": AsyncMock(side_effect=user_api),
            "fetch_permissions": AsyncMock(side_effect=permissions_api),
            "fetch_settings": AsyncMock(side_effect=settings_api),
            "fetch_activity": AsyncMock(side_effect=activity_api),
            "merge_data": Mock(side_effect=merge_user_data),
        }

        cy = await Cy.create_async(tools=tools, enable_parallel=True)

        cy_code = """
        # First fetch user
        user = fetch_user()
        user_id = user["id"]

        # Then fetch related data in parallel
        permissions = fetch_permissions(user_id)
        settings = fetch_settings(user_id)
        activity = fetch_activity(user_id)

        # Merge all data
        complete_profile = merge_data(user, permissions, settings, activity)
        output = complete_profile
        return output
        """

        start = time.time()
        result = await cy.run_async(cy_code)
        duration = time.time() - start

        # Verify complete profile
        assert "Alice" in result
        assert "permissions" in result
        assert "settings" in result
        assert "activity" in result

        # Should take ~0.45s (0.2s for user, then 0.25s for parallel fetches)
        # Not 0.7s if everything was sequential
        # Generous margin for CI/system contention
        assert duration < 2.0, f"API aggregation took {duration:.2f}s (expected <2.0s)"

    @pytest.mark.asyncio
    async def test_batch_processing_pattern(self):
        """Test batch processing with parallel execution."""
        processed_items = []

        async def process_item(item):
            """Process a single item."""
            await asyncio.sleep(0.1)
            processed_items.append(item)
            return item * 2

        def batch_complete(results):
            """Finalize batch processing."""
            return {
                "total": sum(results),
                "count": len(results),
                "items_processed": len(processed_items),
            }

        tools = {
            "process": AsyncMock(side_effect=process_item),
            "finalize": Mock(side_effect=batch_complete),
        }

        cy = await Cy.create_async(tools=tools, enable_parallel=True)

        # Process batch of items
        cy_code = """
        # Process multiple items (should parallelize)
        item1 = process(10)
        item2 = process(20)
        item3 = process(30)
        item4 = process(40)
        item5 = process(50)

        # Collect results
        results = [item1, item2, item3, item4, item5]

        # Finalize batch
        summary = finalize(results)
        output = summary
        return output
        """

        start = time.time()
        result = await cy.run_async(cy_code)
        duration = time.time() - start

        # Verify batch processing
        assert "total" in result
        assert "300" in result  # (10+20+30+40+50) * 2
        assert "items_processed" in result
        assert "5" in result

        # Should complete in ~0.1s (parallel), not 0.5s (sequential)
        # Generous margin for CI/system contention
        assert duration < 1.5, f"Batch processing took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_database_query_aggregation(self):
        """Test parallel database query pattern."""

        async def query_db(query_type):
            """Simulate database query."""
            delays = {"users": 0.2, "orders": 0.3, "products": 0.15, "inventory": 0.25}
            await asyncio.sleep(delays.get(query_type, 0.1))

            results = {
                "users": [{"id": 1}, {"id": 2}],
                "orders": [{"id": 101}, {"id": 102}, {"id": 103}],
                "products": [{"id": "A1"}, {"id": "B2"}],
                "inventory": {"A1": 100, "B2": 50},
            }
            return results.get(query_type, [])

        def join_results(users, orders, products, inventory):
            """Join query results."""
            return {
                "user_count": len(users),
                "order_count": len(orders),
                "product_count": len(products),
                "total_inventory": sum(inventory.values())
                if isinstance(inventory, dict)
                else 0,
            }

        async def query_users():
            return await query_db("users")

        async def query_orders():
            return await query_db("orders")

        async def query_products():
            return await query_db("products")

        async def query_inventory():
            return await query_db("inventory")

        tools = {
            "query_users": AsyncMock(side_effect=query_users),
            "query_orders": AsyncMock(side_effect=query_orders),
            "query_products": AsyncMock(side_effect=query_products),
            "query_inventory": AsyncMock(side_effect=query_inventory),
            "join_data": Mock(side_effect=join_results),
        }

        cy = await Cy.create_async(tools=tools, enable_parallel=True)

        cy_code = """
        # Execute multiple database queries in parallel
        users = query_users()
        orders = query_orders()
        products = query_products()
        inventory = query_inventory()

        # Join all results
        report = join_data(users, orders, products, inventory)
        output = report
        return output
        """

        start = time.time()
        result = await cy.run_async(cy_code)
        duration = time.time() - start

        # Verify aggregated results
        assert "user_count" in result
        assert "2" in result
        assert "order_count" in result
        assert "3" in result
        assert "total_inventory" in result
        assert "150" in result

        # Should complete in time of slowest query (~0.3s), not sum of all
        # Generous margin for CI/system contention
        assert duration < 2.0, f"Database queries took {duration:.2f}s"

    @pytest.mark.asyncio
    async def test_simple_parallel_timing_demo(self):
        """Simplest possible test: sleep calls comparing sequential vs parallel."""

        # Create a simple async sleep tool
        async def sleep_one_second():
            await asyncio.sleep(1.0)
            return "done"

        tools = {"sleep_one": sleep_one_second}

        # Test with 2 calls
        test_code_2 = """
        result1 = sleep_one()
        result2 = sleep_one()
        output = "completed"
        return output
        """

        # Test with 3 calls
        test_code_3 = """
        result1 = sleep_one()
        result2 = sleep_one()
        result3 = sleep_one()
        output = "completed"
        return output
        """

        print("\n🧪 Simple Parallel Timing Demo:\n")

        # Test 2 calls
        cy_seq = await Cy.create_async(tools=tools, enable_parallel=False)
        start = time.time()
        await cy_seq.run_async(test_code_2)
        seq_time_2 = time.time() - start

        cy_par = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )
        start = time.time()
        await cy_par.run_async(test_code_2)
        par_time_2 = time.time() - start

        print("  2 sleep calls:")
        print(f"    Sequential: {seq_time_2:.2f}s")
        print(f"    Parallel:   {par_time_2:.2f}s")
        print(f"    Speedup:    {seq_time_2 / par_time_2:.2f}x\n")

        # Test 3 calls
        cy_seq = await Cy.create_async(tools=tools, enable_parallel=False)
        start = time.time()
        await cy_seq.run_async(test_code_3)
        seq_time_3 = time.time() - start

        cy_par = await Cy.create_async(
            tools=tools, enable_parallel=True, parallel_threshold=2
        )
        start = time.time()
        await cy_par.run_async(test_code_3)
        par_time_3 = time.time() - start

        print("  3 sleep calls:")
        print(f"    Sequential: {seq_time_3:.2f}s")
        print(f"    Parallel:   {par_time_3:.2f}s")
        print(f"    Speedup:    {seq_time_3 / par_time_3:.2f}x")

        # Assertions
        assert seq_time_2 > 1.5, f"2-call sequential too fast: {seq_time_2}"
        assert par_time_2 < 3.0, f"2-call parallel too slow: {par_time_2}"
        assert seq_time_3 > 2.5, f"3-call sequential too fast: {seq_time_3}"
        assert par_time_3 < 3.0, f"3-call parallel too slow: {par_time_3}"

    @pytest.mark.asyncio
    async def test_mcp_domain_character_counting_live_timing(self):
        """Live timing test: 10 domain string character counting with MCP demo service."""

        # Parallel version - independent calls
        parallel_code = """
        result1 = mcp::demo::count_characters(text="google.com")
        result2 = mcp::demo::count_characters(text="microsoft.com")
        result3 = mcp::demo::count_characters(text="amazon.com")
        result4 = mcp::demo::count_characters(text="github.com")
        result5 = mcp::demo::count_characters(text="stackoverflow.com")

        len1 = len(result1)
        len2 = len(result2)
        len3 = len(result3)
        len4 = len(result4)
        len5 = len(result5)

        count = len1 + len2 + len3 + len4 + len5

        output = count
        return output
        """

        # Loop version - always sequential (your original pattern)
        loop_code = """
        domains = ["google.com", "microsoft.com", "amazon.com", "github.com", "stackoverflow.com"]

        i = 0
        count = 0
        while (i < len(domains)) {
            result = mcp::demo::count_characters(text=domains[i])
            result_len = len(result)
            count = count + result_len
            i = i + 1
        }

        output = count
        return output
        """

        # Mock MCP calls with simulated delay
        async def mock_mcp_call(server, tool, **kwargs):
            await asyncio.sleep(0.1)  # Simulate network delay
            # The 'tool' parameter contains the actual tool parameters
            text = tool["text"] if isinstance(tool, dict) and "text" in tool else ""
            return text  # Return the original text so len() works correctly

        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(side_effect=mock_mcp_call)
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::demo::count_characters": {
                "name": "count_characters",
                "parameters": ["text"],
            }
        }

        # Test sequential execution (parallel disabled)
        cy_sequential = await Cy.create_async(
            enable_parallel=False, tools=default_registry.get_tools_dict()
        )
        cy_sequential.mcp_manager = mock_mcp_manager

        start = time.time()
        result_sequential_parallel = await cy_sequential.run_async(parallel_code)
        duration_sequential_parallel = time.time() - start

        # Reset mock
        mock_mcp_manager.call_mcp_tool.reset_mock()

        # Test parallel execution
        cy_parallel = await Cy.create_async(
            enable_parallel=True,
            parallel_threshold=2,
            tools=default_registry.get_tools_dict(),
        )
        cy_parallel.mcp_manager = mock_mcp_manager

        start = time.time()
        result_parallel_parallel = await cy_parallel.run_async(parallel_code)
        duration_parallel_parallel = time.time() - start

        # Reset mock
        mock_mcp_manager.call_mcp_tool.reset_mock()

        # Test loop version (always sequential even with parallel enabled)
        cy_loop = await Cy.create_async(
            enable_parallel=True,
            parallel_threshold=2,
            tools=default_registry.get_tools_dict(),
        )
        cy_loop.mcp_manager = mock_mcp_manager

        start = time.time()
        result_loop = await cy_loop.run_async(loop_code)
        duration_loop = time.time() - start

        print("\n🧪 MCP Domain Character Counting Live Timing Test:")
        print(
            f"   Independent calls (sequential mode): {duration_sequential_parallel:.3f}s"
        )
        print(
            f"   Independent calls (parallel mode):   {duration_parallel_parallel:.3f}s"
        )
        print(f"   Loop version (always sequential):    {duration_loop:.3f}s")

        # Debug: show actual results
        print(
            f"   Results: seq={result_sequential_parallel}, par={result_parallel_parallel}, loop={result_loop}"
        )

        # Verify correctness - all should produce same result
        expected_total = sum(
            len(domain)
            for domain in [
                "google.com",
                "microsoft.com",
                "amazon.com",
                "github.com",
                "stackoverflow.com",
            ]
        )
        print(f"   Expected: {expected_total}")

        assert result_sequential_parallel == str(expected_total)
        assert result_parallel_parallel == str(expected_total)
        assert result_loop == str(expected_total)

        # Verify timing improvements
        speedup = duration_sequential_parallel / duration_parallel_parallel
        print(f"   🚀 Parallel speedup: {speedup:.2f}x")

        # Parallel should be faster than sequential
        assert speedup > 1.5, f"Expected >1.5x speedup, got {speedup:.2f}x"

        # Loop version should be similar to sequential (no parallelization)
        loop_vs_sequential_ratio = (
            abs(duration_loop - duration_sequential_parallel)
            / duration_sequential_parallel
        )
        assert loop_vs_sequential_ratio < 0.5, (
            f"Loop timing should be similar to sequential, got {loop_vs_sequential_ratio:.2f} difference ratio"
        )
