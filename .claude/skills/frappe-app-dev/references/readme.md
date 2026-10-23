# README.md — Functional Documentation

`README.md` at the app's repo root is written for a **reader who has never
opened the code** — a new team member, a client, or a future maintainer
deciding whether this app does what they need. It documents *what the app
does and why*, not folder structure (that's `CLAUDE.md`'s job).

## Required sections, in order

```markdown
# <App Display Name>

## Overview
2–4 sentences: what business problem this app solves, who uses it, and
where it fits (e.g. "Custom ERPNext app for <client/product> that handles
ticket sales, player KYC, and prize payouts for the Chances platform").

## Key DocTypes
Table of the DocTypes a reader needs to understand to use the app —
both DocTypes this app owns (`doctype/`) and standard Frappe/ERPNext
DocTypes it customizes (`customization/`).

| DocType | Owned by this app? | Purpose |
| ------- | ------------------ | ------- |
| Creatives | Yes (custom) | Stores ad creative assets tied to a sponsor campaign. |
| Customer | No (ERPNext core, customized) | Extended with KYC and social media fields for player onboarding. |

## Features
Bullet list of functional capabilities, in plain business language —
what a user can *do*, not what code runs.

- Sell tickets to episodes and track recipient de-duplication across
  reminder notifications.
- Send SMS notifications via Termii on purchase confirmation.
- Push notifications via Yudiz on episode reminders.

## Integrations
One line per external integration this app talks to, and a pointer to
`SETUP.md` for the actual required fields/credentials. Do not duplicate
setup details here — this section only says *that* an integration exists.

- **Termii (SMS)** — see [SETUP.md](./SETUP.md#termii-sms)
- **Yudiz (Push notifications)** — see [SETUP.md](./SETUP.md#yudiz-push)

## Installation
Standard bench install steps, e.g.:

    bench get-app <app_name> <repo_url>
    bench --site <site_name> install-app <app_name>

## App Structure
One line: "See [CLAUDE.md](./CLAUDE.md) for internal module/folder layout
and coding conventions." Do not re-explain the tree here.

## Maintainers
Team/contact responsible for the app (name/email or team alias — no
personal phone numbers or unnecessary PII).
```

## Rules

- Write for a non-developer reader wherever possible; save technical detail
  (whitelisted endpoint names, hook wiring) for `CLAUDE.md`/`api.md`.
- Every DocType this app owns, and every standard DocType it meaningfully
  customizes, must appear in the **Key DocTypes** table — a reader should
  never have to open `doctype/` or `customization/` folders just to learn
  what a DocType is *for*.
- Keep **Features** as a living list — update it whenever a feature is
  added or removed, in the same PR as the code change.
- `README.md` links to `SETUP.md` for configuration; it never repeats
  credential names, field names, or setup steps itself.

## Anti-patterns

- **Don't paste the `CLAUDE.md` folder tree into `README.md`.** Different
  audience, different job — link to it instead.
- **Don't list every DocType in the app.** Only ones a reader needs to
  understand to use or reason about the app functionally.
- **Don't bury integration credentials here.** They belong only in
  `SETUP.md`.