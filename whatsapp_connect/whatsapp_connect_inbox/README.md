<!-- Copyright (c) 2026, 8848 Digital LLP and contributors. License: MIT. See license.txt -->

# WhatsApp Connect Inbox

## Purpose

The WhatsApp Inbox page: agents chat with customers from one screen. It
lists the conversations, shows the messages, and sends text, files and
templates. It also sets the status and the assignee of a conversation.

A conversation is a WhatsApp Profile with a conversation status. The core
module keeps the last message, the unread count and the status up to date
(`whatsapp_connect_core/messaging/conversation.py`) and sends a realtime
event for each new message and status change.

`notifications.py` tells agents about new messages (an incoming handler): a
realtime popup (`public/js/inbox_notifications.js`, on every desk page) and a
desk notification (Notification Log) that links to the chat.

## DocTypes

| DocType | Purpose |
| ------- | ------- |
| WhatsApp Quick Reply | A saved answer. Agents type / and its shortcut in the inbox to insert it. |

## Pages

- **WhatsApp Inbox** (`/app/whatsapp-inbox`): the conversation list (Open, Pending, Closed, All; filter by assignee; search) and the chat. `/app/whatsapp-inbox/<number>` opens one conversation.
