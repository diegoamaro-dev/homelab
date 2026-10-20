# Incident — Aurora disappeared from Open WebUI (Torre model store behind a moved drive letter)

**Date:** 2026-10-19 → 2026-10-20
**Type:** Dated incident record. Documentation only.
**Status:** **RESOLVED** (2026-10-20 03:18 CEST).
- The root cause was remedied on Torre (storage mapping restored, `OllamaService` recovered).
- The Torre GPU path was re-validated end to end from the UM790 (**V-1 PASS**, §9).
- Aurora's definition, its data and the model were never lost.
- **Preventive items F-INC-1…3 remain open as follow-ups** (§13). None is implemented.

**Production changed by this document:** **no.**
- **Recovery work** happened on Torre (Windows), performed by the operator.
- **On the UM790** nothing was changed at any point: no Aurora, Open WebUI, Ollama,
  `ollama-proxy`, Qdrant, Home Assistant, Docker, networking or storage change.

> Dated record (`PROJECT_RULES.md` → *Historical Documentation*). It states what was known on
> 2026-10-20 and is not rewritten as the situation advances. Earlier records are not modified.

**Evidence labels:**
- **OBSERVED** — read-only checks from the UM790.
- **OPERATOR-REPORTED** — the operator's checks and actions on Torre (Windows) and in the UI.
- **INFERRED** — a reasoned conclusion that was not observed directly.
- **RECOMMENDATION** — a future action. None is authorized by this record.

---

## 1. Context

- **Aurora is the persistent assistant / configuration layer hosted on the UM790**, through Open
  WebUI and the platform around it. Its identity, configuration and persistent state remained
  intact on the UM790 throughout this incident (§5.1).
- **`qwen2.5:7b-instruct` is Aurora's base inference model, not Aurora itself.**
  - It may exist on both the UM790 and Torre.
  - Aurora's Open WebUI model entry has `base_model_id NULL`, so it **overlays** its
    configuration onto a model of the same id that the Ollama endpoint must publish
    (`CURRENT_STATE.md` → *Open WebUI*).
- **Torre is the preferred, replaceable GPU inference accelerator**, not where Aurora's state is
  kept (`ROADMAP.md` → *Post-RTX-1 follow-ups*).
- Since RTX-1.6, Open WebUI and Home Assistant reach Ollama through `ollama-proxy`:
  - **primary:** Torre's GPU Ollama, over Tailscale;
  - **backup:** the UM790 CPU Ollama.
- nginx moves a request to the backup only on `error | timeout | 502 | 503 | 504`
  (`03_services/ollama-proxy/nginx.conf`).
- On Torre, Ollama runs as the NSSM service `OllamaService`, which wraps `ollama.exe serve`. Its
  model store is configured as `OLLAMA_MODELS=D:\ai\ollama\models`
  (`06_security/rtx_node_security.md`).

## 2. User-visible symptom

- **Aurora disappeared from Open WebUI.** The chat front door could no longer select it
  (OPERATOR-REPORTED).

## 3. Impact

- **Chat front door (`ai.amarolab.es`):** Aurora was unavailable (OBSERVED cause, §5.1).
- **Home Assistant voice:** it uses the same proxy and model id, so it was very likely affected
  too (INFERRED). Not tested during the incident.
- **No data loss, no configuration change on the UM790, no security impact** (§10, §11).

**Duration**

| Period (CEST) | State | Label |
|---|---|---|
| until 2026-10-19 21:48:36 | Normal: last chat served by Torre with `200` | OBSERVED |
| 21:48 → 2026-10-20 ~01:46 | Failure began somewhere in this window. No proxy traffic exists to narrow it | OBSERVED |
| ~01:46 → ~02:20 | Torre reachable and serving an empty catalogue. Aurora unavailable | OBSERVED |
| 02:25 → 03:15 | Torre's port times out intermittently and the proxy falls back to the UM790 CPU | OBSERVED |
| 02:25 → 03:15 | These timeouts are attributed to the Torre recovery work then in progress | INFERRED |
| from 03:18 | Normal operation through Torre | OBSERVED |

## 4. Investigation and recovery timeline (CEST, 2026-10-20 unless noted)

| Time | Event | Label |
|---|---|---|
| 10-19 21:48:36 | Last `POST /api/chat` served by Torre with `200` before the incident | OBSERVED |
| before ~01:46 | Windows SSD/boot troubleshooting on Torre: both SSDs physically removed and reinstalled | OPERATOR-REPORTED |
| ~01:46 | Torre `GET /api/tags` returns `200` with an **empty** model list | OBSERVED |
| 01:54:30 | `POST /api/show qwen2.5:7b-instruct` against Torre returns **`404`** | OBSERVED |
| ~01:46 → ~02:20 | Read-only investigation on the UM790 (§5.1) | OBSERVED |
| after ~02:20 | Windows-side diagnosis and storage recovery (§5.2, §8) | OPERATOR-REPORTED |
| 02:25:05 → 03:15:47 | Intermittent connect timeouts to Torre's port in the proxy log. The proxy fails over to the UM790 on each one | OBSERVED |
| 02:25:05 → 03:15:47 | The timeouts coincide with the operator's `OllamaService` recovery work (§8) and are attributed to it | INFERRED |
| 03:05:38 | First proxied chat served by Torre since the incident (`200`) | OBSERVED |
| from 03:18:20 | Continuous `200`s with Torre as the **only** upstream: `GET /api/tags` and nine `POST /api/chat` | OBSERVED |
| 03:19:38 → 03:20:12 | Proxied `POST /api/chat` requests at `200`, Torre the only upstream, upstream times 0.4–5.2 s | OBSERVED |
| after 03:18 | Aurora visible again in Open WebUI; a real interaction answered successfully at normal RTX-backed speed | OPERATOR-REPORTED |
| 03:25 | Read-only V-1 check from the UM790 passes (§9) | OBSERVED |

## 5. Evidence

### 5.1 UM790 side (OBSERVED, read-only)

**Open WebUI**
- `running`, `healthy`, `RestartCount 0`, same image.
- Not recreated since 2026-06-28.
- Up since the 2026-10-07 boot.

**Persistence**
- The container's `webui.db` is the same inode as the host bind-mount file.
- No database or migration errors in the container log.

**Aurora's definition**
- The model row exists and is `is_active=1`.
- Its tool associations are intact (6 `toolIds`) and its system prompt is unchanged.
- Its `updated_at` is unchanged since June.
- The `aurora_context` filter is active and global.
- The single admin user owns the model.
- Inspected with `sqlite3 -readonly`. Identifiers, sizes and timestamps only; no content was
  printed.

**RAG / memory**
- All Qdrant collections are present and `green`.

**Home Assistant**
- The `ollama` (proxy endpoint), Wyoming ×3 and MQTT integrations are present and enabled.
- `HA_BASE_URL` answers `200` from the Open WebUI container.

**Providers during the incident**

| Endpoint | `/api/tags` | `qwen2.5:7b-instruct` |
|---|---|---|
| Torre (primary) | `200`, **zero models** | `404` |
| UM790 (backup) | listed | present, `200` on `/api/show` |

**Proxy**
- A `200` with an empty list, and a `404`, are **not** failover conditions.
- So the proxy kept routing to the reachable-but-empty Torre and never consulted the backup.

**Unexplained observation, not attributed**
- The six Open WebUI tool rows carry `updated_at` 2026-10-15 22:08:31. That is the same second
  as a proxied chat request, five days before the incident.
- No link to this incident is asserted.

### 5.2 Torre side (OPERATOR-REPORTED)

**Storage layout during the incident**
- Both SSDs had been physically removed and reinstalled during Windows boot/storage
  troubleshooting.
- Windows then assigned drive letters differently:
  - the model-storage volume (label `Contenedor`), which normally provides `D:`, received
    another letter;
  - a Google Drive for desktop virtual drive temporarily occupied `D:`.
- `OllamaService` was still configured with `OLLAMA_MODELS=D:\ai\ollama\models`, so it was
  pointed at a location that did not hold the model store.
- The model data itself was intact on the `Contenedor` volume.

**Service state**
- `OllamaService` was found **Paused/orphaned**: the NSSM wrapper existed, but no
  `ollama.exe` child process was running.
- Start attempts during recovery hit transient port-bind conflicts on 11434 (§8).

**Windows events**
- Windows logs show abnormal shutdown/startup events in the same period. They are consistent
  with the operator's troubleshooting.
- They do not indicate model deletion; none occurred.

## 6. Ruled-out hypotheses

| Hypothesis | Ruled out by | Label |
|---|---|---|
| Aurora deleted or modified in Open WebUI | Row present, active, `updated_at` unchanged | OBSERVED |
| Open WebUI on a different or new database | Same inode, same bind mount, no recreation, no migration | OBSERVED |
| User / auth / workspace visibility change | Single admin user, still the owner | OBSERVED |
| RAG / vector data loss | All collections `green` | OBSERVED |
| Home Assistant integration lost | Integrations present and enabled | OBSERVED |
| The model was deleted on Torre | Blobs and manifests intact; `qwen2.5:7b-instruct` present at 4.7 GB once `D:` was restored | OPERATOR-REPORTED, then OBSERVED in §9 |
| An unexpected Windows shutdown deleted the models | Nothing was deleted. The abnormal events match the operator's troubleshooting | OPERATOR-REPORTED |
| The QR deployment, active in a similar window, caused it | Investigated separately: no evidence of QR activity modifying Torre, Ollama, `D:\ai`, NSSM, `OLLAMA_MODELS` or the model store. **Temporal proximity is not causation; no causality is attributed to QR** | OPERATOR-REPORTED |
| The 2026-10-20 documentation reconciliation touched Open WebUI | It edited repository documentation only. Open WebUI's `ai-stack/` mounts are read-only and were not modified | OBSERVED |

## 7. Root cause

**The Torre Ollama provider depended on a mutable Windows drive-letter mapping.**

1. Physical SSD removal and reinsertion during boot/storage troubleshooting changed Windows'
   drive-letter assignment.
2. The model-storage volume no longer provided `D:`; a Google Drive virtual drive occupied it.
3. `OllamaService` still used `OLLAMA_MODELS=D:\ai\ollama\models`, so Torre's Ollama could not
   see the model store and returned an **empty model catalogue**.
4. Torre stayed reachable and answered `200`/`404`, so `ollama-proxy` did not fail over.
5. The base model disappeared from the provider catalogue Open WebUI saw. Aurora, which
   overlays that base model, therefore disappeared from the UI, although its configuration and
   persistent data were intact.

Steps 1–3 are OPERATOR-REPORTED. Steps 3–5 are OBSERVED from the UM790.

**Contributing factor.** During recovery, `OllamaService` was in a Paused/orphaned state (NSSM
without an `ollama.exe` child) and had transient port-bind conflicts (OPERATOR-REPORTED). This
prolonged the recovery; it was not the trigger. Its origin is **UNKNOWN**.

## 8. Recovery

All recovery work was on Torre and is OPERATOR-REPORTED.

**Storage**
1. Moved the Google Drive virtual drive away from `D:`.
2. Restored the `Contenedor` volume to `D:`.
3. Confirmed `D:\ai\ollama\models` holds the existing blobs and manifests, with
   `qwen2.5:7b-instruct` present at 4.7 GB.

**`OllamaService`**
1. Found it Paused/orphaned and stopped it successfully.
2. Initial `Start-Service` attempts returned errors. Logs showed transient port-bind conflicts
   during the investigation.
3. Ran a manual `ollama.exe serve`. It proved the executable, model store, listener and
   inference path all worked. The manual instance was then stopped.
4. `OllamaService` then reached `Running`. Verified:
   - the process tree is `NSSM → ollama.exe serve`;
   - `ollama.exe` listens on 11434;
   - the service-managed instance lists `qwen2.5:7b-instruct`.

**Not required and not performed:**
- no Open WebUI restore;
- no `webui.db` recovery;
- no Qdrant restore;
- no Aurora recreation;
- no model re-download;
- no backup restore;
- no change on the UM790.

## 9. Validation — V-1 PASS

**OBSERVED from the UM790, 2026-10-20 03:18–03:25 CEST (read-only)**
- `GET /api/tags` against Torre over Tailscale returns `qwen2.5:7b-instruct` (4.7 GB).
- `GET /api/tags` through `ollama-proxy` returns `qwen2.5:7b-instruct`.
- The proxy log shows `POST /api/chat` requests at `200` with Torre as the **only** upstream,
  with upstream times of 0.4–5.2 s. There have been no connect timeouts since
  03:15:47.

**OPERATOR-REPORTED**
- Aurora is visible again in Open WebUI.
- A real Aurora interaction succeeded, with the expected fast, RTX-backed performance.

**Interim state, for the record**
- Between 02:25 and 03:15 the proxy repeatedly marked Torre down on connect timeouts and served
  from the UM790 CPU.
- That is the designed transport failover working while Torre was being recovered (INFERRED:
  the attribution to the recovery work is not directly logged).
- It is not a separate fault.

## 10. Data-integrity assessment

**No data loss occurred.**

**UM790 (OBSERVED)**
- Open WebUI data, the Aurora definition, tools, filter, Qdrant collections and Home Assistant
  configuration are all intact.

**Torre (OPERATOR-REPORTED; model presence also OBSERVED in §9)**
- Blobs and manifests are intact.
- `qwen2.5:7b-instruct` was never deleted and was not re-downloaded.

**Backups**
- No restore was needed or run.
- The latest nightly backup evidence before the incident is snapshot `536e0020` (2026-10-19
  03:00).
- A restore of `webui.db` has **never** been validated; the documented drills cover Qdrant and
  operational digests only. Recorded for completeness; it did not affect this incident.

## 11. Security / privacy notes

- **Security posture:** no credential, token, firewall, Tailscale, Cloudflare or exposure change
  occurred or was needed. This was an availability incident only.
- **Investigation hygiene:** read-only commands only on the UM790. No conversation content,
  memory text or secret was printed.
- **This record omits:**
  - IP addresses and the tailnet name;
  - cloud-account identities;
  - disk models, serials and volume GUIDs;
  - Windows process identifiers.

  It names the drive letter, the model-store path and the volume label, because they *are* the
  finding. The path is already documented in `06_security/rtx_node_security.md`.

## 12. Lessons learned

1. **A drive letter is not a storage identity.**
   - Windows assigns letters at mount time. They move when disks are added, removed or
     re-cabled, and other software (here, a cloud-sync virtual drive) can claim a freed letter.
   - A service configured by letter keeps starting cleanly against whatever holds that letter.
   - Recorded as `07_operations/lessons_learned.md` → *L-RTX-3*.
2. **Reachable is not the same as able to serve.**
   - The failover design covered a Torre that is *down*. It did not cover a Torre that is *up
     but empty*.
   - So the "a Torre outage only degrades performance" assurance held for transport failures
     and failed for this one.
3. **Disappearance in the UI was a dependency symptom, not data loss.**
   - Checking persistence before acting avoided a needless restore, Aurora recreation or model
     re-download.
4. **Verify the service-managed process, not just the service status.**
   - "Paused/orphaned" NSSM with no child process looked like a service that existed.
   - Proof of recovery was the process tree, the listener and the catalogue it served — the same
     instinct as *L-RTX-1*.

## 13. Follow-up items

All of these are **RECOMMENDATIONS**. None is authorized or implemented by this record.

| ID | Item | Type | Note |
|---|---|---|---|
| ~~V-1~~ | Observe the Torre GPU path serving `qwen2.5:7b-instruct` from the UM790 | validation | **PASS 2026-10-20 03:25** (§9) |
| **F-INC-1** | Remove or harden the drive-letter dependency of Torre's model store | resilience | Candidates are Windows-side configuration: a pinned drive letter for the model volume, or a volume-stable path (e.g. an NTFS mount folder) for `OLLAMA_MODELS`. Choose and validate as a separate, approved change |
| **F-INC-2** | Improve `ollama-proxy` functional-health detection, so that `200` with an empty model catalogue does not count as a healthy preferred provider | design | Not a fix request. Weigh the simplest option first, e.g. a check that requires the expected model to be listed. Keep it proportionate (`PROJECT_RULES.md` → *Infrastructure Philosophy*; `01_architecture/hardware_agnostic_compute_architecture.md` §R-3) |
| **F-INC-3** | Add or update the Torre recovery runbook | runbook | Cover storage mapping, `OllamaService`/NSSM state including the Paused/orphaned case and port-bind conflicts, model-store verification, and end-to-end validation from the UM790. Natural home: the recovery section of `06_security/rtx_node_security.md` |

---

## References

- `00_overview/CURRENT_STATE.md` → *ollama-proxy* (failover claim corrected by this record)
- `06_security/rtx_node_security.md` (Torre service, model store, recovery)
- `06_security/security_posture.md` → *ollama-proxy* accepted risk
- `01_architecture/hardware_agnostic_compute_architecture.md` §R-2 / §R-3
- `03_services/ollama-proxy/nginx.conf` (failover conditions)
- `07_operations/lessons_learned.md` → *L-RTX-1*, *L-RTX-3*
