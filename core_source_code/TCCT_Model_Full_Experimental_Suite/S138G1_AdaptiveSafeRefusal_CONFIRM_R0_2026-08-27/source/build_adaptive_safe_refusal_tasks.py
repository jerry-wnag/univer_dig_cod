from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT / "protocol" / "frozen_protocol.json"
Cell = tuple[int, int]
Shape = tuple[Cell, ...]
Grid = list[list[int]]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(cells: set[Cell]) -> Shape:
    min_row = min(row for row, _ in cells)
    min_column = min(column for _, column in cells)
    return tuple(sorted((row - min_row, column - min_column) for row, column in cells))


def expand(shapes: set[Shape]) -> set[Shape]:
    output: set[Shape] = set()
    for shape in shapes:
        occupied = set(shape)
        frontier = {
            (row + dr, column + dc)
            for row, column in shape
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
        } - occupied
        for cell in frontier:
            output.add(normalize(occupied | {cell}))
    return output


def shape_catalog() -> tuple[Shape, ...]:
    by_area: dict[int, set[Shape]] = {1: {((0, 0),)}}
    for area in range(2, 9):
        by_area[area] = expand(by_area[area - 1])
    return tuple(
        sorted(
            shape
            for area in range(5, 9)
            for shape in by_area[area]
            if max(row for row, _ in shape) < 5
            and max(column for _, column in shape) < 5
        )
    )


def symmetric(shape: Shape, axis: str) -> bool:
    max_row = max(row for row, _ in shape)
    max_column = max(column for _, column in shape)
    if axis == "LEFT_RIGHT":
        reflected = {(row, max_column - column) for row, column in shape}
    elif axis == "TOP_BOTTOM":
        reflected = {(max_row - row, column) for row, column in shape}
    else:
        raise ValueError(axis)
    return set(shape) == reflected


def render(shape: Shape, top: int, left: int, color: int) -> Grid:
    height, width = 14, 15
    grid = [[0 for _ in range(width)] for _ in range(height)]
    occupied: set[Cell] = set()

    def paint(cells: list[Cell], value: int) -> None:
        for row, column in cells:
            if not (0 <= row < height and 0 <= column < width):
                raise ValueError("out of bounds")
            if (row, column) in occupied:
                raise ValueError("collision")
            occupied.add((row, column))
            grid[row][column] = value

    paint([(top + row, left + column) for row, column in shape], color)
    paint([(height - 1, width - 2), (height - 1, width - 1)], color)
    paint([(height - 1, 0), (height - 1, 1)], 6)
    paint([(0, width - 1)], 9)
    return grid


def target_cells(grid: Grid, color: int) -> set[Cell]:
    height, width = len(grid), len(grid[0])
    return {
        (row, column)
        for row in range(height)
        for column in range(width)
        if grid[row][column] == color
    } - {(height - 1, width - 2), (height - 1, width - 1)}


def apply_family(grid: Grid, color: int, family: str) -> Grid:
    output = [row[:] for row in grid]
    cells = target_cells(grid, color)
    r0, r1 = min(row for row, _ in cells), max(row for row, _ in cells)
    c0, c1 = min(column for _, column in cells), max(column for _, column in cells)
    if family == "HIDDEN_IDENTITY":
        mapped = cells
    elif family == "HIDDEN_HORIZONTAL_COMPLEMENT":
        mapped = {(row, c0 + c1 - column) for row, column in cells}
    elif family == "HIDDEN_VERTICAL_COMPLEMENT":
        mapped = {(r0 + r1 - row, column) for row, column in cells}
    else:
        raise ValueError(family)
    for row, column in cells:
        output[row][column] = 0
    for row, column in mapped:
        output[row][column] = color
    return output


OLD_TRAIN_SHAPES: set[Shape] = {
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 0), (2, 2)),
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1), (3, 1)),
}
OLD_TRAIN_SHAPES |= {
    normalize({(column, row) for row, column in shape}) for shape in OLD_TRAIN_SHAPES
}
OLD_TEST_SHAPES: set[Shape] = {
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1), (3, 2)),
    ((0, 1), (1, 1), (1, 2), (2, 0), (2, 1), (3, 0)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2)),
}


def shapes_from_predecessor(path: Path) -> tuple[set[Shape], set[Shape]]:
    predecessor = load_json(path)
    train_shapes: set[Shape] = set()
    test_shapes: set[Shape] = set()
    for task in predecessor["Tasks"]:
        metadata = task["PrivateGeneratorMetadata"]
        train_shapes.update(
            normalize({tuple(cell) for cell in row["Shape"]})
            for row in metadata["NeutralTrainingExamples"]
        )
        test_shapes.add(
            normalize({tuple(cell) for cell in metadata["TestWitnessShape"]})
        )
    return train_shapes, test_shapes


S138F_TRAIN_SHAPES, S138F_TEST_SHAPES = shapes_from_predecessor(
    ROOT / "predecessor_s138f" / "test_outputs_s138f.json"
)
S138G_TRAIN_SHAPES, S138G_TEST_SHAPES = shapes_from_predecessor(
    ROOT / "predecessor_s138g" / "test_outputs_s138g.json"
)
PRIOR_TRAIN_SHAPES = S138F_TRAIN_SHAPES | S138G_TRAIN_SHAPES
PRIOR_TEST_SHAPES = S138F_TEST_SHAPES | S138G_TEST_SHAPES


def valid_placements(shape: Shape) -> list[tuple[int, int]]:
    shape_height = max(row for row, _ in shape) + 1
    shape_width = max(column for _, column in shape) + 1
    return [
        (top, left)
        for top in range(1, 10 - shape_height + 1)
        for left in range(1, 13 - shape_width + 1)
    ]


def build_task(
    rng: random.Random,
    task_id: str,
    axis: str,
    family: str,
    catalog: tuple[Shape, ...],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    excluded_train = OLD_TRAIN_SHAPES | PRIOR_TRAIN_SHAPES
    excluded_test = OLD_TEST_SHAPES | PRIOR_TEST_SHAPES
    train_pool = [
        shape for shape in catalog
        if symmetric(shape, "LEFT_RIGHT")
        and symmetric(shape, "TOP_BOTTOM")
        and shape not in excluded_train
    ]
    test_pool = [
        shape for shape in catalog
        if not symmetric(shape, "LEFT_RIGHT")
        and not symmetric(shape, "TOP_BOTTOM")
        and shape not in excluded_test
    ]
    train_shapes = rng.sample(train_pool, 3)
    test_shape = rng.choice(test_pool)
    colors = rng.sample([1, 2, 3, 4, 5, 7, 8], 4)
    initial_train = []
    metadata = []
    for shape, color in zip(train_shapes, colors[:3]):
        top, left = rng.choice(valid_placements(shape))
        input_grid = render(shape, top, left, color)
        output_grid = apply_family(input_grid, color, family)
        if output_grid != input_grid:
            raise AssertionError("training example is not neutral under its hidden pair")
        initial_train.append({"Input": input_grid, "Output": output_grid})
        metadata.append(
            {"Shape": shape, "Top": top, "Left": left, "Color": color}
        )

    test_top, test_left = rng.choice(valid_placements(test_shape))
    test_color = colors[3]
    test_input = render(test_shape, test_top, test_left, test_color)
    test_output = apply_family(test_input, test_color, family)
    reflection_family = (
        "HIDDEN_HORIZONTAL_COMPLEMENT"
        if axis == "LEFT_RIGHT"
        else "HIDDEN_VERTICAL_COMPLEMENT"
    )
    if apply_family(test_input, test_color, reflection_family) == apply_family(
        test_input, test_color, "HIDDEN_IDENTITY"
    ):
        raise AssertionError("fresh test input does not distinguish its declared pair")

    public = {
        "TaskID": task_id,
        "InitialTrain": initial_train,
        "QueryPool": [],
        "KernelMustSynthesizeInterventions": True,
        "Test": [{"Input": test_input}],
    }
    sealed = {
        "TaskID": task_id,
        "TestOutputs": [{"Output": test_output}],
        "PrivateGeneratorMetadata": {
            "HiddenFamily": family,
            "DifficultyConstructionAxis": axis,
            "NeutralTrainingExamples": metadata,
            "TestWitnessShape": test_shape,
            "TestTop": test_top,
            "TestLeft": test_left,
            "TestColor": test_color,
        },
    }
    oracle = {
        "TaskID": task_id,
        "HiddenFamily": family,
        "ArbitraryValidKernelInterventionsAllowed": True,
    }
    return public, sealed, oracle


def main() -> int:
    protocol = load_json(PROTOCOL_PATH)
    protocol_hash = sha256(PROTOCOL_PATH)
    rng = random.Random(int(protocol["FreshTaskGeneratorSeed"]))
    assignments = [
        ("LEFT_RIGHT", "HIDDEN_HORIZONTAL_COMPLEMENT"),
        ("LEFT_RIGHT", "HIDDEN_HORIZONTAL_COMPLEMENT"),
        ("TOP_BOTTOM", "HIDDEN_VERTICAL_COMPLEMENT"),
        ("TOP_BOTTOM", "HIDDEN_VERTICAL_COMPLEMENT"),
        (rng.choice(("LEFT_RIGHT", "TOP_BOTTOM")), "HIDDEN_IDENTITY"),
    ]
    rng.shuffle(assignments)
    catalog = shape_catalog()
    triples = [
        build_task(rng, task_id, axis, family, catalog)
        for task_id, (axis, family) in zip(protocol["TaskOrder"], assignments)
    ]
    public_tasks = [triple[0] for triple in triples]
    sealed_tasks = [triple[1] for triple in triples]
    oracle_tasks = [triple[2] for triple in triples]
    if [task["TaskID"] for task in public_tasks] != protocol["TaskOrder"]:
        raise AssertionError("task order differs from frozen protocol")
    if any(
        tuple(tuple(cell) for cell in row["PrivateGeneratorMetadata"]["TestWitnessShape"])
        in (OLD_TEST_SHAPES | PRIOR_TEST_SHAPES)
        for row in sealed_tasks
    ):
        raise AssertionError("a prior S138-C/F/G test shape was reused")

    write_json(
        ROOT / "input" / "public_tasks.json",
        {
            "Stage": protocol["Stage"],
            "ProtocolSHA256": protocol_hash,
            "Tasks": public_tasks,
            "LearnerVisibleNamedTransformationPrimitiveCount": 0,
            "LearnerVisibleTestOutputCount": 0,
            "LearnerVisibleGeneratorFamilyCount": 0,
            "PublicQueryPoolSize": 0,
        },
    )
    write_json(
        ROOT / "sealed" / "test_outputs.json",
        {"ProtocolSHA256": protocol_hash, "Tasks": sealed_tasks},
    )
    write_json(
        ROOT / "sealed" / "oracle_responses.json",
        {"ProtocolSHA256": protocol_hash, "Tasks": oracle_tasks},
    )
    write_json(
        ROOT / "sealed" / "materialization_manifest.json",
        {
            "ProtocolSHA256": protocol_hash,
            "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
            "TaskCount": len(public_tasks),
            "CatalogSize": len(catalog),
            "PriorTestShapesExcluded": True,
            "S138FTestShapesExcluded": True,
            "S138GTestShapesExcluded": True,
            "PublicDifficultyAxisCount": 0,
            "PostSeedWorldFilteringUsed": False,
        },
    )
    print(
        json.dumps(
            {
                "BuiltAdaptiveSafeRefusalTasks": len(public_tasks),
                "ProtocolSHA256": protocol_hash,
                "PostSeedWorldFilteringUsed": False,
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
