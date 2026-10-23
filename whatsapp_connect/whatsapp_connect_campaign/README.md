<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Campaign

## Purpose

Sends a template to many recipients: recipient lists, scheduled campaigns,
retries, and the delivery reports.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Recipient List | A reusable list of numbers, imported from any doctype. |
| WhatsApp Recipient | One recipient with per-recipient values (child table). |
| WhatsApp Campaign | A template sent to a list or numbers, now or later, with progress counts. |

## Reports

- **WhatsApp Delivery Summary**: sent, delivered, read, failed and opted-out messages with rates, by template, campaign, account or day.
- **WhatsApp Campaign Recipients**: one row per message of a campaign, with status, times and Meta's error.
