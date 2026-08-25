"""Freeze first, then materialize S132-K4A fresh online-concept worlds."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import random
from pathlib import Path
from typing import Any


WORLD_SPECS = [
    ("Q401", [4, 5], 1_324_401),
    ("Q402", [5, 6], 1_324_402),
    ("Q403", [3, 4, 5], 1_324_403),
    ("Q404", [2, 5, 4], 1_324_404),
    ("Q405", [4, 4, 3], 1_324_405),
    ("Q406", [5, 4], 1_324_406),
    ("Q407", [6, 5], 1_324_407),
    ("Q408", [4, 3, 5], 1_324_408),
    ("Q409", [5, 2, 4], 1_324_409),
    ("Q410", [3, 4, 4], 1_324_410),
]
QUERY_SEEDS = [1_324_501 + index for index in range(len(WORLD_SPECS))]
CONTROL_QUERY_SEEDS = [1_324_601 + index for index in range(len(WORLD_SPECS))]
CONTROL_SEEDS = [1_324_701 + index for index in range(len(WORLD_SPECS))]


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


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def action_ranks(table: list[list[int]]) -> list[int]:
    return [len({row[action] for row in table}) for action in range(len(table[0]))]


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


def freeze(package: Path) -> None:
    package = package.resolve()
    for folder in ("input", "oracle", "sealed", "protocol", "results", "verification"):
        (package / folder).mkdir(parents=True, exist_ok=True)
    manifest_path = package / "protocol" / "S132K4A_pre_world_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("S132-K4A protocol is already frozen")
    expected_sources = {
        "TCCT_S129C1_FreshBlindConfirmationBuilder.py",
        "TCCT_S132K3B_IndependentVerifier.py",
        "TCCT_S132K3B_PartialObservationTransfer.wl",
        "TCCT_S132K4A_FreshOnlineConceptCreation.wl",
        "TCCT_S132K4A_FreshOnlineConceptCreationBuilder.py",
        "TCCT_S132K4A_IndependentVerifier.py",
    }
    actual_sources = {path.name for path in (package / "source").iterdir() if path.is_file()}
    if actual_sources != expected_sources:
        raise RuntimeError(f"unexpected source set: {sorted(actual_sources ^ expected_sources)}")
    manifest = {
        "Stage": "S132-K4A fresh online bounded concept creation",
        "EvidenceStatus": "LOCAL_PREWORLD_FROZEN_FRESH_SEQUENTIAL_CONFIRMATION",
        "FrozenUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "FrozenBeforeWorldMaterialization": True,
        "StartingConceptLibraryCount": 0,
        "PreloadedK3ASchemasAllowed": False,
        "ConceptMetaRule": "exact anonymous action-word transformation equivalence",
        "MaximumConceptWordLength": 4,
        "WorldSpecifications": [
            {"WorldID": world_id, "Dimensions": dimensions, "Seed": seed}
            for world_id, dimensions, seed in WORLD_SPECS
        ],
        "QueryOrderSeeds": QUERY_SEEDS,
        "ControlQueryOrderSeeds": CONTROL_QUERY_SEEDS,
        "RankMatchedControlSeeds": CONTROL_SEEDS,
        "InitialDirectObservationFraction": 0.5,
        "DirectQueryBatchFraction": 0.05,
        "MinimumDirectPositiveWitnessesBeforeInference": 2,
        "ConceptActivationPolicy": (
            "Every exact anonymous shortening schema discovered after a world is certified "
            "is added; no Top-N, support threshold, or future-world filtering"
        ),
        "TemporalRule": "world i may use only concepts created after worlds strictly before i",
        "ConflictPolicy": (
            "same-target provenance union; all hypotheses in every simultaneous "
            "different-target conflict are jointly disabled"
        ),
        "MatchedBaseline": "same query order with concept creation and transfer disabled",
        "PrimaryGate": {
            "AllStructuredAndControlFinalModelsExact": True,
            "UnsafeCommittedInferenceCount": 0,
            "FinalStructuredLibraryNonempty": True,
            "AtLeastOneLaterWorldUsesPriorCreatedConcept": True,
            "PositiveStructuredMembershipSavingsEligibleWorldFractionAtLeast": 0.5,
            "AggregateStructuredMembershipSavingsStrictlyPositive": True,
            "AggregateStructuredConcreteSavingsStrictlyPositive": True,
            "StructuredConcreteSavingsStrictlyExceedControlSavings": True,
        },
        "Generator": "unchanged frozen S129-C1 in-bound generator",
        "GeneratorTruthReadableByLearner": False,
        "FullStateSchemaPrefilterOnCurrentWorldAllowed": False,
        "CanonicalTCCTModified": False,
        "B8ASymbolicLearnerIntegrationClaimAllowed": False,
        "OpenEndedLanguageInventionClaimAllowed": False,
        "SourceHashes": source_hashes(package),
    }
    dump(manifest_path, manifest)
    dump(package / "protocol" / "S132K4A_freeze_receipt.json", {
        "ManifestSHA256": sha256(manifest_path),
        "WorldsMaterialized": False,
        "RunComplete": False,
    })
    print(f"FROZEN {manifest_path}")


def materialize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K4A_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4A_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": source_hashes(package) == manifest["SourceHashes"],
        "NotPreviouslyMaterialized": receipt["WorldsMaterialized"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(checks)
    generator = load_module(
        package / "source" / "TCCT_S129C1_FreshBlindConfirmationBuilder.py",
        "s132k4a_frozen_generator",
    )
    structured, controls, public, truth = [], [], [], []
    for index, (world_id, dimensions, seed) in enumerate(WORLD_SPECS):
        programs = generator.in_bound_programs(dimensions, seed)
        public_world, oracle_world, truth_world = generator.make_world(
            world_id, dimensions, programs, seed, "S132K4A_FRESH_ONLINE"
        )
        table = oracle_world["TransitionTable"]
        structured.append({
            "WorldID": world_id,
            "StateCount": len(table),
            "ActionCount": len(table[0]),
            "TransitionTable": table,
        })
        control_table = rank_matched_table(table, CONTROL_SEEDS[index])
        controls.append({
            "WorldID": world_id,
            "StateCount": len(control_table),
            "ActionCount": len(control_table[0]),
            "TransitionTable": control_table,
            "TargetActionImageRanks": action_ranks(table),
            "ControlActionImageRanks": action_ranks(control_table),
        })
        public.append({
            "WorldID": world_id,
            "StateCount": public_world["StateCount"],
            "ActionCount": public_world["ActionCount"],
            "StartState": public_world["StartState"],
        })
        truth.append({**truth_world, "ControlSeed": CONTROL_SEEDS[index]})
    public_path = package / "input" / "S132K4A_public_input.json"
    oracle_path = package / "oracle" / "S132K4A_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K4A_generator_truth.json"
    dump(public_path, {
        "Stage": "S132-K4A fresh public sequence",
        "ForbiddenFieldsAbsent": ["TransitionTable", "GeneratorPrograms", "Seed", "Dimensions"],
        "Worlds": public,
    })
    dump(oracle_path, {
        "Stage": "S132-K4A simulated membership and equivalence oracles",
        "LearnerMayAccessOnlyThroughFrozenOracleProcedures": True,
        "StructuredWorlds": structured,
        "RankMatchedControls": controls,
    })
    dump(truth_path, {
        "Stage": "S132-K4A sealed generator truth",
        "ReadableByLearner": False,
        "Worlds": truth,
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
    print(f"MATERIALIZED {len(structured)} fresh worlds and {len(controls)} controls")


def finalize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K4A_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4A_freeze_receipt.json"
    result_path = package / "results" / "S132K4A_result.json"
    verification_path = (
        package / "verification" / "S132K4A_independent_verification.json"
    )
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
