"""Command line adapter for the local attention selector."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .core import SelectionPolicy
from .evaluation import ndcg_at_k
from .local_model import LocalModelCaller
from .service import AttentionSelectorService, JsonReceiptWriter, LocalStoreReader
from .store import ChunkStore, ingest_files


DEFAULT_STORE = Path.home() / ".local" / "share" / "lab-attention-selector" / "chunks"


class EmptyCorpusReader:
    def read_chunks(self):
        return ()


def _receipt(value: dict) -> None:
    sys.stdout.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _write_private(path: Path, value: bytes) -> None:
    target = path.expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[1]
    if target == repo_root or repo_root in target.parents:
        raise ValueError("package output must be outside the repository")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target.parent, 0o700)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(value)
        stream.flush()
        os.fsync(stream.fileno())


def _policy(args: argparse.Namespace) -> SelectionPolicy:
    return SelectionPolicy(args.max_chunks, args.max_chunk_bytes, args.max_total_bytes,
                           args.idf_scale, args.policy_version, tuple(args.exclude_source_id))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lab-attention-selector")
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    commands = parser.add_subparsers(dest="command", required=True)

    ingest = commands.add_parser("ingest")
    ingest.add_argument("source", type=Path)
    ingest.add_argument("--max-chunk-bytes", type=int, required=True)
    ingest.add_argument("--captured-at", required=True)

    for name in ("package", "rank"):
        command = commands.add_parser(name)
        command.add_argument("--max-chunks", type=int, required=True)
        command.add_argument("--max-chunk-bytes", type=int, required=True)
        command.add_argument("--max-total-bytes", type=int, required=True)
        command.add_argument("--idf-scale", type=int, default=1024)
        command.add_argument("--policy-version", default="lexical-v1")
        command.add_argument("--exclude-source-id", action="append", default=[])
        command.add_argument("--query-stdin", action="store_true", required=True)
        if name == "package":
            command.add_argument("--index-budget-bytes", type=int, required=True)
            command.add_argument("--chunk-budget-bytes", type=int, required=True)
            command.add_argument("--output-dir", type=Path, required=True)

    explain = commands.add_parser("explain")
    explain.add_argument("--equation")
    explain.add_argument("--cause")
    explain.add_argument("--host", default="127.0.0.1")
    explain.add_argument("--port", type=int, default=11434)
    explain.add_argument("--seed", type=int, default=0)
    explain.add_argument("--model", default=os.environ.get("LAB_SELECTOR_LOCAL_MODEL", ""))

    evaluate = commands.add_parser("ndcg")
    evaluate.add_argument("--ranked-ids", type=Path, required=True)
    evaluate.add_argument("--gold", type=Path)
    evaluate.add_argument("--k", type=int)
    return parser


def run(args: argparse.Namespace) -> int:
    if args.command == "ingest":
        store = ChunkStore(args.store)
        result = ingest_files(args.source, store, max_chunk_bytes=args.max_chunk_bytes,
                              captured_at=args.captured_at)
        success = bool(result.appended or result.duplicates)
        causes = sorted({cause for _, cause in result.rejected})
        _receipt({"status": "VERBATIM" if success else "NO_DATA",
                  "cause": None if success else "; ".join(causes) or "source contains no non-empty UTF-8 chunks",
                  "appended": len(result.appended), "duplicates": result.duplicates,
                  "rejected_count": len(result.rejected), "causes": causes})
        return 0
    if args.command in {"package", "rank"}:
        query = sys.stdin.read() if args.query_stdin else ""
        policy = _policy(args)
        service = AttentionSelectorService(LocalStoreReader(ChunkStore(args.store)), JsonReceiptWriter(), policy)
        if args.command == "rank":
            result = service.rank(query)
            return 0 if result.status == "VERBATIM" else 2
        package = service.package(query, index_budget_bytes=args.index_budget_bytes,
                                  chunk_budget_bytes=args.chunk_budget_bytes)
        if not package.pass1_bytes or not package.pass2_bytes:
            return 2
        output = args.output_dir.expanduser()
        output.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(output, 0o700)
        _write_private(output / "pass-1-index.json", package.pass1_bytes)
        _write_private(output / "pass-2-verbatim.json", package.pass2_bytes)
        return 0 if package.status == "VERBATIM" else 2
    if args.command == "explain":
        if not args.model or not args.equation or not args.cause:
            _receipt({"status": "NO_DATA", "cause": "model, equation, or cause is absent"})
            return 2
        try:
            writer = JsonReceiptWriter()
            service = AttentionSelectorService(EmptyCorpusReader(), writer,
                                               SelectionPolicy(1, 1),
                                               LocalModelCaller(args.host, args.port, args.model, seed=args.seed))
            text = service.explain(args.equation, args.cause)
        except (RuntimeError, ValueError) as exc:
            _receipt({"status": "NO_DATA", "cause": str(exc)})
            return 2
        sys.stdout.write(text + ("\n" if not text.endswith("\n") else ""))
        return 0
    if args.command == "ndcg":
        ranked = json.loads(args.ranked_ids.read_text(encoding="utf-8"))
        gold = json.loads(args.gold.read_text(encoding="utf-8")) if args.gold else None
        result = ndcg_at_k(ranked, gold, args.k)
        _receipt(result)
        return 0 if result["status"] == "MEASURED" else 2
    return 2


def main() -> int:
    try:
        return run(build_parser().parse_args())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        _receipt({"status": "NO_DATA", "cause": type(exc).__name__})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
