"""Config flow for supported Comfee/Midea-family local appliances."""

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
from midealocal.cloud import SUPPORTED_CLOUDS, get_midea_cloud
from midealocal.const import ProtocolVersion
from midealocal.devices import device_selector
from midealocal.discover import discover

from .const import (
    CONF_ACCOUNT,
    CONF_BRAND,
    CONF_CLOUD_NAME,
    CONF_DEVICE,
    CONF_KEY,
    CONF_KEY_METHOD,
    CONF_MAC,
    CONF_MANUFACTURER_CODE,
    CONF_SERIAL_NUMBER,
    CONF_SUBTYPE,
    DEFAULT_CLOUD_NAME,
    DEFAULT_PORT,
    DEFAULT_PROTOCOL,
    DOMAIN,
)
from .device_profiles import (
    device_type_options,
    get_device_profile,
    normalize_device_type,
    profile_name,
    resolve_device_brand,
)

_LOGGER = logging.getLogger(__package__)
CLOUD_LABELS = {
    "SmartHome": "MSmartHome / SmartHome",
    "NetHome Plus": "NetHome Plus",
    "Midea Air": "Midea Air / Arctic King",
    "Ariston Clima": "Ariston Clima",
    "美的美居": "Midea Meiju (China)",
}
CLOUD_OPTIONS = {
    cloud_name: CLOUD_LABELS.get(cloud_name, cloud_name)
    for cloud_name in SUPPORTED_CLOUDS
}
MEIJU_CLOUD_NAME = "美的美居"


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
        """Discover supported appliances and obtain their local keys."""
        if user_input is not None:
            account = str(user_input[CONF_ACCOUNT]).strip()
            password = str(user_input[CONF_PASSWORD])
            cloud_name = str(
                user_input.get(CONF_CLOUD_NAME, DEFAULT_CLOUD_NAME),
            )
            ip_address = str(user_input.get(CONF_IP_ADDRESS) or "").strip() or None
            try:
                self._candidates = await self._async_cloud_candidates(
                    account,
                    password,
                    ip_address,
                    cloud_name,
                )
            except CloudLoginError:
                return self._show_cloud_form(user_input, "cloud_login_failed")
            except DeviceNotFoundError:
                return self._show_cloud_form(user_input, "device_not_found")
            except DeviceNotInAccountError:
                return self._show_cloud_form(user_input, "device_not_in_account")
            except Exception:
                _LOGGER.exception("Unexpected error while setting up local appliance")
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
        """Select one of several discovered appliances."""
        if user_input is not None:
            return await self._async_create_entry(
                self._candidates[int(user_input[CONF_DEVICE])],
            )
        return self._show_device_form()

    async def async_step_manual(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Add an appliance with already-known local credentials."""
        if user_input is not None:
            try:
                token = _normalize_hex_credential(user_input[CONF_TOKEN])
                key = _normalize_hex_credential(user_input[CONF_KEY])
            except (TypeError, ValueError):
                return self._show_manual_form(user_input, "invalid_token")
            try:
                device_type = normalize_device_type(
                    user_input.get(CONF_TYPE, 0xE1),
                )
            except (TypeError, ValueError):
                return self._show_manual_form(user_input, "unsupported_device_type")
            profile = get_device_profile(device_type)
            if profile is None:
                return self._show_manual_form(user_input, "unsupported_device_type")

            model = str(user_input.get(CONF_MODEL) or profile.code)
            name = str(user_input.get(CONF_NAME) or profile.name_en)

            candidate = {
                CONF_DEVICE_ID: int(user_input[CONF_DEVICE_ID]),
                CONF_TYPE: device_type,
                CONF_IP_ADDRESS: str(user_input[CONF_IP_ADDRESS]).strip(),
                CONF_PORT: int(user_input.get(CONF_PORT, DEFAULT_PORT)),
                CONF_PROTOCOL: int(user_input.get(CONF_PROTOCOL, DEFAULT_PROTOCOL)),
                CONF_MODEL: model,
                CONF_NAME: name,
                CONF_TOKEN: token,
                CONF_KEY: key,
                CONF_SUBTYPE: int(user_input.get(CONF_SUBTYPE, 0) or 0),
                CONF_BRAND: resolve_device_brand(
                    device_type,
                    name,
                    model,
                    explicit_brand=user_input.get(CONF_BRAND),
                ),
                CONF_MANUFACTURER_CODE: str(
                    user_input.get(CONF_MANUFACTURER_CODE) or "",
                ).strip(),
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
                vol.Optional(
                    CONF_CLOUD_NAME,
                    default=DEFAULT_CLOUD_NAME,
                ): vol.In(CLOUD_OPTIONS),
                vol.Optional(CONF_IP_ADDRESS, default=""): str,
            },
        )
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(
                schema,
                {
                    CONF_ACCOUNT: user_input.get(CONF_ACCOUNT, ""),
                    CONF_CLOUD_NAME: user_input.get(
                        CONF_CLOUD_NAME,
                        DEFAULT_CLOUD_NAME,
                    ),
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
                vol.Optional(CONF_TYPE, default=0xE1): vol.In(
                    device_type_options(),
                ),
                vol.Optional(CONF_SUBTYPE, default=0): int,
                vol.Optional(CONF_MODEL, default=""): str,
                vol.Optional(CONF_NAME, default=""): str,
                vol.Optional(CONF_BRAND, default=""): str,
                vol.Optional(CONF_MANUFACTURER_CODE, default=""): str,
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
        cloud_name: str = DEFAULT_CLOUD_NAME,
    ) -> list[dict[str, Any]]:
        """Discover local drivers and validate cloud-provided keys."""
        local_devices = await self.hass.async_add_executor_job(
            _discover_devices,
            ip_address,
        )
        local_supported = [
            (device_id, info)
            for device_id, info in local_devices.items()
            if get_device_profile(info.get("type")) is not None
        ]
        if not local_supported:
            raise DeviceNotFoundError

        session = async_get_clientsession(self.hass)
        cloud = get_midea_cloud(cloud_name, session, account, password)
        if not await cloud.login():
            raise CloudLoginError
        appliances = await self._async_list_appliances(cloud, cloud_name)
        if not appliances:
            raise DeviceNotInAccountError

        candidates: list[dict[str, Any]] = []
        for device_id, info in local_supported:
            appliance = _lookup_appliance(appliances, device_id)
            if appliance is None:
                continue
            device_type = normalize_device_type(info.get("type"))
            profile = get_device_profile(device_type)
            if profile is None:
                continue
            subtype = _safe_int(appliance.get("model_number"), default=0)
            keys = await cloud.get_cloud_keys(int(device_id)) or {}
            for key_method, material in sorted(
                keys.items(),
                key=lambda item: str(item[0]),
            ):
                if not isinstance(material, dict):
                    continue
                if not material.get("token") or not material.get("key"):
                    continue
                candidate = {
                    CONF_DEVICE_ID: int(device_id),
                    CONF_TYPE: device_type,
                    CONF_IP_ADDRESS: str(info["ip_address"]),
                    CONF_PORT: int(info.get("port", DEFAULT_PORT)),
                    CONF_PROTOCOL: int(info.get("protocol", DEFAULT_PROTOCOL)),
                    CONF_MODEL: str(
                        info.get("model") or appliance.get("model") or profile.code,
                    ),
                    CONF_NAME: str(appliance.get("name") or profile.name_en),
                    CONF_TOKEN: str(material["token"]),
                    CONF_KEY: str(material["key"]),
                    CONF_SUBTYPE: subtype,
                    CONF_MAC: info.get("mac"),
                    CONF_SERIAL_NUMBER: info.get("sn") or appliance.get("sn"),
                    CONF_KEY_METHOD: _safe_int(key_method, default=0),
                    CONF_BRAND: resolve_device_brand(
                        device_type,
                        appliance.get("manufacturer"),
                        appliance.get("manufacturer_code"),
                        appliance.get("name"),
                        appliance.get("model"),
                        explicit_brand=appliance.get("brand"),
                    ),
                    CONF_MANUFACTURER_CODE: str(
                        appliance.get("manufacturer_code") or "",
                    ),
                }
                connected = await self.hass.async_add_executor_job(
                    _validate_candidate,
                    candidate,
                )
                if connected:
                    candidates.append(candidate)
                    break
        if not candidates and not any(
            _lookup_appliance(appliances, device_id) is not None
            for device_id, _ in local_supported
        ):
            raise DeviceNotInAccountError
        return candidates

    @staticmethod
    async def _async_list_appliances(
        cloud: Any,
        cloud_name: str,
    ) -> dict[Any, dict[str, Any]] | None:
        """List appliances, including every home required by Meiju Cloud."""
        if cloud_name != MEIJU_CLOUD_NAME:
            return await cloud.list_appliances(None)

        appliances: dict[Any, dict[str, Any]] = {}
        homes = await cloud.list_home() or {}
        for home_id in homes:
            appliances.update(await cloud.list_appliances(str(home_id)) or {})
        return appliances

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
            CONF_BRAND,
            CONF_MANUFACTURER_CODE,
        }
        return self.async_create_entry(
            title=str(candidate[CONF_NAME]),
            data={key: value for key, value in candidate.items() if key in stored_keys},
        )

    @staticmethod
    def _candidate_label(candidate: dict[str, Any]) -> str:
        """Build a non-sensitive device selector label."""
        return (
            f"{candidate.get(CONF_BRAND, 'Midea ecosystem')} · "
            f"{candidate[CONF_NAME]} — "
            f"{profile_name(candidate[CONF_TYPE], vietnamese=True)} "
            f"({candidate[CONF_IP_ADDRESS]})"
        )


class CloudLoginError(Exception):
    """The cloud account could not authenticate."""


class DeviceNotFoundError(Exception):
    """No supported local device was discovered."""


class DeviceNotInAccountError(Exception):
    """A discovered device is not present in the cloud account."""


def _discover_devices(ip_address: str | None) -> dict[int, dict[str, Any]]:
    """Run the blocking local discovery operation."""
    return discover(ip_address=ip_address)


def _lookup_appliance(
    appliances: dict[Any, dict[str, Any]],
    device_id: Any,
) -> dict[str, Any] | None:
    """Find a cloud appliance despite string/integer ID differences."""
    try:
        numeric_id = int(device_id)
    except (TypeError, ValueError):
        return None
    appliance = appliances.get(numeric_id)
    if isinstance(appliance, dict):
        return appliance
    appliance = appliances.get(str(numeric_id))
    return appliance if isinstance(appliance, dict) else None


def _safe_int(value: Any, *, default: int) -> int:
    """Convert optional cloud metadata without failing the whole flow."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
        if get_device_profile(candidate.get(CONF_TYPE)) is None:
            return False
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
        _LOGGER.debug("Unable to validate local appliance credentials", exc_info=True)
        return False
    finally:
        if device is not None:
            device.close_socket()
