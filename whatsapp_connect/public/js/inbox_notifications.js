// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

// Popups for new WhatsApp messages on every desk page (whatsapp_connect_inbox/notifications.py).
const NEW_MESSAGE_EVENT = "whatsapp_connect_new_message";
const POPUP_SECONDS = 8;

frappe.provide("whatsapp_connect.notifications");

/**
 * Open a conversation in the WhatsApp Inbox.
 *
 * @param {string} number - The customer's number.
 * @returns {void}
 */
whatsapp_connect.notifications.open_chat = function (number) {
	frappe.set_route("whatsapp-inbox", number);
};

/**
 * Tell if the user is looking at this conversation, so no popup is needed.
 *
 * @param {string} number - The customer's number.
 * @returns {boolean} True when the chat is open in a visible tab.
 */
whatsapp_connect.notifications.is_chat_visible = function (number) {
	const route = frappe.get_route();
	return !document.hidden && route[0] === "whatsapp-inbox" && route[1] === number;
};

/**
 * Show a new message: a desktop notification when the tab is hidden, else a popup in the desk.
 * Both open the chat when clicked.
 *
 * @param {object} data - {phone_number, title, body}.
 * @returns {void}
 */
whatsapp_connect.notifications.show = function (data) {
	if (!data || whatsapp_connect.notifications.is_chat_visible(data.phone_number)) return;
	const open = () => whatsapp_connect.notifications.open_chat(data.phone_number);

	if (document.hidden && window.Notification && Notification.permission === "granted") {
		const notification = new Notification(data.title, {
			body: data.body,
			tag: `whatsapp-${data.phone_number}`,
			icon: "/assets/whatsapp_connect/images/logo.svg",
		});
		notification.onclick = () => {
			window.focus();
			open();
			notification.close();
		};
		return;
	}

	const esc = frappe.utils.escape_html;
	const $alert = frappe.show_alert(
		{
			message: `<div class="wac-alert"><b>${esc(data.title)}</b><div class="ellipsis">${esc(
				data.body || ""
			)}</div></div>`,
			indicator: "green",
		},
		POPUP_SECONDS
	);
	if ($alert) $alert.css("cursor", "pointer").on("click", open);
};

/**
 * Ask the browser for permission to show desktop notifications.
 *
 * @returns {Promise<string>} The permission: "granted", "denied" or "default".
 */
whatsapp_connect.notifications.request_permission = function () {
	if (!window.Notification) return Promise.resolve("denied");
	return Promise.resolve(Notification.requestPermission());
};

$(document).ready(() => {
	// frappe.realtime is set up by the desk; it does not exist on website pages.
	if (frappe.realtime && frappe.session && frappe.session.user !== "Guest") {
		frappe.realtime.on(NEW_MESSAGE_EVENT, (data) => whatsapp_connect.notifications.show(data));
	}
});
