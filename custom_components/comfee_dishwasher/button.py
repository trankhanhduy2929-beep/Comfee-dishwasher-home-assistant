"""Buttons for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ComfeeDishwasherCoordinator
from .entity import ComfeeDishwasherEntity


class ComfeeDishwasherStartButton(ComfeeDishwasherEntity, ButtonEntity):
    """Start the currently selected dishwasher program."""

    entity_description = ButtonEntityDescription(
        key="start",
        name="Start current program",
        entity_registry_enabled_default=False,
    )

    def __init__(self, coordinator: ComfeeDishwasherCoordinator) -> None:
        """Initialize the start button."""
        super().__init__(coordinator, "start")

    async def async_press(self) -> None:
        """Start the selected program."""
        await self.coordinator.async_start_work()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the start button."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    async_add_entities([ComfeeDishwasherStartButton(coordinator)])
