"""Binary sensors for supported Comfee/Midea-family appliances."""

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .attribute_catalog import (
    DEFAULT_ENABLED_BINARY_KEYS,
    attribute_hint,
    is_binary_attribute,
)
from .coordinator import ComfeeDishwasherCoordinator
from .device_profiles import DISHWASHER_TYPES, writable_attributes_for
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
    """Set up appliance binary sensors."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    data = coordinator.data or {}
    if coordinator.device_type in DISHWASHER_TYPES:
        descriptions = BINARY_SENSOR_DESCRIPTIONS
    else:
        shared_keys = {"error_active", "operation_warning", "local_connection"}
        descriptions = tuple(
            description
            for description in BINARY_SENSOR_DESCRIPTIONS
            if description.key in shared_keys
        )
    entities: list[BinarySensorEntity] = [
        ComfeeDishwasherBinarySensor(coordinator, description)
        for description in descriptions
        if description.key in data
        or DERIVED_SOURCE_KEYS.get(description.key) in data
        or description.key == "local_connection"
    ]
    known_keys = {description.key for description in descriptions}
    writable_keys = writable_attributes_for(coordinator.device_type)
    entities.extend(
        ComfeeGenericBinarySensor(coordinator, str(key))
        for key, value in data.items()
        if str(key) not in known_keys
        and str(key) not in writable_keys
        and is_binary_attribute(key, value)
    )
    async_add_entities(entities)


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
        value = (self.coordinator.data or {}).get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    @property
    def available(self) -> bool:
        """Keep the LAN connectivity sensor visible while disconnected."""
        if self.entity_description.key == "local_connection":
            return True
        return super().available


class ComfeeGenericBinarySensor(ComfeeDishwasherEntity, BinarySensorEntity):
    """Expose a read-only boolean attribute from any supported driver."""

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        attribute: str,
    ) -> None:
        """Initialize a generic binary sensor."""
        super().__init__(coordinator, attribute)
        self._attribute = attribute
        self._attr_entity_registry_enabled_default = (
            attribute in DEFAULT_ENABLED_BINARY_KEYS
        )
        if attribute not in DEFAULT_ENABLED_BINARY_KEYS:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC
        hint = attribute_hint(attribute)
        self._attr_name = hint.name_vi
        self._attr_icon = hint.icon
        classes = {
            "opening": BinarySensorDeviceClass.OPENING,
            "problem": BinarySensorDeviceClass.PROBLEM,
            "running": BinarySensorDeviceClass.RUNNING,
            "motion": BinarySensorDeviceClass.MOTION,
        }
        if hint.binary_device_class in classes:
            self._attr_device_class = classes[hint.binary_device_class]

    @property
    def is_on(self) -> bool | None:
        """Return the cached boolean value."""
        value = (self.coordinator.data or {}).get(self._attribute)
        return value if isinstance(value, bool) else None

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Expose the underlying local-protocol attribute name."""
        return {
            "thuoc_tinh_giao_thuc": self._attribute,
            "ma_loai_thiet_bi": f"0x{self.coordinator.device_type:02X}",
        }
