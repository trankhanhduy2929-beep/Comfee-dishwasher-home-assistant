"""Constants for the Comfee/Midea local appliance integration."""

from enum import IntEnum
from typing import Final, NamedTuple

DOMAIN = "comfee_dishwasher"
CONF_ACCOUNT = "account"
CONF_CLOUD_NAME = "cloud_name"
CONF_KEY = "key"
CONF_SUBTYPE = "subtype"
CONF_MAC = "mac"
CONF_SERIAL_NUMBER = "serial_number"
CONF_KEY_METHOD = "key_method"
CONF_DEVICE = "device"
CONF_BRAND = "brand"
CONF_MANUFACTURER_CODE = "manufacturer_code"

DEVICE_TYPE_DISHWASHER = 0xE1
DEFAULT_PORT = 6444
DEFAULT_PROTOCOL = 3
DEFAULT_CLOUD_NAME = "SmartHome"
WRITABLE_ATTRIBUTES = frozenset({"power", "child_lock", "storage"})

ESTIMATED_ENERGY_LAST_CYCLE = "estimated_energy_last_cycle"
ESTIMATED_WATER_LAST_CYCLE = "estimated_water_last_cycle"
ESTIMATED_ENERGY_TODAY = "estimated_energy_today"
ESTIMATED_WATER_TODAY = "estimated_water_today"
ESTIMATED_ENERGY_THIS_MONTH = "estimated_energy_this_month"
ESTIMATED_WATER_THIS_MONTH = "estimated_water_this_month"

LAST_CYCLE_USAGE_KEYS = frozenset(
    {ESTIMATED_ENERGY_LAST_CYCLE, ESTIMATED_WATER_LAST_CYCLE}
)
DAILY_USAGE_KEYS = frozenset({ESTIMATED_ENERGY_TODAY, ESTIMATED_WATER_TODAY})
MONTHLY_USAGE_KEYS = frozenset(
    {ESTIMATED_ENERGY_THIS_MONTH, ESTIMATED_WATER_THIS_MONTH}
)
USAGE_SENSOR_KEYS = LAST_CYCLE_USAGE_KEYS | DAILY_USAGE_KEYS | MONTHLY_USAGE_KEYS
USAGE_REFERENCE_MODEL = "7600024L"
USAGE_ESTIMATE_SOURCE = "fixed_program_reference"


class ProgramUsageEstimate(NamedTuple):
    """Reference usage estimate for one completed dishwasher program."""

    energy_kwh: float
    water_liters: float


PROGRAM_USAGE_ESTIMATES: Final[dict[str, ProgramUsageEstimate]] = {
    "germ": ProgramUsageEstimate(energy_kwh=0.765, water_liters=9.9),
    "eco_wash": ProgramUsageEstimate(energy_kwh=0.99, water_liters=10.4),
    "strong_wash": ProgramUsageEstimate(energy_kwh=1.28, water_liters=13.9),
    "hour_wash": ProgramUsageEstimate(energy_kwh=0.91, water_liters=10.4),
    "soak_wash": ProgramUsageEstimate(energy_kwh=0.02, water_liters=3.4),
    "self_clean": ProgramUsageEstimate(energy_kwh=1.524, water_liters=10.3),
    "fruit_wash": ProgramUsageEstimate(energy_kwh=1.625, water_liters=13.3),
}


class DishwasherMode(IntEnum):
    """Supported E1 dishwasher programs."""

    NONE = 0x00
    AUTO_WASH = 0x01
    STRONG_WASH = 0x02
    STANDARD_WASH = 0x03
    ECO_WASH = 0x04
    GLASS_WASH = 0x05
    HOUR_WASH = 0x06
    FAST_WASH = 0x07
    SOAK_WASH = 0x08
    NINETY_MINUTE = 0x09
    SELF_CLEAN = 0x0A
    FRUIT_WASH = 0x0B
    SELF_DEFINE = 0x0C
    GERM = 0x0D
    BOWL_WASH = 0x0E
    KILL_GERM = 0x0F
    SEAFOOD_WASH = 0x10
    HOT_POT_WASH = 0x12
    QUIET_NIGHT_WASH = 0x13
    LESS_WASH = 0x14
    OIL_NET_WASH = 0x16
    CLOUD_WASH = 0x19


MODE_NAMES: dict[int, str] = {
    DishwasherMode.NONE: "none",
    DishwasherMode.AUTO_WASH: "auto_wash",
    DishwasherMode.STRONG_WASH: "strong_wash",
    DishwasherMode.STANDARD_WASH: "standard_wash",
    DishwasherMode.ECO_WASH: "eco_wash",
    DishwasherMode.GLASS_WASH: "glass_wash",
    DishwasherMode.HOUR_WASH: "hour_wash",
    DishwasherMode.FAST_WASH: "fast_wash",
    DishwasherMode.SOAK_WASH: "soak_wash",
    DishwasherMode.NINETY_MINUTE: "90min",
    DishwasherMode.SELF_CLEAN: "self_clean",
    DishwasherMode.FRUIT_WASH: "fruit_wash",
    DishwasherMode.SELF_DEFINE: "self_define",
    DishwasherMode.GERM: "germ",
    DishwasherMode.BOWL_WASH: "bowl_wash",
    DishwasherMode.KILL_GERM: "kill_germ",
    DishwasherMode.SEAFOOD_WASH: "sea_food_wash",
    DishwasherMode.HOT_POT_WASH: "hot_pot_wash",
    DishwasherMode.QUIET_NIGHT_WASH: "quiet_night_wash",
    DishwasherMode.LESS_WASH: "less_wash",
    DishwasherMode.OIL_NET_WASH: "oil_net_wash",
    DishwasherMode.CLOUD_WASH: "cloud_wash",
}

MODE_CODES = {
    name: code for code, name in MODE_NAMES.items() if code != DishwasherMode.NONE
}

STATUS_NAMES = ("off", "cancel", "delay", "running", "error", "soft_gear")
PROGRESS_NAMES = ("idle", "pre_wash", "wash", "rinse", "dry", "complete")
