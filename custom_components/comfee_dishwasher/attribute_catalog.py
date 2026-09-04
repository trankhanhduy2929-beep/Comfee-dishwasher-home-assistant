"""Human-friendly hints for raw Midea local attributes."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AttributeHint:
    """Presentation metadata for one raw driver attribute."""

    name_vi: str
    name_en: str
    icon: str
    unit: str | None = None
    sensor_device_class: str | None = None
    state_class: str | None = None
    binary_device_class: str | None = None


_NAMES: dict[str, tuple[str, str]] = {
    "power": ("Nguồn", "Power"),
    "main_power": ("Nguồn chính", "Main power"),
    "status": ("Trạng thái", "Status"),
    "mode": ("Chế độ", "Mode"),
    "progress": ("Tiến độ", "Progress"),
    "start": ("Lệnh khởi động", "Start command"),
    "door": ("Cửa", "Door"),
    "child_lock": ("Khóa trẻ em", "Child lock"),
    "storage": ("Bảo quản / sấy khí", "Storage / air dry"),
    "storage_status": ("Đang bảo quản / sấy khí", "Storage / air dry active"),
    "storage_remaining": ("Thời gian bảo quản còn lại", "Storage time remaining"),
    "time_remaining": ("Thời gian còn lại", "Time remaining"),
    "working_time": ("Thời gian hoạt động", "Working time"),
    "wash_time": ("Thời gian rửa", "Wash time"),
    "keep_warm_time": ("Thời gian giữ ấm", "Keep-warm time"),
    "keep_warm_remaining": ("Thời gian giữ ấm còn lại", "Keep-warm time remaining"),
    "current_temperature": ("Nhiệt độ hiện tại", "Current temperature"),
    "target_temperature": ("Nhiệt độ mục tiêu", "Target temperature"),
    "temperature": ("Nhiệt độ", "Temperature"),
    "temperature_min": ("Nhiệt độ thấp nhất", "Minimum temperature"),
    "temperature_max": ("Nhiệt độ cao nhất", "Maximum temperature"),
    "indoor_temperature": ("Nhiệt độ trong nhà", "Indoor temperature"),
    "outdoor_temperature": ("Nhiệt độ ngoài trời", "Outdoor temperature"),
    "humidity": ("Độ ẩm", "Humidity"),
    "current_humidity": ("Độ ẩm hiện tại", "Current humidity"),
    "target_humidity": ("Độ ẩm mục tiêu", "Target humidity"),
    "indoor_humidity": ("Độ ẩm trong nhà", "Indoor humidity"),
    "pm25": ("Bụi mịn PM2.5", "PM2.5"),
    "co2": ("Nồng độ CO₂", "CO₂ concentration"),
    "tvoc": ("Hợp chất hữu cơ bay hơi", "TVOC"),
    "hcho": ("Nồng độ formaldehyde", "Formaldehyde"),
    "battery_percent": ("Pin còn lại", "Battery level"),
    "filter_life": ("Tuổi thọ bộ lọc", "Filter life"),
    "filter1_life": ("Tuổi thọ bộ lọc 1", "Filter 1 life"),
    "filter2_life": ("Tuổi thọ bộ lọc 2", "Filter 2 life"),
    "filter3_life": ("Tuổi thọ bộ lọc 3", "Filter 3 life"),
    "life1": ("Tuổi thọ lõi lọc 1", "Filter 1 life"),
    "life2": ("Tuổi thọ lõi lọc 2", "Filter 2 life"),
    "life3": ("Tuổi thọ lõi lọc 3", "Filter 3 life"),
    "energy_consumption": ("Điện năng tiêu thụ", "Energy consumption"),
    "total_energy_consumption": ("Tổng điện năng tiêu thụ", "Total energy consumption"),
    "current_energy_consumption": ("Điện năng hiện tại", "Current energy consumption"),
    "total_produced_energy": ("Tổng nhiệt năng tạo ra", "Total produced energy"),
    "water_consumption": ("Lượng nước tiêu thụ", "Water consumption"),
    "water_consumption_big": ("Tổng lượng nước tiêu thụ", "Total water consumption"),
    "water_consumption_average": (
        "Lượng nước tiêu thụ trung bình",
        "Average water consumption",
    ),
    "day_water_consumption": (
        "Lượng nước tiêu thụ trong ngày",
        "Daily water consumption",
    ),
    "water_flow": ("Lưu lượng nước", "Water flow"),
    "velocity": ("Lưu lượng nước", "Water flow rate"),
    "water_level": ("Mức nước", "Water level"),
    "water_level_set": ("Mức nước cài đặt", "Water level setting"),
    "tank": ("Mức bình chứa", "Tank level"),
    "tank_full": ("Bình chứa đầy", "Tank full"),
    "left_salt": ("Lượng muối còn lại", "Salt remaining"),
    "remaining_days": ("Số ngày còn lại", "Days remaining"),
    "use_days": ("Số ngày đã sử dụng", "Days used"),
    "brightness": ("Độ sáng", "Brightness"),
    "color_temperature": ("Nhiệt độ màu", "Color temperature"),
    "fan_speed": ("Tốc độ quạt", "Fan speed"),
    "fan_speed_level": ("Mức tốc độ quạt", "Fan speed level"),
    "fan_level": ("Mức quạt", "Fan level"),
    "dehydration_speed": ("Tốc độ vắt", "Spin speed"),
    "fire_power": ("Mức công suất lửa", "Fire power"),
    "heating_power": ("Công suất gia nhiệt", "Heating power"),
    "realtime_power": ("Công suất tức thời", "Real-time power"),
    "compressor_power": ("Công suất máy nén", "Compressor power"),
    "instant_power0": ("Công suất tức thời", "Instant power"),
    "compressor_current": ("Dòng máy nén", "Compressor current"),
    "compressor_voltage": ("Điện áp máy nén", "Compressor voltage"),
    "compressor_frequency": ("Tần số máy nén", "Compressor frequency"),
    "target_compressor_frequency": (
        "Tần số máy nén mục tiêu",
        "Target compressor frequency",
    ),
    "error_code": ("Mã lỗi", "Error code"),
    "error": ("Lỗi", "Error"),
    "error_type": ("Loại lỗi", "Error type"),
    "error_desc": ("Mô tả lỗi", "Error description"),
    "wrong_operation": ("Mã thao tác sai", "Wrong-operation code"),
    "additional": ("Mã tùy chọn bổ sung", "Additional option code"),
    "rinse_aid": ("Thiếu chất trợ xả", "Rinse-aid shortage"),
    "salt": ("Thiếu muối", "Salt shortage"),
    "water_lack": ("Thiếu nước", "Water shortage"),
    "water_shortage": ("Thiếu nước", "Water shortage"),
    "water_change_reminder": ("Nhắc thay nước", "Water-change reminder"),
    "filter_cleaning_reminder": ("Nhắc vệ sinh bộ lọc", "Filter-cleaning reminder"),
    "cleaning_reminder": ("Nhắc vệ sinh", "Cleaning reminder"),
    "door_warn": ("Cảnh báo cửa", "Door warning"),
    "uv": ("Khử khuẩn UV", "UV sterilization"),
    "dry": ("Chế độ sấy", "Drying option"),
    "dry_status": ("Đang sấy", "Drying"),
    "waterswitch": ("Van cấp nước", "Water inlet"),
    "water_pump": ("Bơm nước", "Water pump"),
    "water_pump_running": ("Bơm nước đang chạy", "Water pump running"),
    "prompt_tone": ("Âm báo", "Prompt tone"),
    "screen_display": ("Màn hình", "Screen display"),
    "display_on_off": ("Hiển thị màn hình", "Display"),
    "screen_status": ("Trạng thái màn hình", "Screen status"),
    "anion": ("Ion âm", "Anion"),
    "oscillate": ("Đảo gió", "Oscillation"),
    "oscillation_angle": ("Góc đảo gió", "Oscillation angle"),
    "tilting_angle": ("Góc nghiêng", "Tilting angle"),
    "light": ("Đèn", "Light"),
    "main_light": ("Đèn chính", "Main light"),
    "night_light": ("Đèn ngủ", "Night light"),
    "ventilation": ("Thông gió", "Ventilation"),
    "smelly_sensor": ("Cảm biến mùi", "Odor sensor"),
    "current_radar": ("Phát hiện chuyển động", "Motion detected"),
    "refrigerator_actual_temp": ("Nhiệt độ ngăn mát", "Refrigerator temperature"),
    "freezer_actual_temp": ("Nhiệt độ ngăn đông", "Freezer temperature"),
    "flex_zone_actual_temp": ("Nhiệt độ ngăn linh hoạt", "Flex-zone temperature"),
    "refrigerator_setting_temp": ("Nhiệt độ cài đặt ngăn mát", "Refrigerator setpoint"),
    "freezer_setting_temp": ("Nhiệt độ cài đặt ngăn đông", "Freezer setpoint"),
    "cooking": ("Đang nấu", "Cooking"),
    "keep_warm": ("Giữ ấm", "Keep warm"),
    "finished": ("Đã hoàn tất", "Finished"),
    "with_pressure": ("Có áp suất", "Pressure active"),
    "power_saving": ("Tiết kiệm điện", "Power saving"),
    "eco_mode": ("Chế độ tiết kiệm", "Eco mode"),
    "sleep_mode": ("Chế độ ngủ", "Sleep mode"),
    "aux_heating": ("Gia nhiệt phụ", "Auxiliary heating"),
    "boost_mode": ("Tăng cường", "Boost mode"),
    "breezeless": ("Chế độ không gió buốt", "Breezeless"),
    "comfort_mode": ("Chế độ thoải mái", "Comfort mode"),
    "frost_protect": ("Chống đóng băng", "Frost protection"),
    "indirect_wind": ("Tránh gió thổi trực tiếp", "Indirect wind"),
    "natural_wind": ("Gió tự nhiên", "Natural wind"),
    "out_silent": ("Chế độ dàn nóng yên lặng", "Outdoor silent mode"),
    "screen_display_alternate": (
        "Hiển thị màn hình thay thế",
        "Alternate screen display",
    ),
    "self_clean": ("Tự làm sạch", "Self-clean"),
    "smart_eye": ("Mắt thần thông minh", "Smart eye"),
    "sound": ("Âm thanh", "Sound"),
    "swing": ("Đảo gió", "Swing"),
    "swing_horizontal": ("Đảo gió ngang", "Horizontal swing"),
    "swing_vertical": ("Đảo gió dọc", "Vertical swing"),
    "disinfect": ("Khử khuẩn", "Disinfection"),
    "sterilization": ("Tiệt khuẩn", "Sterilization"),
    "cl_sterilization": ("Khử khuẩn bằng clo", "Chlorine sterilization"),
    "leak_water_protection": ("Bảo vệ rò rỉ nước", "Water-leak protection"),
    "regeneration": ("Hoàn nguyên bộ làm mềm", "Softener regeneration"),
    "soften": ("Làm mềm nước", "Water softening"),
    "water_way": ("Đường nước", "Water path"),
    "softwater": ("Mức làm mềm nước", "Water-softener level"),
    "soft_available": ("Nước làm mềm còn lại", "Soft-water available"),
    "cold_water_dot": ("Kích hoạt nước nóng không chờ", "Pulsed zero-cold water"),
    "cold_water_single": ("Nước nóng không chờ một lần", "Single zero-cold water"),
    "dhw_power": ("Nguồn nước nóng sinh hoạt", "Domestic hot-water power"),
    "fast_dhw": ("Nước nóng sinh hoạt nhanh", "Fast domestic hot water"),
    "silent_mode": ("Chế độ yên lặng", "Silent mode"),
    "smart_volume": ("Điều chỉnh công suất thông minh", "Smart volume"),
    "tbh": ("Gia nhiệt bổ sung bình nước", "Tank backup heater"),
    "vacation_mode": ("Chế độ kỳ nghỉ", "Vacation mode"),
    "variable_heating": ("Gia nhiệt biến đổi", "Variable heating"),
    "whole_tank_heating": ("Gia nhiệt toàn bình", "Whole-tank heating"),
    "zero_cold_water": ("Nước nóng không chờ", "Zero-cold water"),
    "zone1_curve": ("Đường cong nhiệt vùng 1", "Zone 1 heating curve"),
    "zone1_power": ("Nguồn vùng 1", "Zone 1 power"),
    "zone2_curve": ("Đường cong nhiệt vùng 2", "Zone 2 heating curve"),
    "zone2_power": ("Nguồn vùng 2", "Zone 2 power"),
    "foam_shield": ("Lớp chắn bọt", "Foam shield"),
    "sensor_light": ("Đèn cảm biến", "Sensor light"),
    "humidify": ("Tạo ẩm", "Humidification"),
    "waterions": ("Ion hóa nước", "Water ionization"),
    "link_to_ac": ("Liên kết với điều hòa", "Link to air conditioner"),
    "powerful_purify": ("Lọc không khí tăng cường", "Powerful purification"),
    "pump": ("Bơm nước", "Pump"),
    "standby": ("Chế độ chờ", "Standby"),
    "in_tds": ("TDS nước đầu vào", "Input TDS"),
    "out_tds": ("TDS nước đầu ra", "Output TDS"),
    "volume": ("Dung tích", "Volume"),
    "rate": ("Mức công suất", "Rate"),
    "work_time": ("Thời gian làm việc", "Work time"),
    "work_status": ("Trạng thái làm việc", "Work status"),
    "move_direction": ("Hướng di chuyển", "Move direction"),
    "clean_mode": ("Chế độ làm sạch", "Cleaning mode"),
    "mop": ("Cây lau nhà", "Mop"),
    "carpet_switch": ("Nhận diện thảm", "Carpet detection"),
    "uv_switch": ("Đèn UV", "UV light"),
    "voice_switch": ("Điều khiển giọng nói", "Voice control"),
    "wifi_switch": ("Wi-Fi thiết bị", "Device Wi-Fi"),
}


_ICONS: dict[str, str] = {
    "power": "mdi:power",
    "status": "mdi:information-outline",
    "mode": "mdi:tune-variant",
    "progress": "mdi:progress-check",
    "door": "mdi:door",
    "temperature": "mdi:thermometer",
    "humidity": "mdi:water-percent",
    "pm25": "mdi:blur",
    "co2": "mdi:molecule-co2",
    "tvoc": "mdi:chemical-weapon",
    "hcho": "mdi:flask-outline",
    "energy_consumption": "mdi:lightning-bolt",
    "water_consumption": "mdi:water",
    "water_flow": "mdi:water-pump",
    "fan_speed": "mdi:fan",
    "color_temperature": "mdi:temperature-kelvin",
    "error_code": "mdi:alert-box-outline",
    "error": "mdi:alert-circle",
    "battery_percent": "mdi:battery",
    "filter_life": "mdi:air-filter",
    "light": "mdi:lightbulb",
    "current_radar": "mdi:motion-sensor",
    "work_status": "mdi:robot-vacuum",
}

DEFAULT_ENABLED_SENSOR_KEYS = frozenset(
    {
        "battery_percent",
        "co2",
        "current_humidity",
        "current_temperature",
        "energy_consumption",
        "error_code",
        "hcho",
        "humidity",
        "indoor_humidity",
        "indoor_temperature",
        "mode",
        "outdoor_temperature",
        "pm25",
        "progress",
        "program",
        "realtime_power",
        "status",
        "target_humidity",
        "target_temperature",
        "temperature",
        "time_remaining",
        "total_energy_consumption",
        "tvoc",
        "water_consumption",
        "work_status",
    },
)

DEFAULT_ENABLED_BINARY_KEYS = frozenset(
    {
        "current_radar",
        "device_error",
        "door",
        "door_warn",
        "finished",
        "filter_cleaning_reminder",
        "leak_water",
        "tank_full",
        "water_lack",
        "water_shortage",
    },
)

_NULLABLE_BINARY_KEYS = frozenset(
    {
        "arofene_link",
        "auto_aux_heat_running",
        "bar_door",
        "bar_door_overtime",
        "bathing_working",
        "bottom_compartment_cooling",
        "bottom_compartment_door",
        "bottom_compartment_preheating",
        "bottom_elec_heat",
        "burning_state",
        "child_lock",
        "clean_scale",
        "clean_sink_ponding",
        "cleaning_reminder",
        "compressor_status",
        "cooking",
        "current_radar",
        "disinfect",
        "discharge_status",
        "dispensing",
        "dissipate_heat",
        "door",
        "door_warn",
        "eco",
        "electronic_smell",
        "error",
        "fall_asleep_status",
        "fault",
        "filter_change_reminder",
        "filter_cleaning_reminder",
        "finished",
        "flex_zone_door",
        "flex_zone_door_overtime",
        "flip_side",
        "freezer_door",
        "freezer_door_overtime",
        "full_dust",
        "header_exist",
        "header_led_status",
        "heating",
        "heating_working",
        "high_temperature",
        "high_temperature_lock",
        "high_temperature_work",
        "hot_water_dispensing",
        "keep_warm",
        "lack_water",
        "leak_water",
        "led_status",
        "lid_status",
        "light_status",
        "maintain_warn",
        "maintenance_reminder",
        "microcrystal_fresh",
        "middle_compartment_cooling",
        "middle_compartment_door",
        "middle_compartment_preheating",
        "multi_terminal",
        "mute_effect",
        "mute_status",
        "night_mode",
        "oilcup_full",
        "order1_effect",
        "order2_effect",
        "portable_sense",
        "pre_heat",
        "presets_function",
        "probe",
        "probe_mode",
        "protection",
        "radar_exist",
        "reaction",
        "refrigerator_door",
        "refrigerator_door_overtime",
        "rinse_aid",
        "rsj_stand_by",
        "salt",
        "screen_status",
        "seat_status",
        "smart_grid",
        "standby",
        "status_dhw",
        "status_heating",
        "status_ibh",
        "status_tbh",
        "tank_ejected",
        "tank_full",
        "top_compartment_cooling",
        "top_compartment_door",
        "top_compartment_preheating",
        "top_elec_heat",
        "water_change_reminder",
        "water_flow",
        "water_pump_running",
        "water_shortage",
        "with_pressure",
        "zone1_room_temp_mode",
        "zone1_water_temp_mode",
        "zone2_room_temp_mode",
        "zone2_water_temp_mode",
    },
)

_RUNNING_BINARY_KEYS = frozenset(
    {
        "bathing_working",
        "burning_state",
        "cooking",
        "dispensing",
        "dissipate_heat",
        "heating",
        "heating_working",
        "hot_water_dispensing",
        "status_dhw",
        "status_heating",
        "status_ibh",
        "status_tbh",
        "water_pump_running",
    },
)


def _humanize(key: str) -> str:
    """Make an unknown snake-case attribute readable."""
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", key).replace("_", " ")
    return " ".join(text.split()).capitalize()


def attribute_hint(key: Any) -> AttributeHint:
    """Return localized presentation metadata for an attribute."""
    name = str(key)
    name_vi, name_en = _NAMES.get(
        name,
        (f"Thông số {_humanize(name)}", _humanize(name)),
    )
    icon = _ICONS.get(name)
    lowered = name.casefold()
    if icon is None:
        if "temperature" in lowered or lowered.startswith("temp"):
            icon = "mdi:thermometer"
        elif "humidity" in lowered:
            icon = "mdi:water-percent"
        elif "water" in lowered or "tank" in lowered:
            icon = "mdi:water"
        elif "energy" in lowered or "power" in lowered:
            icon = "mdi:lightning-bolt"
        elif "error" in lowered or "warning" in lowered:
            icon = "mdi:alert-circle-outline"
        elif "door" in lowered:
            icon = "mdi:door"
        else:
            icon = "mdi:information-outline"

    if lowered == "color_temperature":
        return AttributeHint(
            name_vi,
            name_en,
            icon,
            "kelvin",
            None,
            "measurement",
        )
    if "temperature" in lowered or lowered.startswith("temp"):
        return AttributeHint(
            name_vi,
            name_en,
            icon,
            "temperature",
            "temperature",
            "measurement",
        )
    if "humidity" in lowered:
        return AttributeHint(
            name_vi,
            name_en,
            icon,
            "percentage",
            "humidity",
            "measurement",
        )
    if lowered in {"pm25", "pm2.5"}:
        return AttributeHint(name_vi, name_en, icon, "density", "pm25", "measurement")
    if lowered == "co2":
        return AttributeHint(name_vi, name_en, icon, "ppm", "co2", "measurement")
    if lowered == "tvoc":
        return AttributeHint(name_vi, name_en, icon, "ppm", "tvoc", "measurement")
    if lowered == "hcho":
        return AttributeHint(name_vi, name_en, icon, "density", "hcho", "measurement")
    if lowered in {"in_tds", "out_tds"}:
        return AttributeHint(name_vi, name_en, icon, "ppm", None, "measurement")
    if "energy" in lowered:
        total = lowered.startswith("total") or "consumption" in lowered
        return AttributeHint(
            name_vi,
            name_en,
            icon,
            "energy",
            "energy",
            "total_increasing" if total else "measurement",
        )
    if any(
        token in lowered
        for token in (
            "realtime_power",
            "instant_power",
            "compressor_power",
            "heating_power",
            "fast_hot_power",
        )
    ):
        return AttributeHint(name_vi, name_en, icon, "power", "power", "measurement")
    if "voltage" in lowered:
        return AttributeHint(
            name_vi, name_en, icon, "voltage", "voltage", "measurement"
        )
    if "current" in lowered and "temperature" not in lowered:
        return AttributeHint(
            name_vi, name_en, icon, "current", "current", "measurement"
        )
    if "frequency" in lowered:
        return AttributeHint(
            name_vi, name_en, icon, "frequency", "frequency", "measurement"
        )
    if "dehydration_speed" in lowered or lowered.endswith("_rpm"):
        return AttributeHint(name_vi, name_en, icon, "rpm", None, "measurement")
    if any(
        token in lowered
        for token in (
            "time_remaining",
            "working_time",
            "wash_time",
            "keep_warm_time",
            "keep_warm_remaining",
        )
    ):
        return AttributeHint(
            name_vi, name_en, icon, "minutes", "duration", "measurement"
        )
    if lowered.endswith("_days") or lowered in {"remaining_days", "use_days"}:
        return AttributeHint(name_vi, name_en, icon, "days", "duration", "measurement")
    if lowered.endswith("_seconds"):
        return AttributeHint(
            name_vi, name_en, icon, "seconds", "duration", "measurement"
        )
    if "water_consumption" in lowered:
        state_class = (
            "measurement"
            if "average" in lowered or lowered.startswith("day_")
            else "total_increasing"
        )
        return AttributeHint(name_vi, name_en, icon, "volume", "water", state_class)
    if lowered in {"soft_available", "soft_available_big", "volume"}:
        return AttributeHint(name_vi, name_en, icon, "volume", "volume", "measurement")
    if lowered in {
        "battery_percent",
        "filter_life",
        "filter1_life",
        "filter2_life",
        "filter3_life",
        "life1",
        "life2",
        "life3",
        "brightness",
        "tank",
    }:
        return AttributeHint(name_vi, name_en, icon, "percentage", None, "measurement")
    if lowered in {"door", "door_warn", "lid_status"} or lowered.endswith("_door"):
        return AttributeHint(name_vi, name_en, icon, binary_device_class="opening")
    if "radar" in lowered or "motion" in lowered:
        return AttributeHint(name_vi, name_en, icon, binary_device_class="motion")
    if any(
        token in lowered
        for token in (
            "error",
            "fault",
            "full",
            "lack",
            "leak",
            "reminder",
            "shortage",
            "warning",
        )
    ):
        return AttributeHint(name_vi, name_en, icon, binary_device_class="problem")
    if lowered in _RUNNING_BINARY_KEYS or lowered.endswith(
        ("_cooling", "_preheating", "_running", "_working")
    ):
        return AttributeHint(name_vi, name_en, icon, binary_device_class="running")
    return AttributeHint(name_vi, name_en, icon)


def is_scalar_attribute(value: Any) -> bool:
    """Return whether a value can be represented safely as an HA state."""
    return value is None or isinstance(
        value, (bool, int, float, str, list, tuple, dict)
    )


def is_binary_attribute(key: Any, value: Any) -> bool:
    """Return whether an attribute should be represented as a binary sensor."""
    if isinstance(value, bool):
        return True
    if value is not None:
        return False
    name = str(key).casefold()
    return name in _NULLABLE_BINARY_KEYS or name.endswith(
        (
            "_door",
            "_door_overtime",
            "_reminder",
            "_shortage",
            "_working",
            "_running",
        ),
    )
