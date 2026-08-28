from __future__ import annotations

import hashlib
import json
from typing import Any

Grid = list[list[int]]


def grid_hash(grid: Grid) -> str:
    payload = ",".join(str(value) for row in grid for value in row).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def spec_key(spec: dict[str, Any]) -> str:
    return json.dumps({"Kind": spec["Kind"], "Level": spec.get("Level"),
                       "Prefix": spec.get("Prefix", [])}, sort_keys=True, separators=(",", ":"))


def make_input(task: dict[str, Any], spec: dict[str, Any]) -> Grid:
    h, w = task["GridHeight"], task["GridWidth"]
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for level, count in enumerate(task["ContextCounts"]):
        for value in range(count):
            grid[h - 1 - level][2 + 4 * level + value] = [6, 7, 9][level]
    shape = task["TestShape"] if spec["Kind"] == "TEST" else (
        task["TrainShape"] if spec["Kind"] == "TRAIN" else task["ProbeShape"])
    top, left = task["TargetTop"], task["TargetLeft"]
    for row, column in shape:
        grid[top + row][left + column] = task["TargetColor"]
    for level, value in enumerate(spec.get("Prefix", [])):
        grid[1 + level][2 + 4 * level + value] = 8
    kind = spec["Kind"]
    if kind == "CALIBRATE":
        grid[0][spec["Level"]] = 9
    elif kind == "DECISION":
        grid[0][w - 1] = 8
    elif kind == "NUISANCE":
        grid[0][w - 1] = 7
    elif kind == "TEST":
        grid[0][w - 1] = 5
    elif kind != "TRAIN":
        raise ValueError(kind)
    return grid


def target_cells(task: dict[str, Any], grid: Grid) -> set[tuple[int, int]]:
    color = task["TargetColor"]
    return {(row, column) for row, values in enumerate(grid)
            for column, value in enumerate(values) if value == color}


def apply_program(task: dict[str, Any], program: dict[str, Any],
                  spec: dict[str, Any]) -> Grid:
    grid = make_input(task, spec)
    output = [row[:] for row in grid]
    kind, prefix = spec["Kind"], spec.get("Prefix", [])
    if kind == "CALIBRATE":
        level = spec["Level"]
        if program["Keys"][:level] == prefix:
            value = program["Keys"][level]
            output[5 + level][2 + 4 * level + value] = [6, 7, 9][level]
        return output
    if kind == "NUISANCE":
        output[8][12 + program["Nuisance"]] = 9
        return output
    transform = kind in {"TRAIN", "TEST"} or (
        kind == "DECISION" and program["Keys"][:len(prefix)] == prefix)
    if not transform:
        return output
    cells = target_cells(task, grid)
    r0, r1 = min(row for row, _ in cells), max(row for row, _ in cells)
    c0, c1 = min(column for _, column in cells), max(column for _, column in cells)
    decision = program["Decision"]
    if decision == 0:
        mapped = cells
    elif decision == 1:
        mapped = {(row, c0 + c1 - column) for row, column in cells}
    elif decision == 2:
        mapped = {(r0 + r1 - row, column) for row, column in cells}
    else:
        raise ValueError("invalid decision")
    for row, column in cells:
        output[row][column] = 0
    for row, column in mapped:
        output[row][column] = task["TargetColor"]
    return output


def all_prefixes(counts: list[int], length: int) -> list[list[int]]:
    rows: list[list[int]] = [[]]
    for count in counts[:length]:
        rows = [prefix + [value] for prefix in rows for value in range(count)]
    return rows


def query_specs(task: dict[str, Any]) -> list[dict[str, Any]]:
    depth = len(task["ContextCounts"])
    disabled = set(task.get("DisabledCalibrationLevels", []))
    specs = [{"Kind": "CALIBRATE", "Level": level, "Prefix": prefix}
             for level in range(depth) if level not in disabled
             for prefix in all_prefixes(task["ContextCounts"], level)]
    specs += [{"Kind": "DECISION", "Level": None, "Prefix": prefix}
              for prefix in all_prefixes(task["ContextCounts"], depth)]
    specs += [{"Kind": "NUISANCE", "Level": None, "Prefix": []}]
    train_hashes = {grid_hash(row["Input"]) for row in task["InitialTrain"]}
    rows = []
    for spec in specs:
        grid = make_input(task, spec)
        digest = grid_hash(grid)
        if digest not in train_hashes:
            rows.append({**spec, "Input": grid, "InputSHA256": digest})
    return sorted(rows, key=lambda row: row["InputSHA256"])


def programs(task: dict[str, Any]) -> list[dict[str, Any]]:
    return [{"Keys": prefix, "Decision": decision, "Nuisance": nuisance}
            for prefix in all_prefixes(task["ContextCounts"], len(task["ContextCounts"]))
            for decision in range(3) for nuisance in range(task["NuisanceCount"])]


def training_exact(task: dict[str, Any], program: dict[str, Any]) -> bool:
    return all(apply_program(task, program, row["Spec"]) == row["Output"]
               for row in task["InitialTrain"])


def models(task: dict[str, Any]) -> list[dict[str, Any]]:
    queries = query_specs(task)
    rows = []
    for program in programs(task):
        if not training_exact(task, program):
            continue
        test_spec = {"Kind": "TEST", "Level": None, "Prefix": []}
        test_output = apply_program(task, program, test_spec)
        rows.append({
            "ModelKey": ":".join(map(str, program["Keys"] + [program["Decision"], program["Nuisance"]])),
            "Program": program, "DecisionLabel": grid_hash(test_output),
            "TestPrediction": test_output,
            "QueryPredictions": {query["InputSHA256"]: apply_program(task, program, query)
                                 for query in queries},
        })
    return rows
