<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Example: Sales Invoice Detailed (custom Jinja print format, foreign DocType)

A worked example of "Print formats on a DocType you don't own" from
[print-format.md](../../print-format.md) — a `standard = "No"`,
`custom_format = 1`, `print_format_type = Jinja` print format for the core
**Sales Invoice** DocType.

**Sales Invoice is owned by the ERPNext app (`chances_erp` in this bench),
not by whatever custom app adds this format.** That's why `standard` is
`"No"` here, not `"Yes"`: Frappe's Developer Mode export
(`export_module_json`) only writes a `<module_name>/print_format/<name>/`
file when `standard == "Yes"`, and setting that flag doesn't require or
check ownership of the target `doc_type` — so a naive `"Yes"` would just
leave a same-name file expectation that never gets created. The `.json`/
`.html`/`.css` files in this folder are reference content to paste into the
`Print Format` record and into a `fixtures/` entry, not a doctype-folder
export — see step 2 below.

Dynamic behavior demonstrated:

- `add_header(...)` for the letterhead/heading block, with the correct
  8-argument signature (`page_num, max_pages, doc, letter_head,
  no_letterhead, footer, print_settings, print_heading_template`).
- A status badge (`Paid` / `Unpaid` / `Overdue` / `Draft`) driven entirely by
  `doc.status`, colored via a Jinja dict lookup rather than a chain of
  `{% if %}`/`{% elif %}`.
- Conditional rows/sections that only render when the data exists: `po_no`,
  `shipping_address_name`, `contact_display`, `terms`, and `rounded_total`
  only appearing when it actually differs from `grand_total`.
- A `{% for row in doc.items %}` loop over the child table, and a second
  `{% for tax in doc.taxes %}` loop that skips zero-amount tax rows.
- Currency-aware formatting via `frappe.utils.fmt_money(..., currency=doc.currency)`
  and the amount-in-words fallback
  (`doc.in_words or frappe.utils.money_in_words(doc.grand_total, doc.currency)`).

## Using this in a real app

1. Create the `Print Format` record via the Desk UI (or a console
   `frappe.get_doc({"doctype": "Print Format", ...}).insert()`), with
   `doc_type: "Sales Invoice"`, `standard: "No"`, `custom_format: 1`,
   `print_format_type: "Jinja"`, and paste in this folder's `.html`/`.css`
   content. Set `"module"` to whatever module groups print formats in
   *your* app (this example ships with the placeholder `"Accounts"` — it
   does not need to match Sales Invoice's own module).
2. Add it to your app's `hooks.py` so it ships as a fixture instead of a
   doctype-folder file:
   ```python
   custom_fixtures = [
       {
           "doctype": "Print Format",
           "filters": [["name", "in", ["Sales Invoice Detailed"]]],
       },
   ]
   ```
3. Run `bench --site <site> 8848-export-fixtures` (see
   [bench-operations.md](../../bench-operations.md)) — this writes the
   record into `fixtures/print_format.json`. **Do not** run a plain
   `bench --site <site> migrate` expecting it to export this file the way
   it would for a DocType you own — `standard = "No"` records are outside
   Developer Mode's doctype-folder sync entirely.
4. If your app already has a `customization/sales_invoice/` folder for
   other Sales Invoice hooks (doc_events, client script), add a line to
   that folder's `README.md` pointing at this print format so it's
   discoverable from the customization bundle — the actual file still
   lives in `fixtures/`, not inside `customization/`.

## Adapting it

- Remove the `outstanding_amount` row entirely if the app never wants to
  show it on customer-facing copies (e.g. a POS receipt).
- If custom fields exist on Sales Invoice (e.g. a GSTIN), add them as
  another conditional row next to `po_no`, following the same
  `{%- if doc.<field> %}...{%- endif %}` pattern.
- Swap the `status_class` dict values to match the app's own CSS class
  naming if it already has a design system.
