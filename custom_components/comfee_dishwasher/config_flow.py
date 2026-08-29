"""Config flow for the Comfee dishwasher integration."""

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_IP_ADDRESS,
    CONF_MODEL,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_PROTOCOL,
    CONF_TOKEN,
    CONF_TYPE,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from midealocal.cloud import get_midea_cloud
from midealocal.const import ProtocolVersion
from midealocal.devices import device_selector
from midealocal.discover import discover

from .const import (
    CONF_ACCOUNT,
    CONF_DEVICE,
    CONF_KEY,
    CONF_KEY_METHOD,
    CONF_MAC,
    CONF_SERIAL_NUMBER,
    CONF_SUBTYPE,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DEVICE_TYPE_DISHWASHER,
    DOMAIN,
)

_LOGGER = logging.getLogger(__package__)
CLOUD_NAME = "SmartHome"


class ComfeeDishwasherConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle cloud discovery and manual local setup."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._candidates: list[dict[str, Any]] = []

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Choose a setup method."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["cloud", "manual"],
        )

    async def async_step_cloud(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Discover the dishwasher and obtain its local key."""
        if user_input is not None:
            account = str(user_input[CONF_ACCOUNT]).strip()
            password = str(user_input[CONF_PASSWORD])
            ip_address = str(user_input.get(CONF_IP_ADDRESS) or "").strip() or None
            try:
                self._candidates = await self._async_cloud_candidates(
                    account,
                    password,
                    ip_address,
                )
            except CloudLoginError:
                return self._show_cloud_form(user_input, "cloud_login_failed")
            except DeviceNotFoundError:
                return self._show_cloud_form(user_input, "device_not_found")
            except DeviceNotInAccountError:
                return self._show_cloud_form(user_input, "device_not_in_account")
            except Exception:
                _LOGGER.exception("Unexpected error while setting up dishwasher")
                return self._show_cloud_form(user_input, "setup_failed")

            if not self._candidates:
                return self._show_cloud_form(user_input, "device_auth_failed")
            if len(self._candidates) == 1:
                return await self._async_create_entry(self._candidates[0])
            return self._show_device_form()

        return self._show_cloud_form()

    async def async_step_select_device(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Select one of several discovered dishwashers."""
        if user_input is not None:
            return await self._async_create_entry(
                self._candidates[int(user_input[CONF_DEVICE])],
            )
        return self._show_device_form()

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Add a dishwasher with already-known local credentials."""
        if user_input is not None:
            try:
                token = _normalize_hex_credential(user_input[CONF_TOKEN])
                key = _normalize_hex_credential(user_input[CONF_KEY])
            except (TypeError, ValueError):
                return self._show_manual_form(user_input, "invalid_token")

            candidate = {
                CONF_DEVICE_ID: int(user_input[CONF_DEVICE_ID]),
                CONF_TYPE: DEVICE_TYPE_DISHWASHER,
                CONF_IP_ADDRESS: str(user_input[CONF_IP_ADDRESS]).strip(),
                CONF_PORT: int(user_input.get(CONF_PORT, DEFAULT_PORT)),
                CONF_PROTOCOL: int(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)),
                CONF_MODEL: str(user_input.get(CONF_MODEL) or "E1"),
                CONF_NAME: str(user_input.get(CONF_NAME) or "Comfee Dishwasher"),
                CONF_TOKEN: token,
                CONF_KEY: key,
                CONF_SUBTYPE: 0,
            }
            connected = await self.hass.async_add_executor_job(
                _validate_candidate,
                candidate,
            )
            if not connected:
                return self._show_manual_form(user_input, "manual_auth_failed")
            return await self._async_create_entry(candidate)

        return self._show_manual_form()

    def _show_cloud_form(
        self,
        user_input: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> ConfigFlowResult:
        """Render the cloud credential form."""
        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT): str,
                vol.Required(CONF_PASSWORD): str,
                vol.Optional(CONF_IP_ADDRESS, default=""): str,
            },
        )
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(
                schema,
                {
                    CONF_ACCOUNT: user_input.get(CONF_ACCOUNT, ""),
                    CONF_IP_ADDRESS: user_input.get(CONF_IP_ADDRESS, ""),
                },
            )
        return self.async_show_form(
            step_id="cloud",
            data_schema=schema,
            errors={"base": error} if error else None,
        )

    def _show_device_form(self) -> ConfigFlowResult:
        """Render the discovered-device selector."""
        options = {
            str(index): self._candidate_label(candidate)
            for index, candidate in enumerate(self._candidates)
        }
        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema({vol.Required(CONF_DEVICE): vol.In(options)}),
        )

    def _show_manual_form(
        self,
        user_input: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> ConfigFlowResult:
        """Render the manual local-credential form."""
        schema = vol.Schema(
            {
                vol.Required(CONF_DEVICE_ID): int,
                vol.Required(CONF_IP_ADDRESS): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
                vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(
                    [1, 2, 3]
                ),
                vol.Optional(CONF_MODEL, default="E1"): str,
                vol.Optional(CONF_NAME, default="Comfee Dishwasher"): str,
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_KEY): str,
            },
        )
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(schema, user_input)
        return self.async_show_form(
            step_id="manual",
            data_schema=schema,
            errors={"base": error} if error else None,
        )

    async def _async_cloud_candidates(
        self,
        account: str,
        password: str,
        ip_address: str | None,
    ) -> list[dict[str, Any]]:
        """Discover local E1 devices and validate cloud-provided keys."""
        local_devices = await self.hass.async_add_executor_job(
            _discover_devices,
            ip_address,
        )
        local_e1 = [
            (device_id, info)
            for device_id, info in local_devices.items()
            if int(info.get("type", 0)) == DEVICE_TYPE_DISHWASHER
        ]
        if not local_e1:
            raise DeviceNotFoundError

        session = async_get_clientsession(self.hass)
        cloud = get_midea_cloud(CLOUD_NAME, session, account, password)
        if not await cloud.login():
            raise CloudLoginError
        appliances = await cloud.list_appliances(None)
        if not appliances:
            raise DeviceNotInAccountError

        candidates: list[dict[str, Any]] = []
        for device_id, info in local_e1:
            if device_id not in appliances:
                continue
            appliance = appliances[device_id]
            subtype = int(appliance.get("model_number") or 0)
            keys = await cloud.get_cloud_keys(device_id)
            for key_method in sorted(keys):
                material = keys[key_method]
                candidate = {
                    CONF_DEVICE_ID: device_id,
                    CONF_TYPE: DEVICE_TYPE_DISHWASHER,
                    CONF_IP_ADDRESS: info["ip_address"],
                    CONF_PORT: int(info["port"]),
                    CONF_PROTOCOL: int(info["protocol"]),
                    CONF_MODEL: str(
                        info.get("model") or appliance.get("model") or "E1",
                    ),
                    CONF_NAME: str(appliance.get("name") or "Comfee Dishwasher"),
                    CONF_TOKEN: str(material["token"]),
                    CONF_KEY: str(material["key"]),
                    CONF_SUBTYPE: subtype,
                    CONF_MAC: info.get("mac"),
                    CONF_SERIAL_NUMBER: info.get("sn"),
                    CONF_KEY_METHOD: int(key_method),
                }
                connected = await self.hass.async_add_executor_job(
                    _validate_candidate,
                    candidate,
                )
                if connected:
                    candidates.append(candidate)
                    break
        if not candidates and not any(
            device_id in appliances for device_id, _ in local_e1
        ):
            raise DeviceNotInAccountError
        return candidates

    async def _async_create_entry(self, candidate: dict[str, Any]) -> ConfigFlowResult:
        """Validate uniqueness and create the config entry."""
        await self.async_set_unique_id(str(candidate[CONF_DEVICE_ID]))
        self._abort_if_unique_id_configured()
        stored_keys = {
            CONF_DEVICE_ID,
            CONF_TYPE,
            CONF_IP_ADDRESS,
            CONF_PORT,
            CONF_PROTOCOL,
            CONF_MODEL,
            CONF_NAME,
            CONF_TOKEN,
            CONF_KEY,
            CONF_SUBTYPE,
            CONF_MAC,
            CONF_SERIAL_NUMBER,
            CONF_KEY_METHOD,
        }
        return self.async_create_entry(
            title=str(candidate[CONF_NAME]),
            data={key: value for key, value in candidate.items() if key in stored_keys},
        )

    @staticmethod
    def _candidate_label(candidate: dict[str, Any]) -> str:
        """Build a non-sensitive device selector label."""
        return (
            f"{candidate[CONF_NAME]} — {candidate[CONF_MODEL]} "
            f"({candidate[CONF_IP_ADDRESS]})"
        )


class CloudLoginError(Exception):
    """The cloud account could not authenticate."""


class DeviceNotFoundError(Exception):
    """No local E1 device was discovered."""


class DeviceNotInAccountError(Exception):
    """The local E1 device is not in the cloud account."""


def _discover_devices(ip_address: str | None) -> dict[int, dict[str, Any]]:
    """Run the blocking local discovery operation."""
    return discover(ip_address=ip_address)


def _normalize_hex_credential(value: Any) -> str:
    """Normalize a required hexadecimal LAN credential."""
    decoded = bytes.fromhex(str(value))
    if not decoded:
        raise ValueError("Credential cannot be empty")
    return decoded.hex()


def _validate_candidate(candidate: dict[str, Any]) -> bool:
    """Authenticate and query a candidate without sending a control command."""
    device = None
    try:
        device = device_selector(
            name=str(candidate[CONF_NAME]),
            device_id=int(candidate[CONF_DEVICE_ID]),
            device_type=int(candidate[CONF_TYPE]),
            ip_address=str(candidate[CONF_IP_ADDRESS]),
            port=int(candidate[CONF_PORT]),
            token=str(candidate[CONF_TOKEN]),
            key=str(candidate[CONF_KEY]),
            device_protocol=ProtocolVersion(int(candidate[CONF_PROTOCOL])),
            model=str(candidate[CONF_MODEL]),
            subtype=int(candidate.get(CONF_SUBTYPE, 0)),
            customize="",
            mac=candidate.get(CONF_MAC),
            serial_number=candidate.get(CONF_SERIAL_NUMBER),
        )
        return bool(device and device.connect(check_protocol=True))
    except Exception:
        _LOGGER.debug("Unable to validate local dishwasher credentials", exc_info=True)
        return False
    finally:
        if device is not None:
            device.close_socket()
