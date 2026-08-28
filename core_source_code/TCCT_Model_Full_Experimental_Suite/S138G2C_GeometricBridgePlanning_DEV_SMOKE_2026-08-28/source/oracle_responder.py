from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from geometry_world import apply_program, queries


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol" / "frozen_protocol.json"
PUBLIC = ROOT / "input" / "public_tasks.json"
SEALED = ROOT / "sealed" / "oracle_responses.json"
REQUEST = ROOT / "oracle" / "runtime_request.json"
RESPONSE = ROOT / "oracle" / "runtime_response.json"
LOG = ROOT / "oracle" / "query_log.jsonl"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary() -> tuple[dict, dict, dict, str]:
    protocol, public, sealed = load(PROTOCOL), load(PUBLIC), load(SEALED)
    protocol_hash = digest(PROTOCOL)
    if digest(Path(__file__)) != protocol["FrozenOracleResponderSHA256"]:
        raise RuntimeError("oracle source differs from frozen protocol")
    if public["ProtocolSHA256"] != protocol_hash or sealed["ProtocolSHA256"] != protocol_hash:
        raise RuntimeError("oracle protocol boundary mismatch")
    return protocol, public, sealed, protocol_hash


def reset() -> int:
    boundary()
    RESPONSE.parent.mkdir(parents=True, exist_ok=True)
    RESPONSE.write_text("{}\n", encoding="utf-8")
    REQUEST.write_text("{}\n", encoding="utf-8")
    LOG.write_text("", encoding="utf-8")
    print('{"OracleReset":true}', flush=True)
    return 0


def respond(task_id: str, query_number: str) -> int:
    protocol, public, sealed, protocol_hash = boundary()
    request = load(REQUEST)
    if request.get("ProtocolSHA256") != protocol_hash or request.get("TaskID") != task_id or request.get("QueryNumber") != query_number:
        raise RuntimeError("request boundary mismatch")
    if request.get("GeneratedByTCCTKernel") is not True:
        raise RuntimeError("query was not kernel generated")
    task = next(row for row in public["Tasks"] if row["TaskID"] == task_id)
    query = next((row for row in queries(task) if row["InputSHA256"] == request.get("InputSHA256")), None)
    if query is None or query["Input"] != request.get("Input"):
        raise RuntimeError("input is outside the synthesized intervention grammar")
    log_rows = [json.loads(line) for line in LOG.read_text(encoding="utf-8").splitlines() if line] if LOG.exists() else []
    task_rows = [row for row in log_rows if row["TaskID"] == task_id]
    if query_number != f"KQ{len(task_rows) + 1:02d}" or any(row["InputSHA256"] == query["InputSHA256"] for row in task_rows):
        raise RuntimeError("invalid query sequence")
    hidden = next(row for row in sealed["Tasks"] if row["TaskID"] == task_id)["HiddenProgram"]
    output = apply_program(task, hidden, query["Kind"], query["Slot"])
    payload = {
        "ProtocolSHA256": protocol_hash, "TaskID": task_id,
        "QueryNumber": query_number, "Input": query["Input"],
        "InputSHA256": query["InputSHA256"], "Output": output,
        "GeneratedByTCCTKernel": True, "TestOutputAccessed": False,
        "HiddenProgramAccessedByLearner": False,
    }
    RESPONSE.write_text(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    with LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"OracleResponseWritten": True, "TaskID": task_id,
        "QueryNumber": query_number, "TaskQueryCount": len(task_rows) + 1},
        separators=(",", ":")), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--query-id")
    args = parser.parse_args()
    if args.reset:
        return reset()
    if not args.task_id or not args.query_id:
        raise RuntimeError("task and query IDs required")
    return respond(args.task_id, args.query_id)


if __name__ == "__main__":
    raise SystemExit(main())
