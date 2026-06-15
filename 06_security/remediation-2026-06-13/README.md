# Phase 2 — Remediation plan

- **Date:** 2026-06-13
- **Scope:** Acts on the 20 findings from [`../14-security-risks.md`](../14-security-risks.md)
- **Mode:** Plan only. **No changes were applied.** Every section below is
  diffs, file contents, and shell commands you can review then run.

## How priorities are assigned

Two axes, both scored as **L / M / H** in homelab context (single admin,
behind a non-forwarding router, LAN + 6-device tailnet):

- **Risk** — how likely the issue is to be exploited *now*, given the
  current network boundary.
- **Impact** — blast radius if it does fire (data loss, host root, downtime).

Time-to-fix is a wall-clock estimate for the documented procedure on this
host, assuming no surprises.

| Priority | Definition |
|----------|-----------|
| 🔴 Critical | Either Risk ≥ H **or** Impact = H with cheap fix. Address today. |
| 🟠 High | Real exploit path or already-broken capability. Address this week. |
| 🟡 Medium | Defense-in-depth and operability. Address this month. |
| 🟢 Low | Cleanup, hygiene, low-stakes investigation. Whenever convenient. |

## Master table

| ID | Finding | Risk | Impact | Time | Priority | File |
|----|---------|:----:|:------:|:----:|:--------:|------|
| R-01 | Cloudflare tunnel token in plaintext compose | M | H | 30 m + Cloudflare UI | 🔴 Critical | [01-critical.md](01-critical.md) |
| R-02 | Flask `homelab-tools` API on `0.0.0.0:5050`, no auth | H | H | 5 m | 🔴 Critical | [01-critical.md](01-critical.md) |
| R-03 | NPM `keys.json` / `database.sqlite` mode `0644` | M | H | 2 m | 🔴 Critical | [01-critical.md](01-critical.md) |
| R-04 | Mosquitto crash-looping (missing config) | H (already broken) | M | 15 m | ✅ Applied 2026-06-13 | [01-critical.md](01-critical.md) |
| R-06 | Open WebUI mounts `/var/run/docker.sock` rw | M | H (host root) | 45 m | ✅ Applied 2026-06-13 | [02-high.md](02-high.md) |
| R-07 | Ollama + Qdrant unauthenticated on LAN/tailnet | M | M | 20 m | ✅ Qdrant key applied 2026-06-13 · ⏭ port rebind + Ollama deferred to R-14 | [02-high.md](02-high.md) |
| R-12 | No backups | M (already crashed once) | H | 2 h | ✅ Applied 2026-06-13 (snapshot `cc73b4fd`) | [02-high.md](02-high.md) |
| R-05 | Open WebUI `WEBUI_SECRET_KEY` empty | L | M | 15 m | ✅ Applied 2026-06-13 | [03-medium.md](03-medium.md) |
| R-08 | WebDAV Basic auth over plain HTTP (port 8088) | L | M | 5 m (disable) / 1 h (TLS) | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-09 | `rpcbind` exposed on `0.0.0.0:111` (no NFS) | L | L | 2 m | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-10 | No host firewall (UFW inactive) | L | M | 30 m | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-11 | Container images 3 months stale | M | M | 30 m + per-stack verify | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-13 | Apache `000-default` vs NPM port 80 contention | L | L | 2 m | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-14 | 8 containers have no checked-in compose file | L (ops) | M (recovery) | 2–4 h | 🟡 Medium | [03-medium.md](03-medium.md) |
| R-15 | Orphan Chroma store in Open WebUI data dir | — | — | 1 m | 🟢 Low | [04-low.md](04-low.md) |
| R-16 | Two unused Docker bridges (`html_default`, `cloudflared_default`) | — | — | 1 m | 🟢 Low | [04-low.md](04-low.md) |
| R-17 | `diego` in `docker` group | L | (policy) | n/a | 🟢 Low (informational) | [04-low.md](04-low.md) |
| R-18 | Desktop services (GDM/CUPS/Bluetooth/ModemManager) on a server | L | L | 15 m | 🟢 Low | [04-low.md](04-low.md) |
| R-19 | Qdrant `/metrics` + `/telemetry` reachable unauth | L | L | covered by R-07 | 🟢 Low | [04-low.md](04-low.md) |
| R-20 | 2026-06-03 12:55 hard reset — cause not captured | (investigative) | — | 30 m | 🟢 Low | [04-low.md](04-low.md) |

## Recommended sequencing

The dependencies aren't tight, but a sensible order minimizes wasted work:

1. **R-03** (chmod), **R-02** (rebind to localhost), **R-04** (mosquitto
   config) — 5–15 minutes each, no side effects.
2. **R-01** (tunnel token rotation) — needs ~15 min in the Cloudflare UI.
3. **R-14** (compose files) is a soft prerequisite for R-05, R-06, R-07,
   R-11. You can do them via `docker run` instead, but compose is the path
   that doesn't bit-rot.
4. **R-07** (rebind Ollama/Qdrant) + **R-05** (set secret key) +
   **R-06** (socket exposure) — done together if compose is in place.
5. **R-12** (backups) — independent; the HDD target already exists.
6. **R-09**, **R-13**, **R-08**, **R-10** in any order. Run UFW last so
   you've verified what each service actually needs first.
7. **R-11** (image updates) once everything else is stable — this is the
   point where a regression is most likely; restore from R-12 backups if
   needed.
8. Low-priority items at leisure.

## Convention used in the fix files

Each finding follows this structure:

> #### R-NN — Title
> **Risk · Impact · Time · Priority**
>
> **Current state** — one-paragraph recap.
>
> **Target state** — what "fixed" looks like.
>
> **Procedure** — numbered commands and diffs, copy-pasteable.
>
> **Validation** — commands that prove the fix landed.
>
> **Rollback** — how to undo if something breaks.

Diffs are unified format (`diff -u`-style). Commands assume you are
logged in as `diego` (use `sudo` where shown).
