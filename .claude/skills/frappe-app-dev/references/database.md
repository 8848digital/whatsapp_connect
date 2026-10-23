# Database & ORM

## Reading data

```python
# Get single document
doc = frappe.get_doc("Expense", "EXP-0001")

# Get single value
amount = frappe.db.get_value("Expense", "EXP-0001", "amount")

# Get multiple fields
name, amount = frappe.db.get_value("Expense", "EXP-0001", ["name", "amount"])

# Get all matching records
expenses = frappe.db.get_all("Expense",
    filters={"status": "Draft"},
    fields=["name", "title", "amount", "link_field.field"],
    order_by="creation desc",
    limit=20
)

# Get list (same as get_all but respects permissions)
expenses = frappe.db.get_list("Expense", filters={"status": "Draft"}, fields=["*"])

# Count
count = frappe.db.count("Expense", {"status": "Draft"})

# Check existence
exists = frappe.db.exists("Expense", "EXP-0001")
exists = frappe.db.exists("Expense", {"title": "Lunch", "status": "Draft"})
```

## `get_all` vs `get_list`

- `frappe.db.get_all` — ignores permissions, returns all matching records
- `frappe.db.get_list` — respects user permissions, applies filters based on role

Use `get_all` for server-side logic. Use `get_list` in user-facing APIs.

## `frappe.get_doc` vs value-only fetches

`frappe.get_doc` loads the full document — controller instance, child tables, and triggers document-level permission checks. Only use it when you actually need the document object (to call a method, mutate and `.save()`, or work with child tables).

If you only need one or more field values and don't need to mutate or call methods on the document, use the lighter read:

```python
# BAD — loads the whole document just to read two fields
doc = frappe.get_doc("Expense", "EXP-0001")
amount, status = doc.amount, doc.status

# GOOD
amount, status = frappe.db.get_value("Expense", "EXP-0001", ["amount", "status"])
```

For multiple records, use `get_all`/`get_list` rather than loading each with `get_doc` in a loop (see N+1 note below).

## Writing data

```python
# Create
doc = frappe.get_doc({"doctype": "Expense", "title": "Lunch", "amount": 50})
doc.insert()

# Update via doc
doc = frappe.get_doc("Expense", "EXP-0001")
doc.amount = 75
doc.save()

# Quick update (single field, skips controller hooks)
# Use for derived/cached fields, counters, timestamps — NOT for fields with validation logic or status transitions
frappe.db.set_value("Expense", "EXP-0001", "amount", 75)

# Bulk update
frappe.db.set_value("Expense", {"status": "Draft"}, "status", "Cancelled")
```

## Filters syntax

```python
# Dict style (simple equality)
filters = {"status": "Draft", "amount": 100}

# List style (operators)
filters = [
    ["status", "=", "Draft"],
    ["amount", ">", 50],
    ["title", "like", "%lunch%"],
    ["creation", "between", ["2024-01-01", "2024-12-31"]]
]

# Supported operators: =, !=, >, <, >=, <=, like, not like, in, not in, between, is (for NULL)
```

## `frappe.qb.get_query` (preferred for complex queries)

Use instead of `get_all` when you need: joins via linked/child fields, aggregations, OR conditions, subqueries, or record locking. Docs: https://docs.frappe.io/framework/get_query

```python
# Basic usage
query = frappe.qb.get_query("User", fields=["name", "email"], filters={"enabled": 1})
users = query.run(as_dict=True)

# Linked document fields (auto-joins via dot notation)
query = frappe.qb.get_query("Sales Order",
    fields=["name", "customer.customer_name as customer_name"],
    filters={"customer.territory": "North America"}
)

# Child table fields
query = frappe.qb.get_query("Sales Order",
    fields=["name", {"items": ["item_code", "qty", "rate"]}],
    filters={"items.item_code": "Item A"},
    distinct=True
)

# Aggregations
query = frappe.qb.get_query("Expense",
    fields=["category", {"SUM": "amount", "as": "total"}],
    group_by="category"
)

# OR conditions
query = frappe.qb.get_query("User", filters=[
    ["first_name", "=", "Admin"],
    "or",
    ["first_name", "=", "Guest"],
])

# Pagination
query = frappe.qb.get_query("User", fields=["name"], limit=20, offset=40)

# Permission-aware (default is ignore_permissions=True)
query = frappe.qb.get_query("Expense", ignore_permissions=False)

# Record locking
query = frappe.qb.get_query("Stock Entry", filters={"name": "SE-001"}, for_update=True)

# Large datasets — iterate without loading all into memory
with frappe.db.unbuffered_cursor():
    for row in query.run(as_iterator=True, as_dict=True):
        process(row)
```

### When to use what

| Need | Use |
|------|-----|
| Simple CRUD, single doc | `frappe.get_doc`, `frappe.db.get_value`, `frappe.db.set_value` |
| List with simple filters | `frappe.db.get_all` / `frappe.db.get_list` |
| Joins, aggregations, OR logic, child table queries | `frappe.qb.get_query` |
| Composable query — pass query object to other functions to add clauses | `frappe.qb.get_query` |

## Transactions

Frappe manages transactions automatically. You almost never need `frappe.db.commit()` or `frappe.db.rollback()`.

- **POST/PUT web requests**: auto-commit after successful completion. GET requests do NOT commit.
- **Background/scheduled jobs**: auto-commit after successful completion.
- **Patches**: auto-commit after successful `execute()`.
- **Uncaught exceptions**: auto-rollback in all contexts (web requests, background jobs, patches).

`frappe.db.commit()` is only needed in rare cases like flushing writes mid-script so a subsequent `frappe.enqueue` call can read them.

```python
# Use savepoints for partial rollback within a transaction
frappe.db.savepoint("before_risky_op")
try:
    ...
except Exception:
    frappe.db.rollback(save_point="before_risky_op")
```

## PyPika query builder (`frappe.qb`)

You may encounter `frappe.qb.DocType("...")` in existing codebases — this is the lower-level PyPika builder. Prefer `frappe.qb.get_query` (documented above) for new code, but recognize and maintain this style when editing existing code:

```python
Expense = frappe.qb.DocType("Expense")
query = (
    frappe.qb.from_(Expense)
    .select(Expense.name, Expense.amount)
    .where(Expense.status == "Draft")
    .orderby(Expense.creation, order=frappe.qb.desc)
    .limit(20)
)
results = query.run(as_dict=True)
```

## Raw SQL (`frappe.db.sql`)

Use `frappe.db.sql` only for queries `frappe.qb` cannot express (CTEs, window functions, complex unions, etc.) — see Anti-patterns below.

- **Never call functions inline inside the query string.** Compute the value first, store it in a variable, then pass it as a parameter. This applies whether the "function" is a Python call being interpolated or a SQL function whose result should be precomputed in Python.
```python
  # BAD — computed inline, and string-built (SQL injection risk, unreadable)
  frappe.db.sql(f"SELECT * FROM `tabExpense` WHERE status = '{get_current_status()}'")

  # GOOD — compute first, pass as parameter
  current_status = get_current_status()
  frappe.db.sql("SELECT * FROM `tabExpense` WHERE status = %s", (current_status,))
```
  Always use `%s` placeholders with a parameter tuple/dict — never f-strings or `.format()`/`%` string interpolation to build a query. This is a correctness and security rule, not just style.
- **Format multi-line queries with clear indentation** — one clause per line, aligned, so the query is scannable:
```python
  frappe.db.sql("""
      SELECT
          name, amount, status
      FROM
          `tabExpense`
      WHERE
          status = %s
          AND amount > %s
      ORDER BY
          creation DESC
  """, (status, min_amount))
```
- **Move large/complex raw SQL queries into their own file** (e.g. a `queries.py` alongside the module, or a `.sql` file loaded and formatted) rather than inlining a long multi-line string in the middle of business logic. Keep the calling function focused on orchestration, not query text.

## Anti-patterns

- **Don't use raw SQL when `frappe.qb` works.** Prefer the query builder for UPDATE/INSERT. Use `frappe.db.sql` only for queries `frappe.qb` cannot express (CTEs, etc.).
```python
  # BAD
  frappe.db.sql("UPDATE `tabExpense` SET `amount` = `amount` + 1 WHERE name = %s", (name,))
  # GOOD
  Expense = frappe.qb.DocType("Expense")
  frappe.qb.update(Expense).set(Expense.amount, Expense.amount + 1).where(Expense.name == name).run()
```
- **Don't make multiple queries when one will do.** Use OR filters via `frappe.qb.get_query` instead of chaining `frappe.db.get_value(...) or frappe.db.get_value(...)`.
- **Don't run any data-fetching call inside a for-loop** — `frappe.db.sql`, `frappe.db.get_value`, `frappe.db.get_all`, `frappe.db.get_list`, or `frappe.get_doc`. Each iteration is a separate DB round trip (N+1). Batch-fetch before the loop and look up from an in-memory map instead.
```python
  # BAD — N+1
  for exp in expenses:
      exp.category_label = frappe.db.get_value("Expense Category", exp.category, "label")
  # GOOD
  cat_ids = {e.category for e in expenses if e.category}
  cat_map = {c.name: c.label for c in frappe.get_all("Expense Category", filters={"name": ["in", list(cat_ids)]}, fields=["name", "label"])}
  for exp in expenses:
      exp.category_label = cat_map.get(exp.category)
```

### SOP: DB calls inside loops (read or write, single or nested)

This is the single most common performance defect found in review — see the
[quality-code-review](../../quality-code-review/SKILL.md) §3 checklist entry
and the [`db_loop_scan` weekly org-wide scanner](https://github.com/8848digital/org-scans/tree/main/checks/db_loop_scan)
(in the separate `org-scans` repo) that enforces it automatically across
every Frappe app repo in the org. Treat it as a hard rule, not a style
preference:

**Rule:** if a `for`/`while` loop body contains `frappe.db.*`,
`frappe.qb...run()`, `frappe.get_doc`, `frappe.get_all`, `frappe.get_list`,
or `frappe.get_cached_doc` — stop and rewrite before merging. It doesn't
matter whether the call reads or writes, or whether the loop is top-level
or nested two/three levels deep inside another loop. Nesting only makes the
blast radius worse (N × M round trips instead of N), it isn't what makes the
pattern wrong — a single loop with one query per iteration is already the
defect.

**Why this keeps happening:** it's usually written incrementally — a
correct single-record read/write gets wrapped in a loop later to "handle
multiple rows" without anyone going back to batch it. Review every loop that
was added around *existing* single-record DB code as a suspect, not just
brand-new loops.

**Real example seen in production** (two features, same root cause):

```python
# BAD — write-side N+1, nested two loops deep
for grn_id, rows in grn_wise_items.items():                 # outer loop
    result = frappe.db.sql("...", {"grn": grn_id}, as_dict=1)  # 1 query per outer iteration
    for r in result:                                         # inner loop
        frappe.db.set_value(                                 # 1 UPDATE per inner row
            "Purchase Receipt Item", r["custom_purchase_receipt_item"],
            "custom_putaway_qty", r["total_qty"]
        )
```

```python
# BAD — read + write N+1, three loops deep
for grn_id, rows in grn_wise_items.items():
    for row in rows:
        item_wise_qty[row.custom_purchase_receipt_item] += row.qty
    for pri_item, revert_qty in item_wise_qty.items():
        current_qty = frappe.db.get_value(                  # SELECT per item
            "Purchase Receipt Item", pri_item, "custom_putaway_qty"
        ) or 0
        frappe.db.set_value(                                 # UPDATE per item
            "Purchase Receipt Item", pri_item, "custom_putaway_qty",
            max(current_qty - revert_qty, 0), update_modified=False
        )
```

**The fix for reads:** batch-fetch once before/outside the loop into a dict,
look up by key inside the loop (see the `category_label` example above) —
never call `frappe.db.get_value`/`get_all`/`get_list`/`get_doc` per
iteration.

**The fix for writes:** collect `{name: new_value}` pairs while iterating in
memory, then issue **one** bulk UPDATE after the loop instead of one
`frappe.db.set_value` per row. Use a `CASE WHEN` via `frappe.qb`, or raw SQL
only if `frappe.qb` can't express it:

```python
# GOOD — single bulk UPDATE instead of N set_value calls
from pypika import Case

updates = {r["custom_purchase_receipt_item"]: r["total_qty"] for r in result}
if updates:
    PRI = frappe.qb.DocType("Purchase Receipt Item")
    case = Case()
    for name, qty in updates.items():
        case = case.when(PRI.name == name, qty)
    (
        frappe.qb.update(PRI)
        .set(PRI.custom_putaway_qty, case.else_(PRI.custom_putaway_qty))
        .where(PRI.name.isin(list(updates.keys())))
    ).run()
```

For the read-then-write revert case, fetch every needed `current_qty` in one
`frappe.get_all(..., filters={"name": ["in", item_list]})` call, compute the
new values in Python, then apply them with the same bulk-update pattern.

**Checklist before merging any new/edited loop:**
1. Does the loop body call anything starting with `frappe.db.`, `frappe.qb`,
   `frappe.get_doc`, `frappe.get_all`, `frappe.get_list`, or
   `frappe.get_cached_doc`? If yes, it must move outside the loop or become
   a bulk operation — no exceptions for "just one extra query."
2. Is there a second loop nested inside the first? If a DB call sits inside
   *that*, the fix above is not optional — this is the highest-severity form
   of the pattern (N × M queries).
3. Can the whole loop be replaced by one `frappe.qb`/`frappe.get_all` call
   with `filters=[["name", "in", [...]]]` plus in-memory `SUM`/grouping,
   instead of looping at all?
- **Use `frappe.db.delete` for bulk deletion when the DocType has no `on_trash`/`after_delete` hooks.** It runs a single DELETE query. Use `frappe.delete_doc` in a loop only when controller trash hooks need to fire.
- **Don't reach for `frappe.get_doc` for read-only, multi-field fetches.** If you're not calling document methods or saving, use `frappe.db.get_value`/`get_all`/`get_list` instead — `get_doc` is heavier and triggers unnecessary permission/hook overhead.
- **Batch-fetch related records instead of querying in a loop.** (see N+1 example above)