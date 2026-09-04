"""Estimated dishwasher energy and water usage tracking."""

import logging
from collections.abc import Mapping
from datetime import date, datetime, time
from math import isfinite
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    DAILY_USAGE_KEYS,
    DOMAIN,
    ESTIMATED_ENERGY_LAST_CYCLE,
    ESTIMATED_ENERGY_THIS_MONTH,
    ESTIMATED_ENERGY_TODAY,
    ESTIMATED_WATER_LAST_CYCLE,
    ESTIMATED_WATER_THIS_MONTH,
    ESTIMATED_WATER_TODAY,
    LAST_CYCLE_USAGE_KEYS,
    MODE_NAMES,
    MONTHLY_USAGE_KEYS,
    PROGRAM_USAGE_ESTIMATES,
    USAGE_ESTIMATE_SOURCE,
    USAGE_REFERENCE_MODEL,
)

_LOGGER = logging.getLogger(__package__)

STORAGE_VERSION = 1
SAVE_DELAY_SECONDS = 15


class DishwasherUsageTracker:
    """Track fixed per-program usage estimates without polling the appliance."""

    def __init__(self, hass: HomeAssistant, device_id: str) -> None:
        """Initialize an empty usage tracker."""
        now = dt_util.now()
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.usage_{device_id}",
            private=True,
            atomic_writes=True,
        )
        self._initialized = False
        self._day = self._day_key(now)
        self._month = self._month_key(now)
        self._estimated_energy_last_cycle: float | None = None
        self._estimated_water_last_cycle: float | None = None
        self._estimated_energy_today = 0.0
        self._estimated_water_today = 0.0
        self._estimated_energy_this_month = 0.0
        self._estimated_water_this_month = 0.0
        self._cycle_active = False
        self._active_cycle_mode: str | None = None
        self._last_status: str | None = None
        self._last_progress: str | None = None
        self._last_cycle_mode: str | None = None
        self._last_cycle_completed_at: str | None = None
        self._last_cycle_counted: bool | None = None

    @property
    def initialized(self) -> bool:
        """Return whether persistent state has been loaded."""
        return self._initialized

    @property
    def sensor_values(self) -> dict[str, float | None]:
        """Return values exposed by Home Assistant sensors."""
        return {
            ESTIMATED_ENERGY_LAST_CYCLE: self._estimated_energy_last_cycle,
            ESTIMATED_WATER_LAST_CYCLE: self._estimated_water_last_cycle,
            ESTIMATED_ENERGY_TODAY: self._estimated_energy_today,
            ESTIMATED_WATER_TODAY: self._estimated_water_today,
            ESTIMATED_ENERGY_THIS_MONTH: self._estimated_energy_this_month,
            ESTIMATED_WATER_THIS_MONTH: self._estimated_water_this_month,
        }

    async def async_initialize(
        self,
        initial_state: Mapping[str, Any],
        now: datetime | None = None,
    ) -> None:
        """Load saved totals and reconcile them with the current device state."""
        if self._initialized:
            return
        current_time = self._local_time(now)
        try:
            stored = await self._store.async_load()
        except Exception:
            stored = None
            _LOGGER.warning(
                "Unable to load saved dishwasher usage estimates",
                exc_info=True,
            )
        if isinstance(stored, Mapping):
            self._restore(stored, current_time)
        self._rollover(current_time)
        self._initialized = True
        restored_cycle_active = self._cycle_active
        restored_progress = self._last_progress
        current_progress = self._state_from_mapping(
            initial_state, "progress", restored_progress
        )
        current_status = self._state_from_mapping(
            initial_state, "status", self._last_status
        )
        if (
            restored_cycle_active
            and current_progress == "complete"
            and restored_progress == "complete"
            and current_status not in {"cancel", "error"}
        ):
            self._complete_cycle(
                self._active_cycle_mode or self._usable_mode(initial_state.get("mode")),
                current_time,
            )
            self._schedule_save(0)
        self.process_state(initial_state, current_time)

    @callback
    def process_state(
        self,
        state: Mapping[str, Any],
        now: datetime | None = None,
    ) -> bool:
        """Process one complete cached appliance state."""
        current_time = self._local_time(now)
        changed = self._rollover(current_time)
        status = self._state_from_mapping(state, "status", self._last_status)
        progress = self._state_from_mapping(state, "progress", self._last_progress)
        mode = self._usable_mode(state.get("mode"))
        save_immediately = False

        if status not in {"cancel", "error"} and (
            (status == "running" and progress != "complete")
            or progress in {"pre_wash", "wash", "rinse", "dry"}
        ):
            if not self._cycle_active:
                self._cycle_active = True
                changed = True
                save_immediately = True
            if mode is not None and mode != self._active_cycle_mode:
                self._active_cycle_mode = mode
                changed = True
                save_immediately = True

        if (
            self._cycle_active
            and progress == "complete"
            and self._last_progress != "complete"
            and status not in {"cancel", "error"}
        ):
            self._complete_cycle(self._active_cycle_mode or mode, current_time)
            changed = True
            save_immediately = True
        elif self._cycle_active and (
            status in {"cancel", "error"}
            or (status == "off" and progress in {None, "idle"})
        ):
            self._cycle_active = False
            self._active_cycle_mode = None
            changed = True
            save_immediately = True

        if status != self._last_status:
            self._last_status = status
            changed = True
        if progress != self._last_progress:
            self._last_progress = progress
            changed = True

        if changed and self._initialized:
            self._schedule_save(0 if save_immediately else SAVE_DELAY_SECONDS)
        return changed

    @callback
    def rollover(self, now: datetime | None = None) -> bool:
        """Reset day or month totals when the local period changes."""
        changed = self._rollover(self._local_time(now))
        if changed and self._initialized:
            self._schedule_save(0)
        return changed

    def period_start(self, sensor_key: str) -> datetime | None:
        """Return the local reset time for a period sensor."""
        timezone = dt_util.get_default_time_zone()
        if sensor_key in DAILY_USAGE_KEYS:
            return datetime.combine(date.fromisoformat(self._day), time(), timezone)
        if sensor_key in MONTHLY_USAGE_KEYS:
            year, month = (int(part) for part in self._month.split("-", 1))
            return datetime(year, month, 1, tzinfo=timezone)
        return None

    def attributes_for(self, sensor_key: str) -> dict[str, Any]:
        """Return compact metadata explaining the estimated sensor value."""
        attributes: dict[str, Any] = {
            "estimated": True,
            "estimate_source": USAGE_ESTIMATE_SOURCE,
            "reference_model": USAGE_REFERENCE_MODEL,
            "reference_warning": "Reference profile, not a device meter",
            "known_programs": sorted(PROGRAM_USAGE_ESTIMATES),
        }
        if sensor_key in LAST_CYCLE_USAGE_KEYS:
            attributes.update(
                {
                    "program": self._last_cycle_mode,
                    "last_cycle_mode": self._last_cycle_mode,
                    "completed_at": self._last_cycle_completed_at,
                    "counted_in_totals": self._last_cycle_counted,
                }
            )
        elif period_start := self.period_start(sensor_key):
            attributes["period_start"] = period_start.isoformat()
        return attributes

    async def async_shutdown(self) -> None:
        """Flush pending state before the integration unloads."""
        if not self._initialized:
            return
        try:
            await self._store.async_save(self._serialize())
        except Exception:
            _LOGGER.warning(
                "Unable to save dishwasher usage estimates",
                exc_info=True,
            )
        finally:
            self._initialized = False

    def _complete_cycle(self, mode: str | None, now: datetime) -> None:
        """Record one completed cycle when a reference profile is available."""
        estimate = PROGRAM_USAGE_ESTIMATES.get(mode or "")
        self._last_cycle_mode = mode
        self._last_cycle_completed_at = now.isoformat()
        self._last_cycle_counted = estimate is not None
        self._cycle_active = False
        self._active_cycle_mode = None
        if estimate is None:
            self._estimated_energy_last_cycle = None
            self._estimated_water_last_cycle = None
            return
        self._estimated_energy_last_cycle = estimate.energy_kwh
        self._estimated_water_last_cycle = estimate.water_liters
        self._estimated_energy_today = self._round_energy(
            self._estimated_energy_today + estimate.energy_kwh
        )
        self._estimated_water_today = self._round_water(
            self._estimated_water_today + estimate.water_liters
        )
        self._estimated_energy_this_month = self._round_energy(
            self._estimated_energy_this_month + estimate.energy_kwh
        )
        self._estimated_water_this_month = self._round_water(
            self._estimated_water_this_month + estimate.water_liters
        )

    def _rollover(self, now: datetime) -> bool:
        """Apply local daily and monthly boundaries."""
        changed = False
        day = self._day_key(now)
        month = self._month_key(now)
        if day != self._day:
            self._day = day
            self._estimated_energy_today = 0.0
            self._estimated_water_today = 0.0
            changed = True
        if month != self._month:
            self._month = month
            self._estimated_energy_this_month = 0.0
            self._estimated_water_this_month = 0.0
            changed = True
        return changed

    def _restore(self, stored: Mapping[str, Any], now: datetime) -> None:
        """Restore validated values from Home Assistant storage."""
        current_day = self._day_key(now)
        current_month = self._month_key(now)
        stored_day = self._stored_day(stored.get("day"))
        stored_month = self._stored_month(stored.get("month"))
        self._day = stored_day or current_day
        self._month = stored_month or current_month
        self._estimated_energy_last_cycle = self._optional_number(
            stored.get(ESTIMATED_ENERGY_LAST_CYCLE)
        )
        self._estimated_water_last_cycle = self._optional_number(
            stored.get(ESTIMATED_WATER_LAST_CYCLE)
        )
        self._estimated_energy_today = self._number(stored.get(ESTIMATED_ENERGY_TODAY))
        self._estimated_water_today = self._number(stored.get(ESTIMATED_WATER_TODAY))
        self._estimated_energy_this_month = self._number(
            stored.get(ESTIMATED_ENERGY_THIS_MONTH)
        )
        self._estimated_water_this_month = self._number(
            stored.get(ESTIMATED_WATER_THIS_MONTH)
        )
        if stored_day is None:
            self._estimated_energy_today = 0.0
            self._estimated_water_today = 0.0
        if stored_month is None:
            self._estimated_energy_this_month = 0.0
            self._estimated_water_this_month = 0.0
        self._cycle_active = stored.get("cycle_active") is True
        self._active_cycle_mode = self._optional_string(stored.get("active_cycle_mode"))
        self._last_status = self._optional_string(stored.get("last_status"))
        self._last_progress = self._optional_string(stored.get("last_progress"))
        self._last_cycle_mode = self._optional_string(stored.get("last_cycle_mode"))
        self._last_cycle_completed_at = self._optional_string(
            stored.get("last_cycle_completed_at")
        )
        counted = stored.get("last_cycle_counted")
        self._last_cycle_counted = counted if isinstance(counted, bool) else None

    def _serialize(self) -> dict[str, Any]:
        """Serialize state for Home Assistant storage."""
        return {
            "day": self._day,
            "month": self._month,
            **self.sensor_values,
            "cycle_active": self._cycle_active,
            "active_cycle_mode": self._active_cycle_mode,
            "last_status": self._last_status,
            "last_progress": self._last_progress,
            "last_cycle_mode": self._last_cycle_mode,
            "last_cycle_completed_at": self._last_cycle_completed_at,
            "last_cycle_counted": self._last_cycle_counted,
        }

    @callback
    def _schedule_save(self, delay: float) -> None:
        """Coalesce small state changes into one storage write."""
        self._store.async_delay_save(self._serialize, delay)

    @staticmethod
    def _local_time(value: datetime | None) -> datetime:
        """Normalize an optional timestamp to Home Assistant local time."""
        if value is None:
            return dt_util.now()
        return dt_util.as_local(value)

    @staticmethod
    def _day_key(value: datetime) -> str:
        """Return a stable local day key."""
        return value.date().isoformat()

    @staticmethod
    def _month_key(value: datetime) -> str:
        """Return a stable local month key."""
        return value.strftime("%Y-%m")

    @staticmethod
    def _usable_mode(value: Any) -> str | None:
        """Normalize a selected program name."""
        if isinstance(value, int) and not isinstance(value, bool):
            value = MODE_NAMES.get(value)
        if not isinstance(value, str):
            return None
        normalized = value.strip().lower().replace(" ", "_")
        return normalized if normalized and normalized != "none" else None

    @staticmethod
    def _state_string(value: Any, fallback: str | None) -> str | None:
        """Use a valid state string or retain the previous value."""
        if not isinstance(value, str):
            return fallback
        normalized = value.strip().lower()
        return normalized or fallback

    @staticmethod
    def _state_from_mapping(
        state: Mapping[str, Any], key: str, fallback: str | None
    ) -> str | None:
        """Read a state while distinguishing an omitted value from null."""
        if key not in state:
            return fallback
        return DishwasherUsageTracker._state_string(state[key], None)

    @staticmethod
    def _optional_string(value: Any) -> str | None:
        """Validate an optional stored string."""
        return value if isinstance(value, str) else None

    @staticmethod
    def _number(value: Any) -> float:
        """Validate a non-negative stored number."""
        number = DishwasherUsageTracker._optional_number(value)
        return number if number is not None else 0.0

    @staticmethod
    def _optional_number(value: Any) -> float | None:
        """Validate an optional non-negative stored number."""
        if (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and isfinite(value)
            and value >= 0
        ):
            return float(value)
        return None

    @staticmethod
    def _stored_day(value: Any) -> str | None:
        """Validate a stored ISO day key."""
        if not isinstance(value, str):
            return None
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return None

    @staticmethod
    def _stored_month(value: Any) -> str | None:
        """Validate a stored ISO month key."""
        if not isinstance(value, str):
            return None
        try:
            parsed = date.fromisoformat(f"{value}-01")
        except ValueError:
            return None
        return parsed.strftime("%Y-%m")

    @staticmethod
    def _round_energy(value: float) -> float:
        """Keep accumulated energy stable at watt-hour precision."""
        return round(value, 3)

    @staticmethod
    def _round_water(value: float) -> float:
        """Keep accumulated water stable at deciliter precision."""
        return round(value, 1)
