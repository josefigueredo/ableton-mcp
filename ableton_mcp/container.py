"""Dependency injection container using dependency-injector."""

from dependency_injector import containers, providers

from ableton_mcp.adapters.service_adapters import (
    AbletonClipService,
    AbletonConnectionService,
    AbletonTrackService,
    AbletonTransportService,
)
from ableton_mcp.application.use_cases import (
    AddNotesUseCase,
    AnalyzeHarmonyUseCase,
    AnalyzeTempoUseCase,
    ArrangementSuggestionsUseCase,
    ConnectToAbletonUseCase,
    GetClipContentUseCase,
    GetSongInfoUseCase,
    MixAnalysisUseCase,
    TrackOperationsUseCase,
    TransportControlUseCase,
)
from ableton_mcp.infrastructure.osc import AbletonOSCGateway
from ableton_mcp.infrastructure.repositories import (
    InMemoryAnalysisRepository,
    InMemoryClipRepository,
    InMemoryDeviceRepository,
    InMemorySongRepository,
    InMemoryTrackRepository,
)
from ableton_mcp.infrastructure.services import (
    ArrangementServiceImpl,
    MixingServiceImpl,
    MusicTheoryServiceImpl,
    TempoAnalysisServiceImpl,
)
from ableton_mcp.interfaces.mcp_server import AbletonMCPServer


class Container(containers.DeclarativeContainer):
    """Dependency injection container for the Ableton MCP application."""

    # Configuration
    config = providers.Configuration()

    # Infrastructure - Ableton Gateway
    ableton_gateway = providers.Singleton(AbletonOSCGateway)

    # Infrastructure - Repositories
    song_repository = providers.Singleton(InMemorySongRepository)
    track_repository = providers.Singleton(InMemoryTrackRepository)
    device_repository = providers.Singleton(InMemoryDeviceRepository)
    clip_repository = providers.Singleton(InMemoryClipRepository)
    analysis_repository = providers.Singleton(InMemoryAnalysisRepository)

    # Infrastructure - Domain Services
    music_theory_service = providers.Singleton(MusicTheoryServiceImpl)
    tempo_analysis_service = providers.Singleton(TempoAnalysisServiceImpl)
    arrangement_service = providers.Singleton(ArrangementServiceImpl)
    mixing_service = providers.Singleton(MixingServiceImpl)

    # Adapters - Service Adapters
    connection_service = providers.Factory(AbletonConnectionService, gateway=ableton_gateway)

    transport_service = providers.Factory(AbletonTransportService, gateway=ableton_gateway)

    track_service = providers.Factory(AbletonTrackService, gateway=ableton_gateway)

    clip_service = providers.Factory(AbletonClipService, gateway=ableton_gateway)

    # Application - Use Cases
    connect_use_case = providers.Factory(
        ConnectToAbletonUseCase,
        connection_service=connection_service,
        song_repository=song_repository,
        ableton_gateway=ableton_gateway,
    )

    transport_use_case = providers.Factory(
        TransportControlUseCase,
        transport_service=transport_service,
        song_repository=song_repository,
    )

    song_info_use_case = providers.Factory(GetSongInfoUseCase, song_repository=song_repository)

    track_ops_use_case = providers.Factory(
        TrackOperationsUseCase,
        track_repository=track_repository,
        song_repository=song_repository,
        track_service=track_service,
    )

    add_notes_use_case = providers.Factory(
        AddNotesUseCase,
        clip_repository=clip_repository,
        song_repository=song_repository,
        music_theory_service=music_theory_service,
        clip_service=clip_service,
    )

    harmony_analysis_use_case = providers.Factory(
        AnalyzeHarmonyUseCase, music_theory_service=music_theory_service
    )

    tempo_analysis_use_case = providers.Factory(
        AnalyzeTempoUseCase, tempo_service=tempo_analysis_service, song_repository=song_repository
    )

    mix_analysis_use_case = providers.Factory(
        MixAnalysisUseCase, mixing_service=mixing_service, song_repository=song_repository
    )

    arrangement_suggestions_use_case = providers.Factory(
        ArrangementSuggestionsUseCase,
        arrangement_service=arrangement_service,
        song_repository=song_repository,
    )

    clip_content_use_case = providers.Factory(
        GetClipContentUseCase, clip_service=clip_service, song_repository=song_repository
    )

    # Interface - MCP Server
    mcp_server = providers.Factory(
        AbletonMCPServer,
        connect_use_case=connect_use_case,
        transport_use_case=transport_use_case,
        song_info_use_case=song_info_use_case,
        track_ops_use_case=track_ops_use_case,
        add_notes_use_case=add_notes_use_case,
        harmony_analysis_use_case=harmony_analysis_use_case,
        tempo_analysis_use_case=tempo_analysis_use_case,
        mix_analysis_use_case=mix_analysis_use_case,
        arrangement_suggestions_use_case=arrangement_suggestions_use_case,
        clip_content_use_case=clip_content_use_case,
    )
