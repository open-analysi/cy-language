"""Cy language interpreter."""

import sys
import threading
from typing import TYPE_CHECKING, Any, NoReturn, Optional

from cy_language.compiler import compile_cy_program
from cy_language.dependency_analyzer import DependencyAnalyzer
from cy_language.executor import execute_plan, execute_plan_async
from cy_language.parser import Parser

from .errors import CyError, ExecutionPaused
from .errors import RuntimeError as CyRuntimeError
from .execution_plan import ExecutionCheckpoint

if TYPE_CHECKING:
    from .error_context import ErrorContext


class Cy:
    """Cy language interpreter."""

    @staticmethod
    def _process_user_tools(
        tools_dict: dict[str, Any],
        user_tools: dict[str, Any] | None,
    ) -> set:
        """Merge user-provided tools into tools_dict, return hi-latency tool name set.

        Tools can be plain callables or dicts with metadata:
            {"fn": callable, "hi_latency": True}
        """
        hi_latency: set[str] = set()
        if user_tools:
            for name, entry in user_tools.items():
                if isinstance(entry, dict):
                    if "fn" not in entry:
                        raise ValueError(
                            f"Tool '{name}': dict-style registration requires a 'fn' key. "
                            f'Expected format: {{"fn": callable, "hi_latency": True}}'
                        )
                    fn = entry["fn"]
                    if not callable(fn):
                        raise ValueError(
                            f"Tool '{name}': 'fn' must be callable, got {type(fn).__name__}"
                        )
                    tools_dict[name] = fn
                    if entry.get("hi_latency", False):
                        hi_latency.add(name)
                        # Register all FQN forms the compiler might resolve to:
                        # - Flat name: native::tools::{name}
                        # - 2-part namespace: native::{name} (e.g., security::ask_review)
                        if "::" in name:
                            hi_latency.add(f"native::{name}")
                        else:
                            hi_latency.add(f"native::tools::{name}")
                else:
                    tools_dict[name] = entry
        return hi_latency

    def __init__(
        self,
        tools: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        interpolation_mode: str = "markdown",
        item_tag: str = "item",
        mcp_servers: dict[str, dict[str, str]] | None = None,
        enable_parallel: bool = False,
        parallel_threshold: int = 2,
        captured_logs: list | None = None,
        max_captured_logs: int = 1000,
        validate_output: bool = True,
        check_types: bool = False,  # Enable compile-time type checking
        show_enhanced_errors: bool = True,  # Enhanced error messages (default: True)
        stub_tools: bool = False,  # Accept unknown tools (return null at runtime)
        max_iterations: int | None = None,  # Global iteration limit (DoS protection)
    ):
        """Initialize the Cy interpreter.

        Args:
            tools: Optional dictionary of tools available to the Cy program
            variables: Optional dictionary of variables to inject into the program
            interpolation_mode: The default mode for interpolating lists (markdown, csv, xml)
            item_tag: The tag name to use for items when using XML interpolation mode
            mcp_servers: Optional dictionary of MCP server configurations
                       Format: {"server_name": {"base_url": "http://...", "mcp_id": "..."}}
            enable_parallel: If True, enable parallel execution of independent operations
            parallel_threshold: Minimum number of async operations to trigger parallelization
            captured_logs: Optional list to capture log() output. If None, logs go to stderr.
            validate_output: If True, validate that all code paths set output or return
            check_types: If True, perform compile-time type checking
            stub_tools: If True, unknown tools compile and return null at runtime
            max_iterations: Global iteration limit across all loop types (DoS protection).
                          Defaults to PlanExecutor.DEFAULT_MAX_ITERATIONS.
        """
        # Merge user-provided tools with default native tools.
        # Tools can be plain callables or dicts with metadata:
        #   {"fn": callable, "hi_latency": True}
        from cy_language.ui.tools import default_registry

        self.tools = default_registry.get_tools_dict()
        self.hi_latency_tools = self._process_user_tools(self.tools, tools)
        self.external_variables = variables or {}
        self.interpolation_mode = interpolation_mode
        self.item_tag = item_tag
        self.enable_parallel = enable_parallel
        self.parallel_threshold = parallel_threshold
        self.captured_logs = captured_logs
        self.max_captured_logs = max_captured_logs
        self.validate_output = validate_output
        self.check_types = check_types
        self.show_enhanced_errors = show_enhanced_errors
        self.stub_tools = stub_tools
        self.max_iterations = max_iterations

        # Initialize MCP manager if servers are configured (sync version - deprecated)
        self.mcp_manager: Any | None = None
        if mcp_servers:
            # For sync initialization, we can't use await here
            # This will be deprecated in favor of create_async()
            raise RuntimeError(
                "MCP servers require async initialization. Use Cy.create_async() instead of Cy() constructor."
            )
        self.parser = Parser(
            tools=self.tools,
            interpolation_mode=self.interpolation_mode,
            item_tag=self.item_tag,
        )

    @classmethod
    async def create_async(
        cls,
        tools: dict[str, Any] | None = None,
        variables: dict[str, Any] | None = None,
        interpolation_mode: str = "markdown",
        item_tag: str = "item",
        mcp_servers: dict[str, dict[str, str]] | None = None,
        enable_parallel: bool = False,
        parallel_threshold: int = 2,
        captured_logs: list | None = None,
        max_captured_logs: int = 1000,
        validate_output: bool = True,
        check_types: bool = False,  # Enable compile-time type checking
        show_enhanced_errors: bool = True,  # Enhanced error messages (default: True)
        stub_tools: bool = False,  # Accept unknown tools (return null at runtime)
        max_iterations: int | None = None,  # Global iteration limit (DoS protection)
    ) -> "Cy":
        """Create Cy interpreter with async initialization.

        This is the preferred way to create a Cy interpreter when using MCP servers
        as it properly handles async initialization without event loop conflicts.

        Args:
            tools: Optional dictionary of tools available to the Cy program
            variables: Optional dictionary of variables to inject into the program
            interpolation_mode: The default mode for interpolating lists (markdown, csv, xml)
            item_tag: The tag name to use for items when using XML interpolation mode
            mcp_servers: Optional dictionary of MCP server configurations
                       Format: {"server_name": {"base_url": "http://...", "mcp_id": "..."}}
            enable_parallel: If True, enable parallel execution
            parallel_threshold: Minimum async operations for parallelization
            captured_logs: Optional list to capture log() output. If None, logs go to stderr.
            validate_output: If True, validate that all code paths set output or return
            check_types: If True, perform compile-time type checking
            stub_tools: If True, unknown tools compile and return null at runtime
            max_iterations: Global iteration limit across all loop types (DoS protection).

        Returns:
            Initialized Cy interpreter instance
        """
        # Create instance without MCP servers first
        instance = cls.__new__(cls)
        from cy_language.ui.tools import default_registry

        instance.tools = default_registry.get_tools_dict()
        instance.hi_latency_tools = cls._process_user_tools(instance.tools, tools)
        instance.external_variables = variables or {}
        instance.interpolation_mode = interpolation_mode
        instance.item_tag = item_tag
        instance.enable_parallel = enable_parallel
        instance.parallel_threshold = parallel_threshold
        instance.captured_logs = captured_logs
        instance.max_captured_logs = max_captured_logs
        instance.validate_output = validate_output
        instance.check_types = check_types
        instance.show_enhanced_errors = show_enhanced_errors
        instance.stub_tools = stub_tools
        instance.max_iterations = max_iterations

        # Initialize MCP manager asynchronously if servers are configured
        instance.mcp_manager = None
        if mcp_servers:
            from cy_language.mcp_manager import MCPManager

            instance.mcp_manager = MCPManager(mcp_servers)
            await instance.mcp_manager.initialize()  # type: ignore[attr-defined]

        instance.parser = Parser(
            tools=instance.tools,
            interpolation_mode=instance.interpolation_mode,
            item_tag=instance.item_tag,
        )

        return instance

    # -- Shared error handling helpers (used by sync + async execute methods) --

    def _build_error_context(self, program: str) -> Any:
        """Create an ErrorContext for enhanced error reporting, or None."""
        if not getattr(self, "show_enhanced_errors", True):
            return None
        from .error_context import ErrorContext

        return ErrorContext(
            source_code=program,
            tool_registry=self._build_tool_registry(),
            use_color=getattr(self, "use_color_errors", True),
        )

    def _enhance_cy_error(self, e: CyError, error_context: Any) -> CyError:
        """Attach source context to a CyError and optionally print it."""
        if error_context:
            e = error_context.enhance_error(e)
            if getattr(self, "print_enhanced_errors", False):
                print(error_context.format_error(e), file=sys.stderr)
        return e

    def _handle_unexpected_error(self, e: Exception, error_context: Any) -> NoReturn:
        """Handle a non-CyError exception: enhance if possible, else wrap.

        Always raises — never returns normally.
        """
        if error_context:
            enhanced = error_context.enhance_error(e)
            if getattr(self, "print_enhanced_errors", False):
                print(error_context.format_error(enhanced), file=sys.stderr)
            raise enhanced
        # Check if it's a CyError from an alternate import path
        try:
            from cy_language.errors import CyError as AltCyError

            if isinstance(e, AltCyError):
                raise e
        except ImportError:
            pass
        raise CyError(f"Unexpected error: {e}")

    # -- Program execution entry points --

    def _execute_program(self, program: str, input_data: Any = None) -> Any:
        """Internal: run a Cy program and return the native Python result."""
        current_thread = threading.current_thread()
        old_context = getattr(current_thread, "cy_context", None)
        current_thread.cy_context = self  # type: ignore[attr-defined]
        error_context = self._build_error_context(program)

        try:
            return self._run_with_execution_plan(program, input_data, error_context)
        except TypeError:
            raise
        except CyError as e:
            raise self._enhance_cy_error(e, error_context)
        except Exception as e:
            self._handle_unexpected_error(e, error_context)
        finally:
            current_thread.cy_context = old_context  # type: ignore[attr-defined]

    async def _execute_program_async(
        self,
        program: str,
        input_data: Any = None,
        checkpoint: ExecutionCheckpoint | None = None,
    ) -> Any:
        """Internal: run a Cy program asynchronously and return the native Python result."""
        current_thread = threading.current_thread()
        old_context = getattr(current_thread, "cy_context", None)
        current_thread.cy_context = self  # type: ignore[attr-defined]
        error_context = self._build_error_context(program)

        try:
            return await self._run_with_execution_plan_async(
                program, input_data, error_context, checkpoint=checkpoint
            )
        except TypeError:
            raise
        except CyError as e:
            raise self._enhance_cy_error(e, error_context)
        except ExecutionPaused:
            raise
        except Exception as e:
            self._handle_unexpected_error(e, error_context)
        finally:
            current_thread.cy_context = old_context  # type: ignore[attr-defined]

    def run(self, program: str, input_data: Any = None) -> str:
        """Run a Cy program. Returns JSON-formatted string output.

        All output is valid JSON, parseable by json.loads() in any language.
        Use run_native() to get the raw Python object instead.

        Args:
            program: The Cy program code
            input_data: Optional input data to make available as $input

        Returns:
            JSON-formatted string (e.g. '{"a": 1}', '42', 'true', '"hello"').
            Empty string if no return statement was executed.

        Raises:
            CyError: If there is an error in the program
        """
        import json

        from .executor import _NO_RETURN

        result = self._execute_program(program, input_data)
        if result is _NO_RETURN:
            return ""
        return json.dumps(result)

    async def run_async(
        self,
        program: str,
        input_data: Any = None,
        checkpoint: ExecutionCheckpoint | None = None,
    ) -> str:
        """Run a Cy program asynchronously. Returns JSON-formatted string output.

        All output is valid JSON, parseable by json.loads() in any language.
        This is the preferred method when using MCP servers as it properly
        handles async operations without event loop conflicts.

        Args:
            program: The Cy program code
            input_data: Optional input data to make available as $input
            checkpoint: Optional ExecutionCheckpoint to resume a paused execution.
                       The checkpoint's pending_tool_result must be set before passing.

        Returns:
            JSON-formatted string (e.g. '{"a": 1}', '42', 'true', '"hello"').
            Empty string if no return statement was executed.

        Raises:
            CyError: If there is an error in the program
            ExecutionPaused: If a hi-latency tool is encountered without cached result
        """
        import json

        from .executor import _NO_RETURN

        result = await self._execute_program_async(
            program, input_data, checkpoint=checkpoint
        )
        if result is _NO_RETURN:
            return ""
        return json.dumps(result)

    def run_native(self, program: str, input_data: Any = None) -> Any:
        """Run a Cy program and return the native Python result.

        Unlike run(), this preserves the original Python type (dict, list,
        int, etc.) instead of converting to string. Use this when chaining
        Cy scripts together or when the caller needs structured data.

        Args:
            program: The Cy program code
            input_data: Optional input data to make available as $input

        Returns:
            The native Python object returned by the program, or None
            if no return statement was executed.

        Raises:
            CyError: If there is an error in the program
        """
        from .executor import _NO_RETURN

        result = self._execute_program(program, input_data)
        if result is _NO_RETURN:
            return None
        return result

    async def run_native_async(
        self,
        program: str,
        input_data: Any = None,
        checkpoint: ExecutionCheckpoint | None = None,
    ) -> Any:
        """Run a Cy program asynchronously and return the native Python result.

        Unlike run_async(), this preserves the original Python type (dict, list,
        int, etc.) instead of converting to string. Use this when chaining
        Cy scripts together or when the caller needs structured data.

        Args:
            program: The Cy program code
            input_data: Optional input data to make available as $input
            checkpoint: Optional ExecutionCheckpoint to resume a paused execution.
                       The checkpoint's pending_tool_result must be set before passing.

        Returns:
            The native Python object returned by the program, or None
            if no return statement was executed.

        Raises:
            CyError: If there is an error in the program
            ExecutionPaused: If a hi-latency tool is encountered without cached result
        """
        from .executor import _NO_RETURN

        result = await self._execute_program_async(
            program, input_data, checkpoint=checkpoint
        )
        if result is _NO_RETURN:
            return None
        return result

    async def _run_with_execution_plan_async(
        self,
        program: str,
        input_data: Any = None,
        error_context: Optional["ErrorContext"] = None,
        checkpoint: ExecutionCheckpoint | None = None,
    ) -> Any:
        """Run program using execution plan approach asynchronously."""
        # Parse the program to get AST
        try:
            ast_tree = self.parser.parse_only(program)
        except Exception as parse_error:
            # Enhance parse errors
            if error_context:
                enhanced = error_context.enhance_error(parse_error)
                raise enhanced
            raise

        # Auto-derive input schema from input_data if check_types is enabled
        input_schema = None
        if self.check_types and input_data is not None:
            from .type_analysis_api import data_to_schema

            input_schema = data_to_schema(input_data)

        tool_resolver = self._build_stub_resolver()

        # Compile AST to execution plan
        plan = compile_cy_program(
            ast_tree,
            source_file="<string>",
            available_tools=self.tools,
            lark_parser=self.parser.lark_parser_no_transform,
            mcp_manager=self.mcp_manager,
            validate_output=self.validate_output,
            check_types=self.check_types,
            input_schema=input_schema,
            tool_resolver=tool_resolver,
        )

        self._register_stub_callables(tool_resolver)

        # Build node_result_cache and checkpoint_variables from checkpoint if resuming
        node_result_cache = None
        checkpoint_variables = None
        if checkpoint is not None:
            from .execution_plan import _PENDING

            node_result_cache = dict(checkpoint.node_results)
            checkpoint_variables = dict(checkpoint.variables)
            # Inject the human's answer for the pending hi-latency tool.
            # _PENDING sentinel distinguishes "not answered" from "answered null".
            if checkpoint.pending_tool_result is not _PENDING:
                node_result_cache[checkpoint.pending_node_id] = (
                    checkpoint.pending_tool_result
                )
            # Restore captured logs from before the pause so they're preserved
            if self.captured_logs is not None and checkpoint.captured_logs:
                self.captured_logs.extend(checkpoint.captured_logs)

        # Execute the plan asynchronously
        try:
            result = await execute_plan_async(
                plan,
                input_data=input_data,
                tools=self.tools,
                variables=self.external_variables,
                interpolation_mode=self.interpolation_mode,
                item_tag=self.item_tag,
                mcp_manager=self.mcp_manager,
                enable_parallel=self.enable_parallel,
                parallel_threshold=self.parallel_threshold,
                node_result_cache=node_result_cache,
                hi_latency_tools=self.hi_latency_tools,
                checkpoint_variables=checkpoint_variables,
                max_iterations=self.max_iterations,
            )
            return result
        except CyRuntimeError as e:
            # Convert specific runtime errors to more appropriate user-facing errors
            if "No output defined" in str(e):
                from .errors import NameError as CyNameError

                raise CyNameError(
                    "No return statement found in the program", e.line, e.col
                )
            raise  # Re-raise other runtime errors as-is

    def analyze_parallelization(self, program: str) -> dict[str, Any]:
        """Analyze which for-in loops in the program would be parallelized.

        This method compiles the program and analyzes each loop to determine
        if it would be executed with async parallelization when enable_parallel=True.

        Args:
            program: The Cy program code to analyze

        Returns:
            Dictionary with analysis results including:
            - total_loops: Number of for-in loops found
            - parallelizable_loops: List of loops that can be parallelized
            - non_parallelizable_loops: List of loops that cannot be parallelized with reasons
            - would_parallelize: True if any loops would be parallelized
            - report: Human-readable analysis report
        """
        analyzer = DependencyAnalyzer(
            tools=self.tools, debug=getattr(self, "debug", False)
        )

        try:
            # Parse the program to get AST
            ast_tree = self.parser.parse_only(program)

            # Compile AST to execution plan
            # Skip output validation for analysis (not executing)
            # Skip type checking for analysis (not executing)
            plan = compile_cy_program(
                ast_tree,
                source_file="<string>",
                available_tools=self.tools,
                lark_parser=self.parser.lark_parser_no_transform,
                mcp_manager=self.mcp_manager,
                validate_output=False,
                check_types=False,
            )
        except Exception as e:
            return {
                "error": f"Failed to compile: {e!s}",
                "total_loops": 0,
                "parallelizable_loops": [],
                "non_parallelizable_loops": [],
                "would_parallelize": False,
                "report": f"Error: Failed to compile program: {e!s}",
            }

        # Analyze each node
        from cy_language.execution_plan import WhileLoopNode

        parallelizable = []
        non_parallelizable = []
        loop_index = 0

        for node in plan.nodes:
            # Check if it's a transformed for-in loop (while loop with body)
            if isinstance(node, WhileLoopNode) and hasattr(node, "body"):
                loop_index += 1
                can_parallel, reason = analyzer.can_parallelize_for_in(node)

                loop_info = {
                    "index": loop_index,
                    "can_parallelize": can_parallel,
                    "reason": reason,
                }

                if can_parallel:
                    parallelizable.append(loop_info)
                else:
                    non_parallelizable.append(loop_info)

        # Generate report
        total = len(parallelizable) + len(non_parallelizable)
        report_lines = [
            "=== Parallelization Analysis ===",
            f"Parallel execution: {'ENABLED' if self.enable_parallel else 'DISABLED'}",
            f"Threshold: {self.parallel_threshold} iterations",
            f"Total for-in loops: {total}",
        ]

        if self.enable_parallel:
            if parallelizable:
                report_lines.append(
                    f"\n✅ {len(parallelizable)} loop(s) would be parallelized:"
                )
                for loop in parallelizable:
                    report_lines.append(
                        f"  - Loop {loop['index']}: Ready for concurrent execution"
                    )
        else:
            report_lines.append(
                "\n⚠️  Parallelization is DISABLED (enable_parallel=False)"
            )
            report_lines.append(
                "   Set enable_parallel=True to activate parallelization"
            )

        if non_parallelizable:
            report_lines.append(
                f"\n❌ {len(non_parallelizable)} loop(s) would run sequentially:"
            )
            for loop in non_parallelizable:
                report_lines.append(f"  - Loop {loop['index']}: {loop['reason']}")

        report = "\n".join(report_lines)

        return {
            "total_loops": total,
            "parallelizable_loops": parallelizable,
            "non_parallelizable_loops": non_parallelizable,
            "would_parallelize": len(parallelizable) > 0 and self.enable_parallel,
            "report": report,
        }

    def would_parallelize(self, program: str) -> bool:
        """Check if any loops in the program would be parallelized.

        This is a convenience method that returns a simple boolean.

        Args:
            program: The Cy program code to check

        Returns:
            True if parallelization is enabled AND at least one loop can be parallelized
        """
        if not self.enable_parallel:
            return False

        result = self.analyze_parallelization(program)
        return bool(result.get("would_parallelize", False))

    def _build_stub_resolver(self) -> "ToolResolver | None":
        """Build a tool resolver with stub_unknown if stub_tools is enabled."""
        if not self.stub_tools:
            return None
        from .tool_resolver import build_tool_resolver

        return build_tool_resolver(
            available_tools=self.tools,
            mcp_manager=getattr(self, "mcp_manager", None),
            stub_unknown=True,
        )

    def _register_stub_callables(self, tool_resolver: Any) -> None:
        """Register null callables for tools that were auto-stubbed during compilation."""
        if tool_resolver is None or not tool_resolver.stubbed_tools:
            return

        def _null_stub(*args: Any, **kwargs: Any) -> None:
            return None

        for fqn in tool_resolver.stubbed_tools:
            self.tools[fqn] = _null_stub
            # The executor strips FQN prefixes for lookup, so register short names too
            if fqn.startswith("native::tools::"):
                self.tools[fqn[len("native::tools::") :]] = _null_stub
            elif fqn.startswith("native::"):
                self.tools[fqn[len("native::") :]] = _null_stub

    def _build_tool_registry(self) -> dict[str, Any]:
        """Build tool registry for error suggestions."""
        registry = {}

        # Add all tools (includes native functions)
        if hasattr(self, "tools"):
            registry.update(self.tools)

        return registry

    def _run_with_execution_plan(
        self,
        program: str,
        input_data: Any = None,
        error_context: Optional["ErrorContext"] = None,
    ) -> Any:
        """Run program using execution plan approach."""
        # Parse the program to get AST
        try:
            ast_tree = self.parser.parse_only(program)
        except Exception as parse_error:
            # Enhance parse errors
            if error_context:
                enhanced = error_context.enhance_error(parse_error)
                raise enhanced
            raise

        # Auto-derive input schema from input_data if check_types is enabled
        input_schema = None
        if self.check_types and input_data is not None:
            from .type_analysis_api import data_to_schema

            input_schema = data_to_schema(input_data)

        tool_resolver = self._build_stub_resolver()

        # Compile AST to execution plan
        plan = compile_cy_program(
            ast_tree,
            source_file="<string>",
            available_tools=self.tools,
            lark_parser=self.parser.lark_parser_no_transform,
            mcp_manager=self.mcp_manager,
            validate_output=self.validate_output,
            check_types=self.check_types,
            input_schema=input_schema,
            tool_resolver=tool_resolver,
        )

        self._register_stub_callables(tool_resolver)

        # Execute the plan
        try:
            result = execute_plan(
                plan,
                input_data=input_data,
                tools=self.tools,
                variables=self.external_variables,
                interpolation_mode=self.interpolation_mode,
                item_tag=self.item_tag,
                mcp_manager=self.mcp_manager,
                enable_parallel=self.enable_parallel,
                parallel_threshold=self.parallel_threshold,
                max_iterations=self.max_iterations,
            )
            return result
        except CyRuntimeError as e:
            # Convert specific runtime errors to more appropriate user-facing errors
            if "No output defined" in str(e):
                from .errors import NameError as CyNameError

                raise CyNameError(
                    "No return statement found in the program", e.line, e.col
                )
            raise  # Re-raise other runtime errors as-is
