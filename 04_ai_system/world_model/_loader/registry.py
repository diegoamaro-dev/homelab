"""
registry.py — load the canonical single-source registries.

    _schema/tokens.md      → anomaly-token registry (emission order = severity order)
    _schema/windows.md     → named tz-anchored time windows
    _schema/collectors.md  → valid collector ids (active + reserved)

These Markdown tables are the SINGLE SOURCE OF TRUTH (schema §3/§7). The loader
reads them; it never authors severity or bounds elsewhere. Rendered phrases are
taken verbatim (byte-identical, incl. the em-dash) so awareness parity holds.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


class RegistryError(ValueError):
    pass


# ── Markdown table helpers ───────────────────────────────────────────────────
def _clean(cell: str, strip_ticks: bool = True) -> str:
    s = cell.strip()
    if s.startswith("**") and s.endswith("**") and len(s) >= 4:
        s = s[2:-2].strip()
    if strip_ticks and s.startswith("`") and s.endswith("`") and len(s) >= 2:
        s = s[1:-1]
    return s


def _tables(text: str) -> list[list[list[str]]]:
    """Return every Markdown table as a list of data rows (each a list of cells)."""
    tables: list[list[list[str]]] = []
    run: list[str] = []

    def flush() -> None:
        if len(run) >= 2:
            rows = []
            for i, line in enumerate(run):
                cells = [c for c in line.strip().strip("|").split("|")]
                if i == 1 and all(set(c.strip()) <= set("-: ") for c in cells):
                    continue  # separator row
                rows.append([c.strip() for c in cells])
            tables.append(rows[1:])  # drop header row
        run.clear()

    for line in text.splitlines():
        if line.lstrip().startswith("|"):
            run.append(line)
        else:
            flush()
    flush()
    return tables


# ── Data ─────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Token:
    token: str
    tier: str | None
    severity_rank: int | None
    render_phrase: str | None
    status: str            # "active" | "reserved"
    special: bool = False


@dataclass(frozen=True)
class Window:
    name: str
    tz: str
    start_min: int
    end_min: int
    half_open: bool = True


@dataclass(frozen=True)
class Collector:
    collector_id: str
    status: str            # "active" | "reserved"
    exposes_last_changed: bool


@dataclass(frozen=True)
class Registries:
    tokens: dict[str, Token]
    emission_order: list[str]           # active tokens, registry order
    windows: dict[str, Window]
    collectors: dict[str, Collector]

    def active_tokens(self) -> list[str]:
        return list(self.emission_order)


_HHMM = re.compile(r"(\d{1,2}):(\d{2})")


def _load_tokens(path: Path) -> tuple[dict[str, Token], list[str]]:
    text = path.read_text(encoding="utf-8")
    tables = _tables(text)
    if not tables:
        raise RegistryError(f"no table found in {path}")
    tokens: dict[str, Token] = {}
    order: list[str] = []
    for row in tables[0]:                 # first table = the registry
        if len(row) < 3:
            continue
        tok = _clean(row[0])
        if not tok or " " in tok:
            continue
        tier = _clean(row[1]) or None
        phrase = _clean(row[2]) or None
        rank = len(order) + 1
        tokens[tok] = Token(tok, tier, rank, phrase, "active")
        order.append(tok)

    # Reserved / special tokens declared in prose (not the table).
    if "ha_unavailable" in text and "ha_unavailable" not in tokens:
        tokens["ha_unavailable"] = Token(
            "ha_unavailable", None, None,
            "Home Assistant unreachable at last context generation.",
            "reserved", special=True,
        )
    if "firmware_*" in text and "firmware_*" not in tokens:
        tokens["firmware_*"] = Token("firmware_*", None, None, None, "reserved")
    return tokens, order


def _load_windows(path: Path) -> dict[str, Window]:
    tables = _tables(path.read_text(encoding="utf-8"))
    if not tables:
        raise RegistryError(f"no table found in {path}")
    windows: dict[str, Window] = {}
    for row in tables[0]:
        if len(row) < 3:
            continue
        name = _clean(row[0])
        if not name:
            continue
        bounds = _HHMM.findall(row[1])
        if len(bounds) < 2:
            raise RegistryError(f"window {name!r} bounds unparseable: {row[1]!r}")
        (h0, m0), (h1, m1) = bounds[0], bounds[1]
        tz = _clean(row[2])
        windows[name] = Window(name, tz, int(h0) * 60 + int(m0), int(h1) * 60 + int(m1))
    return windows


def _load_collectors(path: Path) -> dict[str, Collector]:
    text = path.read_text(encoding="utf-8")
    tables = _tables(text)
    collectors: dict[str, Collector] = {}
    # First table = the active registry; later tables = anticipated/reserved.
    for ti, table in enumerate(tables):
        for row in table:
            if len(row) < 2:
                continue
            cid = _clean(row[0])
            if not cid or " " in cid:
                continue
            if ti == 0:
                exposes_lc = "last_changed" in " ".join(row)
                status = _clean(row[-1]).lower() or "active"
                collectors[cid] = Collector(cid, "active" if "active" in status else status, exposes_lc)
            else:
                collectors.setdefault(cid, Collector(cid, "reserved", False))
    return collectors


def load(schema_dir: Path) -> Registries:
    tokens, order = _load_tokens(schema_dir / "tokens.md")
    windows = _load_windows(schema_dir / "windows.md")
    collectors = _load_collectors(schema_dir / "collectors.md")
    if not order:
        raise RegistryError("token registry is empty")
    if not windows:
        raise RegistryError("window registry is empty")
    if not any(c.status == "active" for c in collectors.values()):
        raise RegistryError("no active collector in registry")
    return Registries(tokens, order, windows, collectors)
