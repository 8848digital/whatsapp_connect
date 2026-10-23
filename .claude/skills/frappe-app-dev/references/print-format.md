<!--
Copyright (c) 2026 8848 Digital LLP. All rights reserved.
Proprietary and confidential. Unauthorized copying, distribution, or use
of this file, via any medium, is strictly prohibited without prior
written permission from 8848 Digital LLP.
-->

# Print Formats

A **Print Format** controls how a document (or a Query/Script Report) renders
as PDF/print output. Frappe has three ways to build one, plus one optional
external app for a fully visual designer. Pick the lightest approach that
satisfies the requirement — most business documents (invoices, vouchers,
certificates) only need a custom Jinja format.

## Choosing an approach

| Need | Approach |
| ---- | -------- |
| Minor tweak to an existing layout — hide/reorder/relabel fields already shown | **Print Format Builder** (drag-and-drop, no code) |
| Full custom layout: loops, conditionals, computed values, multi-table sections, version-controlled as an app file | **Custom Jinja print format** (`html` written by hand) — this is the default for anything shipped in an app |
| Pixel-perfect visual design (absolute positioning, layered elements, watermarks, dynamic multi-currency tables) with no Jinja | **Print Designer** app (external, opt-in — see below) |
| Print output for a Query/Script Report | `<report_name>.html` inside the report's own folder, using JS micro-templating (client-side), not Jinja — see `report/` in [doctypes.md](./doctypes.md) sibling structure |

Every DocType also gets a **Standard** print format automatically (built from
the form layout + mandatory fields) with no manual creation — it's the
fallback when nothing custom exists and is never a file in this app.

## Ownership decides the `standard` field

`export_module_json` (Frappe's Developer Mode export, in
`frappe/modules/utils.py`) only writes a `<module_name>/print_format/<name>/`
file when the record's own `standard` field is `"Yes"` — the folder path is
always `<module>/print_format/<name>/`, based purely on the Print Format's
*own* module/name, never on which `doc_type` it renders or who owns that
DocType. So whether a print format becomes a real doctype-folder file at all
comes down to one question: **does this app own the target DocType?**

| Target DocType | `standard` | Where it lives |
| --- | --- | --- |
| Owned by this app (a custom DocType under this app's own `doctype/<name>/`) | `"Yes"` | Real app source: `<module_name>/print_format/<name>/`, Developer-Mode-exported, migrated via `bench migrate` — Method 2 below. |
| Owned elsewhere (core Frappe/ERPNext, or a different installed app) | `"No"` | Never a doctype-folder file — Frappe's export only fires for `standard = "Yes"`. To still version it with the app, export it through **`fixtures/`** the same way as any other data on a doctype you don't own (Custom Field, Property Setter, …) — see "Print formats on a DocType you don't own" below. |

`chances_erp/accounts/print_format/purchase_auditing_voucher/` (used as the
worked example below) is `standard = "Yes"` legitimately — `chances_erp` is
the renamed ERPNext fork in this bench, so it *owns* `Purchase Invoice`.
A different app adding a print format for `Sales Invoice` or `Purchase
Invoice` does **not** own that DocType and should use the `"No"` +
`fixtures/` path instead, even though the folder-naming convention below
looks identical either way.

## Method 1: Print Format Builder (drag-and-drop)

Use for quick, low-risk layout tweaks that don't need to ship as a
version-controlled app file (e.g. a user-level customization on a site).

1. From a document's Print view: **Menu → Print → Customize** (needs System
   Manager), or open the awesomebar and search "New Print Format".
2. Drag fields from the sidebar onto the layout; drag back to remove.
3. Add free-form content via a **Custom HTML** block — supports Jinja plus
   Bootstrap 3 classes.
4. Adjust styling via **Customize → Edit Properties** (custom CSS) rather
   than restructuring the layout.
5. The default **Standard** format itself cannot be edited directly — the
   builder always creates/edits a separate named format.

This is the same builder ERPNext exposes for its own doctypes (Quotation,
Item, Sales Invoice, …) — there is no separate "ERPNext builder" vs
"framework builder".

## Method 2: Custom Jinja print format for a DocType this app owns

This is what belongs in `<module_name>/print_format/` per the app structure
convention (see root `CLAUDE.md`). Use this method **only** when the
`doc_type` the format renders is a custom DocType this app itself ships
under `doctype/<name>/`. If the target DocType belongs to core Frappe/
ERPNext or a different installed app, skip to "Print formats on a DocType
you don't own" instead.

1. Open the awesomebar → "New Print Format".
2. Set:
   - `doc_type` — the DocType this format renders (or `print_format_for =
     "Report"` + `report` for a report-scoped format).
   - `module` — the owning module, so it lives under
     `<module_name>/print_format/` when exported.
   - `standard` = **Yes** (required for it to export as an app fixture file
     instead of staying site-only DB data).
   - `custom_format` = **1** — this is what unlocks a hand-written `html`
     field instead of the builder's structured `format_data`.
   - `print_format_type` = **Jinja**.
3. Write the layout in the `html` field using Jinja + the same context
   available to any Frappe Jinja template: `doc` (the document), `letter_head`,
   `no_letterhead`, `print_settings`, and helpers like
   `frappe.utils.format_date(...)`, `frappe.get_list(...)`,
   `frappe.db.get_value(...)`.
4. Optionally set `css` for custom styling, and layout knobs
   (`margin_top/bottom/left/right`, `font_size`, `font`, `page_number`,
   `align_labels_right`, `show_section_headings`, `line_breaks`).
5. With **Developer Mode** enabled on the site, saving with `standard = Yes`
   exports the record as a fixture file into
   `<module_name>/print_format/<name>/` in the owning app — this is what
   makes it a real file the DocType JSON convention in `CLAUDE.md` expects,
   not just a DB row.

### On-disk shape

Frappe externalizes long `Code`-type fields (like `html`) into sibling files
instead of inlining them in the JSON — mirroring how DocType controllers get
their own `.py`/`.js` files. A real example from this bench
(`chances_erp/accounts/print_format/purchase_auditing_voucher/`):

```
print_format/
└── purchase_auditing_voucher/
    ├── __init__.py
    ├── purchase_auditing_voucher.json   ← metadata only — no "html" key
    └── purchase_auditing_voucher.html   ← the actual Jinja template body
```

```json
{
    "doctype": "Print Format",
    "name": "Purchase Auditing Voucher",
    "doc_type": "Purchase Invoice",
    "module": "Accounts",
    "standard": "Yes",
    "custom_format": 0,
    "print_format_type": "Jinja",
    "font": "Default",
    "default_print_language": "en",
    "align_labels_right": 0,
    "show_section_headings": 0,
    "line_breaks": 0,
    "print_format_builder": 0,
    "disabled": 0
}
```

```jinja
{%- from "templates/print_formats/standard_macros.html" import add_header -%}
<div>
    {{ add_header(0, 1, doc, letter_head, no_letterhead, doc.terms or "", print_settings) }}
    <table>
        <tr><td><strong>Supplier Name:</strong></td><td>{{ doc.supplier }}</td></tr>
        <tr><td><strong>Due Date:</strong></td><td>{{ frappe.utils.format_date(doc.due_date) }}</td></tr>
    </table>
</div>
```

`add_header`'s real signature (from
`frappe/templates/print_formats/standard_macros.html`) is `(page_num,
max_pages, doc, letter_head, no_letterhead, footer, print_settings=None,
print_heading_template=None)` — `footer` is a required positional arg
*before* `print_settings`. Some older in-repo print formats call it with
only 5 positional args (skipping `footer`); Jinja tolerates this silently
(missing macro args just become `Undefined` instead of raising), but
`print_settings` then never actually reaches the macro. Always pass
`footer` explicitly (`doc.terms or ""`, or the doctype's own footer text) as
shown above — don't copy the shorter 5-arg form.

If custom CSS is set, it likewise exports as a sibling `<name>.css`. Never
hand-write duplicate content in both the JSON's `html`/`css` keys and the
sidecar file — whichever the DocType export produced is the source of truth;
edit the sidecar, not the JSON, once one exists.

**Do not `mkdir` the print format folder or hand-write the JSON from
scratch** — same rule as DocTypes (see [doctypes.md](./doctypes.md)): create
the record through the UI (or `frappe.get_doc({"doctype": "Print
Format", ...}).insert()` in a console/patch), then let `bench migrate` /
Developer Mode's fixture export materialize the folder.

## Print formats on a DocType you don't own

Sales Invoice, Purchase Invoice, Quotation, and every other core Frappe/
ERPNext DocType fall here for any app that isn't the ERPNext fork itself —
same for a DocType owned by some other installed app.

Note this is a **convention, not a mechanical restriction**:
`export_module_json` never actually checks `doc_type` ownership, so marking
a Sales Invoice print format `standard = "Yes"` in some other app *would*
still export a `<module_name>/print_format/<name>/` file — Frappe doesn't
stop you. The reason to avoid it anyway is consistency with how every other
piece of data on a DocType you don't own is already handled in this project
(`fixtures/` for Custom Field/Property Setter/Workflow State, `customization/`
for hook logic — never a doctype-folder-owned file): `standard = "Yes"`
locks the record from Desk-UI editing in production and claims it as
protected, app-owned system content, which is misleading for a format built
on top of a schema this app doesn't control the evolution of.

Instead:

1. Build the format the same way as Method 2 (custom Jinja, `custom_format
   = 1`), but set `standard = "No"`.
2. Version it with the app through the **fixtures mechanism** instead of
   the doctype-folder one — add it to `hooks.py`'s `custom_fixtures` (see
   [bench-operations.md](./bench-operations.md)):
   ```python
   custom_fixtures = [
       {
           "doctype": "Print Format",
           "filters": [["name", "in", ["Sales Invoice Detailed"]]],
       },
   ]
   ```
   Then run `bench --site <site> 8848-export-fixtures`, which writes it to
   `fixtures/print_format.json` — a flat data snapshot, not a
   Developer-Mode-managed doctype-folder file.
3. If a `customization/<doctype_name>/` folder already exists for that
   DocType (doc_events, client script, etc. — see the `customization/` vs
   `doctype/` split in root `CLAUDE.md`), note the print format's name in
   that folder's `README.md` so it's discoverable from the customization
   bundle it conceptually belongs to, even though its actual file lives in
   `fixtures/`, not inside `customization/`.

See a full worked example — status badge, item/tax loops, conditional
sections, money formatting, and the `fixtures` entry above — at
[examples/print_format/sales_invoice_detailed/](./examples/print_format/sales_invoice_detailed/).

## Method 3: Print Designer app (optional, not installed by default)

[`frappe/print_designer`](https://github.com/frappe/print_designer) is a
separate, installable Frappe app — it is **not** part of core Frappe/ERPNext
(there is no `print_designer` field on the core `Print Format` DocType until
this app is installed). Reach for it only when a design genuinely needs true
WYSIWYG, absolute-positioned layout that plain Jinja/HTML makes painful:
layered elements, a visual table editor, built-in multi-currency handling,
barcodes/QR, and live preview while designing — all with an "advanced"
escape hatch to inject custom Jinja/HTML where needed.

Requires Frappe v15+ (or `develop`). Install like any other app:

```bash
bench get-app print_designer https://github.com/frappe/print_designer
bench --site <site> install-app print_designer
```

Once installed, new Print Formats gain a designer entry point in the UI;
designs are still stored as a `Print Format` record (JSON layout data plus
the existing `html`/`css` fields as a fallback), so the same
`<module_name>/print_format/<name>/` export convention above still applies —
only the *authoring* workflow changes, not where the resulting files live.
Don't add this app to a project's dependencies unless the task actually
calls for its visual designer — a plain Jinja format is less to install,
audit, and upgrade.

## Letter Head & Print Settings

- **Letter Head** (core Frappe DocType) supplies the header/footer image or
  HTML a print format renders via the `letter_head` / `no_letterhead`
  context variables (see the `add_header` macro above). It's user-managed
  data, not app code — export it via `fixtures/` (see root `CLAUDE.md`) if a
  specific letter head must ship with the app.
- **Print Settings** (site-wide singleton) controls defaults like the
  default print format per DocType, whether letter heads are disabled by
  default, and repeat-header/footer behavior. Configure per-site; it is not
  something an app ships as a fixture file.

## After creating/modifying a print format

For a `standard = "Yes"` format on a DocType this app owns (Method 2):

```bash
bench --site <site> migrate
```

If Developer Mode wasn't enabled when the record was saved, enable it and
re-save the `Print Format` record (or bump its `modified` timestamp) so
Developer Mode's export materializes/updates
`<module_name>/print_format/<name>/`.

For a `standard = "No"` format on a DocType this app doesn't own ("Print
formats on a DocType you don't own" above), that record is never touched by
`bench migrate`'s doctype-folder sync — instead run:

```bash
bench --site <site> 8848-export-fixtures
```

per [bench-operations.md](./bench-operations.md), which writes it into
`fixtures/print_format.json` based on the `custom_fixtures` hook entry, not
into `<module_name>/print_format/`. These two commands serve two different
export mechanisms — don't expect one to do the other's job.

## Anti-patterns

- **Don't hand-craft `print_format/<name>/<name>.json` from scratch.** Same
  rule as DocTypes — create the record via UI/console, let export
  materialize the folder, then edit the resulting files.
- **Don't duplicate the template body in both the JSON and the `.html`
  sidecar.** Once Frappe externalizes a `Code` field to its own file, that
  file is the source of truth — the JSON key is gone.
- **Don't install `print_designer` "just in case."** It's an extra
  dependency with its own upgrade cadence; only add it when a design
  actually needs its visual/absolute-positioning capabilities that plain
  Jinja can't reasonably express.
- **Don't put a whitelisted Python function anywhere under `print_format/`.**
  If a print format needs server-side data beyond what Jinja/`doc` already
  expose, add a whitelisted wrapper under `<module_name>/api/` per the app's
  API convention, and call it from client script — `print_format/` holds
  only the format's own JSON/HTML/CSS files.
- **Don't confuse a DocType print format with a Report print format.**
  Report-scoped HTML (`<report_name>.html`) uses client-side JS
  micro-templating, not Jinja, and lives alongside the report files, not
  under `print_format/`.
- **Don't set `standard = "Yes"` for a print format on a DocType this app
  doesn't own.** It will still mechanically export (Frappe never checks
  `doc_type` ownership), which is exactly the problem — it locks the record
  as protected system content and files it as doctype-folder-owned source
  for a schema this app doesn't actually control. Use `standard = "No"` +
  the `fixtures/` path instead, consistent with how Custom Field/Property
  Setter/other foreign-doctype data is already handled in this project.
- **Don't try to nest a Print Format's files inside `doctype/<name>/` or
  `customization/<name>/`.** Frappe's own sync (`get_doc_files` in
  `frappe/model/sync.py`) only scans one level directly under each module
  for a `print_format/` folder — anything nested deeper is invisible to
  `bench migrate` and will never be picked up. If a print format
  conceptually belongs to a `customization/<name>/` bundle, cross-reference
  it from that folder's `README.md`; don't move the actual files there.
