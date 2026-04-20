"""
Integration tests for Cy interpreter MCP configuration and initialization.

These tests verify that the Cy interpreter correctly handles MCP server
configuration and integrates MCP manager throughout the execution pipeline.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cy_language.interpreter import Cy


class TestCyInterpreterMCPConfiguration:
    """Test Cy interpreter MCP server configuration."""

    @pytest.mark.asyncio
    async def test_cy_init_with_mcp_servers(self):
        """Test Cy initialization with MCP server configuration."""
        servers = {
            "demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"},
            "virustotal": {"base_url": "http://localhost:8000", "mcp_id": "virustotal"},
        }

        # Now requires async initialization for MCP servers
        cy = await Cy.create_async(mcp_servers=servers)

        # After implementation, these assertions should pass:
        assert cy.mcp_manager is not None
        assert cy.mcp_manager.servers == servers

    def test_cy_init_without_mcp_servers(self):
        """Test Cy initialization without MCP server configuration."""
        cy = Cy()

        # Should not create MCP manager when no servers configured
        assert cy.mcp_manager is None

    @pytest.mark.asyncio
    async def test_cy_init_with_empty_mcp_servers(self):
        """Test Cy initialization with empty MCP server configuration."""
        cy = await Cy.create_async(mcp_servers={})

        # Should not create MCP manager for empty server config
        assert cy.mcp_manager is None

    def test_cy_init_with_none_mcp_servers(self):
        """Test Cy initialization with None MCP server configuration."""
        cy = Cy(mcp_servers=None)

        assert cy.mcp_manager is None


class TestMCPManagerInitialization:
    """Test MCP manager initialization during Cy setup."""

    @pytest.mark.asyncio
    async def test_mcp_manager_initialization_called(self):
        """Test that MCP manager initialization is called during Cy setup."""
        servers = {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}

        with patch("cy_language.mcp_manager.MCPManager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.initialize = AsyncMock()
            mock_manager_class.return_value = mock_manager_instance

            cy = await Cy.create_async(mcp_servers=servers)

            # After implementation, these should pass:
            mock_manager_class.assert_called_once_with(servers)
            mock_manager_instance.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_mcp_manager_initialization_error_handling(self):
        """Test handling of MCP manager initialization errors."""
        servers = {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}

        with patch("cy_language.mcp_manager.MCPManager") as mock_manager_class:
            mock_manager_instance = Mock()
            mock_manager_instance.initialize = AsyncMock(
                side_effect=Exception("Network error")
            )
            mock_manager_class.return_value = mock_manager_instance

            # Should handle initialization errors gracefully
            # Implementation may choose to log warning or raise exception
            with pytest.raises(Exception, match="Network error"):
                await Cy.create_async(mcp_servers=servers)


class TestExecutionPlanMCPIntegration:
    """Test MCP manager integration with execution plan execution."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Create a mocked MCP manager."""
        manager = Mock()
        manager.call_mcp_tool = AsyncMock(return_value="mocked_result")
        # Add tools_cache for tool resolution
        manager.tools_cache = {}
        return manager

    def test_execution_plan_receives_mcp_manager(self, mock_mcp_manager):
        """Test that execution plan receives MCP manager."""
        # Create Cy instance normally, then replace manager
        cy = Cy()
        cy.mcp_manager = mock_mcp_manager

        # Test with a simple program that doesn't use MCP tools first
        simple_program = """
        result = "hello"
        output = "Result: ${result}"
        return output
        """

        with patch("cy_language.interpreter.execute_plan") as mock_execute:
            mock_execute.return_value = "mocked_output"

            output = cy.run(simple_program)

            # Verify execute_plan was called
            mock_execute.assert_called_once()
            call_kwargs = mock_execute.call_args[1]
            assert call_kwargs["mcp_manager"] is mock_mcp_manager
            assert output == '"mocked_output"'

    def test_execution_without_mcp_manager(self):
        """Test normal execution when no MCP manager is configured."""
        cy = Cy()

        program = """
        result = "hello world"
        output = "Result: ${result}"
        return output
        """

        output = cy.run(program)
        assert output == '"Result: hello world"'


class TestMCPServerConfigValidation:
    """Test validation of MCP server configurations."""

    @pytest.mark.asyncio
    async def test_valid_server_config_format(self):
        """Test that valid server configurations are accepted."""
        valid_configs = [
            {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}},
            {
                "demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"},
                "virustotal": {
                    "base_url": "http://localhost:8000",
                    "mcp_id": "virustotal",
                },
            },
            {
                "custom": {
                    "base_url": "https://api.example.com",
                    "mcp_id": "custom_service",
                }
            },
        ]

        for config in valid_configs:
            # Should not raise exceptions for valid configs
            cy = await Cy.create_async(mcp_servers=config)
            # After implementation: assert cy.mcp_manager is not None

    @pytest.mark.asyncio
    async def test_invalid_server_config_format(self):
        """Test handling of invalid server configurations."""
        invalid_configs = [
            {"demo": {"base_url": "http://localhost:8000"}},  # Missing mcp_id
            {"demo": {"mcp_id": "demo"}},  # Missing base_url
            {"demo": {}},  # Empty config
            {"demo": "invalid_format"},  # String instead of dict
        ]

        for config in invalid_configs:
            # Implementation should either handle gracefully or raise clear error
            try:
                cy = await Cy.create_async(mcp_servers=config)
                # If no exception, initialization should handle invalid configs
            except (ValueError, TypeError) as e:
                # Clear error message expected
                assert "base_url" in str(e) or "mcp_id" in str(e)


class TestMCPIntegrationWithExistingFeatures:
    """Test MCP integration with existing Cy language features."""

    @pytest.fixture
    def mock_mcp_manager(self):
        """Mocked MCP manager."""
        manager = Mock()
        manager.call_mcp_tool = AsyncMock(
            return_value={"status": "success", "data": [1, 2, 3]}
        )
        # Add tools_cache for tool resolution
        manager.tools_cache = {
            "mcp::demo::get_data": {"name": "get_data", "description": "Get demo data"},
            "mcp::demo::process": {"name": "process", "description": "Process data"},
        }
        return manager

    @pytest.mark.asyncio
    async def test_mcp_with_native_tools(self, mock_mcp_manager):
        """Test MCP integration with existing native tools."""

        def native_len(lst):
            return len(lst)

        # Make mock async compatible
        mock_mcp_manager.initialize = AsyncMock()

        # Create with async factory and tools
        with patch("cy_language.mcp_manager.MCPManager", return_value=mock_mcp_manager):
            cy = await Cy.create_async(
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}},
                tools={"native_len": native_len},
            )

        program = """
        mcp_data = mcp::demo::get_data()
        data_length = native_len(mcp_data["data"])
        output = "Data length: ${data_length}"
        return output
        """

        output = await cy.run_async(program)
        # After implementation: assert output == "Data length: 3"

    @pytest.mark.asyncio
    async def test_mcp_with_interpolation_modes(self, mock_mcp_manager):
        """Test MCP tools with different interpolation modes."""
        # Make mock async compatible
        mock_mcp_manager.initialize = AsyncMock()

        with patch("cy_language.mcp_manager.MCPManager", return_value=mock_mcp_manager):
            cy = await Cy.create_async(
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}},
                interpolation_mode="csv",
            )

        program = """
        data = mcp::demo::get_data()
        output = "CSV Data: ${data|csv}"
        return output
        """

        output = await cy.run_async(program)
        # After implementation: should format MCP result as CSV

    @pytest.mark.asyncio
    async def test_mcp_with_external_variables(self, mock_mcp_manager):
        """Test MCP tools with external variables."""
        mock_mcp_manager.call_mcp_tool = AsyncMock(
            side_effect=lambda tool, kwargs: f"Processed: {kwargs['input']}"
        )
        # Make mock async compatible
        mock_mcp_manager.initialize = AsyncMock()

        with patch("cy_language.mcp_manager.MCPManager", return_value=mock_mcp_manager):
            cy = await Cy.create_async(
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}},
                variables={"external_data": "test_input"},
            )

        program = """
        result = mcp::demo::process(input=external_data)
        output = "Result: ${result}"
        return output
        """

        output = await cy.run_async(program)
        # After implementation: assert output == "Result: Processed: test_input"


class TestMCPConfigurationInheritance:
    """Test MCP configuration inheritance and scope."""

    @pytest.mark.asyncio
    async def test_mcp_manager_shared_across_runs(self):
        """Test that MCP manager is shared across multiple program runs."""
        mock_mcp_manager = Mock()
        mock_mcp_manager.call_mcp_tool = AsyncMock(return_value="result1")
        mock_mcp_manager.initialize = AsyncMock()
        # Add tools_cache for tool resolution
        mock_mcp_manager.tools_cache = {
            "mcp::demo::tool1": {"name": "tool1"},
            "mcp::demo::tool2": {"name": "tool2"},
        }

        with patch("cy_language.mcp_manager.MCPManager", return_value=mock_mcp_manager):
            cy = await Cy.create_async(
                mcp_servers={"demo": {"base_url": "http://test", "mcp_id": "demo"}}
            )

        program1 = "result = mcp::demo::tool1()\noutput = result\nreturn output"
        program2 = "result = mcp::demo::tool2()\noutput = result\nreturn output"

        # First run
        await cy.run_async(program1)
        call_count_1 = mock_mcp_manager.call_mcp_tool.call_count

        # Second run should use same manager
        mock_mcp_manager.call_mcp_tool.return_value = "result2"
        await cy.run_async(program2)
        call_count_2 = mock_mcp_manager.call_mcp_tool.call_count

        # Both runs should have used the same manager
        assert call_count_2 == call_count_1 + 1

    @pytest.mark.asyncio
    async def test_different_cy_instances_different_managers(self):
        """Test that different Cy instances have separate MCP managers."""
        servers1 = {"demo": {"base_url": "http://localhost:8000", "mcp_id": "demo"}}
        servers2 = {"other": {"base_url": "http://localhost:8001", "mcp_id": "other"}}

        cy1 = await Cy.create_async(mcp_servers=servers1)
        cy2 = await Cy.create_async(mcp_servers=servers2)

        # After implementation:
        assert cy1.mcp_manager is not cy2.mcp_manager
        assert cy1.mcp_manager.servers != cy2.mcp_manager.servers
