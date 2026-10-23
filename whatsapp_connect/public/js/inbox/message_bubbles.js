// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

const TICKS = { Sent: "✓", Delivered: "✓✓", Read: "✓✓" };
const TYPE_LABELS = {
	location: __("Location"),
	contacts: __("Contact"),
	order: __("Order"),
	flow: __("Flow answers"),
	unsupported: __("Message type not supported"),
};

/**
 * Build the HTML of all messages of a conversation, with day separators.
 *
 * Reactions are shown under the message they react to, not as messages.
 *
 * @param {object[]} messages - Messages from get_conversation, oldest first.
 * @returns {string} HTML of the message area.
 */
export function messages_html(messages) {
	const by_wamid = {};
	const reactions = {};
	messages.forEach((message) => {
		if (message.wamid) by_wamid[message.wamid] = message;
		if (message.message_type === "reaction" && message.reply_to_wamid) {
			(reactions[message.reply_to_wamid] = reactions[message.reply_to_wamid] || []).push(
				message.reaction_emoji
			);
		}
	});

	let last_day = null;
	return messages
		.filter((message) => message.message_type !== "reaction")
		.map((message) => {
			const day = frappe.datetime.str_to_user(
				local_time(message.creation).format("YYYY-MM-DD")
			);
			const separator = day !== last_day ? `<div class="wac-day">${day}</div>` : "";
			last_day = day;
			return separator + bubble_html(message, by_wamid, reactions[message.wamid] || []);
		})
		.join("");
}

/**
 * Build one message bubble.
 *
 * @param {object} message - A message row.
 * @param {object} by_wamid - Loaded messages by Meta's ID, for quoted replies.
 * @param {string[]} emojis - Reactions to this message.
 * @returns {string} HTML of the bubble.
 */
function bubble_html(message, by_wamid, emojis) {
	const esc = frappe.utils.escape_html;
	const outgoing = message.direction === "Outgoing";
	const quoted = by_wamid[message.reply_to_wamid];
	const quote = quoted ? `<div class="wac-quote">${esc(short_text(quoted))}</div>` : "";
	const reaction = emojis.length
		? `<div class="wac-reactions">${emojis.map(esc).join(" ")}</div>`
		: "";
	const source =
		outgoing && message.source
			? `<span class="wac-meta-source" title="${esc(message.source)}">${esc(
					message.source
			  )}</span>`
			: "";
	return `
		<div class="wac-msg ${outgoing ? "wac-msg-out" : "wac-msg-in"}" data-name="${esc(message.name)}">
			<div class="wac-msg-bubble">
				${quote}
				${content_html(message)}
				<div class="wac-msg-meta">${source}<span>${local_time(message.creation).format("HH:mm")}</span>${
		outgoing ? status_html(message) : ""
	}</div>
			</div>
			${reaction}
			${outgoing ? "" : `<a class="wac-msg-reply" data-name="${esc(message.name)}">${__("Reply")}</a>`}
		</div>`;
}

/**
 * Build the content of a bubble for its message type.
 *
 * @param {object} message - A message row.
 * @returns {string} HTML of the content.
 */
function content_html(message) {
	if (message.message_type === "template") {
		const header = message.template_header
			? `<b>${frappe.utils.escape_html(message.template_header)}</b><br>`
			: "";
		const footer = message.template_footer
			? `<div class="wac-footer">${frappe.utils.escape_html(message.template_footer)}</div>`
			: "";
		const text = message.template_text || __("Template: {0}", [message.template]);
		return `${header}${whatsapp_connect.format_text(text)}${footer}`;
	}
	const media = media_html(message);
	const label = TYPE_LABELS[message.message_type];
	const body = message.body ? whatsapp_connect.format_text(message.body) : "";
	if (!media && !body && label) return `<i class="text-muted">${label}</i>`;
	return `${media}${media && body ? "<div class='wac-caption'>" : ""}${body}${
		media && body ? "</div>" : ""
	}${options_html(message)}`;
}

/**
 * Build the media part of a bubble: the picture, the player or a file link.
 *
 * @param {object} message - A message row.
 * @returns {string} HTML, or "" for messages without media.
 */
function media_html(message) {
	const esc = frappe.utils.escape_html;
	const kind = message.message_type;
	if (!["image", "video", "audio", "document", "sticker"].includes(kind)) return "";
	if (!message.attachment)
		return `<div class="wac-media">${__("Loading {0}...", [__(kind)])}</div>`;

	const url = esc(message.attachment);
	if (kind === "image" || kind === "sticker") {
		return `<a href="${url}" target="_blank"><img class="wac-msg-image" src="${url}" alt=""></a>`;
	}
	if (kind === "video")
		return `<video class="wac-msg-video" src="${url}" controls preload="metadata"></video>`;
	if (kind === "audio") return `<audio src="${url}" controls preload="none"></audio>`;
	return `<a class="wac-msg-file" href="${url}" target="_blank">${frappe.utils.icon(
		"file",
		"sm"
	)}<span>${esc(message.filename || __("Document"))}</span></a>`;
}

/**
 * Build the buttons or list rows of an outgoing interactive message.
 *
 * @param {object} message - A message row.
 * @returns {string} HTML, or "" when the message has no options.
 */
function options_html(message) {
	if (message.message_type !== "interactive" || !message.interactive_options) return "";
	let options = message.interactive_options;
	if (typeof options === "string") {
		try {
			options = JSON.parse(options);
		} catch (error) {
			return "";
		}
	}
	const labels = (Array.isArray(options) ? options : []).map((option) => option.title || option);
	return labels
		.map((label) => `<div class="wac-button">${frappe.utils.escape_html(String(label))}</div>`)
		.join("");
}

/**
 * Build the delivery ticks of an outgoing message, or its error.
 *
 * @param {object} message - An outgoing message row.
 * @returns {string} HTML of the status.
 */
function status_html(message) {
	const esc = frappe.utils.escape_html;
	if (message.status === "Failed" || message.status === "Opted Out") {
		const retry =
			message.status === "Failed"
				? ` <a class="wac-msg-retry" data-name="${esc(message.name)}">${__("Retry")}</a>`
				: "";
		return `<span class="wac-tick wac-tick-failed" title="${esc(
			message.error_message || __(message.status)
		)}">${__(message.status)}</span>${retry}`;
	}
	const read = message.status === "Read" ? "wac-tick-read" : "";
	return `<span class="wac-tick ${read}" title="${esc(__(message.status))}">${
		TICKS[message.status] || "…"
	}</span>`;
}

/**
 * Return a short text of a message for a quote.
 *
 * @param {object} message - A message row.
 * @returns {string} Plain text.
 */
export function short_text(message) {
	const text = message.body || message.template_text || __(message.message_type);
	return text.length > 120 ? `${text.slice(0, 119)}…` : text;
}

/**
 * Return a server time as a moment in the user's time zone.
 *
 * @param {string} value - A datetime from the server.
 * @returns {object} The moment.
 */
function local_time(value) {
	return moment(frappe.datetime.convert_to_user_tz(value));
}
