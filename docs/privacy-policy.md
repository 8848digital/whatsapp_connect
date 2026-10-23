<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Privacy policy: WhatsApp Connect

> **Draft for review.** 8848 Digital LLP must approve this text before it is
> used as the Marketplace privacy policy.

This policy describes what the WhatsApp Connect app for Frappe and ERPNext,
published by 8848 Digital LLP, does with personal data.

## Summary

- The app runs on **your** Frappe site, and its data is stored in your site's database.
- 8848 Digital LLP receives **none** of this data. The app sends no usage data or telemetry to us.
- To send and receive WhatsApp messages, the app exchanges data with **Meta Platforms** through the WhatsApp Business Platform.

## Data that the app handles

| Data | Why | Where |
| ---- | --- | ----- |
| Phone numbers and WhatsApp names | To send and receive messages | Your site (WhatsApp Message, WhatsApp Profile) |
| Message content, files and flow answers | To send and receive messages | Your site (WhatsApp Message, File, WhatsApp Flow Response) |
| Delivery status and Meta's error codes | To show if a message arrived | Your site (WhatsApp Message) |
| Opt-out state | To stop templates to people who opted out | Your site (WhatsApp Profile) |
| Document values used in templates | To fill template variables | Sent to Meta in the message; kept on your site with the message |
| Meta access token, App Secret, Flow keys | To call Meta and check its calls | Your site, encrypted |
| Request and webhook logs | Troubleshooting | Your site (WhatsApp Log), deleted after the retention you set |

## Data sent outside your site

The app connects only to Meta's Graph API (the URL on the WhatsApp Account,
normally `https://graph.facebook.com`) and to file URLs that you enter
yourself. Meta's processing is covered by the
[WhatsApp Business Terms](https://www.whatsapp.com/legal/business-terms),
the [WhatsApp Business Messaging Policy](https://business.whatsapp.com/policy)
and the [Meta Privacy Policy](https://www.facebook.com/privacy/policy).

## Your responsibilities

You decide who receives messages and are the data controller for your
customers' data. You must have their consent to message them on WhatsApp,
as Meta's policies require. Customers can stop templates and campaigns by
sending STOP.

## Contact

8848 Digital LLP — [8848digital.com](https://8848digital.com) or
[open an issue](https://github.com/8848digital/whatsapp_connect/issues/new/choose).
