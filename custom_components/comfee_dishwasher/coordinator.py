"""State and command coordination for a Comfee dishwasher."""

import logging
from collections.abc import Callable, Mapping
from threading import Lock, RLock, Thread
from typing import Any, cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PORT, CONF_PROTOCOL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from midealocal.device import MideaDevice
from midealocal.devices.e1 import MideaE1Device

from .const import DOMAIN, WRITABLE_ATTRIBUTES

_LOGGER = logging.getLogger(__package__)


class ComfeeDishwasherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Bridge the local device thread to Home Assistant safely."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: MideaDevice,
    ) -> None:
        """Initialize the coordinator."""
        self.device = device
        self._device_lock = RLock()
        self._pending_lock = Lock()
        self._pending_updates: dict[str, Any] = {}
        self._update_scheduled = False
        self._callback_registered = False
        self._closing = False
        self._device_update_callback = self._handle_device_update
        self.local_port = int(entry.data.get(CONF_PORT, 6444))
        self.local_protocol = int(entry.data.get(CONF_PROTOCOL, 3))
        attributes = self.device.attributes
        initial_state = (
            {str(key): value for key, value in attributes.items()}
            if isinstance(attributes, Mapping)
            else {}
        )
        initial_state["local_connection"] = bool(self.device.available)
        self._cached_data = self._with_derived_states(initial_state)
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name="Comfee dishwasher",
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the latest state already received by the local thread."""
        return dict(self._cached_data)

    async def async_start(self) -> None:
        """Start the dependency's single background socket reader."""
        if self._callback_registered:
            return
        self.device.register_update(self._device_update_callback)
        self._callback_registered = True
        self.device.daemon = True
        try:
            await self.hass.async_add_executor_job(self.device.open)
        except Exception:
            self.device.unregister_update(self._device_update_callback)
            self._callback_registered = False
            raise

    def _handle_device_update(self, status: Mapping[Any, Any]) -> None:
        """Queue a short device-thread update for the Home Assistant loop."""
        if not isinstance(status, Mapping):
            _LOGGER.debug("Ignoring malformed dishwasher update")
            return
        update = self._normalize_device_update(status)
        if not update:
            return
        with self._pending_lock:
            if self._closing:
                return
            self._pending_updates.update(update)
            if self._update_scheduled:
                return
            self._update_scheduled = True
        try:
            self.hass.loop.call_soon_threadsafe(self._async_apply_pending_updates)
        except RuntimeError:
            with self._pending_lock:
                self._pending_updates.clear()
                self._update_scheduled = False

    @staticmethod
    def _normalize_device_update(status: Mapping[Any, Any]) -> dict[str, Any]:
        """Normalize partial dependency updates for the coordinator cache."""
        normalized: dict[str, Any] = {}
        for key, value in status.items():
            name = str(key)
            if name == "available":
                normalized["local_connection"] = bool(value)
            else:
                normalized[name] = value
        return normalized

    def _async_apply_pending_updates(self) -> None:
        """Merge one coalesced callback burst on the Home Assistant loop."""
        with self._pending_lock:
            if self._closing:
                self._pending_updates.clear()
                self._update_scheduled = False
                return
            updates = self._pending_updates
            self._pending_updates = {}
            self._update_scheduled = False
        if not updates:
            return
        data = self._with_derived_states({**self._cached_data, **updates})
        self._cached_data = data
        if data == self.data and self.last_update_success:
            return
        self.async_set_updated_data(dict(data))

    @staticmethod
    def _with_derived_states(attributes: dict[str, Any]) -> dict[str, Any]:
        """Add safe diagnostic states derived from the complete cache."""
        state = dict(attributes)
        error_code = state.get("error_code")
        wrong_operation = state.get("wrong_operation")
        state["error_active"] = bool(
            state.get("status") == "error"
            or (
                isinstance(error_code, (int, float))
                and not isinstance(error_code, bool)
                and error_code != 0
            )
        )
        state["operation_warning"] = bool(
            isinstance(wrong_operation, (int, float))
            and not isinstance(wrong_operation, bool)
            and wrong_operation != 0
        )
        return state

    async def async_request_device_refresh(self) -> None:
        """Ask the local service thread for a fresh read-only state."""
        try:
            await self.hass.async_add_executor_job(self._request_refresh_blocking)
        except Exception as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="local_connection_failed",
            ) from error

    def _request_refresh_blocking(self) -> None:
        """Send one query while leaving socket reads to the service thread."""
        with self._device_lock:
            if self._closing or not self.device.available:
                raise OSError("device is unavailable")
            try:
                self.device.refresh_status()
            except Exception:
                self._mark_unavailable_blocking()
                raise

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
        """Reset the socket so the local service thread reconnects it."""
        try:
            await self.hass.async_add_executor_job(self._reconnect_blocking)
        except Exception as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="local_connection_failed",
            ) from error

    def _reconnect_blocking(self) -> None:
        """Reset connection state without creating a competing socket reader."""
        with self._device_lock:
            if self._closing:
                raise OSError("coordinator is closing")
            self._mark_unavailable_blocking()

    async def _async_command(
        self, command: Callable[..., Any], *arguments: Any
    ) -> None:
        """Run one local command outside the Home Assistant event loop."""
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

    def _command_blocking(
        self,
        command: Callable[..., Any],
        arguments: tuple[Any, ...],
    ) -> None:
        """Send a command while the service thread owns socket reads."""
        with self._device_lock:
            if self._closing or not self.device.available:
                raise OSError("device is unavailable")
            try:
                command(*arguments)
            except Exception:
                self._mark_unavailable_blocking()
                raise

    def _mark_unavailable_blocking(self) -> None:
        """Close the current socket and publish disconnected state."""
        self.device.close_socket()
        self.device.set_available(False)

    async def async_close(self) -> None:
        """Detach callbacks and stop local networking without blocking HA."""
        with self._pending_lock:
            if self._closing:
                return
            self._closing = True
            self._pending_updates.clear()
            self._update_scheduled = False
        if self._callback_registered:
            self.device.unregister_update(self._device_update_callback)
            self._callback_registered = False
        await self.async_shutdown()
        await self.hass.async_add_executor_job(self.close)

    def close(self) -> None:
        """Stop the service thread and close the local socket."""
        with self._device_lock:
            self.device.close()
            self.device.close_socket()
            if isinstance(self.device, Thread) and self.device.is_alive():
                self.device.join(timeout=2)
