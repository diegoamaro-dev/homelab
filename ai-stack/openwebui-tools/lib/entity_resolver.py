"""
amarolab_entity_resolver — inline-only helper text (ER-1.4).

The deterministic bridge between natural language and real Home Assistant
`entity_id`s. Canonical source of the resolver that `ha_get_state` and
`ha_call_service` inline via ../bin/install_tool.

Do NOT `import` this file from a Tool. Open WebUI 0.8.10 executes each Tool in
its own `tool_{id}` module namespace; cross-module imports do not resolve. This
is the same constraint that makes lib/audit_helper.py inline-only.

Convention: at install time, `bin/install_tool` replaces the literal marker

    # @@AMAROLAB_INLINE:entity_resolver@@

in a Tool source with everything between the `# --- INLINE START ---` and
`# --- INLINE END ---` lines below. Everything outside those markers (including
this docstring) is dropped.

NAMING ONLY — never authorization. This resolver is never consulted to permit or
deny (D-ER-9). It reads no authorization field, and the projection carries none.
The `ha_call_service` allowlist (D-12, enforced at the tool boundary) remains the
sole authority for what Aurora may actuate (INV-17).

Not on the awareness path (INV-19): this reads the projection, never raw signals,
and never feeds `home.anomalies` or the context block.

Symbols are prefixed `_amarolab_er_` / `_AMAROLAB_ER_` so they cannot collide
with lib/audit_helper.py's symbols in the shared Tool namespace, and so Open
WebUI's `get_functions_from_tool` does not treat them as Tool methods. Each
inline block re-imports what it needs under its own aliases, so the two are
order-independent.

Exposed inlined symbols:

    _amarolab_er_normalize(s) -> str          D-ER-8 frozen normalization
    _EntityResolver.available() -> bool
    _EntityResolver.lookup(raw) -> str | None closed alias lookup
    _EntityResolver.is_target(id) -> bool | None
    _EntityResolver.candidates(limit=8) -> list[dict]

Projection source (read-only bind mount, ER-1.3):
    container: /opt/aurora/aurora-entities.json
    host:      /home/diego/homelab/ai-stack/aurora/aurora-entities.json
"""

# --- INLINE START ---
import json as _amarolab_er_json
import os as _amarolab_er_os
import re as _amarolab_er_re
import unicodedata as _amarolab_er_unicodedata
from pathlib import Path as _amarolab_er_path

_AMAROLAB_ER_PROJECTION = _amarolab_er_path(_amarolab_er_os.environ.get(
    "AMAROLAB_ENTITY_PROJECTION",
    "/opt/aurora/aurora-entities.json",
))

# The projection contract this resolver is built against. Both are hard pins:
# a projection that does not match is REFUSED rather than read on a guess.
#
# `_AMAROLAB_ER_NORMALIZATION` is the D-ER-8 string the loader stamps into the
# artifact precisely "so a consumer can assert it shares this spec"
# (_loader/resolution.py). Resolving against a registry whose keys were
# normalized under a different spec would silently return wrong ids — the exact
# class of quiet wrongness ER-1 exists to remove. Refusing is the honest answer:
# it surfaces as `resolver_unavailable` at the tool boundary, and direct
# entity_ids keep working regardless (D-ER-9).
_AMAROLAB_ER_PROJECTION_VERSION = 1
_AMAROLAB_ER_NORMALIZATION = "casefold|nfkd|strip-marks|collapse[\\s._-]|trim"

# Bounded candidate list (spec §4 step 6). Names + ids only — AD-18-safe.
_AMAROLAB_ER_CANDIDATE_CAP = 8

_AMAROLAB_ER_SEPARATORS = _amarolab_er_re.compile(r"[\s._-]+")

# Registry integrity guard. Deliberately SEPARATE from the calling Tool's own
# `_ENTITY_ID_RE`, which is the locked Phase C *input* grammar and stays owned by
# the Tool. This one guards the registry's *output*: a resolved id is
# interpolated straight into an HA API URL path, so a corrupted projection could
# otherwise smuggle traversal into it. The pattern is the same one spec §4 step 4
# freezes, and the two must stay identical.
#
# Unreachable against a projection this platform emits — the loader's check 12
# validates every id long before it reaches the artifact. Kept as defence in
# depth, following the ER-1.3 precedent for `resolution.build()`'s guard: a
# runtime file is worth verifying even when its producer is trusted.
_AMAROLAB_ER_ID_RE = _amarolab_er_re.compile(r"^[a-z_]+\.[a-z0-9_]+$")


def _amarolab_er_normalize(s):
    """The frozen D-ER-8 normalization. `"Conexión a Internet"` -> `"conexion a internet"`.

    casefold -> NFKD -> strip combining marks -> collapse [\\s._-]+ to a single
    space -> trim. `ñ -> n` is accepted (negligible collision risk on device
    names).

    This MUST stay byte-for-byte equivalent to `_loader/resolution.py`'s
    `normalize_alias()`: that function produced the registry keys this one looks
    up. The two are pinned together by `_AMAROLAB_ER_NORMALIZATION`, asserted
    against the projection's stamp on every load.

    Note this collapses `.` to a space, so a normalized string can never be
    id-shaped — which is why the caller tests id-shape on the RAW input, before
    normalizing (D-ER-8 / check 12c).
    """
    if not isinstance(s, str):
        return ""
    s = s.casefold()
    s = _amarolab_er_unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not _amarolab_er_unicodedata.combining(c))
    s = _AMAROLAB_ER_SEPARATORS.sub(" ", s)
    return s.strip()


class _EntityResolver:
    """Closed, deterministic lookup over the ER-1.3 projection.

    No fuzzy matching, no scoring, no LLM in the loop (spec §4).

    **A broken projection must never break a direct `entity_id`.** Every method
    degrades to "unavailable" rather than raising, so the caller can honour
    D-ER-9: a syntactically valid id continues to Home Assistant exactly as
    today whether or not this resolver works. Only the alias path depends on it,
    and that path reports `resolver_unavailable` honestly (G-ER-6 consumer half).
    """

    _projection = None      # parsed + validated projection, or None
    _stat_key = None        # (st_mtime_ns, st_size) the cache was built from
    _reason = "not loaded"  # why unavailable, for the audit trail

    @classmethod
    def _load(cls):
        """Parse + validate the projection, caching on (mtime_ns, size).

        The openwebui process is long-lived, so a cached copy would outlive a
        regeneration; re-reading when the stat key moves keeps a manual
        `emit-entity-projection` run visible without a container restart. Never
        raises.
        """
        path = _AMAROLAB_ER_PROJECTION
        try:
            st = path.stat()
            key = (st.st_mtime_ns, st.st_size)
        except OSError as e:
            cls._projection = None
            cls._stat_key = None
            cls._reason = f"projection unreadable: {e.__class__.__name__}"
            return cls._projection

        if cls._projection is not None and cls._stat_key == key:
            return cls._projection

        cls._stat_key = key
        try:
            data = _amarolab_er_json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001 — any parse fault means unavailable
            cls._projection = None
            cls._reason = f"projection is not readable JSON: {e.__class__.__name__}"
            return None

        if not isinstance(data, dict):
            cls._projection = None
            cls._reason = "projection is not a JSON object"
            return None
        if data.get("projection_version") != _AMAROLAB_ER_PROJECTION_VERSION:
            cls._projection = None
            cls._reason = (f"projection_version {data.get('projection_version')!r} != "
                           f"{_AMAROLAB_ER_PROJECTION_VERSION}")
            return None
        if data.get("normalization") != _AMAROLAB_ER_NORMALIZATION:
            cls._projection = None
            cls._reason = "projection normalization spec does not match D-ER-8"
            return None
        if not isinstance(data.get("aliases"), dict) or not data["aliases"]:
            cls._projection = None
            cls._reason = "projection carries no aliases"
            return None
        if not isinstance(data.get("targets"), dict) or not data["targets"]:
            cls._projection = None
            cls._reason = "projection carries no targets"
            return None
        for _alias, _target in data["aliases"].items():
            if not isinstance(_target, str) or not _AMAROLAB_ER_ID_RE.match(_target):
                cls._projection = None
                cls._reason = "projection maps an alias to a non-id-shaped target"
                return None

        cls._projection = data
        cls._reason = "ok"
        return data

    @classmethod
    def available(cls):
        return cls._load() is not None

    @classmethod
    def reason(cls):
        """Why the resolver is unavailable. Never a secret — AD-18."""
        cls._load()
        return cls._reason

    @classmethod
    def lookup(cls, raw):
        """Closed alias lookup on a non-id-shaped string. `None` = miss/unavailable.

        The caller distinguishes miss from unavailable via `available()`: they
        are different answers (`unknown_entity` vs `resolver_unavailable`) and
        call for different operator actions.
        """
        p = cls._load()
        if p is None:
            return None
        return p["aliases"].get(_amarolab_er_normalize(raw))

    @classmethod
    def is_target(cls, entity_id):
        """Is `entity_id` a resolution target? `None` when the resolver is unavailable.

        **Observability only** — never a gate (D-ER-9). The caller passes the id
        to Home Assistant either way.

        `None` rather than `False` when unavailable is deliberate: "the registry
        does not list this id" and "the registry could not be read" are
        different facts, and reporting the second as the first would put a claim
        in the audit log that was never verified.

        Scope, stated precisely because the audit field is named `modelled`: this
        answers *"is this id a target in the resolution registry?"*, NOT *"does
        the World Model model this entity?"* The registry holds only the
        **aliased** signals of bound entities, so an entity the World Model binds
        but carries no aliases for is a target=False. `sun.sun` is exactly that
        case — `environment/daylight-time.md` binds it, and it is deliberately
        unaliased. Recorded as finding F-ER14-1.
        """
        p = cls._load()
        if p is None:
            return None
        return entity_id in p["targets"]

    @classmethod
    def candidates(cls, limit=_AMAROLAB_ER_CANDIDATE_CAP):
        """Bounded, deterministic candidate list — names + ids only (AD-18-safe).

        Returned on a resolver miss so the model gets corrective feedback instead
        of inventing another id (root cause #3). Sorted by entity_id and capped:
        the list is a bounded hint, never the registry.
        """
        p = cls._load()
        if p is None:
            return []
        out = []
        for entity_id in sorted(p["targets"]):
            t = p["targets"][entity_id] or {}
            out.append({"name": t.get("name"), "entity_id": entity_id})
        return out[:limit]
# --- INLINE END ---
