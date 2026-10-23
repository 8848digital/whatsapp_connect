<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Payment

## Purpose

Payment links in WhatsApp templates. `payment_link.py` registers two computed
values (`whatsapp_connect_value_providers` hook) that template mappings use
like field names:

- `payment_link`: the payment URL of the document's ERPNext Payment Request.
  An open, submitted request is reused; otherwise one is made and submitted
  without its email.
- `payment_link_token`: the Payment Request name signed with the site's
  encryption key, for a dynamic URL button `https://<site>/whatsapp_pay?t={{1}}`.

The page `www/whatsapp_pay.py` checks the token and redirects to the payment
URL of an open Payment Request.

Works for Sales Invoice, Sales Order and Payment Request. Needs ERPNext and a
Payment Gateway Account.

## DocTypes

None.
