Troubleshooting Guide
=====================

This guide helps resolve common issues with the Ableton Live MCP Server.

Connection Issues
-----------------

Connection Refused
^^^^^^^^^^^^^^^^^^

**Error**: ``[CONNECTION_FAILED] Failed to connect to Ableton Live``

**Causes**:

1. Ableton Live is not running
2. AbletonOSC remote script is not enabled
3. Ports are blocked or in use

**Solutions**:

1. Start Ableton Live and open a project
2. Enable AbletonOSC in Preferences > Link/Tempo/MIDI
3. Check port availability:

   .. code-block:: bash

      # Windows
      netstat -ano | findstr "11000"

      # macOS/Linux
      lsof -i :11000

4. Try different ports if defaults are occupied

OSC Timeout
^^^^^^^^^^^

**Error**: ``[OSC_COMMUNICATION_ERROR] OSC message timeout``

**Causes**:

1. Ableton Live is busy or unresponsive
2. Network issues
3. AbletonOSC script crashed

**Solutions**:

1. Wait for Ableton to finish processing
2. Restart Ableton Live
3. Reload the AbletonOSC script (disable and re-enable)
4. Check firewall settings

Track/Clip Errors
-----------------

Track Not Found
^^^^^^^^^^^^^^^

**Error**: ``[TRACK_NOT_FOUND] Invalid track ID``

**Causes**:

1. Track index out of range
2. Track was deleted

**Solutions**:

1. Use ``get_song_info`` to list available tracks
2. Verify track indices (0-based)
3. Refresh track list after modifications

Clip Not Found
^^^^^^^^^^^^^^

**Error**: ``[CLIP_NOT_FOUND] Invalid clip reference``

**Causes**:

1. Clip slot is empty
2. Wrong clip index

**Solutions**:

1. Create a clip in the target slot first
2. Verify clip indices (0-based)
3. Use track info to check available clips

Cannot Add Notes
^^^^^^^^^^^^^^^^

**Error**: Notes not appearing in clip

**Causes**:

1. Clip slot is empty (no clip created)
2. Clip is playing and locked
3. Note parameters out of range

**Solutions**:

1. Create an empty MIDI clip first:

   .. code-block:: python

      # In Ableton: Right-click clip slot > Insert MIDI Clip

2. Stop playback before adding notes
3. Verify note parameters:

   - pitch: 0-127
   - velocity: 1-127
   - start: >= 0.0
   - duration: > 0.0

Installation Issues
-------------------

Import Errors
^^^^^^^^^^^^^

**Error**: ``ModuleNotFoundError: No module named 'ableton_mcp'``

**Solutions**:

1. Install in development mode:

   .. code-block:: bash

      pip install -e .

2. Verify virtual environment is activated:

   .. code-block:: bash

      # Check Python path
      which python  # macOS/Linux
      where python  # Windows

3. Reinstall dependencies:

   .. code-block:: bash

      pip install -e ".[dev]"

Dependency Conflicts
^^^^^^^^^^^^^^^^^^^^

**Error**: Version conflicts during installation

**Solutions**:

1. Create a fresh virtual environment:

   .. code-block:: bash

      python -m venv venv --clear
      source venv/bin/activate  # or venv\Scripts\activate on Windows
      pip install -e .

2. Update pip:

   .. code-block:: bash

      pip install --upgrade pip

AbletonOSC Issues
-----------------

Script Not Loading
^^^^^^^^^^^^^^^^^^

**Symptoms**: AbletonOSC doesn't appear in Control Surface list

**Solutions**:

1. Verify installation location:

   - Windows: ``C:\ProgramData\Ableton\Live x.x\Resources\MIDI Remote Scripts\AbletonOSC\``
   - macOS: ``/Applications/Ableton Live x.x/Contents/App-Resources/MIDI Remote Scripts/AbletonOSC/``

2. Check folder contains ``__init__.py``

3. Restart Ableton Live completely (not just reload)

4. Check Ableton's Log.txt for errors:

   - Windows: ``C:\Users\<user>\AppData\Roaming\Ableton\Live x.x\Preferences\Log.txt``
   - macOS: ``~/Library/Preferences/Ableton/Live x.x/Log.txt``

Script Crashes
^^^^^^^^^^^^^^

**Symptoms**: Connection works initially, then stops

**Solutions**:

1. Check Log.txt for Python errors
2. Ensure you're using a compatible AbletonOSC version
3. Report issues to `AbletonOSC repository <https://github.com/ideoforms/AbletonOSC>`_

Performance Issues
------------------

Slow Response
^^^^^^^^^^^^^

**Symptoms**: Commands take a long time to execute

**Solutions**:

1. Reduce logging verbosity:

   .. code-block:: bash

      export ABLETON_MCP_LOG_LEVEL=WARNING

2. Close unnecessary Ableton windows/views

3. Reduce track count if possible

4. Check CPU usage in Ableton

High Memory Usage
^^^^^^^^^^^^^^^^^

**Solutions**:

1. Clear in-memory caches periodically
2. Disconnect and reconnect to reset state
3. Restart the MCP server

Debugging
---------

Enable Debug Logging
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   export ABLETON_MCP_LOG_LEVEL=DEBUG
   export ABLETON_MCP_LOG_TO_CONSOLE=true
   ableton-mcp

View OSC Messages
^^^^^^^^^^^^^^^^^

Enable verbose logging to see OSC traffic:

.. code-block:: python

   import logging
   logging.getLogger("ableton_mcp.infrastructure.osc_client").setLevel(logging.DEBUG)

Test Connection
^^^^^^^^^^^^^^^

.. code-block:: python

   import asyncio
   from ableton_mcp.container import Container

   async def test():
       container = Container()
       gateway = container.ableton_gateway()

       try:
           await gateway.connect()
           print("Connection successful!")

           song = await gateway.get_song_info()
           print(f"Tempo: {song.tempo}")

       except Exception as e:
           print(f"Connection failed: {e}")

       finally:
           await gateway.disconnect()

   asyncio.run(test())

Getting Help
------------

If you're still experiencing issues:

1. **Check Documentation**: Review the `docs/ <../index.html>`_ directory
2. **Search Issues**: Look for similar problems on `GitHub Issues <https://github.com/josefigueredo/ableton-mcp/issues>`_
3. **Ask Questions**: Use `GitHub Discussions <https://github.com/josefigueredo/ableton-mcp/discussions>`_
4. **Report Bugs**: Create a new issue with:

   - Python version
   - Ableton Live version
   - Operating system
   - Full error message/stack trace
   - Steps to reproduce
