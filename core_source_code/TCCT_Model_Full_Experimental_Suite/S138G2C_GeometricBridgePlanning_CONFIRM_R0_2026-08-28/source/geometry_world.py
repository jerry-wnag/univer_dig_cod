from __future__ import annotations

import hashlib
from typing import Any


Grid = list[list[int]]


def grid_hash(grid: Grid) -> str:
    payload = ",".join(str(value) for row in grid for value in row).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def make_input(task: dict[str, Any], kind: str, slot: int | None = None) -> Grid:
    height, width = task["GridHeight"], task["GridWidth"]
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for context in range(task["ContextCount"]):
        grid[height - 1][2 + context] = 6
    shape = task["TestShape"] if kind == "TEST" else (
        task["TrainShape"] if kind == "TRAIN" else task["ProbeShape"]
    )
    top, left = task["TargetTop"], task["TargetLeft"]
    for row, column in shape:
        grid[top + row][left + column] = task["TargetColor"]
    if kind == "CALIBRATION":
        grid[0][0] = 9
    elif kind == "DECISION":
        if slot is None or slot not in task["InstrumentedContextSlots"]:
            raise ValueError("invalid decision-probe slot")
        grid[0][2 + slot] = 8
    elif kind == "NUISANCE":
        grid[0][width - 1] = 7
    elif kind == "TEST":
        grid[0][width - 1] = 5
    elif kind != "TRAIN":
        raise ValueError(kind)
    return grid


def target_cells(task: dict[str, Any], grid: Grid) -> set[tuple[int, int]]:
    color = task["TargetColor"]
    return {(row, column) for row, values in enumerate(grid)
            for column, value in enumerate(values) if value == color}


def apply_program(task: dict[str, Any], program: dict[str, int], kind: str,
                  slot: int | None = None) -> Grid:
    grid = make_input(task, kind, slot)
    output = [row[:] for row in grid]
    if kind == "CALIBRATION":
        output[1][2 + program["Context"]] = 6
        return output
    if kind == "NUISANCE":
        output[1][8 + program["Nuisance"]] = 6
        return output
    should_transform = kind in {"TRAIN", "TEST"} or (
        kind == "DECISION" and slot == program["Context"]
    )
    if not should_transform:
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
    color = task["TargetColor"]
    for row, column in cells:
        output[row][column] = 0
    for row, column in mapped:
        output[row][column] = color
    return output


def queries(task: dict[str, Any]) -> list[dict[str, Any]]:
    specs: list[tuple[str, int | None]] = [("CALIBRATION", None)]
    specs += [("DECISION", slot) for slot in task["InstrumentedContextSlots"]]
    specs += [("NUISANCE", None)]
    rows = []
    for kind, slot in specs:
        grid = make_input(task, kind, slot)
        rows.append({"Kind": kind, "Slot": slot, "Input": grid,
                     "InputSHA256": grid_hash(grid)})
    return sorted(rows, key=lambda row: row["InputSHA256"])


def programs(task: dict[str, Any]) -> list[dict[str, int]]:
    return [{"Context": context, "Decision": decision, "Nuisance": nuisance}
            for context in range(task["ContextCount"])
            for decision in range(3)
            for nuisance in range(task["NuisanceCount"])]


def models(task: dict[str, Any]) -> list[dict[str, Any]]:
    query_rows = queries(task)
    rows = []
    for program in programs(task):
        test_output = apply_program(task, program, "TEST")
        rows.append({
            "Program": program,
            "DecisionLabel": grid_hash(test_output),
            "TestPrediction": test_output,
            "QueryPredictions": {
                query["InputSHA256"]: apply_program(
                    task, program, query["Kind"], query["Slot"]
                ) for query in query_rows
            },
        })
    return rows
