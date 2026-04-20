"""
Unit tests for ArchetypeRouter stub.

These tests verify the stub implementation of ArchetypeRouter
works as expected for the namespace system foundation.
"""

import pytest

from cy_language.archetype_router import ArchetypeRouter


class TestArchetypeRouterStub:
    """Test stub implementation of ArchetypeRouter."""

    def test_create_archetype_router(self):
        """Test that ArchetypeRouter can be instantiated."""
        router = ArchetypeRouter()

        assert router is not None
        assert hasattr(router, "archetype_mappings")
        assert hasattr(router, "_initialized")

    def test_register_archetype(self):
        """Test that register_archetype() can be called without errors."""
        router = ArchetypeRouter()

        integrations = [
            ("app::virustotal", 10),
            ("app::alienvault", 8),
        ]

        router.register_archetype("threatintel", integrations)

        assert "threatintel" in router.archetype_mappings
        assert len(router.archetype_mappings["threatintel"]) == 2

    def test_register_archetype_sorts_by_priority(self):
        """Test that archetype integrations are sorted by priority."""
        router = ArchetypeRouter()

        integrations = [
            ("app::service1", 5),
            ("app::service2", 10),
            ("app::service3", 8),
        ]

        router.register_archetype("test", integrations)

        # Should be sorted highest priority first
        sorted_integrations = router.archetype_mappings["test"]
        assert sorted_integrations[0] == ("app::service2", 10)
        assert sorted_integrations[1] == ("app::service3", 8)
        assert sorted_integrations[2] == ("app::service1", 5)

    @pytest.mark.asyncio
    async def test_initialize_router(self):
        """Test that initialize() can be called without errors."""
        router = ArchetypeRouter()

        await router.initialize()

        assert router._initialized is True

    def test_get_all_archetypes_empty(self):
        """Test that get_all_archetypes() returns empty list."""
        router = ArchetypeRouter()

        archetypes = router.get_all_archetypes()

        assert isinstance(archetypes, list)
        assert len(archetypes) == 0

    @pytest.mark.asyncio
    async def test_call_archetype_not_implemented(self):
        """Test that call_archetype() raises NotImplementedError."""
        router = ArchetypeRouter()

        with pytest.raises(NotImplementedError) as exc_info:
            await router.call_archetype("arc::threatintel::lookup_ip", {})

        error_msg = str(exc_info.value)
        assert "not yet implemented" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_not_implemented_message_clear(self):
        """Test that error message explains stub status."""
        router = ArchetypeRouter()

        with pytest.raises(NotImplementedError) as exc_info:
            await router.call_archetype("arc::siem::query_logs", {})

        error_msg = str(exc_info.value)
        assert "stub" in error_msg.lower() or "not yet implemented" in error_msg.lower()

    def test_multiple_archetype_registration(self):
        """Test registering multiple archetypes."""
        router = ArchetypeRouter()

        router.register_archetype("threatintel", [("app::vt", 10)])
        router.register_archetype("siem", [("app::splunk", 9)])

        assert len(router.archetype_mappings) == 2
        assert "threatintel" in router.archetype_mappings
        assert "siem" in router.archetype_mappings
