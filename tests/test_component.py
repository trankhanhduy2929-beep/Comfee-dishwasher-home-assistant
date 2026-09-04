"""Contract tests for the Comfee dishwasher custom integration."""

from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from hashlib import sha256
from importlib import import_module
from pathlib import Path
from types import MappingProxyType
from unittest import IsolatedAsyncioTestCase, TestCase
from unittest.mock import AsyncMock, Mock, patch
from zipfile import ZipFile

from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
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
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from midealocal.const import ProtocolVersion
from midealocal.devices import device_selector
from midealocal.devices.e1 import MideaE1Device

import build_component
from custom_components.comfee_dishwasher import (
    async_setup_entry,
    async_unload_entry,
    binary_sensor,
    button,
    config_flow,
    select,
    sensor,
    switch,
)
from custom_components.comfee_dishwasher.attribute_catalog import attribute_hint
from custom_components.comfee_dishwasher.const import (
    CONF_ACCOUNT,
    CONF_BRAND,
    CONF_CLOUD_NAME,
    CONF_KEY,
    CONF_KEY_METHOD,
    CONF_SERIAL_NUMBER,
    CONF_SUBTYPE,
    DOMAIN,
    ESTIMATED_ENERGY_LAST_CYCLE,
    ESTIMATED_ENERGY_THIS_MONTH,
    ESTIMATED_ENERGY_TODAY,
    ESTIMATED_WATER_LAST_CYCLE,
    ESTIMATED_WATER_THIS_MONTH,
    ESTIMATED_WATER_TODAY,
    MODE_NAMES,
    USAGE_SENSOR_KEYS,
    WRITABLE_ATTRIBUTES,
)
from custom_components.comfee_dishwasher.coordinator import (
    ComfeeDishwasherCoordinator,
)
from custom_components.comfee_dishwasher.device_profiles import (
    DEVICE_PROFILES,
    resolve_device_brand,
)
from custom_components.comfee_dishwasher.usage import DishwasherUsageTracker

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "comfee_dishwasher"


class ComponentContractTests(TestCase):
    """Verify metadata, safety properties and dependency compatibility."""

    def test_manifest_contract(self) -> None:
        manifest = json.loads((COMPONENT / "manifest.json").read_text())
        self.assertEqual(manifest["domain"], "comfee_dishwasher")
        self.assertEqual(manifest["version"], "0.6.0")
        self.assertEqual(manifest["requirements"], ["midea-local==10.1.0"])
        self.assertEqual(manifest["iot_class"], "local_polling")
        self.assertTrue(manifest["config_flow"])

        hacs = json.loads((ROOT / "hacs.json").read_text())
        self.assertTrue(hacs["zip_release"])
        self.assertEqual(hacs["filename"], "comfee_dishwasher.zip")

    def test_translation_contract(self) -> None:
        strings = json.loads((COMPONENT / "strings.json").read_text())
        self.assertEqual(
            set(strings["config"]["step"]["user"]["menu_options"]),
            {"cloud", "manual"},
        )
        for language in ("en", "vi"):
            translated = json.loads(
                (COMPONENT / "translations" / f"{language}.json").read_text(),
            )
            self.assertEqual(
                set(translated["config"]["step"]["user"]["menu_options"]),
                {"cloud", "manual"},
            )

    def test_entity_translations_are_complete(self) -> None:
        """Every exposed entity and enum state has both translations."""
        descriptions = {
            "binary_sensor": binary_sensor.BINARY_SENSOR_DESCRIPTIONS,
            "button": (
                button.ComfeeDishwasherStartButton.entity_description,
                button.ComfeeDishwasherRefreshButton.entity_description,
                button.ComfeeDishwasherReconnectButton.entity_description,
            ),
            "select": (select.ComfeeDishwasherSelect.entity_description,),
            "sensor": sensor.SENSOR_DESCRIPTIONS,
            "switch": switch.SWITCH_DESCRIPTIONS,
        }
        for language in ("en", "vi"):
            translated = json.loads(
                (COMPONENT / "translations" / f"{language}.json").read_text(),
            )
            for platform, platform_descriptions in descriptions.items():
                entities = translated["entity"][platform]
                for description in platform_descriptions:
                    self.assertIn(description.translation_key, entities)
                    self.assertIn("name", entities[description.translation_key])
                    options = getattr(description, "options", None)
                    if options:
                        self.assertTrue(
                            set(options).issubset(
                                entities[description.translation_key]["state"],
                            ),
                        )

    def test_mode_table_matches_dependency(self) -> None:
        self.assertEqual(MODE_NAMES, MideaE1Device._modes)

    def test_supported_driver_catalog_matches_dependency(self) -> None:
        self.assertEqual(len(DEVICE_PROFILES), 36)
        self.assertEqual(
            set(DEVICE_PROFILES),
            {
                0x13,
                0x26,
                0x34,
                0x40,
                0xA1,
                0xAC,
                0xAD,
                0xB0,
                0xB1,
                0xB3,
                0xB4,
                0xB6,
                0xB8,
                0xBF,
                0xC2,
                0xC3,
                0xCA,
                0xCC,
                0xCD,
                0xCE,
                0xCF,
                0xDA,
                0xDB,
                0xDC,
                0xE1,
                0xE2,
                0xE3,
                0xE6,
                0xE8,
                0xEA,
                0xEC,
                0xED,
                0xFA,
                0xFB,
                0xFC,
                0xFD,
            },
        )
        for device_type in DEVICE_PROFILES:
            device = device_selector(
                name="Test appliance",
                device_id=1,
                device_type=device_type,
                ip_address="192.0.2.10",
                port=6444,
                token="00" * 64,
                key="00" * 32,
                device_protocol=ProtocolVersion.V3,
                model="test",
                subtype=0,
                customize="",
            )
            self.assertIsNotNone(device, f"Missing driver for 0x{device_type:02X}")

    def test_brand_resolution_uses_text_without_guessing_codes(self) -> None:
        self.assertEqual(resolve_device_brand(0xAC, "Toshiba Home AC"), "Toshiba")
        self.assertEqual(
            resolve_device_brand(0xAC, "Arctic King window AC"),
            "Arctic King",
        )
        self.assertEqual(
            resolve_device_brand(0xAC, explicit_brand="Keystone"),
            "Keystone",
        )
        self.assertEqual(
            resolve_device_brand(0xAC, explicit_brand="0000"),
            "Midea ecosystem",
        )
        self.assertEqual(
            resolve_device_brand(
                0xAC,
                "Toshiba Living Room",
                explicit_brand="unknown",
            ),
            "Toshiba",
        )
        self.assertEqual(resolve_device_brand(0xE1, "unknown"), "Comfee / Midea")
        self.assertEqual(resolve_device_brand(0xAC, "unknown"), "Midea ecosystem")

    def test_cloud_options_match_dependency(self) -> None:
        self.assertEqual(
            set(config_flow.CLOUD_OPTIONS),
            set(config_flow.SUPPORTED_CLOUDS),
        )
        self.assertTrue(all(config_flow.CLOUD_OPTIONS.values()))

    def test_writable_profiles_match_boolean_driver_attributes(self) -> None:
        for device_type, profile in DEVICE_PROFILES.items():
            module_name = (
                f"midealocal.devices.{'x' if device_type < 0xA0 else ''}"
                f"{device_type:02x}"
            )
            module = import_module(module_name)
            driver_attributes = {
                str(attribute) for attribute in module.DeviceAttributes
            }
            self.assertTrue(
                profile.writable_attributes.issubset(driver_attributes),
                f"Unknown control in profile 0x{device_type:02X}",
            )

            device = device_selector(
                name="Test appliance",
                device_id=1,
                device_type=device_type,
                ip_address="192.0.2.10",
                port=6444,
                token="00" * 64,
                key="00" * 32,
                device_protocol=ProtocolVersion.V3,
                model="test",
                subtype=0,
                customize="",
            )
            initial_attributes = {
                str(attribute): value for attribute, value in device.attributes.items()
            }
            for attribute in profile.writable_attributes:
                self.assertIn(attribute, initial_attributes)
                self.assertTrue(
                    initial_attributes[attribute] is None
                    or isinstance(initial_attributes[attribute], bool),
                    f"Non-boolean control {attribute} in 0x{device_type:02X}",
                )
                self.assertFalse(
                    attribute_hint(attribute).name_vi.startswith("Thông số "),
                    f"Missing Vietnamese control name for {attribute}",
                )

    def test_known_false_or_enum_controls_are_not_writable(self) -> None:
        forbidden_controls = {
            0xB3: {"lock"},
            0xB8: {"carpet_switch", "uv_switch", "voice_switch", "wifi_switch"},
            0xCD: {"dual_heat", "eco", "elec_heat", "heat"},
            0xCF: {"defrost", "freeze"},
            0xFC: {"screen_display"},
            0xFD: {"screen_display"},
        }
        for device_type, forbidden in forbidden_controls.items():
            self.assertTrue(
                DEVICE_PROFILES[device_type].writable_attributes.isdisjoint(forbidden),
                f"Unsafe controls enabled for 0x{device_type:02X}",
            )

    def test_cycle_controls_are_disabled_by_default(self) -> None:
        self.assertFalse(
            select.ComfeeDishwasherSelect.entity_description.entity_registry_enabled_default,
        )
        self.assertFalse(
            button.ComfeeDishwasherStartButton.entity_description.entity_registry_enabled_default,
        )

    def test_only_verified_boolean_controls_are_writable(self) -> None:
        self.assertEqual(WRITABLE_ATTRIBUTES, {"power", "child_lock", "storage"})

    def test_all_usage_sensors_are_exposed(self) -> None:
        descriptions = {description.key for description in sensor.SENSOR_DESCRIPTIONS}
        self.assertTrue(USAGE_SENSOR_KEYS.issubset(descriptions))

    def test_discovery_passes_single_ip_string(self) -> None:
        with patch.object(config_flow, "discover", return_value={}) as discover_mock:
            self.assertEqual(config_flow._discover_devices("192.0.2.10"), {})
        discover_mock.assert_called_once_with(ip_address="192.0.2.10")

    def test_empty_lan_credential_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            config_flow._normalize_hex_credential("")

    def test_public_source_does_not_store_cloud_password(self) -> None:
        source = "\n".join(
            path.read_text(errors="ignore")
            for path in COMPONENT.rglob("*")
            if path.is_file() and path.suffix in {".py", ".json", ".md"}
        )
        self.assertNotIn('"test-password"', source)

    def test_candidate_validation_is_query_only(self) -> None:
        device = Mock()
        device.connect.return_value = True
        candidate = {
            "name": "Dishwasher",
            "device_id": 1,
            "type": 0xE1,
            "ip_address": "192.0.2.10",
            "port": 6444,
            "token": "00",
            "key": "00",
            "protocol": 3,
            "model": "test",
            "subtype": 0,
        }
        with patch.object(config_flow, "device_selector", return_value=device):
            self.assertTrue(config_flow._validate_candidate(candidate))
        device.connect.assert_called_once_with(check_protocol=True)
        device.close_socket.assert_called_once_with()
        device.set_attribute.assert_not_called()

    def test_candidate_validation_handles_bad_credentials(self) -> None:
        with patch.object(
            config_flow,
            "device_selector",
            side_effect=ValueError("bad credential"),
        ):
            self.assertFalse(config_flow._validate_candidate(self._candidate_data()))

    def test_archive_contains_only_installable_component(self) -> None:
        build_component.main()
        with ZipFile(build_component.OUTPUT) as archive:
            names = archive.namelist()
            with tempfile.TemporaryDirectory(prefix="comfee-hacs-test-") as config_dir:
                install_dir = (
                    Path(config_dir) / "custom_components" / "comfee_dishwasher"
                )
                archive.extractall(install_dir)
                self.assertTrue((install_dir / "manifest.json").is_file())
                self.assertFalse(
                    (install_dir / "comfee_dishwasher" / "manifest.json").exists(),
                )
        self.assertIn("manifest.json", names)
        self.assertIn("brand/icon.png", names)
        self.assertIn("brand/logo.png", names)
        self.assertIn("icons.json", names)
        self.assertIn("diagnostics.py", names)
        self.assertFalse(any("__pycache__" in name for name in names))
        self.assertFalse(any("credentials" in name.casefold() for name in names))
        self.assertFalse(any(name.startswith("comfee_dishwasher/") for name in names))
        self.assertFalse(any(name.startswith("custom_components/") for name in names))
        checksum = build_component.CHECKSUM.read_text(encoding="ascii")
        self.assertIn(build_component.OUTPUT.name, checksum)
        self.assertEqual(
            checksum.split()[0],
            sha256(build_component.OUTPUT.read_bytes()).hexdigest(),
        )

    @staticmethod
    def _candidate_data() -> dict[str, object]:
        return {
            CONF_DEVICE_ID: 123456,
            CONF_TYPE: 0xE1,
            CONF_IP_ADDRESS: "192.0.2.10",
            CONF_PORT: 6444,
            CONF_PROTOCOL: 3,
            CONF_MODEL: "760EY095",
            CONF_NAME: "Dishwasher",
            CONF_TOKEN: "00" * 64,
            CONF_KEY: "00" * 32,
            CONF_SUBTYPE: 0,
        }


class ComponentRuntimeTests(IsolatedAsyncioTestCase):
    """Exercise config flow and lifecycle with a real Home Assistant object."""

    async def asyncSetUp(self) -> None:
        self._config_dir = tempfile.TemporaryDirectory(prefix="comfee-ha-test-")
        self.hass = HomeAssistant(self._config_dir.name)
        self.hass.config_entries = ConfigEntries(self.hass, {})

    async def asyncTearDown(self) -> None:
        await self.hass.async_stop(force=True)
        self._config_dir.cleanup()

    def _flow(self) -> config_flow.ComfeeDishwasherConfigFlow:
        flow = config_flow.ComfeeDishwasherConfigFlow()
        flow.hass = self.hass
        flow.handler = DOMAIN
        flow.flow_id = "test-flow"
        flow.context = {"source": "user", "title_placeholders": {}}
        return flow

    @staticmethod
    def _candidate() -> dict[str, object]:
        return {
            CONF_DEVICE_ID: 123456,
            CONF_TYPE: 0xE1,
            CONF_IP_ADDRESS: "192.0.2.10",
            CONF_PORT: 6444,
            CONF_PROTOCOL: 3,
            CONF_MODEL: "760EY095",
            CONF_NAME: "Dishwasher",
            CONF_TOKEN: "00" * 64,
            CONF_KEY: "00" * 32,
            CONF_SUBTYPE: 0,
        }

    @staticmethod
    def _entry(candidate: dict[str, object]) -> ConfigEntry:
        return ConfigEntry(
            created_at=datetime.now(UTC),
            data=candidate,
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title=str(candidate[CONF_NAME]),
            unique_id=str(candidate[CONF_DEVICE_ID]),
            version=1,
        )

    async def test_cloud_step_does_not_store_account_password(self) -> None:
        flow = self._flow()
        with patch.object(
            flow,
            "_async_cloud_candidates",
            AsyncMock(return_value=[self._candidate()]),
        ) as candidates:
            result = await flow.async_step_cloud(
                {
                    CONF_ACCOUNT: "owner@example.invalid",
                    CONF_PASSWORD: "test-password",
                    CONF_CLOUD_NAME: "NetHome Plus",
                    CONF_IP_ADDRESS: "192.0.2.10",
                },
            )
        candidates.assert_awaited_once_with(
            "owner@example.invalid",
            "test-password",
            "192.0.2.10",
            "NetHome Plus",
        )
        self.assertEqual(result["type"].value, "create_entry")
        self.assertNotIn(CONF_ACCOUNT, result["data"])
        self.assertNotIn(CONF_PASSWORD, result["data"])
        self.assertNotIn(CONF_CLOUD_NAME, result["data"])
        self.assertEqual(result["data"][CONF_MODEL], "760EY095")

    async def test_cloud_candidate_flow_with_mock_cloud(self) -> None:
        flow = self._flow()
        cloud = Mock()
        cloud.login = AsyncMock(return_value=True)
        cloud.list_appliances = AsyncMock(
            return_value={
                123456: {
                    "name": "Dishwasher",
                    "model": "760EY095",
                    "model_number": 0,
                },
            },
        )
        cloud.get_cloud_keys = AsyncMock(
            return_value={1: {"token": "00" * 64, "key": "00" * 32}},
        )
        local = {
            123456: {
                "type": 0xE1,
                "ip_address": "192.0.2.10",
                "port": 6444,
                "protocol": 3,
                "model": "760EY095",
                "mac": None,
                "sn": None,
            },
        }
        with (
            patch.object(config_flow, "_discover_devices", return_value=local),
            patch.object(config_flow, "async_get_clientsession", return_value=Mock()),
            patch.object(config_flow, "get_midea_cloud", return_value=cloud),
            patch.object(config_flow, "_validate_candidate", return_value=True),
        ):
            candidates = await flow._async_cloud_candidates(
                "owner@example.invalid",
                "test-password",
                "192.0.2.10",
            )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][CONF_MODEL], "760EY095")
        self.assertEqual(candidates[0]["key_method"], 1)

    async def test_cloud_candidate_supports_ac_and_alternate_cloud(self) -> None:
        flow = self._flow()
        cloud = Mock()
        cloud.login = AsyncMock(return_value=True)
        cloud.list_appliances = AsyncMock(
            return_value={
                654321: {
                    "brand": "unknown",
                    "name": "Toshiba Living Room",
                    "model": "AC-MODEL",
                    "model_number": "7",
                    "sn": "cloud-serial",
                },
            },
        )
        cloud.get_cloud_keys = AsyncMock(
            return_value={"unknown": {"token": "00" * 64, "key": "00" * 32}},
        )
        local = {
            654321: {
                "type": 0xAC,
                "ip_address": "192.0.2.20",
                "port": 6444,
                "protocol": 3,
                "model": "",
                "mac": None,
                "sn": None,
            },
            999999: {
                "type": 0xA0,
                "ip_address": "192.0.2.30",
            },
        }
        with (
            patch.object(config_flow, "_discover_devices", return_value=local),
            patch.object(config_flow, "async_get_clientsession", return_value=Mock()),
            patch.object(
                config_flow,
                "get_midea_cloud",
                return_value=cloud,
            ) as get_cloud,
            patch.object(config_flow, "_validate_candidate", return_value=True),
        ):
            candidates = await flow._async_cloud_candidates(
                "owner@example.invalid",
                "test-password",
                None,
                "Midea Air",
            )

        get_cloud.assert_called_once_with(
            "Midea Air",
            get_cloud.call_args.args[1],
            "owner@example.invalid",
            "test-password",
        )
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][CONF_TYPE], 0xAC)
        self.assertEqual(candidates[0][CONF_MODEL], "AC-MODEL")
        self.assertEqual(candidates[0][CONF_SERIAL_NUMBER], "cloud-serial")
        self.assertEqual(candidates[0][CONF_KEY_METHOD], 0)
        self.assertEqual(candidates[0][CONF_BRAND], "Toshiba")

    async def test_meiju_cloud_lists_every_home(self) -> None:
        cloud = Mock()
        cloud.list_home = AsyncMock(return_value={1: "Home", 2: "Office"})
        cloud.list_appliances = AsyncMock(
            side_effect=[{1: {"name": "One"}}, {2: {"name": "Two"}}],
        )

        appliances = (
            await config_flow.ComfeeDishwasherConfigFlow._async_list_appliances(
                cloud,
                config_flow.MEIJU_CLOUD_NAME,
            )
        )

        self.assertEqual(set(appliances or {}), {1, 2})
        self.assertEqual(
            [call.args[0] for call in cloud.list_appliances.await_args_list],
            ["1", "2"],
        )

    async def test_manual_flow_preserves_selected_device_type(self) -> None:
        flow = self._flow()
        with patch.object(config_flow, "_validate_candidate", return_value=True):
            result = await flow.async_step_manual(
                {
                    CONF_DEVICE_ID: 654321,
                    CONF_TYPE: 0xAC,
                    CONF_IP_ADDRESS: "192.0.2.20",
                    CONF_PORT: 6444,
                    CONF_PROTOCOL: 3,
                    CONF_MODEL: "",
                    CONF_NAME: "",
                    CONF_BRAND: "Keystone",
                    CONF_TOKEN: "00" * 64,
                    CONF_KEY: "00" * 32,
                    CONF_SUBTYPE: 0,
                },
            )

        self.assertEqual(result["type"].value, "create_entry")
        self.assertEqual(result["data"][CONF_TYPE], 0xAC)
        self.assertEqual(result["data"][CONF_MODEL], "0xAC")
        self.assertEqual(result["data"][CONF_NAME], "Air conditioner")
        self.assertEqual(result["data"][CONF_BRAND], "Keystone")

    async def test_manual_flow_reports_unsupported_type_separately(self) -> None:
        flow = self._flow()
        result = await flow.async_step_manual(
            {
                CONF_DEVICE_ID: 654321,
                CONF_TYPE: 0xA0,
                CONF_IP_ADDRESS: "192.0.2.20",
                CONF_TOKEN: "00" * 64,
                CONF_KEY: "00" * 32,
            },
        )

        self.assertEqual(result["type"].value, "form")
        self.assertEqual(result["errors"]["base"], "unsupported_device_type")

    async def test_non_e1_entities_are_generic_and_unique(self) -> None:
        candidate = {
            **self._candidate(),
            CONF_DEVICE_ID: 654321,
            CONF_TYPE: 0xAC,
            CONF_MODEL: "AC-MODEL",
            CONF_NAME: "Living room AC",
        }
        entry = self._entry(candidate)
        device = Mock()
        device.device_id = 654321
        device.available = True
        device.attributes = {
            "power": False,
            "status": "idle",
            "indoor_temperature": 24.5,
            "water_pump_running": False,
        }
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        entry.runtime_data = coordinator

        entities: list[object] = []
        for platform in (binary_sensor, button, select, sensor, switch):
            await platform.async_setup_entry(self.hass, entry, entities.extend)

        unique_ids = [entity.unique_id for entity in entities]
        self.assertEqual(len(unique_ids), len(set(unique_ids)))
        self.assertIsNone(coordinator.usage)
        self.assertFalse(
            any(
                isinstance(entity, button.ComfeeDishwasherStartButton)
                for entity in entities
            ),
        )
        self.assertFalse(
            any(
                isinstance(entity, select.ComfeeDishwasherSelect) for entity in entities
            ),
        )
        self.assertTrue(
            any(
                isinstance(entity, sensor.ComfeeGenericAttributeSensor)
                and entity.unique_id.endswith("_indoor_temperature")
                for entity in entities
            ),
        )
        self.assertTrue(
            any(
                isinstance(entity, binary_sensor.ComfeeGenericBinarySensor)
                and entity.unique_id.endswith("_water_pump_running")
                for entity in entities
            ),
        )
        self.assertTrue(
            any(
                isinstance(entity, switch.ComfeeDishwasherSwitch)
                and entity.unique_id.endswith("_power")
                for entity in entities
            ),
        )
        device.set_attribute.assert_not_called()
        await coordinator.async_shutdown()

    async def test_nullable_boolean_attribute_creates_binary_sensor(self) -> None:
        candidate = {
            **self._candidate(),
            CONF_DEVICE_ID: 456789,
            CONF_TYPE: 0xCF,
            CONF_MODEL: "HEAT-PUMP",
            CONF_NAME: "Heat pump",
        }
        entry = self._entry(candidate)
        device = Mock()
        device.device_id = 456789
        device.available = True
        device.attributes = {"compressor_status": None}
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        entry.runtime_data = coordinator

        entities: list[object] = []
        await binary_sensor.async_setup_entry(self.hass, entry, entities.extend)

        target = next(
            entity
            for entity in entities
            if isinstance(entity, binary_sensor.ComfeeGenericBinarySensor)
            and entity.unique_id.endswith("_compressor_status")
        )
        self.assertIsNone(target.is_on)
        await coordinator.async_shutdown()

    async def test_forbidden_controls_do_not_create_switches(self) -> None:
        forbidden_controls = {
            0xB3: {"lock"},
            0xB8: {"carpet_switch", "uv_switch", "voice_switch", "wifi_switch"},
            0xCD: {"dual_heat", "eco", "elec_heat", "heat"},
            0xCF: {"defrost", "freeze"},
            0xFC: {"screen_display"},
            0xFD: {"screen_display"},
        }
        for index, (device_type, attributes) in enumerate(
            forbidden_controls.items(),
            start=1,
        ):
            candidate = {
                **self._candidate(),
                CONF_DEVICE_ID: 800000 + index,
                CONF_TYPE: device_type,
                CONF_MODEL: f"TYPE-{device_type:02X}",
                CONF_NAME: f"Device {device_type:02X}",
            }
            entry = self._entry(candidate)
            device = Mock()
            device.device_id = candidate[CONF_DEVICE_ID]
            device.available = True
            device.attributes = dict.fromkeys(attributes, False)
            coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
            coordinator.data = dict(coordinator._cached_data)
            entry.runtime_data = coordinator

            entities: list[object] = []
            await switch.async_setup_entry(self.hass, entry, entities.extend)

            self.assertFalse(
                any(entity._entity_key in attributes for entity in entities),
                f"Unsafe switch created for 0x{device_type:02X}",
            )
            await coordinator.async_shutdown()

    async def test_x34_does_not_expose_e1_program_or_usage_entities(self) -> None:
        candidate = {
            **self._candidate(),
            CONF_DEVICE_ID: 345678,
            CONF_TYPE: 0x34,
            CONF_MODEL: "X34",
            CONF_NAME: "Sink dishwasher",
        }
        entry = self._entry(candidate)
        device = Mock()
        device.device_id = 345678
        device.available = True
        device.attributes = {
            "power": False,
            "status": "off",
            "progress": "idle",
        }
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        entry.runtime_data = coordinator

        entities: list[object] = []
        for platform in (button, select, sensor):
            await platform.async_setup_entry(self.hass, entry, entities.extend)

        self.assertIsNone(coordinator.usage)
        self.assertFalse(
            any(
                isinstance(entity, button.ComfeeDishwasherStartButton)
                for entity in entities
            ),
        )
        self.assertFalse(
            any(
                isinstance(entity, select.ComfeeDishwasherSelect) for entity in entities
            ),
        )
        self.assertFalse(
            any(
                isinstance(entity, sensor.ComfeeDishwasherUsageSensor)
                for entity in entities
            ),
        )
        device.set_attribute.assert_not_called()
        await coordinator.async_shutdown()

    async def test_setup_and_unload_close_socket(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {
            "power": False,
            "status": "off",
            "mode": "eco_wash",
        }
        device.connect.return_value = True
        self.hass.config_entries.async_forward_entry_setups = AsyncMock()
        self.hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)
        with patch(
            "custom_components.comfee_dishwasher._create_device",
            return_value=device,
        ):
            self.assertTrue(await async_setup_entry(self.hass, entry))
            self.assertTrue(await async_unload_entry(self.hass, entry))
            await entry._async_process_on_unload(self.hass)
            await self.hass.async_block_till_done()
        device.register_update.assert_called_once_with(
            device.unregister_update.call_args.args[0]
        )
        device.open.assert_called_once_with()
        device.close.assert_called_once_with()
        device.close_socket.assert_called_once_with()

    async def test_unsupported_local_control_is_rejected(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = {"power": True}
        with self.assertRaises(HomeAssistantError):
            await coordinator.async_set_attribute("uv", True)
        device.set_attribute.assert_not_called()
        await coordinator.async_shutdown()

    async def test_cycle_guard_blocks_open_door(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = {"power": True, "door": True, "status": "off"}
        with self.assertRaises(HomeAssistantError):
            coordinator._validate_cycle_command()
        await coordinator.async_shutdown()

    async def test_generic_boolean_and_text_errors_are_derived(self) -> None:
        normal = ComfeeDishwasherCoordinator._with_derived_states(
            {"error": False, "fault": "none", "wrong_operation": "0"},
        )
        self.assertFalse(normal["error_active"])
        self.assertFalse(normal["operation_warning"])

        active = ComfeeDishwasherCoordinator._with_derived_states(
            {"error": True, "wrong_operation": "door open"},
        )
        self.assertTrue(active["error_active"])
        self.assertTrue(active["operation_warning"])

    async def test_device_callbacks_are_coalesced_on_hass_loop(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {
            "power": True,
            "status": "off",
            "mode": "eco_wash",
            "error_code": 0,
            "wrong_operation": 0,
        }
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        listener = Mock()
        coordinator.async_add_listener(listener)
        await coordinator.async_start()
        callback = device.register_update.call_args.args[0]

        def emit_updates() -> None:
            callback({"status": "running"})
            callback({"progress": "wash", "time_remaining": 42})

        await self.hass.async_add_executor_job(emit_updates)
        await self.hass.async_block_till_done()

        self.assertEqual(coordinator.data["status"], "running")
        self.assertEqual(coordinator.data["progress"], "wash")
        self.assertEqual(coordinator.data["time_remaining"], 42)
        self.assertFalse(coordinator.data["error_active"])
        self.assertEqual(listener.call_count, 1)

        await self.hass.async_add_executor_job(
            callback,
            {"status": "error", "available": False},
        )
        await self.hass.async_block_till_done()

        self.assertTrue(coordinator.data["error_active"])
        self.assertFalse(coordinator.data["local_connection"])
        self.assertEqual(listener.call_count, 2)
        await coordinator.async_close()

    async def test_coalesced_cycle_edges_are_kept_for_usage_tracking(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {
            "status": "off",
            "mode": "eco_wash",
            "progress": "idle",
        }
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        await coordinator.async_start()
        callback = device.register_update.call_args.args[0]

        def emit_cycle() -> None:
            callback({"status": "running", "mode": "eco_wash", "progress": "wash"})
            callback({"status": "running", "progress": "complete"})

        await self.hass.async_add_executor_job(emit_cycle)
        await self.hass.async_block_till_done()

        self.assertEqual(coordinator.data[ESTIMATED_ENERGY_TODAY], 0.99)
        self.assertEqual(coordinator.data[ESTIMATED_WATER_TODAY], 10.4)
        await coordinator.async_close()

    async def test_completed_cycle_updates_usage_once(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {
            "power": True,
            "status": "off",
            "mode": "eco_wash",
            "progress": "idle",
        }
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        await coordinator.async_start()
        callback = device.register_update.call_args.args[0]

        await self.hass.async_add_executor_job(
            callback,
            {"status": "running", "mode": "eco_wash", "progress": "wash"},
        )
        await self.hass.async_block_till_done()
        await self.hass.async_add_executor_job(
            callback,
            {"status": "running", "progress": "complete"},
        )
        await self.hass.async_block_till_done()

        self.assertEqual(coordinator.data[ESTIMATED_ENERGY_LAST_CYCLE], 0.99)
        self.assertEqual(coordinator.data[ESTIMATED_WATER_LAST_CYCLE], 10.4)
        self.assertEqual(coordinator.data[ESTIMATED_ENERGY_TODAY], 0.99)
        self.assertEqual(coordinator.data[ESTIMATED_WATER_TODAY], 10.4)
        self.assertEqual(coordinator.data[ESTIMATED_ENERGY_THIS_MONTH], 0.99)
        self.assertEqual(coordinator.data[ESTIMATED_WATER_THIS_MONTH], 10.4)

        await self.hass.async_add_executor_job(
            callback,
            {"status": "running", "progress": "complete"},
        )
        await self.hass.async_block_till_done()
        await self.hass.async_add_executor_job(
            callback,
            {"status": "off", "progress": "complete"},
        )
        await self.hass.async_block_till_done()
        self.assertEqual(coordinator.data[ESTIMATED_ENERGY_TODAY], 0.99)
        self.assertEqual(coordinator.data[ESTIMATED_WATER_TODAY], 10.4)
        await coordinator.async_close()

    async def test_cancel_error_and_unknown_program_are_not_counted(self) -> None:
        tracker = DishwasherUsageTracker(self.hass, "cancel-error-test")
        now = datetime(2026, 9, 4, 12, tzinfo=UTC)
        await tracker.async_initialize(
            {"status": "off", "mode": "eco_wash", "progress": "idle"},
            now,
        )

        tracker.process_state(
            {"status": "running", "mode": "eco_wash", "progress": "wash"},
            now,
        )
        tracker.process_state(
            {"status": "cancel", "mode": "eco_wash", "progress": "idle"},
            now,
        )
        tracker.process_state(
            {"status": "running", "mode": "strong_wash", "progress": "wash"},
            now,
        )
        tracker.process_state(
            {"status": "error", "mode": "strong_wash", "progress": "complete"},
            now,
        )
        self.assertEqual(tracker.sensor_values[ESTIMATED_ENERGY_TODAY], 0.0)
        self.assertEqual(tracker.sensor_values[ESTIMATED_WATER_TODAY], 0.0)

        tracker.process_state(
            {"status": "running", "mode": "auto_wash", "progress": "wash"},
            now,
        )
        tracker.process_state(
            {"status": "off", "mode": "auto_wash", "progress": "complete"},
            now,
        )
        self.assertIsNone(tracker.sensor_values[ESTIMATED_ENERGY_LAST_CYCLE])
        self.assertIsNone(tracker.sensor_values[ESTIMATED_WATER_LAST_CYCLE])
        self.assertEqual(tracker.sensor_values[ESTIMATED_ENERGY_TODAY], 0.0)
        attributes = tracker.attributes_for(ESTIMATED_ENERGY_LAST_CYCLE)
        self.assertEqual(attributes["program"], "auto_wash")
        self.assertFalse(attributes["counted_in_totals"])
        await tracker.async_shutdown()

    async def test_usage_survives_restart_without_duplicate_counting(self) -> None:
        now = datetime(2026, 9, 4, 12, tzinfo=UTC)
        first = DishwasherUsageTracker(self.hass, "restart-test")
        await first.async_initialize(
            {"status": "off", "mode": "eco_wash", "progress": "idle"},
            now,
        )
        first.process_state(
            {"status": "running", "mode": "eco_wash", "progress": "wash"},
            now,
        )
        await first.async_shutdown()

        second = DishwasherUsageTracker(self.hass, "restart-test")
        await second.async_initialize(
            {"status": "off", "mode": "eco_wash", "progress": "complete"},
            now,
        )
        self.assertEqual(second.sensor_values[ESTIMATED_ENERGY_TODAY], 0.99)
        self.assertEqual(second.sensor_values[ESTIMATED_WATER_TODAY], 10.4)
        await second.async_shutdown()

        third = DishwasherUsageTracker(self.hass, "restart-test")
        await third.async_initialize(
            {"status": "off", "mode": "eco_wash", "progress": "complete"},
            now,
        )
        self.assertEqual(third.sensor_values[ESTIMATED_ENERGY_TODAY], 0.99)
        self.assertEqual(third.sensor_values[ESTIMATED_WATER_TODAY], 10.4)
        await third.async_shutdown()

    async def test_usage_rolls_over_by_local_day_and_month(self) -> None:
        tracker = DishwasherUsageTracker(self.hass, "rollover-test")
        january_first = datetime(2026, 1, 1, 12, tzinfo=UTC)
        await tracker.async_initialize(
            {"status": "off", "mode": "eco_wash", "progress": "idle"},
            january_first,
        )
        tracker.process_state(
            {"status": "running", "mode": "eco_wash", "progress": "wash"},
            january_first,
        )
        tracker.process_state(
            {"status": "off", "mode": "eco_wash", "progress": "complete"},
            january_first,
        )

        january_second = datetime(2026, 1, 2, tzinfo=UTC)
        self.assertTrue(tracker.rollover(january_second))
        self.assertEqual(tracker.sensor_values[ESTIMATED_ENERGY_TODAY], 0.0)
        self.assertEqual(tracker.sensor_values[ESTIMATED_WATER_TODAY], 0.0)
        self.assertEqual(tracker.sensor_values[ESTIMATED_ENERGY_THIS_MONTH], 0.99)
        self.assertEqual(tracker.sensor_values[ESTIMATED_WATER_THIS_MONTH], 10.4)
        self.assertEqual(
            tracker.period_start(ESTIMATED_ENERGY_TODAY),
            january_second,
        )

        february_first = datetime(2026, 2, 1, tzinfo=UTC)
        self.assertTrue(tracker.rollover(february_first))
        self.assertEqual(tracker.sensor_values[ESTIMATED_ENERGY_THIS_MONTH], 0.0)
        self.assertEqual(tracker.sensor_values[ESTIMATED_WATER_THIS_MONTH], 0.0)
        self.assertEqual(
            tracker.period_start(ESTIMATED_ENERGY_THIS_MONTH),
            february_first,
        )
        await tracker.async_shutdown()

    async def test_callback_after_close_is_ignored(self) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {"status": "off"}
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)
        coordinator.data = dict(coordinator._cached_data)
        await coordinator.async_start()
        callback = device.register_update.call_args.args[0]
        await coordinator.async_close()

        callback({"status": "running"})
        await self.hass.async_block_till_done()

        self.assertEqual(coordinator.data["status"], "off")

    async def test_first_refresh_uses_cache_and_manual_refresh_uses_executor(
        self,
    ) -> None:
        entry = ConfigEntry(
            created_at=datetime.now(UTC),
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            modified_at=datetime.now(UTC),
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {"status": "off"}
        coordinator = ComfeeDishwasherCoordinator(self.hass, entry, device)

        await coordinator.async_config_entry_first_refresh()

        device.connect.assert_not_called()
        device.refresh_status.assert_not_called()

        await coordinator.async_request_device_refresh()

        device.refresh_status.assert_called_once_with()
        device.connect.assert_not_called()
        await coordinator.async_close()

    async def test_setup_rediscovers_changed_ip(self) -> None:
        entry = ConfigEntry(
            data=self._candidate(),
            discovery_keys=MappingProxyType({}),
            domain=DOMAIN,
            minor_version=0,
            options=None,
            source="user",
            state=ConfigEntryState.SETUP_IN_PROGRESS,
            subentries_data=None,
            title="Dishwasher",
            unique_id="123456",
            version=1,
        )
        device = Mock()
        device.available = True
        device.attributes = {"power": False, "status": "off", "mode": "eco_wash"}
        self.hass.config_entries.async_update_entry = Mock()
        self.hass.config_entries.async_forward_entry_setups = AsyncMock()
        with (
            patch(
                "custom_components.comfee_dishwasher._create_device",
                return_value=device,
            ),
            patch(
                "custom_components.comfee_dishwasher._connect_device",
                side_effect=[False, True],
            ),
            patch(
                "custom_components.comfee_dishwasher._discover_current_ip",
                return_value="192.0.2.20",
            ),
        ):
            self.assertTrue(await async_setup_entry(self.hass, entry))
        device.set_ip_address.assert_called_once_with("192.0.2.20")
        updated = self.hass.config_entries.async_update_entry.call_args.kwargs["data"]
        self.assertEqual(updated[CONF_IP_ADDRESS], "192.0.2.20")
        await entry._async_process_on_unload(self.hass)
        await self.hass.async_block_till_done()
