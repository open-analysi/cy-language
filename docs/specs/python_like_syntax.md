# Python-Like Syntax Specification

+++
version = "1.0"
date = "2026-04-19"
status = "active"

[[changelog]]
version = "1.0"
date = "2026-04-19"
summary = "Reset spec versioning to flat structure per spec-template. Content carried forward from legacy v4."
+++

## Overview
This specification defines changes to make the Cy language more Python-like and familiar to Python developers. These changes improve language consistency and reduce cognitive load for users coming from Python backgrounds.

## Major Changes from Version 2.1

### 1. Comment Syntax Change
**Old Syntax (C-like):**
```cy
// This is a comment
$name = "Alice"  // Inline comment
```

**New Syntax (Python-like):**
```cy
# This is a comment
$name = "Alice"  # Inline comment
```

**Rationale:** Python developers expect `#` for comments. This change makes Cy feel more natural and Pythonic.

### 2. Removal of Version Pragma
**Old Syntax:**
```cy
#!cy 0.1
$name = "Alice"
$output = "Hello, ${name}"
```

**New Syntax:**
```cy
$name = "Alice"
$output = "Hello, ${name}"
```

**Rationale:**
- Simplifies the language by removing a non-essential feature
- Reduces cognitive overhead for new users
- Version compatibility can be handled at the interpreter level if needed in the future
- Follows the principle of keeping things simple until complexity is truly needed

## Implementation Impact

### Grammar Changes
1. Update `COMMENT` token from `/\/\/[^\n]*/` to `/#[^\n]*/`
2. Remove `version_pragma` rule from grammar
3. Remove `VERSION_NUMBER` token definition
4. Update `start` rule from `[version_pragma] statement*` to `statement*`
5. Change all grammar comments from `//` to `#` for consistency

### Parser Changes
- Remove version pragma parsing logic
- Update comment tokenization

### Interpreter Changes
- Remove version checking logic
- Simplify interpreter initialization

### Test Updates
- Update all test files to use `#` instead of `//` for comments
- Remove version pragma from test cases
- Update comment-related test cases

### Example Updates
- Update all `.cy` example files to use new comment syntax
- Remove version pragma from all examples

## Backward Compatibility
This is a **breaking change** from Version 2.1. Programs written with:
- `//` comments will need to be updated to use `#`
- Version pragmas will need to be removed

A migration tool could be provided to automatically convert old syntax to new syntax.

## Benefits
1. **Improved Python Familiarity**: Python developers will immediately recognize `#` as comments
2. **Simplified Language**: Removing pragma reduces complexity
3. **Cleaner Syntax**: Programs start directly with logic, not metadata
4. **Better Integration**: More natural when embedded in Python projects

## Examples

### Before (Version 2.1)
```cy
#!cy 0.1
// Customer order processing
$base_price = 1000.00
$customer_tier = "premium"  // Customer tier level

// Apply business rules
$discount = calculate_discount($base_price, tier=$customer_tier)
$output = "Discount: ${discount}"
```

### After (Version 3)
```cy
# Customer order processing
$base_price = 1000.00
$customer_tier = "premium"  # Customer tier level

# Apply business rules
$discount = calculate_discount($base_price, tier=$customer_tier)
$output = "Discount: ${discount}"
```

## Future Considerations
If version compatibility becomes necessary in the future, consider:
1. Python-style metadata comments: `# cy-version: 3.0`
2. Runtime version detection based on syntax features used
3. Interpreter-level version configuration rather than in-file pragmas
