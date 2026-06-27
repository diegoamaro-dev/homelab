#!/usr/bin/env python3
"""E5-a retrieval drift measurement harness (permanent, reusable).

Measures whether the library-version skew between the two AMAROLAB embedding
stacks produces measurable retrieval drift, using the fixed query corpus in
`retrieval_validation_fixture.yaml`.

Design (see 09_logs/2026-06-27_phaseE_E5a_drift_measurement.md):
  - Stored passage vectors are FIXED (embedded under stack A). We never
    re-embed them. The only variable is the QUERY embedding stack.
  - Stack A (this venv): the index/passage stack. Query embeddings computed
    here = the "no-skew baseline" (consistent with the stored passages).
  - Stack B: the openwebui-container query/rerank stack. Its query embeddings
    are produced out-of-band (read-only `docker exec`) and passed in via --qb
    as {id: [floats]}.
  - For each fixture query we compare what stack-A vs stack-B query vectors
    retrieve from the SAME live Qdrant index.

Decisive metric (M2): identity of the dense top-N candidate SET. The
production reranker re-scores (query_text, passage_text) pairs and always runs
in stack B; the query TEXT is identical in both arms, so if the dense top-N
SET is identical the final reranked top-k is provably identical.
Supporting metric (M1): cosine(qA, qB) — the root-cause embedding divergence.

This script performs ONLY read-only Qdrant searches and query-string
embedding. It changes no versions, writes no points, re-embeds nothing.

Usage (run under the ingest venv = stack A):
  python measure_retrieval_drift.py \
      --fixture retrieval_validation_fixture.yaml \
      --qb /path/to/stackB_query_embeddings.json \
      --out /path/to/results.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, "/home/diego/homelab/ai-stack/ingest")
from ingest.config import QDRANT_URL, qdrant_api_key  # noqa: E402
from ingest.embedder import Embedder  # noqa: E402
from qdrant_client import QdrantClient  # noqa: E402


def cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


def search(client: QdrantClient, collection: str, vec: list[float], n: int):
    res = client.query_points(
        collection_name=collection, query=vec, limit=n, with_payload=True,
    )
    return [
        {
            "id": str(p.id),
            "score": float(p.score),
            "source_rel": (p.payload or {}).get("source_rel"),
            "chunk_index": (p.payload or {}).get("chunk_index"),
        }
        for p in res.points
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", required=True)
    ap.add_argument("--qb", required=True, help="stack-B query embeddings JSON {id:[floats]}")
    ap.add_argument("--out", required=True, help="results JSON output path")
    ap.add_argument("--dense-n", type=int, default=30)
    ap.add_argument("--top-k", type=int, default=6)
    ap.add_argument("--cos-threshold", type=float, default=0.9999)
    args = ap.parse_args()

    fixture = yaml.safe_load(Path(args.fixture).read_text())
    queries = fixture["queries"]
    qB = json.loads(Path(args.qb).read_text())

    # Stack-A provenance
    import sentence_transformers, torch  # noqa: E402
    stackA = {"sentence_transformers": sentence_transformers.__version__,
              "torch": torch.__version__}

    emb = Embedder()
    client = QdrantClient(url=QDRANT_URL, api_key=qdrant_api_key(), timeout=30.0)

    per_query = []
    all_set_identical = True
    all_top6_order_identical = True
    all_cos_ok = True
    min_cos = 1.0

    for q in queries:
        qid, coll, text = q["id"], q["collection"], q["query"]
        if qid not in qB:
            print(f"!! missing stack-B embedding for {qid}", file=sys.stderr)
            return 3
        qa = emb.embed_query(text)
        qb = qB[qid]
        cos = cosine(qa, qb)

        A = search(client, coll, qa, args.dense_n)
        B = search(client, coll, qb, args.dense_n)
        a_ids = [h["id"] for h in A]
        b_ids = [h["id"] for h in B]
        set_a, set_b = set(a_ids), set(b_ids)
        inter = set_a & set_b
        union = set_a | set_b
        set_identical = set_a == set_b
        order_identical_n = a_ids == b_ids
        order_identical_k = a_ids[: args.top_k] == b_ids[: args.top_k]
        jaccard = len(inter) / len(union) if union else 1.0
        # max cosine-score delta over shared points
        a_score = {h["id"]: h["score"] for h in A}
        b_score = {h["id"]: h["score"] for h in B}
        max_score_delta = max((abs(a_score[i] - b_score[i]) for i in inter), default=0.0)

        all_set_identical &= set_identical
        all_top6_order_identical &= order_identical_k
        all_cos_ok &= cos >= args.cos_threshold
        min_cos = min(min_cos, cos)

        per_query.append({
            "id": qid, "collection": coll, "lang": q["lang"],
            "cosine_qA_qB": round(cos, 8),
            "topN_set_identical": set_identical,
            "topN_order_identical": order_identical_n,
            "topK_order_identical": order_identical_k,
            "jaccard_topN": round(jaccard, 4),
            "common_of_N": f"{len(inter)}/{args.dense_n}",
            "max_score_delta_shared": round(max_score_delta, 8),
        })

    no_drift = all_set_identical and all_top6_order_identical and all_cos_ok
    conclusion = ("No measurable drift detected — no change required."
                  if no_drift else
                  "MEASURABLE DRIFT DETECTED — see per-query rows; E2-b warranted.")

    results = {
        "fixture_version": fixture.get("version"),
        "dense_n": args.dense_n, "top_k": args.top_k,
        "cos_threshold": args.cos_threshold,
        "stackA_versions": stackA,
        "stackB_versions_note": "captured separately at qB generation time",
        "aggregate": {
            "queries": len(queries),
            "all_topN_set_identical": all_set_identical,
            "all_topK_order_identical": all_top6_order_identical,
            "all_cosine_ge_threshold": all_cos_ok,
            "min_cosine_qA_qB": round(min_cos, 8),
        },
        "decision": conclusion,
        "per_query": per_query,
    }
    Path(args.out).write_text(json.dumps(results, indent=2, ensure_ascii=False))

    # Human-readable report to stdout
    print(f"\nStack A (this venv): {stackA}")
    print(f"Fixture v{fixture.get('version')} — {len(queries)} queries — "
          f"DENSE_N={args.dense_n}, top_k={args.top_k}\n")
    hdr = f"{'id':<7} {'coll':<14} {'cos(qA,qB)':>12} {'setN=':>6} {'ord6=':>6} {'jacc':>6} {'common':>8} {'maxΔscore':>11}"
    print(hdr)
    print("-" * len(hdr))
    for r in per_query:
        print(f"{r['id']:<7} {r['collection']:<14} {r['cosine_qA_qB']:>12.8f} "
              f"{str(r['topN_set_identical']):>6} {str(r['topK_order_identical']):>6} "
              f"{r['jaccard_topN']:>6.3f} {r['common_of_N']:>8} {r['max_score_delta_shared']:>11.2e}")
    agg = results["aggregate"]
    print("\nAGGREGATE:")
    print(f"  all top-{args.dense_n} set identical : {agg['all_topN_set_identical']}")
    print(f"  all top-{args.top_k} order identical : {agg['all_topK_order_identical']}")
    print(f"  all cosine >= {args.cos_threshold}      : {agg['all_cosine_ge_threshold']}")
    print(f"  min cosine(qA,qB)            : {agg['min_cosine_qA_qB']:.8f}")
    print(f"\nCONCLUSION: {conclusion}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
