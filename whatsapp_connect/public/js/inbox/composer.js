// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

import { SEND_API } from "./constants";
import { short_text } from "./message_bubbles";
import { open_template_dialog } from "./template_dialog";

/** The reply box: text with quick replies, files, templates and the quoted message. */
export class Composer {
	/**
	 * Draw the reply box.
	 *
	 * @param {jQuery} $wrapper - The composer area of the chat panel.
	 * @param {object} chat - The ChatPanel, reloaded after each send.
	 */
	constructor($wrapper, chat) {
		this.$wrapper = $wrapper;
		this.chat = chat;
		this.quoted = null;
		this.quick_replies = null;
		this.$wrapper.html(`
			<div class="wac-quoted hidden">
				<span class="wac-quoted-text ellipsis"></span>
				<a class="wac-quoted-clear">${frappe.utils.icon("close", "sm")}</a>
			</div>
			<div class="wac-suggestions hidden"></div>
			<div class="wac-composer-row">
				<button class="btn btn-default btn-sm wac-attach" title="${__("Send a file")}">${frappe.utils.icon(
			"attachment",
			"sm"
		)}</button>
				<button class="btn btn-default btn-sm wac-template" title="${__("Send a template")}">${__(
			"Template"
		)}</button>
				<textarea class="form-control wac-input" rows="1" placeholder="${__(
					"Type a message. Type / for quick replies."
				)}"></textarea>
				<button class="btn btn-primary btn-sm wac-send">${__("Send")}</button>
			</div>
		`);
		this.$input = this.$wrapper.find(".wac-input");
		this.bind_events();
	}

	/**
	 * Enable or disable free text for the conversation's reply window.
	 *
	 * @param {object} conversation - The open conversation.
	 * @returns {void}
	 */
	set_conversation(conversation) {
		if (this.phone_number !== conversation.phone_number) {
			this.phone_number = conversation.phone_number;
			this.clear_quote();
			this.$input.val("");
		}
		const open = conversation.window_open;
		this.$input.prop("disabled", !open);
		this.$wrapper.find(".wac-send, .wac-attach").prop("disabled", !open);
		this.$wrapper.find(".wac-template").toggleClass("btn-primary", !open);
	}

	/**
	 * Quote a message in the next reply.
	 *
	 * @param {object} message - The message to answer.
	 * @returns {void}
	 */
	reply_to(message) {
		if (!message) return;
		this.quoted = message;
		this.$wrapper.find(".wac-quoted-text").text(short_text(message));
		this.$wrapper.find(".wac-quoted").removeClass("hidden");
		this.$input.trigger("focus");
	}

	/**
	 * Remove the quoted message.
	 *
	 * @returns {void}
	 */
	clear_quote() {
		this.quoted = null;
		this.$wrapper.find(".wac-quoted").addClass("hidden");
	}

	/**
	 * Bind send, attach, template, quick replies and Enter to send.
	 *
	 * @returns {void}
	 */
	bind_events() {
		this.$wrapper.on("click", ".wac-send", () => this.send_text());
		this.$wrapper.on("click", ".wac-attach", () => this.send_file());
		this.$wrapper.on("click", ".wac-quoted-clear", () => this.clear_quote());
		this.$wrapper.on("click", ".wac-template", () =>
			open_template_dialog({
				phone_number: this.phone_number,
				on_sent: () => this.chat.reload({ scroll: true }),
			})
		);
		this.$wrapper.on("click", ".wac-suggestion", (event) => {
			const reply = this.quick_replies[Number($(event.currentTarget).attr("data-index"))];
			this.$input.val(reply.message).trigger("focus");
			this.fit_input();
			this.hide_suggestions();
		});
		this.$input.on("keydown", (event) => {
			// Enter sends; Shift+Enter adds a line.
			if (event.key === "Enter" && !event.shiftKey) {
				event.preventDefault();
				this.send_text();
			}
		});
		this.$input.on("input", () => {
			this.fit_input();
			this.show_suggestions();
		});
	}

	/**
	 * Grow the text box with its text, up to the CSS max-height.
	 *
	 * @returns {void}
	 */
	fit_input() {
		const element = this.$input[0];
		element.style.height = "auto";
		element.style.height = `${element.scrollHeight + 2}px`;
	}

	/**
	 * Show the quick replies whose shortcut or title starts with the text after "/".
	 *
	 * @returns {void}
	 */
	show_suggestions() {
		const text = this.$input.val();
		if (!text.startsWith("/")) return this.hide_suggestions();
		this.load_quick_replies().then((replies) => {
			const search = text.slice(1).toLowerCase();
			const html = replies
				.map((reply, index) => ({ reply, index }))
				.filter(({ reply }) =>
					[reply.shortcut, reply.title].some((value) =>
						(value || "").toLowerCase().startsWith(search)
					)
				)
				.slice(0, 8)
				.map(
					({ reply, index }) => `
					<div class="wac-suggestion" data-index="${index}">
						<b>${frappe.utils.escape_html(reply.shortcut ? "/" + reply.shortcut : reply.title)}</b>
						<span class="ellipsis">${frappe.utils.escape_html(reply.message)}</span>
					</div>`
				)
				.join("");
			this.$wrapper.find(".wac-suggestions").html(html).toggleClass("hidden", !html);
		});
	}

	/**
	 * Hide the quick reply suggestions.
	 *
	 * @returns {void}
	 */
	hide_suggestions() {
		this.$wrapper.find(".wac-suggestions").addClass("hidden");
	}

	/**
	 * Load the quick replies once.
	 *
	 * @returns {Promise<object[]>} The quick replies.
	 */
	load_quick_replies() {
		if (this.quick_replies) return Promise.resolve(this.quick_replies);
		return frappe
			.call({ method: `${SEND_API}.get_quick_replies`, type: "GET" })
			.then((r) => (this.quick_replies = r.message.data || []));
	}

	/**
	 * Send the typed text, as a reply to the quoted message when there is one.
	 *
	 * @returns {void}
	 */
	send_text() {
		const text = this.$input.val().trim();
		if (!text || this.sending) return;
		this.send("send_text", { text, reply_to: this.quoted ? this.quoted.name : null }).then(
			(ok) => {
				if (!ok) return;
				this.$input.val("");
				this.fit_input();
				this.clear_quote();
			}
		);
	}

	/**
	 * Upload a file and send it, with the typed text as its caption.
	 *
	 * @returns {void}
	 */
	send_file() {
		new frappe.ui.FileUploader({
			folder: "Home/Attachments",
			make_attachments_public: false,
			allow_multiple: false,
			on_success: (file) => {
				const caption = this.$input.val().trim();
				this.send("send_file", { file_url: file.file_url, caption }).then((ok) => {
					if (ok) this.$input.val("");
				});
			},
		});
	}

	/**
	 * Call a send endpoint, show Meta's error when the send fails, and reload the chat.
	 *
	 * @param {string} method - "send_text" or "send_file".
	 * @param {object} args - Arguments besides the number.
	 * @returns {Promise<boolean>} True when Meta accepted the message.
	 */
	send(method, args) {
		this.sending = true;
		return new Promise((resolve) => {
			frappe.call({
				method: `${SEND_API}.${method}`,
				args: { phone_number: this.phone_number, ...args },
				callback: (r) => {
					const result = r.message || {};
					if (!result.status)
						frappe.show_alert({ message: result.message, indicator: "red" });
					this.chat.reload({ scroll: true });
					resolve(Boolean(result.status));
				},
				error: () => resolve(false),
				always: () => (this.sending = false),
			});
		});
	}
}
