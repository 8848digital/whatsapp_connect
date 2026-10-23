// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

import { ConversationList } from "./conversation_list";
import { ChatPanel } from "./chat_panel";
import { REALTIME_EVENT } from "./constants";
import { open_template_dialog } from "./template_dialog";

/** The WhatsApp Inbox: the conversation list on the left, the open chat on the right. */
export class InboxPage {
	/**
	 * Build the page and listen for new messages.
	 *
	 * @param {object} page - The Frappe app page.
	 */
	constructor(page) {
		this.page = page;
		this.$body = $(`
			<div class="wac-inbox">
				<div class="wac-inbox-list"></div>
				<div class="wac-inbox-chat"></div>
			</div>
		`).appendTo(page.main);
		this.list = new ConversationList(this.$body.find(".wac-inbox-list"), (number) =>
			this.open(number)
		);
		this.chat = new ChatPanel(this.$body.find(".wac-inbox-chat"), {
			on_change: () => this.list.refresh(),
			on_back: () => this.show_list(),
		});
		this.page.set_primary_action(__("New Message"), () => this.new_message(), "add");
		this.offer_desktop_notifications();
		this.listen();
		this.list.refresh();
	}

	/**
	 * Open the conversation named in the route, for example /app/whatsapp-inbox/919900000101.
	 *
	 * @returns {void}
	 */
	open_from_route() {
		const number = frappe.get_route()[1];
		if (number && number !== this.chat.phone_number) this.open(number);
	}

	/**
	 * Open a conversation in the chat panel.
	 *
	 * @param {string} number - The customer's number.
	 * @returns {void}
	 */
	open(number) {
		this.list.set_active(number);
		this.chat.open(number);
		this.$body.addClass("wac-inbox-chat-open");
		// Keep the open conversation in the URL without a new route render.
		window.history.replaceState(
			null,
			null,
			`/app/whatsapp-inbox/${encodeURIComponent(number)}`
		);
	}

	/**
	 * Show the list again on small screens, where only one panel fits.
	 *
	 * @returns {void}
	 */
	show_list() {
		this.$body.removeClass("wac-inbox-chat-open");
	}

	/**
	 * Start a conversation with any number by sending a template.
	 *
	 * @returns {void}
	 */
	new_message() {
		open_template_dialog({
			on_sent: (number) => {
				this.list.refresh();
				this.open(number);
			},
		});
	}

	/**
	 * Show a button that turns on desktop notifications, until the user answers the browser.
	 *
	 * @returns {void}
	 */
	offer_desktop_notifications() {
		if (!window.Notification || Notification.permission !== "default") return;
		const $button = this.page.add_button(__("Turn on desktop notifications"), () => {
			whatsapp_connect.notifications.request_permission().then(() => $button.remove());
		});
	}

	/**
	 * Refresh the list and the open chat when a message arrives or its status changes.
	 *
	 * Many events can arrive together (a campaign), so the refreshes are debounced.
	 *
	 * @returns {void}
	 */
	listen() {
		const refresh_list = frappe.utils.debounce(() => this.list.refresh(), 700);
		const refresh_chat = frappe.utils.debounce(() => this.chat.reload(), 300);
		frappe.realtime.doctype_subscribe("WhatsApp Message");
		frappe.realtime.on(REALTIME_EVENT, (data) => {
			if (!data) return;
			refresh_list();
			if (data.phone_number === this.chat.phone_number) refresh_chat();
		});
	}
}
