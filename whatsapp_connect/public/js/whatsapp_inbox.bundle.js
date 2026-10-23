// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

// The WhatsApp Inbox page (whatsapp_connect_inbox/page/whatsapp_inbox) loads this bundle.
import { InboxPage } from "./inbox/inbox_page";

frappe.provide("whatsapp_connect.inbox");
whatsapp_connect.inbox.InboxPage = InboxPage;
