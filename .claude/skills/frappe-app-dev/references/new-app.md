# New App Workflow

Follow these steps in order. Do not skip steps.

## Checklist
```
- [ ] Step 1: Confirm bench root
- [ ] Step 2: Enable developer mode
- [ ] Step 3: Pick or create site
- [ ] Step 4: Create app
- [ ] Step 5: Restructure module directory to convention
- [ ] Step 6: Add mandatory project files
- [ ] Step 7: Install app on site
- [ ] Step 8: Build features
- [ ] Step 9: Migrate and verify
```

## Step 1: Confirm bench root

```bash
ls apps/ sites/ Procfile
```
If it succeeds, bench is valid. Do not run anything else to verify.

## Step 2: Enable developer mode

```bash
bench set-config -g developer_mode 1
```

## Step 3: Pick or create site

See [site-management.md](./site-management.md) for finding or creating a site.

Complete this step before proceeding. You need a working site first. Also
check the site has the mandatory foundation apps installed (`8848_frappe_core`,
`iga_8848`) per that file's "Mandatory foundation apps" section — flag it
to the user if either is missing, don't silently proceed.

## Step 4: Create app

The `bench new-app` command MUST use piped `printf`. No heredoc (`<<EOF`). No `--no-input`. No `--no-git`. No bare `bench new-app <name>` without pipe.

Ask user for: app name, title, description, publisher, email, license.

```bash
printf '<title>\n<description>\n<publisher>\n<email>\n<license>\nN\nN\nN\n' | bench new-app <app-name>
```

Example:
```bash
printf 'Expense Tracker\nTrack expenses\nJohn\njohn@example.com\nProprietary\nN\nN\nN\n' | bench new-app expense_tracker```

Verify:
```bash
ls apps/<app-name>
```

`bench new-app` scaffolds a module directory with the **same name as the
app** by default:

```
apps/<app_name>/
  <app_name>/
    <app_name>/          ← scaffolded module dir — SAME name as app (not yet compliant)
      __init__.py
    hooks.py
    __init__.py
  setup.py
```

This is a **starting point only** — proceed to Step 5 before writing any
feature code. Never leave the module directory named the same as the app;
see `CLAUDE.md`'s `<module_name>` naming rule.

## Step 5: Restructure module directory to convention

1. Ask the user for the intended `<module_name>` (must differ from
   `<app_name>` **and** be namespaced to/derived from it — e.g. app
   `chances_erp`, module `chances_core`, not a bare `core`. Frappe module
   names must be unique across every app installed on a site, so a
   generic, unnamespaced name risks colliding with another app's module —
   see `CLAUDE.md`'s `<module_name>` naming rule).
2. Rename the scaffolded module directory:
```bash
   git -C apps/<app-name> mv <app-name>/<app-name> <app-name>/<module-name>
```
3. Update every reference to the old dotted path
   (`<app_name>.<app_name>.*` → `<app_name>.<module_name>.*`) in `hooks.py`,
   `modules.txt`, and any generated boilerplate.
4. Create the standard subdirectories under `<module_name>/` per `CLAUDE.md`'s
   tree — at minimum `api/v1/`, `doctype/`, `customization/` — as the task
   needs them. Don't pre-create folders the app has no use for yet.
5. Scaffold `<module_name>/README.md` per
   [module-readme.md](./module-readme.md) — at minimum the title and
   `## Purpose` section. Do this now, not as a follow-up.
6. Re-run `bench --site <site> migrate` once after the rename to confirm
   nothing references the old module path.

## Step 6: Add mandatory project files

Every new app ships these at the repo root (`apps/<app-name>/`) before any
feature work is considered done:

- **`README.md`** — functional overview, per
  [readme.md](./readme.md). Fill in Overview/Key DocTypes/Features as they're
  built in Step 8, but create the file with at least the Overview and
  Installation sections now.
- **`license.txt`** — verbatim template, per
  [licensing.md](./licensing.md). Non-negotiable, no exceptions.
- **`SETUP.md`** — only if the app will have an external integration or a
  Settings DocType with required fields (ask the user if unsure). Create it
  once the first integration is added in Step 8, per
  [setup.md](./setup.md); skip entirely otherwise.
- **`<app_name>/commands/`** — copy `__init__.py`, `export_fixtures.py`, and
  `README.md` verbatim from
  [`project_base_template/commands/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/commands)
  in the skills repo, then wire `custom_fixtures` and `commands` in
  `hooks.py` per that folder's `README.md`. Gives the app the
  `8848-export-fixtures` bench command — see
  [bench-operations.md](./bench-operations.md).
- Add the copyright header (per [licensing.md](./licensing.md)) to every
  `.py`/`.js`/`.md` file created from this point on, including files
  generated in this workflow.
- **Align packaging metadata with `license.txt`.** `bench new-app`'s scaffold
  prompt asks for a license identifier (e.g. `mit`) and writes it into
  `pyproject.toml`. For 8848 Digital apps this must be `Proprietary`, not an
  open-source identifier — open the generated `pyproject.toml` after
  scaffolding and correct the `license` field (and `classifiers`, if present)
  to match `license.txt`. Never leave an OSS license identifier (MIT, Apache-2.0,
  etc.) sitting alongside a proprietary `license.txt`.

## Step 7: Install app on site

```bash
bench --site <site> install-app <app-name>
bench --site <site> list-apps  # verify
```

## Step 8: Build features

Write DocTypes, controllers, hooks, permissions, UI directly under
`<module_name>/` (created in Step 5) — never back in a directory named after
the app itself.

Every function/method/class written here needs a docstring (see
`code-style` SKILL.md); every whitelisted endpoint additionally needs the
full API docstring format (see [api.md](./api.md)).

Load the relevant feature references from the main SKILL.md table as needed.
As features land, update `README.md`'s Key DocTypes/Features sections and,
if an integration was added, `SETUP.md`'s credential table — in the same
change, not as a follow-up.

## Step 9: Migrate and verify

```bash
bench --site <site> migrate
```

**Rules:**
- Always pass `--site <site>` explicitly. Never run bare `bench migrate`.
- After migration succeeds, do NOT query the database directly to verify schema changes. Frappe's migrate output is the source of truth.
- If migrate fails with `SyntaxError`, fix the file first, then re-run.

Start bench in background if not already running:
```bash
bench start
```

Get URL:
```bash
bench --site <site> execute frappe.utils.get_url
```