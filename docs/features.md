<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# Features

## Setup

| Feature | Details |
| ------- | ------- |
| WhatsApp Setup page | Connects and tests a number from the desk; no work in the Meta App Dashboard. |
| Connect with Facebook | Meta's Embedded Signup through the 8848 hub: log in, choose the business, add and verify the number. The site gets a token that does not expire. Numbers that stay on the WhatsApp Business app are supported. |
| Use my own Meta app | Checks the token, lists its business accounts and numbers, and sets the app webhook through the Graph API. Warns when the token expires. |
| Setup steps | Check the number, register it with a two-step verification PIN, connect webhooks, sync templates, create Flow keys. Each step shows its result. |
| Tests | Send `hello_world` to a number; wait for a message from your phone. |
| Hub mode | One site (8848's) runs Embedded Signup for all sites and relays Meta's webhooks and Flow calls, signed with a secret for each site. The hub keeps no customer token. |

## Accounts and security

| Feature | Details |
| ------- | ------- |
| Several accounts | One WhatsApp Account per phone number; a default for outgoing and for incoming messages. |
| Subscribe App to Webhooks | Subscribes the Meta app to the WhatsApp Business Account. |
| Webhook signature check | With an App Secret, webhook and Flow endpoint calls without a valid `X-Hub-Signature-256` get HTTP 403 before anything is saved. WhatsApp Settings can refuse unsigned calls when no secret is set. |
| Logs | Every Graph API call and webhook call is kept in WhatsApp Log (never the token) and cleared after a set number of days. |

## Messages

| Feature | Details |
| ------- | ------- |
| Send | Text with link preview, image, document, video, audio, sticker, reaction, reply to a message, reply buttons (up to 3), lists (up to 10), templates, flows. |
| Receive | Text, media (saved as private files), reactions, replies, button and list answers, template button taps, orders, locations, contacts, flow answers; other types are kept as raw data. |
| Media uploaded to Meta | Files stored on the site are uploaded and sent as a media ID, so private files and sites that Meta cannot reach work. |
| Delivery status | Sent, delivered and read times; statuses never move back; Meta's error code and reason on failed messages; pricing category. |
| Failed sends kept | A message that Meta refuses is kept as Failed and can be sent again. |
| Read receipts | Optional, per account. |
| Duplicates | A message that Meta delivers twice is saved once. |
| Coexistence | Messages typed in the WhatsApp Business app (`smb_message_echoes`) are saved as outgoing messages. |

## Contacts and timeline

| Feature | Details |
| ------- | ------- |
| Contact linking | Incoming messages are linked to the Contact, Lead, CRM Lead or Customer with the same number (any format). |
| Lead capture | Optional: a message from a number that matches no record creates a Lead (ERPNext) or a CRM Lead (Frappe CRM) with the WhatsApp name, number, source and owner, and the message is linked to it. The next messages find the Lead, so there are no duplicates. |
| Timeline | Messages show as cards in their document's timeline; Customer, Supplier and Lead include their contacts' messages. |
| Profiles | One WhatsApp Profile per number, with the WhatsApp name and the linked Contact. |
| Opt-out | STOP / START keywords; templates, notifications and campaigns skip opted-out numbers. |
| Reply window | The 24-hour customer service window is tracked per number. |

## WhatsApp Inbox

| Feature | Details |
| ------- | ------- |
| Conversation list | One row for each customer number that wrote, newest first, with the last message, time, unread count and assignee. Tabs for Open, Pending, Closed and All, with counts. Filter by assignee; search by name or number. |
| Chat | Message history with day separators, delivery ticks, Meta's error and Retry on failed messages, quoted replies, reactions, images, video, audio and documents. |
| Real time | New messages and status changes appear without a reload (realtime event to users who can read WhatsApp Messages). |
| Reply | Text (Enter sends, Shift+Enter adds a line), reply to a message, files (image, video, audio or document by file type), templates with values for each variable. |
| Reply window | Free text and files only within 24 hours of the customer's last message; a notice shows when the window closes within two hours or is closed. |
| Quick replies | WhatsApp Quick Reply: type / and the shortcut to insert a saved answer. |
| Status and assignment | Open, Pending, Closed. A message from the customer opens a closed conversation again. Assign to a user with a WhatsApp role; the user gets a notification. |
| New message | Start a conversation with any number by sending a template. |
| Notifications | For each new message: a popup on any desk page, or a browser notification when the tab is in the background (after **Turn on desktop notifications** in the inbox). The first unread message of a conversation also adds a desk notification (bell icon). Clicking any of them opens the chat. Goes to the assigned user, else to all agents; set in WhatsApp Settings. |
| Link to the record | The chat header links to the Contact, Lead or Customer of the conversation; template variables are filled from it. |

## Auto-replies

| Feature | Details |
| ------- | ------- |
| Rules | WhatsApp Auto Reply: a trigger and a reply, for one account or all, with a priority. |
| Triggers | Keyword (whole message, contains, starts with; case does not matter), button or list reply (ID or text), first message from a number, message outside business hours, any other message. Keyword and button rules answer first. Without one, the welcome and the away rule both answer. Without those, the "any other message" rule answers. |
| Replies | Text, reply buttons (up to 3) or a list (up to 10), an approved template, a Flow, or an action. |
| Actions | Order Status (open Sales Orders with progress and delivery date) and Outstanding Balance (unpaid Sales Invoices and the total) of the Customer that wrote, found by the number. Other apps add actions with the `whatsapp_connect_auto_reply_actions` hook. |
| Business hours | WhatsApp Auto Reply Settings: hours for each day, in the system time zone. |
| Limits | Do not answer the same number again within a set time. No answer when an agent has the conversation. STOP and START are not answered. Pause all auto-replies in one place. |
| Background | Answers are sent in a background job; a failed answer is logged and the next rule still answers. |

## Send from any document

| Feature | Details |
| ------- | ------- |
| Send WhatsApp dialog | In the menu of every form: the document's and its contacts' numbers, approved templates with a preview filled from the document, free-text replies within the 24-hour window. |
| Reply link | On received messages in the timeline. |

## Templates

| Feature | Details |
| ------- | ------- |
| Create and submit | Header (text, image, document, video), body with variables and samples, footer, buttons; submitted to Meta for approval; media header samples uploaded with Meta's resumable upload. |
| Buttons | Quick reply, phone number, URL (static or dynamic), copy code, one-time password, flow, catalog, multi-product. |
| Field mapping | Variables, header and dynamic buttons filled from document fields; values cleaned for Meta's rules. |
| Sync and status | Sync all templates from Meta; status and rejection reason from the webhook. |
| Delete | Deleted in Meta; the local delete goes on when Meta refuses. |
| Live preview | The form shows the message as WhatsApp shows it. |

## Notifications

| Feature | Details |
| ------- | ------- |
| Triggers | Document events (new, save, submit, cancel, delete, value change, save after submit), days before/after a date field, schedules (hourly to yearly) with document filters. |
| Recipients | A phone field, the party's mobile number (Payment Entry, Payment Request and similar), other numbers, users with a role (with conditions; number from User or Employee). |
| Attachments | The document print as a PDF in a chosen print format, an attachment field, or a fixed file. |
| More | Python condition, variables from fields, set a field after sending, Send Now to test; sending runs in background jobs. |

## Campaigns

| Feature | Details |
| ------- | ------- |
| Recipient lists | Typed or imported from any doctype with filters, names and per-recipient values. |
| Campaigns | Values for everyone or per recipient, header file, catalog and multi-product products, send now or at a time. |
| Reliability | Background batches, rate limits retried, failed messages retried on request, opted-out recipients recorded, cancel stops sending. |
| Progress | Sent, delivered, read, failed and opted-out counts with a progress bar. |

## WhatsApp Flows

| Feature | Details |
| ------- | ------- |
| Builder | Screens and components (headings, text, text input, text area, date picker, dropdown, radio buttons, checkboxes, opt-in); Flow JSON generated; JSON can also be written directly. |
| Meta | Save (create, update, upload JSON with validation errors), publish, deprecate, delete drafts, status, preview link, import from Meta. |
| Sending | Send to a number; draft flows are sent in draft mode for testing. |
| Answers | Saved as WhatsApp Flow Response; can create a document (for example a Lead); realtime event. |
| Data endpoint | Meta's encryption (RSA-OAEP, AES-GCM), key pair generated per account, default screen logic, a hook for custom logic. |

## Reports

| Report | Details |
| ------ | ------- |
| WhatsApp Delivery Summary | Sent, delivered, read, failed and opted out with delivery and read rates, by template, campaign, account or day, with a chart. |
| WhatsApp Campaign Recipients | One row per message of a campaign. |
