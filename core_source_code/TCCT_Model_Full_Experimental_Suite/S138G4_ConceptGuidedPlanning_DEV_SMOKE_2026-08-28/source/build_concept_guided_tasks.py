from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from adaptive_geometry import apply_program, make_input

ROOT = Path(__file__).resolve().parents[1]
SYMMETRIC_SHAPES = [
    [[0, 0], [0, 1], [1, 0], [1, 1]],
    [[0, 1], [1, 0], [1, 1], [1, 2], [2, 1]],
]
SHAPE_CANDIDATES = [
    [[0, 0], [1, 0], [2, 0], [2, 1]],
    [[0, 0], [0, 1], [1, 1], [1, 2], [2, 2]],
    [[0, 1], [1, 1], [2, 0], [2, 1], [3, 0]],
    [[0, 2], [1, 0], [1, 1], [1, 2], [2, 0]],
    [[0, 0], [1, 0], [1, 1], [2, 1], [3, 1]],
    [[0, 0], [0, 1], [0, 2], [1, 2], [2, 1], [2, 2]],
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


DISCRIMINATING_SHAPES = [shape for shape in SHAPE_CANDIDATES
                         if len({reflection_signature(shape, decision) for decision in range(3)}) == 3]
if len(DISCRIMINATING_SHAPES) < 5:
    raise RuntimeError("insufficient three-way decision-separating shapes")
CONTEXT_PATTERNS = [[2, 2, 2], [2, 3, 2], [3, 2, 2], [2, 2, 3], [3, 2, 3]]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_task(rng: random.Random, task_id: str, role: str, shape: list[list[int]],
               counts: list[int]) -> tuple[dict, dict, dict]:
    expected = {"CONCEPT_TRANSFER_DEPTH1": 1, "CONCEPT_TRANSFER_DEPTH2": 2,
                "CONCEPT_TRANSFER_DEPTH3": 3, "CONCEPT_MISMATCH_FALLBACK_DEPTH2": 2,
                "DEPTH4_BUDGET_CONTROL": 4}[role]
    if role == "CONCEPT_MISMATCH_FALLBACK_DEPTH2":
        counts = [counts[0], counts[1], 2]
    task = {
        "TaskID": task_id, "GridHeight": 12, "GridWidth": 16,
        "ContextCounts": counts, "NuisanceCount": 2,
        "DisabledCalibrationLevels": [2] if role == "CONCEPT_MISMATCH_FALLBACK_DEPTH2" else [],
        "TrainShape": rng.choice(SYMMETRIC_SHAPES), "ProbeShape": rng.choice(DISCRIMINATING_SHAPES),
        "TestShape": shape, "TargetTop": rng.randint(3, 4), "TargetLeft": rng.randint(5, 7),
        "TargetColor": rng.choice([1, 2, 3, 4]), "KernelMustSynthesizeInterventions": True,
        "MaximumPlanningDepthVisibleAsResourceCapOnly": 3,
    }
    hidden = {"Keys": [rng.randrange(count) for count in counts],
              "Decision": rng.randrange(3), "Nuisance": rng.randrange(2)}
    known_keys = max(0, 4 - expected)
    train_spec = {"Kind": "TRAIN", "Level": None, "Prefix": []}
    initial = [{"Spec": train_spec, "Input": make_input(task, train_spec),
                "Output": apply_program(task, hidden, train_spec)}]
    for level in range(known_keys):
        spec = {"Kind": "CALIBRATE", "Level": level, "Prefix": hidden["Keys"][:level]}
        initial.append({"Spec": spec, "Input": make_input(task, spec),
                        "Output": apply_program(task, hidden, spec)})
    public = dict(task)
    public.update({"InitialTrain": initial,
                   "Test": [{"Input": make_input(task, {"Kind": "TEST", "Level": None, "Prefix": []})}]})
    sealed = {"TaskID": task_id, "ExpectedRole": role,
              "ExpectedMinimumGuaranteedDepth": expected, "HiddenProgram": hidden,
              "TestOutputs": [{"Output": apply_program(task, hidden,
                  {"Kind": "TEST", "Level": None, "Prefix": []})}]}
    return public, sealed, {"TaskID": task_id, "HiddenProgram": hidden}


def main() -> int:
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol, protocol_hash = load(protocol_path), digest(protocol_path)
    rng = random.Random(int(protocol["FreshTaskGeneratorSeed"]))
    roles = ["CONCEPT_TRANSFER_DEPTH1", "CONCEPT_TRANSFER_DEPTH2", "CONCEPT_TRANSFER_DEPTH3",
             "CONCEPT_MISMATCH_FALLBACK_DEPTH2", "DEPTH4_BUDGET_CONTROL"]
    rng.shuffle(roles)
    shapes = rng.sample(DISCRIMINATING_SHAPES, 5)
    patterns = rng.sample(CONTEXT_PATTERNS, 5)
    triples = [build_task(rng, task_id, role, shape, counts)
               for task_id, role, shape, counts in zip(protocol["TaskOrder"], roles, shapes, patterns)]
    write(ROOT / "input" / "public_tasks.json", {"Stage": protocol["Stage"],
        "ProtocolSHA256": protocol_hash, "Tasks": [row[0] for row in triples],
        "PublicQueryPoolSize": 0, "LearnerVisibleRoleLabelCount": 0,
        "LearnerVisibleRequiredDepthCount": 0, "LearnerVisibleHiddenProgramCount": 0})
    write(ROOT / "sealed" / "test_outputs.json", {"ProtocolSHA256": protocol_hash,
        "Tasks": [row[1] for row in triples]})
    write(ROOT / "sealed" / "oracle_responses.json", {"ProtocolSHA256": protocol_hash,
        "Tasks": [row[2] for row in triples]})
    write(ROOT / "sealed" / "materialization_manifest.json", {
        "ProtocolSHA256": protocol_hash, "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
        "RoleMultiset": sorted(roles), "UniqueTestShapes": True,
        "PostSeedWorldFilteringUsed": False, "WorldReplacementAfterMaterializationUsed": False})
    print(json.dumps({"BuiltFreshConceptGuidedTasks": 5, "ProtocolSHA256": protocol_hash,
                      "PostSeedWorldFilteringUsed": False}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
