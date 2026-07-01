"""
parity/ — WM-3 gate instrument (NON-authoritative).

Proves `loader rules ≡ HOME_RULES` by a differential oracle: evaluate the
compiled AST (from world_model.generated.json) and detect_home() over the SAME
/api/states snapshot and assert identical tokens, order, and rendering.

This is NOT a shipped consumer and NOT the evaluation engine (that is WM-4). It
imports detect_home() READ-ONLY and never modifies aurora-context.
"""
