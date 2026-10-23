<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Support

| Problem | What to check |
| ------- | ------------- |
| A WhatsApp Setup step failed | The step's message gives the reason. Fix it and click **Run Setup Again**. |
| Connect with Facebook is greyed out | Set **Hub URL** in WhatsApp Settings, or use **Enter App Details**. |
| Incoming messages do not arrive | The callback URL and verify token in Meta; Subscribe App to Webhooks; the `messages` field is subscribed; the account is enabled. |
| Webhook calls get HTTP 403 | The App Secret on the WhatsApp Account must be the one of the Meta app. |
| A template is missing in the lists | Only Approved templates can be sent; click Sync from Meta. |
| A message is Failed | Open it: Error Code and Error Message show Meta's reason; Send Again retries it. |
| A notification is not sent | Enabled, the condition, the recipients, the opt-out state; WhatsApp Log shows the calls. |
| A free-text reply is refused | WhatsApp allows free text only within 24 hours of the customer's last message. |

- **Bugs and ideas:** [open an issue](https://github.com/8848digital/whatsapp_connect/issues/new/choose).
- **Security problems:** see [SECURITY.md](SECURITY.md).
- **Implementation and custom work:** [8848 Digital LLP](https://8848digital.com).

Do not put tokens, secrets or customer data in issues.
