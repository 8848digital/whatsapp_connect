<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Flow

## Purpose

Builds WhatsApp Flows (screens and components), manages them in Meta,
sends them, saves the answers, and answers Meta's encrypted data-endpoint
calls.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Flow | A flow: screens, components, Flow JSON, Meta status and the doctype that answers create. |
| WhatsApp Flow Screen | One screen of a flow (child table). |
| WhatsApp Flow Component | One text or answer component on a screen (child table). |
| WhatsApp Flow Response | The answers of one customer, and the document they created. |
