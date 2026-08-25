"""Freeze first, then construct S132-K5B fresh paired confirmation worlds."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


FORMAL_STRUCTURED_SPECS = [
    {"WorldID": "F501", "Family": "DIHEDRAL_PRODUCT", "Parameters": [13, 3], "Seed": 1_326_501},
    {"WorldID": "F502", "Family": "OVERWRITE_GATE", "Parameters": [6, 5], "Seed": 1_326_502},
    {"WorldID": "F503", "Family": "BOOLEAN_AFFINE", "Parameters": [5, 3], "Seed": 1_326_503},
    {"WorldID": "F504", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [61], "Seed": 1_326_504},
    {"WorldID": "F505", "Family": "DIHEDRAL_PRODUCT", "Parameters": [15, 2], "Seed": 1_326_505},
    {"WorldID": "F506", "Family": "OVERWRITE_GATE", "Parameters": [5, 4, 3], "Seed": 1_326_506},
    {"WorldID": "F507", "Family": "BOOLEAN_AFFINE", "Parameters": [4, 7], "Seed": 1_326_507},
    {"WorldID": "F508", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [79], "Seed": 1_326_508},
]

FORMAL_NEAR_LAW_SPECS = [
    {"WorldID": "FN521", "Kind": "NEAR_IDEMPOTENT", "Parameters": [37], "Seed": 1_326_521},
    {"WorldID": "FN522", "Kind": "NEAR_INVOLUTION", "Parameters": [39], "Seed": 1_326_522},
    {"WorldID": "FN523", "Kind": "NEAR_INVERSE_PAIR", "Parameters": [41], "Seed": 1_326_523},
    {"WorldID": "FN524", "Kind": "NEAR_ABSORPTION", "Parameters": [6, 7], "Seed": 1_326_524},
]

DEV_STRUCTURED_SPECS = [
    {"WorldID": "D501", "Family": "DIHEDRAL_PRODUCT", "Parameters": [5, 2], "Seed": 9_326_501},
    {"WorldID": "D502", "Family": "OVERWRITE_GATE", "Parameters": [3, 3], "Seed": 9_326_502},
    {"WorldID": "D503", "Family": "BOOLEAN_AFFINE", "Parameters": [3, 2], "Seed": 9_326_503},
    {"WorldID": "D504", "Family": "CONJUGATED_SEMIGROUP", "Parameters": [17], "Seed": 9_326_504},
]

DEV_NEAR_LAW_SPECS = [
    {"WorldID": "DN521", "Kind": "NEAR_IDEMPOTENT", "Parameters": [9], "Seed": 9_326_521},
    {"WorldID": "DN522", "Kind": "NEAR_INVOLUTION", "Parameters": [11], "Seed": 9_326_522},
    {"WorldID": "DN523", "Kind": "NEAR_INVERSE_PAIR", "Parameters": [13], "Seed": 9_326_523},
    {"WorldID": "DN524", "Kind": "NEAR_ABSORPTION", "Parameters": [3, 4], "Seed": 9_326_524},
]

EXPECTED_SOURCE_NAMES = {
    "TCCT_S132K3B_IndependentVerifier.py",
    "TCCT_S132K3B_PartialObservationTransfer.wl",
    "TCCT_S132K4A_FreshOnlineConceptCreation.wl",
    "TCCT_S132K4A_IndependentVerifier.py",
    "TCCT_S132K4B_OutOfFamilyBuilder.py",
    "TCCT_S132K5A_ExactIndexedActivation.wl",
    "TCCT_S132K5A_IndependentVerifier.py",
    "TCCT_S132K5B_FreshBuilder.py",
    "TCCT_S132K5B_FreshIndexedConfirmation.wl",
    "TCCT_S132K5B_IndependentVerifier.py",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_hashes(package: Path) -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir())
        if path.is_file()
    }


def profile_specs(profile: str):
    if profile == "formal":
        structured = FORMAL_STRUCTURED_SPECS
        near = FORMAL_NEAR_LAW_SPECS
        base = 1_326_600
    elif profile == "dev":
        structured = DEV_STRUCTURED_SPECS
        near = DEV_NEAR_LAW_SPECS
        base = 9_326_600
    else:
        raise ValueError(profile)
    return {
        "Structured": structured,
        "Near": near,
        "QuerySeeds": [base + 1 + index for index in range(len(structured))],
        "ControlQuerySeeds": [base + 101 + index for index in range(len(structured))],
        "ControlSeeds": [base + 201 + index for index in range(len(structured))],
        "ChallengeQuerySeeds": [base + 301 + index for index in range(len(near))],
    }


def freeze(package: Path, profile: str) -> None:
    package = package.resolve()
    for folder in ("input", "oracle", "sealed", "protocol", "results", "verification"):
        (package / folder).mkdir(parents=True, exist_ok=True)
    manifest_path = package / "protocol" / "S132K5B_pre_world_manifest.json"
    if manifest_path.exists():
        raise RuntimeError("S132-K5B protocol is already frozen")
    actual = {path.name for path in (package / "source").iterdir() if path.is_file()}
    if actual != EXPECTED_SOURCE_NAMES:
        raise RuntimeError(f"unexpected source set: {sorted(actual ^ EXPECTED_SOURCE_NAMES)}")
    specs = profile_specs(profile)
    structured = specs["Structured"]
    near = specs["Near"]
    families = sorted({row["Family"] for row in structured})
    manifest = {
        "Stage": "S132-K5B fresh paired exact indexed activation confirmation",
        "EvidenceStatus": "LOCAL_PREWORLD_FROZEN_FRESH_PAIRED_CONFIRMATION",
        "Profile": profile,
        "FrozenUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "FrozenBeforeWorldMaterialization": True,
        "StartingConceptLibraryCount": 0,
        "MaximumConceptWordLength": 4,
        "StructuredWorldSpecifications": [
            {"WorldID": row["WorldID"], "Family": row["Family"]}
            for row in structured
        ],
        "GeneratorFamilies": families,
        "NearLawWorldSpecifications": [
            {"WorldID": row["WorldID"], "Kind": row["Kind"]}
            for row in near
        ],
        "QueryOrderSeeds": specs["QuerySeeds"],
        "ControlQueryOrderSeeds": specs["ControlQuerySeeds"],
        "RankMatchedControlSeeds": specs["ControlSeeds"],
        "ChallengeQueryOrderSeeds": specs["ChallengeQuerySeeds"],
        "InitialDirectObservationFraction": 0.5,
        "DirectQueryBatchFraction": 0.05,
        "MinimumDirectPositiveWitnessesBeforeInference": 2,
        "PairedExecutionOrder": "odd rows indexed-first; even rows full-scan-first",
        "PairedInputs": "same world, query seed, available library, and frozen learner semantics",
        "ConceptMetaRule": "exact anonymous action-word transformation equivalence",
        "ConceptActivationPolicy": "unchanged K4A exhaustive exact schemas with maximum word length 4",
        "TemporalRule": "world i may use only concepts certified after earlier worlds",
        "NearLawRule": "near-law worlds use the final structured library and do not update it",
        "MatchedBaseline": "same query order with concepts disabled, using frozen full-scan learner",
        "PrimaryMainGate": {
            "PairedOriginalFieldsExactlyEqual": True,
            "AllFinalModelsExact": True,
            "UnsafeCommittedInferenceCount": 0,
            "ActualIndexedClosureWorkStrictlyLower": True,
            "AggregateIndexedRuntimeStrictlyLowerInSameProcess": True,
            "FreshStructuredTransferGatePass": True,
            "AllNearLawChallengesExact": True,
        },
        "FreshStructuredTransferGate": {
            "FinalStructuredLibraryNonempty": True,
            "AtLeastOneLaterWorldUsesPriorConcept": True,
            "AggregateStructuredMembershipSavingsStrictlyPositive": True,
            "AggregateStructuredConcreteSavingsStrictlyPositive": True,
            "StructuredConcreteSavingsStrictlyExceedControlSavings": True,
            "PositiveSavingsCoverageAtLeastThreeOfFourFamilies": True,
        },
        "IndependentOnlyGate": {
            "AllPythonTraceReconstructionsExact": True,
            "StateRelabelDiscoveryInvariance": f"{len(structured)}/{len(structured)}",
            "RankMatchedControlsValid": f"{len(structured)}/{len(structured)}",
            "NearLawTargetsBrokenAndRepresented": f"{len(near)}/{len(near)}",
        },
        "NoArbitraryPercentageSpeedOrSavingsThreshold": True,
        "GeneratorTruthReadableByLearner": False,
        "CanonicalTCCTModified": False,
        "FrozenK3BK4AAndK5AMechanismsModified": False,
        "OnlyExecutionStrategyChanged": True,
        "ObservationNoiseIncluded": False,
        "WorldSizeHiddenFromLearner": False,
        "OpenEndedLanguageInventionClaimAllowed": False,
        "SourceHashes": source_hashes(package),
    }
    dump(manifest_path, manifest)
    dump(package / "protocol" / "S132K5B_freeze_receipt.json", {
        "ManifestSHA256": sha256(manifest_path),
        "WorldsMaterialized": False,
        "RunComplete": False,
    })
    print(f"FROZEN {manifest_path}")


def materialize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K5B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K5B_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "ManifestHash": sha256(manifest_path) == receipt["ManifestSHA256"],
        "Sources": source_hashes(package) == manifest["SourceHashes"],
        "NotPreviouslyMaterialized": receipt["WorldsMaterialized"] is False,
    }
    if not all(checks.values()):
        raise RuntimeError(checks)
    helper = load_module(
        package / "source" / "TCCT_S132K4B_OutOfFamilyBuilder.py",
        "s132k5b_frozen_generator",
    )
    specs = profile_specs(manifest["Profile"])
    public_worlds, structured_worlds, structured_truth, controls = [], [], [], []
    for index, spec in enumerate(specs["Structured"]):
        public, oracle, truth = helper.make_structured_world(spec)
        control_table = helper.rank_matched_table(
            oracle["TransitionTable"], specs["ControlSeeds"][index]
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
    for spec in specs["Near"]:
        oracle, truth = helper.make_near_law_world(spec)
        challenges.append(oracle)
        challenge_truth.append(truth)
    public_path = package / "input" / "S132K5B_public_input.json"
    oracle_path = package / "oracle" / "S132K5B_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K5B_generator_truth.json"
    dump(public_path, {
        "Stage": "S132-K5B public input",
        "ForbiddenFieldsAbsent": ["TransitionTable", "GeneratorParameters", "Seed", "Family"],
        "Worlds": public_worlds,
    })
    dump(oracle_path, {
        "Stage": "S132-K5B simulated membership and equivalence oracles",
        "LearnerMayAccessOnlyThroughFrozenOracleProcedures": True,
        "StructuredWorlds": structured_worlds,
        "RankMatchedControls": controls,
        "NearLawChallenges": challenges,
    })
    dump(truth_path, {
        "Stage": "S132-K5B sealed generator truth",
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
    manifest_path = package / "protocol" / "S132K5B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K5B_freeze_receipt.json"
    result_path = package / "results" / "S132K5B_result.json"
    verification_path = package / "verification" / "S132K5B_independent_verification.json"
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
    parser.add_argument("--profile", choices=["formal", "dev"], default="formal")
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze(args.package, args.profile)
    elif args.phase == "materialize":
        materialize(args.package)
    else:
        finalize(args.package)


if __name__ == "__main__":
    main()
