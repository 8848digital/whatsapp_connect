# CLAUDE.md — Frappe Skills & Custom App Structure

This file documents the agent skills available in this repository and the
canonical structure of a custom Frappe application used in this project.
Read this file at the start of every session that involves Frappe development.

All paths below are **relative to this file** (the skills repo root).
To resolve any path dynamically in Python:

````python
import pathlib

# Resolve the skills repo root from any script inside the repo
SKILLS_ROOT = pathlib.Path(__file__).resolve().parent
# -- or, from anywhere on disk --
SKILLS_ROOT = pathlib.Path("CLAUDE.md").resolve().parent

# Example: open a skill file
skill_path = SKILLS_ROOT / ".claude" / "skills" / "frappe-app-dev" / "SKILL.md"
ref_path   = SKILLS_ROOT / ".claude" / "skills" / "frappe-app-dev" / "references" / "new-app.md"
````

---

## Skills Overview

Skills live under `.claude/skills/<name>/` relative to this repo root.
Each skill has a `SKILL.md` — read it before writing code for that topic.

| Skill | When to activate | Entry point |
| ----- | ---------------- | ----------- |
| `frappe-app-dev` | Creating/modifying DocTypes, controllers, APIs, hooks, permissions, background jobs, scheduler, bench CLI, site management, tests | [SKILL.md](./.claude/skills/frappe-app-dev/SKILL.md) |
| `code-style` | Writing or reviewing any Python/JS code; questions about style, naming, line length, function size, helper ordering, docstrings | [SKILL.md](./.claude/skills/code-style/SKILL.md) |
| `quality-code-review` | Performing code reviews, audits, or pull-request feedback | [SKILL.md](./.claude/skills/quality-code-review/SKILL.md) |
| `ui-design` | Building Frappe Desk UI, Vue SPAs, portal pages, or any front-end component | [SKILL.md](./.claude/skills/ui-design/SKILL.md) |
| `fix-issue` | Fixing a reported GitHub issue end-to-end (facts → reproduce + fix → separate-context validation) | [SKILL.md](./.claude/skills/fix-issue/SKILL.md) |
| `deep-app-audit` | Multi-agent security / correctness / customization audit of a whole Frappe app. User-invoked only: `/deep-app-audit <app path>` | [SKILL.md](./.claude/skills/deep-app-audit/SKILL.md) |
| `technical-writing` | Writing docs, READMEs, commit messages, PR descriptions, plans, or release notes (Simplified Technical English) | [SKILL.md](./.claude/skills/technical-writing/SKILL.md) |
| `draft-security-advisory` | Turning a vulnerability report into a GitHub Security Advisory. User-invoked only: `/draft-security-advisory` | [SKILL.md](./.claude/skills/draft-security-advisory/SKILL.md) |
| `resolve-backport-conflicts` | Resolving conflict markers in a Mergify backport PR. User-invoked only: `/resolve-backport-conflicts <PR>` | [SKILL.md](./.claude/skills/resolve-backport-conflicts/SKILL.md) |

### Activation Rules

- **Always** load `code-style` when writing or editing Python or JavaScript.
- **Always** load `frappe-app-dev` for any Frappe/bench task.
- Load `ui-design` for any front-end or UX task.
- Load `quality-code-review` when explicitly reviewing existing code, **and**
  always run its §0 Project hygiene checklist as a final pass before ending
  any task that created or modified files — docstrings, copyright headers,
  README/SETUP updates, structural conventions. This is a quick self-check,
  not a full §1–§8 review; only run the full checklist when the user actually
  asks for a code review.
- Do **not** load all skills at once. Load only what the current task needs.

---

## frappe-app-dev — Flow Selection

Once [SKILL.md](./.claude/skills/frappe-app-dev/SKILL.md) is loaded, pick exactly one flow:

| Situation | Reference file |
| --------- | -------------- |
| Creating a new app | [new-app.md](./.claude/skills/frappe-app-dev/references/new-app.md) |
| Working on an existing app | [existing-app.md](./.claude/skills/frappe-app-dev/references/existing-app.md) |

Then load only the feature references you need for the task:

| Topic | When to load | Reference file |
| ----- | ------------ | -------------- |
| Site management | Finding/creating/managing sites | [site-management.md](./.claude/skills/frappe-app-dev/references/site-management.md) |
| DocTypes | Creating/modifying DocTypes, fields, naming | [doctypes.md](./.claude/skills/frappe-app-dev/references/doctypes.md) |
| Controllers | Document lifecycle, server logic | [controllers.md](./.claude/skills/frappe-app-dev/references/controllers.md) |
| Whitelisted APIs | REST endpoints, `@frappe.whitelist()` | [api.md](./.claude/skills/frappe-app-dev/references/api.md) |
| Database & ORM | `frappe.db`, queries, raw SQL | [database.md](./.claude/skills/frappe-app-dev/references/database.md) |
| Caching | Redis, `frappe.cache` | [caching.md](./.claude/skills/frappe-app-dev/references/caching.md) |
| Realtime | WebSocket, `publish_realtime` | [realtime.md](./.claude/skills/frappe-app-dev/references/realtime.md) |
| Background jobs | `frappe.enqueue`, scheduled jobs | [background-jobs.md](./.claude/skills/frappe-app-dev/references/background-jobs.md) |
| Hooks | `hooks.py` patterns | [hooks.md](./.claude/skills/frappe-app-dev/references/hooks.md) |
| Permissions | Roles, DocType permissions, `has_permission` | [permissions.md](./.claude/skills/frappe-app-dev/references/permissions.md) |
| Testing | Writing & running tests | [testing.md](./.claude/skills/frappe-app-dev/references/testing.md) |
| Frontend & UI | Desk UI, Vue SPA, portal pages | [frontend.md](./.claude/skills/frappe-app-dev/references/frontend.md) (router → 3 sub-files) |
| Frontend — Desk | Desk form/list customisation | [frontend-desk.md](./.claude/skills/frappe-app-dev/references/frontend-desk.md) |
| Frontend — Vue | Vue SPA apps | [frontend-vue.md](./.claude/skills/frappe-app-dev/references/frontend-vue.md) |
| Frontend — Portal | Portal/website pages | [frontend-portal.md](./.claude/skills/frappe-app-dev/references/frontend-portal.md) |
| Print formats | Creating/customizing print formats, Print Format Builder, Print Designer | [print-format.md](./.claude/skills/frappe-app-dev/references/print-format.md) |
| Bench CLI | All bench commands reference | [bench-operations.md](./.claude/skills/frappe-app-dev/references/bench-operations.md) |
| README.md | Writing/updating the app's functional README | [readme.md](./.claude/skills/frappe-app-dev/references/readme.md) |
| Module README.md | Creating/modifying anything inside a module (DocTypes, reports, workspaces, customizations, print formats, web forms, dashboards) | [module-readme.md](./.claude/skills/frappe-app-dev/references/module-readme.md) |
| SETUP.md | Documenting integration/config requirements | [setup.md](./.claude/skills/frappe-app-dev/references/setup.md) |
| Licensing & file headers | Adding license.txt, per-file copyright headers | [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md) |

---

## Custom App Structure Convention

All custom Frappe apps in this project follow the layout below.
Replace `<app_name>` with the actual app name (snake_case).
Replace `<module_name>` with the actual module name (snake_case). **`<module_name>` must never be the same string as `<app_name>`**, and **must be namespaced to/derived from `<app_name>`** (e.g. app `chances_erp` → module `chances_core`, not a bare `core`) — the module directory is a distinct, purposefully-named submodule of the app package, not a repeat of the app's own name. Frappe module names must be unique across every app installed on a site, so a bare, generic module name (`selling`, `core`, `utils`) risks colliding with a same-named module in a different installed app; namespacing to the app name avoids that.

**An app has one or more `<module_name>` directories, not exactly one.** A
small, single-purpose app may have just one. A larger app whose business
logic naturally splits into distinct domains has multiple sibling
`<module_name>` directories side by side under the app package, one per
domain — each independently namespaced to `<app_name>` (e.g. `chances_core`,
`chances_billing`, `chances_reporting`) and each named for what it does.
This matches `modules.txt`: every module listed there gets its own
`<module_name>/` directory. There is no single, app-wide `api/`/
`customization/`/`doctype/`/etc. — **every `<module_name>` directory
independently follows the full structure and rules below** (its own `api/`,
its own `customization/`, its own `doctype/`, its own `README.md`, and so
on). A whitelisted endpoint that belongs to the `chances_billing` module
lives under `chances_billing/api/v1/`; one that belongs to `chances_core`
lives under `chances_core/api/v1/` — never in a shared, app-root `api/`.

**Do not create a catch-all module named after the app itself** (e.g. a
`chances_erp/chances_erp/` directory inside the `chances_erp` app) as a
default "everything else" bucket — that's exactly the
`<module_name> != <app_name>` rule above, restated for the multi-module
case. Every module directory should be purpose-named and namespaced to the
app; if scaffolding (`bench new-app`) generates a default self-named module
and nothing ends up using it, delete it rather than leaving an empty stray
directory around.

````
<app_name>/                            ← repo root
├── <app_name>/                        ← Python package (pip-installable)
│   ├── <module_name>/                 ← One of one-or-more module directories (name MUST differ from <app_name>, each namespaced to it)
│   │   ├── api/                       ← ALL versioned public REST endpoints live here — and ONLY here
│   │   │   ├── v1/
│   │   │   │   ├── bank.py            ← Whitelisted endpoints for bank-related operations
│   │   │   │   ├── braniac.py         ← Whitelisted endpoints for braniac-related operations
│   │   │   │   └── company.py         ← Whitelisted endpoints for company-related operations
│   │   │   └── __init__.py
│   │   │
│   │   ├── customization/             ← Extend / override standard ERPNext/Frappe documents functionality
│   │   │   └── customer/              ← Customizations for the core "Customer" DocType (not owned by this app)
│   │   │       ├── customer.js        ← Client-side form script (adds/hides fields, form events on Customer)
│   │   │       ├── customer.py        ← doc_events hook functions for Customer (validate/on_update/etc.), NOT a Document subclass
│   │   │       ├── customer_kyc.py    ← KYC-specific business logic for Customer (verification, document checks)
│   │   │       ├── social_media.py    ← Social media profile linking/validation logic for Customer
│   │   │       └── utils.py           ← Shared helper functions used by customer.py/customer_kyc.py/social_media.py
│   │   │       └── (other business logic files — no api.py here)
│   │   │
│   │   ├── dashboard/                 ← Dashboard chart / number-card scripts
│   │   │   ├── prize_agreement.py     ← Chart/number-card data provider for Prize Agreement
│   │   │   ├── quotation.py           ← Chart/number-card data provider for Quotation
│   │   │   └── sales_order.py         ← Chart/number-card data provider for Sales Order
│   │   │
│   │   ├── doctype/                   ← Custom DocTypes (one sub-folder each)
│   │   │   └── creatives/              ← "Creatives" DocType, owned by this app
│   │   │       ├── __init__.py
│   │   │       ├── creatives.js       ← Client script
│   │   │       ├── creatives.json     ← DocType definition (source of truth)
│   │   │       ├── creatives.py       ← Controller (Document subclass + lifecycle hooks)
│   │   │       └── (other business logic files — no api.py here, see below)
│   │   │
│   │   ├── print_format/              ← Custom print format definitions
│   │   │   ├── __init__.py
│   │   │   ├── csr_certificate/       ← "CSR Certificate" print format
│   │   │   │   ├── __init__.py
│   │   │   │   └── csr_certificate.json
│   │   │   └── sponsor_donation/      ← "Sponsor Donation" print format
│   │   │       ├── __init__.py
│   │   │       └── sponsor_donation.json
│   │   │
│   │   ├── report/                    ← Script/Query reports (one sub-folder each)
│   │   │   └── blanket_order_tracking_report/   ← "Blanket Order Tracking" report
│   │   │       ├── __init__.py
│   │   │       ├── blanket_order_tracking_report.js
│   │   │       ├── blanket_order_tracking_report.json
│   │   │       ├── blanket_order_tracking_report.py
│   │   │       └── (other business logic files)
│   │   ├── web_form/                  ← Portal web forms (one sub-folder each)
│   │   │   ├── __init__.py
│   │   │   ├── agent/                 ← "Agent" portal web form
│   │   │   │   ├── __init__.py
│   │   │   │   ├── agent.js
│   │   │   │   ├── agent.json
│   │   │   │   └── agent.py
│   │   │   ├── sales_invoice/         ← "Sales Invoice" portal web form
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sales_invoice.js
│   │   │   │   ├── sales_invoice.json
│   │   │   │   └── sales_invoice.py
│   │   │   └── ticket/                ← "Ticket" portal web form
│   │   │       ├── __init__.py
│   │   │       ├── ticket.js
│   │   │       ├── ticket.json
│   │   │       └── ticket.py
│   │   │
│   │   ├── workspace/                 ← Workspace JSON definitions
│   │   │   └── automation/            ← "Automation" workspace
│   │   │       └── automation.json
│   │   │
│   │   ├── tasks.py                   ← Background/scheduled job functions (frappe.enqueue, scheduler_events targets)
│   │   ├── permissions.py             ← permission_query_conditions / has_permission hook functions (app-wide, not tied to one customization/<name>/)
│   │   ├── README.md                  ← Module-level summary — see references/module-readme.md
│   │   └── __init__.py
│   │
│   ├── <module_name_2>/               ← Sibling module — same internal structure as above,
│   │   │                                 repeated for every module in modules.txt (its own
│   │   │                                 api/, customization/, doctype/, README.md, etc.)
│   │   └── ...
│   │
│   ├── utils/                         ← App-wide utility package (business logic + shared helpers, no whitelisted code)
│   │   ├── __init__.py
│   │   ├── common.py                  ← Truly generic, cross-cutting helpers (e.g. jinja method/filter targets) — the only app-root "catch-all", keep it small
│   │   └── api_handlers/              ← Cross-cutting helpers used BY whitelisted endpoints, but not whitelisted themselves
│   │       └── response_formatter.py  ← Standardised JSON envelope helper (`api_response(...)`), shared across all API versions/modules
│   │       └── envelope.py            
│   │       └── error_messages.py      
│   │
│   ├── commands/                      ← Custom `bench` CLI commands
│   │   ├── __init__.py                ← registers `commands = [export_fixtures]`
│   │   ├── export_fixtures.py         ← `8848-export-fixtures`, copied verbatim from `project_base_template/commands/` (linked in Directory Purposes below)
│   │   └── README.md
│   │
│   ├── config/                        ← App-level config (desktop icons etc.)
│   │   └── __init__.py
│   │
│   ├── fixtures/                      ← Exportable fixture JSON files
│   │   ├── account_closing_balance.json
│   │   ├── address.json
│   │   └── asset_capitalization_stock_item.json
│   │
│   ├── public/                        ← Static assets served by nginx/gunicorn
│   │   └── js/
│   │       ├── <app_name>.bundle.js   ← Webpack entry point (auto-loaded desk-wide)
│   │       ├── lead.js
│   │       ├── ticket_web_form.js
│   │       └── workflow_action.js
│   │
│   │
│   ├── templates/                     ← Jinja templates for portal pages
│   │   ├── pages/
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── tests/                         ← Feature/integration tests spanning multiple modules (DocType-specific tests instead live alongside their DocType — see testing.md)
│   │   └── __init__.py
│   │
│   ├── __init__.py
│   ├── hooks.py                       ← App hooks wiring everything together
│   ├── install.py                     ← Post-install setup (run once on install)
│   ├── boot_session.py                ← Data injected into `frappe.boot` on session start
│   ├── modules.txt                    ← List of modules in this app
│   └── patches.txt                    ← Migration patch list
│
├── scripts/                           ← Repo-level scripts (linting, CI)
│   └── check_max_lines.py
│
├── commitlint.config.js               ← Conventional commits config
├── pyproject.toml                     ← PEP 517 build metadata
├── README.md                          ← Functional overview — see references/readme.md
├── SETUP.md                           ← Integration/config requirements — see references/setup.md (only if the app has integrations/settings; see rule below)
└── license.txt                        ← Mandatory in every project — see references/licensing.md
````

> **Note on `utils/` vs a root `utils.py`:** this app has exactly one `utils`
> namespace — the `utils/` package. There is no separate `<app_name>/utils.py`
> file anywhere. A package and a same-named module cannot coexist in the same
> parent directory (Python can only resolve one of them, and which one wins
> is not something to rely on) — so all app-wide helpers, including the
> generic ones that used to live in a standalone `utils.py`, live inside the
> `utils/` package (`utils/common.py` for generic helpers, `utils/api_handlers/`
> for API-supporting helpers). If a new category of shared helper is needed,
> add a new file under `utils/`, not a new top-level `utils.py`.

### Directory Purposes

Every row below prefixed `<module_name>/` applies **independently to each
module directory** — a two-module app has two `api/` folders, two
`doctype/` folders, two `README.md` files, and so on, one nested under each
module, never one shared copy at the app root.

| Directory | Purpose |
| --------- | ------- |
| `<module_name>/api/` | The **only** location for versioned, custom whitelisted endpoints not tied to a single DocType this app owns. See versioning pattern below. No `api/` folder or `api.py` file may exist anywhere else in the app. |
| `<module_name>/customization/` | Extend / override standard ERPNext/Frappe documents functionality — hook logic and thin business-logic files for DocTypes **owned by another app** (core Frappe/ERPNext, or a different installed app). Never place an `api.py` here — whitelisted endpoints belong under `<module_name>/api/`. |
| `<module_name>/dashboard/` | Chart / number-card / dashboard data providers. |
| `<module_name>/doctype/` | DocTypes **this app owns** — standard controller layout. Never place an `api.py` here — whitelisted endpoints belong under `<module_name>/api/`. |
| `<module_name>/print_format/` | Custom print format JSON (and JS if using a script-based format). |
| `<module_name>/report/` | Query / script reports. |
| `<module_name>/web_form/` | Portal-facing web forms. |
| `<module_name>/workspace/` | Desk workspace JSON. |
| `<module_name>/tasks.py` | Functions targeted by `frappe.enqueue(...)` and `hooks.py`'s `scheduler_events`. Not tied to one DocType. If it grows past ~300 lines, split by feature (`tasks_billing.py`, etc.) rather than one giant file — see `background-jobs.md`. |
| `<module_name>/permissions.py` | Functions targeted by `hooks.py`'s `permission_query_conditions` and `has_permission` for DocTypes not otherwise covered by a `customization/<name>/` file — see `permissions.md`. |
| `<module_name>/README.md` | Short summary of what this module contains — DocTypes, reports, workspaces, customizations, print formats, web forms, dashboards — see [module-readme.md](./.claude/skills/frappe-app-dev/references/module-readme.md). |
| `utils/` | App-wide utility package. Holds plain, non-whitelisted business logic and helpers shared across modules. The only top-level "generic helpers" location — there is no separate root `utils.py`. |
| `utils/common.py` | Truly generic, cross-cutting helpers with no more specific home (e.g. Jinja method/filter targets for `hooks.py`'s `jinja` key). Prefer a more specific file/folder before adding here — see the `utils.py`/`utils/` anti-pattern below. |
| `utils/api_handlers/` | Cross-cutting helpers **used by** whitelisted endpoints across every module's `api/` — the standard response envelope (`envelope.py`), error-message cleanup (`error_messages.py`), and the `after_request` response formatter (`response_formatter.py`). Copied **verbatim** from [`project_base_template/api_handlers/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/api_handlers) in the skills repo — then replace the `<app_name>` token inside the copied files and wire `after_request` in `hooks.py`, per [`project_base_template/custom_app_setup.md`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/custom_app_setup.md) §4.9 and [api.md](./.claude/skills/frappe-app-dev/references/api.md). Do **not** hand-write these. These files are never whitelisted themselves; they're imported by thin wrappers under `<module_name>/api/`. |
| `commands/` | Custom `bench` CLI commands for this app. Copied verbatim from [`project_base_template/commands/`](https://github.com/8848digital/skills/tree/8848-skills/project_base_template/commands) in the skills repo — see that folder's `README.md` for setup and [bench-operations.md](./.claude/skills/frappe-app-dev/references/bench-operations.md) for usage. Ships the `8848-export-fixtures` command by default. |
| `config/` | App config (desktop icons, module config). |
| `fixtures/` | Data exported via `fixtures` in `hooks.py`, synced across sites/environments. |
| `public/js/` | Bundled client-side assets not tied to a single doctype form (global scripts, workflow actions). |
| `scripts/` | Repo tooling — not shipped to sites (e.g. `check_max_lines.py`). |
| `templates/` | Jinja templates and website page controllers. |
| `tests/` | Feature/integration tests spanning multiple modules. DocType-specific tests live alongside their DocType instead (`doctype/<name>/test_<name>.py`) — see `testing.md`. |
| `hooks.py` | App-level hook registration only — no business logic. |
| `boot_session.py` | Data injected into `frappe.boot` on session start. Target of `hooks.py`'s `boot_session` key. |
| `install.py` | `after_install`/`before_install` logic for `bench install-app`. Target of `hooks.py`'s `after_install`/`before_install`/`after_uninstall` keys. |
| `modules.txt` | Registered module list — managed by Frappe, don't hand-edit casually. |
| `patches.txt` | Data migration patches run on `bench migrate`. |
| `README.md` | Functional documentation of what the app does — see [readme.md](./.claude/skills/frappe-app-dev/references/readme.md). |
| `SETUP.md` | Integration/configuration requirements — see [setup.md](./.claude/skills/frappe-app-dev/references/setup.md). Omit only if the app has zero external integrations and zero required settings. |
| `license.txt` | Mandatory in every repo, verbatim template — see [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md). |

### Key Conventions

| Area | Rule |
| ---- | ---- |
| **`<module_name>` naming** | The module directory must be named distinctly from `<app_name>`, and must be namespaced to/derived from `<app_name>` (e.g. `chances_core`, not `core`). Never reuse the app's own name as the module name, and never pick a bare generic name — Frappe module names must be unique across every app installed on a site, and an unnamespaced module name can collide with another app's module of the same name. |
| **Number of modules** | An app has one or more `<module_name>` directories, as siblings under the app package — not necessarily exactly one. Split into multiple purpose-named, app-namespaced modules when the app has multiple distinct business domains (e.g. `chances_core`, `chances_billing`); each module independently follows every other rule in this table (its own `api/`, its own `customization/`, its own `README.md`, etc.). |
| **DocType naming** | A custom DocType's own name must be singular (`Creative`, not `Creatives`) and must never use "Master" as a prefix or suffix (`Customer`, not `Customer Master`) — see [doctypes.md](./.claude/skills/frappe-app-dev/references/doctypes.md#naming-conventions-doctypes-own-name). |
| **Customization folder naming** | The folder for extending/overriding standard ERPNext/Frappe documents functionality must be named `customization/`. Never name it `custom/` or any other variant. |
| **API location** | All whitelisted endpoint code — `api.py` files, `api/` folders, and versioned endpoint files — lives **only** under `<module_name>/api/`. It must never appear inside `doctype/`, `customization/`, or as a standalone folder anywhere else in the app. Non-whitelisted helper code that supports the API layer (error handling, pre-request guards, response formatting) is not itself endpoint code and lives in `utils/api_handlers/` instead — see below. This includes `hooks.py`'s `override_whitelisted_methods` targets — the override function is itself whitelisted and lives under `<module_name>/api/`, same as any other endpoint. |
| **API support helpers location** | `error_messages.py`, `envelope.py`, and `response_formatter.py` (and any similar cross-cutting, non-whitelisted API helper) live in `utils/api_handlers/` at the app root — not inside any module's `api/` folder. This is a single shared location reused by every module's `api/vN/` endpoints in the app, so the response envelope and error handling stay identical across modules. |
| **Whitelisting** | `@frappe.whitelist()` may only be used on functions inside `<module_name>/api/`. Never whitelist a method or function inside `doctype/<name>/<name>.py` or `customization/<name>/*.py` — controller and customization files hold plain, non-whitelisted logic; expose it via a thin wrapper in `<module_name>/api/`. |
| **API versioning** | All public endpoints live under `<module_name>/api/v1/`. Never put versioned logic directly in the module root. |
| **API docstrings** | Every `@frappe.whitelist()` function must have a docstring documenting a 2–3 line explanation, the endpoint path, HTTP method, parameters (name, type, required/optional, description), and the response format. Dotted paths use the `<app_name>.<module_name>` convention. See [api.md](./.claude/skills/frappe-app-dev/references/api.md) for the required template. |
| **Docstrings — all functions** | Every custom function/method/class in the app — not just whitelisted endpoints — must have a docstring (explanation, parameters, return value). See [code-style SKILL.md](./.claude/skills/code-style/SKILL.md). |
| **Customization vs DocType** | Use `customization/` to extend / override standard ERPNext/Frappe documents functionality. Use `doctype/` for net-new custom DocTypes only. Neither folder may contain API code. |
| **`doc_events` wiring** | For a DocType **this app owns**, prefer controller class methods (`validate`, `on_submit`, etc. in `doctype/<name>/<name>.py`) over `hooks.py`'s `doc_events` — see `controllers.md`. Use `doc_events` mainly for DocTypes **owned by another app**, wired to functions in `customization/<name>/<name>.py`, and only there — never scattered into other files — see `hooks.md` and the `customization/` vs `doctype/` section below. A rare cross-cutting `doc_events` entry (e.g. `"*"` for all DocTypes) belongs in a module-root file named for what it does (e.g. `<module_name>/audit.py`), not stuffed into `tasks.py` or `permissions.py`. |
| **Hook files hold functions, not logic** | Both `doctype/<name>/<name>.py` (this app's controllers) and `customization/<name>/<name>.py` (`doc_events` targets for DocTypes owned elsewhere) contain only the hook methods/functions themselves — `validate`, `on_submit`, `on_update`, etc. — each delegating to a real implementation in a sibling file (`<name>_utils.py`, `utils.py`, or another feature-named file in the same folder). No business logic (queries, mutations, conditionals implementing behavior) is written inline in these files. See `controllers.md`'s "File structure: hooks vs. logic" and `hooks.md`'s "File structure: hooks vs. logic (customization)". |
| **Scheduler/background job targets** | `hooks.py`'s `scheduler_events` and any `frappe.enqueue(...)` dotted path point at `<module_name>/tasks.py` (or a feature-split file alongside it) — never at an app-root `tasks.py`/`setup.py`. |
| **Permission hook targets** | `hooks.py`'s `permission_query_conditions` and `has_permission` point at `<module_name>/permissions.py` unless the DocType already has a `customization/<name>/` file, in which case it belongs there instead. |
| **`utils/` is a package, not a file** | There is exactly one `utils` namespace per app: the `utils/` package. Never create a separate top-level `utils.py` alongside it — a package and a same-named module cannot coexist. Add new generic helpers to `utils/common.py`, and new files/subfolders under `utils/` for anything more specific. |
| **Fixtures** | Keep fixture JSON files in `fixtures/`. Export via the custom `commands/export_fixtures.py` bench command (`bench --site <site> 8848-export-fixtures`), which reads the `custom_fixtures` hook — not Frappe's built-in `fixtures` hook/`export-fixtures` command — and strips null/empty/zero-valued fields. See [bench-operations.md](./.claude/skills/frappe-app-dev/references/bench-operations.md). |
| **Public JS bundles** | `public/js/<app_name>.bundle.js` is the Webpack entry point. Additional form scripts go in the appropriate `doctype/` or `customization/` folder, **not** in `public/js/`. |
| **Print formats** | One sub-folder per format under `print_format/`. Each folder must contain `__init__.py` + the JSON definition. |
| **Web forms** | One sub-folder per form under `web_form/`. Each folder must contain `__init__.py`, `.json`, `.py` (server script), and `.js` (client script). |
| **Max line length** | Enforced by `scripts/check_max_lines.py`. Run it in CI and locally before committing. |
| **Issue-first workflow** | **Mandatory.** Every change to a repo — feature, fix, optimization, refactor, docs, config, dependency, any task, whether a person or an AI agent does it — starts from a GitHub issue. Raise the issue first, then open a PR against that issue. No issue, no PR, no merge. See "Issue-first workflow" below. |
| **Commit messages** | Follow Conventional Commits (enforced by `commitlint.config.js`). |
| **Version bump policy** | App version follows `a.b.c` (in `pyproject.toml` / `<app_name>/__init__.py`'s `__version__`). `a` (major) is bumped manually, by the developer's own decision — never inferred automatically. `b` (minor) must be bumped whenever a change landing on `develop`, `master`, or the default branch includes a **database change** — creating/altering a table (new DocType, new/changed field with a schema effect) or a migration-driven insert/update of records (a patch in `patches.txt`). `c` (patch) is bumped for any other change with no database change (docs, refactors, non-schema logic fixes). |
| **README.md** | Every app ships a functional `README.md` at repo root per [readme.md](./.claude/skills/frappe-app-dev/references/readme.md) — what the app does, not how it's structured. |
| **`<module_name>/README.md`** | Every module ships its own `README.md` per [module-readme.md](./.claude/skills/frappe-app-dev/references/module-readme.md), scaffolded at module-creation time and kept in sync whenever a DocType, report, workspace, customization, print format, web form, or dashboard is added/removed/renamed within that module. |
| **SETUP.md** | Every app with an external integration or a Settings-style DocType ships a `SETUP.md` at repo root per [setup.md](./.claude/skills/frappe-app-dev/references/setup.md), listing mandatory fields/credentials. |
| **license.txt** | Mandatory in every repo, verbatim, per [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md). |
| **File headers** | Every `.py` and `.js` file (and `.md` docs) carries the copyright header from [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md). JSON files are exempt (no comment syntax). |

---

## Issue-first workflow

This rule is **mandatory** for every change in every repo: a feature, a
fix, an optimization, a refactor, a docs or config change, a dependency
update, or any other task. It applies the same way to work that a person
does by hand and to work given to an AI agent.

1. **Raise the issue first.** Before you change code, make sure a GitHub
   issue exists for the work. The issue states the problem or the goal,
   and the expected result. If no issue exists, create one.
2. **Create a branch** from the target branch for that issue.
3. **Make the change** on that branch only.
4. **Reference the issue in each commit** with `Refs #<issue>`.
5. **Open a PR against the issue.** The PR description starts with
   `Closes #<issue>` (or `Fixes #<issue>`), so GitHub links the two and
   closes the issue on merge.
6. **One issue for each PR.** A PR without a linked issue is not
   reviewed and not merged.

**For AI agents:** before you start any task that changes files in a repo,
ask the user for the issue number. If there is no issue, offer to create
one, and create it only after the user agrees. Do not open a PR that has
no linked issue.

---

## `customization/` vs `doctype/`

Both hold Python logic tied to a DocType, but **ownership** differs:

- **`doctype/<name>/`** — this app defines the DocType (has its own `.json`).
  The `.py` here is the actual `Document` subclass. Wire hooks as class
  methods (`before_save`, `on_submit`, etc.).
- **`customization/<name>/`** — the DocType is owned elsewhere (core Frappe,
  ERPNext, or another installed app). This app cannot add a `Document`
  subclass for it, so instead:
  - `<name>.py` holds `doc_events` hook functions (registered in `hooks.py`,
    not as class methods).
  - `utils.py` / feature-named files hold the actual logic.
  - `<name>.js` holds client-script customizations for that doctype's form.
  - Any whitelisted endpoint scoped to this customization still belongs
    under `<module_name>/api/` — **not** inside `customization/<name>/`.

````python
# customization/customer/customer.py — doc_events hook, NOT a Document subclass
from <app_name>.<module_name>.customization.customer.utils import sync_customer_kyc

def on_update(doc, method):
    """
    Hook fired on Customer save. Keeps the customer's KYC record in sync
    with the latest form values.

    Parameters:
        doc (Document, required): The Customer document being saved.
        method (str, required): The hook event name passed by Frappe.

    Returns:
        None
    """
    sync_customer_kyc(doc)
````

````python
# hooks.py
doc_events = {
    "Customer": {
        "on_update": "<app_name>.<module_name>.customization.customer.customer.on_update"
    }
}
````

Note: neither `customer.py` nor `utils.py` here may contain `@frappe.whitelist()`
— any whitelisted endpoint touching Customer still lives under
`<module_name>/api/`, never inside `customization/`.

---

## Versioned `api/`

App-wide custom APIs (not scoped to one DocType) are versioned, and live
**exclusively** under `<module_name>/api/`. Only whitelisted endpoint code
lives here — cross-cutting, non-whitelisted support helpers (error
handling, pre-request guards, response formatting) live at the app root in
`utils/api_handlers/` instead, since they're reused by every module's API
surface, not just one module's:

````
<app_name>/<app_name>/
    <module_name>/
        api/
            v1/
                bank.py
                company.py
            __init__.py
    utils/
        api_handlers/
            response_formatter.py   ← standard response-shape helper, imported by api/vN/ files
            envelope.py             ← standard response-shape helper, imported by api/vN/ files
            error_messages.py       ← standard response-shape helper, imported by api/vN/ files
````

- Each resource gets its own file under `v1/` (or the current version).
- Cross-cutting concerns (`response_formatter.py`, `envelope.py`, `error_messages.py`) live in `utils/api_handlers/` at the app root —
  never duplicated per module, and never inside `api/` itself. They are
  **copied verbatim** from `project_base_template/api_handlers/` (not
  hand-written) — see [api.md](./.claude/skills/frappe-app-dev/references/api.md)
  and `project_base_template/custom_app_setup.md` §4.9.
- `response_formatter.py` also registers the `after_request` hook
  (`format_frappe_response_to_custom`) that rewrites every
  `/api/method/<app_name>…` response into the standard envelope globally —
  so wiring `after_request` in `hooks.py` is part of adopting these files,
  not optional.
- `envelope.py` is where the `api_response(...)` helper belongs;
  import it (re-exported from `response_formatter.py`) into any `api/vN/*.py`
  file that needs to shape a response explicitly.
- When introducing `v2/`, keep `v1/` working — do not break existing clients.
- No folder in the app other than `<module_name>/api/` (not `doctype/`,
  `customization/`, module root, or app root) may contain an `api/` folder
  or an `api.py` file.

---

## Anti-patterns

- **Don't change a repo without an issue.** Every change — by a person or
  by an AI agent — starts from a GitHub issue, and its PR links that issue
  with `Closes #<issue>`. A PR with no linked issue is not merged. See
  "Issue-first workflow" above.
- **Don't dump unrelated helpers into `utils/common.py`.** It's for truly
  generic, cross-cutting helpers used by many unrelated modules — not a
  catch-all. Prefer a file scoped to what the function does
  (`customization/customer/utils.py`, `utils/api_handlers/response_formatter.py`).
- **Don't create a top-level `utils.py` alongside the `utils/` package.** A
  package and a same-named module can't coexist in the same directory — pick
  one namespace (`utils/`) and put everything under it.
- **Don't write `Document`-style controller code in `customization/`.** You
  don't own that DocType's class — use `doc_events` hook functions instead
  of trying to subclass or monkey-patch the controller.
- **Don't write business logic inline inside a hook method/function in
  `doctype/<name>/<name>.py` or `customization/<name>/<name>.py`.** Both
  files exist only to wire hooks (`validate`, `on_submit`, `on_update`,
  etc.) to an implementation defined elsewhere — the hook body should be a
  one-line call to a function in a sibling file, never the queries,
  mutations, or conditionals that implement the behavior itself.
- **Don't invent a new standalone file named after the hook/event itself**
  (e.g. `set_naming.py`, `autoname.py`, `naming.py`) for a `doc_events`
  target. Every `doc_events` hook — including `before_naming` and
  `autoname` — targets that DocType's own `<name>.py`
  (`doctype/<name>/<name>.py` if this app owns it, `customization/<name>/<name>.py`
  if it doesn't), same as `validate` or `on_update` would. If that file
  already exists for the DocType, add the new hook function to it; only
  create the file if it doesn't exist yet, and even then name it after the
  DocType, never after the hook. See `hooks.md`'s "Naming hooks" example.
- **Don't put repo tooling in `<app_name>/scripts/`.** Keep it at the
  repo-root `scripts/` so it's clearly excluded from what gets installed to
  a site.
- **Don't skip `fixtures/` for environment-portable config data** (custom
  roles, custom fields, workflow states). Hand-managing these via the UI on
  each site causes drift between dev / staging / production.
- **Don't create `api.py` files or `api/` folders inside `doctype/`,
  `customization/`, or the app root.** All whitelisted endpoint code lives
  in exactly one place: `<module_name>/api/`. This is a hard rule, not a
  preference — it keeps the whitelisted surface area auditable from a
  single location. Non-whitelisted API support helpers still go in
  `utils/api_handlers/`, not inside `api/`.
- **Don't put `envelope.py`/`error_messages.py`/`response_formatter.py`
  back inside `<module_name>/api/`.** They're shared, non-whitelisted
  helpers — their home is `utils/api_handlers/` at the app root, reused by
  every module's `api/vN/` files.
- **Don't use `@frappe.whitelist()` inside a controller or customization
  file.** A method like `approve()` on an `Expense` controller stays plain
  Python. If the client needs to call it, write a whitelisted wrapper under
  `<module_name>/api/` that loads the document and calls the method
  internally — see [api.md](./.claude/skills/frappe-app-dev/references/api.md).
- **Don't name the module directory the same as the app.** `<module_name>`
  must be a distinct, meaningful name — never a repeat of `<app_name>`.
- **Don't give the module a bare, generic name.** A module name like
  `selling`, `core`, or `utils` satisfies "differs from `<app_name>`" but
  isn't namespaced, so it can collide with a same-named module from a
  different app installed on the same site (Frappe module names must be
  unique site-wide). Namespace it to the app instead, e.g. `chances_core`
  rather than `core`.
- **Don't leave a stray, unused default module around.** `bench new-app`
  scaffolds a module named after the app itself; if the app grows into
  multiple purpose-named modules instead (the normal case — see "Number of
  modules" above) and nothing ends up in that default module, delete it
  rather than leaving an empty directory that duplicates the app's own name.
- **Don't use `custom/` as a folder name.** The folder for extending or
  overriding standard ERPNext/Frappe documents functionality must always be
  named `customization/` — never `custom/` or any other shortened variant.
- **Don't write a function without a docstring.** This applies to every
  function/method/class in the app, not only whitelisted endpoints — see
  [code-style SKILL.md](./.claude/skills/code-style/SKILL.md).
- **Don't ship a repo without `license.txt`.** Every project gets the
  verbatim template from [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md), no exceptions.
- **Don't ship `.py`/`.js`/`.md` files without the copyright header.** See
  [licensing.md](./.claude/skills/frappe-app-dev/references/licensing.md) for the exact block per file type. JSON files are the only exemption.
- **Don't ship an integration without `SETUP.md`.** If the app talks to an
  external service (SMS, push, payment gateway, auth) or has a Settings
  DocType with required fields, document them in `SETUP.md` — see
  [setup.md](./.claude/skills/frappe-app-dev/references/setup.md).
- **Don't scatter scheduler/permission-hook targets loose in the app-package
  root.** `hooks.py` targets for `scheduler_events`, `permission_query_conditions`,
  and `has_permission` live under `<module_name>/tasks.py` and
  `<module_name>/permissions.py` respectively — never `<app_name>/tasks.py`
  or `<app_name>/permissions.py` sitting next to `hooks.py`.
