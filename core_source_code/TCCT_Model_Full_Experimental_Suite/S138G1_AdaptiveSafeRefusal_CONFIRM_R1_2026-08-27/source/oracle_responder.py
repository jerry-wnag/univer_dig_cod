from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "protocol" / "frozen_protocol.json"
PUBLIC_PATH = ROOT / "input" / "public_tasks.json"
SEALED_ORACLE_PATH = ROOT / "sealed" / "oracle_responses.json"
RESPONSE_PATH = ROOT / "oracle" / "runtime_response.json"
REQUEST_PATH = ROOT / "oracle" / "runtime_request.json"
LOG_PATH = ROOT / "oracle" / "query_log.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protocol_and_boundary() -> tuple[dict[str, Any], str]:
    protocol = load_json(PROTOCOL_PATH)
    protocol_hash = sha256(PROTOCOL_PATH)
    if sha256(Path(__file__)) != protocol["FrozenOracleResponderSHA256"]:
        raise RuntimeError("oracle responder differs from frozen protocol")
    public = load_json(PUBLIC_PATH)
    sealed = load_json(SEALED_ORACLE_PATH)
    if public["ProtocolSHA256"] != protocol_hash:
        raise RuntimeError("public task protocol hash mismatch")
    if sealed["ProtocolSHA256"] != protocol_hash:
        raise RuntimeError("sealed oracle protocol hash mismatch")
    return protocol, protocol_hash


def reset() -> int:
    protocol_and_boundary()
    RESPONSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESPONSE_PATH.write_text("{}\n", encoding="utf-8")
    REQUEST_PATH.write_text("{}\n", encoding="utf-8")
    LOG_PATH.write_text("", encoding="utf-8")
    print(json.dumps({"OracleReset": True}, separators=(",", ":")), flush=True)
    return 0


def existing_log_rows() -> list[dict[str, Any]]:
    if not LOG_PATH.exists():
        return []
    return [json.loads(line) for line in LOG_PATH.read_text(encoding="utf-8").splitlines() if line]


def grid_hash(grid: list[list[int]]) -> str:
    payload = ",".join(str(value) for row in grid for value in row).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def validate_kernel_intervention(
    grid: Any, expected_dimensions: tuple[int, int] | None = None,
) -> tuple[list[list[int]], int]:
    if not isinstance(grid, list) or not grid:
        raise RuntimeError("kernel intervention must be a nonempty rectangular grid")
    height = len(grid)
    if not isinstance(grid[0], list) or not grid[0]:
        raise RuntimeError("kernel intervention must be a nonempty rectangular grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise RuntimeError("kernel intervention must be a rectangular grid")
    protocol = load_json(PROTOCOL_PATH)
    if height not in protocol["GridHeightChoices"] or width not in protocol["GridWidthChoices"]:
        raise RuntimeError("kernel intervention dimensions are outside the frozen stress range")
    if expected_dimensions is not None and (height, width) != expected_dimensions:
        raise RuntimeError("kernel intervention dimensions differ from its observed task")
    normalized = [[int(value) for value in row] for row in grid]
    if any(value < 0 or value > 9 for row in normalized for value in row):
        raise RuntimeError("kernel intervention contains an invalid color")
    if normalized[height - 1][0:2] != [6, 6] or normalized[0][width - 1] != 9:
        raise RuntimeError("kernel intervention violates invariant context markers")
    colors = {
        value for row in normalized for value in row
        if value not in {0, 6, 9}
    }
    if len(colors) != 1:
        raise RuntimeError("kernel intervention must contain exactly one active object color")
    color = next(iter(colors))
    if normalized[height - 1][width - 2:width] != [color, color]:
        raise RuntimeError("kernel intervention violates the same-color context fixture")
    cells = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if normalized[row][column] == color
    } - {(height - 1, width - 2), (height - 1, width - 1)}
    if len(cells) < int(protocol["KernelMinimumSynthesizedObjectArea"]):
        raise RuntimeError("kernel intervention object is too small")
    reached = {next(iter(cells))}
    frontier = list(reached)
    while frontier:
        row, column = frontier.pop()
        for candidate in cells - reached:
            if abs(row - candidate[0]) + abs(column - candidate[1]) == 1:
                reached.add(candidate)
                frontier.append(candidate)
    if reached != cells:
        raise RuntimeError("kernel intervention object is not edge-connected")
    return normalized, color


def target_cells(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    return {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    } - {(height - 1, width - 2), (height - 1, width - 1)}


def apply_family(grid: list[list[int]], color: int, family: str) -> list[list[int]]:
    height, width = len(grid), len(grid[0])
    offset = int(load_json(PROTOCOL_PATH)["ContextTranslationOffset"])
    output = [row[:] for row in grid]
    cells = target_cells(grid, color)
    outside = {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] != 0 and (row, column) not in cells
    }
    r0, r1 = min(row for row, _ in cells), max(row for row, _ in cells)
    c0, c1 = min(column for _, column in cells), max(column for _, column in cells)
    if family == "HIDDEN_IDENTITY":
        mapped = cells
        for row, column in cells:
            output[row][column] = 0
    elif family == "HIDDEN_HORIZONTAL_COMPLEMENT":
        mapped = {(row, c0 + c1 - column) for row, column in cells}
        for row, column in cells:
            output[row][column] = 0
    elif family == "HIDDEN_VERTICAL_COMPLEMENT":
        mapped = {(r0 + r1 - row, column) for row, column in cells}
        for row, column in cells:
            output[row][column] = 0
    elif family == "HIDDEN_CROSS_AXIS_QUARTER_TURN":
        mapped = {(r0 + column - c0, c0 + r1 - row) for row, column in cells}
        for row, column in cells:
            output[row][column] = 0
    elif family == "HIDDEN_UNION_TRANSLATE":
        mapped = {(row + offset, column) for row, column in cells}
    else:
        raise RuntimeError("sealed oracle family is invalid")
    if mapped & outside:
        raise RuntimeError("oracle transformation collides with context")
    if any(not (0 <= row < height and 0 <= column < width) for row, column in mapped):
        raise RuntimeError("oracle transformation is out of bounds")
    for row, column in mapped:
        output[row][column] = color
    return output


def respond(task_id: str, query_id: str) -> int:
    protocol, protocol_hash = protocol_and_boundary()
    if task_id not in protocol["ActiveTaskIDs"]:
        raise RuntimeError("oracle access requested for a non-active task")

    public = load_json(PUBLIC_PATH)
    public_task = next(task for task in public["Tasks"] if task["TaskID"] == task_id)
    if public_task["QueryPool"]:
        raise RuntimeError("public query pool must be empty in S137-B")
    request = load_json(REQUEST_PATH)
    if request.get("ProtocolSHA256") != protocol_hash:
        raise RuntimeError("kernel request protocol hash mismatch")
    if request.get("TaskID") != task_id or request.get("QueryID") != query_id:
        raise RuntimeError("kernel request identity mismatch")
    if request.get("GeneratedByTCCTKernel") is not True:
        raise RuntimeError("oracle accepts only TCCT-kernel-generated interventions")
    observed_grid = public_task["InitialTrain"][0]["Input"]
    expected_dimensions = (len(observed_grid), len(observed_grid[0]))
    grid, color = validate_kernel_intervention(
        request.get("Input"), expected_dimensions=expected_dimensions
    )
    input_sha256 = grid_hash(grid)
    if request.get("InputSHA256") != input_sha256:
        raise RuntimeError("kernel intervention hash mismatch")
    forbidden_hashes = {
        grid_hash(item["Input"])
        for item in public_task["InitialTrain"] + public_task["Test"]
    }
    if input_sha256 in forbidden_hashes:
        raise RuntimeError("kernel intervention duplicates a public train or test input")

    log_rows = existing_log_rows()
    task_rows = [row for row in log_rows if row["TaskID"] == task_id]
    if len(task_rows) >= int(protocol["MaximumActiveQueriesPerTask"]):
        raise RuntimeError("maximum active queries exceeded")
    if any(row["QueryID"] == query_id for row in task_rows):
        raise RuntimeError("duplicate active query")
    if any(row["InputSHA256"] == input_sha256 for row in task_rows):
        raise RuntimeError("duplicate active intervention")
    expected_query_id = f"KQ{len(task_rows) + 1:02d}"
    if query_id != expected_query_id:
        raise RuntimeError("kernel query IDs must be sequential")

    sealed = load_json(SEALED_ORACLE_PATH)
    sealed_task = next(task for task in sealed["Tasks"] if task["TaskID"] == task_id)
    output = apply_family(grid, color, sealed_task["HiddenFamily"])
    payload = {
        "ProtocolSHA256": protocol_hash,
        "TaskID": task_id,
        "QueryID": query_id,
        "Input": grid,
        "InputSHA256": input_sha256,
        "Output": output,
        "GeneratedByTCCTKernel": True,
        "OracleUsedSealedFamily": True,
        "TestOutputAccessed": False,
        "GeneratorFamilyAccessed": False,
    }
    RESPONSE_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({
        "OracleResponseWritten": True,
        "TaskID": task_id,
        "QueryID": query_id,
        "TaskQueryCount": len(task_rows) + 1,
    }, separators=(",", ":")), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--query-id")
    args = parser.parse_args()
    if args.reset:
        if args.task_id or args.query_id:
            raise RuntimeError("reset cannot include a task or query ID")
        return reset()
    if not args.task_id or not args.query_id:
        raise RuntimeError("task ID and query ID are required")
    return respond(args.task_id, args.query_id)


if __name__ == "__main__":
    raise SystemExit(main())
