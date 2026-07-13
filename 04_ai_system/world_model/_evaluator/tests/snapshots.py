"""
snapshots.py — enumerated boundary /api/states snapshots (engine regression).

SYNTHETIC INPUTS exercising every rule branch, D7 handling, the duration and
window boundaries, the battery kinds, and full ordering. They are unit-test
fixtures, NOT operational evidence, and assert no real anomaly occurred.

Provenance: migrated 1:1 at WM-4 from the WM-3 parity harness
(`_loader/parity/snapshots.py`, retired with `HOME_RULES`), made
self-contained (no import of the live script). The expected outcomes in
`expected.py` were frozen from the final differential run against the live
`HOME_RULES` detector (G-WM4-1) — the retired oracle's last word.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

HOME_TZ = ZoneInfo("Europe/Madrid")

# Real entity_ids (from the WM-2 bindings).
IDS = {
    "bridge": "binary_sensor.zigbee2mqtt_bridge_connection_state",
    "permit": "switch.zigbee2mqtt_bridge_permit_join",
    "wan": "binary_sensor.rooter_estado_wan",
    "printer": "switch.impresora_3d",
    "awning": "cover.toldo",
    "door": "binary_sensor.sensor_puerta_principal_contact",
    "water": "sensor.sensor_planta_entrada_water_warning",
    "soil": "sensor.sensor_planta_entrada_soil_moisture",
    "door_bat_flag": "binary_sensor.sensor_puerta_principal_battery_low",
    "door_bat_pct": "sensor.sensor_puerta_principal_battery",
    "plant_bat_cat": "sensor.sensor_planta_entrada_battery_state",
    "pasillo_bat": "sensor.sensor_pasillo_battery",
    "entrada_bat": "sensor.sensor_entarda_battery",
    "desk_bat": "sensor.0x842712fffe3217d0_battery",
}


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_now(hour: int, minute: int = 0):
    local = datetime(2026, 7, 2, hour, minute, tzinfo=HOME_TZ)
    return local.astimezone(timezone.utc), local


def nominal(now_utc: datetime) -> dict:
    def s(state: str, last_changed: str | None = None) -> dict:
        return {"state": state,
                "last_changed": last_changed if last_changed is not None else _iso(now_utc)}

    return {
        IDS["bridge"]: s("on"),
        IDS["permit"]: s("off"),
        IDS["wan"]: s("on"),
        IDS["printer"]: s("off"),
        IDS["awning"]: s("closed"),
        IDS["door"]: s("off"),
        IDS["water"]: s("none"),
        IDS["soil"]: s("74"),
        IDS["door_bat_flag"]: s("off"),
        IDS["door_bat_pct"]: s("100"),
        IDS["plant_bat_cat"]: s("middle"),
        IDS["pasillo_bat"]: s("100"),
        IDS["entrada_bat"]: s("100"),
        IDS["desk_bat"]: s("100"),
    }


def _ago(now_utc: datetime, minutes: int) -> str:
    return _iso(now_utc - timedelta(minutes=minutes))


def cases() -> list[dict]:
    out: list[dict] = []

    def add(name, hour, mutate=None, minute=0):
        now_utc, now_local = build_now(hour, minute)
        st = nominal(now_utc)
        if mutate:
            mutate(st, now_utc)
        out.append({"name": name, "states": st, "now_utc": now_utc, "now_local": now_local})

    add("healthy_daytime", 12)
    add("healthy_overnight", 3)
    add("bridge_off", 12, lambda st, n: st.update({IDS["bridge"]: {"state": "off"}}))
    add("bridge_unavailable", 12, lambda st, n: st.update({IDS["bridge"]: {"state": "unavailable"}}))
    add("bridge_unknown_notoken", 12, lambda st, n: st.update({IDS["bridge"]: {"state": "unknown"}}))
    add("wan_off", 12, lambda st, n: st.update({IDS["wan"]: {"state": "off"}}))
    add("wan_unavailable_notoken", 12, lambda st, n: st.update({IDS["wan"]: {"state": "unavailable"}}))
    add("permit_join_on", 12, lambda st, n: st.update({IDS["permit"]: {"state": "on"}}))
    add("printer_on_overnight", 3, lambda st, n: st.update({IDS["printer"]: {"state": "on"}}))
    add("printer_on_daytime_notoken", 12, lambda st, n: st.update({IDS["printer"]: {"state": "on"}}))
    add("printer_on_boundary_0559", 5, lambda st, n: st.update({IDS["printer"]: {"state": "on"}}), minute=59)
    add("printer_on_boundary_0600_notoken", 6, lambda st, n: st.update({IDS["printer"]: {"state": "on"}}))
    add("awning_open_overnight", 3, lambda st, n: st.update({IDS["awning"]: {"state": "open"}}))
    add("awning_open_daytime_notoken", 12, lambda st, n: st.update({IDS["awning"]: {"state": "open"}}))
    add("door_open_20m", 12, lambda st, n: st.update({IDS["door"]: {"state": "on", "last_changed": _ago(n, 20)}}))
    add("door_open_5m_notoken", 12, lambda st, n: st.update({IDS["door"]: {"state": "on", "last_changed": _ago(n, 5)}}))
    add("door_open_no_lc_notoken", 12, lambda st, n: st.update({IDS["door"]: {"state": "on"}}))
    add("water_warning", 12, lambda st, n: st.update({IDS["water"]: {"state": "warning"}}))
    add("water_none_notoken", 12, lambda st, n: st.update({IDS["water"]: {"state": "none"}}))
    add("water_unavailable_notoken", 12, lambda st, n: st.update({IDS["water"]: {"state": "unavailable"}}))
    add("soil_dry_15", 12, lambda st, n: st.update({IDS["soil"]: {"state": "15"}}))
    add("soil_ok_25_notoken", 12, lambda st, n: st.update({IDS["soil"]: {"state": "25"}}))
    add("soil_boundary_20_notoken", 12, lambda st, n: st.update({IDS["soil"]: {"state": "20"}}))
    add("soil_unknown_notoken", 12, lambda st, n: st.update({IDS["soil"]: {"state": "unknown"}}))
    add("battery_flag_on", 12, lambda st, n: st.update({IDS["door_bat_flag"]: {"state": "on"}}))
    add("battery_pct_15", 12, lambda st, n: st.update({IDS["pasillo_bat"]: {"state": "15"}}))
    add("battery_pct_boundary_20", 12, lambda st, n: st.update({IDS["desk_bat"]: {"state": "20"}}))
    add("battery_cat_low", 12, lambda st, n: st.update({IDS["plant_bat_cat"]: {"state": "low"}}))
    add("battery_cat_LOW_caseins", 12, lambda st, n: st.update({IDS["plant_bat_cat"]: {"state": "LOW"}}))
    add("battery_cat_middle_notoken", 12, lambda st, n: st.update({IDS["plant_bat_cat"]: {"state": "middle"}}))

    def multi_battery(st, n):
        st.update({
            IDS["door_bat_flag"]: {"state": "on"},
            IDS["plant_bat_cat"]: {"state": "empty"},
            IDS["pasillo_bat"]: {"state": "10"},
        })
    add("battery_multi_order", 12, multi_battery)

    def all_nine(st, n):
        st.update({
            IDS["bridge"]: {"state": "off"},
            IDS["wan"]: {"state": "off"},
            IDS["permit"]: {"state": "on"},
            IDS["printer"]: {"state": "on"},
            IDS["awning"]: {"state": "open"},
            IDS["door"]: {"state": "on", "last_changed": _ago(n, 30)},
            IDS["water"]: {"state": "warning"},
            IDS["soil"]: {"state": "5"},
            IDS["door_bat_flag"]: {"state": "on"},
        })
    add("all_nine_overnight", 3, all_nine)

    return out
