"""Freeze first, then construct S132-K4B out-of-family fresh worlds."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import itertools
import json
import math
import random
from pathlib import Path
from typing import Any, Callable, Iterable


STRUCTURED_SPECS = [
    {"WorldID": "O401", "Family": "DIHEDRAL_PRODUCT", "Parameters": [7, 3], "Seed": 1_325_401},
    {"WorldID": "O402", "Family": "OVERWRITE_GATE", "Parameters": [4, 5], "Seed": 1_325_402},
    {"WorldID": "O403", "Family": "BOOLEAN_AFFINE", "Parameters": [4, 3], "Seed": 1_325_403},
    {"WorldID": "O404", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [37], "Seed": 1_325_404},
    {"WorldID": "O405", "Family": "DIHEDRAL_PRODUCT", "Parameters": [9, 4], "Seed": 1_325_405},
    {"WorldID": "O406", "Family": "OVERWRITE_GATE", "Parameters": [5, 6], "Seed": 1_325_406},
    {"WorldID": "O407", "Family": "BOOLEAN_AFFINE", "Parameters": [5, 2], "Seed": 1_325_407},
    {"WorldID": "O408", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [53], "Seed": 1_325_408},
    {"WorldID": "O409", "Family": "DIHEDRAL_PRODUCT", "Parameters": [11, 3], "Seed": 1_325_409},
    {"WorldID": "O410", "Family": "OVERWRITE_GATE", "Parameters": [4, 4, 3], "Seed": 1_325_410},
    {"WorldID": "O411", "Family": "BOOLEAN_AFFINE", "Parameters": [4, 5], "Seed": 1_325_411},
    {"WorldID": "O412", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [71], "Seed": 1_325_412},
]

NEAR_LAW_SPECS = [
    {"WorldID": "N421", "Kind": "NEAR_IDEMPOTENT", "Parameters": [31], "Seed": 1_325_421},
    {"WorldID": "N422", "Kind": "NEAR_INVOLUTION", "Parameters": [33], "Seed": 1_325_422},
    {"WorldID": "N423", "Kind": "NEAR_INVERSE_PAIR", "Parameters": [35], "Seed": 1_325_423},
    {"WorldID": "N424", "Kind": "NEAR_ABSORPTION", "Parameters": [5, 7], "Seed": 1_325_424},
]

QUERY_SEEDS = [1_325_501 + index for index in range(len(STRUCTURED_SPECS))]
CONTROL_QUERY_SEEDS = [1_325_601 + index for index in range(len(STRUCTURED_SPECS))]
CONTROL_SEEDS = [1_325_701 + index for index in range(len(STRUCTURED_SPECS))]
CHALLENGE_QUERY_SEEDS = [1_325_801 + index for index in range(len(NEAR_LAW_SPECS))]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_hashes(package: Path) -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir())
        if path.is_file()
    }


def action_ranks(table: list[list[int]]) -> list[int]:
    return [len({row[action] for row in table}) for action in range(len(table[0]))]


def word_transform(table: list[list[int]], word: Iterable[int]) -> tuple[int, ...]:
    mapping = list(range(len(table)))
    for action in word:
        mapping = [table[state][action - 1] - 1 for state in mapping]
    return tuple(mapping)


def rank_matched_table(table: list[list[int]], seed: int) -> list[list[int]]:
    rng = random.Random(seed)
    state_count = len(table)
    columns = []
    for rank in action_ranks(table):
        image = rng.sample(range(1, state_count + 1), rank)
        values = image + [rng.choice(image) for _ in range(state_count - rank)]
        rng.shuffle(values)
        columns.append(values)
    return [list(row) for row in zip(*columns)]


def table_from_functions(
    states: list[Any], functions: list[Callable[[Any], Any]],
) -> list[list[int]]:
    index = {state: position for position, state in enumerate(states)}
    return [
        [index[function(state)] for function in functions]
        for state in states
    ]


def relabel_table(
    canonical_zero_based: list[list[int]], action_order: list[int], state_seed: int,
) -> tuple[list[list[int]], list[int]]:
    state_count = len(canonical_zero_based)
    rng = random.Random(state_seed)
    new_id_for_old = list(range(state_count))
    rng.shuffle(new_id_for_old)
    output = [[0] * len(action_order) for _ in range(state_count)]
    for old_state, canonical_row in enumerate(canonical_zero_based):
        new_state = new_id_for_old[old_state]
        for new_action, old_action in enumerate(action_order):
            output[new_state][new_action] = new_id_for_old[canonical_row[old_action]] + 1
    return output, new_id_for_old


def set_coordinate(state: tuple[int, ...], coordinate: int, value: int) -> tuple[int, ...]:
    result = list(state)
    result[coordinate] = value
    return tuple(result)


def build_canonical(spec: dict[str, Any]) -> tuple[list[list[int]], dict[str, Any]]:
    family = spec["Family"]
    params = spec["Parameters"]
    seed = int(spec["Seed"])
    rng = random.Random(seed)

    if family == "DIHEDRAL_PRODUCT":
        n, m = params
        reflection_offset = rng.randrange(n)
        reset_value = rng.randrange(m)
        states = list(itertools.product(range(n), range(m)))
        functions = [
            lambda state: ((state[0] + 1) % n, state[1]),
            lambda state: ((state[0] - 1) % n, state[1]),
            lambda state: ((reflection_offset - state[0]) % n, state[1]),
            lambda state: (state[0], reset_value),
        ]
        detail = {"ReflectionOffset": reflection_offset, "ResetValue": reset_value}
    elif family == "OVERWRITE_GATE":
        dimensions = params
        states = list(itertools.product(*(range(size) for size in dimensions)))
        first_value = rng.randrange(dimensions[0])
        last_value = rng.randrange(dimensions[-1])
        middle_coordinate = 1 if len(dimensions) > 1 else 0
        functions = [
            lambda state: set_coordinate(state, 0, first_value),
            lambda state: set_coordinate(state, len(dimensions) - 1, last_value),
            lambda state: set_coordinate(
                state, middle_coordinate,
                (state[middle_coordinate] + 1) % dimensions[middle_coordinate],
            ),
            lambda state: (
                set_coordinate(state, 0, first_value)
                if state[-1] == last_value else state
            ),
        ]
        detail = {"FirstValue": first_value, "LastValue": last_value}
    elif family == "BOOLEAN_AFFINE":
        bit_count, modulus = params
        states = list(itertools.product(range(2 ** bit_count), range(modulus)))
        masks = rng.sample(range(1, 2 ** bit_count), 2)
        clear_bit = rng.randrange(bit_count)
        functions = [
            lambda state: (state[0] ^ masks[0], state[1]),
            lambda state: (state[0] ^ masks[1], state[1]),
            lambda state: (state[0], (state[1] + 1) % modulus),
            lambda state: (state[0] & ~(1 << clear_bit), state[1]),
        ]
        detail = {"Masks": masks, "ClearBit": clear_bit}
    elif family == "CONJUGATED_SEMIGROUP":
        (size,) = params
        reflection_offset = rng.randrange(size)
        states = list(range(size))
        functions = [
            lambda state: (state + 1) % size,
            lambda state: (state - 1) % size,
            lambda state: (reflection_offset - state) % size,
            lambda state: state - (state % 2),
        ]
        detail = {"ReflectionOffset": reflection_offset}
    else:
        raise ValueError(family)

    return table_from_functions(states, functions), detail


def make_structured_world(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    canonical, detail = build_canonical(spec)
    action_count = len(canonical[0])
    action_order = list(range(action_count))
    random.Random(int(spec["Seed"]) + 11).shuffle(action_order)
    table, state_relabel = relabel_table(canonical, action_order, int(spec["Seed"]) + 23)
    alternate, alternate_relabel = relabel_table(
        canonical, action_order, int(spec["Seed"]) + 37
    )
    oracle = {
        "WorldID": spec["WorldID"],
        "StateCount": len(table),
        "ActionCount": len(table[0]),
        "TransitionTable": table,
    }
    public = {
        "WorldID": spec["WorldID"],
        "StateCount": len(table),
        "ActionCount": len(table[0]),
        "StartState": 1,
    }
    truth = {
        "WorldID": spec["WorldID"],
        "Family": spec["Family"],
        "Parameters": spec["Parameters"],
        "Seed": spec["Seed"],
        "GeneratorDetail": detail,
        "ActionOrderOldIndices": action_order,
        "StateRelabelNewIDForOld": state_relabel,
        "AlternateStateRelabelNewIDForOld": alternate_relabel,
        "AlternateRelabeledTransitionTable": alternate,
    }
    return public, oracle, truth


def near_law_canonical(spec: dict[str, Any]) -> tuple[list[list[int]], list[int], list[int], list[list[int]]]:
    kind = spec["Kind"]
    params = spec["Parameters"]
    seed = int(spec["Seed"])
    rng = random.Random(seed)

    if kind == "NEAR_ABSORPTION":
        width, height = params
        states = list(itertools.product(range(width), range(height)))
        index = {state: position for position, state in enumerate(states)}
        p = [index[(0, y)] for _, y in states]
        q = [index[(x, 0)] for x, _ in states]
        q[index[(1, 1)]] = index[(2, 1)]
        size = len(states)
        target_long, target_short = [0, 1, 0], [1, 0]
        anonymous = [[1, 2, 1], [2, 1]]
    else:
        (size,) = params
        if kind == "NEAR_IDEMPOTENT":
            target = list(range(size))
            target[0], target[1], target[2] = 1, 2, 2
            p = target
            target_long, target_short = [0, 0], [0]
            anonymous = [[1, 1], [1]]
        elif kind == "NEAR_INVOLUTION":
            target = list(range(size))
            for position in range(0, size - 1, 2):
                target[position], target[position + 1] = position + 1, position
            target[0], target[1] = 1, 2
            p = target
            target_long, target_short = [0, 0], []
            anonymous = [[1, 1], []]
        elif kind == "NEAR_INVERSE_PAIR":
            p = [(state + 1) % size for state in range(size)]
            q = [(state - 1) % size for state in range(size)]
            q[0] = size - 2
            target_long, target_short = [0, 1], []
            anonymous = [[1, 2], []]
        else:
            raise ValueError(kind)

    maps = [p]
    if kind in {"NEAR_INVERSE_PAIR", "NEAR_ABSORPTION"}:
        maps.append(q)
    while len(maps) < 4:
        permutation = list(range(size))
        rng.shuffle(permutation)
        maps.append(permutation)
    canonical = [[mapping[state] for mapping in maps] for state in range(size)]
    return canonical, target_long, target_short, anonymous


def make_near_law_world(spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical, old_long, old_short, anonymous = near_law_canonical(spec)
    action_order = list(range(len(canonical[0])))
    random.Random(int(spec["Seed"]) + 11).shuffle(action_order)
    table, state_relabel = relabel_table(canonical, action_order, int(spec["Seed"]) + 23)
    new_action_for_old = {old: new + 1 for new, old in enumerate(action_order)}
    target_long = [new_action_for_old[action] for action in old_long]
    target_short = [new_action_for_old[action] for action in old_short]
    left, right = word_transform(table, target_long), word_transform(table, target_short)
    mismatch_count = sum(a != b for a, b in zip(left, right))
    if mismatch_count <= 0:
        raise RuntimeError(f"near-law relation unexpectedly exact: {spec['WorldID']}")
    oracle = {
        "WorldID": spec["WorldID"],
        "StateCount": len(table),
        "ActionCount": len(table[0]),
        "TransitionTable": table,
    }
    truth = {
        "WorldID": spec["WorldID"],
        "Kind": spec["Kind"],
        "Parameters": spec["Parameters"],
        "Seed": spec["Seed"],
        "ActionOrderOldIndices": action_order,
        "StateRelabelNewIDForOld": state_relabel,
        "TargetLong": target_long,
        "TargetShort": target_short,
        "TargetAnonymousSchema": anonymous,
        "TargetMismatchCount": mismatch_count,
    }
    return oracle, truth


def expected_source_names() -> set[str]:
    return {
        "TCCT_S132K3B_IndependentVerifier.py",
        "TCCT_S132K3B_PartialObservationTransfer.wl",
        "TCCT_S132K4A_FreshOnlineConceptCreation.wl",
        "TCCT_S132K4A_IndependentVerifier.py",
        "TCCT_S132K4B_IndependentVerifier.py",
        "TCCT_S132K4B_OutOfFamilyBuilder.py",
        "TCCT_S132K4B_OutOfFamilyConceptTransfer.wl",
    }


def freeze(package: Path) -> None:
    package = package.resolve()
    for folder in ("input", "oracle", "sealed", "protocol", "results", "verification"):
        (package / folder).mkdir(parents=True, exist_ok=True)
    manifest_path = package / "protocol" / "S132K4B_pre_world_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("S132-K4B protocol is already frozen")
    actual = {path.name for path in (package / "source").iterdir() if path.is_file()}
    if actual != expected_source_names():
        raise RuntimeError(f"unexpected source set: {sorted(actual ^ expected_source_names())}")
    families = sorted({spec["Family"] for spec in STRUCTURED_SPECS})
    manifest = {
        "Stage": "S132-K4B fresh out-of-family bounded concept transfer stress test",
        "EvidenceStatus": "LOCAL_PREWORLD_FROZEN_FRESH_OUT_OF_FAMILY_CONFIRMATION",
        "FrozenUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "FrozenBeforeWorldMaterialization": True,
        "StartingConceptLibraryCount": 0,
        "PreloadedK4ASchemasAllowed": False,
        "MaximumConceptWordLength": 4,
        "StructuredWorldSpecifications": [
            {"WorldID": row["WorldID"], "Family": row["Family"]}
            for row in STRUCTURED_SPECS
        ],
        "GeneratorFamilies": families,
        "GeneratorFamilyCount": len(families),
        "NearLawWorldSpecifications": [
            {"WorldID": row["WorldID"], "Kind": row["Kind"]}
            for row in NEAR_LAW_SPECS
        ],
        "QueryOrderSeeds": QUERY_SEEDS,
        "ControlQueryOrderSeeds": CONTROL_QUERY_SEEDS,
        "RankMatchedControlSeeds": CONTROL_SEEDS,
        "ChallengeQueryOrderSeeds": CHALLENGE_QUERY_SEEDS,
        "InitialDirectObservationFraction": 0.5,
        "DirectQueryBatchFraction": 0.05,
        "MinimumDirectPositiveWitnessesBeforeInference": 2,
        "ConceptMetaRule": "exact anonymous action-word transformation equivalence",
        "ConceptActivationPolicy": (
            "unchanged K4A policy: add every exact schema after certification; "
            "no Top-N, support threshold, or future filtering"
        ),
        "TemporalRule": "structured world i may use only concepts created after earlier structured worlds",
        "NearLawRule": "near-law challenges use the final structured library but never update it",
        "MatchedBaseline": "same query order with concept creation and transfer disabled",
        "PrimaryMainGate": {
            "AllFinalModelsExact": True,
            "UnsafeCommittedInferenceCount": 0,
            "FinalStructuredLibraryNonempty": True,
            "AtLeastOneLaterWorldUsesPriorCreatedConcept": True,
            "AggregateStructuredMembershipSavingsStrictlyPositive": True,
            "AggregateStructuredConcreteSavingsStrictlyPositive": True,
            "StructuredConcreteSavingsStrictlyExceedRandomControlSavings": True,
            "PositiveSavingsCoverageAtLeastThreeOfFourFamilies": True,
            "AllNearLawChallengesExact": True,
        },
        "IndependentOnlyGate": {
            "StateRelabelDiscoveryInvariance": "12/12",
            "NearLawTargetsBrokenAndRepresentedInStructuredLibrary": "4/4",
            "AllTraceAndLibraryReconstructionsExact": True,
        },
        "NoArbitraryPercentageSavingsThreshold": True,
        "Generator": "four new K4B generator families; no S129-C1 generator call",
        "GeneratorTruthReadableByLearner": False,
        "FullStateSchemaPrefilterOnCurrentWorldAllowed": False,
        "CanonicalTCCTModified": False,
        "FrozenK3BAndK4ALearnerModified": False,
        "ObservationNoiseIncluded": False,
        "WorldSizeHiddenFromLearner": False,
        "OpenEndedLanguageInventionClaimAllowed": False,
        "SourceHashes": source_hashes(package),
    }
    dump(manifest_path, manifest)
    dump(package / "protocol" / "S132K4B_freeze_receipt.json", {
        "ManifestSHA256": sha256(manifest_path),
        "WorldsMaterialized": False,
        "RunComplete": False,
    })
    print(f"FROZEN {manifest_path}")


def materialize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K4B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4B_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": source_hashes(package) == manifest["SourceHashes"],
        "NotPreviouslyMaterialized": receipt["WorldsMaterialized"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(checks)

    public_worlds, structured_worlds, structured_truth = [], [], []
    controls = []
    for index, spec in enumerate(STRUCTURED_SPECS):
        public, oracle, truth = make_structured_world(spec)
        control_table = rank_matched_table(oracle["TransitionTable"], CONTROL_SEEDS[index])
        control = {
            "WorldID": spec["WorldID"],
            "StateCount": len(control_table),
            "ActionCount": len(control_table[0]),
            "TransitionTable": control_table,
            "TargetActionImageRanks": action_ranks(oracle["TransitionTable"]),
            "ControlActionImageRanks": action_ranks(control_table),
        }
        if control["TargetActionImageRanks"] != control["ControlActionImageRanks"]:
            raise RuntimeError(f"rank mismatch: {spec['WorldID']}")
        public_worlds.append(public)
        structured_worlds.append(oracle)
        structured_truth.append(truth)
        controls.append(control)

    challenges, challenge_truth = [], []
    for spec in NEAR_LAW_SPECS:
        oracle, truth = make_near_law_world(spec)
        challenges.append(oracle)
        challenge_truth.append(truth)

    public_path = package / "input" / "S132K4B_public_input.json"
    oracle_path = package / "oracle" / "S132K4B_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K4B_generator_truth.json"
    dump(public_path, {
        "Stage": "S132-K4B public input",
        "ForbiddenFieldsAbsent": ["TransitionTable", "GeneratorParameters", "Seed", "Family"],
        "Worlds": public_worlds,
    })
    dump(oracle_path, {
        "Stage": "S132-K4B simulated membership and equivalence oracles",
        "LearnerMayAccessOnlyThroughFrozenOracleProcedures": True,
        "StructuredWorlds": structured_worlds,
        "RankMatchedControls": controls,
        "NearLawChallenges": challenges,
    })
    dump(truth_path, {
        "Stage": "S132-K4B sealed generator truth",
        "ReadableByLearner": False,
        "StructuredWorlds": structured_truth,
        "NearLawChallenges": challenge_truth,
    })
    receipt.update({
        "WorldsMaterialized": True,
        "MaterializedUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "MaterializedAfterManifestFreeze": True,
        "FreezeChecksAtMaterialization": checks,
        "PublicInputSHA256": sha256(public_path),
        "OracleSHA256": sha256(oracle_path),
        "SealedTruthSHA256": sha256(truth_path),
    })
    dump(receipt_path, receipt)
    print(
        f"MATERIALIZED {len(structured_worlds)} structured, "
        f"{len(controls)} controls, {len(challenges)} near-law challenges"
    )


def finalize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K4B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4B_freeze_receipt.json"
    result_path = package / "results" / "S132K4B_result.json"
    verification_path = package / "verification" / "S132K4B_independent_verification.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": source_hashes(package) == manifest["SourceHashes"],
        "WorldsMaterialized": receipt["WorldsMaterialized"] is True,
        "NotPreviouslyFinalized": receipt["RunComplete"] is False,
        "IndependentEvidenceIntegrity": verification["EvidenceIntegrityPass"] is True,
    }
    if not result_path.exists() or not all(checks.values()):
        raise RuntimeError(checks)
    receipt.update({
        "RunComplete": True,
        "CompletedUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "CompletionChecks": checks,
        "ResultSHA256": sha256(result_path),
        "IndependentVerificationSHA256": sha256(verification_path),
        "FinalConclusion": verification["FinalConclusion"],
    })
    dump(receipt_path, receipt)
    print(f"FINALIZED {verification['FinalConclusion']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["freeze", "materialize", "finalize"])
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze(args.package)
    elif args.phase == "materialize":
        materialize(args.package)
    else:
        finalize(args.package)


if __name__ == "__main__":
    main()
