<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

<p align="center"><img src="docs/images/logo.png" alt="WhatsApp Connect logo" width="96"></p>

# WhatsApp Connect

## Overview

WhatsApp Connect lets Frappe and ERPNext send and receive WhatsApp messages
through the Meta WhatsApp Business Platform (Cloud API), with no third-party
gateway. Teams send templates from any document, automate notifications
(for example invoices and payment receipts), run campaigns, chat with
customers inside the document timeline, and collect structured answers with
WhatsApp Flows. It works on Frappe 14, 15 and 16, with or without ERPNext.

| | |
| --- | --- |
| **Frappe** | 14, 15, 16 |
| **License** | MIT |
| **Maintained by** | [8848 Digital LLP](https://8848digital.com) |

## Key DocTypes

| DocType | Owned by this app? | Purpose |
| ------- | ------------------ | ------- |
| WhatsApp Account | Yes | A WhatsApp Business phone number connected through a Meta app. |
| WhatsApp Settings | Yes | App-wide settings: webhook signature policy, default country code, log retention, phone source for users. |
| WhatsApp Message | Yes | Every message sent or received, with its delivery status and Meta's error. |
| WhatsApp Profile | Yes | One customer number: WhatsApp name, linked Contact, opt-out state, last message time. |
| WhatsApp Template | Yes | Message templates approved by Meta, with variables filled from document fields. |
| WhatsApp Notification | Yes | Sends a template automatically on a document event, a date or a schedule. |
| WhatsApp Recipient List | Yes | A reusable list of numbers with per-recipient values. |
| WhatsApp Campaign | Yes | Sends a template to many recipients, now or later, with progress and retries. |
| WhatsApp Flow | Yes | Screens of forms that customers fill inside WhatsApp. |
| WhatsApp Flow Response | Yes | The answers of one customer to a flow. |
| WhatsApp Log | Yes | Graph API calls and webhook calls, for troubleshooting. |

## Features

- **Send from any document.** **⋯ > Send WhatsApp** on every form offers the
  document's and its contacts' numbers, sends an approved template with a
  preview filled from the document, or a free-text reply within 24 hours of
  the customer's last message.

  ![Send WhatsApp dialog with a template preview](docs/images/send-dialog.png)

- **Conversations in the timeline.** Messages appear in the timeline of their
  document; incoming messages are linked to the Contact, Lead or Customer
  with the same number. Customers, suppliers and leads also show their
  contacts' chats. **Reply** opens the dialog.

  ![Contact timeline with WhatsApp messages and Reply links](docs/images/timeline.png)

- **Templates** with a live WhatsApp preview: header (text, image,
  document, video), variables, footer and buttons (quick reply, call, URL,
  copy code, one-time password, flow, catalog, multi-product). Submit to
  Meta, sync from Meta, status updates from the webhook.

  ![WhatsApp Template with the live preview](docs/images/template.png)

- **Notifications** on document events (new, save, submit, cancel, delete,
  value change), dates (days before/after) and schedules. Send to a phone
  field, the party's mobile number (Payment Entry, Payment Request), other
  numbers or users with a role. Attach the document print as a PDF.

  ![Payment receipt notification on Payment Entry](docs/images/notification.png)

- **Campaigns** to recipient lists (imported from any doctype), with values
  for everyone or per recipient, at a set time. Rate limits are retried,
  failed messages can be sent again, and progress is shown.

  ![Campaign with its progress](docs/images/campaign.png)

- **WhatsApp Flows**: build screens and fields, publish in Meta, send them,
  and save the answers as a document (for example a Lead). Flows with a data
  endpoint are supported, with Meta's encryption.

  ![WhatsApp Flow with screens and components](docs/images/flow.png)

- **Delivery report** by template, campaign, account or day, and **failure
  reasons** from Meta on each failed message.

  ![WhatsApp Delivery Summary report](docs/images/report.png)

- **Opt-out**: customers who send STOP get no more templates or campaigns;
  START opts them in again.
- **Security**: webhook and Flow endpoint calls must be signed with the Meta
  App Secret.
- **Media**: files are uploaded to Meta, so private files and sites that Meta
  cannot reach work; incoming media is saved as private files.
- **Coexistence**: messages typed in the WhatsApp Business app on the phone
  are saved too.

The complete list is in [docs/features.md](docs/features.md), and the step-by-step
guide in [docs/user-guide.md](docs/user-guide.md).

## Integrations

- **Meta WhatsApp Business Platform (Cloud API)**: see [SETUP.md](./SETUP.md#meta-whatsapp-cloud-api)
- **Meta webhooks**: see [SETUP.md](./SETUP.md#webhooks)
- **WhatsApp Flows data endpoint** (optional): see [SETUP.md](./SETUP.md#whatsapp-flows-data-endpoint-optional)

## Installation

```bash
bench get-app https://github.com/8848digital/whatsapp_connect
bench --site <site_name> install-app whatsapp_connect
```

Then follow [SETUP.md](./SETUP.md).

## App Structure

See [CLAUDE.md](./CLAUDE.md) for the module and folder conventions, and
[docs/development.md](docs/development.md) for the development setup.

## Maintainers

8848 Digital LLP — [open an issue](https://github.com/8848digital/whatsapp_connect/issues/new/choose).
See [SUPPORT.md](SUPPORT.md) and [SECURITY.md](SECURITY.md).

## License

MIT. Copyright (c) 2026 8848 Digital LLP. See [license.txt](license.txt).
