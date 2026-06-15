"""20-question benchmark for the guardian_cloud Qdrant collection."""
import sys, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, '/home/diego/homelab/ai-stack/ingest')

from ingest.store import Store
from ingest.embedder import Embedder

# (category, lang, question, expected_top_source_rel)
QUESTIONS = [
    # ---- Architecture ----
    ("architecture", "en", "What is the high-level architecture of Guardian Cloud's mobile app?", "docs/ARCHITECTURE.md"),
    ("architecture", "es", "¿Cuáles son los estados de protección?", "docs/PROTECTION_MODEL.md"),
    ("architecture", "en", "What are the Guardian Cloud system invariants?", "docs/SYSTEM_INVARIANTS.md"),
    ("architecture", "en", "What is the data flow from the app to final storage?", "docs/ARCHITECTURE.md"),
    # ---- Deployment ----
    ("deployment", "es", "¿Cómo configuro el túnel de Cloudflare para la beta?", "docs/CLOUDFLARE_TUNNEL_SETUP.md"),
    ("deployment", "en", "What are the pre-flight checks for release v0.3?", "docs/RELEASE_CHECKLIST_v0.3.md"),
    ("deployment", "en", "What is the Play Store release plan?", "strategy/PLAYSTORE_RELEASE_PLAN.md"),
    ("deployment", "es", "¿Cuál es el orden de implementación del rollout?", "docs/IMPLEMENTATION_ORDER.md"),
    # ---- Recovery ----
    ("recovery", "en", "How does cross-device recovery work in Guardian Cloud?", "docs/CROSS_DEVICE_RECOVERY.md"),
    ("recovery", "es", "¿Qué pasa si la app es matada durante un upload?", "docs/RECOVERY_BETA_VALIDATION.md"),
    ("recovery", "en", "How do I rebuild the mobile scaffold from scratch?", "REBUILD.md"),
    ("recovery", "en", "What changed in v0.2 for background recovery?", "docs/STATE_v0.2_BACKGROUND_RECOVERY.md"),
    # ---- Chunk upload ----
    ("chunk-upload", "en", "How are recording chunks uploaded to a NAS over WebDAV?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("chunk-upload", "es", "¿Qué errores y reintentos se manejan en el upload al NAS?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("chunk-upload", "en", "What does the API spec say about chunks?", "docs/API_SPEC.md"),
    ("chunk-upload", "en", "How does evidence export and forensic preservation work?", "docs/EVIDENCE_EXPORT_AND_FORENSIC.md"),
    # ---- Backend ----
    ("backend", "en", "What backend endpoints does the NAS WebDAV design define?", "strategy/NAS_WEBDAV_DESIGN.md"),
    ("backend", "es", "¿Cuál es el modelo de amenazas del backend?", "docs/SECURITY.md"),
    ("backend", "en", "How are chunks secured in transit and at rest?", "docs/SECURITY.md"),
    ("backend", "en", "What anti-patterns should I avoid when extending Guardian Cloud?", "docs/ANTI_PATTERNS.md"),
]

K = 6
COLL = "guardian_cloud"

store = Store()
emb = Embedder()
out = []
for i, (cat, lang, q, expected) in enumerate(QUESTIONS, 1):
    vec = emb.embed_query(q)
    hits = store.query(COLL, vec, k=K)
    rank = next((j + 1 for j, h in enumerate(hits) if h["source_rel"] == expected), None)
    top = hits[0] if hits else {"source_rel": None, "score": 0, "title": "", "content": ""}
    out.append({
        "n": i,
        "category": cat,
        "lang": lang,
        "question": q,
        "expected": expected,
        "top1_source": top["source_rel"],
        "top1_score": round(top["score"], 4),
        "top1_title": top.get("title", "")[:60],
        "expected_rank": rank,       # 1..K or None
        "top_3_hit": (rank is not None and rank <= 3),
        "top_6_hit": (rank is not None and rank <= K),
        "hits": [
            {"rank": j + 1, "source": h["source_rel"], "score": round(h["score"], 4)}
            for j, h in enumerate(hits)
        ],
    })

print(json.dumps(out, indent=2, ensure_ascii=False))
