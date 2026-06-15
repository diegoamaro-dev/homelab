"""20-question benchmark for `guardian_cloud` with cross-encoder reranking.

Pulls top-N=30 from Qdrant (dense, multilingual-e5-small), then re-ranks
with BAAI/bge-reranker-v2-m3 and returns top-K=6.

Outputs JSON with both pre-rerank (cosine-only) and post-rerank top-6 per
question so a before/after comparison can be done without re-running the
Phase 1 benchmark.
"""
import json, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, '/home/diego/homelab/ai-stack/ingest')

from qdrant_client import QdrantClient

from ingest.config import QDRANT_URL, qdrant_api_key
from ingest.embedder import Embedder
from ingest.reranker import Reranker

# Same 20 questions as the Phase 1 benchmark (gc_benchmark_2026-06-14.py)
QUESTIONS = [
    ("architecture", "en", "What is the high-level architecture of Guardian Cloud's mobile app?", "docs/ARCHITECTURE.md"),
    ("architecture", "es", "¿Cuáles son los estados de protección?", "docs/PROTECTION_MODEL.md"),
    ("architecture", "en", "What are the Guardian Cloud system invariants?", "docs/SYSTEM_INVARIANTS.md"),
    ("architecture", "en", "What is the data flow from the app to final storage?", "docs/ARCHITECTURE.md"),
    ("deployment", "es", "¿Cómo configuro el túnel de Cloudflare para la beta?", "docs/CLOUDFLARE_TUNNEL_SETUP.md"),
    ("deployment", "en", "What are the pre-flight checks for release v0.3?", "docs/RELEASE_CHECKLIST_v0.3.md"),
    ("deployment", "en", "What is the Play Store release plan?", "strategy/PLAYSTORE_RELEASE_PLAN.md"),
    ("deployment", "es", "¿Cuál es el orden de implementación del rollout?", "docs/IMPLEMENTATION_ORDER.md"),
    ("recovery", "en", "How does cross-device recovery work in Guardian Cloud?", "docs/CROSS_DEVICE_RECOVERY.md"),
    ("recovery", "es", "¿Qué pasa si la app es matada durante un upload?", "docs/RECOVERY_BETA_VALIDATION.md"),
    ("recovery", "en", "How do I rebuild the mobile scaffold from scratch?", "REBUILD.md"),
    ("recovery", "en", "What changed in v0.2 for background recovery?", "docs/STATE_v0.2_BACKGROUND_RECOVERY.md"),
    ("chunk-upload", "en", "How are recording chunks uploaded to a NAS over WebDAV?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("chunk-upload", "es", "¿Qué errores y reintentos se manejan en el upload al NAS?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("chunk-upload", "en", "What does the API spec say about chunks?", "docs/API_SPEC.md"),
    ("chunk-upload", "en", "How does evidence export and forensic preservation work?", "docs/EVIDENCE_EXPORT_AND_FORENSIC.md"),
    ("backend", "en", "What backend endpoints does the NAS WebDAV design define?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("backend", "es", "¿Cuál es el modelo de amenazas del backend?", "docs/SECURITY.md"),
    ("backend", "en", "How are chunks secured in transit and at rest?", "docs/SECURITY.md"),
    ("backend", "en", "What anti-patterns should I avoid when extending Guardian Cloud?", "docs/ANTI_PATTERNS.md"),
]

COLL = "guardian_cloud"
DENSE_N = 30
TOP_K = 6


def dense_top_n(client: QdrantClient, vec: list[float], n: int) -> list[dict]:
    """Bypass store.query()'s 400-char truncation — reranker needs full content."""
    res = client.query_points(
        collection_name=COLL, query=vec, limit=n, with_payload=True,
    )
    out = []
    for p in res.points:
        payload = p.payload or {}
        out.append({
            "cosine_score": float(p.score),
            "source_rel":   payload.get("source_rel"),
            "title":        payload.get("title"),
            "chunk_index":  payload.get("chunk_index"),
            "content":      payload.get("content", ""),
        })
    return out


def main():
    client = QdrantClient(url=QDRANT_URL, api_key=qdrant_api_key(), timeout=30.0)
    emb = Embedder()
    rer = Reranker()

    out = []
    for i, (cat, lang, q, expected) in enumerate(QUESTIONS, 1):
        vec = emb.embed_query(q)
        cands = dense_top_n(client, vec, DENSE_N)

        # Pre-rerank top-6 (what Phase 1 saw, recomputed for parity)
        dense_top_k = sorted(cands, key=lambda c: c["cosine_score"], reverse=True)[:TOP_K]

        # Post-rerank top-6 (Phase 1.5)
        rer_top_k = rer.rerank(q, [dict(c) for c in cands], top_k=TOP_K)

        def find_rank(top_list, key="source_rel"):
            for j, c in enumerate(top_list, 1):
                if c[key] == expected:
                    return j
            return None

        out.append({
            "n": i,
            "category": cat,
            "lang": lang,
            "question": q,
            "expected": expected,
            "dense": {
                "top1_source": dense_top_k[0]["source_rel"] if dense_top_k else None,
                "top1_score":  round(dense_top_k[0]["cosine_score"], 4) if dense_top_k else None,
                "expected_rank": find_rank(dense_top_k),
                "top_3_hit": (find_rank(dense_top_k) or 99) <= 3,
                "top_6_hit": (find_rank(dense_top_k) or 99) <= TOP_K,
                "hits": [
                    {"rank": j+1, "source": c["source_rel"], "score": round(c["cosine_score"], 4)}
                    for j, c in enumerate(dense_top_k)
                ],
            },
            "reranked": {
                "top1_source": rer_top_k[0]["source_rel"] if rer_top_k else None,
                "top1_rerank_score":  round(rer_top_k[0]["rerank_score"], 4) if rer_top_k else None,
                "top1_cosine_score":  round(rer_top_k[0]["cosine_score"], 4) if rer_top_k else None,
                "expected_rank": find_rank(rer_top_k),
                "top_3_hit": (find_rank(rer_top_k) or 99) <= 3,
                "top_6_hit": (find_rank(rer_top_k) or 99) <= TOP_K,
                "hits": [
                    {
                        "rank": j+1,
                        "source": c["source_rel"],
                        "rerank_score": round(c["rerank_score"], 4),
                        "cosine_score": round(c["cosine_score"], 4),
                    }
                    for j, c in enumerate(rer_top_k)
                ],
            },
        })

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
