"""Predefined example programs for the Cy language editor.

These serve two purposes:
1. Quick-access demos in the editor sidebar (featured / starter examples).
2. Stable fixtures for unit tests.

Example source code is kept as module-level constants at the bottom of this
file so that the public API at the top stays readable.
"""

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# Display name -> example key (ordered for the sidebar selector)
EXAMPLES: dict[str, str] = {
    "Hello World": "basic",
    "List Comprehensions": "phase37_list_comprehension",
    "Namespaced Functions": "phase35_namespaces",
    "Safe Navigation": "phase28_safe_navigation",
    "Null Coalescing (??)": "phase28_null_coalesce",
    "Chaining Fallbacks": "phase28_chaining",
    "Security Workflow": "phase28_workflow",
}


def get_test_examples() -> dict[str, str]:
    """Return all predefined test examples.

    Keys are short identifiers (e.g. ``"basic"``); values are the full
    program source code.
    """
    return {
        "basic": _BASIC,
        "list": _LIST,
        "struct": _STRUCT,
        "phase28_safe_navigation": _SAFE_NAVIGATION,
        "phase28_null_coalesce": _NULL_COALESCE,
        "phase28_chaining": _CHAINING,
        "phase28_workflow": _WORKFLOW,
        "phase37_list_comprehension": _LIST_COMPREHENSION,
        "phase35_namespaces": _NAMESPACES,
    }


# ---------------------------------------------------------------------------
# Example source code
# ---------------------------------------------------------------------------

_BASIC = """\
# Basic example
name = "Alice"
result = "Hello, $name!"
return result
"""

_LIST = """\
# List example
fruits = ["apple", "banana", "cherry"]
result = "Fruits: ${fruits}"
return result
"""

_STRUCT = """\
# Struct example
user = {"id": 123, "name": "Bob"}
result = "User #${user.id}: ${user.name}"
return result
"""

_SAFE_NAVIGATION = """\
# Safe Navigation
# Field access returns null for missing keys (no exceptions!)
data = {"user": {"name": "Alice"}}

# Safe access - returns null if field doesn't exist
city = data.user.address.city  # Returns null, no error!
log("City: ${city}")  # Logs: "City: null"

# Use 'or' operator for fallback (returns actual values now)
city_with_fallback = data.user.address.city or "Unknown"
log("City with 'or': ${city_with_fallback}")  # Logs: "City with 'or': Unknown"

return {"city": city, "with_fallback": city_with_fallback}
"""

_NULL_COALESCE = """\
# Null-Coalescing Operator (??)
# The ?? operator only replaces null values, preserving falsy values like 0, [], {}

data = {"count": 0, "items": [], "config": {}}

# Problem with 'or': replaces ALL falsy values
count_with_or = data.count or 10
items_with_or = data.items or ["default"]
config_with_or = data.config or {"default": True}

# Solution with '??': only replaces null
count_with_coalesce = data.count ?? 10  # Keeps 0!
items_with_coalesce = data.items ?? ["default"]  # Keeps []!
config_with_coalesce = data.config ?? {"default": True}  # Keeps {}!

# Safe navigation with ?? for missing fields
user_name = data.user.name ?? "Guest"  # "Guest" (user doesn't exist)
actual_count = data.count ?? 99  # 0 (count exists and is 0)

return {
    "or_results": {
        "count": count_with_or,      # 10 (replaced 0!)
        "items": items_with_or,      # ["default"] (replaced []!)
        "config": config_with_or     # {"default": True} (replaced {}!)
    },
    "coalesce_results": {
        "count": count_with_coalesce,    # 0 (preserved!)
        "items": items_with_coalesce,    # [] (preserved!)
        "config": config_with_coalesce   # {} (preserved!)
    },
    "safe_nav": {
        "user_name": user_name,          # "Guest"
        "actual_count": actual_count      # 0
    }
}
"""

_CHAINING = """\
# Chaining ?? for Multiple Fallbacks
# Chain multiple ?? operators for progressive fallbacks

config = {}

# Try multiple sources in order
server = config.primary_server ?? config.backup_server ?? config.default_server ?? "localhost"
port = config.custom_port ?? config.standard_port ?? 8080
timeout = config.timeout ?? 30

log("Server: ${server}")  # "localhost"
log("Port: ${port}")      # 8080
log("Timeout: ${timeout}") # 30

# Complex nested example with input
# Simulate enrichment data that might be incomplete
enrichments = {
    "geo": {
        "country": "US"
        # city is missing
    }
    # network is missing entirely
}

# Safe navigation with chained fallbacks
ip = enrichments.network.ip ?? enrichments.backup.ip ?? "0.0.0.0"
country = enrichments.geo.country ?? enrichments.geo.region ?? "Unknown"
city = enrichments.geo.city ?? enrichments.geo.state ?? enrichments.geo.country ?? "Unknown"

return {
    "connection": {
        "server": server,
        "port": port,
        "timeout": timeout
    },
    "location": {
        "ip": ip,           # "0.0.0.0" (all sources were null)
        "country": country, # "US" (first one had value)
        "city": city        # "US" (fell back to country)
    }
}
"""

_WORKFLOW = """\
# Practical Workflow Example
# Process security alert with potentially incomplete enrichment data

# Simulate an alert with partial enrichment
alert = {
    "id": "ALT-2024-001",
    "severity": null,  # Missing severity!
    "source_ip": "192.168.1.100",
    "enrichments": {
        "reputation": {
            "score": 0  # Score is 0 (not null)
            # verdict is missing
        }
        # geo enrichment is missing entirely
    }
}

# Safe field access with appropriate defaults using ??
alert_id = alert.id
severity = alert.severity ?? "medium"  # Default to medium if missing
source_ip = alert.source_ip

# Reputation handling - be careful with 0 scores!
rep_score = alert.enrichments.reputation.score ?? -1  # Keeps 0 (it's not null)
rep_verdict = alert.enrichments.reputation.verdict ?? "unknown"

# Geographic data with safe navigation
country = alert.enrichments.geo.country ?? "Unknown"
city = alert.enrichments.geo.city ?? "Unknown"

# Risk calculation considering nulls and zeros
risk_multiplier = if (rep_score == 0) {
    1.5  # Zero reputation is suspicious
} elif (rep_score > 0) {
    1.0  # Positive reputation
} else {
    2.0  # Unknown reputation (-1)
}

# Build analysis result
return {
    "alert_id": alert_id,
    "severity": severity,
    "source": {
        "ip": source_ip,
        "country": country,
        "city": city
    },
    "reputation": {
        "score": rep_score,
        "verdict": rep_verdict,
        "risk_multiplier": risk_multiplier
    },
    "analysis": {
        "has_reputation": rep_score >= 0,
        "has_geo": country != "Unknown",
        "needs_enrichment": (country == "Unknown") or (rep_verdict == "unknown")
    }
}
"""

_LIST_COMPREHENSION = """\
# List Comprehensions
# Compact syntax for transforming and filtering lists
# Replaces the common for-loop + accumulator pattern

# ========== Basic: Extract a field ==========
users = [
    {"id": "U001", "name": "Alice", "role": "admin"},
    {"id": "U002", "name": "Bob", "role": "user"},
    {"id": "U003", "name": "Charlie", "role": "admin"}
]

names = [u.name for(u in users)]
log("Names: ${names}")  # ["Alice", "Bob", "Charlie"]

ids = [u.id for(u in users)]
log("IDs: ${ids}")  # ["U001", "U002", "U003"]

# ========== With Filter ==========
admins = [u.name for(u in users) if(u.role == "admin")]
log("Admins: ${admins}")  # ["Alice", "Charlie"]

# ========== Transform elements ==========
nums = [1, 2, 3, 4, 5]
doubled = [n * 2 for(n in nums)]
log("Doubled: ${doubled}")  # [2, 4, 6, 8, 10]

evens = [n for(n in nums) if(n % 2 == 0)]
log("Evens: ${evens}")  # [2, 4]

# ========== String interpolation in element expression ==========
greetings = ["Hello ${u.name}!" for(u in users)]
log("Greetings: ${greetings}")

# ========== Tool calls in element expression ==========
words = ["hello", "world"]
upper_words = [str::uppercase(w) for(w in words)]
log("Upper: ${upper_words}")  # ["HELLO", "WORLD"]

# ========== Nested field access ==========
records = [
    {"profile": {"email": "alice@example.com"}},
    {"profile": {"email": "bob@example.com"}}
]
emails = [r.profile.email for(r in records)]
log("Emails: ${emails}")

# ========== Chained with other operations ==========
email_count = len([u.name for(u in users) if(u.role == "admin")])
log("Admin count: ${email_count}")  # 2

return {
    "names": names,
    "admins": admins,
    "doubled": doubled,
    "evens": evens,
    "greetings": greetings,
    "upper_words": upper_words,
    "emails": emails,
    "admin_count": email_count
}
"""

_NAMESPACES = """\
# 2-Part Namespaces for Native Functions
# Functions are now organized into logical namespaces for better clarity

# ========== JSON Functions (json::) ==========
data = {"name": "Alice", "scores": [95, 87, 92]}
json_text = json::stringify(data, 2)  # Pretty-print with indent=2
log("JSON output:")
log(json_text)

parsed = json::parse('{"city": "NYC", "temp": 72}')
log("Parsed city: ${parsed.city}")

# ========== String Functions (str::) ==========
message = "  Hello World  "
trimmed = str::trim(message)
upper = str::uppercase(trimmed)
lower = str::lowercase(trimmed)
log("Trimmed: '${trimmed}', Upper: '${upper}', Lower: '${lower}'")

# Split and join
words = str::split("apple,banana,cherry", ",")
rejoined = str::join(words, " | ")
log("Split and rejoined: ${rejoined}")

# String checks
filename = "report.pdf"
is_pdf = str::endswith(filename, ".pdf")
is_img = str::startswith(filename, "img_")
log("Is PDF: ${is_pdf}, Is image: ${is_img}")

# ========== List Functions (list::) ==========
numbers = [5, 2, 8, 1, 9]
sorted_nums = list::sort(numbers)
reversed_nums = list::reverse(numbers)
first_three = list::take(numbers, 3)
log("Sorted: ${sorted_nums}, Reversed: ${reversed_nums}, First 3: ${first_three}")

# Generate a range
sequence = list::range(1, 6)  # [1, 2, 3, 4, 5]
log("Range 1-5: ${sequence}")

# ========== Dict Functions (dict::) ==========
config = {"host": "localhost", "port": 8080, "debug": True}
all_keys = dict::keys(config)
all_values = dict::values(config)
log("Keys: ${all_keys}, Values: ${all_values}")

# ========== Math Functions (math::) ==========
negative = -42
positive = math::abs(negative)
pi_approx = 3.14159
rounded = math::round(pi_approx, 2)
log("Absolute: ${positive}, Rounded: ${rounded}")

# ========== URL Functions (url::) ==========
query = "hello world & more"
encoded = url::encode(query)
decoded = url::decode(encoded)
log("Encoded: ${encoded}, Decoded: ${decoded}")

# ========== IP Functions (ip::) ==========
ipv4 = "192.168.1.1"
ipv6 = "::1"
invalid = "not-an-ip"

log("Is ${ipv4} valid IPv4? ${ip::is_v4(ipv4)}")
log("Is ${ipv6} valid IPv6? ${ip::is_v6(ipv6)}")
log("Is ${invalid} a valid IP? ${ip::is_valid(invalid)}")

# ========== Time Functions (time::) ==========
now_time = time::now()
future = time::add_duration(now_time, "2h30m")
log("Now: ${now_time}")
log("In 2h30m: ${future}")

# ========== Type Conversion (type::) ==========
num_str = "42"
converted = type::int(num_str)
back_to_str = type::str(converted)
log("String '${num_str}' -> int ${converted} -> string '${back_to_str}'")

# ========== Regex Functions (regex::) ==========
text = "Error code: E-1234 on line 56"
has_error = regex::match("E-\\\\d+", text)
error_code = regex::extract("E-(\\\\d+)", text)
log("Has error pattern: ${has_error}, Extracted code: ${error_code}")

return {
    "json_demo": parsed,
    "string_demo": {"upper": upper, "words": words},
    "list_demo": {"sorted": sorted_nums, "range": sequence},
    "math_demo": {"abs": positive, "rounded": rounded},
    "ip_demo": {"ipv4_valid": ip::is_v4(ipv4), "ipv6_valid": ip::is_v6(ipv6)}
}
"""
