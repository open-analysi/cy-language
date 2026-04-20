# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Orientation

- **Product pitch + Python API examples:** `README.md`.
- **Language surface (syntax, control flow, native functions):** `docs/TUTORIAL.md`.
- **Design spec (source of truth when behavior is ambiguous):** `docs/specs/cy_language_design.md`.

## Design bias: prefer simpler over more features

When the language surface gets painful, propose dropping the feature rather than working harder to support it. Real precedent: we removed support for double quotes inside interpolation (`"${a["a"]}"` — painful) in favor of single quotes only (`"${a['a']}"` — trivial). If something is fighting you, say so and suggest the simpler alternative. The spec can be edited.

## Docs are tested code

Every ```` ```cy ```` block in any file listed in `DOC_FILES` (inside `tests/unit/test_doc_cy_blocks.py`) is validated by the test suite. UI examples in `src/cy_language/ui/examples.py` are always compiled and executed. ```` ```python ```` blocks in `README.md` can be executed with `<!-- py-test: run -->`.

Blocks are **strict**: every block must pass whatever its annotation demands, or carry an explicit annotation — no auto-classification. Annotations are HTML comments on the line immediately before the opening fence:

| Annotation | What it asserts |
|---|---|
| *(none)* | Must **parse** successfully (syntax check only) |
| `<!-- cy-test: run -->` | Must **compile and execute** successfully |
| `<!-- cy-test: compile-only -->` | Must **parse and transform** (no execution) |
| `<!-- cy-test: expect-error -->` | Must **fail** to parse (assert invalid syntax) |
| `<!-- cy-test: expect-error: X -->` | Must fail with error message containing `X` |
| `<!-- cy-test: skip -->` | Skipped (use only when the block isn't Cy at all) |

Notes:
- `expect-error` assertions are two-way: if the language later starts accepting the block, the test fails and the docs must be updated.
- Prefer splitting mixed valid/invalid examples into separate blocks over skipping whole blocks.
- After touching any `.cy` block, run `poetry run pytest tests/unit/test_doc_cy_blocks.py -x -q`.
- To bring a new markdown file under validation, add its path to `DOC_FILES` in that test file.

## Commands

Use `poetry` for everything Python. Run `make help` for the full target list (test, test-all, test-cli, lint, format, typecheck, release, …). `pytest-asyncio` is in auto mode — plain `async def test_*` works without decorators.

Version bumps and `CHANGELOG.md` are managed by commitizen via `make release` (reads Conventional Commits). Don't hand-edit the version in `pyproject.toml`.

## Architecture — the pipeline

```
source text
   │  parser.py + grammar.py            (Lark LALR → AST)
   ▼
   AST
   │  compiler.py                       (AST → ExecutionPlan nodes; validates tool refs)
   ▼
   ExecutionPlan   ◄── serializable JSON IR (execution_plan.py: to_json / from_json)
   │  type_inference_engine.py          (walks plan; NameError on undefined vars, etc.)
   ▼
   executor.py                          (interprets the plan; async-aware; pause/resume)
```

Load-bearing modules (others are self-documenting from their filenames):

- **`interpreter.py`** — public `Cy` facade: `run`, `run_native`, `run_async`, `run_native_async`.
- **`compiler.py`** (~113 KB) — biggest file in the repo; AST lowering + tool/namespace validation.
- **`executor.py`** (~98 KB) — the interpreter loop, including sync/async tools, pause/resume, and node-level result caching for replay.
- **`type_inference_engine.py`** (~74 KB) — the type engine; runs at compile time when `check_types=True`.
- **`tool_resolver.py`** — short-name / FQN / alias resolution with ambiguity detection.
- **`native_functions.py`** — registers the `str::` / `list::` / `json::` / `math::` / `time::` / `regex::` / `url::` / `ip::` / `type::` / `llm::` stdlib; each namespaced name is also aliased to a legacy flat name for backward compatibility.

## Non-obvious invariants

- **Type checking defaults differ by entry point.** The API default is **opt-in** (`Cy(check_types=False)`); the CLI (`cy run`, `cy check`) enables it **by default** and exposes `--no-check-types` to disable. When adding features, check both paths.
- **`input` is read-only** inside a script; the compiler rejects direct reassignment. Assign a copy first: `x = input`.
- **Execution Plans and outputs are pure JSON.** The executor sanitizes Python-specific values (datetime, Decimal, sets, UUID, custom classes) via `_sanitize_for_json` in `executor.py`. Don't add Python-type leakage into outputs.
- **`run()` returns a JSON string; `run_native()` returns native Python values.** Chain scripts with `run_native()` — the next script's `input` wants structured data, not a string.
- **Pause/resume:** tools registered with `hi_latency: True` suspend execution via the `ExecutionPaused` exception; the raised `ExecutionCheckpoint` is JSON-serializable (`to_json` / `from_json`) and replayable later with `checkpoint.pending_tool_result` set.
- **Interpolation has two syntaxes, on purpose:** `$var` for bare identifiers, `${expr}` for anything else (indexing, field access, arithmetic, function calls, `|format` hints). Don't try to make `$arr[0]` work inside strings — use `${arr[0]}`.
- **Inside `${...}` in a normal string, use single quotes for dict keys** (`${data['key']}`). Double quotes there collide with the surrounding string delimiter; they only work inside triple-quoted strings. This is enforced in `grammar.py`.
