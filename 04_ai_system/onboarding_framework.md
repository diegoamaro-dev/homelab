# AMAROLAB Knowledge Platform — Onboarding Framework

- **Status:** Standing reference. Validated in E-6 (2026-06-28) against disposable corpus `e6_test`.
- **Authority:** This document defines the repeatable procedure for onboarding future knowledge domains. Follow it in full. Deviations must be documented.
- **Platform contract:** [`knowledge_platform_contract.md`](knowledge_platform_contract.md)

---

## Success criterion

> A new knowledge domain can be onboarded, validated and completely removed without leaving any production artifact or changing the behaviour of existing collections.

---

## 1. Naming rules

Collection names must:

- Match `[a-z][a-z0-9_]*` — lowercase, digits, underscores only; no hyphens.
- Be unique across `corpora.yaml` and Qdrant. Check both before choosing a name.
- Be ≤ 32 characters.
- Be descriptive and stable — renaming a collection requires a full re-index.

**Examples:** `homelab_docs`, `guardian_cloud`, `myfreetour`, `e6_test`

---

## 2. Folder and path expectations

### `type: fs`

- `path` must be an **absolute path** on the UM790 host.
- The directory must exist and be readable by the `diego` user at sync time.
- The path is stored verbatim in the `source_path` payload field of every indexed chunk — treat it as non-sensitive, or sanitize content before indexing.

### `type: git`

- `path` must be an **absolute path** to a local git clone on the host (i.e. `.git/` must exist at `<path>/.git`).
- The connector runs `git pull` at sync time — network access is required.
- Clones managed outside the homelab repo (e.g. `guardian_cloud` at `/mnt/storage/projects/guardian-cloud`) must remain accessible at the configured path.

---

## 3. Corpus definition template

Add one entry to `ai-stack/ingest/conf/corpora.yaml` under the `corpora:` list:

```yaml
- name: <collection_name>          # snake_case, unique, ≤ 32 chars
  type: fs                         # fs | git
  path: /absolute/path/to/content  # host path; must exist at sync time
  include:
    - "**/*.md"                    # glob patterns relative to path
    # add further patterns as needed
  exclude:
    - "secrets/**"                 # exclude any sensitive subtree
    # mirror exclude_global if fine-tuning is needed
  enabled: true                    # false = placeholder; skip without error
```

`source_kind_map` is inherited from `defaults` unless overridden. The global
`exclude_global` list (`.git/`, `node_modules/`, `venv/`, etc.) always applies.

**Placeholder pattern:** if a domain is not yet ready to index, add it with
`enabled: false`. A disabled corpus is an expected skip (rc 0, `skipped_reason`
populated) — it does not fail the nightly run.

---

## 4. Collection creation

Collections are **not** auto-created by the ingest pipeline. `bin/ingest init` is a
no-op. Create the collection via the Qdrant REST API before the first sync:

```bash
curl -s -X PUT "http://127.0.0.1:6333/collections/<collection_name>" \
  -H "api-key: $QDRANT__SERVICE__API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 384, "distance": "Cosine"}}'
```

Required parameters — do not change:

| Parameter | Value | Reason |
|---|---|---|
| `size` | `384` | Embedder output dimension (EMBED_DIM, `intfloat/multilingual-e5-small`) |
| `distance` | `"Cosine"` | Platform embedding contract (D-08) |

Verify creation:

```bash
bin/ingest status   # e6_test should appear with 0 points
```

If the collection does not exist when `sync` runs, Qdrant returns an error and the
sync exits rc=1. Create the collection first.

---

## 5. Empty-collection behaviour

A collection with 0 points (immediately after creation, or after `bin/ingest drop`)
returns the following from `rag_search`:

```json
{"hits": [], "code": "empty_collection"}
```

The LLM receives a clean empty signal and apologises without hallucinating. This is
the correct behaviour for a newly created collection that has not yet been indexed,
or for a placeholder with `enabled: false`.

---

## 6. Indexing procedure

```bash
# 1. Dry-run first (walks and chunks but does not embed or write to Qdrant)
bin/ingest sync --collection <collection_name> --dry-run

# 2. Inspect output: confirm files_seen > 0, no errors
# 3. Full sync
bin/ingest sync --collection <collection_name>

# 4. Confirm point count
bin/ingest status
```

The sync is **idempotent** — re-running it on unchanged content is a no-op
(`files_skipped_unchanged` = files_seen, `chunks_upserted` = 0, rc=0).

After any content change, re-run `bin/ingest sync --collection <collection_name>`.
The next nightly run via `bin/ingest-nightly` will include it in the full sync
automatically (no cron change needed).

---

## 7. `rag_search` tool extension

After the corpus is indexed and retrieval is validated via `bin/ingest search` (§8),
extend the tool so the LLM can route queries to the new collection:

1. Edit `ai-stack/openwebui-tools/tools/rag_search.py`:
   - Add the collection name to the `Literal[...]` type annotation on the `collection` parameter.
   - Add a description of the new corpus to the `:param collection:` docstring.
2. Reinstall the tool:
   ```bash
   bin/install_tool rag_search
   ```
3. **No container recreate needed** for a tool code update — the tool Python source
   is stored in Open WebUI's database (not the bind-mount). A container recreate is
   only required if the **ingest package** at `/opt/ingest` is changed.
4. Verify the updated enum and docstring are live in the Open WebUI admin panel.

---

## 8. Validation procedure

Validate at two levels:

### Level 1 — Pipeline (always required)

```bash
bin/ingest search --collection <collection_name> --query "<query_1>"
bin/ingest search --collection <collection_name> --query "<query_2>"
# ... at minimum 3 queries covering different subtopics
```

For each query, verify:
- At least one hit returned (non-empty result).
- Top hit `source_rel` is the expected file.
- `content` excerpt is coherent and relevant.

### Level 2 — End-to-end (required for production corpora)

After extending `rag_search` (§7), make a call through the Open WebUI web UI that
forces a `rag_search` invocation targeting the new collection. Verify:
- The tool is dispatched (visible in the tool call trace).
- Hits are returned from the correct collection.
- The audit log records the call (`check-audit-liveness` will report fresh).

---

## 9. Retrieval fixture extension rules

The permanent fixture at `04_ai_system/validation/retrieval_validation_fixture.yaml`
documents the retrieval contract for **production collections**. Rules:

- Add **minimum 2 queries** per production collection (recommended: 4, as for existing corpora — 2 in each active language).
- Queries must be **byte-stable**: no time-sensitive terms ("latest", "current date"), no references to ephemeral state.
- Queries must cover **at least 2 distinct subtopics** within the collection.
- After adding queries, run the full fixture and confirm no regression on the existing entries.
- **Disposable / test corpora** (like `e6_test`) must NOT be added to the permanent fixture. Use a temporary validation script instead.

---

## 10. Rollback and removal procedure

Two modes:

### Mode A — Placeholder (suspend indexing, keep collection)

1. Set `enabled: false` in the `corpora.yaml` entry.
2. Remove the collection name from `rag_search.py` `Literal[...]` and reinstall the tool.
3. The Qdrant collection is preserved (points remain). Re-enable later by reversing both steps.

### Mode B — Full removal (no trace in production)

Execute in order:

```bash
# 1. Revert corpora.yaml: remove the entry entirely (or set enabled: false, then remove)
# 2. Drop all points (does not delete the collection itself)
bin/ingest drop --collection <collection_name> --yes
# 3. Delete the Qdrant collection
curl -s -X DELETE "http://127.0.0.1:6333/collections/<collection_name>" \
  -H "api-key: $QDRANT__SERVICE__API_KEY"
# 4. Revert rag_search.py Literal[...] and reinstall
bin/install_tool rag_search
# 5. Remove fixture entries (if any were added)
# 6. Remove source content (if it was a disposable corpus)
# 7. Run full sync and verify rc=0, production counts unchanged
bin/ingest sync
bin/ingest status
```

After Mode B, `bin/ingest status` must not show the removed collection, and the
production point counts (1911/2918/872/419/280/0 as of 2026-06-28, post F-1 corpus split) must be unchanged.

---

## 11. Documentation requirements

Every production onboarding must produce:

| Artefact | Location | Content |
|---|---|---|
| Apply log | `09_logs/YYYY-MM-DD_<domain>_onboarding_applied.md` | Procedure, point count, validation evidence |
| Contract update | `04_ai_system/knowledge_platform_contract.md` §3 | Add row to collection inventory table |
| Tool update | `ai-stack/openwebui-tools/tools/rag_search.py` | `Literal[...]` + docstring |
| Fixture entries | `04_ai_system/validation/retrieval_validation_fixture.yaml` | ≥2 queries (production corpus only) |

Disposable corpora (used for framework validation or testing) require an apply log
only. They must be fully removed before documentation is committed.

---

## 12. Security and privacy rules

- **No secrets in corpus content.** API keys, tokens, passwords, or private keys must not appear in any indexed document. Ingest stores `content` verbatim in Qdrant payloads and returns it to the LLM.
- **No PII without review.** Personal names, addresses, or financial data require explicit approval before indexing.
- **Corpus content is LLM-visible.** Any user with Open WebUI access can trigger a `rag_search` call and see chunk content. Treat indexed content as accessible to all AMAROLAB users.
- **`source_path` is stored in Qdrant.** Absolute host paths appear in the payload. These are not sensitive in the current single-user context but should not include credential paths.
- **`guardian_cloud` is read-only.** The Guardian Cloud git clone must not be modified during or after onboarding operations. No write operations on `/mnt/storage/projects/guardian-cloud`.
- **New collections are isolated.** Points in `e6_test` are never mixed with points in `homelab_docs` or any other collection. `rag_search` routes to exactly one collection per call.

---

## Appendix — E-6 proof summary (2026-06-28)

The framework was validated end-to-end using a disposable corpus `e6_test`
(fictional Project Helios — IoT temperature monitoring). Full procedure in apply log:
[`../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md`](../09_logs/2026-06-28_phaseE_E6_onboarding_framework_applied.md).

Result: the success criterion was met — `e6_test` was onboarded, validated, and
completely removed without leaving any production artifact or changing the behaviour
of existing collections.
