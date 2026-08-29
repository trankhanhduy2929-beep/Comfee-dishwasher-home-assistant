"""Shared entities for the Comfee dishwasher integration."""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ComfeeDishwasherCoordinator


class ComfeeDishwasherEntity(CoordinatorEntity[ComfeeDishwasherCoordinator]):
    """Base entity for a local Comfee dishwasher."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ComfeeDishwasherCoordinator,
        entity_key: str,
    ) -> None:
        """Initialize a dishwasher entity."""
        super().__init__(coordinator)
        self._entity_key = entity_key
        self._attr_unique_id = f"{coordinator.device.device_id}_{entity_key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device registry information."""
        device = self.coordinator.device
        device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.device_id))},
            manufacturer="Comfee / Midea",
            name=device.name,
            model=device.model or "E1 Dishwasher",
            model_id="E1",
        )
        if device.mac:
            device_info["connections"] = {(CONNECTION_NETWORK_MAC, device.mac)}
        if device.serial_number:
            device_info["serial_number"] = device.serial_number
        return device_info
