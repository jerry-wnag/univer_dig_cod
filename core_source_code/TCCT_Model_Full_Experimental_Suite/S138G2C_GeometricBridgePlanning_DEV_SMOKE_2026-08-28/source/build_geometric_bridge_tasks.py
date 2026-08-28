from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from geometry_world import apply_program, make_input


ROOT = Path(__file__).resolve().parents[1]


TRAIN_SHAPES = [
    [[0, 0], [0, 1], [1, 0], [1, 1]],
    [[0, 1], [1, 0], [1, 1], [1, 2], [2, 1]],
    [[0, 0], [0, 1], [0, 2], [1, 0], [1, 1], [1, 2]],
]
TEST_SHAPES = [
    [[0, 0], [1, 0], [2, 0], [2, 1]],
    [[0, 0], [0, 1], [1, 1], [1, 2], [2, 2]],
    [[0, 1], [1, 1], [2, 0], [2, 1], [3, 0]],
    [[0, 0], [0, 1], [1, 0], [2, 0], [2, 1], [2, 2]],
    [[0, 2], [1, 0], [1, 1], [1, 2], [2, 0]],
    [[0, 0], [1, 0], [1, 1], [2, 1], [3, 1]],
    [[0, 0], [0, 1], [0, 2], [1, 2], [2, 1], [2, 2]],
    [[0, 1], [0, 2], [1, 0], [1, 1], [2, 0], [3, 0]],
]


def reflection_signature(shape: list[list[int]], decision: int) -> tuple[tuple[int, int], ...]:
    cells = {tuple(cell) for cell in shape}
    r0, r1 = min(row for row, _ in cells), max(row for row, _ in cells)
    c0, c1 = min(column for _, column in cells), max(column for _, column in cells)
    if decision == 0:
        mapped = cells
    elif decision == 1:
        mapped = {(row, c0 + c1 - column) for row, column in cells}
    else:
        mapped = {(r0 + r1 - row, column) for row, column in cells}
    return tuple(sorted(mapped))


DISCRIMINATING_SHAPES = [shape for shape in TEST_SHAPES
                         if len({reflection_signature(shape, decision) for decision in range(3)}) == 3]
if len(DISCRIMINATING_SHAPES) < 5:
    raise RuntimeError("insufficient decision-separating fresh shapes")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_task(rng: random.Random, task_id: str, role: str,
               test_shape: list[list[int]]) -> tuple[dict, dict, dict]:
    context_count = rng.randint(3, 5)
    nuisance_count = rng.randint(2, 3)
    all_slots = list(range(context_count))
    sealed_slot = rng.choice(all_slots) if role == "GEOMETRIC_IRREDUCIBLE_CONTROL" else None
    instrumented = [slot for slot in all_slots if slot != sealed_slot]
    task = {
        "TaskID": task_id, "GridHeight": 10, "GridWidth": 12,
        "ContextCount": context_count, "NuisanceCount": nuisance_count,
        "InstrumentedContextSlots": instrumented,
        "TrainShape": rng.choice(TRAIN_SHAPES),
        "ProbeShape": rng.choice(DISCRIMINATING_SHAPES),
        "TestShape": test_shape,
        "TargetTop": rng.randint(3, 4), "TargetLeft": rng.randint(4, 6),
        "TargetColor": rng.choice([1, 2, 3, 4]),
    }
    neutral_program = {"Context": 0, "Decision": 0, "Nuisance": 0}
    train_input = make_input(task, "TRAIN")
    train_output = apply_program(task, neutral_program, "TRAIN")
    public = dict(task)
    public.update({
        "InitialTrain": [{"Input": train_input, "Output": train_output}],
        "Test": [{"Input": make_input(task, "TEST")}],
        "KernelMustSynthesizeInterventions": True,
    })
    truth = {"Context": rng.randrange(context_count), "Decision": rng.randrange(3),
             "Nuisance": rng.randrange(nuisance_count)}
    sealed = {
        "TaskID": task_id, "ExpectedRole": role, "HiddenProgram": truth,
        "TestOutputs": [{"Output": apply_program(task, truth, "TEST")}],
        "PrivateGeneratorMetadata": {"UninstrumentedContextSlot": sealed_slot},
    }
    oracle = {"TaskID": task_id, "HiddenProgram": truth}
    return public, sealed, oracle


def main() -> int:
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol, protocol_hash = load(protocol_path), digest(protocol_path)
    rng = random.Random(int(protocol["FreshTaskGeneratorSeed"]))
    roles = ["GEOMETRIC_TWO_STEP_BRIDGE"] * 3 + ["GEOMETRIC_IRREDUCIBLE_CONTROL"] * 2
    rng.shuffle(roles)
    test_shapes = rng.sample(DISCRIMINATING_SHAPES, 5)
    triples = [build_task(rng, task_id, role, shape)
               for task_id, role, shape in zip(protocol["TaskOrder"], roles, test_shapes)]
    write(ROOT / "input" / "public_tasks.json", {
        "Stage": protocol["Stage"], "ProtocolSHA256": protocol_hash,
        "Tasks": [row[0] for row in triples],
        "LearnerVisibleHiddenProgramCount": 0,
        "LearnerVisibleRoleLabelCount": 0,
        "PublicQueryPoolSize": 0,
    })
    write(ROOT / "sealed" / "test_outputs.json", {
        "ProtocolSHA256": protocol_hash, "Tasks": [row[1] for row in triples]})
    write(ROOT / "sealed" / "oracle_responses.json", {
        "ProtocolSHA256": protocol_hash, "Tasks": [row[2] for row in triples]})
    write(ROOT / "sealed" / "materialization_manifest.json", {
        "ProtocolSHA256": protocol_hash, "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
        "TaskCount": 5, "PositiveCount": roles.count("GEOMETRIC_TWO_STEP_BRIDGE"),
        "ControlCount": roles.count("GEOMETRIC_IRREDUCIBLE_CONTROL"),
        "UniqueTestShapes": len({tuple(map(tuple, shape)) for shape in test_shapes}) == 5,
        "PostSeedWorldFilteringUsed": False,
        "WorldReplacementAfterMaterializationUsed": False,
    })
    print(json.dumps({"BuiltFreshGeometricBridgeTasks": 5,
        "ProtocolSHA256": protocol_hash, "PostSeedWorldFilteringUsed": False},
        separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
