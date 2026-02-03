API Reference
=============

This section provides detailed API documentation for all modules in the
Ableton Live MCP Server.

Architecture Overview
---------------------

The project follows Clean Architecture with the following layers:

.. code-block:: text

   ┌─────────────────────────────────────────┐
   │              Interfaces                 │  MCP Protocol
   │         (MCP Server, CLI)               │
   ├─────────────────────────────────────────┤
   │               Adapters                  │  Service Integration
   │       (OSC, Service Adapters)           │
   ├─────────────────────────────────────────┤
   │              Application                │  Use Cases
   │           (Business Logic)              │
   ├─────────────────────────────────────────┤
   │               Domain                    │  Core Business
   │     (Entities, Services, Repos)         │
   ├─────────────────────────────────────────┤
   │            Infrastructure               │  External Concerns
   │    (OSC Client, Repositories)           │
   └─────────────────────────────────────────┘

Module Index
------------

.. toctree::
   :maxdepth: 2

   interfaces
   application
   domain
   infrastructure

Quick Reference
---------------

Main Entry Points
^^^^^^^^^^^^^^^^^

- :mod:`ableton_mcp.interfaces.mcp_server` - MCP protocol handler
- :mod:`ableton_mcp.container` - Dependency injection container
- :mod:`ableton_mcp.main` - Application entry point

Key Classes
^^^^^^^^^^^

**Domain Entities**

- :class:`~ableton_mcp.domain.entities.Song` - Song metadata
- :class:`~ableton_mcp.domain.entities.Track` - Track information
- :class:`~ableton_mcp.domain.entities.Clip` - Clip data
- :class:`~ableton_mcp.domain.entities.Note` - MIDI note

**Use Cases**

- :class:`~ableton_mcp.application.use_cases.ConnectToAbletonUseCase`
- :class:`~ableton_mcp.application.use_cases.TransportControlUseCase`
- :class:`~ableton_mcp.application.use_cases.AddNotesUseCase`
- :class:`~ableton_mcp.application.use_cases.AnalyzeHarmonyUseCase`

**Services**

- :class:`~ableton_mcp.infrastructure.services.MusicTheoryService`
- :class:`~ableton_mcp.infrastructure.services.TempoAnalysisService`
