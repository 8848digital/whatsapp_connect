// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.provide("whatsapp_connect");

/**
 * Render text the way WhatsApp shows it: *bold*, _italic_, ~strike~, line breaks.
 * HTML in the text is escaped first.
 *
 * @param {string} text - The message text.
 * @param {string[]} [samples] - Values for {{1}}, {{2}}...; highlighted when given.
 * @returns {string} Safe HTML.
 */
whatsapp_connect.format_text = function (text, samples) {
	let html = frappe.utils.escape_html(text || "");
	if (samples) {
		html = html.replace(/\{\{(\d+)\}\}/g, (match, number) => {
			const value = samples[Number(number) - 1];
			return `<span class="wac-variable">${frappe.utils.escape_html(
				value ? value : match
			)}</span>`;
		});
	}
	return html
		.replace(/\*([^*\n]+)\*/g, "<b>$1</b>")
		.replace(/_([^_\n]+)_/g, "<i>$1</i>")
		.replace(/~([^~\n]+)~/g, "<s>$1</s>")
		.replace(/\n/g, "<br>");
};

/**
 * Build the HTML of a message bubble.
 *
 * @param {object} message - {header, header_type, body_html, footer, buttons}.
 * @returns {string} HTML of the chat background with one bubble.
 */
whatsapp_connect.bubble = function (message) {
	const esc = frappe.utils.escape_html;
	let header = "";
	if (message.header_type === "Text" && message.header) {
		header = `<div><b>${esc(message.header)}</b></div>`;
	} else if (["Image", "Document", "Video"].includes(message.header_type)) {
		header = `<div class="wac-media">${esc(__(message.header_type))}</div>`;
	}
	const footer = message.footer ? `<div class="wac-footer">${esc(message.footer)}</div>` : "";
	const buttons = (message.buttons || [])
		.map((label) => `<div class="wac-button">${esc(label)}</div>`)
		.join("");
	return `<div class="wac-chat"><div class="wac-bubble">${header}<div>${message.body_html}</div>${footer}${buttons}</div></div>`;
};
