---
name: code-style
description: Code style rules for readable, maintainable implementation. Load this skill always when writing or editing code, and whenever the user asks about code style, refactoring shape, function/file size, object-oriented structure, helper ordering, comments, or docstrings. For Frappe-specific work, prefer frappe-app-dev.
---

# Code Style Rules

- Keep functions small. Split when a function has multiple jobs or needs sections to be readable.
- Keep files under 300 lines when practical. Split by responsibility, not by arbitrary layer.
- Prefer object-oriented code over scattered functions.
- Put higher-order/public functions near the top of the file; keep low-level utilities at the bottom.
- Prefix file-local functions (not meant to be imported elsewhere) with `__`.
- Do not use nested for-loops; refactor (e.g. early continue, helper function, flatten data first) to avoid deep nesting.
- Write terse, simple English comments. Explain why something is surprising; do not narrate obvious code. Add a short example or use case in the comment when it clarifies non-obvious usage.
- Do not add abstractions until there are repeated concrete uses.
- Do not duplicate logic across files — extract shared code into a common helper once it repeats.
- Import only what's used; never `import *`.
- Leave a blank line between import blocks (stdlib / third-party / app-local) and before each function or class definition.
- Add blank lines between logical sections within a function body for readability.
- Use descriptive names — avoid single-letter names like `i`, `j` outside tight loops; prefer `invoice_index`, `customer_count`, etc.
- Strip unused variables/functions, and debug statements (`print`, `console.log`, `breakpoint`) before finishing a change.

## Docstrings — mandatory on every function

Every function, method, and class — not only whitelisted API endpoints — must
have a docstring. This is a hard rule, not a style preference. Whitelisted
endpoints follow the stricter, longer format defined in
`frappe-app-dev/references/api.md`; every other function follows the format
below.

Minimum content:

- 2–3 line explanation of what it does and, if non-obvious, why it exists.
  Do not just restate the function signature in words.
- Every parameter: name, type, required/optional.
- Return value and its type (or `None`).

No exceptions for "small" or "obvious" functions — a one-line helper still
gets at least a one-line docstring stating what it returns.

**Python:**

````python
def format_customer_display_name(customer_name: str, customer_code: str) -> str:
    """
    Build the display string shown in dropdowns and print formats.

    Parameters:
        customer_name (str, required): The customer's registered name.
        customer_code (str, required): The internal customer code.

    Returns:
        str: "<customer_code> - <customer_name>"
    """
    return f"{customer_code} - {customer_name}"
````

**JavaScript:**

````javascript
/**
 * Build the display string shown in dropdowns and print formats.
 *
 * @param {string} customerName - The customer's registered name.
 * @param {string} customerCode - The internal customer code.
 * @returns {string} "<customerCode> - <customerName>"
 */
function formatCustomerDisplayName(customerName, customerCode) {
    return `${customerCode} - ${customerName}`;
}
````

**Note on this skill repo's own reference docs:** code snippets inside
`frappe-app-dev/references/*.md` are illustrative and may omit docstrings for
readability of the reference material itself. This is a documentation
convention only — it is never a license to skip docstrings in actual app
code. When in doubt, the rule above governs; the reference docs' brevity does
not.

For file-level copyright/license headers (separate from function docstrings),
see `frappe-app-dev/references/licensing.md`.

For Frappe-specific work, prefer `frappe-app-dev`.