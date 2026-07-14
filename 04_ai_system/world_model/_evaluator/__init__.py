"""
World Model evaluation engine (WM-4).

Stage ④ of the cognitive pipeline (world_model_architecture.md §1.3): the
World Model **evaluated at now**. This package consumes the compiled artifact
`world_model.generated.json` (emitted by `_loader/`) plus a signals snapshot
and produces the ordered anomaly evaluation — Awareness.

Architectural separation (WM-4, operator-ratified):
    `_loader/`    compiles  (docs → artifact; Parse→Resolve→Normalize→Validate→Emit)
    `_evaluator/` evaluates (artifact + signals @ now → Awareness)

Deterministic (B3): evaluation is a pure function of (artifact, states,
now_utc) — no live reads, no probabilistic step, no writes. The engine never
invokes the loader; consumers read the emitted artifact (retain-last-good).
Backend-agnostic AST semantics per INV-WM3-A: `eval_node` knows only the AST;
all Home-Assistant specifics live in the `HAContext` adapter.
"""

from .engine import (  # noqa: F401
    DEFAULT_ARTIFACT,
    EVALUATOR_VERSION,
    SUPPORTED_ARTIFACT_VERSIONS,
    Anomaly,
    ArtifactError,
    Awareness,
    HAContext,
    aggregate_verdict,
    eval_node,
    evaluate_model,
    evaluate_world,
    load_artifact,
    to_overall_status,
    worst_verdict,
)
