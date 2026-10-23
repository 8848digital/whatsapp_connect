// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

import { Composer } from "./composer";
import { INBOX_API } from "./constants";
import { messages_html } from "./message_bubbles";

const STATUSES = ["Open", "Pending", "Closed"];
const RETRY_API = "whatsapp_connect.whatsapp_connect_core.api.v1.message.retry";
// Warn the agent when the 24-hour window closes within this many minutes.
const WINDOW_WARNING_MINUTES = 120;

/** The right panel: the open conversation, its actions and the reply box. */
export class ChatPanel {
	/**
	 * Show the empty state until a conversation is opened.
	 *
	 * @param {jQuery} $wrapper - The chat panel.
	 * @param {object} callbacks - {on_change, on_back}.
	 */
	constructor($wrapper, callbacks) {
		this.$wrapper = $wrapper;
		this.callbacks = callbacks;
		this.phone_number = null;
		this.agents = null;
		this.$wrapper.html(`<div class="wac-empty">${__("Select a conversation")}</div>`);
		this.bind_events();
	}

	/**
	 * Open a conversation and mark it as read.
	 *
	 * @param {string} number - The customer's number.
	 * @returns {Promise} Resolves when the chat is drawn.
	 */
	open(number) {
		this.phone_number = number;
		this.messages = [];
		return this.reload({ scroll: true });
	}

	/**
	 * Load the open conversation again, for example after a new message.
	 *
	 * @param {object} [options] - {scroll}: scroll to the newest message.
	 * @returns {Promise} Resolves when the chat is drawn.
	 */
	reload(options = {}) {
		if (!this.phone_number) return Promise.resolve();
		const number = this.phone_number;
		return frappe
			.call({
				method: `${INBOX_API}.get_conversation`,
				type: "GET",
				args: { phone_number: number },
			})
			.then((r) => {
				if (number !== this.phone_number) return;
				const near_bottom = this.is_near_bottom();
				this.data = r.message.data;
				this.messages = this.data.messages;
				this.render();
				if (options.scroll || near_bottom) this.scroll_to_bottom();
				if (this.data.conversation.unread_count) this.mark_read();
			});
	}

	/**
	 * Draw the header, the messages and the reply box.
	 *
	 * @returns {void}
	 */
	render() {
		const conversation = this.data.conversation;
		if (!this.$header) {
			this.$wrapper.html(`
				<div class="wac-chat-header"></div>
				<div class="wac-chat-messages"></div>
				<div class="wac-chat-window"></div>
				<div class="wac-chat-composer"></div>
			`);
			this.$header = this.$wrapper.find(".wac-chat-header");
			this.$messages = this.$wrapper.find(".wac-chat-messages");
			this.composer = new Composer(this.$wrapper.find(".wac-chat-composer"), this);
		}
		this.$header.html(this.header_html(conversation));
		this.$messages.html(messages_html(this.messages));
		this.$wrapper.find(".wac-chat-window").html(this.window_html(conversation));
		this.composer.set_conversation(conversation);
	}

	/**
	 * Build the header: name, number, linked record, assignee and status.
	 *
	 * @param {object} conversation - The conversation.
	 * @returns {string} HTML of the header.
	 */
	header_html(conversation) {
		const esc = frappe.utils.escape_html;
		const reference = this.data.reference;
		const link = reference
			? `<a href="/app/${frappe.router.slug(reference.doctype)}/${encodeURIComponent(
					reference.name
			  )}">${esc(__(reference.doctype))}: ${esc(reference.name)}</a>`
			: "";
		const statuses = STATUSES.map(
			(status) =>
				`<option value="${status}" ${
					status === conversation.conversation_status ? "selected" : ""
				}>${__(status)}</option>`
		).join("");
		const opted_out = conversation.opted_out
			? `<span class="indicator-pill red">${__("Opted out")}</span>`
			: "";
		return `
			<button class="btn btn-xs btn-default wac-chat-back">${frappe.utils.icon("left", "sm")}</button>
			<div class="wac-avatar">${esc(frappe.get_abbr(conversation.display_name))}</div>
			<div class="wac-chat-title">
				<div class="wac-chat-name ellipsis">${esc(conversation.display_name)} ${opted_out}</div>
				<div class="wac-chat-sub ellipsis">+${esc(conversation.phone_number)} ${
			link ? "· " + link : ""
		}</div>
			</div>
			<div class="wac-chat-actions">
				<button class="btn btn-xs btn-default wac-assign">${
					conversation.assigned_to_name
						? esc(conversation.assigned_to_name)
						: __("Assign")
				}</button>
				<select class="form-control input-xs wac-status">${statuses}</select>
			</div>`;
	}

	/**
	 * Build the reply window notice: closed, or closing soon.
	 *
	 * @param {object} conversation - The conversation.
	 * @returns {string} HTML of the notice, or "" while the window is open for a while.
	 */
	window_html(conversation) {
		if (!conversation.window_open) {
			return `<div class="wac-window wac-window-closed">${__(
				"The customer has not written in the last 24 hours. Send a template to continue."
			)}</div>`;
		}
		const minutes = conversation.window_minutes_left;
		if (minutes > WINDOW_WARNING_MINUTES) return "";
		return `<div class="wac-window wac-window-soon">${__(
			"The reply window closes in {0} minutes.",
			[minutes]
		)}</div>`;
	}

	/**
	 * Bind the header buttons and the reply links once.
	 *
	 * @returns {void}
	 */
	bind_events() {
		this.$wrapper.on("click", ".wac-chat-back", () => this.callbacks.on_back());
		this.$wrapper.on("change", ".wac-status", (event) =>
			this.set_status($(event.target).val())
		);
		this.$wrapper.on("click", ".wac-assign", () => this.choose_assignee());
		this.$wrapper.on("click", ".wac-msg-retry", (event) => {
			frappe
				.call({
					method: RETRY_API,
					args: { message: $(event.currentTarget).attr("data-name") },
				})
				.then(() => this.reload());
		});
		this.$wrapper.on("click", ".wac-msg-reply", (event) => {
			const name = $(event.currentTarget).attr("data-name");
			this.composer.reply_to(this.messages.find((message) => message.name === name));
		});
	}

	/**
	 * Set the conversation status.
	 *
	 * @param {string} status - Open, Pending or Closed.
	 * @returns {void}
	 */
	set_status(status) {
		this.call("set_status", { status }).then(() => this.callbacks.on_change());
	}

	/**
	 * Ask for the user to assign, then assign the conversation.
	 *
	 * @returns {void}
	 */
	choose_assignee() {
		const agents = this.agents
			? Promise.resolve(this.agents)
			: frappe
					.call({ method: `${INBOX_API}.get_agents`, type: "GET" })
					.then((r) => (this.agents = r.message.data));
		agents.then((rows) => {
			const dialog = new frappe.ui.Dialog({
				title: __("Assign conversation"),
				fields: [
					{
						fieldname: "user",
						label: __("User"),
						fieldtype: "Select",
						options: [
							{ value: "", label: __("Nobody") },
							...rows.map((row) => ({
								value: row.name,
								label: row.full_name || row.name,
							})),
						],
						default: this.data.conversation.assigned_to || frappe.session.user,
					},
				],
				primary_action_label: __("Assign"),
				primary_action: (values) => {
					dialog.hide();
					this.call("assign", { user: values.user || "" }).then(() => {
						this.reload();
						this.callbacks.on_change();
					});
				},
			});
			dialog.show();
		});
	}

	/**
	 * Set the unread count to zero.
	 *
	 * @returns {void}
	 */
	mark_read() {
		this.call("mark_read").then(() => this.callbacks.on_change());
	}

	/**
	 * Call an inbox endpoint for the open conversation.
	 *
	 * @param {string} method - The endpoint name in the inbox API.
	 * @param {object} [args] - Arguments besides the number.
	 * @returns {Promise} The call.
	 */
	call(method, args = {}) {
		return frappe.call({
			method: `${INBOX_API}.${method}`,
			args: { phone_number: this.phone_number, ...args },
		});
	}

	/**
	 * Tell if the message area shows the newest message.
	 *
	 * @returns {boolean} True when scrolled to (near) the bottom.
	 */
	is_near_bottom() {
		const element = this.$messages && this.$messages[0];
		return !element || element.scrollHeight - element.scrollTop - element.clientHeight < 80;
	}

	/**
	 * Scroll the message area to the newest message.
	 *
	 * @returns {void}
	 */
	scroll_to_bottom() {
		const element = this.$messages[0];
		element.scrollTop = element.scrollHeight;
	}
}
