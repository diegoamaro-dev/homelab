"""
hostmod.py — READ-ONLY import of the live HOME_RULES.

Loads `ai-stack/ingest/bin/aurora-context` (an extension-less script with a
`__main__` guard, so importing has no side effects and issues no network call)
and re-exports the detector + its low-level state helpers. The parity harness
reuses these helpers so the ONLY variable under test is the compiled rules vs
detect_home()'s hand-written conditions — not timestamp/state extraction.

aurora-context is never modified.
"""

from __future__ import annotations

import importlib.util
from importlib.machinery import SourceFileLoader
from pathlib import Path

_AC_PATH = Path("/home/diego/homelab/ai-stack/ingest/bin/aurora-context")


def _load():
    loader = SourceFileLoader("aurora_context_readonly", str(_AC_PATH))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)                       # runs defs/constants only (guarded main)
    return mod


_AC = _load()

detect_home = _AC.detect_home
render_home = _AC.render_home
battery_low_devices = _AC._battery_low_devices
state_of = _AC._state
num_of = _AC._num
parse_ts = _AC.parse_ts
iso = _AC.iso
UNAVAIL = _AC.UNAVAIL
HOME_TZ = _AC.HOME_TZ

# For the optional real-data capture (read-only GET /api/states).
read_env = _AC.read_env
fetch_ha_states = _AC.fetch_ha_states
ENV_FILE = _AC.ENV_FILE
HA_TIMEOUT_S = _AC.HA_TIMEOUT_S
