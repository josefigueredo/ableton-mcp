"""Unit tests for dependency injection container."""

import pytest

from ableton_mcp.container import Container


class TestContainer:
    """Tests for DI container configuration."""

    def test_container_instantiation(self) -> None:
        """Test that container can be instantiated."""
        container = Container()
        assert container is not None

    def test_gateway_provider(self) -> None:
        """Test gateway provider is configured."""
        container = Container()
        # Gateway should be a singleton provider
        assert container.ableton_gateway is not None

    def test_repository_providers(self) -> None:
        """Test repository providers are configured."""
        container = Container()
        assert container.song_repository is not None
        assert container.clip_repository is not None
        assert container.track_repository is not None

    def test_service_providers(self) -> None:
        """Test service providers are configured."""
        container = Container()
        assert container.music_theory_service is not None
        assert container.tempo_analysis_service is not None
        assert container.arrangement_service is not None
        assert container.mixing_service is not None

    def test_adapter_providers(self) -> None:
        """Test adapter providers are configured."""
        container = Container()
        assert container.connection_service is not None
        assert container.transport_service is not None
        assert container.track_service is not None
        assert container.clip_service is not None

    def test_use_case_providers(self) -> None:
        """Test use case providers are configured."""
        container = Container()
        assert container.connect_use_case is not None
        assert container.transport_use_case is not None
        assert container.song_info_use_case is not None
        assert container.track_ops_use_case is not None
        assert container.add_notes_use_case is not None
        assert container.harmony_analysis_use_case is not None
        assert container.tempo_analysis_use_case is not None
        assert container.mix_analysis_use_case is not None
        assert container.arrangement_suggestions_use_case is not None
        assert container.clip_content_use_case is not None

    def test_mcp_server_provider(self) -> None:
        """Test MCP server provider is configured."""
        container = Container()
        assert container.mcp_server is not None

    def test_singleton_behavior(self) -> None:
        """Test that singletons return same instance."""
        container = Container()
        gateway1 = container.ableton_gateway()
        gateway2 = container.ableton_gateway()
        assert gateway1 is gateway2

    def test_factory_behavior(self) -> None:
        """Test that factories create new instances."""
        container = Container()
        # Use cases are factories, should create new instances
        # Note: The actual behavior depends on the provider type
        use_case1 = container.connect_use_case()
        use_case2 = container.connect_use_case()
        # Factory providers create new instances each time
        assert use_case1 is not use_case2
