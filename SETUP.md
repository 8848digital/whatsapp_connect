<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# SETUP.md

## Meta WhatsApp Cloud API

### Overview

All messages, templates and flows go through the Meta WhatsApp Business
Platform (Cloud API). Create a Meta app with the WhatsApp product first:
[Get started](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started).

### Required Credentials

| Credential | Where it's stored | Required? |
| ---------- | ------------------ | --------- |
| Access Token | WhatsApp Account → Access Token (encrypted) | Yes. Use a permanent System User token in production. |
| Phone Number ID | WhatsApp Account → Phone Number ID | Yes |
| WhatsApp Business Account ID | WhatsApp Account → WhatsApp Business Account ID | Yes |
| App ID | WhatsApp Account → App ID | For template header samples |
| App Secret | WhatsApp Account → App Secret (encrypted) | Strongly recommended: webhook calls are checked with it |
| Webhook Verify Token | WhatsApp Account → Webhook Verify Token | Yes. Any secret text; the same text goes into Meta. |

Find them in the Meta App Dashboard: **WhatsApp > API Setup** (token, phone
number ID, business account ID) and **App settings > Basic** (App ID, App Secret).

### Settings DocType Fields

**WhatsApp Account** (one per phone number):

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Account Name | Data | Yes | |
| Enabled | Check | | Disabled accounts receive no webhooks and send nothing. |
| Default for Outgoing / Incoming Messages | Check | | One default per direction. |
| Send Read Receipts | Check | | Marks incoming messages as read in WhatsApp. |
| Graph API URL | Data | Yes | `https://graph.facebook.com` |
| Graph API Version | Data | Yes | For example `v21.0`. |

**WhatsApp Settings** (single):

| Field | Type | Mandatory | Notes |
| ----- | ---- | --------- | ----- |
| Refuse Unsigned Webhook Calls | Check | No | Refuses webhook calls when no account has an App Secret. |
| Default Country Code | Data | No | Added to numbers stored without one, for example `91`. |
| Keep WhatsApp Logs for (Days) | Int | No | Default 30; 0 keeps them. |
| Phone Number of Users | Select | No | Where role-based notifications find users' numbers (User or Employee). |

### Site Config / Environment Variables

None. All configuration is stored in the DocTypes above.

### How to Test

1. Save the WhatsApp Account and click **Subscribe App to Webhooks**.
2. In **WhatsApp Template**, click **Sync from Meta**: the approved templates
   of the account appear.
3. Open a Contact with your test number and click **⋯ > Send WhatsApp**.

## Webhooks

Register this URL in the Meta App Dashboard, **WhatsApp > Configuration >
Webhook** (the WhatsApp Account form shows it too):

| Meta setting | Value |
| ------------ | ----- |
| Callback URL | `https://<site>/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive` |
| Verify token | The account's Webhook Verify Token |
| Webhook fields | `messages`, `message_template_status_update`; `smb_message_echoes` if the number is also used in the WhatsApp Business app |

The site must be reachable from the internet over HTTPS. With an App
Secret, unsigned or forged calls get HTTP 403.

**How to test:** send a message from your phone to the business number. It
appears in **WhatsApp Message** and in the timeline of the Contact with
that number.

## WhatsApp Flows Data Endpoint (optional)

Only for flows with **Use Data Endpoint**. Meta encrypts these calls with
the account's public key.

| Item | Where |
| ---- | ----- |
| Flow key pair | WhatsApp Account → **Generate Flow Keys** (stores the private key encrypted and registers the public key in Meta) |
| Endpoint URL | Set automatically when the flow is saved to Meta: `https://<site>/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.endpoint.receive` |

**How to test:** open the flow's preview link (Meta > **Open Preview**) and
go through the screens.
