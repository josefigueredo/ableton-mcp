Installation
============

This guide covers the installation process for the Ableton Live MCP Server.

System Requirements
-------------------

- **Python**: 3.11 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Network**: Local network access for OSC communication
- **Ports**: 11000-11001 available for OSC (configurable)

Prerequisites
-------------

Ableton Live
^^^^^^^^^^^^

You need Ableton Live installed on your system. Any recent version should work.

AbletonOSC Remote Script
^^^^^^^^^^^^^^^^^^^^^^^^

The AbletonOSC remote script enables OSC communication with Ableton Live.

1. Download AbletonOSC from `GitHub <https://github.com/ideoforms/AbletonOSC>`_
2. Copy the ``AbletonOSC`` folder to your Ableton Live MIDI Remote Scripts directory:

   - **Windows**: ``C:\ProgramData\Ableton\Live x.x\Resources\MIDI Remote Scripts\``
   - **macOS**: ``/Applications/Ableton Live x.x/Contents/App-Resources/MIDI Remote Scripts/``

3. Restart Ableton Live
4. Go to **Preferences** > **Link/Tempo/MIDI**
5. Select ``AbletonOSC`` in a Control Surface slot

Installation Methods
--------------------

From Source (Recommended for Development)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Clone the repository
   git clone https://github.com/josefigueredo/ableton-mcp.git
   cd ableton-mcp

   # Create virtual environment
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate

   # Install in development mode
   pip install -e .

   # Install development dependencies (optional)
   pip install -e ".[dev]"

From PyPI
^^^^^^^^^

.. code-block:: bash

   pip install ableton-mcp

Verifying Installation
----------------------

After installation, verify everything is working:

.. code-block:: bash

   # Check the command is available
   ableton-mcp --help

   # Or run directly
   python -m ableton_mcp.main --help

Development Setup
-----------------

For contributors, install with development dependencies:

.. code-block:: bash

   # Install with dev dependencies
   pip install -e ".[dev]"

   # Install pre-commit hooks
   pre-commit install

   # Run tests to verify setup
   pytest

This installs additional tools:

- **pytest** - Testing framework
- **black** - Code formatter
- **ruff** - Linter
- **mypy** - Type checker
- **pre-commit** - Git hooks

Next Steps
----------

Once installed, proceed to :doc:`quickstart` to learn how to use the server.
