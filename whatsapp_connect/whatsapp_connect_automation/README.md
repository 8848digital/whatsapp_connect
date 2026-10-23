<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Automation

## Purpose

Answers incoming messages without an agent: keywords, button replies, a
welcome message, an away message outside business hours, and actions that
read ERP data (order status, outstanding balance).

`auto_reply.py` is an incoming handler. It chooses the rules (`rules.py`) and
sends the answers in a background job, so the webhook answers Meta quickly.
`actions.py` reads the actions from the `whatsapp_connect_auto_reply_actions`
hook; `erp_actions.py` holds the built-in ERPNext actions.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Auto Reply | A rule: the trigger (Keyword, Button Reply, First Message, Outside Business Hours, Any Other Message) and the reply (text, buttons or list, template, Flow, action). |
| WhatsApp Auto Reply Option | A button or list row of a rule (child table). |
| WhatsApp Auto Reply Settings | Pause all auto-replies; business hours. |
| WhatsApp Business Hour | Opening hours of one day (child table). |

## Hooks

- `whatsapp_connect_auto_reply_actions = {"<name>": "<dotted.path>"}`: the function gets the incoming WhatsApp Message and returns the reply text.
