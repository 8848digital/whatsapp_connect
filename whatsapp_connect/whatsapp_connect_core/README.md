<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Core

## Purpose

Owns the connection to the Meta WhatsApp Cloud API: accounts, the Cloud API
client, the webhook, messages, profiles, templates, the send dialog and the
timeline.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Account | A phone number connected through a Meta app; credentials and Flow keys. |
| WhatsApp Settings | Webhook signature policy, country code, log retention, user phone source, lead capture, inbox notifications. |
| WhatsApp Message | One sent or received message, with status, error and reference document. |
| WhatsApp Profile | One customer number: name, contact, opt-out, last incoming time, and the conversation state of the WhatsApp Inbox (status, assignee, unread count, last message). |
| WhatsApp Template | A message template, synced with Meta. |
| WhatsApp Template Button | A button of a template (child table). |
| WhatsApp Log | A Graph API call or webhook call. |

## Workspace

**WhatsApp Connect** (`/app/whatsapp-connect`): number cards (Open WhatsApp
Chats, Unread WhatsApp Chats, WhatsApp Received Today, WhatsApp Failed This
Week), the WhatsApp Messages chart, shortcuts, and link cards. Frappe 16 also
gets the WhatsApp Connect sidebar (`sidebar/`).
