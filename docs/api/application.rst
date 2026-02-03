Application Layer
=================

The application layer contains use cases that orchestrate business logic.
Each use case represents a single operation that can be performed.

Use Cases
---------

.. automodule:: ableton_mcp.application.use_cases
   :members:
   :undoc-members:
   :show-inheritance:

Use Case Pattern
----------------

All use cases follow a consistent pattern:

1. **Request DTO** - Input data structure
2. **execute()** method - Performs the operation
3. **UseCaseResult** - Standard response structure

Example
^^^^^^^

.. code-block:: python

   from ableton_mcp.application.use_cases import TransportControlUseCase
   from ableton_mcp.application.use_cases import TransportControlRequest

   # Create request
   request = TransportControlRequest(action="play")

   # Execute use case
   result = await use_case.execute(request)

   # Check result
   if result.success:
       print("Playback started!")
   else:
       print(f"Error: {result.error}")

Request DTOs
------------

TransportControlRequest
^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class TransportControlRequest:
       action: str  # "play", "stop", or "record"

AddNotesRequest
^^^^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class AddNotesRequest:
       track_id: int
       clip_id: int
       notes: list[Note]
       quantize: bool = False
       quantize_value: float = 0.25
       scale_filter: str | None = None
       root_note: int = 60

AnalyzeHarmonyRequest
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   @dataclass
   class AnalyzeHarmonyRequest:
       notes: list[int]
       suggest_progressions: bool = True
       genre: str = "pop"

UseCaseResult
-------------

All use cases return a ``UseCaseResult``:

.. code-block:: python

   @dataclass
   class UseCaseResult:
       success: bool
       data: Any = None
       error: str | None = None
       error_code: str | None = None

Error Handling
--------------

Use cases handle errors gracefully and return structured error information:

.. code-block:: python

   result = await use_case.execute(request)

   if not result.success:
       print(f"Error code: {result.error_code}")
       print(f"Error message: {result.error}")
