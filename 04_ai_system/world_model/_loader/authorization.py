"""
authorization.py — D-12 allowlist reference for validation check 11a (INV-17).

DESCRIPTIVE MIRROR, NEVER A GRANT. This is a read-only transcription of the
enforced allowlist `_ALLOWED_DOMAINS` in
`ai-stack/openwebui-tools/tools/ha_call_service.py` (the runtime safety boundary,
D-12). The loader uses it to prove that a `writable: true` entity's action surface
is a SUBSET of the enforced authorization. It confers no authority: the tool's
frozenset remains the sole enforcement point (INV-17 / Vision §7).

Keep in sync with the tool. Adding a domain here changes nothing at runtime.
"""

from __future__ import annotations

from .model import ParsedEntity, domain_of

# Mirror of ha_call_service.py `_ALLOWED_DOMAINS` (D-12, closed for v1).
ALLOWED_DOMAINS = frozenset({
    "light", "switch", "scene", "cover", "climate", "media_player",
    "script", "automation", "fan", "vacuum",
    "input_boolean", "input_select", "input_number",
})

# Mirror of `_EXPLICITLY_DENIED` (documented default-deny; belt-and-braces).
DENIED_DOMAINS = frozenset({
    "homeassistant", "recorder", "hassio", "system_log", "backup",
    "auth", "persistent_notification", "notify", "mqtt",
})


def action_domains(entity: ParsedEntity) -> list[str]:
    """The HA domains an entity would actuate (from its single-signal binding)."""
    domains: list[str] = []
    if entity.binding_shape == "single":
        eid = (entity.binding_signals.get("state") or {}).get("ha_entity")
        if eid and (d := domain_of(eid)):
            domains.append(d)
    return domains


def check(entity: ParsedEntity) -> list[str]:
    """Return authorization violations (11a). Empty list = ok."""
    if not entity.writable:
        return []
    domains = action_domains(entity)
    if not domains:
        return [f"{entity.id}: writable:true but no actuable HA domain resolvable from binding"]
    problems: list[str] = []
    for d in domains:
        if d in DENIED_DOMAINS:
            problems.append(f"{entity.id}: writable domain {d!r} is in the D-12 deny set")
        elif d not in ALLOWED_DOMAINS:
            problems.append(f"{entity.id}: writable domain {d!r} is not in the D-12 allowlist (INV-17)")
    return problems
