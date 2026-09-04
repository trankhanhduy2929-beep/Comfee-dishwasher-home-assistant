"""Shared entities for the Comfee/Midea local integration."""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_BRAND, DOMAIN
from .coordinator import ComfeeDishwasherCoordinator
from .device_profiles import profile_name, resolve_device_brand


class ComfeeDishwasherEntity(CoordinatorEntity[ComfeeDishwasherCoordinator]):
    """Base entity for a supported local appliance."""

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
        type_code = self.coordinator.device_type
        profile = self.coordinator.profile
        manufacturer = str(
            self.coordinator.config_entry.data.get(CONF_BRAND)
            or resolve_device_brand(
                type_code,
                self.coordinator.config_entry.data.get(CONF_BRAND),
                device.name,
                device.model,
            ),
        )
        model_name = (
            profile.name_en
            if profile is not None
            else profile_name(type_code, vietnamese=False)
        )
        device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device.device_id))},
            manufacturer=manufacturer,
            name=device.name,
            model=device.model or model_name,
            model_id=f"0x{type_code:02X}",
        )
        if device.mac:
            device_info["connections"] = {(CONNECTION_NETWORK_MAC, device.mac)}
        if device.serial_number:
            device_info["serial_number"] = device.serial_number
        return device_info

    @property
    def available(self) -> bool:
        """Return cached local availability without touching the device thread."""
        if self._entity_key in {"local_connection", "reconnect", "refresh"}:
            return True
        return bool(
            super().available
            and (self.coordinator.data or {}).get("local_connection", False)
        )
