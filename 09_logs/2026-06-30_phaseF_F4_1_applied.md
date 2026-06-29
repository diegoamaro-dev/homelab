# F4.1 — ops_digests retrieval substrate (applied)

- **Phase / milestone:** F — Operational Intelligence · **F4.1** (frozen at F4.0;
  authority: [`04_ai_system/phase_f_architecture.md`](../04_ai_system/phase_f_architecture.md) §9-F-4, AD-14…AD-18).
- **Date:** 2026-06-30.
- **Scope:** Stand up the operational-memory retrieval substrate — create the
  `ops_digests` collection, wire it into the ingest pipeline, and extend `rag_search`
  to route to it. **No digest generator** (that is F4.2).
- **Status:** IMPLEMENTED. **G-F4-03 (partial)** + **G-F4-04 (empty-path + enum live)**
  PASS. **STOP at the git approval gate** — nothing committed/pushed/tagged.

## Implementation (E-6 onboarding framework)

1. **Collection** — `PUT /collections/ops_digests` at **size 384 / Cosine** (D-08;
   framework §4), created via the ingest config loader so the Qdrant key never touched
   the shell. Verified `size=384 distance=Cosine points=0 status=green`.
2. **Corpus** — added the `ops_digests` entry to
   [`ai-stack/ingest/conf/corpora.yaml`](../ai-stack/ingest/conf/corpora.yaml)
   (`type: fs`, `path: /home/diego/homelab/09_ops/runtime`, `include: ["**/*.md"]`,
   `enabled: true`), placed after `knowledge_history`.
3. **Tool** — [`rag_search.py`](../ai-stack/openwebui-tools/tools/rag_search.py)
   `0.1.0 → 0.2.0`: added `"ops_digests"` to the `collection` `Literal`, the
   frontmatter description, the `:param collection:` doc, and the routing docstring
   (with the same-night → `system_status` caveat, AD-04/AD-17). Reinstalled via
   `bin/install_tool` (`action=update`, `specs=1`); **no container recreate**
   (framework §7.3).

## Validation

- **G-F4-03 (partial):** `bin/ingest status` lists `ops_digests` (0 pts, enabled);
  dry-run + real `sync` on the empty corpus → `files_seen 0, errors [], rc 0`;
  **production counts unchanged** (`homelab_docs 1968`, `knowledge_history 3029`,
  `guardian_cloud 872`, `ensambla2 419`, `infra_audits 280`, `myfreetour 0/disabled`).
- **G-F4-04 (F4.1 portion):** empty-collection retrieval is clean — `bin/ingest search`
  rc 0 / no hits; the tool-path reproduction returns `{"hits": [], "code":
  "empty_collection"}` (D-22, `rag_search.py:177`). The live `webui.db` copy was dumped
  and confirmed to carry the `ops_digests` enum + v0.2.0.
- **Deferred (correct milestone sequencing):** full G-F4-03 (index a real digest +
  idempotency) and the G-F4-04 end-to-end-with-hits → F4.2/F4.3 (need digest content);
  retrieval-fixture entries → F4.3 (framework §9 needs retrievable content);
  date-anchored retrieval **G-F4-05** → F4.3.

## Decisions

- `rag_search` `0.1.0 → 0.2.0` to mark the additive enum change (matches the
  `system_status` v0.2.0 convention). Not a redesign.
- Recorded the new collection in the platform contract §3 inventory (deployed reality;
  framework §11).
- `knowledge_history` remains absent from the enum (R-F4-A); **not** folded in here —
  left to the operator's discretion (architecture §6.5 / §4B Q8).

## Rollback (framework §10; AD-14 isolation)

`enabled: false` in `corpora.yaml` + revert the `rag_search` enum + `bin/install_tool`;
optionally `bin/ingest drop --collection ops_digests --yes` then
`DELETE /collections/ops_digests`. **No production corpus is touched** — `homelab_docs`
and `knowledge_history` are never written to.

## Git gate (STOP — operator approval required before any git command)

Working-tree changes pending review:

- `ai-stack/ingest/conf/corpora.yaml` — `ops_digests` corpus entry
- `ai-stack/openwebui-tools/tools/rag_search.py` — enum + docstring + v0.2.0
- `04_ai_system/knowledge_platform_contract.md` — §3 inventory row
- `09_logs/2026-06-30_phaseF_F4_1_applied.md` — this log
- `04_ai_system/phase_f_architecture.md` — **F4.0 freeze** (prior session, still pending
  the same gate)

Runtime-only (never git): the `ops_digests` Qdrant collection; the `rag_search` row in
`webui.db`.
