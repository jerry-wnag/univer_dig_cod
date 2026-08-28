from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from source.build_adaptive_safe_refusal_tasks import (
    apply_family,
    load_json,
    target_cells,
    write_json,
)


Cell = tuple[int, int]
Grid = list[list[int]]


def normalize(cells: set[Cell]) -> tuple[Cell, ...]:
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def expand(shapes: set[tuple[Cell, ...]]) -> set[tuple[Cell, ...]]:
    output: set[tuple[Cell, ...]] = set()
    for shape in shapes:
        shape_set = set(shape)
        frontier = {
            (row + dr, column + dc)
            for row, column in shape
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        } - shape_set
        for cell in frontier:
            output.add(normalize(shape_set | {cell}))
    return output


def shapes() -> tuple[tuple[Cell, ...], ...]:
    by_area: dict[int, set[tuple[Cell, ...]]] = {1: {((0, 0),)}}
    for area in range(2, 8):
        by_area[area] = expand(by_area[area - 1])
    return tuple(
        sorted(
            shape
            for area in range(4, 8)
            for shape in by_area[area]
            if max(row for row, _ in shape) < 4
            and max(column for _, column in shape) < 4
        )
    )


def grid_hash(grid: Grid) -> str:
    payload = ",".join(str(value) for row in grid for value in row).encode("ascii")
    return hashlib.sha256(payload).hexdigest()


def symmetric(shape: tuple[Cell, ...], axis: str) -> bool:
    max_row = max(row for row, _ in shape)
    max_column = max(column for _, column in shape)
    if axis == "LEFT_RIGHT":
        reflected = {(row, max_column - column) for row, column in shape}
    elif axis == "TOP_BOTTOM":
        reflected = {(max_row - row, column) for row, column in shape}
    else:
        raise ValueError(axis)
    return set(shape) == reflected


def scaffold(task: dict[str, Any]) -> tuple[Grid, int]:
    grid = [row[:] for row in task["InitialTrain"][0]["Input"]]
    height, width = len(grid), len(grid[0])
    color = grid[height - 1][width - 1]
    for row, column in target_cells(grid, color):
        grid[row][column] = 0
    if grid[height - 1][width - 2:] != [color, color]:
        raise AssertionError("same-color fixture missing")
    return grid, color


def universe(task: dict[str, Any], protocol: dict[str, Any]) -> list[dict[str, Any]]:
    base, color = scaffold(task)
    height, width = len(base), len(base[0])
    forbidden = {
        grid_hash(row["Input"])
        for row in task["InitialTrain"] + task["Test"]
    }
    rows = []
    for shape in shapes():
        shape_height = max(row for row, _ in shape) + 1
        shape_width = max(column for _, column in shape) + 1
        envelope = max(shape_height, shape_width)
        maximum_top = height - envelope - protocol["ContextTranslationOffset"]
        maximum_left = width - envelope - 1
        for top in range(maximum_top):
            for left in range(maximum_left):
                cells = [(top + row, left + column) for row, column in shape]
                if any(base[row][column] != 0 for row, column in cells):
                    continue
                grid = [row[:] for row in base]
                for row, column in cells:
                    grid[row][column] = color
                digest = grid_hash(grid)
                if digest not in forbidden:
                    rows.append(
                        {
                            "Input": grid,
                            "InputSHA256": digest,
                            "Shape": shape,
                            "HorizontalSymmetric": symmetric(shape, "LEFT_RIGHT"),
                            "VerticalSymmetric": symmetric(shape, "TOP_BOTTOM"),
                        }
                    )
    double_neutral = sorted(
        (
            row for row in rows
            if row["HorizontalSymmetric"] and row["VerticalSymmetric"]
        ),
        key=lambda row: row["InputSHA256"],
    )
    double_neutral_quota = protocol["SupportTrapDoubleNeutralQuota"]
    if len(double_neutral) < double_neutral_quota:
        raise AssertionError(
            "insufficient support-trap construction capacity: "
            f"double={len(double_neutral)}"
        )
    return double_neutral[:double_neutral_quota]


def main() -> int:
    protocol = load_json(ROOT / "protocol" / "frozen_protocol.json")
    public = load_json(ROOT / "input" / "public_tasks.json")
    audits = []
    for task in public["Tasks"]:
        rows = universe(task, protocol)
        indistinguishable_count = 0
        for row in rows:
            grid = row["Input"]
            color = grid[-1][-1]
            identity_output = apply_family(grid, color, "HIDDEN_IDENTITY")
            horizontal_output = apply_family(
                grid, color, "HIDDEN_HORIZONTAL_COMPLEMENT"
            )
            vertical_output = apply_family(
                grid, color, "HIDDEN_VERTICAL_COMPLEMENT"
            )
            if identity_output == horizontal_output == vertical_output:
                indistinguishable_count += 1
        test_grid = task["Test"][0]["Input"]
        test_color = test_grid[-1][-1]
        test_predictions = [
            apply_family(test_grid, test_color, family)
            for family in (
                "HIDDEN_IDENTITY",
                "HIDDEN_HORIZONTAL_COMPLEMENT",
                "HIDDEN_VERTICAL_COMPLEMENT",
            )
        ]
        distinct_test_prediction_count = len(
            {json.dumps(value, separators=(",", ":")) for value in test_predictions}
        )
        unique_count = len({row["InputSHA256"] for row in rows})
        expected_total = protocol["SupportTrapDoubleNeutralQuota"]
        pass_flag = all(
            [
                len(rows) == expected_total,
                unique_count == expected_total,
                "DifficultyConstructionAxis" not in task,
                indistinguishable_count == expected_total,
                distinct_test_prediction_count == 3,
            ]
        )
        audits.append(
            {
                "TaskID": task["TaskID"],
                "PublicAxisPresent": "DifficultyConstructionAxis" in task,
                "InterventionUniverseCount": len(rows),
                "UniqueInterventionCount": unique_count,
                "IdentityHorizontalVerticalIndistinguishableInputCount":
                    indistinguishable_count,
                "InformativeAllowedInterventionCount":
                    len(rows) - indistinguishable_count,
                "DistinctTestPredictionCountAcrossStructuralTrio":
                    distinct_test_prediction_count,
                "PoolSHA256": hashlib.sha256(
                    "\n".join(row["InputSHA256"] for row in rows).encode("ascii")
                ).hexdigest(),
                "DifficultyConstructionPass": pass_flag,
            }
        )
    overall = all(row["DifficultyConstructionPass"] for row in audits)
    certificate = {
        "Stage": protocol["Stage"],
        "CertificateType": "EXHAUSTIVE_SYMMETRY_PRESERVING_SUPPORT_TRAP",
        "ModelCandidatesUsedToConstructPool": False,
        "PostSeedWorldFilteringUsed": False,
        "TaskCount": len(audits),
        "AllFiveStructuralTriosIndistinguishableOnAllowedInterventions": overall
        and all(row["InformativeAllowedInterventionCount"] == 0 for row in audits),
        "AllFiveTestsHaveThreeDistinctStructuralPredictions": overall
        and all(
            row["DistinctTestPredictionCountAcrossStructuralTrio"] == 3
            for row in audits
        ),
        "AllPublicDifficultyAxesAbsent": all(
            not row["PublicAxisPresent"] for row in audits
        ),
        "DifficultyCertificatePass": overall,
        "TaskAudits": audits,
    }
    write_json(ROOT / "diagnostic" / "difficulty_certificate.json", certificate)
    print(json.dumps(certificate, separators=(",", ":")))
    return 0 if all(
        [
            certificate[
                "AllFiveStructuralTriosIndistinguishableOnAllowedInterventions"
            ],
            certificate["AllFiveTestsHaveThreeDistinctStructuralPredictions"],
            certificate["AllPublicDifficultyAxesAbsent"],
        ]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
