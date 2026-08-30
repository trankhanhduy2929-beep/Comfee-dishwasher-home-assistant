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

DERIVED_SOURCE_KEYS = {
    "error_active": "error_code",
    "operation_warning": "wrong_operation",
}

BINARY_SENSOR_DESCRIPTIONS = (
    BinarySensorEntityDescription(
        key="door",
        translation_key="door",
        device_class=BinarySensorDeviceClass.OPENING,
    ),
    BinarySensorEntityDescription(
        key="rinse_aid",
        translation_key="rinse_aid",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="salt",
        translation_key="salt",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="water_lack",
        translation_key="water_lack",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="dry_status",
        translation_key="dry_status",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="storage_status",
        translation_key="storage_status",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="uv",
        translation_key="uv",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="dry",
        translation_key="dry",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="waterswitch",
        translation_key="waterswitch",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="error_active",
        translation_key="error_active",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="operation_warning",
        translation_key="operation_warning",
        device_class=BinarySensorDeviceClass.PROBLEM,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="local_connection",
        translation_key="local_connection",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
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
        or DERIVED_SOURCE_KEYS.get(description.key) in coordinator.data
        or description.key == "local_connection"
    )


class ComfeeDishwasherBinarySensor(ComfeeDishwasherEntity, BinarySensorEntity):
    """Represent a dishwasher binary sensor."""

    entity_description: BinarySensorEntityDescription

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
        if self.entity_description.key == "local_connection":
            return bool(self.coordinator.data.get("local_connection", False))
        source_key = DERIVED_SOURCE_KEYS.get(self.entity_description.key)
        if source_key is not None:
            value = self.coordinator.data.get(self.entity_description.key)
            if isinstance(value, bool):
                return value
            source_value = self.coordinator.data.get(source_key)
            return (
                bool(source_value)
                if isinstance(source_value, (int, float))
                and not isinstance(source_value, bool)
                else None
            )
        value = self.coordinator.data.get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        """Keep the LAN connectivity sensor visible while disconnected."""
        if self.entity_description.key == "local_connection":
            return True
        return super().available
