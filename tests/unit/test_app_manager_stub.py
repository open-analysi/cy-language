"""
Unit tests for AppIntegrationManager stub.

These tests verify the stub implementation of AppIntegrationManager
works as expected for the namespace system foundation.
"""

import pytest

from cy_language.app_manager import AppIntegrationManager


class TestAppIntegrationManagerStub:
    """Test stub implementation of AppIntegrationManager."""

    def test_create_app_manager(self):
        """Test that AppIntegrationManager can be instantiated."""
        manager = AppIntegrationManager()

        assert manager is not None
        assert hasattr(manager, "integrations")
        assert hasattr(manager, "tools_cache")

    @pytest.mark.asyncio
    async def test_initialize_app_manager(self):
        """Test that initialize() can be called without errors."""
        manager = AppIntegrationManager()

        await manager.initialize()

        assert manager._initialized is True

    def test_get_all_tools_empty(self):
        """Test that get_all_tools() returns empty dict."""
        manager = AppIntegrationManager()

        tools = manager.get_all_tools()

        assert isinstance(tools, dict)
        assert len(tools) == 0

    @pytest.mark.asyncio
    async def test_call_app_tool_not_implemented(self):
        """Test that call_app_tool() raises NotImplementedError."""
        manager = AppIntegrationManager()

        with pytest.raises(NotImplementedError) as exc_info:
            await manager.call_app_tool("app::splunk::search_run", {})

        error_msg = str(exc_info.value)
        assert "not yet implemented" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_not_implemented_message_clear(self):
        """Test that error message explains stub status."""
        manager = AppIntegrationManager()

        with pytest.raises(NotImplementedError) as exc_info:
            await manager.call_app_tool("app::virustotal::lookup_ip", {})

        error_msg = str(exc_info.value)
        assert "stub" in error_msg.lower() or "not yet implemented" in error_msg.lower()

    def test_create_with_integrations_config(self):
        """Test creating manager with integrations configuration."""
        config = {
            "splunk": {"base_url": "https://splunk.example.com", "api_key": "test"},
            "virustotal": {"api_key": "vt_test_key"},
        }

        manager = AppIntegrationManager(integrations=config)

        assert manager.integrations == config
        assert "splunk" in manager.integrations
        assert "virustotal" in manager.integrations
