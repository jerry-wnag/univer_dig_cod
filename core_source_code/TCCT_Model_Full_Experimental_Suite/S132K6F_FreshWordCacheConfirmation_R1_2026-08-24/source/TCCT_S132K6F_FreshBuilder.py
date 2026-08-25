"""Freeze first, then construct S132-K6F fresh word-cache worlds."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


STRUCTURED_SPECS = [
    {"WorldID": "F601", "Family": "DIHEDRAL_PRODUCT", "Parameters": [21, 4], "Seed": 1_329_601},
    {"WorldID": "F602", "Family": "OVERWRITE_GATE", "Parameters": [8, 6], "Seed": 1_329_602},
    {"WorldID": "F603", "Family": "BOOLEAN_AFFINE", "Parameters": [4, 7], "Seed": 1_329_603},
    {"WorldID": "F604", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [59], "Seed": 1_329_604},
    {"WorldID": "F605", "Family": "DIHEDRAL_PRODUCT", "Parameters": [16, 3], "Seed": 1_329_605},
    {"WorldID": "F606", "Family": "OVERWRITE_GATE", "Parameters": [5, 5, 4], "Seed": 1_329_606},
    {"WorldID": "F607", "Family": "BOOLEAN_AFFINE", "Parameters": [5, 3], "Seed": 1_329_607},
    {"WorldID": "F608", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [101], "Seed": 1_329_608},
]

NEAR_LAW_SPECS = [
    {"WorldID": "FN621", "Kind": "NEAR_IDEMPOTENT", "Parameters": [51], "Seed": 1_329_621},
    {"WorldID": "FN622", "Kind": "NEAR_INVOLUTION", "Parameters": [55], "Seed": 1_329_622},
    {"WorldID": "FN623", "Kind": "NEAR_INVERSE_PAIR", "Parameters": [57], "Seed": 1_329_623},
    {"WorldID": "FN624", "Kind": "NEAR_ABSORPTION", "Parameters": [8, 8], "Seed": 1_329_624},
]

QUERY_SEEDS = [1_329_701 + index for index in range(len(STRUCTURED_SPECS))]
CONTROL_QUERY_SEEDS = [1_329_801 + index for index in range(len(STRUCTURED_SPECS))]
CONTROL_SEEDS = [1_329_901 + index for index in range(len(STRUCTURED_SPECS))]
CHALLENGE_QUERY_SEEDS = [1_330_001 + index for index in range(len(NEAR_LAW_SPECS))]

EXPECTED_SOURCE_NAMES = {
    "TCCT_S132K3B_IndependentVerifier.py",
    "TCCT_S132K3B_PartialObservationTransfer.wl",
    "TCCT_S132K4A_FreshOnlineConceptCreation.wl",
    "TCCT_S132K4A_IndependentVerifier.py",
    "TCCT_S132K4B_OutOfFamilyBuilder.py",
    "TCCT_S132K5A_ExactIndexedActivation.wl",
    "TCCT_S132K5A_IndependentVerifier.py",
    "TCCT_S132K6B_IndependentVerifier.py",
    "TCCT_S132K6B_PackedWitnessScheduler.wl",
    "TCCT_S132K6E_ExactWordCachePatch.wl",
    "TCCT_S132K6F_FreshBuilder.py",
    "TCCT_S132K6F_FreshWordCacheConfirmation.wl",
    "TCCT_S132K6F_IndependentVerifier.py",
}

EXPECTED_INPUT_NAMES = {
    "S132K6E_frozen_result.json",
    "S132K6E_frozen_verification.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def hashes(folder: Path) -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted(folder.iterdir())
        if path.is_file()
    }


def freeze(package: Path) -> None:
    package = package.resolve()
    for folder in ("oracle", "sealed", "protocol", "results", "verification"):
        (package / folder).mkdir(parents=True, exist_ok=True)
    manifest_path = package / "protocol" / "S132K6F_pre_world_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("S132-K6F protocol is already frozen")

    actual_sources = {
        path.name for path in (package / "source").iterdir() if path.is_file()
    }
    actual_inputs = {
        path.name for path in (package / "input").iterdir() if path.is_file()
    }
    if actual_sources != EXPECTED_SOURCE_NAMES or actual_inputs != EXPECTED_INPUT_NAMES:
        raise RuntimeError(
            {
                "SourceDifference": sorted(actual_sources ^ EXPECTED_SOURCE_NAMES),
                "InputDifference": sorted(actual_inputs ^ EXPECTED_INPUT_NAMES),
            }
        )

    accepted_result = json.loads(
        (package / "input" / "S132K6E_frozen_result.json").read_text(
            encoding="utf-8"
        )
    )
    accepted_verification = json.loads(
        (package / "input" / "S132K6E_frozen_verification.json").read_text(
            encoding="utf-8"
        )
    )
    k6e_source = package / "source" / "TCCT_S132K6E_ExactWordCachePatch.wl"
    accepted_k6e_hash = accepted_verification["SourceSHA256"][k6e_source.name]
    accepted_checks = {
        "K6EDevelopmentGate": accepted_result["DevelopmentOptimizationGatePass"] is True,
        "K6EIndependentGate": accepted_verification["VerificationPass"] is True,
        "K6ESourceHash": sha256(k6e_source) == accepted_k6e_hash,
    }
    if not all(accepted_checks.values()):
        raise RuntimeError(accepted_checks)

    families = sorted({row["Family"] for row in STRUCTURED_SPECS})
    manifest = {
        "Stage": "S132-K6F fresh exact action-word cache confirmation",
        "EvidenceStatus": "LOCAL_PREWORLD_FROZEN_FRESH_WORD_CACHE_CONFIRMATION",
        "Profile": "formal",
        "FrozenUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "FrozenBeforeWorldMaterialization": True,
        "AcceptedK6ESourceSHA256": accepted_k6e_hash,
        "StartingConceptLibraryCount": 0,
        "MaximumConceptWordLength": 4,
        "StructuredWorldSpecifications": [
            {"WorldID": row["WorldID"], "Family": row["Family"]}
            for row in STRUCTURED_SPECS
        ],
        "GeneratorFamilies": families,
        "NearLawWorldSpecifications": [
            {"WorldID": row["WorldID"], "Kind": row["Kind"]}
            for row in NEAR_LAW_SPECS
        ],
        "PredeclaredStateCountRange": [48, 112],
        "QueryOrderSeeds": QUERY_SEEDS,
        "ControlQueryOrderSeeds": CONTROL_QUERY_SEEDS,
        "RankMatchedControlSeeds": CONTROL_SEEDS,
        "ChallengeQueryOrderSeeds": CHALLENGE_QUERY_SEEDS,
        "InitialDirectObservationFraction": 0.5,
        "DirectQueryBatchFraction": 0.05,
        "MinimumDirectPositiveWitnessesBeforeInference": 2,
        "PairedExecutionOrder": (
            "three-way Latin rotation: K6E/K6B/K5A, K6B/K5A/K6E, "
            "K5A/K6E/K6B"
        ),
        "PairedInputs": (
            "same fresh world, query seed, and available concept library for "
            "K6E, frozen K6B, and K5A"
        ),
        "ConceptMetaRule": "exact anonymous action-word transformation equivalence",
        "ConceptActivationPolicy": "unchanged K4A exact schemas with maximum word length 4",
        "TemporalRule": "world i may use only concepts certified after earlier worlds",
        "NearLawRule": "near-law worlds use the final structured library and do not update it",
        "PrimaryMainGate": {
            "AcceptedK6ESourceHashMatch": True,
            "AllK6EK6BK5AFieldsExactlyEqual": True,
            "AllFinalModelsExact": True,
            "UnsafeCommittedInferenceCount": 0,
            "ExactWordCacheAccountingConservation": True,
            "PhysicalTraceLookupsStrictlyReduced": True,
            "AggregateK6ERuntimeStrictlyBelowK6BInSameProcess": True,
            "AggregateK6ERuntimeStrictlyBelowK5AInSameProcess": True,
            "AllBaseAndCacheNumericArraysPacked": True,
            "ExactWordCacheActuallyExercised": True,
            "FreshStructuredLibraryNonempty": True,
            "AtLeastOneLaterWorldUsesPriorConcept": True,
            "AllNearLawChallengesExact": True,
        },
        "IndependentOnlyGate": {
            "AllPythonTraceReconstructionsExact": True,
            "StateRelabelDiscoveryInvariance": "8/8",
            "RankMatchedControlsValid": "8/8",
            "NearLawTargetsBrokenAndRepresented": "4/4",
        },
        "NoArbitraryPercentageSpeedThreshold": True,
        "GeneratorTruthReadableByLearner": False,
        "CanonicalTCCTModified": False,
        "K3BK4AK5AK6BMechanismsModified": False,
        "OnlyRepeatedActionWordTraceExecutionChanged": True,
        "ObservationNoiseIncluded": False,
        "WorldSizeHiddenFromLearner": False,
        "OpenEndedLanguageInventionClaimAllowed": False,
        "AcceptedInputChecks": accepted_checks,
        "SourceHashes": hashes(package / "source"),
        "InputHashes": hashes(package / "input"),
    }
    dump(manifest_path, manifest)
    dump(
        package / "protocol" / "S132K6F_freeze_receipt.json",
        {
            "ManifestSHA256": sha256(manifest_path),
            "WorldsMaterialized": False,
            "RunComplete": False,
        },
    )
    print(f"FROZEN {manifest_path}")


def materialize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K6F_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K6F_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": hashes(package / "source") == manifest["SourceHashes"],
        "AcceptedInputs": all(
            sha256(package / "input" / name) == digest
            for name, digest in manifest["InputHashes"].items()
        ),
        "NotPreviouslyMaterialized": receipt["WorldsMaterialized"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(checks)

    helper = load_module(
        package / "source" / "TCCT_S132K4B_OutOfFamilyBuilder.py",
        "s132k6f_frozen_generator",
    )
    public_worlds, structured_worlds, structured_truth, controls = [], [], [], []
    for index, spec in enumerate(STRUCTURED_SPECS):
        public, oracle, truth = helper.make_structured_world(spec)
        control_table = helper.rank_matched_table(
            oracle["TransitionTable"], CONTROL_SEEDS[index]
        )
        control = {
            "WorldID": spec["WorldID"],
            "StateCount": len(control_table),
            "ActionCount": len(control_table[0]),
            "TransitionTable": control_table,
            "TargetActionImageRanks": helper.action_ranks(oracle["TransitionTable"]),
            "ControlActionImageRanks": helper.action_ranks(control_table),
        }
        if control["TargetActionImageRanks"] != control["ControlActionImageRanks"]:
            raise RuntimeError(f"rank mismatch: {spec['WorldID']}")
        public_worlds.append(public)
        structured_worlds.append(oracle)
        structured_truth.append(truth)
        controls.append(control)

    challenges, challenge_truth = [], []
    for spec in NEAR_LAW_SPECS:
        oracle, truth = helper.make_near_law_world(spec)
        challenges.append(oracle)
        challenge_truth.append(truth)

    public_path = package / "input" / "S132K6F_public_input.json"
    oracle_path = package / "oracle" / "S132K6F_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K6F_generator_truth.json"
    dump(
        public_path,
        {
            "Stage": "S132-K6F public input",
            "ForbiddenFieldsAbsent": [
                "TransitionTable", "GeneratorParameters", "Seed", "Family"
            ],
            "Worlds": public_worlds,
        },
    )
    dump(
        oracle_path,
        {
            "Stage": "S132-K6F simulated membership and equivalence oracles",
            "LearnerMayAccessOnlyThroughFrozenOracleProcedures": True,
            "StructuredWorlds": structured_worlds,
            "RankMatchedControls": controls,
            "NearLawChallenges": challenges,
        },
    )
    dump(
        truth_path,
        {
            "Stage": "S132-K6F sealed generator truth",
            "ReadableByLearner": False,
            "StructuredWorlds": structured_truth,
            "NearLawChallenges": challenge_truth,
        },
    )
    receipt.update(
        {
            "WorldsMaterialized": True,
            "MaterializedUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
            "MaterializedAfterManifestFreeze": True,
            "FreezeChecksAtMaterialization": checks,
            "PublicInputSHA256": sha256(public_path),
            "OracleSHA256": sha256(oracle_path),
            "SealedTruthSHA256": sha256(truth_path),
        }
    )
    dump(receipt_path, receipt)
    print(
        f"MATERIALIZED {len(structured_worlds)} structured, "
        f"{len(controls)} controls, {len(challenges)} near-law challenges"
    )


def finalize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K6F_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K6F_freeze_receipt.json"
    result_path = package / "results" / "S132K6F_result.json"
    verification_path = (
        package / "verification" / "S132K6F_independent_verification.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": hashes(package / "source") == manifest["SourceHashes"],
        "AcceptedInputs": all(
            sha256(package / "input" / name) == digest
            for name, digest in manifest["InputHashes"].items()
        ),
        "WorldsMaterialized": receipt["WorldsMaterialized"] is True,
        "NotPreviouslyFinalized": receipt["RunComplete"] is False,
        "IndependentEvidenceIntegrity": verification["EvidenceIntegrityPass"] is True,
    }
    if not result_path.exists() or not all(checks.values()):
        raise RuntimeError(checks)
    receipt.update(
        {
            "RunComplete": True,
            "CompletedUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
            "CompletionChecks": checks,
            "ResultSHA256": sha256(result_path),
            "IndependentVerificationSHA256": sha256(verification_path),
            "FinalConclusion": verification["FinalConclusion"],
        }
    )
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
