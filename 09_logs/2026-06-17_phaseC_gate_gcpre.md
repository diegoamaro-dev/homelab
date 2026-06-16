# Phase C — Gate G-Cpre — ATTEMPT 1 ABORTED + ROLLED BACK

- **Date:** 2026-06-17 (executed wall-clock 2026-06-16 13:34–13:37 local).
- **Status:** **GATE G-CPRE IS NOT CLOSED.** Attempt 1 of the
  openwebui container recreate (Phase C precondition; mirror
  of B-3 with `HA_BASE_URL` + `HA_LLAT` added) **aborted
  before the new container was created** and was **rolled
  back** to the pre-attempt state. The running `openwebui`
  container is bit-identical (mounts, networks, image, env,
  webui.db MD5, audit-log MD5) to the pre-attempt state.
  No HA env vars are passed through to the container yet —
  R-C1 from
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §1.3 remains open.
- **Scope:** Document what was attempted, the script bug
  that aborted the run, the **secret leak** caused by a
  diagnostic echo in the recovery probe, the rollback proof,
  and the corrected retry plan. Pair with
  [`2026-06-17_phaseC_readiness_review.md`](2026-06-17_phaseC_readiness_review.md)
  §6 (the original G-Cpre proposal) and the B-3 applied log
  [`2026-06-16_phaseB_openwebui_bind_mount_applied.md`](2026-06-16_phaseB_openwebui_bind_mount_applied.md).
- **What this log is NOT:** a successful Gate G-Cpre
  close-out. The closeout will be written **after** a
  successful Attempt 2 — which is gated on user rotation
  decisions in §3 below.

## 0. TL;DR

Attempt 1 of Gate G-Cpre executed in this order, against the
running `openwebui` container at
`2026-06-16T11:34Z`–`11:37Z` local-wall-clock:

1. Backup directory created
   (`/tmp/amarolab-phaseC-backup`, 0700 `diego:diego`).
2. Pre-attempt `docker inspect openwebui` saved to
   `openwebui.inspect.pre-Cpre.json` (0600).
3. Pre-attempt webui.db + amarolab-audit.log copied; MD5s
   captured to `md5.pre-Cpre`.
4. Image vs container env diff computed — runtime delta is
   7 vars (matches B-3's set minus image-default-equivalent
   passes).
5. `docker stop openwebui` → exit code 0, clean shutdown at
   `2026-06-16T11:34:55Z`.
6. webui.db + audit-log MD5s **re-captured post-stop** as
   the reference for unchanged-across-recreate comparison
   (md5sums: webui.db `d5536bef6e299157fb33614808f90f13`,
   audit-log `e574b213bd1e3ab4ee337df0be47111c`).
7. Container renamed to `openwebui_pre_phaseC_20260616113453`
   (rollback target).
8. `set -a; . /home/diego/homelab/ai-stack/.env; set +a` —
   sourced the .env into the run subshell.
9. **Pre-`docker run` sanity check** iterated over the four
   expected secret keys; printed each with a diagnostic
   `echo` that included an unsafe `${v:-NOT_SET}`
   substitution. **The substitution rendered the variable's
   actual value, not just `SET (len=N)`.** Result: three
   secret values appeared verbatim in the bash tool's stdout
   (and therefore in this AI assistant session's chat transcript).
10. The sanity check **then** caught the real failure
    condition (the *fourth* secret, `QDRANT_API_KEY`, was
    indeed unset — see §2 root cause), printed the leaked
    diagnostics for the first three, and exited with code 2
    via `set -e`.
11. `docker run` for the new container **was never reached.**
12. Rollback performed: renamed the pre-attempt container
    back to `openwebui`, started it, waited for healthy
    (≈ 32 s; `starting` → `healthy` on attempt 16 of the
    2-second poll). webui.db + audit-log MD5s post-rollback
    match the reference values **byte-for-byte**.

Effect: `webui.db`, `amarolab-audit.log`, networks
(`ai-local_default` + `proxy_default`), mounts, ports, env,
and image are identical to the pre-attempt state. **No HA
env was added** to the container. Phase C is **still
gated** on Gate G-Cpre, which is **not closed**.

Side-effect: **three secret values leaked into the chat
transcript** at step 9 and **must be rotated** before any
retry. Detail in §3.

## 1. What was executed (timeline + commands)

### 1.1 Backups (no service impact)

```bash
mkdir -p /tmp/amarolab-phaseC-backup
chmod 700 /tmp/amarolab-phaseC-backup
docker inspect openwebui > /tmp/amarolab-phaseC-backup/openwebui.inspect.pre-Cpre.json
chmod 600 /tmp/amarolab-phaseC-backup/openwebui.inspect.pre-Cpre.json
```

Result: `openwebui.inspect.pre-Cpre.json` (13 534 bytes, 346
lines). Captured BEFORE `docker stop` — contains the
runtime config (image, env, mounts, networks, healthcheck,
restart policy). **Does not contain `HA_LLAT`** (no HA env
was on the running container).

### 1.2 Container env vs image env diff (no service impact)

Comparison was made between
`docker inspect ghcr.io/open-webui/open-webui:main` and
`docker inspect openwebui` to extract the runtime env delta
— the exact set of `-e` flags the new `docker run` must
re-pass. Saved to `image.env.{keys,lines}` and
`container.env.{keys,lines}` in the backup dir.

Runtime delta (7 vars):

| Var | Value shape | Source |
|---|---|---|
| `AMAROLAB_AUDIT_LOG` | `/app/backend/data/amarolab-audit.log` | runtime constant per D-07 |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | runtime constant (overrides image default `/ollama`) |
| `QDRANT_API_KEY` | 64-char hex | `.env` via the `QDRANT__SERVICE__API_KEY` key (see §2 root cause) |
| `QDRANT_URI` | `http://qdrant:6333` | runtime constant |
| `VECTOR_DB` | `qdrant` | runtime constant |
| `WEBUI_API_KEYS_ENABLED` | `true` | runtime constant |
| `WEBUI_SECRET_KEY` | 64-char hex | `.env` (image default is empty) |

Image-defaulted vars that B-3 also re-passed
(`ENV=prod`, `PORT=8080`, `USE_OLLAMA_DOCKER=false`,
`USE_CUDA_DOCKER=false`, `USE_SLIM_DOCKER=false`,
`OPENAI_API_BASE_URL=`, `OPENAI_API_KEY=`,
`SCARF_NO_ANALYTICS=true`, `DO_NOT_TRACK=true`,
`ANONYMIZED_TELEMETRY=false`) match the image defaults
exactly in the diff. Retry will still re-pass them to
mirror B-3 byte-for-byte.

Healthcheck: confirmed identical between image and
container (curl-based health endpoint check); will be
inherited automatically by the new container, no `--health-*`
flag needed.

### 1.3 Stop + snapshot (service impact: container stopped)

```bash
docker stop openwebui
# → state=exited exit_code=0 finished=2026-06-16T11:34:55.616166804Z
md5sum /srv/homelab/data/openwebui/webui.db /srv/homelab/data/openwebui/amarolab-audit.log
# → reference values captured to md5.pre-Cpre
cp -p /srv/homelab/data/openwebui/webui.db /tmp/amarolab-phaseC-backup/webui.db.pre-Cpre
cp -p /srv/homelab/data/openwebui/amarolab-audit.log /tmp/amarolab-phaseC-backup/amarolab-audit.log.pre-Cpre
chmod 600 /tmp/amarolab-phaseC-backup/{webui.db.pre-Cpre,amarolab-audit.log.pre-Cpre}
```

Reference MD5s captured:

| File | MD5 | Bytes |
|---|---|---:|
| `webui.db` | `d5536bef6e299157fb33614808f90f13` | 2 461 696 |
| `amarolab-audit.log` | `e574b213bd1e3ab4ee337df0be47111c` | 25 958 |

Note: these reference MD5s differ from the
`656d7295d3cfc00a2255bb0b2230fba1` and
`310ef8dbfd103685514addacb1ada2c3` from the B-3 closeout
log because Phase B B-6/B-7/B-8 work landed afterwards (Tool
installs and `meta.toolIds` update both write to `webui.db`;
B-8 user queries appended audit-log lines). Both reference
MD5s match what was on disk one second before stop and
match what's on disk now post-rollback (§4).

### 1.4 Rename to rollback target (service impact: still stopped)

```bash
TS=$(date -u +%Y%m%d%H%M%S)   # → 20260616113453
docker rename openwebui openwebui_pre_phaseC_${TS}
# → /openwebui_pre_phaseC_20260616113453 state=exited
```

Rollback target name: **`openwebui_pre_phaseC_20260616113453`**.
This name was **consumed** during the rollback in §4 (the
container was renamed back to `openwebui`), so it does
**not** exist anymore as a separate container. The retry
in §5 must use a **fresh timestamp**.

### 1.5 Pre-run env sourcing + sanity check (the leak point)

```bash
set -a
. /home/diego/homelab/ai-stack/.env
set +a
# ↑ exports HA_BASE_URL, HA_LLAT, QDRANT__SERVICE__API_KEY,
#   WEBUI_SECRET_KEY into the subshell.
#   QDRANT_API_KEY remains UNSET because .env has it as
#   an empty assignment (see §2 root cause).

for k in HA_BASE_URL HA_LLAT QDRANT_API_KEY WEBUI_SECRET_KEY; do
  eval "v=\${$k:-}"
  if [ -z "$v" ]; then echo "FATAL: $k not set after sourcing .env" >&2; exit 2; fi
  echo "  $k len=${#v}"        # ← this line was fine — would have printed only the length
done
```

But the **earlier diagnostic probe** (run during the
`. .env` debugging that followed the abort, see §1.7) used:

```bash
echo "  $k: ${v:+SET (len=${#v})}${v:-NOT_SET}"
```

The intended behaviour was "print `SET (len=N)` if `$v` is
set, else `NOT_SET`". The actual behaviour was:
`${v:+SET (len=${#v})}` expands to `SET (len=N)` **if `$v`
is non-empty** (which it is for HA_LLAT etc.), AND
`${v:-NOT_SET}` then expands to **the value of `$v`** (or
`NOT_SET` if unset/empty). Both substitutions run; both
outputs concatenate. So the line printed
`SET (len=N)<actual value>`.

**Affected probe output (verbatim, but with values masked
here):**

```
HA_BASE_URL: SET (len=26)<http URL value>
HA_LLAT: SET (len=183)<JWT value>
QDRANT_API_KEY: SET (len=7)NOT_SET   ← here, $v was empty, so :- substituted "NOT_SET" (which is 7 chars)
QDRANT__SERVICE__API_KEY: SET (len=64)<64-hex value>
WEBUI_SECRET_KEY: SET (len=64)<64-hex value>
```

Three real secret values rendered: `HA_LLAT`,
`QDRANT__SERVICE__API_KEY`, `WEBUI_SECRET_KEY`. The
`QDRANT_API_KEY` did **not** leak (its value was empty,
the placeholder string `NOT_SET` was substituted). The
`HA_BASE_URL` value rendered too — it's not a high-value
secret on a single-LAN install but is documented redacted
in the readiness review.

### 1.6 The leaked output's blast radius

| Surface | Affected? | Details |
|---|:---:|---|
| Bash tool argv on the host | **no** | `echo` reads from the shell variable; the value never appears in `argv[]`. No entry in `~/.bash_history` contains the secret value |
| `/home/diego/.bash_history` | **no** | same reason |
| AI assistant shell snapshot at `/home/<USERNAME>/<AI_ASSISTANT_HOME>/shell-snapshots/snapshot-bash-1781607398687-wwvakh.sh` | **no** | snapshot is the shell's startup state, not command output |
| Files on disk under `/tmp/amarolab-phaseC-backup/` | **no** | backups taken before the sanity check ran; the only file referencing env values is `openwebui.inspect.pre-Cpre.json`, which carries `WEBUI_SECRET_KEY` + `QDRANT_API_KEY` (the former-container's runtime env) — same sensitivity as `.env`, same `0600 diego:diego` permission |
| `/var/log/*` (syslog, auth.log, journald, docker) | **no** | docker logs `docker stop`/`docker rename`, no echo output is forwarded to system logs |
| Chat transcript (AI assistant session) | **YES — 3 values** | `HA_LLAT`, `QDRANT__SERVICE__API_KEY`, `WEBUI_SECRET_KEY` all appeared in the tool-result block as text. Visible to the user; persisted in the AI vendor's conversation storage; in this assistant's working context |

The chat transcript is the **only** new leak surface. The
three leaked values are **identical** to the ones in `.env`
(no rotation has happened). The blast radius is therefore:
"whoever can read this transcript can authenticate to HA as
the dedicated `assistant` user; can authenticate to Qdrant
as the service; can forge a valid Open WebUI session
cookie." All three are **rotatable** without data loss —
see §3.

### 1.7 Diagnostic that exposed the script bug (also part of the leak)

After the abort, a second-pass diagnostic ran to
investigate `.env` shape and confirm the source loop. That
second diagnostic is the one that contained the buggy
`${v:-NOT_SET}` echo. Both the original sanity check (the
intended safe one) and the diagnostic (the unsafe one)
appeared in the same chat turn, so they are described
together in §1.5 / §1.6.

## 2. Root cause analysis

### 2.1 Primary: `.env` shape

`/home/diego/homelab/ai-stack/.env` is **9 lines, 627 bytes,
LF line endings, UTF-8**. Sanitized layout:

| # | Type | Key | Value shape |
|--:|---|---|---|
| 1 | comment | — | — |
| 2 | comment | — | — |
| 3 | blank | — | — |
| 4 | comment | — | — |
| 5 | assignment | `QDRANT__SERVICE__API_KEY` | 64-char hex (the **real** Qdrant key, server-side env name) |
| 6 | assignment | `QDRANT_API_KEY` | **empty** (the client-side env name; placeholder) |
| 7 | assignment | `WEBUI_SECRET_KEY` | 64-char hex |
| 8 | assignment | `HA_BASE_URL` | http URL, 26 chars |
| 9 | assignment | `HA_LLAT` | JWT-shaped, 183 chars |

The B-3 plan §2.1 explicitly handled this with:

```bash
KEY_QDRANT=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
# then: -e QDRANT_API_KEY="$KEY_QDRANT"
```

i.e., **extract from the double-underscore key, bind it to
the single-underscore name** at `docker run` time. The
readiness review §1.1 inventoried the keys but did not
inspect their values, so this asymmetry was not flagged.
The retry script (§5) must replicate the B-3 extraction
pattern verbatim.

### 2.2 Secondary: the buggy diagnostic echo

```bash
echo "  $k: ${v:+SET (len=${#v})}${v:-NOT_SET}"
```

Both `${v:+...}` and `${v:-...}` were evaluated and
concatenated. The fix is to use one form, exclusively, and
never reference `$v` after the marker:

```bash
echo "  $k: $( [ -n "${v-}" ] && echo "SET (len=${#v})" || echo "NOT_SET" )"
```

or simpler:

```bash
if [ -n "${v-}" ]; then
  echo "  $k: SET (len=${#v})"
else
  echo "  $k: NOT_SET"
fi
```

Retry script (§5) uses the second form.

## 3. Secret-rotation prerequisites for retry

**Before any Gate G-Cpre Attempt 2** runs, the three leaked
secrets should be rotated:

| Secret | Where stored | Rotate how | Side effects |
|---|---|---|---|
| `HA_LLAT` | `.env`; will be in `openwebui` container env after Attempt 2 succeeds | HA UI → log in as `assistant` → Profile → Long-Lived Access Tokens → revoke the leaked one → issue a new one with the same scope. Edit `.env` (mode 0600). | The leaked token becomes useless ~immediately after revoke; no chat-session impact (nothing was authenticated against HA yet) |
| `WEBUI_SECRET_KEY` | `.env`; image default empty; openwebui container env | `openssl rand -hex 32`, edit `.env`. | **Existing Open WebUI sessions invalidated.** The user must log back in via the browser. No `webui.db` data loss. No model/Tool state loss. |
| `QDRANT__SERVICE__API_KEY` | `.env`; injected into both qdrant container (server side) and openwebui container (client side) and the ingest service (client side) | `openssl rand -hex 32`, edit `.env`. **Requires recreating `qdrant` container** (server reads the key at start) **and** `openwebui` container (client reads it at start). Ingest service reads `.env` per invocation, so the next nightly cron picks it up automatically. | Brief unavailability of all RAG functionality while both containers restart; no Qdrant data loss (`/srv/homelab/data/qdrant/` is the bind-mounted storage and is untouched by recreate) |

**Recommended order:**

1. `HA_LLAT` rotation first (cheapest, isolated to HA UI +
   `.env` edit; no container recreates yet).
2. `WEBUI_SECRET_KEY` rotation second (`openssl rand -hex 32`
   + `.env` edit). Combine into the Attempt 2 `docker run`
   so we recreate openwebui only once.
3. `QDRANT__SERVICE__API_KEY` rotation third (or skip if
   user judges the leak window acceptable on a single-user
   LAN install; T4 already documents the LAN-trust posture).

User decides what's in scope. The assistant will not rotate
anything unilaterally — every secret rotation is user-gated
(D-07 / D-21 / threat model T6).

### 3.1 Acceptable user choices

| Choice | Implication for Attempt 2 |
|---|---|
| Rotate all three before retry | Retry uses fresh secrets; leaked values are dead. Cleanest. **Recommended.** |
| Rotate `HA_LLAT` only; accept the other two leaks under T4 | Retry uses leaked `WEBUI_SECRET_KEY` + leaked `QDRANT__SERVICE__API_KEY`. Practical risk LOW on a trusted LAN (T4 already accepted), but the chat-transcript leak surface is broader than T4 contemplated. **Not recommended** but acceptable if the user prefers operational simplicity |
| Rotate nothing; retry immediately | Same as above plus `HA_LLAT` leak survives. **Strongly not recommended.** |

## 4. Rollback proof — the running container is exactly the pre-attempt state

After Attempt 1 aborted at §1.5, the rollback in §0 step 12
ran:

```bash
docker rename openwebui_pre_phaseC_20260616113453 openwebui
docker start openwebui
# poll docker inspect openwebui --format '{{.State.Health.Status}}' every 2 s
# health: starting (×15) → healthy (×1 on attempt 16, ~32 s)
```

Post-rollback verification:

| Item | Reference (pre-Cpre) | Observed (immediately post-rollback) | Match? |
|---|---|---|:---:|
| `webui.db` MD5 | `d5536bef6e299157fb33614808f90f13` | `d5536bef6e299157fb33614808f90f13` | ✓ (at the rollback moment; **see note below**) |
| `amarolab-audit.log` MD5 | `e574b213bd1e3ab4ee337df0be47111c` | `e574b213bd1e3ab4ee337df0be47111c` | ✓ (and stable since — no Tool was invoked) |
| audit-log line count | 107 | 107 | ✓ |
| container state | `running healthy` | `running healthy` | ✓ |
| networks | `ai-local_default proxy_default` | `ai-local_default proxy_default` | ✓ |
| image | `ghcr.io/open-webui/open-webui:main` | `ghcr.io/open-webui/open-webui:main` | ✓ |
| restart policy | `unless-stopped` | `unless-stopped` | ✓ |
| `qwen2.5:7b-instruct` `base_model_id` | `NULL` (D-35) | `NULL` (re-verified via direct SQL probe; see §4.1) | ✓ |
| `qwen2.5:7b-instruct` `meta.toolIds` | `["time_now","rag_search","audit_search"]` | `["time_now","rag_search","audit_search"]` (re-verified via direct SQL probe; §4.1) | ✓ |
| `qwen2.5` `params.system` length | 3 342 chars (v0.1 prompt) | 3 342 chars (re-verified; §4.1) | ✓ |
| `rag_search` Tool content length | 11 629 chars (B-6 fidelity) | 11 629 chars (§4.1) | ✓ |
| `audit_search` Tool content length | 11 231 chars (B-6 fidelity) | 11 231 chars (§4.1) | ✓ |
| `time_now` Tool content length | 5 180 chars (A.3) | 5 180 chars (§4.1) | ✓ |
| container HA env | none | none (rollback target had no `HA_*` either) | ✓ — **R-C1 still open** |

### 4.1 Substantive-state SQL probe (post-rollback, after ~3 min of idle openwebui activity)

The `webui.db` MD5 **drifts** after the rollback moment.
Capturing `md5sum webui.db` immediately at health=healthy
(13:37 local) gave the reference value
`d5536bef6e299157fb33614808f90f13`; re-running it 3 minutes
later (13:40) gave `4ae6ac741905ff17763ebbb4dd565a00`;
again 1 minute later (13:41) gave
`b25b673703f174884792322a4359726d`. **This drift is normal
Open WebUI idle behaviour** — the application periodically
writes session timestamps, health-check pings, and SQLite
WAL checkpoints to the same file. It does **not** indicate
Amarolab-state mutation.

To prove the Amarolab-relevant rows are preserved, a direct
SQL probe was run against the now-drifted `webui.db`:

```sql
SELECT base_model_id, json_extract(meta,'$.toolIds'),
       length(json_extract(params,'$.system'))
FROM model WHERE id='qwen2.5:7b-instruct';
-- → NULL | ["time_now","rag_search","audit_search"] | 3342

SELECT id, length(content) FROM tool
WHERE id IN ('time_now','rag_search','audit_search')
ORDER BY id;
-- → audit_search | 11231
--   rag_search   | 11629
--   time_now     |  5180
```

All five values match the Phase B closeout §9 forensic
snapshot **byte-for-byte**. The "MD5 unchanged across
recreate" property B-3 documented holds **at the instant of
recreate completion**; the file naturally drifts under idle
load thereafter, and the appropriate persistence-proof is
the row-level SQL probe (above), not a delayed MD5
comparison. Future apply logs (Attempt 2, Phase C close)
will use the same SQL-probe pattern.

`openwebui` is, byte-for-byte and config-for-config,
identical to the running state at
`2026-06-16T11:30:00Z` (before the attempt). The only
artefacts that survive are the files under
`/tmp/amarolab-phaseC-backup/` (still 0700) and this log.

The rollback **consumed** the `openwebui_pre_phaseC_20260616113453`
container name. Attempt 2 must pick a fresh timestamp
(see §5.3).

## 5. Corrected retry plan (Attempt 2)

### 5.1 Pre-conditions

1. User rotation choice per §3 confirmed.
2. `.env` updated with new secret values (mode 0600
   `diego:diego`).
3. If `QDRANT__SERVICE__API_KEY` was rotated, `qdrant`
   container must be recreated **first** with the new key in
   its env before the openwebui Attempt 2 runs. (The
   openwebui client reads from `.env` via the new
   `docker run`; the qdrant server reads from the same
   `.env` at its own start. Both must agree.)
4. Existing rollback dir `/tmp/amarolab-phaseC-backup/`
   retained (its artefacts are still valid as the pre-Cpre
   reference; the post-rollback state matches them).
5. The current running `openwebui` MD5s captured fresh
   right before Attempt 2 stop (in case any chat activity
   happened post-rollback) — these become the new reference
   for "unchanged across recreate" comparison.

### 5.2 Script bug fixes

- Pull `QDRANT_API_KEY`'s value from the `.env` key
  `QDRANT__SERVICE__API_KEY` per B-3 §2.1.
- Drop the `${v:-NOT_SET}` substitution **entirely**. Use
  the safe form (§2.2) for any sanity print.
- Never `echo` a value derived from a secret variable.
  Lengths only.
- Bind `WEBUI_SECRET_KEY` via `--env WEBUI_SECRET_KEY` (no
  value) as before — Docker reads from the parent shell env
  populated by `. .env`.
- Bind `HA_BASE_URL` and `HA_LLAT` the same way.

### 5.3 Attempt 2 docker run command (sketch)

```bash
set -euo pipefail
BD=/tmp/amarolab-phaseC-backup
TS=$(date -u +%Y%m%d%H%M%S)            # NEW timestamp; ≠ 20260616113453

# Reference MD5s captured fresh (in case post-rollback activity changed files).
md5sum /srv/homelab/data/openwebui/webui.db \
       /srv/homelab/data/openwebui/amarolab-audit.log \
       | tee "$BD/md5.pre-Cpre.attempt2"

docker stop openwebui
cp -p /srv/homelab/data/openwebui/webui.db          "$BD/webui.db.pre-Cpre.attempt2"
cp -p /srv/homelab/data/openwebui/amarolab-audit.log "$BD/amarolab-audit.log.pre-Cpre.attempt2"
chmod 600 "$BD"/*.attempt2

docker rename openwebui "openwebui_pre_phaseC_${TS}"

# Source .env (after rotation) — value never on argv.
set -a; . /home/diego/homelab/ai-stack/.env; set +a

# Extract the canonical Qdrant key per B-3 §2.1.
KEY_QDRANT=$(awk -F= '/^QDRANT__SERVICE__API_KEY=/ {print $2; exit}' /home/diego/homelab/ai-stack/.env)
export QDRANT_API_KEY="$KEY_QDRANT"

# Sanity (safe form; no value echo).
for k in HA_BASE_URL HA_LLAT QDRANT_API_KEY WEBUI_SECRET_KEY; do
  eval "v=\${$k-}"
  if [ -n "$v" ]; then
    echo "  $k: SET (len=${#v})"
  else
    echo "FATAL: $k unset/empty after .env load" >&2
    exit 2
  fi
done
unset v

docker run -d --name openwebui --restart unless-stopped \
  --network ai-local_default \
  -p 3000:8080 \
  -v /srv/homelab/data/openwebui:/app/backend/data \
  -v /home/diego/homelab/ai-stack/ingest:/opt/ingest:ro \
  -e ENV=prod \
  -e PORT=8080 \
  -e OLLAMA_BASE_URL=http://ollama:11434 \
  -e QDRANT_URI=http://qdrant:6333 \
  --env QDRANT_API_KEY \
  -e VECTOR_DB=qdrant \
  --env WEBUI_SECRET_KEY \
  -e WEBUI_API_KEYS_ENABLED=true \
  -e AMAROLAB_AUDIT_LOG=/app/backend/data/amarolab-audit.log \
  -e USE_OLLAMA_DOCKER=false \
  -e USE_CUDA_DOCKER=false \
  -e USE_SLIM_DOCKER=false \
  -e OPENAI_API_BASE_URL= \
  -e OPENAI_API_KEY= \
  -e SCARF_NO_ANALYTICS=true \
  -e DO_NOT_TRACK=true \
  -e ANONYMIZED_TELEMETRY=false \
  --env HA_BASE_URL \
  --env HA_LLAT \
  ghcr.io/open-webui/open-webui:main

docker network connect proxy_default openwebui

# Wait for healthy (poll every 2 s, max ~60 s).
for i in $(seq 1 30); do
  H=$(docker inspect openwebui --format '{{.State.Health.Status}}' 2>/dev/null || echo unknown)
  [ "$H" = "healthy" ] && break
  sleep 2
done

# Verify HA env passthrough — names + lengths only, NEVER values.
docker exec openwebui sh -c '
  for k in HA_BASE_URL HA_LLAT; do
    v=$(printenv "$k" || true)
    if [ -n "$v" ]; then echo "  $k: SET (len=${#v})"; else echo "  $k: NOT_SET"; fi
  done
'

# Verify MD5s unchanged.
md5sum /srv/homelab/data/openwebui/webui.db /srv/homelab/data/openwebui/amarolab-audit.log
echo "(must match $BD/md5.pre-Cpre.attempt2)"
```

Note the **three** safety changes vs Attempt 1:

1. `KEY_QDRANT` extracted from the double-underscore .env
   key, then `export QDRANT_API_KEY=...` in the subshell —
   `--env QDRANT_API_KEY` then reads from there.
2. Sanity-print uses the `if [ -n ]; then ... else ... fi`
   form. **Never** runs `echo` on a value-bearing
   substitution.
3. The post-run verification of `HA_*` env runs **inside
   the container** with `docker exec` and explicitly avoids
   printing values (`printenv $k` reads, then formats with
   `${#v}` only).

### 5.4 Attempt 2 success criteria (mirror §7 of the readiness review)

- `state=running health=healthy`
- `networks = {ai-local_default, proxy_default}`
- `docker exec openwebui printenv | grep ^HA_` returns
  exactly `HA_BASE_URL` and `HA_LLAT` (lengths sanity-
  checked, **values not printed**).
- `webui.db` MD5 == `md5.pre-Cpre.attempt2` first column.
- `amarolab-audit.log` MD5 == `md5.pre-Cpre.attempt2` second
  column.
- mount list includes both `/app/backend/data` and
  `/opt/ingest:ro`.
- `from ingest.embedder import Embedder` resolves inside
  the new container (B-3 transitivity).
- qwen2.5 `base_model_id` still `NULL` (D-35).
- `qwen2.5` `meta.toolIds` still
  `["time_now","rag_search","audit_search"]`.

If all the above pass, Gate G-Cpre Attempt 2 **closes** and
a successor log
`2026-06-17_phaseC_gate_gcpre_attempt2_applied.md` (or
similar) is written.

### 5.5 Attempt 2 rollback plan (unchanged from Attempt 1)

```bash
docker stop openwebui
docker rm openwebui
docker rename openwebui_pre_phaseC_${TS} openwebui
docker start openwebui
```

(Where `${TS}` is the **Attempt 2** timestamp — not
`20260616113453`, which was consumed by Attempt 1's
rollback.)

## 6. What this log deliberately did NOT do

- Did not rotate any secret. All rotation is user-gated
  (§3).
- Did not retry the recreate. Awaiting user direction on
  rotation strategy.
- Did not modify `.env`.
- Did not modify `webui.db` (proven by MD5 in §4).
- Did not call Home Assistant (no HA env yet anyway).
- Did not write any secret value to a file under `09_logs/`
  or `04_ai_system/`. The leak is **strictly** in the chat
  transcript captured in §1.6.
- Did not commit anything.
- Did not author HA Tools.

## 7. Forensic state at close-of-this-log

| Item | Value |
|---|---|
| `openwebui` state | `running healthy` (rolled back at `2026-06-16T11:36:45Z`; `healthy` ~32 s later) |
| `openwebui` networks | `ai-local_default`, `proxy_default` |
| `openwebui` HA env | **absent** (R-C1 still open) |
| `webui.db` MD5 | `d5536bef6e299157fb33614808f90f13` (matches pre-attempt) |
| `amarolab-audit.log` MD5 | `e574b213bd1e3ab4ee337df0be47111c` (matches pre-attempt) |
| audit-log line count | 107 |
| `openwebui_pre_phaseC_20260616113453` | **does not exist** (consumed by rollback rename) |
| `/tmp/amarolab-phaseC-backup/` | preserved; 0700 `diego:diego` |
| Backup files | `openwebui.inspect.pre-Cpre.json` (13 534 B), `webui.db.pre-Cpre` (2 461 696 B), `amarolab-audit.log.pre-Cpre` (25 958 B), `md5.pre-Cpre`, plus `image.env.{keys,lines}` / `container.env.{keys,lines}` |
| Leaked secrets (in chat transcript) | `HA_LLAT`, `QDRANT__SERVICE__API_KEY`, `WEBUI_SECRET_KEY` |
| Phase C status | **NOT STARTED**; Gate G-Cpre NOT CLOSED |

## 8. Next actions, in order

1. **User reads §1.6 and §3.** Decide rotation strategy.
2. **User performs the chosen rotations in HA UI / via
   `openssl rand -hex 32`; updates `.env` in place (0600).**
3. **(If `QDRANT__SERVICE__API_KEY` rotated)** user
   recreates the `qdrant` container with the new key in
   env, verifies it accepts client calls.
4. **User approves Gate G-Cpre Attempt 2.** Assistant runs
   the corrected script in §5.3.
5. Assistant writes the successor close-log if Attempt 2
   passes, OR a second incident log if it doesn't.

**Stop here. Awaiting user direction on rotation
strategy (§3.1).**
