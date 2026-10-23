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

const SEND_API = "whatsapp_connect.whatsapp_connect_core.api.v1.send";
const TEMPLATE_PREVIEW_API = "whatsapp_connect.whatsapp_connect_core.api.v1.template.preview";

/**
 * Tell if the Send WhatsApp menu item makes sense on this form.
 *
 * @param {object} frm - The form.
 * @returns {boolean} False for new documents, single doctypes and the app's own doctypes.
 */
whatsapp_connect.can_send_from = function (frm) {
	return !frm.is_new() && !frm.meta.issingle && !frm.doctype.startsWith("WhatsApp ");
};

/**
 * Open the Send WhatsApp dialog for a document.
 *
 * @param {object} frm - The form of the document.
 * @param {object} [defaults] - {to, mode}; mode "Template" (default) or "Reply".
 * @returns {object} The dialog.
 */
whatsapp_connect.open_send_dialog = function (frm, defaults = {}) {
	let options = [];
	const dialog = new frappe.ui.Dialog({
		title: __("Send WhatsApp"),
		fields: [
			{
				fieldname: "to",
				label: __("To"),
				fieldtype: "Autocomplete",
				reqd: 1,
				description: __("A number of this document, or any number with the country code"),
				onchange: () => show_window_state(),
			},
			{
				fieldname: "mode",
				label: __("Send"),
				fieldtype: "Select",
				options: [
					{ value: "Template", label: __("Template") },
					{ value: "Reply", label: __("Free-text reply") },
				],
				default: defaults.mode || "Template",
				onchange: () => show_window_state(),
			},
			{ fieldname: "window_state", fieldtype: "HTML" },
			{
				fieldname: "template",
				label: __("Template"),
				fieldtype: "Link",
				options: "WhatsApp Template",
				depends_on: "eval:doc.mode=='Template'",
				mandatory_depends_on: "eval:doc.mode=='Template'",
				get_query: () => ({ filters: { status: "Approved" } }),
				onchange: () => show_preview(),
			},
			{ fieldname: "preview", fieldtype: "HTML", depends_on: "eval:doc.mode=='Template'" },
			{
				fieldname: "text",
				label: __("Message"),
				fieldtype: "Small Text",
				depends_on: "eval:doc.mode=='Reply'",
				mandatory_depends_on: "eval:doc.mode=='Reply'",
			},
		],
		primary_action_label: __("Send"),
		primary_action: (values) => send(values),
	});

	/** Show if a free-text reply is possible for the selected number. */
	function show_window_state() {
		const to = (dialog.get_value("to") || "").replace(/\D/g, "");
		const option = options.find((row) => row.number === to);
		let html = "";
		if (dialog.get_value("mode") === "Reply") {
			html =
				option && option.window_open
					? `<p class="small text-success">${__(
							"The customer wrote in the last 24 hours: you can reply with free text."
					  )}</p>`
					: `<p class="small text-warning">${__(
							"No message from this number in the last 24 hours: WhatsApp allows only templates."
					  )}</p>`;
		}
		dialog.fields_dict.window_state.$wrapper.html(html);
	}

	/** Show the selected template filled with the document's values. */
	function show_preview() {
		const template = dialog.get_value("template");
		const wrapper = dialog.fields_dict.preview.$wrapper;
		if (!template) return wrapper.empty();
		frappe.call({
			method: TEMPLATE_PREVIEW_API,
			args: { template, doctype: frm.doctype, name: frm.docname },
			callback: (r) => {
				const preview = (r.message && r.message.data) || {};
				wrapper.html(
					whatsapp_connect.bubble({
						...preview,
						body_html: whatsapp_connect.format_text(preview.body),
					})
				);
			},
		});
	}

	/** Send the template or the reply and refresh the form. */
	function send(values) {
		const reply = values.mode === "Reply";
		frappe.call({
			method: `${SEND_API}.${reply ? "send_reply_message" : "send_template_message"}`,
			args: reply
				? { to: values.to, text: values.text, doctype: frm.doctype, name: frm.docname }
				: {
						template: values.template,
						to: values.to,
						doctype: frm.doctype,
						name: frm.docname,
				  },
			freeze: true,
			freeze_message: __("Sending..."),
			callback: (r) => {
				const result = r.message || {};
				frappe.show_alert({
					message: result.message,
					indicator: result.status ? "green" : "red",
				});
				if (result.status) dialog.hide();
				frm.reload_doc();
			},
		});
	}

	frappe.call({
		method: `${SEND_API}.options`,
		args: { doctype: frm.doctype, name: frm.docname },
		callback: (r) => {
			options = (r.message && r.message.data) || [];
			dialog.set_df_property(
				"to",
				"options",
				options.map((row) => ({ value: row.number, label: row.label }))
			);
			const to = defaults.to || (options[0] && options[0].number);
			if (to) dialog.set_value("to", to);
			show_window_state();
		},
	});
	dialog.show();
	return dialog;
};

$(document).on("form-refresh", (event, frm) => {
	if (frm && whatsapp_connect.can_send_from(frm)) {
		frm.page.add_menu_item(__("Send WhatsApp"), () => whatsapp_connect.open_send_dialog(frm));
	}
});

// "Reply" on received WhatsApp messages in the form timeline (whatsapp_connect_core/messaging/timeline.py).
$(document).on("click", ".whatsapp-connect-reply", function (event) {
	event.preventDefault();
	if (window.cur_frm) {
		whatsapp_connect.open_send_dialog(window.cur_frm, {
			to: $(this).attr("data-number"),
			mode: "Reply",
		});
	}
});
