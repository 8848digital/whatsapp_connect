# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

import frappe

from whatsapp_connect.whatsapp_connect_core.webhook.signature import SIGNATURE_HEADER
from whatsapp_connect.whatsapp_connect_flow import endpoint


# nosemgrep: frappe-semgrep-rules.rules.security.guest-whitelisted-method -- Meta calls the Flow endpoint without a session; the request is signed (X-Hub-Signature-256) and encrypted with the account's Flow key
@frappe.whitelist(allow_guest=True, methods=["POST"])
def receive():
	"""
	Data endpoint for WhatsApp Flows that use one. Meta sends an encrypted request
	when the flow opens or moves to another screen; the answer is encrypted too.

	**Endpoint:** `/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.endpoint.receive`
	**HTTP Method:** POST
	**Parameters:**
	        - encrypted_flow_data (str, required): Base64 AES-GCM encrypted request
	        - encrypted_aes_key (str, required): Base64 RSA-OAEP encrypted AES key
	        - initial_vector (str, required): Base64 IV
	        - X-Hub-Signature-256 (header, required when an App Secret is set)
	**Response:**
	Plain text: the base64 encrypted answer (200). 403 for a bad signature,
	421 when no Flow key can decrypt the request (Meta then refreshes the key).
	"""
	return endpoint.handle_request(
		frappe.request.get_data(cache=True), frappe.request.headers.get(SIGNATURE_HEADER)
	)
