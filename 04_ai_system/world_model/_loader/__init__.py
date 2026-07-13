"""
World Model loader/compiler (WM-3).

Deterministic, idempotent pipeline over the canonical world_model/ docs:

    Parse → Resolve → Normalize → Validate → Emit

Emits the derived, gitignored, fully-regenerable `world_model.generated.json`.
Read-only w.r.t. canonical docs; does not evaluate live state or interpret
meaning — Awareness evaluation is `_evaluator/` (WM-4; loader compiles,
evaluator evaluates). Fail-loud: retains last-good on failure.

Conforms to the frozen architecture (AD-21, world_model_architecture.md) and the
operative schema contract (_schema/entity.schema.md). See INV-WM3-A in ast.py.
"""

LOADER_VERSION = "0.1.0"
ARTIFACT_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = (1,)
