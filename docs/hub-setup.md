<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Hub setup (8848 Digital, once)

**Connect with Facebook** on the WhatsApp Setup page needs a hub: one site,
run by 8848 Digital, with a Meta app that can use Embedded Signup. Customers
do not do any of this. You do it once, then every customer site connects
with a few clicks.

## What you need

| Item | Why |
| ---- | --- |
| A verified Meta Business portfolio for 8848 Digital | Meta requires business verification for Tech Providers. |
| A Meta app of type **Business** with the WhatsApp product | The app that customers give access to. |
| Tech Provider status for the app | Embedded Signup for other businesses' numbers. |
| Advanced access to `whatsapp_business_management` and `whatsapp_business_messaging` | Through App Review. |
| A Frappe site on a public HTTPS domain with WhatsApp Connect | The hub, for example `https://hub.8848digital.com`. |

Meta's guides: [Become a Tech Provider](https://developers.facebook.com/documentation/business-messaging/whatsapp/solution-providers/get-started-for-tech-providers),
[Embedded Signup](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/overview),
[Embedded Signup implementation](https://developers.facebook.com/documentation/business-messaging/whatsapp/embedded-signup/implementation/).

## Steps

### 1. Meta Business and the app

1. In [Meta Business Settings](https://business.facebook.com/settings), finish **Business verification** for 8848 Digital.
2. In the [App Dashboard](https://developers.facebook.com/apps), create an app of type **Business** and add **WhatsApp**.
3. Follow Meta's Tech Provider steps for the app (accept the terms, connect the business portfolio).

### 2. Facebook Login for Business

1. Add the **Facebook Login for Business** product.
2. **Settings**: add the hub domain to **Allowed domains for the JavaScript SDK** and to **Valid OAuth redirect URIs** (`https://hub.8848digital.com/`). The domain must use HTTPS.
3. **Configurations > Create configuration**: choose **WhatsApp Embedded Signup**, token type **System-user access token**, never expires, permissions `whatsapp_business_management` and `whatsapp_business_messaging`.
4. Copy the **Configuration ID**.

### 3. App Review

Request **Advanced access** for `whatsapp_business_management` and
`whatsapp_business_messaging`. Meta asks for a screencast: record the
WhatsApp Setup page connecting a test number (see
[demo-video-script.md](demo-video-script.md)).

### 4. The hub site

1. Install WhatsApp Connect on the hub site.
2. Open **WhatsApp Hub Settings** and fill in:

   | Field | Value |
   | ----- | ----- |
   | Enable Hub | On |
   | App ID, App Secret | App settings > Basic |
   | Embedded Signup Configuration ID | From step 2 |
   | Webhook Verify Token | Any long random text |
   | Graph API Version | The version your app uses, for example `v24.0` |

3. Save. The form shows the URLs for the next step.

### 5. The app webhook

In the App Dashboard: **WhatsApp > Configuration > Webhook**:

| Setting | Value |
| ------- | ----- |
| Callback URL | `https://<hub>/api/method/whatsapp_connect.whatsapp_connect_setup.api.v1.hub.webhook` |
| Verify token | The Webhook Verify Token of WhatsApp Hub Settings |
| Fields | `messages`, `message_template_status_update`, `smb_message_echoes` |

The hub checks each call with the App Secret and forwards it to the site
that owns the business account.

### 6. Tell customers the Hub URL

Customers enter the hub's address (`https://hub.8848digital.com`) in
**WhatsApp Settings > Hub URL**. To make this automatic, set it as the
default value of that field in a release.

## How to test

1. On a test site, set **Hub URL**, open **WhatsApp Setup** and click
   **Connect with Facebook**.
2. Finish the Meta window with a test number.
3. On the hub, **WhatsApp Hub Connection** shows the site as **Claimed**.
4. On the test site, click **Test** and send a message from your phone:
   **Last Forwarded On** changes on the hub connection.

## Operation

| Task | Where |
| ---- | ----- |
| See connected sites | WhatsApp Hub Connection (status, number, last forward, errors) |
| Failed forwards | **Failed Forwards** and **Last Error** on the connection; the site was down or refused the signature |
| Stop a site | The site clicks **Disconnect from Hub** on its WhatsApp Account, or set the connection to Disconnected |
| Old sessions | Unclaimed sessions are deleted daily |
| Rotate the App Secret | Change it in Meta and in WhatsApp Hub Settings at the same time; sites are not affected |

## Security

- The hub endpoints `start`, `finish`, `claim` and `disconnect` are rate
  limited. A session can only be claimed with the secret that `start`
  returned to the site's server, and only within one hour.
- The hub calls only public HTTPS sites (not private or local addresses),
  unless **Allow HTTP and Private Sites** is on (testing only).
- The hub keeps no customer token after the claim. Each site has its own
  forwarding secret.
