"""Device and brand profiles for the Midea local protocol.

The protocol uses a numeric device type rather than a marketing brand. Keep
the catalog in one small, dependency-free module so config flow, entities and
diagnostics all make the same decision about what a device is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DeviceProfile:
    """Describe a device family implemented by ``midea-local``."""

    type_code: int
    name_en: str
    name_vi: str
    category: str
    writable_attributes: frozenset[str] = frozenset()

    @property
    def code(self) -> str:
        """Return the protocol type in the usual hexadecimal notation."""
        return f"0x{self.type_code:02X}"

    @property
    def display_name(self) -> str:
        """Return the Vietnamese name used in the device selector."""
        return self.name_vi


# These are the device modules shipped by midea-local 10.1.0. Do not add a
# type here until the pinned dependency has a matching MideaAppliance class.
DEVICE_PROFILES: dict[int, DeviceProfile] = {
    0x13: DeviceProfile(
        0x13,
        "Smart light",
        "Đèn thông minh",
        "lighting",
        frozenset({"power"}),
    ),
    0x26: DeviceProfile(
        0x26,
        "Bathroom heater",
        "Máy sưởi nhà tắm",
        "bathroom",
        frozenset({"main_light", "night_light"}),
    ),
    0x34: DeviceProfile(
        0x34,
        "Sink dishwasher",
        "Máy rửa bát dạng bồn",
        "dishwasher",
        frozenset({"power", "child_lock", "storage"}),
    ),
    0x40: DeviceProfile(
        0x40,
        "Integrated ceiling fan",
        "Quạt trần tích hợp",
        "fan",
        frozenset({"light", "ventilation", "smelly_sensor"}),
    ),
    0xA1: DeviceProfile(
        0xA1,
        "Dehumidifier",
        "Máy hút ẩm",
        "dehumidifier",
        frozenset({"power", "child_lock", "swing", "anion", "pump", "prompt_tone"}),
    ),
    0xAC: DeviceProfile(
        0xAC,
        "Air conditioner",
        "Điều hòa không khí",
        "air_conditioner",
        frozenset(
            {
                "power",
                "aux_heating",
                "boost_mode",
                "power_saving",
                "sleep_mode",
                "frost_protect",
                "comfort_mode",
                "eco_mode",
                "natural_wind",
                "smart_eye",
                "dry",
                "screen_display",
                "screen_display_alternate",
                "indirect_wind",
                "breezeless",
                "out_silent",
                "anion",
                "sound",
                "self_clean",
                "prompt_tone",
                "swing_horizontal",
                "swing_vertical",
            },
        ),
    ),
    0xAD: DeviceProfile(
        0xAD,
        "Air quality sensor",
        "Cảm biến chất lượng không khí",
        "air_quality",
        frozenset(),
    ),
    0xB0: DeviceProfile(
        0xB0,
        "Microwave oven",
        "Lò vi sóng",
        "cooking",
        frozenset({"child_lock"}),
    ),
    0xB1: DeviceProfile(
        0xB1,
        "Electric oven",
        "Lò nướng điện",
        "cooking",
        frozenset(),
    ),
    0xB3: DeviceProfile(
        0xB3,
        "Dish sterilizer",
        "Tủ sấy/khử khuẩn bát đĩa",
        "cooking",
        frozenset(),
    ),
    0xB4: DeviceProfile(
        0xB4,
        "Toaster",
        "Máy nướng bánh mì",
        "cooking",
        frozenset(),
    ),
    0xB6: DeviceProfile(
        0xB6,
        "Range hood",
        "Máy hút mùi",
        "ventilation",
        frozenset({"power", "light"}),
    ),
    0xB8: DeviceProfile(
        0xB8,
        "Robot vacuum",
        "Robot hút bụi",
        "vacuum",
        frozenset(),
    ),
    0xBF: DeviceProfile(
        0xBF,
        "Microwave steam oven",
        "Lò hấp kết hợp vi sóng",
        "cooking",
        frozenset(),
    ),
    0xC2: DeviceProfile(
        0xC2,
        "Smart toilet",
        "Bồn cầu thông minh",
        "bathroom",
        frozenset({"power", "child_lock", "sensor_light", "foam_shield"}),
    ),
    0xC3: DeviceProfile(
        0xC3,
        "Heat-pump controller",
        "Bộ điều khiển bơm nhiệt",
        "heat_pump",
        frozenset(
            {
                "dhw_power",
                "disinfect",
                "eco_mode",
                "fast_dhw",
                "silent_mode",
                "tbh",
                "zone1_curve",
                "zone1_power",
                "zone2_curve",
                "zone2_power",
            }
        ),
    ),
    0xCA: DeviceProfile(
        0xCA,
        "Refrigerator",
        "Tủ lạnh",
        "refrigeration",
        frozenset(),
    ),
    0xCC: DeviceProfile(
        0xCC,
        "Air-conditioner controller",
        "Bộ điều khiển điều hòa",
        "air_conditioner",
        frozenset(
            {
                "power",
                "aux_heating",
                "eco_mode",
                "night_light",
                "sleep_mode",
                "swing",
            }
        ),
    ),
    0xCD: DeviceProfile(
        0xCD,
        "Heat-pump water heater",
        "Bình nước nóng bơm nhiệt",
        "water_heater",
        frozenset({"power", "vacation_mode"}),
    ),
    0xCE: DeviceProfile(
        0xCE,
        "Fresh-air appliance",
        "Thiết bị cấp gió tươi",
        "air_quality",
        frozenset(
            {
                "power",
                "child_lock",
                "sleep_mode",
                "eco_mode",
                "aux_heating",
                "link_to_ac",
                "powerful_purify",
            }
        ),
    ),
    0xCF: DeviceProfile(
        0xCF,
        "Heat pump",
        "Máy bơm nhiệt",
        "heat_pump",
        frozenset({"power", "aux_heating"}),
    ),
    0xDA: DeviceProfile(
        0xDA,
        "Top-load washing machine",
        "Máy giặt cửa trên",
        "laundry",
        frozenset({"power"}),
    ),
    0xDB: DeviceProfile(
        0xDB,
        "Front-load washing machine",
        "Máy giặt cửa trước",
        "laundry",
        frozenset({"power"}),
    ),
    0xDC: DeviceProfile(
        0xDC,
        "Clothes dryer",
        "Máy sấy quần áo",
        "laundry",
        frozenset({"power"}),
    ),
    0xE1: DeviceProfile(
        0xE1,
        "Dishwasher",
        "Máy rửa bát",
        "dishwasher",
        frozenset({"power", "child_lock", "storage"}),
    ),
    0xE2: DeviceProfile(
        0xE2,
        "Electric water heater",
        "Bình nước nóng điện",
        "water_heater",
        frozenset({"power", "sterilization", "variable_heating", "whole_tank_heating"}),
    ),
    0xE3: DeviceProfile(
        0xE3,
        "Gas water heater",
        "Bình nước nóng gas",
        "water_heater",
        frozenset({"power", "smart_volume", "zero_cold_water"}),
    ),
    0xE6: DeviceProfile(
        0xE6,
        "Gas boiler",
        "Lò hơi gas",
        "boiler",
        frozenset(
            {"main_power", "heating_power", "cold_water_dot", "cold_water_single"}
        ),
    ),
    0xE8: DeviceProfile(
        0xE8,
        "Electric slow cooker",
        "Nồi nấu chậm điện",
        "cooking",
        frozenset(),
    ),
    0xEA: DeviceProfile(
        0xEA,
        "Rice cooker",
        "Nồi cơm điện",
        "cooking",
        frozenset(),
    ),
    0xEC: DeviceProfile(
        0xEC,
        "Electric pressure cooker",
        "Nồi áp suất điện",
        "cooking",
        frozenset(),
    ),
    0xED: DeviceProfile(
        0xED,
        "Water purifier",
        "Máy lọc nước/làm mềm nước",
        "water_purifier",
        frozenset(
            {
                "power",
                "child_lock",
                "soften",
                "cl_sterilization",
                "leak_water_protection",
                "regeneration",
                "water_way",
            }
        ),
    ),
    0xFA: DeviceProfile(
        0xFA,
        "Electric fan",
        "Quạt điện",
        "fan",
        frozenset({"power", "child_lock", "oscillate", "humidify", "waterions"}),
    ),
    0xFB: DeviceProfile(
        0xFB,
        "Electric heater",
        "Máy sưởi điện",
        "heater",
        frozenset({"power", "child_lock"}),
    ),
    0xFC: DeviceProfile(
        0xFC,
        "Air purifier",
        "Máy lọc không khí",
        "air_purifier",
        frozenset({"power", "anion", "standby", "prompt_tone", "child_lock"}),
    ),
    0xFD: DeviceProfile(
        0xFD,
        "Humidifier",
        "Máy tạo ẩm",
        "humidifier",
        frozenset({"power", "prompt_tone", "disinfect"}),
    ),
}

SUPPORTED_DEVICE_TYPES = frozenset(DEVICE_PROFILES)
DISHWASHER_TYPES = frozenset({0x34, 0xE1})


# These aliases are intentionally text-based. Manufacturer/enterprise codes
# differ between regions and are not stable enough to guess from a numeric
# value alone. If metadata does not contain a recognizable brand, the UI
# reports the neutral Midea ecosystem name instead of inventing one.
BRAND_ALIASES: tuple[tuple[str, str], ...] = (
    ("arctic king", "Arctic King"),
    ("arcticking", "Arctic King"),
    ("little swan", "Little Swan"),
    ("littleswan", "Little Swan"),
    ("pro breeze", "Pro Breeze"),
    ("probreeze", "Pro Breeze"),
    ("electrolux", "Electrolux"),
    ("inventor", "Inventor"),
    ("invertor", "Inventor"),
    ("toshiba", "Toshiba"),
    ("carrier", "Carrier"),
    ("rotenso", "Rotenso"),
    ("ariston", "Ariston"),
    ("vandelo", "Vandelo"),
    ("eureka", "Eureka"),
    ("colmo", "COLMO"),
    ("comfee", "Comfee"),
    ("midea", "Midea"),
    ("mdv", "MDV"),
    ("kuka", "KUKA"),
    ("wahin", "Wahin"),
    ("netsu", "Netsu"),
    ("beverly", "Beverly"),
    ("bugu", "Bugu"),
    ("美的", "Midea"),
)

_UNKNOWN_BRAND_VALUES = frozenset(
    {"default", "n/a", "na", "none", "null", "oem", "other", "unknown"}
)


def normalize_device_type(value: Any) -> int:
    """Convert a decimal/hex protocol type to an integer.

    Cloud responses have used both integers and strings such as ``0xE1`` or
    ``E1`` over time. Accept all of those forms while rejecting booleans and
    floating-point values that could silently select the wrong driver.
    """
    if isinstance(value, bool) or value is None:
        raise ValueError("device type must be an integer or hexadecimal string")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError("device type cannot be empty")
        try:
            if text.casefold().startswith("0x"):
                return int(text, 16)
            if all(character in "0123456789abcdefABCDEF" for character in text) and (
                any(character in "abcdefABCDEF" for character in text) or len(text) <= 2
            ):
                return int(text, 16)
            return int(text, 10)
        except ValueError as error:
            raise ValueError(f"invalid device type: {value!r}") from error
    raise ValueError(f"invalid device type: {value!r}")


def get_device_profile(device_type: Any) -> DeviceProfile | None:
    """Return a profile for a supported protocol type."""
    try:
        return DEVICE_PROFILES.get(normalize_device_type(device_type))
    except ValueError:
        return None


def device_type_options() -> dict[int, str]:
    """Return labels suitable for a Home Assistant ``vol.In`` selector."""
    return {
        type_code: f"{profile.name_vi} ({profile.code})"
        for type_code, profile in sorted(
            DEVICE_PROFILES.items(),
            key=lambda item: item[1].name_vi,
        )
    }


def writable_attributes_for(device_type: Any) -> frozenset[str]:
    """Return the conservative set of attributes exposed as switches."""
    profile = get_device_profile(device_type)
    return profile.writable_attributes if profile else frozenset()


def resolve_brand(*values: Any) -> str:
    """Resolve a display brand from cloud/device text without guessing codes."""
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = " ".join(
            value.casefold().replace("_", " ").replace("-", " ").split(),
        )
        compact = normalized.replace(" ", "")
        for alias, brand in BRAND_ALIASES:
            if alias in normalized or alias.replace(" ", "") in compact:
                return brand
    return "Midea ecosystem"


def _explicit_brand(value: Any) -> str | None:
    """Return a safe cloud-provided brand label, including unknown OEM names."""
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().split())
    if cleaned.casefold() in _UNKNOWN_BRAND_VALUES:
        return None
    if not 2 <= len(cleaned) <= 64 or not any(
        character.isalpha() for character in cleaned
    ):
        return None
    if any(ord(character) < 32 for character in cleaned):
        return None
    canonical = resolve_brand(cleaned)
    return cleaned if canonical == "Midea ecosystem" else canonical


def resolve_device_brand(
    device_type: Any,
    *values: Any,
    explicit_brand: Any = None,
) -> str:
    """Resolve a brand while preserving explicit OEM and dishwasher identity."""
    brand = _explicit_brand(explicit_brand)
    if brand is not None:
        return brand
    brand = resolve_brand(*values)
    if (
        brand == "Midea ecosystem"
        and get_device_profile(device_type) is not None
        and normalize_device_type(device_type) in DISHWASHER_TYPES
    ):
        return "Comfee / Midea"
    return brand


def profile_name(device_type: Any, *, vietnamese: bool = True) -> str:
    """Return a localized family name, with a safe fallback."""
    profile = get_device_profile(device_type)
    if profile is None:
        try:
            code = f"0x{normalize_device_type(device_type):02X}"
        except ValueError:
            code = "unknown"
        return f"Thiết bị Midea ({code})" if vietnamese else f"Midea device ({code})"
    return profile.name_vi if vietnamese else profile.name_en
