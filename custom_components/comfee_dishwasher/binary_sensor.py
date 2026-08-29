"""Binary sensors for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ComfeeDishwasherCoordinator
from .entity import ComfeeDishwasherEntity


BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="door",
        name="Door",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    BinarySensorEntityDescription(
        key="rinse_aid",
        name="Rinse-aid shortage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="salt",
        name="Salt shortage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="water_lack",
        name="Water shortage",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="dry_status",
        name="Drying",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="storage_status",
        name="Storage active",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up dishwasher binary sensors."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    async_add_entities(
        ComfeeDishwasherBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
        if description.key in coordinator.data
    )


class ComfeeDishwasherBinarySensor(ComfeeDishwasherEntity, BinarySensorEntity):
    """Represent a dishwasher binary sensor."""

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize a dishwasher binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return whether the condition is active."""
        value = self.coordinator.data.get(self.entity_description.key)
        return value if isinstance(value, bool) else None
