"""
expected.py — frozen expected outcomes for the snapshot regression suite.

FROZEN 2026-07-13 from the final G-WM4-1 differential run against the live
`HOME_RULES` detector (`detect_home()`, retired at WM-4): 32/32 synthetic
engine-equivalence PASS + live real-data parity MATCH (130 real entities;
real `plant_water_warning` reproduced identically). These literals are the
retired oracle's last word — the engine must keep producing exactly this.
Do not edit to make a failing test pass; a mismatch means the engine (or the
model docs) changed behaviour and must be reconciled deliberately.
"""

EXPECTED = {
    'healthy_daytime': [],
    'healthy_overnight': [],
    'bridge_off': [('zigbee_bridge_down', '[critical] Zigbee mesh down — Zigbee devices unavailable')],
    'bridge_unavailable': [('zigbee_bridge_down', '[critical] Zigbee mesh down — Zigbee devices unavailable')],
    'bridge_unknown_notoken': [],
    'wan_off': [('wan_down', '[high] internet (WAN) down')],
    'wan_unavailable_notoken': [],
    'permit_join_on': [('zigbee_permit_join_on', '[high] Zigbee pairing left open (security)')],
    'printer_on_overnight': [('printer_on_overnight', '[medium] 3D printer on overnight')],
    'printer_on_daytime_notoken': [],
    'printer_on_boundary_0559': [('printer_on_overnight', '[medium] 3D printer on overnight')],
    'printer_on_boundary_0600_notoken': [],
    'awning_open_overnight': [('awning_left_extended', '[medium] awning left extended overnight')],
    'awning_open_daytime_notoken': [],
    'door_open_20m': [('door_open_extended', '[medium] main door open >15 min')],
    'door_open_5m_notoken': [],
    'door_open_no_lc_notoken': [],
    'water_warning': [('plant_water_warning', '[low] entrance plant needs water')],
    'water_none_notoken': [],
    'water_unavailable_notoken': [],
    'soil_dry_15': [('plant_soil_dry', '[low] entrance plant soil dry (<20%)')],
    'soil_ok_25_notoken': [],
    'soil_boundary_20_notoken': [],
    'soil_unknown_notoken': [],
    'battery_flag_on': [('device_battery_low', '[low] low battery: Main Door')],
    'battery_pct_15': [('device_battery_low', '[low] low battery: Pasillo motion')],
    'battery_pct_boundary_20': [('device_battery_low', '[low] low battery: Desk button')],
    'battery_cat_low': [('device_battery_low', '[low] low battery: Entrance Plant')],
    'battery_cat_LOW_caseins': [('device_battery_low', '[low] low battery: Entrance Plant')],
    'battery_cat_middle_notoken': [],
    'battery_multi_order': [('device_battery_low', '[low] low battery: Main Door, Entrance Plant, Pasillo motion')],
    'all_nine_overnight': [('zigbee_bridge_down', '[critical] Zigbee mesh down — Zigbee devices unavailable'), ('wan_down', '[high] internet (WAN) down'), ('zigbee_permit_join_on', '[high] Zigbee pairing left open (security)'), ('printer_on_overnight', '[medium] 3D printer on overnight'), ('awning_left_extended', '[medium] awning left extended overnight'), ('door_open_extended', '[medium] main door open >15 min'), ('plant_water_warning', '[low] entrance plant needs water'), ('plant_soil_dry', '[low] entrance plant soil dry (<20%)'), ('device_battery_low', '[low] low battery: Main Door')],
}
