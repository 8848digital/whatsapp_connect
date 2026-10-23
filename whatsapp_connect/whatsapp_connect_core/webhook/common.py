# Copyright (c) 2026, 8848 Digital LLP and contributors
# License: MIT. See license.txt

"""Helpers shared by the webhook handlers."""

from datetime import datetime, timezone

from frappe.utils import convert_utc_to_system_timezone, now_datetime


def to_datetime(timestamp: str | int | None) -> datetime:
	"""
	Convert Meta's Unix timestamp to a naive datetime in the system time zone.

	Parameters:
	        timestamp (str | int, optional): Seconds since the epoch, as sent by Meta.

	Returns:
	        datetime: The time, or now when the timestamp is missing.
	"""
	if not timestamp:
		return now_datetime()
	utc = datetime.fromtimestamp(int(timestamp), tz=timezone.utc).replace(tzinfo=None)
	return convert_utc_to_system_timezone(utc).replace(tzinfo=None)
