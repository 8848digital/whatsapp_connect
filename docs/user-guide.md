<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# User guide

This guide shows how to use WhatsApp Connect, step by step.

## 1. Connect a WhatsApp number

1. Open **WhatsApp Setup** (type it in the search bar).
2. Click **Connect with Facebook**, log in, choose your business, add your
   number and type the code that WhatsApp sends. If you already have a Meta
   app, click **Enter App Details** instead.
3. Wait for the setup steps to show **Done**.
4. Click **Test**: send `hello_world` to your mobile, then send a message
   from your phone and click **Check Incoming**.

![WhatsApp Setup page](images/setup.png)

Details of both ways, and what each step does: [SETUP.md](../SETUP.md).

## 2. Add templates

To start a conversation, WhatsApp requires a template that Meta approved.
Free text is allowed only within 24 hours of the customer's last message.

- **To get your existing templates:** go to **WhatsApp Template** and click
  **Sync from Meta**.
- **To make a new template:**
  1. Click **Add WhatsApp Template**. Enter a name (lowercase letters, digits,
     underscores), the language code and the category.
  2. Write the text with variables `{{1}}`, `{{2}}`... and give one sample
     per line in **Samples**.
  3. Optional: set **Used With** (for example Sales Order) and, in **Values
     from Fields**, one field per line for `{{1}}`, `{{2}}`...
  4. Optional: add a header, a footer and buttons. The **Preview** shows
     the message as WhatsApp shows it.
  5. Save and click **Submit to Meta**. The status changes to **Approved**
     when Meta approves it.

![WhatsApp Template with the live preview](images/template.png)

## 3. Send from a document

Open a document (for example a Contact, Customer or Sales Invoice) and click
**⋯ > Send WhatsApp**.

1. In **To**, select a number of the document or its contacts, or type one
   with the country code.
2. Select **Template**, pick a template, check the preview, and click **Send**.

![Send WhatsApp dialog with a template](images/send-dialog.png)

To answer a customer who wrote in the last 24 hours, select **Free-text
reply**, or click **Reply** on their message in the timeline.

![Free-text reply inside the 24-hour window](images/reply-dialog.png)

## 4. Follow the conversation

Messages appear in the timeline of the document they belong to. Incoming
messages are linked to the Contact, Lead or Customer with the same number,
whatever the number format. A Customer, Supplier or Lead also shows the
messages of its contacts.

![Contact timeline with WhatsApp messages](images/timeline.png)

To make every enquiry a Lead, open **WhatsApp Settings** and select **Create a
Lead for Unknown Numbers**. A message from a number that matches no record
then creates a Lead with the customer's WhatsApp name and number. Set the
**Lead Source** and the **Lead Owner** in the same section. The owner also
gets the conversation in the WhatsApp Inbox.

### Chat in the WhatsApp Inbox

Open **WhatsApp Inbox** (type it in the search bar). The left side lists the
conversations. A conversation starts when a customer writes, or when you send
a template with **New Message**.

1. Click a conversation to open it. Its unread count goes back to zero.
2. Type a reply and press Enter. Use Shift+Enter for a new line.
3. To answer one message, point at it and click **Reply**.
4. To send a file, click the paper clip. The text you typed becomes its caption.
5. To insert a saved answer, type / and its shortcut. Add saved answers in
   **WhatsApp Quick Reply**.
6. Click **Assign** to give the conversation to a colleague. Set the status to
   **Pending** or **Closed** when you are done.

WhatsApp allows free text only within 24 hours of the customer's last
message. After that, click **Template** to send an approved template.

When a message arrives, a popup shows on any desk page, and the bell icon
gets a notification. Click either to open the chat. To get notifications
when the browser tab is in the background, click **Turn on desktop
notifications** in the inbox and allow them in the browser. The assigned
user gets the notifications. When nobody is assigned, all agents get them.
Change this in **WhatsApp Settings** > **Notify Agents of New Messages**.

![WhatsApp Inbox with a conversation open](images/inbox.png)

## 5. Send messages automatically

Go to **WhatsApp Notification** and click **Add WhatsApp Notification**.

1. **Send**: Document Event, Date Based, or Scheduled.
   - Document Event: pick the **Document Type** and **When** (New, Save,
     Submit, Cancel, Delete, Value Change, Save After Submit).
   - Date Based: pick a date field and the days after it (negative for
     days before).
   - Scheduled: pick the frequency and, optionally, document filters.
2. Optional: a **Condition**, for example `doc.status == "Paid"`.
3. Pick the **Template**.
4. **Recipients**: a phone field, **Send to the Party's Mobile Number** (for
   Payment Entry, Payment Request and other documents without a phone
   field), other numbers, or users with a role.
5. Optional: **Attach Document Print** (sent as a PDF, in the print format
   you pick), an attachment field, or a fixed file.
6. Save. Click **Send Now** to test it with one document.

![Payment receipt notification on Payment Entry](images/notification.png)

**Example — payment receipt:** Document Type *Payment Entry*, When *Submit*,
condition `doc.payment_type == "Receive"`, a template with the fields
`party_name`, `paid_amount`, `name`, Send to the Party's Mobile Number, and
Attach Document Print.

**Example — payment link:** Document Type *Payment Request*, When *Submit*,
a template with a URL button ending in `{{1}}`, and `payment_url` in the
button's **Value from Field**.

## 6. Send a campaign

1. Optional: go to **WhatsApp Recipient List**, add numbers, or set the
   import settings (document type, phone field, name field, variable fields,
   filters) and click **Import Recipients**.
2. Go to **WhatsApp Campaign** and click **Add WhatsApp Campaign**.
3. Pick the template, the recipient list or numbers, and the values:
   **Same for Everyone** or **Per Recipient**.
4. Optional: a header file, catalog products, and **Send At**.
5. Submit. Without Send At, sending starts at once.

The campaign shows its progress. Click **Refresh Progress** for the latest
delivery counts, and **Retry Failed** to send failed messages again.

![Campaign with its progress](images/campaign.png)

## 7. Build a WhatsApp Flow

1. Go to **WhatsApp Flow** and click **Add WhatsApp Flow**.
2. Add **Screens** (an ID such as `DETAILS`, and a title).
3. Add **Components**: for each, the screen ID, the type, a field name for
   answers, the label, and whether it is required.
4. Optional: in **Save Answers To**, pick a doctype (for example Lead), and set
   **Save to Field** on the components.
5. Save, then **Meta > Save to Meta**. Fix any validation errors that Meta
   reports, then **Open Preview** to try it.
6. **Meta > Publish** when it is ready (a published flow cannot be changed),
   and **Send to a Number**.

The answers are saved in **WhatsApp Flow Response**.

![WhatsApp Flow with screens and components](images/flow.png)

## 8. Check delivery

- **WhatsApp Delivery Summary** (report): sent, delivered, read, failed and
  opted-out messages with rates, by template, campaign, account or day.
- A failed message shows Meta's **Error Code** and **Error Message**; click
  **Send Again** to retry it.

![WhatsApp Delivery Summary](images/report.png)

![Failed message with Meta's reason](images/failed-message.png)

## 9. Opt-out

When a customer sends **STOP**, their **WhatsApp Profile** is marked **Opted
Out**: templates, notifications and campaigns are not sent to them, while
free-text replies are still allowed. **START** removes the opt-out.

![WhatsApp Profiles that opted out](images/opt-out.png)
