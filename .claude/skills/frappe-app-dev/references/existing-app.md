# Existing App Workflow

Use this flow when the user wants to extend, modify, or fix an app that already exists.

## Checklist
```
- [ ] Step 1: Find and confirm bench root
- [ ] Step 2: Locate the app
- [ ] Step 3: Confirm site and app installation
- [ ] Step 4: Enable developer mode
- [ ] Step 5: Check mandatory project files
- [ ] Step 6: Build / modify features
- [ ] Step 7: Migrate and verify
```

## Step 1: Find and confirm bench root

The bench root is typically the parent of the workspace directory, or the workspace itself. Look for `apps/`, `sites/`, and `Procfile`.

```bash
ls apps/ sites/ Procfile
```

If the workspace is inside the app (e.g. user opened `apps/<app_name>/`), go up:
```bash
ls ../../apps/ ../../sites/ ../../Procfile
```

## Step 2: Locate the app

```bash
ls apps/
```

Find the app directory. Read its module structure:
```bash
ls apps/<app-name>/<app-name>/
```

Each subdirectory under the module is a Frappe module (contains DocTypes, etc.):
```bash
ls apps/<app-name>/<app-name>/<module-name>/
```

Do NOT create a second app. Do NOT run `bench new-app`.

If the module directory is still named the same as the app, or uses a bare,
unnamespaced name (older app predating the current `<module_name>` naming
rule in `CLAUDE.md` — must differ from `<app_name>` **and** be namespaced
to/derived from it, e.g. `chances_core` not `core`), do not silently rename
it mid-task — that's a breaking change to every import path. Flag it to the
user and treat renaming as its own separate, deliberate change.

If the task involves adding a **new** module to this app, apply the same
naming rule: namespace the new module name to `<app_name>` (e.g.
`chances_billing`, not `billing`) so it can't collide with a same-named
module from a different app installed on the same site.

## Step 3: Confirm site and app installation

See [site-management.md](./site-management.md) for finding the right site for this app.

Verify the app is installed:
```bash
bench --site <site> list-apps
```

If not installed:
```bash
bench --site <site> install-app <app-name>
```

While checking `list-apps`, also confirm the mandatory foundation apps
(`8848_frappe_core`, `iga_8848`) are present — see site-management.md's
"Mandatory foundation apps" section. Flag it to the user if either is
missing rather than silently proceeding.

## Step 4: Enable developer mode

```bash
bench set-config -g developer_mode 1
```

## Step 5: Check mandatory project files

```bash
ls apps/<app-name>/README.md apps/<app-name>/license.txt apps/<app-name>/SETUP.md
```

- **Missing `license.txt`** — add it now, verbatim, per
  [licensing.md](./licensing.md), regardless of what this task is about.
- **Missing `README.md`** — add a minimal one per [readme.md](./readme.md)
  before proceeding; backfilling the full Key DocTypes/Features tables can
  happen incrementally, but the file should exist.
- **Missing `SETUP.md`** — only add it if the app has an existing
  integration or Settings DocType with required fields; otherwise skip.
- **Missing `<module_name>/README.md`** on a module this task touches —
  add a minimal one per [module-readme.md](./module-readme.md) (title +
  `## Purpose` at least) before proceeding.
- **Missing `<app_name>/commands/`** — add it now, copying `__init__.py`,
  `export_fixtures.py`, and `README.md` verbatim from
  [`project_base_template/commands/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/commands)
  in the skills repo, and wiring `custom_fixtures` + `commands` in
  `hooks.py` per that folder's `README.md` — see
  [bench-operations.md](./bench-operations.md).
- **Missing `<app_name>/utils/api_handlers/`** (and you are adding or
  touching a whitelisted endpoint) — add it now, copying `envelope.py`,
  `error_messages.py`, and `response_formatter.py` **verbatim** from
  [`project_base_template/api_handlers/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/api_handlers)
  in the skills repo into `<app_name>/utils/api_handlers/`. These are
  canonical shared files — **do not hand-write your own response envelope.**
  After copying, replace the `<app_name>` token inside the files (the
  `Wired in hooks.py:` docstring line and the `/api/method/<app_name>` path
  check in `response_formatter.py`) and wire the formatter in `hooks.py`:
  `after_request = ["<app_name>.utils.api_handlers.response_formatter.format_frappe_response_to_custom"]`.
  Full steps: `project_base_template/custom_app_setup.md` §4.9; usage:
  [api.md](./api.md).
- Don't let a missing file block the actual task — create a minimal
  version and continue, rather than treating this as a blocker to raise
  with the user first.

## Step 6: Build / modify features

Read the app's existing code to understand patterns before making changes. Load only the relevant feature references from the main SKILL.md table.

Key files to read first:
- `apps/<app>/setup.cfg` or `pyproject.toml` — app metadata
- `apps/<app>/<app>/hooks.py` — existing hooks
- `apps/<app>/<app>/<module>/` — existing DocTypes and modules

Every function/method/class you add or modify needs a docstring (see
`code-style` SKILL.md), and every new/modified `.py`/`.js`/`.md` file needs
the copyright header (see [licensing.md](./licensing.md)) if it doesn't
already have one. If the change adds/removes a feature, integration, or
user-facing DocType, update `README.md` (and `SETUP.md` for integrations)
in the same change. If the change adds, removes, or renames a DocType,
report, workspace, customization, print format, web form, or dashboard
within a module, update that module's `<module_name>/README.md` in the
same change — see [module-readme.md](./module-readme.md).

## Step 7: Migrate and verify

```bash
bench --site <site> migrate
```

Same rules as new app — see [new-app.md](./new-app.md#step-9-migrate-and-verify) for migrate rules.