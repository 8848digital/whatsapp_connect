# `<module_name>/README.md` — Module-Level Summary

Every module (`<module_name>/`) ships its own `README.md`, written for a
**contributor working inside this app** who needs to orient inside one
module without opening every subfolder. This is a different audience from
the app-level `README.md` ([readme.md](./readme.md)): technical and
structural, not business-facing.

## Required sections, in order

```markdown
# <Module Display Name>

## Purpose
1–2 sentences: what this module is responsible for within the app (e.g.
"Owns campaign creative assets and sponsor-facing reporting for the
Chances platform.").

## DocTypes
Table of DocTypes defined in this module's `doctype/` folder.

| DocType | Purpose |
| ------- | ------- |
| Creative | Ad creative asset tied to a sponsor campaign. |

## Customizations
Table of DocTypes owned elsewhere that this module customizes, from
`customization/`.

| DocType | Owned by | What's customized |
| ------- | -------- | ------------------ |
| Customer | ERPNext core | KYC fields, social media linking. |

## Reports
Bullet list of reports in `report/`, one line each on what it shows.

## Workspaces
Bullet list of workspaces in `workspace/`, one line each on what they group.

## Print Formats
Bullet list of print formats in `print_format/`.

## Web Forms
Bullet list of portal web forms in `web_form/`.

## Dashboards
Bullet list of dashboard chart/number-card providers in `dashboard/`.
```

Omit any section for a subfolder that doesn't exist in this module — don't
list empty sections.

## Rules

- **Scaffold at module-creation time.** When a module is created (new app's
  Step 5, or a new module added to an existing app), create
  `<module_name>/README.md` with at least the `# <Module Display Name>` and
  `## Purpose` sections — don't leave it for later.
- **Update in the same PR/commit as the structural change.** Adding,
  removing, or renaming a DocType, report, workspace, customization, print
  format, or web form inside a module updates that module's `README.md` in
  the same change — not as a follow-up.
- Keep entries one line each; link to the DocType's own JSON/controller for
  detail, don't duplicate field-level documentation here.
- Write for a developer who already knows Frappe — no need to explain what
  a DocType or a workspace *is*, only what this module's instances are *for*.

## Anti-patterns

- **Don't let this drift into a copy of the app-level `README.md`.** No
  business narrative, no installation steps, no integrations list — those
  belong at the app root.
- **Don't list DocTypes/reports/etc. from *other* modules.** Only what
  physically lives in this module's folder.
- **Don't skip the update because "it's just a small change."** A single
  new DocType still needs one row added — that's the entire point of
  keeping this file current.
