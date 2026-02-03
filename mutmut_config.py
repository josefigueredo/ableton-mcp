"""Mutmut configuration for mutation testing.

Mutation testing helps verify test quality by introducing small
changes (mutations) to the code and checking if tests catch them.

Usage:
    # Run mutation testing
    mutmut run

    # View results
    mutmut results

    # Show specific mutant
    mutmut show <id>

    # Generate HTML report
    mutmut html
"""


def pre_mutation(context):
    """
    Called before each mutation.

    Skip mutations in files that are:
    - Test files themselves
    - Configuration files
    - __init__.py files
    - Type stubs
    """
    # Skip test files
    if "test_" in context.filename:
        context.skip = True
        return

    # Skip __init__ files (usually just imports)
    if context.filename.endswith("__init__.py"):
        context.skip = True
        return

    # Skip conftest files
    if "conftest" in context.filename:
        context.skip = True
        return


def pre_mutation_ast(context):
    """
    Called before mutating the AST.

    Can be used to skip specific mutations based on code patterns.
    """
    # Skip mutations in logging statements
    if "logger" in context.current_source_line.lower():
        context.skip = True
        return

    # Skip mutations in __repr__ methods
    if "__repr__" in context.current_source_line:
        context.skip = True
        return

    # Skip mutations in type hints only lines
    if context.current_source_line.strip().startswith("->"):
        context.skip = True
        return
