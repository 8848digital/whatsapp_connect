<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect CRM

## Purpose

Makes WhatsApp Connect work with Frappe CRM. Frappe CRM was written for the
frappe_whatsapp app, so this module serves CRM with the names that app uses:

- `api/v1/crm_whatsapp.py` overrides the endpoints of `crm.api.whatsapp`
  (`override_whitelisted_methods` in hooks.py). The WhatsApp tab of CRM Leads
  and CRM Deals shows the messages of the record's numbers and sends text,
  files, reactions and templates through WhatsApp Connect.
- WhatsApp Message has the read-only names `type` and `message`
  (`whatsapp_connect_core/doctype/whatsapp_message/frappe_whatsapp_fields.py`),
  because Frappe CRM's doc_events read them.
- `permissions.py` (after_migrate) gives Sales User and Sales Manager read
  access to WhatsApp Templates.

On sites without Frappe CRM, nothing here runs.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Templates | Virtual and read only: the approved WhatsApp Templates, for the CRM template picker. |
