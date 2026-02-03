Ableton Live MCP Server
=======================

.. image:: https://github.com/josefigueredo/ableton-mcp/actions/workflows/tests.yml/badge.svg
   :target: https://github.com/josefigueredo/ableton-mcp/actions/workflows/tests.yml
   :alt: Tests

.. image:: https://codecov.io/gh/josefigueredo/ableton-mcp/branch/main/graph/badge.svg
   :target: https://codecov.io/gh/josefigueredo/ableton-mcp
   :alt: Coverage

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

A sophisticated Model Context Protocol (MCP) server that transforms any AI assistant
into an expert Ableton Live collaborator with deep music production knowledge and
real-time DAW control.

Features
--------

- **Real-time OSC Communication** - Bidirectional control via AbletonOSC remote script
- **Complete Transport Control** - Play, stop, record, and transport management
- **Track Operations** - Volume, pan, mute, solo, arm, create, and delete tracks
- **Device & Plugin Control** - Parameter automation and preset management
- **Clip Management** - Fire, stop, create clips with intelligent MIDI note addition
- **Music Theory Engine** - Scale filtering, key detection, chord suggestions

Quick Start
-----------

Installation
^^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/josefigueredo/ableton-mcp.git
   cd ableton-mcp

   # Create and activate virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install the package
   pip install -e .

Running the Server
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Start the MCP server
   ableton-mcp

   # Or run directly
   python -m ableton_mcp.main

Prerequisites
^^^^^^^^^^^^^

1. **Ableton Live** - Any recent version
2. **AbletonOSC** - Remote script for OSC communication (`Installation Guide <https://github.com/ideoforms/AbletonOSC>`_)
3. **Python 3.11+** - With pip package manager

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   api/interfaces
   api/application
   api/domain
   api/infrastructure

.. toctree::
   :maxdepth: 2
   :caption: Guides

   guides/architecture
   guides/music-theory
   guides/troubleshooting

.. toctree::
   :maxdepth: 1
   :caption: Project

   changelog
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
