"""Diagnostics for a supported local appliance."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_TOKEN,
)
from homeassistant.core import HomeAssistant

from .const import CONF_KEY, CONF_SERIAL_NUMBER
from .coordinator import ComfeeDishwasherCoordinator

TO_REDACT = {
    "unique_id",
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_SERIAL_NUMBER,
    CONF_TOKEN,
    CONF_KEY,
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return redacted local diagnostics for a config entry."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "connection": {
            "transport": "local_tcp",
            "ip_address": "<redacted>",
            "port": coordinator.local_port,
            "protocol": coordinator.local_protocol,
            "last_update_success": coordinator.last_update_success,
            "device_available": (coordinator.data or {}).get(
                "local_connection",
                False,
            ),
        },
        "device_attributes": dict(coordinator.data or {}),
    }
