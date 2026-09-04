"""Comfee dishwasher integration using the Midea local protocol."""

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_MODEL,
    CONF_NAME,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_TOKEN,
    CONF_TYPE,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError, ConfigEntryNotReady
from midealocal.const import ProtocolVersion
from midealocal.device import MideaDevice
from midealocal.devices import device_selector
from midealocal.discover import discover

from .const import (
    CONF_KEY,
    CONF_MAC,
    CONF_SERIAL_NUMBER,
    CONF_SUBTYPE,
    DEVICE_TYPE_DISHWASHER,
)
from .coordinator import ComfeeDishwasherCoordinator

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


def _create_device(data: Mapping[str, Any]) -> MideaDevice | None:
    """Create the E1 device implementation from a config entry."""
    return device_selector(
        name=data[CONF_NAME],
        device_id=data[CONF_DEVICE_ID],
        device_type=data[CONF_TYPE],
        ip_address=data[CONF_IP_ADDRESS],
        port=data[CONF_PORT],
        token=data[CONF_TOKEN],
        key=data[CONF_KEY],
        device_protocol=ProtocolVersion(data[CONF_PROTOCOL]),
        model=data[CONF_MODEL],
        subtype=data.get(CONF_SUBTYPE, 0),
        customize="",
        mac=data.get(CONF_MAC),
        serial_number=data.get(CONF_SERIAL_NUMBER),
    )


def _connect_device(device: MideaDevice) -> bool:
    """Connect to the device and close any failed socket."""
    connected = device.connect(check_protocol=True)
    if not connected:
        device.close_socket()
    return connected


def _discover_current_ip(device_id: int) -> str | None:
    """Find the current address of a configured dishwasher."""
    info = discover().get(device_id)
    if info is None or int(info.get(CONF_TYPE, 0)) != DEVICE_TYPE_DISHWASHER:
        return None
    ip_address = info.get(CONF_IP_ADDRESS)
    return str(ip_address) if ip_address else None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Comfee dishwasher config entry."""
    data = dict(entry.data)
    device = await hass.async_add_executor_job(_create_device, data)
    if device is None:
        raise ConfigEntryError("The configured device is not an E1 dishwasher")

    connected = await hass.async_add_executor_job(_connect_device, device)
    if not connected:
        current_ip = await hass.async_add_executor_job(
            _discover_current_ip,
            int(data[CONF_DEVICE_ID]),
        )
        if current_ip and current_ip != data[CONF_IP_ADDRESS]:
            await hass.async_add_executor_job(device.set_ip_address, current_ip)
            connected = await hass.async_add_executor_job(_connect_device, device)
            if connected:
                data[CONF_IP_ADDRESS] = current_ip
                hass.config_entries.async_update_entry(entry, data=data)
    if not connected:
        raise ConfigEntryNotReady("Unable to authenticate with the dishwasher")

    coordinator = ComfeeDishwasherCoordinator(hass, entry, device)

    async def _close_device() -> None:
        await coordinator.async_close()

    entry.async_on_unload(_close_device)
    try:
        await coordinator.async_initialize_usage()
        await coordinator.async_config_entry_first_refresh()
        await coordinator.async_start()
    except Exception as error:
        await _close_device()
        raise ConfigEntryNotReady("Unable to read the dishwasher state") from error

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Comfee dishwasher config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
