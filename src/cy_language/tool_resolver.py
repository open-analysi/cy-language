"""
Tool Resolver for Cy language namespace system.

Resolves function names (FQN or short names) to fully qualified names with
compile-time ambiguity detection and helpful error messages.

"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from cy_language.tool_signature import ToolSignature

# Domain aliases for polymorphic built-ins. These map 2-part user-facing names
# to the flat canonical name. They are registered in the FQN registry (so
# str::len → native::str::len resolves) but NOT in the short name index (so
# typing just "len" still unambiguously resolves to native::tools::len).
_DOMAIN_ALIASES: dict[str, str] = {
    "str::len": "len",
    "list::len": "len",
    "dict::len": "len",
    "list::sum": "sum",
    "list::min": "min",
    "list::max": "max",
}


class ToolResolver:
    """Resolves function names to FQNs with compile-time validation.

    Supports both Fully Qualified Names (FQN) like app::splunk::search_run
    and short names like search_run, with intelligent ambiguity detection.

    Also stores type metadata for each tool to support type inference.
    """

    def __init__(self, *, stub_unknown: bool = False) -> None:
        """Initialize empty tool resolver.

        Args:
            stub_unknown: If True, unknown tools are auto-registered as stubs
                         instead of raising ToolResolutionError. Stubs are
                         recorded in ``stubbed_tools`` for runtime wiring.
        """
        self.fqn_registry: dict[
            str, Callable | None
        ] = {}  # FQN → function (or None for placeholders)
        self.short_name_index: dict[str, list[str]] = {}  # short_name → [FQNs]
        # Type metadata storage
        self._type_metadata: dict[str, ToolSignature] = {}  # FQN → complete signature
        self.stub_unknown = stub_unknown
        self.stubbed_tools: set[str] = set()  # FQNs that were auto-stubbed

    def register_tool(self, fqn: str, function: Callable | None) -> None:
        """Register a tool with its FQN.

        Args:
            fqn: Fully qualified name (e.g., "app::splunk::search_run")
            function: The callable function, or None for placeholder tools

        Raises:
            ValueError: If FQN is empty or invalid
        """
        if not fqn:
            raise ValueError("FQN cannot be empty")

        self.fqn_registry[fqn] = function

    def register_short_name(self, short_name: str, fqn: str) -> None:
        """Register a short name mapping to FQN.

        Args:
            short_name: Short name (e.g., "search_run")
            fqn: Fully qualified name this short name maps to

        Raises:
            ValueError: If short_name or fqn is empty
        """
        if not short_name or not fqn:
            raise ValueError("Short name and FQN cannot be empty")

        if short_name not in self.short_name_index:
            self.short_name_index[short_name] = []

        if fqn not in self.short_name_index[short_name]:
            self.short_name_index[short_name].append(fqn)

    def _stub_tool(self, name: str) -> tuple[str, str]:
        """Auto-register an unknown tool as a stub and return its resolution.

        Used when ``stub_unknown=True`` to accept any tool name at compile time.
        """
        fqn = name if "::" in name else f"native::tools::{name}"

        self.fqn_registry[fqn] = None
        self.stubbed_tools.add(fqn)
        # Only register short names for flat tools. Namespaced stubs (app::x::y)
        # are resolved by FQN — registering their leaf name would cause ambiguity
        # when multiple namespaces share the same leaf (e.g. app::a::run, app::b::run).
        if "::" not in name:
            self.register_short_name(name, fqn)
        return (fqn, name)

    def resolve(self, name: str) -> tuple[str, str]:
        """Resolve a name to (FQN, original_name).

        Args:
            name: Either an FQN or short name

        Returns:
            Tuple of (resolved_fqn, original_name)

        Raises:
            AmbiguousToolError: If short name matches multiple FQNs
            ToolResolutionError: If name cannot be resolved (and stub_unknown is False)
        """
        from cy_language.errors import AmbiguousToolError, ToolResolutionError

        # If contains ::, it could be a full FQN or a 2-part user namespace
        if "::" in name:
            # First check if it's a direct match (full 3-part FQN)
            if name in self.fqn_registry:
                return (name, name)

            # Check if it's a 2-part user namespace (e.g., str::uppercase)
            # Try to resolve by prefixing with "native::"
            parts = name.split("::")
            if len(parts) == 2:
                native_fqn = f"native::{name}"
                if native_fqn in self.fqn_registry:
                    return (native_fqn, name)

            # Not found — stub or raise
            if self.stub_unknown:
                return self._stub_tool(name)
            suggestions = self.get_matches(name)
            raise ToolResolutionError(name, suggestions)

        # Short name - check for ambiguity
        if name in self.short_name_index:
            matches = self.short_name_index[name]
            if len(matches) == 1:
                return (matches[0], name)
            # Check if all matches point to the same function (aliases)
            # If so, it's not truly ambiguous - prefer the namespaced version
            functions = [self.fqn_registry.get(fqn) for fqn in matches]
            unique_functions = {id(f) for f in functions if f is not None}

            if len(unique_functions) == 1:
                # All matches are aliases for the same function
                # Prefer the 2-part namespaced version if available
                for fqn in matches:
                    parts = fqn.split("::")
                    # Prefer native::{namespace}::{name} over native::tools::{name}
                    if len(parts) == 3 and parts[1] != "tools":
                        return (fqn, name)
                # Fall back to first match
                return (matches[0], name)
            raise AmbiguousToolError(name, matches)

        # Not found — stub or raise
        if self.stub_unknown:
            return self._stub_tool(name)
        suggestions = self.get_matches(name)
        raise ToolResolutionError(name, suggestions)

    def get_matches(self, partial_name: str) -> list[str]:
        """Get user-friendly tool names that match partial name (for suggestions).

        Returns names in the form users would type them:
        - Native flat tools: "len", "sum"
        - Native namespaced tools: "str::uppercase", "json::parse"
        - App/MCP tools: "app::splunk::search_run" (full FQN)

        Args:
            partial_name: Partial tool name to match

        Returns:
            List of user-friendly tool names (up to 5)
        """
        matches = set()
        partial_lower = partial_name.lower()

        for fqn in self.fqn_registry:
            fqn_lower = fqn.lower()

            matched = False
            # Match if partial_name is substring of FQN
            if partial_lower in fqn_lower:
                matched = True

            # Also check if it's similar to the short name (last part of FQN)
            if not matched and "::" in fqn:
                short_name = fqn.split("::")[-1].lower()
                if (
                    len(partial_lower) >= 3 and short_name.startswith(partial_lower[:3])
                ) or (
                    len(short_name) >= 3 and partial_lower.startswith(short_name[:3])
                ):
                    matched = True

            if matched:
                matches.add(self._fqn_to_user_name(fqn))

        return sorted(matches)[:5]

    @staticmethod
    def _fqn_to_user_name(fqn: str) -> str:
        """Convert internal FQN to user-facing name.

        Examples:
            native::tools::len → len
            native::str::uppercase → str::uppercase
            native::json::parse → json::parse
            app::splunk::search_run → app::splunk::search_run
        """
        if fqn.startswith("native::tools::"):
            return fqn[len("native::tools::") :]
        if fqn.startswith("native::"):
            return fqn[len("native::") :]
        return fqn

    # Type metadata methods

    def register_tool_with_types(self, signature: "ToolSignature") -> None:
        """Register a tool with complete type information.

        This stores type metadata
        while maintaining backward compatibility with existing code.

        Args:
            signature: ToolSignature with complete type information
        """
        # Store type metadata
        self._type_metadata[signature.fqn] = signature

        # Also register using legacy API for backward compatibility
        self.register_tool(signature.fqn, signature.function)

        # Register short name (extract from FQN)
        if "::" in signature.fqn:
            short_name = signature.fqn.split("::")[-1]
            # Skip short name for domain aliases of polymorphic built-ins.
            # E.g., native::str::len should not add "len" to the short name index
            # since "len" already resolves via native::tools::len. The 2-part
            # syntax (str::len) still works through the native:: prefix lookup.
            fqn_suffix = signature.fqn.removeprefix("native::")
            if fqn_suffix not in _DOMAIN_ALIASES:
                self.register_short_name(short_name, signature.fqn)

    def get_signature(self, name: str) -> Optional["ToolSignature"]:
        """Get tool signature for a given name (FQN or short name).

        Args:
            name: Fully qualified name or short name

        Returns:
            ToolSignature if available, None otherwise
        """
        # If it's an FQN, look it up directly
        if "::" in name:
            return self._type_metadata.get(name)

        # Otherwise, it's a short name - resolve to FQN first
        if name in self.short_name_index:
            matches = self.short_name_index[name]
            if len(matches) == 1:
                fqn = matches[0]
                return self._type_metadata.get(fqn)
            # If ambiguous, return None (caller should handle ambiguity)

        # Not found
        return None

    def has_signature(self, fqn: str) -> bool:
        """Check if tool has type signature available.

        Args:
            fqn: Fully qualified name

        Returns:
            True if signature exists, False otherwise
        """
        return fqn in self._type_metadata

    def has_tool(self, fqn: str) -> bool:
        """Check if tool is registered.

        Args:
            fqn: Fully qualified name

        Returns:
            True if tool exists, False otherwise
        """
        return fqn in self.fqn_registry

    def get_tool_signature(self, fqn: str) -> Optional["ToolSignature"]:
        """Get tool signature for a given FQN (alias for get_signature).

        Args:
            fqn: Fully qualified name

        Returns:
            ToolSignature if available, None otherwise
        """
        return self.get_signature(fqn)

    @classmethod
    def from_native_tools(cls) -> "ToolResolver":
        """Create ToolResolver with native functions auto-registered.

        Uses inspect module to extract type signatures from Python functions
        and automatically registers all native tools with complete type information.

        Note:
            - Flat tools (e.g., "len") get FQN: native::tools::len
            - Namespaced tools (e.g., "type::str") get FQN: native::type::str
            - This maintains the 3-part FQN format: namespace::category::name

        Returns:
            ToolResolver with all native tools registered
        """
        from cy_language.tool_signature import extract_signature_from_function
        from cy_language.ui.tools import default_registry

        resolver = cls()
        tools_dict = default_registry.get_tools_dict()

        for tool_name, tool_func in tools_dict.items():
            # Build FQN - handle 2-part namespaced names differently
            if "::" in tool_name:
                # Tool already has namespace (e.g., "type::str", "json::parse")
                # Use format: native::{namespace}::{name}
                fqn = f"native::{tool_name}"
            else:
                # Flat tool (e.g., "len", "sum")
                # Use format: native::tools::{name}
                fqn = f"native::tools::{tool_name}"

            # Extract signature from function
            signature = extract_signature_from_function(
                fqn=fqn, function=tool_func, description=""
            )

            # Register with type information
            resolver.register_tool_with_types(signature)

        return resolver

    def export_signatures(self) -> dict[str, Any]:
        """Export all tool signatures as JSON-compatible dict.

        Returns:
            Dict mapping FQN to serialized tool signatures
        """
        return {
            fqn: signature.model_dump(exclude={"function"})
            for fqn, signature in self._type_metadata.items()
        }

    def import_signatures(self, data: dict[str, Any]) -> None:
        """Import tool signatures from JSON-compatible dict.

        Args:
            data: Dict mapping FQN to serialized tool signatures
        """
        from cy_language.tool_signature import ToolSignature

        if not isinstance(data, dict):
            raise TypeError("Import data must be a dictionary")

        for fqn, sig_data in data.items():
            # Validate sig_data is a dict
            if not isinstance(sig_data, dict):
                raise ValueError(
                    f"Signature data for '{fqn}' must be a dictionary, got {type(sig_data).__name__}"
                )

            try:
                # Deserialize signature
                signature = ToolSignature.model_validate({**sig_data, "function": None})
            except AttributeError as e:
                raise ValueError(f"Invalid signature format for '{fqn}': {e}")

            # Register it (without function since import doesn't include callable)
            self._type_metadata[fqn] = signature

            # Also register in legacy registry
            self.register_tool(fqn, None)

            # Register short name
            if "::" in fqn:
                short_name = fqn.split("::")[-1]
                self.register_short_name(short_name, fqn)


# PHASE 27: Unified build_tool_resolver() function
def build_tool_resolver(
    include_native: bool = True,
    tool_registry: Any | None = None,
    available_tools: dict[str, Callable] | None = None,
    custom_tools: dict[str, Callable] | None = None,
    mcp_manager: Any | None = None,
    app_manager: Any | None = None,
    arc_router: Any | None = None,
    stub_unknown: bool = False,
) -> "ToolResolver":
    """
    Build ToolResolver with proper type signatures from all tool sources.

    SINGLE SOURCE OF TRUTH - This function is used by both:
    - analyze_types() (type analysis path)
    - compile_cy_program() (execution path)

    Args:
        include_native: Include built-in native tools (len, str, etc.)
        tool_registry: Pre-built ToolRegistry (takes precedence over managers)
        available_tools: Custom tools dict (for Cy() path, legacy name)
        custom_tools: Custom tools dict (preferred name, same as available_tools)
        mcp_manager: MCP tool manager
        app_manager: Application tool manager
        arc_router: Archetype router for placeholders
        stub_unknown: If True, unknown tools are auto-registered as stubs

    Returns:
        ToolResolver with all tools properly registered with type signatures
    """
    from cy_language.tool_registry_builder import build_tool_registry

    resolver = ToolResolver(stub_unknown=stub_unknown)

    # PATH 1: If tool_registry is provided, use it directly (takes precedence)
    if tool_registry is not None:
        # Convert ToolRegistry to ToolResolver by registering all tools
        for _fqn, signature in tool_registry.tools.items():
            resolver.register_tool_with_types(signature)
        return resolver

    # Merge available_tools and custom_tools (support both parameter names)
    tools_dict = {}
    if available_tools:
        tools_dict.update(available_tools)
    if custom_tools:
        tools_dict.update(custom_tools)

    # PATH 2: Build registry from managers
    registry = build_tool_registry(
        include_native=include_native,
        mcp_manager=mcp_manager,
        app_manager=app_manager,
        custom_tools=tools_dict if tools_dict else None,
    )

    # Convert registry to resolver
    for _fqn, signature in registry.tools.items():
        resolver.register_tool_with_types(signature)

    # Handle arc_router (archetype placeholders)
    if arc_router is not None and hasattr(arc_router, "get_all_archetypes"):
        # Register archetype tools as placeholders
        from cy_language.tool_signature import ToolSignature

        for arc_fqn in arc_router.get_all_archetypes():
            # Create placeholder signature (returns object type)
            placeholder_sig = ToolSignature(
                fqn=arc_fqn,
                function=None,
                parameters={},
                return_type={"type": "object"},
                description="Archetype placeholder",
            )
            resolver.register_tool_with_types(placeholder_sig)

    return resolver
