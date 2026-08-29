"""Switches for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ComfeeDishwasherCoordinator
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
    """Set up dishwasher switches."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    async_add_entities(
        ComfeeDishwasherSwitch(coordinator, description)
        for description in SWITCH_DESCRIPTIONS
        if description.key in coordinator.data
    )


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
        value = self.coordinator.data.get(self.entity_description.key)
        return value if isinstance(value, bool) else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_set_attribute(self.entity_description.key, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_set_attribute(self.entity_description.key, False)
