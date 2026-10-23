<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Development

WhatsApp Connect follows the 8848 Digital
[custom app setup](https://github.com/8848digital/skills/blob/8848-skills/project_base_template/custom_app_setup.md)
and the [8848 skills](https://github.com/8848digital/skills).

## Bench

Use one bench for each Frappe version you test, never a client bench.

| Frappe | Python | Branch |
| ------ | ------ | ------ |
| 14 | 3.10 | `version-14` |
| 15 | 3.10–3.12 | `version-15` |
| 16 | 3.14 | `version-16` |

```bash
bench init bench-v15 --frappe-branch version-15 --python python3.12
cd bench-v15
bench get-app --branch version-15 payments
bench get-app --branch version-15 erpnext
bench get-app https://github.com/8848digital/whatsapp_connect
bench new-site whatsapp.localhost --install-app payments --install-app erpnext --install-app whatsapp_connect
bench --site whatsapp.localhost set-config allow_tests true
```

On Frappe 14 and 15, run ERPNext's test setup once:
`bench --site whatsapp.localhost execute erpnext.setup.utils.before_tests`.

## Code layout

Five modules, each with `api/v1/` (the only place for whitelisted
functions), `doctype/` and a `README.md`:

| Module | Contents |
| ------ | -------- |
| `whatsapp_connect_core` | Accounts, Cloud API client (`cloud_api/`), webhook (`webhook/`), messages, profiles, templates, sending (`messaging/`), timeline, send dialog |
| `whatsapp_connect_notification` | Notifications, recipients, attachments, scheduled jobs |
| `whatsapp_connect_campaign` | Recipient lists, campaigns, batch sender, reports |
| `whatsapp_connect_flow` | Flows, Meta Flow API, encryption, endpoint, answers |
| `whatsapp_connect_setup` | WhatsApp Setup page, own-app setup, Embedded Signup hub and relay |

Controllers only call functions in a sibling `*_utils.py` file. Modules
extend each other through hooks in `hooks.py`:

| Hook | Use |
| ---- | --- |
| `whatsapp_connect_payload_builders` | `{"<message type>": "<function>"}` builds the message object to send |
| `whatsapp_connect_webhook_fields` | `{"<webhook field>": "<function>"}` handles a webhook field |
| `whatsapp_connect_incoming_handlers` | `["<function>"]` called with each saved incoming message |
| `whatsapp_connect_flow_handlers` | `{"<flow name>": "<function>"}` custom answers for the Flow data endpoint |

Other apps can use the same hooks, for example to answer a flow's endpoint
calls with their own data.

## Code quality

```bash
cd apps/whatsapp_connect
pip install pre-commit
pre-commit install
```

pre-commit runs black, isort, flake8, eslint, prettier, JSON/YAML/TOML
checks and a 250-line limit for Python files. Commit messages follow
Conventional Commits (`commitlint.config.js`). CI runs the tests on
Frappe 14, 15 and 16; the Linters workflow runs pre-commit, commitlint,
Semgrep and pip-audit.

Every function has a docstring; whitelisted functions use the 8848 API
docstring (endpoint, method, parameters, response) and return the
`api_response` envelope from `utils/api_handlers/`.

## Workflow

Every change starts from a GitHub issue, goes on a branch, and is merged
with a pull request that closes the issue.

## Agent skills

`CLAUDE.md` and `.claude/skills/` come from the skills repo. Update them
with `scripts/sync_skills.sh`; it also updates `commands/` and
`utils/api_handlers/`. The app is MIT-licensed (Frappe Marketplace), so new
files get this header, not the proprietary one from the `licensing`
reference:

```python
# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt
```

After a sync, set the MIT header again on the synced files.

## Tests

```bash
bench --site whatsapp.localhost run-tests --app whatsapp_connect
```

The tests never call Meta: the Graph API is mocked.
