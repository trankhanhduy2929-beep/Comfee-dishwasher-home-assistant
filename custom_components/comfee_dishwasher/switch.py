"""Switches for supported Comfee/Midea-family appliances."""

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .attribute_catalog import attribute_hint
from .coordinator import ComfeeDishwasherCoordinator
from .device_profiles import writable_attributes_for
from .entity import ComfeeDishwasherEntity

SWITCH_DESCRIPTIONS = (
    SwitchEntityDescription(
        key="power",
        translation_key="power",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="child_lock",
        translation_key="child_lock",
        device_class=SwitchDeviceClass.SWITCH,
    ),
    SwitchEntityDescription(
        key="storage",
        translation_key="storage",
        device_class=SwitchDeviceClass.SWITCH,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up allow-listed local appliance switches."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    data = coordinator.data or {}
    writable_keys = writable_attributes_for(coordinator.device_type)
    entities: list[SwitchEntity] = [
        ComfeeDishwasherSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
        if description.key in data and description.key in writable_keys
    ]
    known_keys = {description.key for description in SWITCH_DESCRIPTIONS}
    entities.extend(
        ComfeeGenericSwitch(coordinator, attribute)
        for attribute in sorted(writable_keys)
        if attribute in data and attribute not in known_keys
    )
    async_add_entities(entities)


class ComfeeDishwasherSwitch(ComfeeDishwasherEntity, SwitchEntity):
    """Represent a dishwasher switch."""

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize a dishwasher switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return the switch state."""
        value = (self.coordinator.data or {}).get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_set_attribute(self.entity_description.key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_set_attribute(self.entity_description.key, False)


class ComfeeGenericSwitch(ComfeeDishwasherEntity, SwitchEntity):
    """Expose an allow-listed boolean control for another device family."""

    _attr_entity_registry_enabled_default = False

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        attribute: str,
    ) -> None:
        """Initialize a conservative generic switch."""
        super().__init__(coordinator, attribute)
        self._attribute = attribute
        hint = attribute_hint(attribute)
        self._attr_name = hint.name_vi
        self._attr_icon = hint.icon

    @property
    def is_on(self) -> bool | None:
        """Return the cached switch state."""
        value = (self.coordinator.data or {}).get(self._attribute)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the allow-listed attribute over LAN."""
        await self.coordinator.async_set_attribute(self._attribute, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the allow-listed attribute over LAN."""
        await self.coordinator.async_set_attribute(self._attribute, False)
