# Cy Language

Cy is a scripting language designed for AI to write and humans to read. It's for platforms that need to execute LLM-generated or user-authored automation safely — sandboxed, composable, and verifiable before it runs.

## Why Cy?

- **Designed for AI to write, easy for humans to read.** Python-like syntax with curly-brace blocks, English boolean operators (`and`/`or`/`not`), and a small surface area. LLMs generate it reliably. Humans review it without decoding.
- **Sandboxed and isolated.** No imports, no file I/O, no eval. A script can only call tools you explicitly register. Every run is isolated — no global state, no side effects beyond what your tools do. Same inputs + same tools = same output.
- **Nothing crashes on missing data.** Accessing a missing field or out-of-bounds index returns `null` instead of throwing. Two operators — `??` and `or` — let you provide defaults where you need them. No defensive checks, no try/catch around every access.
- **Errors surface at compile time, not halfway through a run.** Unknown tools, type mismatches, and invalid field access are caught before execution starts. The type inference API can also analyze a script's return type — so you validate that script A's output matches script B's input before either one runs. This matters when tools make expensive LLM calls or slow HTTP requests: you catch errors in seconds, not after minutes of waiting.
- **Pause execution, come back later.** When a script hits a slow tool (API call, human approval), execution suspends and returns a checkpoint with full state. Resume it whenever the result is ready. No threads, no callbacks.
- **JSON in, JSON out.** Input data is JSON, `cy.run()` returns a JSON string, and the compiled plan itself is a JSON IR. You can swap the runtime — the current executor is Python, but a Rust, Go, or JS runtime can run the same compiled plan. You can also compose workflows across runtimes: one script runs in Python, its JSON output feeds the next in Rust, no serialization glue needed.

## When not to use Cy

- **You're writing application code.** Backend services, CLIs, data pipelines — just use Python. You trust your own code, you don't need a sandbox.
- **You need the Python ecosystem.** Cy has no package manager and no imports. If you need pandas, requests, or anything beyond the tools you register, Cy will get in your way.
- **You're the only one writing the scripts.** Cy's constraints exist to protect a platform from its users' scripts. If you're both the platform and the user, those constraints are overhead with no payoff.
- **You need raw performance.** Cy's executor is interpreted. It's fine for orchestration logic — calling tools, transforming data, branching on results — but don't use it for tight loops over large datasets.

## Table of Contents

- [Why Cy?](#why-cy)
- [When not to use Cy](#when-not-to-use-cy)
- [Quick Start](#quick-start)
- [CLI](#cli)
  - [Installation](#installation)
  - [Commands](#commands)
  - [External Tools](#external-tools)
- [Language at a Glance](#language-at-a-glance)
- [Python API](#python-api)
  - [Running a Script](#running-a-script)
  - [Input Data](#input-data)
  - [Variables](#variables)
  - [Custom Tools](#custom-tools)
  - [Namespaced Tools](#namespaced-tools)
  - [Logging](#logging)
  - [Error Handling](#error-handling)
  - [Async Tools](#async-tools)
  - [Pause and Resume](#pause-and-resume)
  - [Type Checking](#type-checking)
  - [Script Analysis](#script-analysis)
- [Tool Namespaces](#tool-namespaces)
- [Development Setup](#development-setup)

---

## Quick Start

**As a library:**

```bash
pip install cy-language
```

<!-- py-test: run -->
```python
from cy_language import Cy

cy = Cy()
result = cy.run("""
name = "Alice"
items = ["apple", "banana", "cherry"]
output = "Hello ${name}, you have ${len(items)} items: ${items|csv}"
return output
""")
print(result)  # Hello Alice, you have 3 items: apple, banana, cherry
```

**As a CLI tool:**

```bash
pip install cy-language[cli]
cy run program.cy
```

---

## CLI

The `cy` command-line tool lets you run, typecheck, and compile Cy programs directly from the terminal. It also provides an `install` command for setting up Cy as a skill in agentic tools like Claude Code.

### Installation

The CLI requires the `cli` extra (which adds [Typer](https://typer.tiangolo.com/)). The core library stays lean — `pip install cy-language` (without `[cli]`) does not install any CLI dependencies.

**From PyPI:**

```bash
# Install globally with pipx (recommended)
pipx install cy-language[cli]

# Or with pip
pip install cy-language[cli]
```

**From a local clone of the repo:**

```bash
# Using pipx in editable mode — makes `cy` available on your PATH,
# and source changes take effect immediately
pipx install -e ".[cli]"

# Or through Poetry (available as `poetry run cy` or after `poetry shell`)
poetry install -E cli
poetry run cy --version
```

### Commands

```
cy run <file>              # compile + typecheck + execute
cy check <file>            # compile + typecheck only, report errors
cy compile <file>          # compile only, emit execution plan as JSON
cy install <target>        # install Cy skill for an agentic tool
cy --version               # print version
```

**`cy run`** — the primary command. Parses, compiles, and executes a `.cy` file:

```bash
cy run program.cy
cy run program.cy --input "some data"
cy run program.cy --input-file data.txt
cy run program.cy --mode csv
```

**`cy check`** — compile and typecheck without executing. Useful for CI or pre-commit validation:

```bash
cy check program.cy
# No errors found. Output type: {'type': 'string'}
```

**`cy compile`** — emit the execution plan as JSON (useful for debugging or tooling):

```bash
cy compile program.cy
cy compile program.cy --pretty
```

**`cy install`** — install the Cy language skill for agentic tools:

```bash
# Install globally (~/.claude/skills/)
cy install claude-code

# Install for the current project only (.claude/skills/)
cy install claude-code --project
```

### External Tools

By default, the CLI only has access to Cy's built-in native functions. Three flags extend this:

**`--tools`** — load Python functions from a file. The file must export a `tools` dict:

<!-- py-test: run -->
```python
# Write a tools file, then use it from the CLI
from pathlib import Path
import tempfile, textwrap

tools_content = textwrap.dedent("""\
    def classify(score):
        if score >= 90: return "critical"
        if score >= 70: return "high"
        return "low"

    tools = {"classify": classify}
""")

# Verify the tools file is valid Python with the expected structure
exec_globals = {}
exec(tools_content, exec_globals)
assert isinstance(exec_globals["tools"], dict)
assert exec_globals["tools"]["classify"](85) == "high"
```

```bash
# Use with any command: run, check, or compile
cy run script.cy --tools my_tools.py
cy check script.cy --tools my_tools.py
cy compile script.cy --tools my_tools.py
```

**`--stub-tools`** — accept unknown tool calls without failing. Unknown tools return `null` at runtime. Useful for validating script logic without live integrations:

```bash
cy run script.cy --stub-tools
cy check script.cy --stub-tools

# Combine with --tools: known tools execute, unknown ones return null
cy run script.cy --tools my_tools.py --stub-tools
```

**`--mcp-stdio`** — connect to an [MCP](https://modelcontextprotocol.io/) server via stdio transport. Tools are available as `mcp::{name}::{tool}`:

```bash
cy run script.cy --mcp-stdio "demo=uv run --with mcp[cli] mcp run server.py"

# Multiple servers
cy run script.cy \
  --mcp-stdio "intel=python intel_server.py" \
  --mcp-stdio "slack=npx @mcp/slack-server"
```

---

## Language at a Glance

Cy syntax is Python-like with curly-brace blocks. Here's enough to read a script — for the full language reference, see the **[Tutorial](docs/TUTORIAL.md)**.

```cy
# Variables, strings, interpolation
name = "Alice"
scores = [95, 87, 92]
msg = "Hello ${name}, avg: ${sum(scores) / len(scores)}"

# Null safety — missing fields return null, never crash
alert = {"user": {"name": "Alice"}}
dept = alert.user.department.name   # null
ip = alert.source_ip ?? "0.0.0.0"  # ?? only replaces null, not 0 or ""

# Control flow
grade = if (scores[0] >= 90) { "A" } else { "B" }

results = []
for (s in scores) {
    results = results + [if (s >= 90) { "pass" } else { "fail" }]
}

# List comprehensions
admins = [u.name for(u in users) if(u.role == "admin")]

# Tool calls (built-in or custom)
upper = str::uppercase(name)
data = app::threat_intel::ip_lookup(ip="8.8.8.8")

# Error handling
try {
    result = risky_operation()
} catch (e) {
    result = "failed: ${e}"
}

# Every script ends with return
return {"grade": grade, "results": results}
```

**Key differences from Python:** curly braces not indentation, `and`/`or`/`not` (no `&&`/`||`), `in` for membership, `??` for null defaults, `${...}` interpolation, all field access is null-safe, no imports, `break`/`continue` for loop control, every script must `return`.

📖 **Full language tutorial:** [docs/TUTORIAL.md](docs/TUTORIAL.md) — syntax, control flow, native functions, type checking, and real-world examples.

---

## Python API

Cy embeds in any Python application as a library. Every example in this section is executed by the test suite — if the API changes, these break before the docs go stale.

### Running a Script

`run()` returns a JSON string. `run_native()` returns a Python object:

<!-- py-test: run -->
```python
import json
from cy_language import Cy

cy = Cy()

# run() → JSON string, always
json_result = cy.run("""
name = "Alice"
return {"greeting": "Hello ${name}", "length": len(name)}
""")
parsed = json.loads(json_result)
assert parsed == {"greeting": "Hello Alice", "length": 5}

# run_native() → Python object
native_result = cy.run_native("""
items = [1, 2, 3, 4, 5]
return {"total": sum(items), "count": len(items)}
""")
assert native_result == {"total": 15, "count": 5}
assert isinstance(native_result, dict)
```

Both have async variants: `run_async()` and `run_native_async()`.

### Input Data

Pass data into a script with `input_data`. It becomes the `input` variable:

<!-- py-test: run -->
```python
from cy_language import Cy

cy = Cy()
result = cy.run_native("""
name = input.name ?? "Anonymous"
scores = input.scores ?? []
return {"greeting": "Hello ${name}", "total": sum(scores)}
""", input_data={"name": "Bob", "scores": [10, 20, 30]})

assert result == {"greeting": "Hello Bob", "total": 60}
```

Missing fields don't crash — they return `null`, and `??` provides a fallback:

<!-- py-test: run -->
```python
from cy_language import Cy

cy = Cy()
result = cy.run_native("""
name = input.name ?? "Anonymous"
return name
""", input_data={})

assert result == "Anonymous"
```

### Variables

Pre-define variables available to every script run. Use them for configuration and constants:

<!-- py-test: run -->
```python
from cy_language import Cy

cy = Cy(variables={
    "threshold": 50,
    "env": "production",
    "allowed_ips": ["10.0.0.1", "10.0.0.2"],
})

result = cy.run_native("""
status = if (env == "production") { "live" } else { "dev" }
return {"status": status, "threshold": threshold, "ip_count": len(allowed_ips)}
""")

assert result == {"status": "live", "threshold": 50, "ip_count": 2}
```

**`variables` vs `input_data`:** Variables are set once on the `Cy` instance and reused across calls. `input_data` changes per call — it's the data each script processes:

<!-- py-test: run -->
```python
from cy_language import Cy

cy = Cy(variables={"max_score": 100})

r1 = cy.run_native('return "${input.name}: ${max_score}"', input_data={"name": "Alice"})
r2 = cy.run_native('return "${input.name}: ${max_score}"', input_data={"name": "Bob"})

assert r1 == "Alice: 100"
assert r2 == "Bob: 100"
```

### Custom Tools

Register Python functions as tools. Scripts can only call tools you register plus the built-in native functions:

<!-- py-test: run -->
```python
from cy_language import Cy

def classify(score):
    if score >= 90:
        return "critical"
    elif score >= 70:
        return "high"
    return "low"

cy = Cy(tools={"classify": classify})

result = cy.run_native("""
sev = classify(85)
return {"severity": sev, "label": "Score 85 is ${sev}"}
""")

assert result["severity"] == "high"
```

Tools accept positional, named, or mixed arguments (positional first, then named — like Python):

<!-- py-test: run -->
```python
from cy_language import Cy

def search(query, limit=10, offset=0):
    return {"query": query, "limit": limit, "offset": offset}

cy = Cy(tools={"search": search})

# All positional
r1 = cy.run_native('return search("alerts", 5, 20)')
assert r1 == {"query": "alerts", "limit": 5, "offset": 20}

# All named
r2 = cy.run_native('return search(query="alerts", limit=5, offset=20)')
assert r2 == {"query": "alerts", "limit": 5, "offset": 20}

# Mixed: positional first, then named (skip optional params with named)
r3 = cy.run_native('return search("alerts", offset=20)')
assert r3 == {"query": "alerts", "limit": 10, "offset": 20}
```

Dicts returned by tools are accessible with dot notation in Cy:

<!-- py-test: run -->
```python
from cy_language import Cy

def lookup_user(user_id):
    return {"id": user_id, "name": "Alice", "role": "admin"}

cy = Cy(tools={"lookup_user": lookup_user})

result = cy.run_native("""
user = lookup_user("U001")
return "${user.name} (${user.role})"
""")

assert result == "Alice (admin)"
```

### Namespaced Tools

For integrations with external systems, use a 3-part namespace — `app::{integration}::{action}`:

<!-- py-test: run -->
```python
from cy_language import Cy

def ip_lookup(ip):
    return {"ip": ip, "country": "US", "risk": "low"}

def domain_lookup(domain):
    return {"domain": domain, "registrar": "Example Inc"}

cy = Cy(tools={
    "app::threat_intel::ip_lookup": ip_lookup,
    "app::threat_intel::domain_lookup": domain_lookup,
})

result = cy.run_native("""
ip_info = app::threat_intel::ip_lookup("8.8.8.8")
domain_info = app::threat_intel::domain_lookup("example.com")
return {
    "ip_country": ip_info.country,
    "registrar": domain_info.registrar
}
""")

assert result == {"ip_country": "US", "registrar": "Example Inc"}
```

This keeps tool names organized and avoids collisions when multiple integrations are registered.

### Logging

`log()` writes to stderr and doesn't affect the return value. Pass `captured_logs` to collect messages programmatically:

<!-- py-test: run -->
```python
from cy_language import Cy

logs = []
cy = Cy(captured_logs=logs)

result = cy.run_native("""
data = [1, 2, 3, 4, 5]
log("Processing ${len(data)} items")
total = sum(data)
log("Total: ${total}")
return total
""")

assert result == 15
messages = [entry["message"] for entry in logs]
assert messages == ["Processing 5 items", "Total: 15"]
```

### Error Handling

All Cy errors inherit from `CyError`. Catch it to handle any script failure, or catch specific subclasses for finer control:

<!-- py-test: run -->
```python
from cy_language import Cy
from cy_language.errors import CyError, CompilerError

cy = Cy()

# Unknown tool → caught at compile time (before execution)
try:
    cy.run('return bogus_function()')
except CompilerError as e:
    assert "bogus_function" in str(e)

# Runtime error → caught during execution
try:
    cy.run('return 1 / 0')
except CyError as e:
    assert "zero" in str(e).lower()
```

**Exception hierarchy:**
- `CyError` — base class for all Cy errors
  - `CompilerError` — unknown tools, type mismatches
    - `AmbiguousToolError` — tool short name matches multiple FQNs
    - `ToolResolutionError` — tool cannot be resolved
  - `SyntaxError` — syntax errors
  - `RuntimeError` — evaluation errors (division by zero, type mismatch at runtime)
  - `InterpolationError` — string interpolation errors
  - `NameError` — undefined variables or invalid names
  - `ToolError` — tool-related errors
    - `ToolNotFoundError` — referenced tool not found
    - `ToolInvocationError` — a registered tool raised during execution
  - `NotSupportedYetError` — reserved but unimplemented features

### Async Tools

Async Python functions work as tools with no special registration — the executor detects and awaits them automatically:

<!-- py-test: run -->
```python
import asyncio
from cy_language import Cy

async def fetch_data(url):
    # In practice, this would be an HTTP call
    return {"url": url, "status": 200, "body": "ok"}

async def main():
    cy = Cy(tools={"fetch_data": fetch_data})
    result = await cy.run_native_async("""
    data = fetch_data("https://api.example.com/users")
    return {"status": data.status, "body": data.body}
    """)
    assert result == {"status": 200, "body": "ok"}

asyncio.run(main())
```

### Pause and Resume

Mark a tool as `hi_latency` to pause execution when it's called. The script suspends, returns a checkpoint with full state, and resumes later when you provide the result:

<!-- py-test: run -->
```python
import asyncio
from cy_language import Cy
from cy_language.errors import ExecutionPaused

async def approve(question):
    return "placeholder"  # actual function is never called during pause

async def main():
    cy = Cy(tools={
        "approve": {"fn": approve, "hi_latency": True},
    })

    program = """
    answer = approve("Deploy to production?")
    return "Decision: ${answer}"
    """

    # First run — pauses at approve(), returns a checkpoint
    try:
        await cy.run_native_async(program)
    except ExecutionPaused as e:
        checkpoint = e.checkpoint

    # Later — provide the human's answer and resume
    checkpoint.pending_tool_result = "yes, deploy"
    result = await cy.run_native_async(program, checkpoint=checkpoint)
    assert result == "Decision: yes, deploy"

asyncio.run(main())
```

The checkpoint is JSON-serializable — store it in a database, send it to a queue, resume hours later.

### Type Checking

Enable `check_types` to catch errors at compile time — before the script runs:

<!-- py-test: expect-error -->
```python
from cy_language import Cy

cy = Cy(check_types=True)
cy.run("""
x = 5
y = "text"
result = x + y
return result
""")
```

Use `analyze_types()` to infer a script's output schema without running it — useful for validating that one script's output matches another's input:

<!-- py-test: run -->
```python
from cy_language import analyze_types

schema = analyze_types("""
name = "Alice"
score = 95
return {"name": name, "score": score}
""")

assert schema["type"] == "object"
assert "name" in schema["properties"]
assert "score" in schema["properties"]
```

### Script Analysis

Inspect what a script depends on — which tools it calls and which external variables it references — without running it:

<!-- py-test: run -->
```python
from cy_language import analyze_script

result = analyze_script("""
name = input.name ?? "Anonymous"
upper = str::uppercase(name)
return {"name": upper, "length": len(name)}
""")

assert "input" in result["external_variables"]
assert "native::str::uppercase" in result["tools_used"]
assert "native::tools::len" in result["tools_used"]
```

---

## Tool Namespaces

Cy uses `::` delimited namespaces for tools.

Native tools use two levels:
- **Flat name**: `len`, `str`, `int`, `from_json`, etc.
- **Namespaced**: `str::uppercase`, `list::sort`, `json::parse`, `time::now`, etc.

Integration tools use three levels:
- `app::{integration}::{action}` — e.g., `app::virustotal::ip_reputation`
- `mcp::{server}::{tool}` — for MCP (Model Context Protocol) tools

Both flat and namespaced names work interchangeably in scripts:

```cy
# These are equivalent
result1 = uppercase("hello")
result2 = str::uppercase("hello")
```

---

## Development Setup

```bash
# Install with dev dependencies
poetry install --with dev

# Install with CLI support (for working on the cy command)
poetry install -E cli

# Run all tests
poetry run pytest tests/ -x -q

# Run CLI tests only
poetry run pytest tests/unit/test_cli.py -x -q

# Run the CLI through Poetry
poetry run cy --version
poetry run cy run examples/basic/01_basic_variable_assignment.cy

# Install the CLI globally from your local checkout (editable)
pipx install -e ".[cli]"
```

### Skills (via skilltree)

This repo uses [skilltree](https://github.com/imarios/skilltree) to manage Claude Code skills as declared dependencies. The manifest lives in `skilltree.yaml`; installed skills land under `.claude/skills/` and are gitignored.

Install skilltree once:

```bash
pipx install skilltree
```

Then, from the repo root:

```bash
# Fetch and install all skills declared in skilltree.yaml
skilltree install

# List what's installed
skilltree list

# Pull updated versions of remote skills
skilltree update
```

Local skills (e.g., `skills/cy-language-programming`) are symlinked, so edits take effect immediately. Remote skills are read-only artifacts — to change one, edit it in its origin repo, then `skilltree update` here (bump the pinned version first if the manifest pins a specific tag).

---

## License

Apache-2.0
