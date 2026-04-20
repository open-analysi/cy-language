# The Cy Language Design Specification

+++
version = "1.0"
date = "2026-04-19"
status = "active"

[[changelog]]
version = "1.0"
date = "2026-04-19"
summary = "Reset spec versioning to flat structure per spec-template. Content carried forward from legacy v4."
+++

## About

Our goal is to define the **Cy Language**, a domain-specific language (DSL) designed to build AI agents for analyzing, prioritizing, and resolving cybersecurity alerts. This document focuses solely on the design and implementation of the Cy Language.

In short, the Cy Language is how we program AI-based Tasks. An alternative would have been to let users write Python scripts using tools like LangChain or LangGraph, but that approach introduces several limitations that Cy is designed to address:

* Executing arbitrary Python code within a SaaS environment raises serious security risks. Cy allows us to constrain the behavior of user-defined programs, making it easier to audit and enforce policy.
* Cy is a domain-specific language purpose-built for orchestrating LLM-based workflows, rather than a general-purpose language.
* Cy programs are compiled into a **Task Execution Plan**—a structured, graph-based representation of the steps and dependencies involved in executing a Task. This plan can be interpreted in multiple ways: a simple interpreter could run it sequentially in Python (current mode), while a more advanced one could convert it into a LangGraph DAG for parallel execution (future work).
* **Compilation always includes type checking** (enabled by default; opt-out available for backward compatibility). This catches typos and type errors before any side-effects occur at runtime.
* **Execution Plans are serializable to JSON** (`ExecutionPlan.to_json()` / `from_json()`) so a compiled plan can be cached and re-run without recompiling. The CLI supports replaying a pre-compiled plan directly.

## Terminology

### Task

A **Task** is a single unit of work that needs to be completed. It typically has one or more inputs and produces one output. In the context of LLMs, a Task can be thought of as a prompt to the model with a specific objective and all the required information.

Tasks can invoke other Tasks, similar to how functions call other functions in programming. This forms a **call graph** (e.g., A → B → C), where Task A calls Task B, and B calls Task C. Cycles are not allowed.

Each Task includes:

* A **Directive**—usually a Cy script—that defines the prompt for the LLM and/or the sequence of steps required to construct a dynamic prompt.
* A set of **Knowledge Units** available during execution. Some may be directly referenced in the script; others are implicitly added as contextual information in the prompt, constructed automatically (not defined in the Directive).

### Knowledge Units

**Knowledge Units** are entities available to the LLM during Task execution. These include:

* **Documents** (e.g., PDFs, Markdown, plain text)
* **Tables** (structured data)
* **Tools** (external functions or APIs)

### Directive

A **Directive** is the instruction set given to the LLM to define the goal of the Task and the context required to complete it. It can range from a simple static message to a fully programmable script that references external Knowledge Units. In other words, a Directive is the script (definition) for a Task, while a Task is the instance that gets executed with specific inputs.

A Directive can be:

* A static block of text
* A dynamic script written in the **Cy Language**

Directives may reference other Tasks, Tools, Documents, and Tables, enabling complex prompt construction.

### Tool

A **Tool** is a callable function that an LLM can use to complete its Task. These functions can be provided by external systems, such as MCP (Model Context Protocol) servers.

In Cy, a Tool is called like a regular function inside a script.

Since different MCP servers may bring similarly named tools, Cy language supports namespacing as follows:
- `mcp::server1::function1()`
- `mcp::server2::function1()`

### Native Function

**Native Functions** are built-in operations in the Cy language—like `add(1, 2)` or `print()` in Python.

Native functions are organized into **2-part namespaces** by domain, making the standard library discoverable and unambiguous:
- `str::` — string operations (`str::len`, `str::uppercase`, `str::split`, …)
- `list::` — list operations (`list::len`, `list::sum`, `list::sort`, …)
- `json::` — JSON parse/stringify (`json::parse`, `json::stringify`)
- `math::`, `time::`, `regex::`, `url::`, `ip::`, `type::`, `llm::` — and others

This is distinct from the 3-part form used for external tools (e.g., `mcp::server1::function1()`). 2-part namespaces are reserved for built-ins; 3-part for external/tool integrations.

**Backward-compatible aliases:** legacy flat names (e.g., `from_json`, `to_json`, `uppercase`) remain callable alongside their namespaced equivalents (`json::parse`, `json::stringify`, `str::uppercase`). Scripts may mix both forms. New code should prefer the namespaced form.

**Note:** In Cy, the syntax for calling **Functions**, **Tools**, and **Tasks** is unified. They all appear as function calls, but each behaves differently under the hood as described above.


## The Cy Language

### Core Ideas

- The language draws inspiration from Bash and Python.
  - When in doubt about a feature, assume that we follow what Python does. Document the assumption in the execution plan and suggest an edit in the spec as well.
- Variable references always begin with a `$`, making them visually distinct from text. Examples:
  - `$hello`
  - `${hello}`
- Like in Bash, variable assignment does not require a dollar sign. Both of the following are valid:
  - `x = 1`
  - `$x = 1`
- Cy scripts are compiled into a **Task Execution Plan**—a structured JSON representation of the task steps. This plan is designed to be inspectable and visualizable using graph libraries like GraphViz.
- In the simplest case, the Task Execution Plan is executed by a single Python process. Initially, the compiler and interpreter can reside in the same process.
- A special reserved variable `$input` holds the input to the Directive. You can assign and alias it:
  - `alias = $input`

#### Supported Types

- Numbers (integers and floats)
- Strings
- Booleans
- Lists (`[]`)
- Structs (JSON-style dictionaries or hash tables)
- Nested data structures (lists of structs, structs with lists, etc.)

#### Literal Syntax Examples

- List: `[1, 2]`
- String: `"hello"`
- Number: `1.1`, `2`
- Boolean: `True`, `False`
- Struct: `{"a": 1, "b": True, "c": [1, 2]}`

#### Math Operators

- Addition: `+`
- Subtraction: `-`
- Multiplication: `*`
- Division: `/`

#### Typing

- Cy is dynamically typed, similar to Python.

#### Arguments & Tools

- If multiple arguments are passed to a Cy script, `$input` will be a list (`[]`).
- Tools behave like functions and can take arguments and return values:
  - `x = tool1($f)`
- Functions and tools are provided externally at runtime.
- Users cannot currently define new functions within Cy scripts.
- External data such as Tables (lists of structs), Documents (strings), and other Tasks or Tools can be injected into the runtime.

#### Struct Access

- **Outside interpolation**: Use bracket notation for field access: `$user["name"]`, `$data["key"]`
- **Inside interpolation**: Use dot notation for field access: `${user.name}`, `${data.key}`
- Note: `$h.a` is invalid outside interpolation—dot access must be inside `${...}` to disambiguate from string literals

#### Lists

- Example: `$items = ["apple", "banana", "cherry"]`
- Trailing commas are allowed:
  - `x = [1, 2, ]`

#### Indexed Access

**Lists:**
- **Outside interpolation**: `$data[2]` (direct indexed access)
- **Inside interpolation**: `${data[2]}` (indexed access in interpolation)
- **Chained access**: `${matrix[1][0]}` (only supported inside interpolation)

**Important**: Different syntax for expressions vs interpolation:
  - Expression: `$arr[0]` (valid - direct access)
  - Interpolation: `${arr[0]}` (valid - interpolation access)
  - Invalid: `$arr[0]` inside a string would be treated as `$arr` + literal `[0]`

#### Equality & Control Flow

- Equality checks return booleans:
  - `x = 1 == $b`
- Python-style semantics apply (e.g., `[1, 2] == [1, 2]` is `True`)
- Control structures:

 ```cy
  if ($x) {
      t \= 1
  } elif ($y) {
      t \= 2
  } else {
      t \= 10
  }
```

- Loops:

```cy
  while (x \> y) {
      t \= t \+ 1
      x \= x / 2
  }
```

#### Comments

- Single-line comments start with `#` (Python-style)
- Multiline comments and nested comments are not supported

#### Strings

- Use double quotes (`"`) for single-line strings and triple quotes (`"""`) for multi-line strings.
- Example:

  "Hello\\nworld"

  """ "a"=1

      "b"=2

  """

#### String Interpolation

- Variables can be embedded in strings:
  - "Hello ${world} $thend"
  - Multi-line example:

    $output \= """

    multi

    line string supported

    """


- Use `\` to escape characters:
  - "\\$" → $
  - "\\${" → `${`

#### Output Handling

- `$output` holds the final generated text (last assignment wins).

  $output \= "The final $result"

- Alternatively, use the `return` keyword:

  return $variable\_x

- Use `print()` for intermediate outputs:

  print("Result is $result")

- Variables are global to a Directive; reassigning overwrites previous values.

#### I/O Contract

- **Input (`$input`)** and the **output** of a run are clean JSON — independent of Python or Cy internals. No Python-specific types (datetime, Decimal, custom classes, sets) escape the runtime; the interpreter sanitizes non-JSON values to JSON-safe representations.
- Two interpreter entry points are provided:
  - `interpreter.run(program, input_data)` — returns the output as a **JSON string**, suitable for CLI, cross-language callers, and any consumer that can parse JSON.
  - `interpreter.run_native(program, input_data)` — returns the output as **native Python values** (dict, list, int, str, bool, None). Use this when chaining Cy scripts, where the next script's `$input` needs structured data rather than a string.
- A `str()` native function is available inside Cy for simple stringification.

---

### Variable Grammar

- Allowed: letters, digits, and underscores (e.g., `hello_world`)
- Not allowed: hyphens (e.g., `hello-world`)
- Must start with a letter (uppercase allowed)
- Unicode variable names are not supported

---

### Tool Signature Contract

- Function calls support positional arguments, named arguments, or mixed (positional first, then named). Once a named argument appears, all remaining must be named. The argument adapter normalizes mixed calls to the optimal format for each function type.

  hits \= semantic\_search(db=$alert\_db, query=$alert\_semantic, k=10)

---

### Error Handling

- Errors should be human-readable and include line/column info.
- `$output` must be defined, unless in special modes (e.g., SPM).
- `$input` is read-only:
  - Valid: `$input_copy = $input`
  - Invalid: `$input = "oops!"`
- **Undefined variables are detected at compile time** (not runtime) as part of the default type-checking pass. Typos in variable names fail before any tools are invoked, so scripts cannot silently propagate bad references.
- **Python-style syntax is detected with helpful hints.** Because most Cy users come from Python, the parser specifically recognizes common Python patterns that are invalid in Cy — `if …:` / `elif …:` / `while …:` / `for x in y:` (colon block headers), `//` floor division or C-style comments, missing `$` on variables, etc. — and produces an error message that shows the equivalent Cy syntax.
- Suggested error types:
  - `SyntaxError`, `RuntimeError`, `InterpolationError`, `NameError`
  - `ToolError`, `ToolNotFoundError`, `ToolInvocationError`
  - `NotSupportedYet` for reserved or future keywords
- Example structured error format:

  {

    "type": "SyntaxError",

    "line": 3,

    "col": 5,

    "message": "Unexpected token 'foo'"

  }

---

### String Interpolation (Deep Dive)

String interpolation is essential in Cy because the final output is natural language text for LLM consumption.

**Phase 18 Update**: We are enhancing interpolation to support full expressions inside `${}` while maintaining 100% backward compatibility. This enhancement is customer-driven to reduce boilerplate code.

#### Examples:

$user \= "Alice"

$output \= "Hello, $user\!"             # → Hello, Alice\!

$output \= "Balance: ${amount}"       # → Balance: 42

$output \= "Cost is \\\\$5"             # → Cost is $5

$output \= "User \#${userObj.id}: ${userObj.name}" # → User \#7: Bob

$output \= "Show me \\\\${notAVar}"     # → Show me ${notAVar}

#### Simple vs Complex Interpolation Syntax

**Design Decision: Explicit Syntax Distinction**

Cy intentionally uses two distinct interpolation syntaxes to maintain clear semantics and predictable parsing:

1. **Simple Variables: `$var`**
   - Only for basic variable references
   - Must be simple identifiers (letters, numbers, underscores)
   - Examples: `$name`, `$age`, `$user_id`
   - Cannot include complex expressions

2. **Complex Expressions: `${...}`**
   - For any complex expression or operation
   - List indexed access: `${arr[0]}`, `${matrix[1][0]}`
   - Struct field access: `${user.name}`, `${obj.field.subfield}`
   - Format hints: `${data|csv}`, `${items|xml}`

**Phase 18 Enhancement (In Development):**
The following patterns will be supported in Phase 18:
   - Function calls inside interpolation: `${add(1, 2)}`, `${len($items)}`
   - Arithmetic inside interpolation: `${$count + 1}`, `${$price * 1.1}`
   - Boolean expressions: `${$score >= 90 and 'Pass' or 'Fail'}`
   - Complex expressions: `${add($x, $y) * len($items)}`

**Quote Handling Constraint:**
- `${data['key']}` - Single quotes work in all string types
- `${data["key"]}` - Double quotes only work in triple-quoted strings `"""..."""`
- This is a lexer-level constraint: the lexer ends double-quoted strings at the first unescaped `"`

**Best Practice:** Use single quotes for dictionary keys in interpolation or use triple quotes when double quotes are necessary.

**Important: Mixed syntax is not supported**
```cy
# ❌ INVALID - This will NOT work as indexed access
$arr = ["a", "b", "c"]
$output = "Item: $arr[0]"  # Results in: "Item: - a\n- b\n- c[0]"

# ✅ CORRECT - Use braces for indexed access
$arr = ["a", "b", "c"]
$output = "Item: ${arr[0]}"  # Results in: "Item: a"
```

**Rationale:**
- **Clear Distinction**: Simple vs complex patterns are visually distinct
- **Predictable Parsing**: `$var` always means exactly one variable identifier
- **Explicit Complexity**: Complex expressions require explicit `${...}` syntax
- **Consistent Rules**: All non-trivial operations use braced syntax

#### Interpolation Output Styles

- Set globally in the Python interpreter:
  - `interpreter = Cy(interpolation_mode="markdown")`
- Supports per-expression override:
  - `${expr|xml}` or `${expr|csv}`
- Planned formats:
  - Markdown (default)
  - Comma-separated values (CSV)
  - XML
  - JSON and YAML (future support)
- Supports nested data structures.

---

### Reserved Keywords

- `$input`, `$output`, `return`
- Control keywords: `if`, `for`, `null`, `True`, `False`, `not`
- SQL keywords reserved for future use: `SELECT`, `FROM`, `WHERE`, etc.
- Pipe symbol `|` reserved for future stream/filter syntax

---

### Future Additions

- Visual builder (e.g., VSCode-style editor)
- Alternative interpreters for executing Task Execution Plans
- SQL-like syntax for manipulating structured data
- Future versions may support block-local variables to avoid name collisions in large directives
- Allow (optionally) wrapping a directive inside a named block like main { ... } to enable richer future constructs like local variable scoping or lambdas
- Introduce $debug(...) as a semantic alternative to print that’s omitted in production mode.

---

### Versioning

- Version 3 removes the version pragma for simplicity
- Version compatibility is handled at the interpreter level
- Future versions may reintroduce versioning if needed, potentially using Python-style metadata comments like `# cy-version: 3.0`

---

## Example Programs in Cy

None scope means defaults. Don’t take it as if we assume that there is nothing happening in the Python code side of things.

### 1\. Variable assignment \+ interpolation

#### Injected Scope in Python

None

#### Example Program

$name \= "Alice" $output \= "Hi $name\!"

#### Output

Hi Alice\!

### 2\. List printing (default markdown printer)

#### Injected Scope in Python

interpreter \= Cy(interpolation\_mode="markdown")   \# default bullets

#### Example Program

$fruits \= \["apple", "banana", "cherry",\] $output \= "Fruits:\\n${fruits}"

#### Output

Fruits: \- apple \- banana \- cherry

### 3\. Struct access

#### Injected Scope in Python

None

#### Example Program

$user \= { "id": 7, "name": "Bob" } $output \= "User \#${user.id}: ${user.name}"

#### Output

User \#7: Bob

### 4\. Tool call with positional args

#### Injected Scope in Python

tools \= { "add": lambda a, b: a \+ b }

#### Example Program

$sum \= add(3, 4\) $output \= "3 \+ 4 \= ${sum}"

#### Output

3 \+ 4 \= 7

### 5\.  Escaping ${ and $

#### Injected Scope in Python

None

#### Example Program

$output \= "Show me \\${notAVar} and \\$100"

#### Output

Show me ${notAVar} and $100

### 6\.  Multiline string with interpolation

#### Injected Scope in Python

None

#### Example Program

$name \= "Eve" $output \= """ Hello $name,

This is a multiline string. """

#### Output

Hello Eve,

This is a multiline string.

### 7\.  XML printer hint (per‑expression override)

#### Injected Scope in Python

interpreter \= Cy(interpolation\_mode="markdown")  \# global default

#### Example Program

$items \= \["a", "b"\] $output \= "\<items\>${items|xml}\</items\>"

#### Output

\<items\> \<item\>a\</item\> \<item\>b\</item\> \</items\>

### 8\.  List of structs example with a CSV override

#### Injected Scope in Python

interpreter \= Cy(interpolation\_mode="markdown")  \# global default

#### Example Program

# List of structs example with a CSV override $records \= \[ { "id": 1, "name": "alice", "score": 92 }, { "id": 2, "name": "bob",   "score": 87 }, \]

$output \= """ Audit summary \------------- Raw table (CSV):

${records|csv} """

#### Output

Audit summary \------------- Raw table (CSV):

id,name,score 1,alice,92 2,bob,87

### 9\. With external Tools/Directives and Variables

#### Injected Scope in Python

\# Injected scope for Cy tools \= { "alert\_to\_text": lambda alert: f"{alert.get('title','')}: {alert.get('description','')}", "semantic\_search": lambda db, query, k=10: {"semantic": \[f"similar alert {i+1}" for i in range(k)\]}, }

variables \= { "alert\_db": "alerts\_vector\_db"   \# becomes $alert\_db in Cy }

interpreter \= Cy(tools=tools, variables=variables, interpolation\_mode="markdown") output \= interpreter.run(cy\_program, input\_data)

#### Example Program

$alert = $input
$alert_semantic = alert_to_text($alert)  # Takes an alert and makes it a string that can be easily used for semantic similarity matching in a vector database. The return type is "String"
$similar_alert_corpus = semantic_search($alert_db, $alert_semantic).semantic  # A list of Strings that represent the details of each of the most similar alerts we found.

$output \= """ Here is a new alert: $alert\_semantic

Here is a list of alerts that are similar: $similar\_alert\_corpus

Let's use the similar alerts to identify the disposition of the new alert. Be conservative, if the results are mixed, it's ok to say Unknown.

Return a JSON. { "disposition": \<add response here\> "explanation": \<add your reasoning here\> } """

### 10. Enhanced Expression Interpolation (Phase 18 - NEW)

#### Injected Scope in Python

```python
tools = {
    "add": lambda a, b: a + b,
    "len": lambda lst: len(lst) if isinstance(lst, list) else 0,
}
variables = {
    "items": ["apple", "banana", "cherry"],
    "prices": [1.99, 0.99, 2.50],
    "tax_rate": 0.08,
}
interpreter = Cy(tools=tools, variables=variables)
```

#### Example Program

```cy
# Phase 18: Full expressions in interpolation
$base_price = 100
$discount = 15

# Function calls in interpolation
$summary = "Cart has ${len($items)} items"

# Arithmetic in interpolation
$total_msg = "Subtotal: ${$base_price - $discount}, With tax: ${($base_price - $discount) * (1 + $tax_rate)}"

# Boolean expressions in interpolation
$score = 95
$status = "Grade: ${$score >= 90 and 'A' or $score >= 80 and 'B' or 'C'}"

# Complex nested expressions
$analysis = """
Items: ${len($items)}
Total Price: ${sum($prices)}
Average Price: ${sum($prices) / len($items)}
With Discount: ${sum($prices) * 0.9}
Status: ${sum($prices) > 5.0 and 'Premium Order' or 'Standard Order'}
"""

$output = $analysis
```

#### Output

```
Items: 3
Total Price: 5.48
Average Price: 1.83
With Discount: 4.93
Status: Premium Order
```

### 11. Conditional logic and loops (factorial calculator)

#### Injected Scope in Python

variables \= { "n": 5 }
interpreter \= Cy(variables=variables)

#### Example Program

```cy
x \= $n
fact \= 1

if ($x \> 0\) {
    while ($x \> 1\) {
        $fact \= $fact \* $x
        $x \= $x \- 1
    }
    $output \= "Factorial of $n is $fact"
} else {
    $output \= "$n is not a positive number"
}
```

#### Output

Factorial of 5 is 120

## Implementation Suggestions

| Area | Decision | Rationale / Implication | Example |
| :---- | :---- | :---- | :---- |
| Parser | **Lark (LALR)** | Modern, concise EBNF grammar; automatic AST \+ Transformer; easy to extend. | `parser = Lark(grammar, parser="lalr", transformer=Interpreter(tools))` |
| Identifier style | **Variables start with `$` (`$var`, `${var}`)** | Clear visual cue; unambiguous in strings; familiar convention. Must support escaping (`\$var`). | `$examples = vector_lookup("foo")` |
| Interpreter core | Transformer with: • \`vars\` dict for state • \`tools\` registry • \`interpolate()\` for \`$var\` / \`${var}\` • \`render\_directive()\` for output format | Simple, sandboxed, testable runtime. | — |
| Tool registry | **`{name: callable}` dict passed at init** | Decouples DSL from implementation; easy mocking. | `tools = {"vector_lookup": lambda q: [...]}` |
| Variables registry | **`{name: string}` dict passed at init** | Decouples DSL from implementation; easy mocking. | `variables = {"doc1": “hello world”}` |
| Tool Calling (Runtime) | **`Synchronous`** | Makes things easy for now. Tools are called one after the other as encountered. | `-` |
| AST pretty‑printer For Debugging | **`-`** | \- | `-` |
| Advice: Keep a separate reserved‑word table in your lexer so it fails early when someone tries $if \= … or $select \= …. | **`-`** | \- | `-` |

## Cy Repository Design And Plan

* Cy language lives in its own repository that we are building here.
* The goal is to use the Cy languages in other projects as a package.
* We should have unit tests for all 9 examples we described in the main Language Design Document.
* We first want to build our compiler/interpreter and make sure that all our examples work.
* It would be helpful to expose the formal grammar in an appendix once stabilized.
* Next, for development, we want to build a simple `streamlit` UI that allows us to run Cy Programs with example tools and variables
  * The tools and variables are defined inside the main `streamlit` app and that’s ok for now
  * The UI is not something we publish, it’s just for the local development experience
  * The external tools and variables should be simple ones we can code inside the `stramlit` main app (some basic python functions as tools and strings as variables)
  * The `streamlit` app at any given time has a single Cy program that it has loaded.
  * From the UI we should be able to load a different script from a particular local folder (say the `examples` folder may contain few different \*.cy scripts)
    * This should be a drop down menu in our UI to let us choose a different script
  * The main text box allows us to type in the script (we will have a default one that loads up)
    * The main text box shows the script and allows us to edit it
    * Support syntax highlighting using `streamlit-ace`
  * There is a `Run` button that executes the script and prints the $output on screen
  * There is a `Save` button to save changes to the current script
  * There is a `New` button to start a new script from scratch
  * There is a box at the bottom for the result of the `$output` variable (only to be populated after we click on Run)
  * There is a box on the side that accepts the `$input`
* Create detailed PLAN.md with all the main steps for this repository and use it throughput for the development progress. We first need to agree on the PLAN before we start writing code.
  * Start with building the repo and the tooling we need
  * Next with the language and the unit tests for it
  * When all tests pass we process with the `streamlit` UI
  * I will then do manual testing and come up with any improvements
  * Create also a detailed section on future work using all the future work items we have listed.
