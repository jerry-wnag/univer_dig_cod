from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

from adaptive_geometry import apply_program, make_input, query_specs, target_cells

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
    [[0, 1], [1, 0], [1, 1], [2, 1], [2, 2], [3, 2]],
    [[0, 0], [0, 1], [1, 0], [2, 0], [2, 1], [3, 1]],
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

FAMILY_CONFIGS = {
    "MIXED_PREFIX": {
        "Sources": [
            ("SRC001", [2, 3, 2], 1, 3, "SOURCE_DEPTH3"),
            ("SRC002", [3, 2, 2], 2, 2, "SOURCE_DEPTH2"),
            ("SRC003", [2, 2, 3], 3, 1, "SOURCE_DEPTH1"),
        ],
        "Targets": [
            ("KT001", [2, 3, 2], 3, 1, "SURFACE_PERMUTATION_TRANSFER", [], False, False),
            ("KT002", [2, 2, 2, 2], 3, 2, "COORDINATE_SCALE_TRANSFER", [], False, False),
            ("KT003", [3, 2, 3], 1, 3, "SEQUENTIAL_CONCEPT_COMPOSITION", [], False, False),
            ("KT004", [2, 2], 0, 2, "ADVERSARIAL_CONCEPT_REJECTION", [], False, True),
            ("KT005", [2], 0, 2, "NO_REUSABLE_CONCEPT_FALLBACK", [0], False, False),
        ],
    },
    "HIGH_PREFIX": {
        "Sources": [
            ("SRC001", [2, 2, 2, 2], 2, 3, "SOURCE_DEPTH3"),
            ("SRC002", [2, 3, 2, 2], 3, 2, "SOURCE_DEPTH2"),
            ("SRC003", [3, 2, 2], 3, 1, "SOURCE_DEPTH1"),
        ],
        "Targets": [
            ("KT001", [2, 2, 3], 3, 1, "SURFACE_PERMUTATION_TRANSFER", [], False, False),
            ("KT002", [2, 3, 2, 2], 3, 2, "COORDINATE_SCALE_TRANSFER", [], False, False),
            ("KT003", [2, 2, 2, 3], 2, 3, "SEQUENTIAL_CONCEPT_COMPOSITION", [], False, False),
            ("KT004", [3, 2, 2], 0, 2, "ADVERSARIAL_CONCEPT_REJECTION", [], False, True),
            ("KT005", [2], 0, 2, "NO_REUSABLE_CONCEPT_FALLBACK", [0], False, False),
        ],
    },
    "LOW_PREFIX": {
        "Sources": [
            ("SRC001", [2, 3], 0, 3, "SOURCE_DEPTH3"),
            ("SRC002", [3, 2], 1, 2, "SOURCE_DEPTH2"),
            ("SRC003", [3], 1, 1, "SOURCE_DEPTH1"),
        ],
        "Targets": [
            ("KT001", [2], 1, 1, "SURFACE_PERMUTATION_TRANSFER", [], False, False),
            ("KT002", [2, 3, 2], 2, 2, "COORDINATE_SCALE_TRANSFER", [], False, False),
            ("KT003", [3, 2], 0, 3, "SEQUENTIAL_CONCEPT_COMPOSITION", [], False, False),
            ("KT004", [2, 3], 0, 2, "ADVERSARIAL_CONCEPT_REJECTION", [], False, True),
            ("KT005", [2], 0, 2, "NO_REUSABLE_CONCEPT_FALLBACK", [0], False, False),
        ],
    },
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_task(rng: random.Random, task_id: str, counts: list[int], known_keys: int,
               expected_depth: int, phase: str, role: str, shape: list[list[int]],
               *, disabled: list[int] | None = None, global_probe: bool = False,
               global_binary: bool = False) -> tuple[dict, dict, dict]:
    height = 20
    width = max(16, 6 + 4 * len(counts))
    task = {
        "TaskID": task_id, "GridHeight": height, "GridWidth": width,
        "ContextCounts": counts, "NuisanceCount": 2,
        "DisabledCalibrationLevels": disabled or [], "CorruptedCalibrationLevels": [],
        "GlobalDecisionProbe": global_probe,
        "GlobalBinaryDecisionProbes": global_binary,
        "TrainShape": rng.choice(SYMMETRIC_SHAPES),
        "ProbeShape": rng.choice(DISCRIMINATING_SHAPES), "TestShape": shape,
        "TargetTop": 11, "TargetLeft": width - 6, "TargetColor": rng.choice([1, 2, 3, 4]),
        "KernelMustSynthesizeInterventions": True,
        "MaximumPlanningDepthVisibleAsResourceCapOnly": 3,
        "SurfaceTokenPermutation": rng.sample(["TAU", "RHO", "XI", "MU"], 4),
    }
    hidden = {"Keys": [rng.randrange(count) for count in counts],
              "Decision": rng.randrange(3), "Nuisance": rng.randrange(2)}
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
    for query in query_specs(public):
        expected_cells = len({tuple(cell) for cell in public["ProbeShape"]})
        observed_cells = len(target_cells(public, query["Input"]))
        if observed_cells != expected_cells:
            raise RuntimeError(("probe geometry collision", task_id, query["Kind"],
                                query.get("Level"), query.get("Prefix"), expected_cells, observed_cells))
    sealed = {"TaskID": task_id, "Phase": phase, "ExpectedRole": role,
              "ExpectedMinimumGuaranteedDepth": expected_depth, "HiddenProgram": hidden,
              "TestOutputs": [{"Output": apply_program(task, hidden,
                  {"Kind": "TEST", "Level": None, "Prefix": []})}]}
    oracle = {"TaskID": task_id, "Phase": phase, "HiddenProgram": hidden}
    return public, sealed, oracle


def main() -> int:
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol, protocol_hash = load(protocol_path), digest(protocol_path)
    rng = random.Random(int(protocol["FreshTaskGeneratorSeed"]))
    family = protocol["GeneratorFamily"]
    if family not in FAMILY_CONFIGS:
        raise RuntimeError(f"unknown frozen generator family: {family}")
    shapes = [rng.choice(DISCRIMINATING_SHAPES) for _ in range(8)]
    source_specs = FAMILY_CONFIGS[family]["Sources"]
    sources = [build_task(rng, task_id, counts, known, depth, "SOURCE", role, shape)
               for (task_id, counts, known, depth, role), shape in zip(source_specs, shapes[:3])]
    target_specs = list(FAMILY_CONFIGS[family]["Targets"])
    rng.shuffle(target_specs)
    targets = [build_task(rng, task_id, counts, known, depth, "TARGET", role, shape,
                          disabled=disabled, global_probe=global_probe, global_binary=global_binary)
               for (task_id, counts, known, depth, role, disabled, global_probe, global_binary), shape
               in zip(target_specs, shapes[3:])]
    write(ROOT / "input" / "public_tasks.json", {
        "Stage": protocol["Stage"], "ProtocolSHA256": protocol_hash,
        "SourceTasks": [row[0] for row in sources], "TargetTasks": [row[0] for row in targets],
        "ConceptLabelsProvidedByGenerator": False, "ConceptBodiesProvidedByGenerator": False,
        "PublicQueryPoolSize": 0, "LearnerVisibleRoleLabelCount": 0,
        "LearnerVisibleRequiredDepthCount": 0, "LearnerVisibleHiddenProgramCount": 0,
    })
    all_rows = sources + targets
    write(ROOT / "sealed" / "test_outputs.json", {
        "ProtocolSHA256": protocol_hash, "Tasks": [row[1] for row in all_rows]})
    write(ROOT / "sealed" / "oracle_responses.json", {
        "ProtocolSHA256": protocol_hash, "Tasks": [row[2] for row in all_rows]})
    write(ROOT / "sealed" / "materialization_manifest.json", {
        "ProtocolSHA256": protocol_hash, "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
        "SourceTaskCount": 3, "TargetTaskCount": 5,
        "TargetRoleMultiset": sorted(row[4] for row in target_specs),
        "PostSeedWorldFilteringUsed": False, "WorldReplacementAfterMaterializationUsed": False,
        "ConceptLabelsMaterialized": False, "ConceptBodiesMaterialized": False,
        "GeneratorFamily": family,
        "GeometryCollisionAudit": "ALL_LEGAL_QUERY_INPUTS_PRESERVE_PROBE_CELL_COUNT",
    })
    print(json.dumps({"BuiltSourceTasks": 3, "BuiltFreshTargetTasks": 5,
                      "ProtocolSHA256": protocol_hash,
                      "PostSeedWorldFilteringUsed": False}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
