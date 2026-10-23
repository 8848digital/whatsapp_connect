# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Check the URLs that sites give to the hub, so the hub only calls public sites."""

import ipaddress
import socket
from urllib.parse import urlparse

import frappe
from frappe import _


def check_site_urls(site_url: str, other_urls: list[str], allow_insecure: bool = False) -> None:
	"""
	Check that the site URL is public and that the other URLs belong to the same site.

	Parameters:
	        site_url (str, required): The site's base URL.
	        other_urls (list[str], required): The webhook and Flow endpoint URLs of the site.
	        allow_insecure (bool, optional): Accept http:// and private addresses (testing).

	Returns:
	        None
	"""
	site = urlparse(site_url or "")
	if site.scheme not in ("https", "http") or not site.hostname:
		frappe.throw(_("The site URL {0} is not valid").format(site_url))
	if not allow_insecure:
		if site.scheme != "https":
			frappe.throw(_("The site must use https://"))
		__check_public_host(site.hostname)
	for url in other_urls:
		other = urlparse(url or "")
		if (other.scheme, other.netloc) != (site.scheme, site.netloc):
			frappe.throw(_("{0} is not on the site {1}").format(url, site_url))


def __check_public_host(hostname: str) -> None:
	"""
	Refuse host names that resolve to loopback, private or reserved addresses.

	Parameters:
	        hostname (str, required): The host name of the site.

	Returns:
	        None
	"""
	try:
		addresses = {info[4][0] for info in socket.getaddrinfo(hostname, None)}
	except socket.gaierror:
		frappe.throw(_("The site {0} cannot be found in DNS").format(hostname))
	for address in addresses:
		if not ipaddress.ip_address(address).is_global:
			frappe.throw(_("The site {0} is not on the public internet").format(hostname))
