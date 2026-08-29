"""Polling and command coordination for a Comfee dishwasher."""

import logging
from collections.abc import Callable
from datetime import timedelta
from threading import RLock
from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from midealocal.device import MideaDevice
from midealocal.devices.e1 import MideaE1Device

from .const import DOMAIN, WRITABLE_ATTRIBUTES

_LOGGER = logging.getLogger(__package__)


class ComfeeDishwasherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep one authenticated local device connection for all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: MideaDevice,
    ) -> None:
        """Initialize the coordinator."""
        self.device = device
        self._device_lock = RLock()
        self.local_port = int(entry.data.get(CONF_PORT, 6444))
        self.local_protocol = int(entry.data.get(CONF_PROTOCOL, 3))
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name="Comfee dishwasher",
            update_interval=timedelta(seconds=30),
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Read the dishwasher state over the local connection."""
        try:
            return await self.hass.async_add_executor_job(self._refresh_blocking)
        except Exception as error:
            raise UpdateFailed(f"Unable to read dishwasher state: {error}") from error

    def _refresh_blocking(self) -> dict[str, Any]:
        """Refresh state in a worker thread."""
        with self._device_lock:
            try:
                if not self.device.available:
                    if not self.device.connect(check_protocol=True):
                        raise OSError("device connection failed")
                else:
                    self.device.refresh_status(check_protocol=True)
            except Exception:
                self.device.close_socket()
                if not self.device.connect(check_protocol=True):
                    raise
            return self._state_snapshot()

    def _state_snapshot(self) -> dict[str, Any]:
        """Return device attributes plus safe derived diagnostic states."""
        attributes = {str(key): value for key, value in self.device.attributes.items()}
        error_code = attributes.get("error_code")
        wrong_operation = attributes.get("wrong_operation")
        attributes["error_active"] = bool(
            attributes.get("status") == "error"
            or isinstance(error_code, (int, float))
            and error_code != 0
        )
        attributes["operation_warning"] = bool(
            isinstance(wrong_operation, (int, float)) and wrong_operation != 0
        )
        attributes["local_connection"] = self.device.available
        return attributes

    async def async_set_attribute(self, attribute: str, value: bool) -> None:
        """Set a boolean dishwasher attribute."""
        if attribute not in WRITABLE_ATTRIBUTES:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_control",
            )
        await self._async_command(self.device.set_attribute, attribute, value)

    async def async_set_mode(self, mode: int) -> None:
        """Select and start a dishwasher program."""
        self._validate_cycle_command()
        device = cast(MideaE1Device, self.device)
        await self._async_command(device.set_work_mode, mode)

    async def async_start_work(self) -> None:
        """Start the currently selected dishwasher program."""
        self._validate_cycle_command()
        if self.data.get("mode") in (None, "none"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="program_not_selected",
            )
        device = cast(MideaE1Device, self.device)
        await self._async_command(device.start_work)

    def _validate_cycle_command(self) -> None:
        """Reject an unsafe cycle command before it reaches the appliance."""
        if not self.data.get("power"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_off",
            )
        if self.data.get("door"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="door_open",
            )
        if self.data.get("status") == "running":
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="cycle_running",
            )

    async def async_reconnect(self) -> None:
        """Reconnect and query the dishwasher over the local network."""
        try:
            data = await self.hass.async_add_executor_job(
                self._reconnect_blocking,
            )
        except Exception as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="local_connection_failed",
            ) from error
        self.async_set_updated_data(data)

    def _reconnect_blocking(self) -> dict[str, Any]:
        """Close and reopen the authenticated local socket."""
        with self._device_lock:
            self.device.close_socket()
            if not self.device.connect(check_protocol=True):
                raise OSError("device connection failed")
            return self._state_snapshot()

    async def _async_command(
        self, command: Callable[..., Any], *arguments: Any
    ) -> None:
        """Run one device command and refresh state."""
        try:
            await self.hass.async_add_executor_job(
                self._command_blocking,
                command,
                arguments,
            )
        except HomeAssistantError:
            raise
        except Exception as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="command_failed",
            ) from error
        await self.async_request_refresh()

    def _command_blocking(
        self,
        command: Callable[..., Any],
        arguments: tuple[Any, ...],
    ) -> None:
        """Run a command while holding the device lock."""
        with self._device_lock:
            if not self.device.available and not self.device.connect(
                check_protocol=True
            ):
                raise OSError("device connection failed")
            try:
                command(*arguments)
            except Exception:
                self.device.close_socket()
                self.device.set_available(False)
                raise

    def close(self) -> None:
        """Close the local socket."""
        with self._device_lock:
            self.device.close_socket()
