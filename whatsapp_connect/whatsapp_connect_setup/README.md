<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Setup

## Purpose

The **WhatsApp Setup** page (`/app/whatsapp-setup`) connects and tests a
number from the desk, with no work in the Meta App Dashboard:

- **Connect with Facebook**: Meta's Embedded Signup through the 8848 hub.
- **Use my own Meta app**: finds the numbers of the token and sets the app
  webhook through the Graph API.

The same module runs the **hub** on one site (8848's), when WhatsApp Hub
Settings is enabled.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Hub Settings | Hub site only: the Meta app (App ID, App Secret, Embedded Signup configuration ID, webhook verify token). |
| WhatsApp Hub Connection | Hub site only: one site that connected through the hub; its webhook URL and forwarding secret. |

## How Connect with Facebook works

```
Site (WhatsApp Setup)        Hub (8848)                     Meta
  start_signup  ───────────▶ start: session + claim secret
  popup ───────────────────▶ /whatsapp_signup ────────────▶ Embedded Signup popup
                             finish: code ─────────────────▶ token, subscribe app
  complete_signup ─────────▶ claim (claim secret): token, forwarding secret
  register, sync, test ─────────────────────────────────────▶ Graph API (site's token)
                             webhook ◀───────────────────── messages, statuses
  webhook.receive ◀───────── forward, signed for the site
```

- The App Secret of the hub app never leaves the hub. The site keeps its
  forwarding secret as the account's App Secret, so the normal webhook and
  Flow endpoint signature checks work unchanged.
- The hub deletes the token when the site claims it.
- Flow endpoint calls go through the hub (`hub.flow_endpoint`); their body
  stays encrypted with the site's Flow key.

## Main files

| File | Contents |
| ---- | -------- |
| `account_setup.py` | Save the WhatsApp Account; run the steps: check, register (PIN), webhooks, templates, Flow keys |
| `discovery.py` | Check a token (`debug_token`) and list its business accounts and numbers |
| `webhook_setup.py` | Set the own app's webhook (`/<app>/subscriptions`) and subscribe the business account |
| `manual_setup.py` | Use my own Meta app |
| `hub_client.py` | The site's side of Connect with Facebook: start, complete, disconnect |
| `setup_checks.py` | Send `hello_world`, find a new incoming message |
| `hub/signup.py`, `hub/meta.py` | Hub: sessions, code exchange, claim, disconnect |
| `hub/relay.py` | Hub: check Meta's signature and forward webhooks and Flow calls |
| `page/whatsapp_setup/` | The desk page; dialogs in `public/js/whatsapp_setup_dialogs.js` |
| `../www/whatsapp_signup.*` | Hub page that opens Meta's popup |

## API

`api/v1/setup.py` (System Manager, WhatsApp Manager): `get_status`,
`start_hub_signup`, `complete_hub_signup`, `discover_numbers`,
`connect_own_app`, `run_steps`, `send_test`, `check_incoming`,
`disconnect_hub`.

`api/v1/hub.py` (guest, hub only, rate limited): `start`, `finish`, `claim`,
`disconnect`, `webhook`, `flow_endpoint`.

## Tests

`test_manual_setup.py`, `test_hub_signup.py`, `test_hub_relay.py`,
`test_setup_checks.py`. Meta is mocked; in the hub tests the site is its
own hub.
