"""Public API for type analysis (inference + validation) in Cy language.

This module provides the main entry point for external systems (like Backend-Y)
to perform type analysis on Cy scripts.

"""

from typing import Any, Union, cast

from genson import SchemaBuilder

from cy_language.compiler import compile_cy_program
from cy_language.parser import Parser
from cy_language.tool_resolver import ToolResolver
from cy_language.tool_signature import ParameterSignature, ToolSignature
from cy_language.type_inference_engine import TypeInferenceEngine


def _validate_json_schema(schema: dict[str, Any]) -> None:
    """Validate that a schema is a valid JSON Schema.

    Performs basic validation of JSON Schema format.

    Args:
        schema: JSON Schema dict to validate

    Raises:
        ValueError: If schema is invalid
    """
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a dictionary")

    # Check if type field exists and is valid
    if "type" in schema:
        valid_types = {
            "string",
            "number",
            "integer",
            "object",
            "array",
            "boolean",
            "null",
        }
        schema_type = schema["type"]
        if schema_type not in valid_types:
            raise ValueError(
                f"Invalid schema type '{schema_type}'. "
                f"Must be one of: {', '.join(sorted(valid_types))}"
            )


def infer_output_schema(
    code: str,
    input_schema: dict[str, Any] | None = None,
    tool_registry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Infer the output schema of a Cy script.

    This is the main public API for type inference. Given Cy source code,
    optional input schema, and optional tool definitions, returns a JSON Schema
    representing the script's output type.

    Args:
        code: Cy language source code to analyze
        input_schema: Optional JSON Schema for the $input variable.
                     If provided, the script can reference $input with this type.
        tool_registry: Optional dictionary of tool definitions with type signatures.
                      Format: {
                          "tool_name": {
                              "parameters": {...},
                              "return_type": {...}
                          }
                      }

    Returns:
        JSON Schema dict representing the script's output type.
        Output is determined by (in priority order):
        1. Union of all return statement types (if any)
        2. {} (Any type) if no explicit output ($output no longer supported)

    Raises:
        SyntaxError: If the Cy code cannot be parsed
        ValueError: If type inference fails or schemas are invalid

    Examples:
        >>> code = 'x = 5\\noutput = x + 10'
        >>> infer_output_schema(code)
        {'type': 'number'}

        >>> code = 'name = $input.name\\noutput = "Hello " + name'
        >>> input_schema = {
        ...     'type': 'object',
        ...     'properties': {'name': {'type': 'string'}}
        ... }
        >>> infer_output_schema(code, input_schema)
        {'type': 'string'}
    """
    # Handle empty or whitespace-only code
    if not code or code.strip() == "":
        return {}

    # Validate input_schema if provided
    if input_schema is not None:
        _validate_json_schema(input_schema)

    # Step 1: Parse Cy code
    try:
        parser = Parser()
        ast = parser.parse_only(code)
    except Exception as e:
        # Re-raise parsing errors as SyntaxError
        raise SyntaxError(f"Failed to parse Cy code: {e}") from e

    # Step 2: Create tool resolver with native tools and custom tools
    # (Must be done BEFORE compilation for tool resolution)
    tool_resolver = ToolResolver.from_native_tools()

    # Register custom tools if provided
    if tool_registry:
        try:
            custom_tools = _parse_tool_registry(tool_registry)
            for tool_sig in custom_tools:
                tool_resolver.register_tool_with_types(tool_sig)
        except Exception as e:
            raise ValueError(f"Invalid tool registry: {e}") from e

    # Step 3: Compile to execution plan with tool resolver
    # If compilation fails due to unknown tools, register them as placeholders
    # Disable output validation for type inference (analyzing partial scripts)
    try:
        execution_plan = compile_cy_program(
            ast, source_file="<api>", tool_resolver=tool_resolver, validate_output=False
        )
    except Exception as e:
        # Check if it's a tool resolution error for an unknown tool
        from cy_language.errors import ToolResolutionError

        # The error might be the ToolResolutionError itself or wrapped
        if isinstance(e, ToolResolutionError) or isinstance(
            e.__cause__, ToolResolutionError
        ):
            # Get the actual ToolResolutionError
            tool_error = e if isinstance(e, ToolResolutionError) else e.__cause__
            # Register the unknown tool as a placeholder (no types = returns Any)
            assert isinstance(
                tool_error, ToolResolutionError
            )  # Type assertion for mypy
            unknown_tool = tool_error.tool_name
            tool_resolver.register_tool(unknown_tool, None)
            # Also register short name if needed
            if "::" not in unknown_tool:
                tool_resolver.register_short_name(unknown_tool, unknown_tool)
            # Retry compilation
            try:
                execution_plan = compile_cy_program(
                    ast,
                    source_file="<api>",
                    tool_resolver=tool_resolver,
                    validate_output=False,
                )
            except Exception as retry_e:
                raise ValueError(f"Failed to compile Cy code: {retry_e}") from retry_e
        else:
            raise ValueError(f"Failed to compile Cy code: {e}") from e

    # Step 4: Run type inference
    try:
        engine = TypeInferenceEngine(
            execution_plan, tool_resolver, input_schema=input_schema
        )
        type_env = engine.infer_types()
    except Exception as e:
        raise ValueError(f"Type inference failed: {e}") from e

    # Step 5: Extract output schema
    return _extract_output_schema(type_env, engine)


def analyze_types(
    code: str,
    input_schema: dict[str, Any] | None = None,
    tool_registry: dict[str, Any] | None = None,
    strict_input: bool = False,
    custom_tools: dict[str, Any] | None = None,
    stub_unknown: bool = False,
) -> dict[str, Any]:
    """Analyze types in Cy code with single-pass inference and validation.

    This is the main public API for type analysis. Given Cy source code,
    optional input schema, and optional tool definitions, performs both type inference
    and type checking in a single pass. Raises TypeError on validation failures.

    Args:
        code: Cy language source code to analyze
        input_schema: Optional JSON Schema for the input variable.
                     If provided, the script can reference input with this type.
        tool_registry: Optional dictionary of tool definitions with type signatures.
                      Format: {
                          "tool_name": {
                              "parameters": {...},
                              "return_type": {...}
                          }
                      }
        strict_input: If True, validate that all input field accesses exist in input_schema.
                     This is useful for workflow composition to catch field mismatches
                     at validation time. Requires input_schema to be provided.
        custom_tools: Optional dictionary of Python callables to register as tools.
                     Format: {"name": callable} — same as Cy(tools=...).
        stub_unknown: If True, unknown tools are accepted (treated as returning Any).

    Returns:
        JSON Schema dict representing the script's output type.
        Output is determined by (in priority order):
        1. Union of all return statement types (if any)
        2. {} (Any type) if no explicit output

    Raises:
        SyntaxError: If the Cy code cannot be parsed
        TypeError: If type validation fails (with detailed error messages including
                  line numbers and type information)
        ValueError: If schemas are invalid, strict_input is True without input_schema,
                   or type inference fails

    Examples:
        >>> code = 'x = 5\\ny = 3\\nresult = x + y\\nreturn result'
        >>> analyze_types(code)
        {'type': 'number'}

        >>> code = 'result = 5 + "text"\\nreturn result'
        >>> analyze_types(code)  # Raises TypeError
        TypeError: ...

        >>> code = 'name = input.name\\nreturn "Hello " + name'
        >>> input_schema = {
        ...     'type': 'object',
        ...     'properties': {'name': {'type': 'string'}}
        ... }
        >>> analyze_types(code, input_schema)
        {'type': 'string'}

        >>> # Strict input validation for workflow composition
        >>> code = 'summary = input["detailed_analysis"]\\nreturn summary'
        >>> schema = {'type': 'object', 'properties': {'ip_address': {'type': 'string'}}}
        >>> analyze_types(code, schema, strict_input=True)  # Raises TypeError
        TypeError: Line 1: field 'detailed_analysis' not found in input schema. Available fields: ip_address
    """
    # Handle empty or whitespace-only code
    if not code or code.strip() == "":
        return {}

    # Validate input_schema if provided
    if input_schema is not None:
        _validate_json_schema(input_schema)

    # Step 1: Parse Cy code
    try:
        parser = Parser()
        ast = parser.parse_only(code)
    except Exception as e:
        # Re-raise parsing errors as SyntaxError
        raise SyntaxError(f"Failed to parse Cy code: {e}") from e

    # Step 2: Create tool resolver with native tools and custom tools
    if custom_tools or stub_unknown:
        # Use build_tool_resolver for custom tools and/or stub mode
        from cy_language.tool_resolver import build_tool_resolver

        tool_resolver = build_tool_resolver(
            custom_tools=custom_tools,
            stub_unknown=stub_unknown,
        )
    else:
        tool_resolver = ToolResolver.from_native_tools()

    # Register typed tool definitions if provided (legacy format)
    if tool_registry:
        try:
            parsed_tools = _parse_tool_registry(tool_registry)
            for tool_sig in parsed_tools:
                tool_resolver.register_tool_with_types(tool_sig)
        except Exception as e:
            raise ValueError(f"Invalid tool registry: {e}") from e

    # Step 3: Compile to execution plan with tool resolver
    # Disable output validation for type inference (analyzing partial scripts)
    try:
        execution_plan = compile_cy_program(
            ast, source_file="<api>", tool_resolver=tool_resolver, validate_output=False
        )
    except Exception as e:
        # Check if it's a tool resolution error for an unknown tool
        from cy_language.errors import ToolResolutionError

        # The error might be the ToolResolutionError itself or wrapped
        if isinstance(e, ToolResolutionError) or isinstance(
            e.__cause__, ToolResolutionError
        ):
            # Get the actual ToolResolutionError
            tool_error = e if isinstance(e, ToolResolutionError) else e.__cause__
            # Register the unknown tool as a placeholder (no types = returns Any)
            assert isinstance(tool_error, ToolResolutionError)
            unknown_tool = tool_error.tool_name
            tool_resolver.register_tool(unknown_tool, None)
            # Also register short name if needed
            if "::" not in unknown_tool:
                tool_resolver.register_short_name(unknown_tool, unknown_tool)
            # Retry compilation
            try:
                execution_plan = compile_cy_program(
                    ast,
                    source_file="<api>",
                    tool_resolver=tool_resolver,
                    validate_output=False,
                )
            except Exception as retry_e:
                raise ValueError(f"Failed to compile Cy code: {retry_e}") from retry_e
        else:
            raise ValueError(f"Failed to compile Cy code: {e}") from e

    # Step 4: Run type inference WITH validation (check_types=True)
    try:
        engine = TypeInferenceEngine(
            execution_plan,
            tool_resolver,
            input_schema=input_schema,
            check_types=True,
            strict_input=strict_input,
        )
        type_env = engine.infer_types()
    except ValueError:
        # Re-raise ValueError for strict_input configuration errors
        raise
    except TypeError:
        # Re-raise TypeError as-is (validation failures)
        raise
    except Exception as e:
        raise ValueError(f"Type analysis failed: {e}") from e

    # Step 5: Extract output schema
    return _extract_output_schema(type_env, engine)


def _extract_output_schema(
    type_env: Any,  # TypeEnvironment
    engine: Any,  # TypeInferenceEngine
) -> dict[str, Any]:
    """Extract output schema from type environment and engine.

    Only return statements produce output.

    Priority:
    1. Check for aggregated return types
    2. Return {} (Any) if no output found

    Args:
        type_env: TypeEnvironment with inferred variable types
        engine: TypeInferenceEngine with return type tracking

    Returns:
        JSON Schema for the script's output
    """
    # Priority 1: Check for aggregated return types
    return_type = engine.get_aggregated_return_type()
    if return_type:
        return cast(dict[str, Any], return_type)

    # Priority 2: No explicit output
    return {}


def _parse_tool_registry(
    tool_registry: Union[dict[str, Any], Any],
) -> list[ToolSignature]:
    """Parse tool registry dict or ToolRegistry object into ToolSignature objects.

    Args:
        tool_registry: Either:
                      - Dict mapping tool names to type signatures (legacy format)
                      - ToolRegistry object

    Returns:
        List of ToolSignature objects

    Raises:
        ValueError: If tool registry format is invalid
    """
    from cy_language.tool_signature import ToolRegistry

    signatures = []

    # If it's a ToolRegistry object, extract signatures directly
    if isinstance(tool_registry, ToolRegistry):
        return list(tool_registry.tools.values())

    # Legacy: Dict format
    for tool_name, tool_spec in tool_registry.items():
        # Validate tool spec is a dict
        if not isinstance(tool_spec, dict):
            raise ValueError(
                f"Invalid tool registry format for '{tool_name}': "
                f"expected dict, got {type(tool_spec).__name__}"
            )

        # Extract parameters and return_type
        params_spec = tool_spec.get("parameters", {})
        return_type = tool_spec.get("return_type", {})

        # Convert parameters dict to ParameterSignature objects
        parameters = {}
        for param_name, param_type in params_spec.items():
            parameters[param_name] = ParameterSignature(
                name=param_name,
                type_schema=param_type,
                required=True,  # Default to required
                default_value=None,
                description="",
            )

        # Create ToolSignature
        # Handle FQN generation based on tool_name format:
        # - If no "::" : Simple name → custom::tools::name
        # - If 2 parts (namespace::name) : Add "tools" → namespace::tools::name
        # - If 3+ parts : Use as-is (full FQN)
        parts = tool_name.split("::")
        if len(parts) == 1:
            fqn = f"custom::tools::{tool_name}"  # Simple name
        elif len(parts) == 2:
            namespace, name = parts
            fqn = f"{namespace}::tools::{name}"  # Add "tools" category
        else:
            fqn = tool_name  # Full FQN with 3+ parts

        signature = ToolSignature(
            fqn=fqn,
            function=None,  # No actual Python function for custom tools
            parameters=parameters,
            return_type=return_type,
            description=tool_spec.get("description", ""),
        )

        signatures.append(signature)

    return signatures


def data_to_schema(data: Any) -> dict[str, Any]:
    """Convert sample data to JSON Schema using GenSON.

    Utility function to convert Python data into a JSON Schema.
    Useful for generating input schemas from sample data.

    Args:
        data: Any Python data (dict, list, str, int, etc.)

    Returns:
        JSON Schema representing the data's type

    Examples:
        >>> data_to_schema({"name": "Alice", "age": 30})
        {
            'type': 'object',
            'properties': {
                'name': {'type': 'string'},
                'age': {'type': 'integer'}
            }
        }

        >>> data_to_schema([1, 2, 3])
        {'type': 'array', 'items': {'type': 'integer'}}
    """
    builder = SchemaBuilder()
    builder.add_object(data)
    return cast(dict[str, Any], builder.to_schema())


def validate_schema_matches_data(schema: dict[str, Any], data: Any) -> bool:
    """Validate that a schema matches sample data using GenSON.

    Utility function for testing. Generates a schema from data and checks
    if it's compatible with the provided schema.

    Args:
        schema: JSON Schema to validate
        data: Sample data to check against schema

    Returns:
        True if schema is compatible with data, False otherwise

    Examples:
        >>> schema = {'type': 'number'}
        >>> validate_schema_matches_data(schema, 42)
        True

        >>> validate_schema_matches_data(schema, "text")
        False
    """
    # Generate schema from data
    builder = SchemaBuilder()
    builder.add_object(data)
    data_schema = builder.to_schema()

    # Basic compatibility check: types should match
    # Note: GenSON uses "integer" but Cy uses "number" for numeric types
    schema_type = schema.get("type")
    data_type = data_schema.get("type")

    # Treat integer and number as compatible
    if schema_type == "number" and data_type == "integer":
        return True
    if schema_type == "integer" and data_type == "number":
        return True

    return cast(bool, schema_type == data_type)
