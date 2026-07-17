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

# 0.2.1 (ER-1.3) — patch: D-ER-13 tightens check 12a (an aliased signal must bind
# `ha_entity`). Validation contract only — no output change and no consumer impact:
# the rule is unreachable on the current tree, so the emitted artifact is
# byte-identical. ER-1.3 deliberately does NOT regenerate the artifact, so the live
# `generator.loader_version` stays 0.2.0 until the next run — which is correct: 0.2.0
# is the version that actually produced it. A version stamp is provenance, never a
# freshness signal (PROJECT_RULES.md -> "Content Provenance over Repository
# Chronology"); freshness is decided by content hash.
# 0.2.0 (ER-1.2) — minor: additive. New validation contract (check 12, fail-loud)
# + the additive `resolution` registry. No breaking change to any consumer.
LOADER_VERSION = "0.2.1"
# STAYS 1 (D-ER-7). `resolution` is additive. The evaluator pins
# SUPPORTED_ARTIFACT_VERSIONS = (1,) and bin/aurora-context CATCHES an artifact
# error and fails soft to "Home State: Unavailable" — so a bump would not fail
# loud, it would silently degrade awareness nightly and undo the WM-6 closure.
ARTIFACT_VERSION = 1
SUPPORTED_SCHEMA_VERSIONS = (1,)
