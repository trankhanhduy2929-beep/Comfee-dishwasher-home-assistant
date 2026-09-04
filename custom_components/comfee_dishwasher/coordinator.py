"""State and command coordination for a supported local appliance."""

import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from threading import Lock, RLock, Thread
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DEVICE_ID, CONF_PORT, CONF_PROTOCOL, CONF_TYPE
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from midealocal.device import MideaDevice
from midealocal.devices.e1 import MideaE1Device

from .const import DOMAIN
from .device_profiles import get_device_profile, writable_attributes_for
from .usage import DishwasherUsageTracker

_LOGGER = logging.getLogger(__package__)
_USAGE_UPDATE_KEYS = frozenset({"status", "progress", "mode"})
_MAX_PENDING_USAGE_UPDATES = 64


class ComfeeDishwasherCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Bridge one local Midea-family device thread to Home Assistant safely."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: MideaDevice,
    ) -> None:
        """Initialize the coordinator."""
        self.device = device
        self.device_type = int(entry.data.get(CONF_TYPE, 0xE1))
        self.profile = get_device_profile(self.device_type)
        self._device_lock = RLock()
        self._pending_lock = Lock()
        self._pending_updates: dict[str, Any] = {}
        self._pending_usage_updates: list[dict[str, Any]] = []
        self._update_scheduled = False
        self._callback_registered = False
        self._closing = False
        self._remove_usage_rollover: CALLBACK_TYPE | None = None
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
        self.usage = (
            DishwasherUsageTracker(
                hass,
                str(entry.data.get(CONF_DEVICE_ID, self.device.device_id)),
            )
            if self.device_type == 0xE1
            else None
        )
        if self.usage is not None:
            initial_state.update(self.usage.sensor_values)
        self._cached_data = self._with_derived_states(initial_state)
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name="Comfee/Midea local appliance",
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Return the latest state already received by the local thread."""
        if self.usage is not None and self.usage.rollover():
            self._cached_data.update(self.usage.sensor_values)
        return dict(self._cached_data)

    async def async_initialize_usage(self) -> None:
        """Load persisted usage before entities are created."""
        if self.usage is None:
            return
        await self.usage.async_initialize(self._cached_data)
        self._cached_data = {
            **self._cached_data,
            **self.usage.sensor_values,
        }

    async def async_start(self) -> None:
        """Start the dependency's single background socket reader."""
        if self._callback_registered:
            return
        await self.async_initialize_usage()
        if self.data is not None and self._cached_data != self.data:
            self.async_set_updated_data(dict(self._cached_data))
        try:
            self.device.register_update(self._device_update_callback)
            self._callback_registered = True
            self.device.daemon = True
            if self.usage is not None:
                self._remove_usage_rollover = async_track_time_change(
                    self.hass,
                    self._async_rollover_usage,
                    hour=0,
                    minute=0,
                    second=0,
                )
            await self.hass.async_add_executor_job(self.device.open)
        except Exception:
            if self._callback_registered:
                self.device.unregister_update(self._device_update_callback)
                self._callback_registered = False
            if self._remove_usage_rollover is not None:
                self._remove_usage_rollover()
                self._remove_usage_rollover = None
            raise

    def _handle_device_update(self, status: Mapping[Any, Any]) -> None:
        """Queue a short device-thread update for the Home Assistant loop."""
        if not isinstance(status, Mapping):
            _LOGGER.debug("Ignoring malformed local-appliance update")
            return
        update = self._normalize_device_update(status)
        if not update:
            return
        with self._pending_lock:
            if self._closing:
                return
            self._pending_updates.update(update)
            usage_update = (
                {
                    key: value
                    for key, value in update.items()
                    if key in _USAGE_UPDATE_KEYS
                }
                if self.usage is not None
                else {}
            )
            if usage_update:
                self._pending_usage_updates.append(usage_update)
                if len(self._pending_usage_updates) > _MAX_PENDING_USAGE_UPDATES:
                    del self._pending_usage_updates[:-_MAX_PENDING_USAGE_UPDATES]
            if self._update_scheduled:
                return
            self._update_scheduled = True
        try:
            self.hass.loop.call_soon_threadsafe(self._async_apply_pending_updates)
        except RuntimeError:
            with self._pending_lock:
                self._pending_updates.clear()
                self._pending_usage_updates.clear()
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
                self._pending_usage_updates.clear()
                self._update_scheduled = False
                return
            updates = self._pending_updates
            self._pending_updates = {}
            usage_updates = self._pending_usage_updates
            self._pending_usage_updates = []
            self._update_scheduled = False
        if not updates:
            return
        base_data = dict(self._cached_data)
        if usage_updates and self.usage is not None:
            usage_state = dict(base_data)
            for usage_update in usage_updates:
                usage_state.update(usage_update)
                self.usage.process_state(usage_state)
        data = self._with_derived_states({**base_data, **updates})
        if self.usage is not None:
            data.update(self.usage.sensor_values)
        self._cached_data = data
        if data == self.data and self.last_update_success:
            return
        self.async_set_updated_data(dict(data))

    @callback
    def _async_rollover_usage(self, now: datetime) -> None:
        """Publish local day and month resets without polling the appliance."""
        if self._closing or self.usage is None or not self.usage.rollover(now):
            return
        data = {**self._cached_data, **self.usage.sensor_values}
        self._cached_data = data
        if data != self.data or not self.last_update_success:
            self.async_set_updated_data(dict(data))

    @staticmethod
    def _with_derived_states(attributes: dict[str, Any]) -> dict[str, Any]:
        """Add safe diagnostic states derived from the complete cache."""
        state = dict(attributes)
        state["error_active"] = bool(
            state.get("status") == "error"
            or ComfeeDishwasherCoordinator._diagnostic_value_is_active(
                state.get("error_code"),
            )
            or ComfeeDishwasherCoordinator._diagnostic_value_is_active(
                state.get("error"),
            )
            or ComfeeDishwasherCoordinator._diagnostic_value_is_active(
                state.get("fault"),
            )
        )
        state["operation_warning"] = (
            ComfeeDishwasherCoordinator._diagnostic_value_is_active(
                state.get("wrong_operation"),
            )
        )
        return state

    @staticmethod
    def _diagnostic_value_is_active(value: Any) -> bool:
        """Normalize common numeric, boolean and text diagnostic values."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().casefold().replace("_", " ")
            return normalized not in {
                "",
                "0",
                "false",
                "no error",
                "none",
                "normal",
                "ok",
                "unknown",
            }
        return False

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

    async def async_set_attribute(
        self,
        attribute: str,
        value: bool | float | str,
    ) -> None:
        """Set one explicitly allow-listed attribute outside the event loop."""
        allowed = writable_attributes_for(self.device_type)
        if attribute not in allowed or attribute not in self._cached_data:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_control",
            )
        await self._async_command(self.device.set_attribute, attribute, value)

    async def async_set_mode(self, mode: int) -> None:
        """Select and start a dishwasher program."""
        if not isinstance(self.device, MideaE1Device):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_control",
            )
        self._validate_cycle_command()
        await self._async_command(self.device.set_work_mode, mode)

    async def async_start_work(self) -> None:
        """Start the currently selected dishwasher program."""
        if not isinstance(self.device, MideaE1Device):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_control",
            )
        self._validate_cycle_command()
        if not self.data or self.data.get("mode") in (None, "none"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="program_not_selected",
            )
        await self._async_command(self.device.start_work)

    def _validate_cycle_command(self) -> None:
        """Reject an unsafe cycle command before it reaches the appliance."""
        data = self.data or self._cached_data
        if not data.get("power"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="device_off",
            )
        if data.get("door"):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="door_open",
            )
        if data.get("status") == "running":
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
        if self._remove_usage_rollover is not None:
            self._remove_usage_rollover()
            self._remove_usage_rollover = None
        if self.usage is not None:
            await self.usage.async_shutdown()
        await self.async_shutdown()
        await self.hass.async_add_executor_job(self.close)

    def close(self) -> None:
        """Stop the service thread and close the local socket."""
        with self._device_lock:
            self.device.close()
            self.device.close_socket()
            if isinstance(self.device, Thread) and self.device.is_alive():
                self.device.join(timeout=2)
