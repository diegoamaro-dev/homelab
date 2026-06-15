"""homelab-rag-ingest CLI entry point.

Subcommands:
    sync   [--collection X] [--dry-run]   ingest one or all corpora
    status                                 per-collection point counts
    search --collection X --query Y [--k N]
    drop   --collection X --yes            delete all points for a collection
    init                                   no-op (collections pre-created)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import asdict

from . import config as cfg
from .embedder import Embedder
from .pipeline import sync_corpus
from .store import Store


def _print_report(rep) -> None:
    d = asdict(rep)
    print(json.dumps(d, indent=2, ensure_ascii=False))


def cmd_sync(args) -> int:
    ic = cfg.load_corpora()
    selected = [c for c in ic.corpora if (not args.collection or c.name == args.collection)]
    if not selected:
        print(f"no corpus named '{args.collection}'", file=sys.stderr)
        return 2

    store = Store()
    embedder = Embedder() if not args.dry_run else None

    rc = 0
    for corpus in selected:
        print(f"\n=== {corpus.name} ({'dry-run' if args.dry_run else 'sync'}) ===")
        t0 = time.time()
        if args.dry_run:
            # Need a stub embedder so pipeline can run without downloading the model
            class _Stub:
                def embed_passages(self, ts): return [[0.0]*cfg.EMBED_DIM for _ in ts]
            rep = sync_corpus(corpus, _Stub(), store, dry_run=True)
        else:
            rep = sync_corpus(corpus, embedder, store, dry_run=False)
        rep_dict = asdict(rep)
        rep_dict["elapsed_seconds"] = round(time.time() - t0, 2)
        print(json.dumps(rep_dict, indent=2, ensure_ascii=False))
        if rep.errors:
            rc = 1
    return rc


def cmd_status(_args) -> int:
    ic = cfg.load_corpora()
    store = Store()
    print(f"{'collection':<24} {'points':>10}  {'enabled':>8}")
    print("-" * 48)
    for c in ic.corpora:
        try:
            n = store.count(c.name)
        except Exception as e:  # noqa
            n = -1
        print(f"{c.name:<24} {n:>10}  {str(c.enabled):>8}")
    return 0


def cmd_search(args) -> int:
    store = Store()
    embedder = Embedder()
    vec = embedder.embed_query(args.query)
    hits = store.query(args.collection, vec, k=args.k)
    for i, h in enumerate(hits, 1):
        print(f"\n[{i}] score={h['score']:.4f}  {h['source_rel']} (chunk {h['chunk_index']})")
        if h.get("title"):
            print(f"     title: {h['title']}")
        print(f"     {h['content'][:240]}{'…' if len(h['content']) > 240 else ''}")
    return 0


def cmd_drop(args) -> int:
    if not args.yes:
        print("refusing — pass --yes to confirm", file=sys.stderr)
        return 2
    store = Store()
    n = store.delete_collection_data(args.collection)
    print(f"deleted {n} points from {args.collection}")
    return 0


def cmd_init(_args) -> int:
    print("collections are pre-created via Phase 1 / P1.2 (see audit docs).")
    print("Nothing to do.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="homelab-rag-ingest")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("sync", help="ingest one or all corpora")
    s.add_argument("--collection", help="restrict to a single corpus name")
    s.add_argument("--dry-run", action="store_true",
                   help="walk + chunk but do not embed or upsert")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("status", help="per-collection point counts")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("search", help="query a collection")
    s.add_argument("--collection", required=True)
    s.add_argument("--query", required=True)
    s.add_argument("--k", type=int, default=6)
    s.set_defaults(func=cmd_search)

    s = sub.add_parser("drop", help="delete all points for a collection")
    s.add_argument("--collection", required=True)
    s.add_argument("--yes", action="store_true")
    s.set_defaults(func=cmd_drop)

    s = sub.add_parser("init", help="(no-op) collections are pre-created")
    s.set_defaults(func=cmd_init)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg.load_env_file()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
