# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Graph API calls with a token that is not stored on a WhatsApp Account (yet)."""

import frappe

from whatsapp_connect.whatsapp_connect_core.cloud_api import CloudAPI

DEFAULT_GRAPH_URL = "https://graph.facebook.com"
DEFAULT_GRAPH_VERSION = "v24.0"
WEBHOOK_PATH = "/api/method/whatsapp_connect.whatsapp_connect_core.api.v1.webhook.receive"
FLOW_ENDPOINT_PATH = "/api/method/whatsapp_connect.whatsapp_connect_flow.api.v1.endpoint.receive"


class TokenGraph(CloudAPI):
	"""The CloudAPI client, built from a token instead of a saved WhatsApp Account."""

	def __init__(
		self,
		token: str,
		graph_api_url: str | None = None,
		graph_api_version: str | None = None,
		account: str | None = None,
	):
		"""
		Keep the token and the Graph API base URL.

		Parameters:
		        token (str, required): A user, system user or app access token.
		        graph_api_url (str, optional): Default https://graph.facebook.com.
		        graph_api_version (str, optional): Default v24.0.
		        account (str, optional): WhatsApp Account to link the WhatsApp Log entries to.

		Returns:
		        None
		"""
		self.account = frappe._dict(name=account)
		self.token = token
		url = (graph_api_url or DEFAULT_GRAPH_URL).rstrip("/")
		self.base_url = f"{url}/{graph_api_version or DEFAULT_GRAPH_VERSION}"


def app_graph(app_id: str, app_secret: str, account=None) -> TokenGraph:
	"""
	Return a client that uses the app access token (App ID|App Secret).

	Parameters:
	        app_id (str, required): The Meta App ID.
	        app_secret (str, required): The Meta App Secret.
	        account (Document, optional): WhatsApp Account for the Graph API URL, version and logs.

	Returns:
	        TokenGraph: The client.
	"""
	return TokenGraph(
		f"{app_id}|{app_secret}",
		account.graph_api_url if account else None,
		account.graph_api_version if account else None,
		account.name if account else None,
	)
