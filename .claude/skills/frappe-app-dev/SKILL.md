---
name: frappe-app-dev
description: >-
  Builds full-stack Frappe Framework applications end-to-end. Use this skill any
  time the user mentions: creating or modifying a DocType, writing a controller
  or lifecycle hook, adding a whitelisted API, setting up a new Frappe app or
  bench site, building a desk form or list view, creating portal pages, writing
  background jobs or scheduled tasks, managing permissions or roles, writing
  Frappe tests, or working with frappe.db / frappe.qb. Also applies when the
  user says things like "how do I hook into save", "add a field to a DocType",
  "create a REST endpoint in Frappe", "run bench migrate", or "install an app on
  a site" — even if they don't explicitly say "Frappe".
---

# Frappe Full-Stack App Builder

## Global Rules

- Use bare `bench`. Not `./env/bin/bench`. Not a full path.
- Do not run `which bench`, `bench --version`, `bench --help`, or check frappe version. No discovery commands.
- Do not delegate bench detection to a subagent. Run `ls apps/ sites/ Procfile` yourself.
- Do not create DocType folders with `mkdir`. Frappe creates them via `bench migrate`.
- Run `bench start` in a background process only.
- Before running `bench start`, check if it's already running in an existing terminal. Do not start a second instance.
- Always pass `--site <site>` explicitly to bench commands. Never run bare `bench migrate`.
- Every function/method/class written in this app needs a docstring (see `code-style` SKILL.md), and every `.py`/`.js`/`.md` file needs the copyright header (see [licensing.md](./references/licensing.md)) — these apply regardless of which feature reference below is in play.
- Before starting any task that changes files, confirm the GitHub issue for
  it (issue-first workflow in `CLAUDE.md`, mandatory). Ask the user for the
  issue number. If there is none, offer to create one. The PR must link the
  issue with `Closes #<issue>`.
- Before ending any task that created or modified files, run through
  `quality-code-review`'s §0 Project hygiene checklist (docstrings, copyright
  headers, README/SETUP updates, structural conventions) — a lightweight
  self-check, not the full review.

## Flow Selection

Determine which flow applies, then read ONLY the relevant file:

### Creating a brand new app

Read [new-app.md](./references/new-app.md) — covers bench setup, app scaffolding, site creation, and installation.

### Working on an existing app

Read [existing-app.md](./references/existing-app.md) — covers finding the bench, locating the app, confirming site, and extending features.

## Feature References

Load ONLY the references needed for the current task:

| Topic            | When to load                                 | File                                                    |
| ---------------- | -------------------------------------------- | ------------------------------------------------------- |
| Site management  | Finding/creating/managing sites              | [site-management.md](./references/site-management.md)   |
| DocTypes         | Creating/modifying DocTypes, fields, naming  | [doctypes.md](./references/doctypes.md)                 |
| Controllers      | Document lifecycle, server logic             | [controllers.md](./references/controllers.md)           |
| Whitelisted APIs | REST endpoints, `@frappe.whitelist()`        | [api.md](./references/api.md)                           |
| Database & ORM   | `frappe.db`, queries, raw SQL                | [database.md](./references/database.md)                 |
| Caching          | Redis, `frappe.cache`                        | [caching.md](./references/caching.md)                   |
| Realtime         | WebSocket, `publish_realtime`                | [realtime.md](./references/realtime.md)                 |
| Background jobs  | `frappe.enqueue`, scheduled jobs             | [background-jobs.md](./references/background-jobs.md)   |
| Hooks            | `hooks.py` patterns                          | [hooks.md](./references/hooks.md)                       |
| Permissions      | Roles, DocType permissions, `has_permission` | [permissions.md](./references/permissions.md)           |
| Testing          | Writing & running tests                      | [testing.md](./references/testing.md)                   |
| Frontend & UI    | Desk UI, Vue SPA, portal pages           | [frontend.md](./references/frontend.md) (router → 3 sub-files) |
| Print formats    | Creating/customizing print formats, Print Designer | [print-format.md](./references/print-format.md) |
| Bench CLI        | All bench commands reference                 | [bench-operations.md](./references/bench-operations.md) |
| README.md        | Writing/updating the app's functional README | [readme.md](./references/readme.md)                     |
| SETUP.md         | Documenting integration/config requirements  | [setup.md](./references/setup.md)                       |
| Licensing & file headers | Adding license.txt, per-file copyright headers | [licensing.md](./references/licensing.md)         |

## Important: Do NOT load all references at once. Read only what the current task requires.