# SETUP.md — Integration & Configuration Requirements

Any app that talks to an external service, or exposes a Settings-style
DocType with required fields, ships a `SETUP.md` at the repo root. Its job:
tell whoever is deploying the app exactly what to configure before it will
work — nothing more.

**When to skip it:** the app has zero external integrations and zero
required settings. Everything else gets a `SETUP.md`.

## Required sections, one subsection per integration/settings group

```markdown
# SETUP.md

## <Integration Name> (e.g. Termii SMS)

### Overview
1–2 lines: what this integration is used for in the app.

### Required Credentials
| Credential | Where it's stored | Required? |
| ---------- | ------------------ | --------- |
| API Key | `site_config.json` → `termii_api_key` | Yes |
| Sender ID | Settings DocType → "Chances Settings" → `sender_id` | Yes |

### Settings DocType Fields
If config is stored in a Frappe Single DocType (e.g. "Chances Settings"),
list every mandatory field:

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Termii API Key | Password | Yes | Get from Termii dashboard → API Keys |
| Sender ID | Data | Yes | Must be pre-approved by Termii |

### Site Config / Environment Variables
List anything expected in `site_config.json` / `common_site_config.json`
or as an environment variable — key name, expected value shape, and
whether it's per-site or shared.

### Webhooks (if applicable)
Any URL that must be registered with the third party (e.g. delivery
status callback), and the endpoint in this app that handles it.

### How to Test
Minimal steps to confirm the integration is wired correctly (e.g. "Trigger
a test SMS from Settings → Chances Settings → 'Send Test SMS' button").
```

## Rules

- One subsection per integration — don't merge Termii and Yudiz into one
  undifferentiated block.
- Never put actual secret values (API keys, tokens) in `SETUP.md` — only
  the *name* of the credential and where it's configured.
- Keep this in sync with the actual Settings DocType — if a field is added
  or removed there, update `SETUP.md` in the same PR.
- Cross-link from `README.md`'s Integrations section, don't duplicate.

## Anti-patterns

- **Don't put setup instructions inline in `README.md`.** `README.md` says
  an integration exists; `SETUP.md` says how to configure it.
- **Don't paste real API keys, tokens, or secrets into `SETUP.md`.** It
  documents *what's required*, not the values themselves.
- **Don't skip this file because "it's just one field."** If a Settings
  DocType has any mandatory field, it goes in `SETUP.md`.