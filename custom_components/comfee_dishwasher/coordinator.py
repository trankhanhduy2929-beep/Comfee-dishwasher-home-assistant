"""Polling and command coordination for a Comfee dishwasher."""

from collections.abc import Callable
from datetime import timedelta
import logging
from threading import RLock
from typing import Any, cast

from midealocal.device import MideaDevice
from midealocal.devices.e1 import MideaE1Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN

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
            return dict(self.device.attributes)

    async def async_set_attribute(self, attribute: str, value: bool) -> None:
        """Set a boolean dishwasher attribute."""
        await self._async_command(self.device.set_attribute, attribute, value)

    async def async_set_mode(self, mode: int) -> None:
        """Select and start a dishwasher program."""
        device = cast(MideaE1Device, self.device)
        await self._async_command(device.set_work_mode, mode)

    async def async_start_work(self) -> None:
        """Start the currently selected dishwasher program."""
        if not self.data.get("power"):
            raise HomeAssistantError(
                "Turn on the dishwasher before starting a wash cycle",
            )
        device = cast(MideaE1Device, self.device)
        await self._async_command(device.start_work)

    async def _async_command(self, command: Callable[..., Any], *arguments: Any) -> None:
        """Run one device command and refresh state."""
        try:
            await self.hass.async_add_executor_job(
                self._command_blocking,
                command,
                arguments,
            )
        except Exception as error:
            raise HomeAssistantError(
                "Unable to send the command to the dishwasher",
            ) from error
        await self.async_request_refresh()

    def _command_blocking(
        self,
        command: Callable[..., Any],
        arguments: tuple[Any, ...],
    ) -> None:
        """Run a command while holding the device lock."""
        with self._device_lock:
            if not self.device.available and not self.device.connect(check_protocol=True):
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
