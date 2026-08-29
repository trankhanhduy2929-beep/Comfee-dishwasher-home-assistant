"""Sensors for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import MODE_NAMES, PROGRESS_NAMES, STATUS_NAMES
from .coordinator import ComfeeDishwasherCoordinator
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
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up dishwasher sensors."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    async_add_entities(
        ComfeeDishwasherSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
        if description.key in coordinator.data
    )


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
        value = self.coordinator.data.get(self.entity_description.key)
        if value in (None, "unknown"):
            return None
        return value
