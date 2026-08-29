"""Sensors for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import ComfeeDishwasherCoordinator
from .entity import ComfeeDishwasherEntity


SENSOR_DESCRIPTIONS = (
    SensorEntityDescription(
        key="status",
        name="Status",
        device_class=SensorDeviceClass.ENUM,
        options=["off", "cancel", "delay", "running", "error", "soft_gear"],
    ),
    SensorEntityDescription(
        key="mode",
        name="Wash program",
        device_class=SensorDeviceClass.ENUM,
        options=[
            "none",
            "auto_wash",
            "strong_wash",
            "standard_wash",
            "eco_wash",
            "glass_wash",
            "hour_wash",
            "fast_wash",
            "soak_wash",
            "90min",
            "self_clean",
            "fruit_wash",
            "self_define",
            "germ",
            "bowl_wash",
            "kill_germ",
            "sea_food_wash",
            "hot_pot_wash",
            "quiet_night_wash",
            "less_wash",
            "oil_net_wash",
            "cloud_wash",
        ],
    ),
    SensorEntityDescription(
        key="progress",
        name="Progress",
        device_class=SensorDeviceClass.ENUM,
        options=["idle", "pre_wash", "wash", "rinse", "dry", "complete"],
    ),
    SensorEntityDescription(
        key="time_remaining",
        name="Time remaining",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="temperature",
        name="Water temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="error_code",
        name="Error code",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="bright",
        name="Rinse-aid level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="softwater",
        name="Water-softener level",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    SensorEntityDescription(
        key="storage_remaining",
        name="Storage remaining",
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
