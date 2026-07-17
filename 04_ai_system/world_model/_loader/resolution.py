"""
resolution.py — ER-1 deterministic entity resolution (normalization + registry).

Owns three things, and nothing else:

  * `normalize_alias()` — **D-ER-8**, the frozen normalization. Single source: the
    loader normalizes here, Validate compares canonical forms produced here, and
    Emit serialises keys produced here. Any consumer MUST use this same spec.
  * `normalized_pairs()` — shape-aware extraction of authored aliases (**D-ER-11**):
    a single-signal binding takes a flat list (its reserved `state` signal); a
    multi-signal binding takes a per-signal map. **No implicit primary signal.**
  * `build()` — the additive `resolution` block emitted into the compiled artifact.

NAMING ONLY — never authorization. This module never reads `writable`, and the
emitted registry carries **no authorization-adjacent field**, so no consumer can
mistake it for an allowlist. The `ha_call_service` allowlist (D-12, enforced at the
tool boundary) remains the sole authority for what Aurora may actuate (INV-17), and
the resolver is never consulted to permit or deny (D-ER-9).

Additive: the block is a new top-level key. **`ARTIFACT_VERSION` stays 1** (D-ER-7) —
the evaluator pins `SUPPORTED_ARTIFACT_VERSIONS = (1,)` and `bin/aurora-context`
*catches* an artifact error and fails soft to `Home State: Unavailable`, so a bump
would not fail loud; it would silently degrade awareness.
"""

from __future__ import annotations

import re
import unicodedata

from .model import ParsedEntity, domain_of


class ResolutionError(ValueError):
    """A registry invariant was violated at Emit (should be unreachable — Validate
    runs first and fails loud). Never silently drop a target."""


# ── D-ER-8 (frozen) ──────────────────────────────────────────────────────────
# casefold → NFKD → strip combining marks → collapse [\s._-]+ to a single space → trim.
# Stamped into the artifact so a consumer can assert it shares this spec.
NORMALIZATION = "casefold|nfkd|strip-marks|collapse[\\s._-]|trim"

_SEPARATORS = re.compile(r"[\s._-]+")


def normalize_alias(s: str) -> str:
    """The frozen D-ER-8 normalization. `"Conexión a Internet"` → `"conexion a internet"`.

    `ñ → n` is accepted (negligible collision risk on device names). Note this
    collapses `.` to a space, so a NORMALIZED alias can never be id-shaped — which
    is why check 12c tests the RAW authored string instead.
    """
    s = s.casefold()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = _SEPARATORS.sub(" ", s)
    return s.strip()


def authored_map(entity: ParsedEntity) -> dict:
    """signal → authored alias list, per D-ER-11. `{}` when none authored.

    Shape is NOT judged here — that is check 12a, which reports precisely. A flat
    list is attributed to the reserved `state` signal (the single-signal shape);
    if the entity is actually multi-signal, `state` is not a declared signal and
    12a rejects it.
    """
    al = entity.fm.get("aliases")
    if al is None:
        return {}
    if isinstance(al, dict):
        return al
    if isinstance(al, list):
        return {"state": al}
    return {}                       # not a list/map — 12a rejects


def normalized_pairs(entity: ParsedEntity) -> dict:
    """signal → [(authored, normalized)] for every well-formed string alias.

    Defensive by design: this runs at Normalize (stage ③), BEFORE Validate, so it
    must not raise on malformed input. Non-string / empty entries are skipped here
    and rejected by check 12b.
    """
    out: dict = {}
    for signal, names in authored_map(entity).items():
        if not isinstance(names, list):
            continue                # 12a/12b reject
        pairs = [(n, normalize_alias(n)) for n in names
                 if isinstance(n, str) and n.strip()]
        if pairs:
            out[signal] = pairs
    return out


# ── Registry (emitted, additive) ─────────────────────────────────────────────
def build(entities: list[ParsedEntity]) -> dict | None:
    """Compile the `resolution` block. Returns None when no entity carries aliases.

    Deterministic: `aliases` sorted by normalized key; `targets` sorted by
    entity_id; authored alias lists keep authored order.
    """
    aliases: dict[str, str] = {}
    targets: dict[str, dict] = {}
    entities_with_aliases = 0

    for e in sorted(entities, key=lambda x: x.id):
        pairs_by_signal = e.aliases_normalized
        if not pairs_by_signal:
            continue
        entities_with_aliases += 1
        for signal, pairs in pairs_by_signal.items():
            backend = e.binding_signals.get(signal) or {}
            eid = backend.get("ha_entity")
            if not eid:
                # Unreachable: 12a requires an aliased signal to be declared AND to bind
                # ha_entity (D-ER-13), and Validate runs before Emit. Kept as defence in
                # depth — fail loud rather than drop a target silently; silent success is
                # the defect ER-1 exists to kill.
                raise ResolutionError(
                    f"{e.id}: aliased signal {signal!r} has no ha_entity to resolve to")
            targets.setdefault(eid, {
                "entity": e.id,
                "name": e.fm.get("name"),
                "region": e.region,
                "domain": domain_of(eid),
                "signal": signal,
                "aliases": [raw for raw, _ in pairs],
            })
            for _, norm in pairs:
                aliases[norm] = eid

    if not aliases:
        return None

    return {
        "normalization": NORMALIZATION,
        "aliases": {k: aliases[k] for k in sorted(aliases)},
        "targets": {k: targets[k] for k in sorted(targets)},
        "stats": {
            "aliases": len(aliases),
            "targets": len(targets),
            "entities": entities_with_aliases,
        },
    }
