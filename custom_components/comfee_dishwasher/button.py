"""Buttons for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ComfeeDishwasherCoordinator
from .entity import ComfeeDishwasherEntity


class ComfeeDishwasherStartButton(ComfeeDishwasherEntity, ButtonEntity):
    """Start the currently selected dishwasher program."""

    entity_description = ButtonEntityDescription(
        key="start",
        translation_key="start",
        entity_registry_enabled_default=False,
    )

    def __init__(self, coordinator: ComfeeDishwasherCoordinator) -> None:
        """Initialize the start button."""
        super().__init__(coordinator, "start")

    async def async_press(self) -> None:
        """Start the selected program."""
        await self.coordinator.async_start_work()


class ComfeeDishwasherRefreshButton(ComfeeDishwasherEntity, ButtonEntity):
    """Request an immediate read-only local status update."""

    entity_description = ButtonEntityDescription(
        key="refresh",
        translation_key="refresh",
        device_class=ButtonDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
    )

    def __init__(self, coordinator: ComfeeDishwasherCoordinator) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator, "refresh")

    async def async_press(self) -> None:
        """Query current state without sending a control command."""
        await self.coordinator.async_request_device_refresh()


class ComfeeDishwasherReconnectButton(ComfeeDishwasherEntity, ButtonEntity):
    """Reconnect the authenticated local TCP socket."""

    entity_description = ButtonEntityDescription(
        key="reconnect",
        translation_key="reconnect",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.DIAGNOSTIC,
    )

    def __init__(self, coordinator: ComfeeDishwasherCoordinator) -> None:
        """Initialize the reconnect button."""
        super().__init__(coordinator, "reconnect")

    async def async_press(self) -> None:
        """Reconnect the appliance over LAN."""
        await self.coordinator.async_reconnect()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up local appliance buttons."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    entities: list[ButtonEntity] = [
        ComfeeDishwasherRefreshButton(coordinator),
        ComfeeDishwasherReconnectButton(coordinator),
    ]
    if coordinator.device_type == 0xE1 and "mode" in coordinator.data:
        entities.append(ComfeeDishwasherStartButton(coordinator))
    async_add_entities(entities)
