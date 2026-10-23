// Copyright (c) 2026, 8848 Digital LLP and contributors
// License: MIT. See license.txt

frappe.provide("whatsapp_connect.setup");

const SETUP_DIALOG_API = "whatsapp_connect.whatsapp_connect_setup.api.v1.setup";
const INCOMING_CHECK_SECONDS = 120;

/**
 * Build the result list of the setup steps.
 *
 * @param {object} result - {account, steps, expires_at}.
 * @returns {string} Safe HTML.
 */
whatsapp_connect.setup.steps_html = function (result) {
	const esc = frappe.utils.escape_html;
	const rows = (result.steps || [])
		.map(
			(step) => `
		<div class="wac-setup-row">
			<span class="indicator-pill ${step.ok ? "green" : "red"}">${
				step.ok ? __("Done") : __("Failed")
			}</span>
			<span class="wac-setup-name">${esc(step.step)}</span>
			<span class="wac-setup-message">${esc(step.message || "")}</span>
		</div>`
		)
		.join("");
	const expiry =
		result.expires_at > 0
			? `<p class="text-warning">${__(
					"This access token expires on {0}. Use a system user token that never expires.",
					[
						esc(
							frappe.datetime.str_to_user(
								frappe.datetime.obj_to_str(new Date(result.expires_at * 1000))
							)
						),
					]
			  )}</p>`
			: "";
	return `<h4>${__("Setup of {0}", [esc(result.account || "")])}</h4>${expiry}
		<div class="wac-setup-list">${rows}</div>
		<p class="text-muted">${__(
			"Use Test on the account to send a message and check incoming messages."
		)}</p>`;
};

/**
 * Ask for the credentials of an own Meta app, find its numbers and connect one.
 *
 * @param {Function} on_done - Called with the setup result.
 * @returns {void}
 */
whatsapp_connect.setup.own_app_dialog = function (on_done) {
	let found = null;
	const dialog = new frappe.ui.Dialog({
		title: __("Use my own Meta app"),
		size: "large",
		fields: [
			{
				fieldtype: "HTML",
				options: `<p class="text-muted">${__(
					"In Meta: App settings > Basic shows the App ID and App Secret. Business Settings > System users > Generate token (never expires) with whatsapp_business_management and whatsapp_business_messaging gives the token."
				)}</p>`,
			},
			{ fieldname: "app_id", fieldtype: "Data", label: __("App ID"), reqd: 1 },
			{ fieldname: "app_secret", fieldtype: "Password", label: __("App Secret"), reqd: 1 },
			{
				fieldname: "access_token",
				fieldtype: "Password",
				label: __("Access Token"),
				reqd: 1,
			},
			{ fieldname: "number_section", fieldtype: "Section Break", hidden: 1 },
			{ fieldname: "phone_number_id", fieldtype: "Select", label: __("Phone Number") },
			{
				fieldname: "register_number",
				fieldtype: "Check",
				label: __("Register the number for the Cloud API"),
				description: __(
					"Needed once for a new number. Leave it off for a number that already sends messages."
				),
			},
		],
		primary_action_label: __("Find Numbers"),
		primary_action(values) {
			if (!found) {
				frappe
					.call({
						method: `${SETUP_DIALOG_API}.discover_numbers`,
						args: values,
						freeze: true,
					})
					.then((r) => {
						found = r.message.data;
						const options = found.accounts.flatMap((waba) =>
							waba.phone_numbers.map((n) => ({
								value: n.id,
								label: `${n.display_phone_number} (${
									n.verified_name || waba.name
								})`,
							}))
						);
						if (!options.length) {
							frappe.msgprint(
								__(
									"The business account has no phone number yet. Add one in Meta first."
								)
							);
							found = null;
							return;
						}
						dialog.set_df_property("number_section", "hidden", 0);
						dialog.set_df_property("phone_number_id", "options", options);
						dialog.set_value("phone_number_id", options[0].value);
						dialog.set_primary_action(__("Connect"), dialog.primary_action);
					});
				return;
			}
			frappe
				.call({
					method: `${SETUP_DIALOG_API}.connect_own_app`,
					args: values,
					freeze: true,
					freeze_message: __("Setting up your number..."),
				})
				.then((r) => {
					dialog.hide();
					on_done(r.message.data);
				});
		},
	});
	dialog.show();
};

/**
 * Test an account: send hello_world to a number, or wait for a message from the user's phone.
 *
 * @param {object} account - {name, display_phone_number}.
 * @returns {void}
 */
whatsapp_connect.setup.test_dialog = function (account) {
	const dialog = new frappe.ui.Dialog({
		title: __("Test {0}", [account.name]),
		fields: [
			{ fieldname: "send_section", fieldtype: "Section Break", label: __("Send a message") },
			{
				fieldname: "to",
				fieldtype: "Data",
				label: __("Send hello_world to"),
				description: __(
					"Your mobile number with the country code, for example 919876543210."
				),
			},
			{ fieldname: "send", fieldtype: "Button", label: __("Send Test Message") },
			{
				fieldname: "incoming_section",
				fieldtype: "Section Break",
				label: __("Receive a message"),
			},
			{
				fieldname: "incoming_help",
				fieldtype: "HTML",
				options: `<p>${__(
					"Send any message from your phone to {0}, then click Check Incoming.",
					[frappe.utils.escape_html(account.display_phone_number || account.name)]
				)}</p><p class="wac-incoming-status" role="status"></p>`,
			},
			{ fieldname: "check", fieldtype: "Button", label: __("Check Incoming") },
		],
	});
	dialog.fields_dict.send.$input.on("click", () => {
		const to = dialog.get_value("to");
		if (!to) return frappe.msgprint(__("Enter a number first"));
		frappe
			.call({
				method: `${SETUP_DIALOG_API}.send_test`,
				args: { account: account.name, to },
				freeze: true,
			})
			.then((r) => frappe.show_alert({ message: r.message.message, indicator: "green" }));
	});
	dialog.fields_dict.check.$input.on("click", () =>
		whatsapp_connect.setup.wait_for_incoming(account, dialog)
	);
	dialog.show();
};

/**
 * Poll for an incoming message for two minutes and show the result in the test dialog.
 *
 * @param {object} account - {name}.
 * @param {object} dialog - The test dialog.
 * @returns {void}
 */
whatsapp_connect.setup.wait_for_incoming = function (account, dialog) {
	const $status = dialog.$wrapper.find(".wac-incoming-status");
	// Messages sent a few minutes before the click count: the user sends first, then checks.
	const since = moment(frappe.datetime.now_datetime())
		.subtract(5, "minutes")
		.format("YYYY-MM-DD HH:mm:ss");
	const started = Date.now();
	$status.text(__("Waiting for your message..."));
	const poll = () => {
		frappe
			.call({
				method: `${SETUP_DIALOG_API}.check_incoming`,
				type: "GET",
				args: { account: account.name, since },
			})
			.then((r) => {
				const data = r.message.data;
				if (data.found) {
					$status.html(
						`<span class="indicator-pill green">${__(
							"Received"
						)}</span> ${frappe.utils.escape_html(
							`${data.phone_number}: ${data.body || ""}`
						)}`
					);
				} else if (Date.now() - started > INCOMING_CHECK_SECONDS * 1000) {
					$status.text(
						__(
							"No message arrived. Check the webhook in WhatsApp Log, then try again."
						)
					);
				} else if (dialog.display) {
					setTimeout(poll, 3000);
				}
			});
	};
	poll();
};
