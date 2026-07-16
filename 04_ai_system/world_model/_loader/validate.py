"""
validate.py — Stage ④ Validate (fail-loud).

Runs the frozen §4.7 / schema §5 ruleset (checks 1–11b) against the normalized
model. Accumulates ALL violations, then raises a single ValidationError. The
loader emits NOTHING on failure (caller retains last-good).
"""

from __future__ import annotations

import re
from pathlib import Path

from . import ast, authorization, resolution
from .model import (BOUNDARIES, KINDS, PRIORITIES, REGIONS, STATUSES,
                    ParsedEntity, is_kebab, is_snake)
from .registry import Registries

SUPPORTED_SCHEMA_VERSIONS = (1,)

# ER-1 check 12c — an alias must not be a literal HA entity_id. Mirrors the tool
# boundary's grammar; id-shaped input never reaches the alias path (D-ER-2), so
# such an alias would be dead and misleading.
_ID_SHAPED = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")
_ALIAS_MIN_LEN = 2
_ALIAS_MAX_LEN = 64


class ValidationError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__(f"{len(problems)} validation error(s):\n  - " + "\n  - ".join(problems))


# ── AD-18 secret patterns (conservative: no false positive on ids/semver) ─────
_AD18 = [
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "IPv4 address"),
    (re.compile(r"\b(?:[0-9A-Fa-f]{1,4}:){4,}[0-9A-Fa-f]{1,4}\b"), "IPv6 address"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{8,}"), "JWT/bearer token"),
    (re.compile(r"\b[A-Fa-f0-9]{32,}\b"), "long hex secret"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{12,}"), "bearer credential"),
    (re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret_key)\b\s*[:=]\s*\S+"), "credential assignment"),
]


class _V:
    def __init__(self, entities: list[ParsedEntity], archetypes: dict, reg: Registries):
        self.entities = entities
        self.archetypes = archetypes
        self.reg = reg
        self.by_id = {e.id: e for e in entities}
        self.problems: list[str] = []

    def err(self, msg: str) -> None:
        self.problems.append(msg)

    # 1 ── Structural ────────────────────────────────────────────────────────
    def structural(self) -> None:
        for e in self.entities:
            fm = e.fm
            for req in ("id", "name", "region", "kind", "status", "schema_version"):
                if req not in fm or fm.get(req) in (None, ""):
                    self.err(f"{e.file.name}: missing required field {req!r}")
            if fm.get("region") not in REGIONS:
                self.err(f"{e.id}: invalid region {fm.get('region')!r}")
            if fm.get("kind") not in KINDS:
                self.err(f"{e.id}: invalid kind {fm.get('kind')!r}")
            if fm.get("status") not in STATUSES:
                self.err(f"{e.id}: invalid status {fm.get('status')!r}")
            if "priority" in fm and fm["priority"] not in PRIORITIES:
                self.err(f"{e.id}: invalid priority {fm['priority']!r}")
            if "boundary" in fm and fm["boundary"] not in BOUNDARIES:
                self.err(f"{e.id}: invalid boundary {fm['boundary']!r}")
            if not isinstance(fm.get("schema_version"), int):
                self.err(f"{e.id}: schema_version must be an integer")
            if not e.id or not is_kebab(e.id):
                self.err(f"{e.id!r}: id must be kebab-case")
            if e.file.stem != e.id:
                self.err(f"{e.file.name}: filename must equal id ({e.id!r})")
            if e.region != fm.get("region"):
                self.err(f"{e.id}: directory region {e.region!r} != frontmatter region {fm.get('region')!r}")
            # field-name naming (binding signal names + rule fields)
            for sig in e.binding_signals:
                if not is_snake(sig):
                    self.err(f"{e.id}: binding signal name {sig!r} must be snake_case")
            for r in e.rules:
                if not is_snake(r.token):
                    self.err(f"{e.id}: token {r.token!r} must be snake_case")
                for f in ast.fields_read(r.ast_node):
                    if not is_snake(f):
                        self.err(f"{e.id}: field {f!r} must be snake_case")
            # conditional requirements
            if e.evaluable and e.kind != "aspect":
                if e.baseline is None:
                    self.err(f"{e.id}: evaluable entity missing baseline")
                if e.binding_shape is None:
                    self.err(f"{e.id}: evaluable entity missing binding")
            if e.evaluable and not e.collector:
                self.err(f"{e.id}: evaluable entity missing collector")
            if e.evaluable and "priority" not in fm:
                self.err(f"{e.id}: deviable entity missing priority")

    # 2 ── Grammar (windows tz-anchored) ─────────────────────────────────────
    def grammar(self) -> None:
        for e in self.entities:
            for r in e.rules:
                for w in ast.windows_used(r.ast_node):
                    win = self.reg.windows.get(w)
                    if win is None:
                        self.err(f"{e.id}: rule {r.token!r} references unknown window {w!r}")
                    elif not win.tz:
                        self.err(f"{e.id}: window {w!r} is not tz-anchored")

    # 3 ── Token ──────────────────────────────────────────────────────────────
    def token(self) -> None:
        for e in self.entities:
            for r in e.rules:
                tk = self.reg.tokens.get(r.token)
                if tk is None:
                    self.err(f"{e.id}: token {r.token!r} not in tokens.md registry")
                elif tk.status != "active":
                    self.err(f"{e.id}: token {r.token!r} is {tk.status}, not usable in a rule")

    # 4 ── Referential (+ cycles) ─────────────────────────────────────────────
    def referential(self) -> None:
        seen: dict[str, int] = {}
        for e in self.entities:
            seen[e.id] = seen.get(e.id, 0) + 1
        for i, n in seen.items():
            if n > 1:
                self.err(f"duplicate entity id {i!r} ({n} files)")
        for e in self.entities:
            for dep in e.depends_on:
                if dep not in self.by_id:
                    self.err(f"{e.id}: depends_on unknown entity {dep!r}")
            if (po := e.fm.get("part_of")):
                tgt = self.by_id.get(po)
                if tgt is None:
                    self.err(f"{e.id}: part_of unknown entity {po!r}")
                elif tgt.kind != "aggregate":
                    self.err(f"{e.id}: part_of {po!r} is not an aggregate")
            if (arch := e.fm.get("archetype")) and arch not in self.archetypes:
                self.err(f"{e.id}: unknown archetype {arch!r}")
            ap = e.fm.get("applies_to")
            if isinstance(ap, list):
                for m in ap:
                    ent = m.get("entity")
                    if ent and ent not in self.by_id:
                        self.err(f"{e.id}: applies_to references unknown entity {ent!r}")
        # archetype-of-archetype rejected
        for a in self.archetypes.values():
            if "archetype" in a.defaults:
                self.err(f"archetype {a.archetype_id!r}: deep inheritance (archetype-of-archetype) rejected")
        self._cycles()

    def _cycles(self) -> None:
        graph = {e.id: list(e.depends_on) for e in self.entities}
        WHITE, GREY, BLACK = 0, 1, 2
        color = {k: WHITE for k in graph}

        def visit(u: str, stack: list[str]) -> None:
            color[u] = GREY
            for v in graph.get(u, []):
                if v not in color:
                    continue
                if color[v] == GREY:
                    self.err(f"dependency cycle: {' -> '.join(stack + [v])}")
                elif color[v] == WHITE:
                    visit(v, stack + [v])
            color[u] = BLACK

        for node in graph:
            if color[node] == WHITE:
                visit(node, [node])

    # 5 ── Safety (AD-18) ─────────────────────────────────────────────────────
    def safety(self) -> None:
        for e in self.entities:
            text = e.file.read_text(encoding="utf-8")
            for rx, label in _AD18:
                m = rx.search(text)
                if m:
                    self.err(f"{e.id}: AD-18 — possible {label} in doc ({m.group()[:12]}…)")

    # 6 ── Boundary ───────────────────────────────────────────────────────────
    def boundary(self) -> None:
        for e in self.entities:
            if e.fm.get("boundary") == "read_only":
                if e.writable:
                    self.err(f"{e.id}: read_only entity must not be writable")
                if e.rules:
                    self.err(f"{e.id}: read_only entity must not carry anomaly_rules")
            if e.region == "operator":
                for sig in e.binding_signals:
                    if sig in ("occupancy", "presence", "person"):
                        self.err(f"{e.id}: operator entity must not carry presence/occupancy signal {sig!r}")

    # 7 ── Coverage ───────────────────────────────────────────────────────────
    def coverage(self) -> None:
        produced = {r.token for e in self.entities for r in e.rules}
        for tok in self.reg.emission_order:               # active tokens only
            if tok not in produced:
                self.err(f"coverage: active token {tok!r} is produced by no rule")
        for e in self.entities:
            c = e.collector
            if c is not None:
                col = self.reg.collectors.get(c)
                if col is None:
                    self.err(f"{e.id}: collector {c!r} not in collectors.md")
                elif col.status != "active":
                    self.err(f"{e.id}: collector {c!r} is {col.status}, not active")

    # 8 ── Prose ──────────────────────────────────────────────────────────────
    def prose(self) -> None:
        for e in self.entities:
            for req in ("Purpose", "Reasoning"):
                if req not in e.prose_headings:
                    self.err(f"{e.id}: missing required prose section '## {req}'")

    # 9 ── Lifecycle ──────────────────────────────────────────────────────────
    def lifecycle(self) -> None:
        for e in self.entities:
            if e.status == "active":
                for dep in e.depends_on:
                    tgt = self.by_id.get(dep)
                    if tgt is not None and tgt.status == "retired":
                        self.err(f"{e.id}: active entity depends on retired {dep!r}")

    # 10 ── Version ───────────────────────────────────────────────────────────
    def version(self) -> None:
        for e in self.entities:
            sv = e.fm.get("schema_version")
            if isinstance(sv, int) and sv not in SUPPORTED_SCHEMA_VERSIONS:
                self.err(f"{e.id}: schema_version {sv} unsupported (loader reads {SUPPORTED_SCHEMA_VERSIONS})")

    # 11a ── Authorization (INV-17) ───────────────────────────────────────────
    def authz(self) -> None:
        for e in self.entities:
            self.problems.extend(authorization.check(e))

    # 11b ── Duration / collector ─────────────────────────────────────────────
    def duration_collector(self) -> None:
        for e in self.entities:
            needs = any(ast.uses_last_changed(r.ast_node) for r in e.rules
                        if r.kind != "fold") or any(
                r.fold and any(ast.uses_last_changed(v) for v in r.fold["per_signal"].values())
                for r in e.rules if r.kind == "fold")
            if needs:
                col = self.reg.collectors.get(e.collector or "")
                if col is None or not col.exposes_last_changed:
                    self.err(f"{e.id}: duration rule requires a collector exposing last_changed")

    # 12 ── Aliases (ER-1; schema §5.1 12a–12f) ───────────────────────────────
    def aliases(self) -> None:
        """Fail-loud alias validation. Naming only — an alias never grants or
        denies anything (INV-17 / D-ER-9); D-12 remains the sole authority."""
        # 12f — archetype-level aliases. Defaults are merged into every member, so
        # an archetype alias would fan out and collide by construction. Aliases are
        # per-entity identity, never inherited. (Resolve already keeps defaults out
        # of `fm`, so this is defence in depth against a future refactor.)
        for a in self.archetypes.values():
            if "aliases" in a.defaults:
                self.err(f"archetype {a.archetype_id!r}: archetype-level aliases are "
                         f"rejected (12f) — aliases are per-entity identity")

        seen: dict[str, tuple[str, str]] = {}          # normalized -> (entity, signal)
        for e in self.entities:
            raw = e.fm.get("aliases")
            if raw is None:
                continue

            # 12a — shape mirrors `binding` (D-ER-11).
            if e.binding_shape is None:
                self.err(f"{e.id}: declares aliases but has no binding (12a)")
                continue
            if e.binding_shape == "single" and not isinstance(raw, list):
                self.err(f"{e.id}: single-signal binding requires a flat alias list (12a)")
                continue
            if e.binding_shape == "multi" and not isinstance(raw, dict):
                self.err(f"{e.id}: multi-signal binding requires a per-signal alias map "
                         f"— there is no implicit `state` (12a, D-ER-11)")
                continue

            for signal, names in resolution.authored_map(e).items():
                if signal not in e.binding_signals:
                    self.err(f"{e.id}: alias signal {signal!r} is not a declared "
                             f"binding signal (12a)")
                    continue
                # 12b — type/bounds.
                if not isinstance(names, list) or not names:
                    self.err(f"{e.id}/{signal}: aliases must be a non-empty list (12b)")
                    continue
                for n in names:
                    if not isinstance(n, str) or not n.strip():
                        self.err(f"{e.id}/{signal}: alias {n!r} must be a non-empty "
                                 f"string (12b)")
                        continue
                    norm = resolution.normalize_alias(n)
                    if not (_ALIAS_MIN_LEN <= len(norm) <= _ALIAS_MAX_LEN):
                        self.err(f"{e.id}/{signal}: alias {n!r} normalizes to "
                                 f"{len(norm)} chars (bounds {_ALIAS_MIN_LEN}-"
                                 f"{_ALIAS_MAX_LEN}) (12b)")
                    # 12c — not id-shaped. Checked on the RAW authored string:
                    # D-ER-8 collapses `.` to a space, so a normalized alias can
                    # never be id-shaped and testing it would be vacuous.
                    if _ID_SHAPED.match(n.strip().casefold()):
                        self.err(f"{e.id}/{signal}: alias {n!r} is id-shaped — a "
                                 f"literal entity_id is a dead alias (12c, D-ER-2)")
                    # 12d — global normalized uniqueness (the lookup table is flat).
                    if norm in seen:
                        o = seen[norm]
                        self.err(f"alias collision {norm!r}: {o[0]}/{o[1]} and "
                                 f"{e.id}/{signal} (12d)")
                    else:
                        seen[norm] = (e.id, signal)

        # 12e — an alias MAY equal its OWN entity's identifier (harmless
        # redundancy: both denote the same thing), but MUST NOT equal a DIFFERENT
        # entity's identifier (D-ER-12).
        for e in self.entities:
            norm_id = resolution.normalize_alias(e.id)
            owner = seen.get(norm_id)
            if owner and owner[0] != e.id:
                self.err(f"{owner[0]}/{owner[1]}: alias {norm_id!r} is a different "
                         f"entity's identifier ({e.id!r}) (12e, D-ER-12)")

    def run(self) -> None:
        for check in (self.structural, self.grammar, self.token, self.referential,
                      self.safety, self.boundary, self.coverage, self.prose,
                      self.lifecycle, self.version, self.authz, self.duration_collector,
                      self.aliases):
            check()
        if self.problems:
            raise ValidationError(self.problems)


def validate(entities: list[ParsedEntity], archetypes: dict, reg: Registries) -> None:
    _V(entities, archetypes, reg).run()
