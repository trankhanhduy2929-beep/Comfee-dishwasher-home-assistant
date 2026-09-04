"""Sensors for supported Comfee/Midea-family appliances."""

import json
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    REVOLUTIONS_PER_MINUTE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .attribute_catalog import (
    DEFAULT_ENABLED_SENSOR_KEYS,
    attribute_hint,
    is_binary_attribute,
    is_scalar_attribute,
)
from .const import (
    ESTIMATED_ENERGY_LAST_CYCLE,
    ESTIMATED_ENERGY_THIS_MONTH,
    ESTIMATED_ENERGY_TODAY,
    ESTIMATED_WATER_LAST_CYCLE,
    ESTIMATED_WATER_THIS_MONTH,
    ESTIMATED_WATER_TODAY,
    MODE_NAMES,
    PROGRESS_NAMES,
    STATUS_NAMES,
    USAGE_SENSOR_KEYS,
)
from .coordinator import ComfeeDishwasherCoordinator
from .device_profiles import DISHWASHER_TYPES, writable_attributes_for
from .entity import ComfeeDishwasherEntity

SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="status",
        translation_key="status",
        device_class=SensorDeviceClass.ENUM,
        options=list(STATUS_NAMES),
    ),
    SensorEntityDescription(
        key="mode",
        translation_key="mode",
        device_class=SensorDeviceClass.ENUM,
        options=list(MODE_NAMES.values()),
    ),
    SensorEntityDescription(
        key="progress",
        translation_key="progress",
        device_class=SensorDeviceClass.ENUM,
        options=list(PROGRESS_NAMES),
    ),
    SensorEntityDescription(
        key="time_remaining",
        translation_key="time_remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="error_code",
        translation_key="error_code",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="additional",
        translation_key="additional_code",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="wrong_operation",
        translation_key="wrong_operation",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="bright",
        translation_key="rinse_aid_level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="softwater",
        translation_key="softwater_level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="storage_remaining",
        translation_key="storage_remaining",
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key=ESTIMATED_ENERGY_LAST_CYCLE,
        translation_key=ESTIMATED_ENERGY_LAST_CYCLE,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=ESTIMATED_WATER_LAST_CYCLE,
        translation_key=ESTIMATED_WATER_LAST_CYCLE,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=ESTIMATED_ENERGY_TODAY,
        translation_key=ESTIMATED_ENERGY_TODAY,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=ESTIMATED_WATER_TODAY,
        translation_key=ESTIMATED_WATER_TODAY,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
    ),
    SensorEntityDescription(
        key=ESTIMATED_ENERGY_THIS_MONTH,
        translation_key=ESTIMATED_ENERGY_THIS_MONTH,
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=3,
    ),
    SensorEntityDescription(
        key=ESTIMATED_WATER_THIS_MONTH,
        translation_key=ESTIMATED_WATER_THIS_MONTH,
        device_class=SensorDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.LITERS,
        state_class=SensorStateClass.TOTAL,
        suggested_display_precision=1,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up appliance sensors."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    data = coordinator.data or {}
    if coordinator.device_type == 0xE1:
        descriptions = SENSOR_DESCRIPTIONS
    elif coordinator.device_type in DISHWASHER_TYPES:
        descriptions = tuple(
            description
            for description in SENSOR_DESCRIPTIONS
            if description.key not in {"status", "mode"}
            and description.key not in USAGE_SENSOR_KEYS
        )
    else:
        descriptions = ()
    entities: list[SensorEntity] = [
        (
            ComfeeDishwasherUsageSensor(coordinator, description)
            if description.key in USAGE_SENSOR_KEYS
            else ComfeeDishwasherSensor(coordinator, description)
        )
        for description in descriptions
        if description.key in data
    ]
    known_keys = {description.key for description in descriptions}
    known_keys.update({"local_connection", "error_active", "operation_warning"})
    writable_keys = writable_attributes_for(coordinator.device_type)
    entities.extend(
        ComfeeGenericAttributeSensor(coordinator, str(key))
        for key, value in data.items()
        if str(key) not in known_keys
        and str(key) not in writable_keys
        and not is_binary_attribute(key, value)
        and is_scalar_attribute(value)
    )
    async_add_entities(entities)


class ComfeeDishwasherSensor(ComfeeDishwasherEntity, SensorEntity):
    """Represent a dishwasher sensor."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize a dishwasher sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the current sensor value."""
        value = (self.coordinator.data or {}).get(self.entity_description.key)
        if value in (None, "unknown"):
            return None
        return value


class ComfeeDishwasherUsageSensor(ComfeeDishwasherSensor):
    """Represent a persisted dishwasher usage estimate."""

    @property
    def available(self) -> bool:
        """Keep stored totals available when the appliance is offline."""
        return self.coordinator.data is not None

    @property
    def last_reset(self) -> datetime | None:
        """Return the start of the current local day or month."""
        usage = self.coordinator.usage
        return usage.period_start(self.entity_description.key) if usage else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Explain that the value is an estimate, not a device meter."""
        usage = self.coordinator.usage
        return usage.attributes_for(self.entity_description.key) if usage else {}


class ComfeeGenericAttributeSensor(ComfeeDishwasherEntity, SensorEntity):
    """Expose a scalar attribute for device families without a special entity."""

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        attribute: str,
    ) -> None:
        """Initialize a generic read-only attribute sensor."""
        super().__init__(coordinator, attribute)
        self._attribute = attribute
        self._attr_entity_registry_enabled_default = (
            attribute in DEFAULT_ENABLED_SENSOR_KEYS
        )
        if attribute not in DEFAULT_ENABLED_SENSOR_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        hint = attribute_hint(attribute)
        self._attr_name = hint.name_vi
        self._attr_icon = hint.icon
        value = (coordinator.data or {}).get(attribute)
        if not isinstance(value, (list, tuple, dict)):
            self._apply_hint(hint)

    def _apply_hint(self, hint: Any) -> None:
        """Apply optional Home Assistant sensor metadata."""
        units = {
            "percentage": PERCENTAGE,
            "temperature": UnitOfTemperature.CELSIUS,
            "energy": UnitOfEnergy.KILO_WATT_HOUR,
            "power": UnitOfPower.WATT,
            "volume": UnitOfVolume.LITERS,
            "volume_flow_rate": UnitOfVolumeFlowRate.LITERS_PER_MINUTE,
            "kelvin": UnitOfTemperature.KELVIN,
            "minutes": UnitOfTime.MINUTES,
            "days": UnitOfTime.DAYS,
            "seconds": UnitOfTime.SECONDS,
            "current": UnitOfElectricCurrent.AMPERE,
            "voltage": UnitOfElectricPotential.VOLT,
            "frequency": UnitOfFrequency.HERTZ,
            "rpm": REVOLUTIONS_PER_MINUTE,
            "ppm": "ppm",
            "density": "μg/m³",
        }
        device_classes = {
            "temperature": SensorDeviceClass.TEMPERATURE,
            "humidity": SensorDeviceClass.HUMIDITY,
            "energy": SensorDeviceClass.ENERGY,
            "power": SensorDeviceClass.POWER,
            "volume": SensorDeviceClass.VOLUME,
            "water": SensorDeviceClass.WATER,
            "volume_flow_rate": SensorDeviceClass.VOLUME_FLOW_RATE,
            "duration": SensorDeviceClass.DURATION,
            "pm25": getattr(SensorDeviceClass, "PM25", None),
            "co2": getattr(SensorDeviceClass, "CO2", None),
            "tvoc": getattr(
                SensorDeviceClass,
                "VOLATILE_ORGANIC_COMPOUNDS_PARTS",
                None,
            ),
            "hcho": getattr(SensorDeviceClass, "VOLATILE_ORGANIC_COMPOUNDS", None),
            "current": getattr(SensorDeviceClass, "CURRENT", None),
            "voltage": getattr(SensorDeviceClass, "VOLTAGE", None),
            "frequency": getattr(SensorDeviceClass, "FREQUENCY", None),
        }
        if hint.unit in units:
            self._attr_native_unit_of_measurement = units[hint.unit]
        device_class = device_classes.get(hint.sensor_device_class)
        if device_class is not None:
            self._attr_device_class = device_class
        if hint.state_class == "measurement":
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif hint.state_class == "total_increasing":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING

    @property
    def native_value(self) -> StateType:
        """Return the cached raw attribute in a state-safe form."""
        value = (self.coordinator.data or {}).get(self._attribute)
        if value is None or value == "unknown":
            return None
        if isinstance(value, (list, tuple, dict)):
            try:
                encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
            except (TypeError, ValueError):
                encoded = str(value)
            return encoded[:255]
        if isinstance(value, (str, int, float)):
            return value
        return str(value)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose protocol metadata without putting it into the state value."""
        return {
            "thuoc_tinh_giao_thuc": self._attribute,
            "ma_loai_thiet_bi": f"0x{self.coordinator.device_type:02X}",
        }
