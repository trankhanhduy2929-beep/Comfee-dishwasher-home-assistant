"""Constants for the Comfee dishwasher integration."""

from enum import IntEnum

DOMAIN = "comfee_dishwasher"
CONF_ACCOUNT = "account"
CONF_KEY = "key"
CONF_SUBTYPE = "subtype"
CONF_MAC = "mac"
CONF_SERIAL_NUMBER = "serial_number"
CONF_KEY_METHOD = "key_method"
CONF_DEVICE = "device"

DEVICE_TYPE_DISHWASHER = 0xE1
DEFAULT_PORT = 6444
DEFAULT_PROTOCOL = 3
WRITABLE_ATTRIBUTES = frozenset({"power", "child_lock", "storage"})


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
