Configuration
=============

This guide covers all configuration options for the Ableton Live MCP Server.

Environment Variables
---------------------

OSC Configuration
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``ABLETON_OSC_HOST``
     - ``127.0.0.1``
     - Hostname or IP address for OSC communication
   * - ``ABLETON_OSC_SEND_PORT``
     - ``11000``
     - Port for sending OSC messages to Ableton
   * - ``ABLETON_OSC_RECEIVE_PORT``
     - ``11001``
     - Port for receiving OSC messages from Ableton

Logging Configuration
^^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Default
     - Description
   * - ``ABLETON_MCP_LOG_LEVEL``
     - ``INFO``
     - Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
   * - ``ABLETON_MCP_LOG_FILE``
     - ``ableton_mcp.log``
     - Path to the log file
   * - ``ABLETON_MCP_LOG_TO_CONSOLE``
     - ``false``
     - Also output logs to console (true/false)

Example Configuration
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Set environment variables
   export ABLETON_OSC_HOST=127.0.0.1
   export ABLETON_OSC_SEND_PORT=11000
   export ABLETON_OSC_RECEIVE_PORT=11001
   export ABLETON_MCP_LOG_LEVEL=DEBUG
   export ABLETON_MCP_LOG_TO_CONSOLE=true

   # Start the server
   ableton-mcp

Programmatic Configuration
--------------------------

You can also configure the server programmatically:

.. code-block:: python

   from ableton_mcp.container import Container

   # Create container with custom configuration
   container = Container()

   # Configure from environment
   container.config.osc.host.from_env("ABLETON_OSC_HOST", default="127.0.0.1")
   container.config.osc.send_port.from_env("ABLETON_OSC_SEND_PORT", default=11000)
   container.config.osc.receive_port.from_env("ABLETON_OSC_RECEIVE_PORT", default=11001)

   # Or set directly
   container.config.osc.host.from_value("192.168.1.100")
   container.config.osc.send_port.from_value(12000)

Logging
-------

The server uses structured JSON logging with automatic file rotation.

Log File Location
^^^^^^^^^^^^^^^^^

By default, logs are written to ``ableton_mcp.log`` in the current directory.
Log rotation is configured with:

- Maximum file size: 10MB
- Backup count: 5 files

Log Format
^^^^^^^^^^

Logs are in JSON format for easy parsing:

.. code-block:: json

   {
     "event": "Connected to Ableton Live",
     "host": "127.0.0.1",
     "port": 11000,
     "logger": "gateway",
     "level": "info",
     "timestamp": "2026-01-15T10:30:00.123Z"
   }

Viewing Logs
^^^^^^^^^^^^

.. code-block:: bash

   # Follow logs in real-time
   tail -f ableton_mcp.log

   # Parse JSON logs with jq
   cat ableton_mcp.log | jq '.event'

Network Configuration
---------------------

Firewall Settings
^^^^^^^^^^^^^^^^^

Ensure the following UDP ports are accessible:

- **11000** (or configured send port) - Outgoing to Ableton
- **11001** (or configured receive port) - Incoming from Ableton

Remote Connections
^^^^^^^^^^^^^^^^^^

To connect to Ableton on a different machine:

1. Configure ``ABLETON_OSC_HOST`` to the target machine's IP
2. Ensure firewall allows UDP traffic on configured ports
3. AbletonOSC must be configured to accept remote connections

Docker Configuration
--------------------

When running in Docker, use the provided compose file:

.. code-block:: bash

   # Start development environment
   docker-compose -f docker-compose.dev.yml up dev

   # Run tests
   docker-compose -f docker-compose.dev.yml up test

   # Run linting
   docker-compose -f docker-compose.dev.yml up lint

The Docker configuration uses ``host.docker.internal`` to connect to
Ableton Live running on the host machine.
