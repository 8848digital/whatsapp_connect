// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.pages["whatsapp-inbox"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("WhatsApp Inbox"),
		single_column: true,
	});
	frappe.require(
		["whatsapp_inbox.bundle.js", "/assets/whatsapp_connect/css/whatsapp_inbox.css"],
		() => {
			wrapper.whatsapp_inbox = new whatsapp_connect.inbox.InboxPage(page);
			wrapper.whatsapp_inbox.open_from_route();
		}
	);
};

frappe.pages["whatsapp-inbox"].on_page_show = function (wrapper) {
	if (wrapper.whatsapp_inbox) wrapper.whatsapp_inbox.open_from_route();
};
