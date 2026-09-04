"""Wash-program select for a Comfee dishwasher."""

from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, MODE_CODES
from .coordinator import ComfeeDishwasherCoordinator
from .entity import ComfeeDishwasherEntity


class ComfeeDishwasherSelect(ComfeeDishwasherEntity, SelectEntity):
    """Select and start a dishwasher program."""

    entity_description = SelectEntityDescription(
        key="wash_program",
        translation_key="wash_program",
        options=list(MODE_CODES),
        entity_registry_enabled_default=False,
    )

    def __init__(self, coordinator: ComfeeDishwasherCoordinator) -> None:
        """Initialize the wash-program select."""
        super().__init__(coordinator, "wash_program")

    @property
    def current_option(self) -> str | None:
        """Return the current program."""
        value = (self.coordinator.data or {}).get("mode")
        return value if isinstance(value, str) and value in MODE_CODES else None

    @property
    def options(self) -> list[str]:
        """Return supported programs."""
        return list(MODE_CODES)

    async def async_select_option(self, option: str) -> None:
        """Select and start a program."""
        if option not in MODE_CODES:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unsupported_program",
            )
        await self.coordinator.async_set_mode(int(MODE_CODES[option]))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Any,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the wash-program select."""
    coordinator: ComfeeDishwasherCoordinator = entry.runtime_data
    if coordinator.device_type == 0xE1 and "mode" in coordinator.data:
        async_add_entities([ComfeeDishwasherSelect(coordinator)])
