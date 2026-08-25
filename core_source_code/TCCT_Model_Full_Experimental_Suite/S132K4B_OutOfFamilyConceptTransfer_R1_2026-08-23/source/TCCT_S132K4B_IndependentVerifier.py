"""Independent reconstruction and sealed audits for S132-K4B."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_tuple(schema: list[list[int]]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(schema[0]), tuple(schema[1])


def word_transform(table: list[list[int]], word: list[int]) -> tuple[int, ...]:
    mapping = list(range(len(table)))
    for action in word:
        mapping = [table[state][action - 1] - 1 for state in mapping]
    return tuple(mapping)


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K4B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4B_freeze_receipt.json"
    public_path = package / "input" / "S132K4B_public_input.json"
    oracle_path = package / "oracle" / "S132K4B_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K4B_generator_truth.json"
    result_path = package / "results" / "S132K4B_result.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    k3 = load_module(
        package / "source" / "TCCT_S132K3B_IndependentVerifier.py",
        "s132k4b_k3_helper",
    )
    k4 = load_module(
        package / "source" / "TCCT_S132K4A_IndependentVerifier.py",
        "s132k4b_k4_helper",
    )

    current_sources = {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir()) if path.is_file()
    }
    source_hash_pass = current_sources == manifest["SourceHashes"]
    phase_pass = (
        sha256(manifest_path) == receipt["ManifestSHA256"]
        and receipt["WorldsMaterialized"] is True
        and receipt["MaterializedAfterManifestFreeze"] is True
        and sha256(public_path) == receipt["PublicInputSHA256"]
        and sha256(oracle_path) == receipt["OracleSHA256"]
        and sha256(truth_path) == receipt["SealedTruthSHA256"]
    )
    maximum = int(manifest["MaximumConceptWordLength"])
    initial = float(manifest["InitialDirectObservationFraction"])
    batch = float(manifest["DirectQueryBatchFraction"])
    witnesses = int(manifest["MinimumDirectPositiveWitnessesBeforeInference"])

    expected_structured_ids = [
        row["WorldID"] for row in manifest["StructuredWorldSpecifications"]
    ]
    expected_challenge_ids = [
        row["WorldID"] for row in manifest["NearLawWorldSpecifications"]
    ]
    sequence_shape_pass = (
        expected_structured_ids
        == [row["WorldID"] for row in public["Worlds"]]
        == [row["WorldID"] for row in oracle["StructuredWorlds"]]
        == [row["WorldID"] for row in oracle["RankMatchedControls"]]
        == [row["WorldID"] for row in result["StructuredResults"]]
        == [row["WorldID"] for row in result["ControlResults"]]
        and expected_challenge_ids
        == [row["WorldID"] for row in oracle["NearLawChallenges"]]
        == [row["WorldID"] for row in result["NearLawChallengeResults"]]
    )
    rank_match_pass = all(
        k4.action_ranks(structured["TransitionTable"])
        == k4.action_ranks(control["TransitionTable"])
        == control["TargetActionImageRanks"]
        == control["ControlActionImageRanks"]
        for structured, control in zip(
            oracle["StructuredWorlds"], oracle["RankMatchedControls"]
        )
    )

    def reconstruct_stream(worlds, rows):
        library: dict[Any, dict[str, Any]] = {}
        next_id = 0
        audits = []
        for world, row in zip(worlds, rows):
            available = sorted(library.values(), key=lambda record: record["SchemaID"])
            transfer = k3.replay(
                world["TransitionTable"], available,
                row["Transfer"]["QueryOrder"], True,
                initial, batch, witnesses,
            )
            baseline = k3.replay(
                world["TransitionTable"], [],
                row["Baseline"]["QueryOrder"], False,
                initial, batch, witnesses,
            )
            transfer_mismatch = [
                key for key, value in transfer.items()
                if row["Transfer"][key] != value
            ]
            baseline_mismatch = [
                key for key, value in baseline.items()
                if row["Baseline"][key] != value
            ]
            schemas = k4.discover(world["TransitionTable"], maximum)
            before = len(library)
            next_id, new_count = k4.update_library(
                library, next_id, schemas, world["WorldID"]
            )
            expected_mq = baseline["MembershipQueries"] - transfer["MembershipQueries"]
            expected_logical = baseline["LogicalInteractionCost"] - transfer["LogicalInteractionCost"]
            expected_concrete = baseline["ConcreteOracleCellCost"] - transfer["ConcreteOracleCellCost"]
            trajectory = (
                int(row["LibraryBeforeCount"]) == before
                and int(row["SchemasDiscoveredThisWorld"]) == len(schemas)
                and int(row["NewSchemaCount"]) == new_count
                and int(row["LibraryAfterCount"]) == len(library)
                and bool(row["PriorCreatedConceptUsed"])
                == (transfer["FinalInferredTransitionCount"] > 0)
                and int(row["MembershipQuerySavings"]) == expected_mq
                and int(row["LogicalInteractionCostSavings"]) == expected_logical
                and int(row["ConcreteOracleCellCostSavings"]) == expected_concrete
            )
            audits.append({
                "WorldID": world["WorldID"],
                "TransferReconstructionPass": not transfer_mismatch,
                "TransferMismatchFields": transfer_mismatch,
                "BaselineReconstructionPass": not baseline_mismatch,
                "BaselineMismatchFields": baseline_mismatch,
                "LibraryTrajectoryPass": trajectory,
            })
        records = sorted(library.values(), key=lambda record: record["SchemaID"])
        passed = all(
            row["TransferReconstructionPass"]
            and row["BaselineReconstructionPass"]
            and row["LibraryTrajectoryPass"]
            for row in audits
        )
        return audits, records, passed

    structured_audits, structured_library, structured_pass = reconstruct_stream(
        oracle["StructuredWorlds"], result["StructuredResults"]
    )
    control_audits, control_library, control_pass = reconstruct_stream(
        oracle["RankMatchedControls"], result["ControlResults"]
    )
    library_pass = (
        structured_library == result["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"]
    )

    challenge_audits = []
    for world, row in zip(
        oracle["NearLawChallenges"], result["NearLawChallengeResults"]
    ):
        transfer = k3.replay(
            world["TransitionTable"], structured_library,
            row["Transfer"]["QueryOrder"], True,
            initial, batch, witnesses,
        )
        baseline = k3.replay(
            world["TransitionTable"], [],
            row["Baseline"]["QueryOrder"], False,
            initial, batch, witnesses,
        )
        transfer_mismatch = [
            key for key, value in transfer.items() if row["Transfer"][key] != value
        ]
        baseline_mismatch = [
            key for key, value in baseline.items() if row["Baseline"][key] != value
        ]
        arithmetic = (
            int(row["AvailableStructuredConceptCount"]) == len(structured_library)
            and int(row["MembershipQuerySavings"])
            == baseline["MembershipQueries"] - transfer["MembershipQueries"]
            and int(row["LogicalInteractionCostSavings"])
            == baseline["LogicalInteractionCost"] - transfer["LogicalInteractionCost"]
            and int(row["ConcreteOracleCellCostSavings"])
            == baseline["ConcreteOracleCellCost"] - transfer["ConcreteOracleCellCost"]
        )
        challenge_audits.append({
            "WorldID": world["WorldID"],
            "TransferReconstructionPass": not transfer_mismatch,
            "TransferMismatchFields": transfer_mismatch,
            "BaselineReconstructionPass": not baseline_mismatch,
            "BaselineMismatchFields": baseline_mismatch,
            "ArithmeticPass": arithmetic,
        })
    challenge_pass = all(
        row["TransferReconstructionPass"]
        and row["BaselineReconstructionPass"]
        and row["ArithmeticPass"]
        for row in challenge_audits
    )

    alternate_by_id = {
        row["WorldID"]: row["AlternateRelabeledTransitionTable"]
        for row in truth["StructuredWorlds"]
    }
    relabel_audits = []
    for world in oracle["StructuredWorlds"]:
        observed_schemas = k4.discover(world["TransitionTable"], maximum)
        alternate_schemas = k4.discover(alternate_by_id[world["WorldID"]], maximum)
        relabel_audits.append({
            "WorldID": world["WorldID"],
            "SchemaCount": len(observed_schemas),
            "StateRelabelDiscoveryInvariant": observed_schemas == alternate_schemas,
        })
    relabel_pass = all(row["StateRelabelDiscoveryInvariant"] for row in relabel_audits)

    final_schema_set = {
        schema_tuple(record["Schema"]) for record in structured_library
    }
    challenge_world_by_id = {
        row["WorldID"]: row for row in oracle["NearLawChallenges"]
    }
    target_audits = []
    for target in truth["NearLawChallenges"]:
        world = challenge_world_by_id[target["WorldID"]]
        left = word_transform(world["TransitionTable"], target["TargetLong"])
        right = word_transform(world["TransitionTable"], target["TargetShort"])
        mismatch_count = sum(a != b for a, b in zip(left, right))
        target_audits.append({
            "WorldID": target["WorldID"],
            "Kind": target["Kind"],
            "TargetRelationActuallyBroken": mismatch_count > 0,
            "MismatchCountMatchesSealedConstruction":
                mismatch_count == int(target["TargetMismatchCount"]),
            "TargetAnonymousSchemaPresentInStructuredLibrary":
                schema_tuple(target["TargetAnonymousSchema"]) in final_schema_set,
        })
    target_pass = all(
        row["TargetRelationActuallyBroken"]
        and row["MismatchCountMatchesSealedConstruction"]
        and row["TargetAnonymousSchemaPresentInStructuredLibrary"]
        for row in target_audits
    )

    structured_rows = result["StructuredResults"]
    control_rows = result["ControlResults"]
    challenge_rows = result["NearLawChallengeResults"]
    all_exact = all(
        row[mode]["FinalExact"]
        for rows in (structured_rows, control_rows, challenge_rows)
        for row in rows for mode in ("Transfer", "Baseline")
    )
    unsafe = sum(
        int(row["Transfer"]["UnsafeCommittedInferenceCount"])
        for rows in (structured_rows, control_rows, challenge_rows)
        for row in rows
    )
    structured_mq = sum(int(row["MembershipQuerySavings"]) for row in structured_rows)
    structured_logical = sum(
        int(row["LogicalInteractionCostSavings"]) for row in structured_rows
    )
    structured_concrete = sum(
        int(row["ConcreteOracleCellCostSavings"]) for row in structured_rows
    )
    control_mq = sum(int(row["MembershipQuerySavings"]) for row in control_rows)
    control_concrete = sum(
        int(row["ConcreteOracleCellCostSavings"]) for row in control_rows
    )
    challenge_mq = sum(int(row["MembershipQuerySavings"]) for row in challenge_rows)
    challenge_concrete = sum(
        int(row["ConcreteOracleCellCostSavings"]) for row in challenge_rows
    )
    family_positive = {
        family: any(
            row["Family"] == family
            and int(row["LibraryBeforeCount"]) > 0
            and int(row["MembershipQuerySavings"]) > 0
            for row in structured_rows
        )
        for family in manifest["GeneratorFamilies"]
    }
    positive_family_count = sum(family_positive.values())
    family_labels_pass = all(
        row["Family"] == expected["Family"]
        for row, expected in zip(
            structured_rows, manifest["StructuredWorldSpecifications"]
        )
    )
    starting_empty = (
        int(structured_rows[0]["LibraryBeforeCount"]) == 0
        and int(control_rows[0]["LibraryBeforeCount"]) == 0
    )
    prior_used = any(
        int(row["LibraryBeforeCount"]) > 0
        and int(row["Transfer"]["FinalInferredTransitionCount"]) > 0
        for row in structured_rows
    )
    near_law_exact = all(
        row[mode]["FinalExact"]
        for row in challenge_rows for mode in ("Transfer", "Baseline")
    )
    expected_main_gate = (
        starting_empty and all_exact and unsafe == 0
        and len(structured_library) > 0 and prior_used
        and positive_family_count >= 3
        and structured_mq > 0 and structured_concrete > 0
        and structured_concrete > control_concrete and near_law_exact
    )
    aggregate_pass = (
        int(result["AggregateStructuredMembershipQuerySavings"]) == structured_mq
        and int(result["AggregateStructuredLogicalInteractionCostSavings"])
        == structured_logical
        and int(result["AggregateStructuredConcreteOracleCellCostSavings"])
        == structured_concrete
        and int(result["AggregateControlMembershipQuerySavings"]) == control_mq
        and int(result["AggregateControlConcreteOracleCellCostSavings"])
        == control_concrete
        and int(result["AggregateNearLawMembershipQuerySavings"]) == challenge_mq
        and int(result["AggregateNearLawConcreteOracleCellCostSavings"])
        == challenge_concrete
        and int(result["PositiveSavingsFamilyCount"]) == positive_family_count
        and result["PositiveSavingsFamilyCoverage"] == family_positive
    )
    boundary_pass = (
        result["FreshWorldsMaterializedAfterProtocolFreeze"] is True
        and int(result["StartingConceptLibraryCount"]) == 0
        and int(result["PreloadedK4ASchemaCount"]) == 0
        and int(result["MaximumConceptWordLength"]) == 4
        and result["CanonicalTCCTModified"] is False
        and result["FrozenK3BAndK4ALearnerModified"] is False
        and result["GeneratorTruthReadByLearner"] is False
        and result["OpenEndedPrimitiveOrLanguageInventionProven"] is False
        and result["ObservationNoiseRobustnessProven"] is False
        and result["WorldSizeUnknownToLearner"] is False
    )
    main_gate_consistency_pass = bool(result["MainGatePass"]) == expected_main_gate
    evidence_integrity = (
        source_hash_pass and phase_pass and sequence_shape_pass
        and rank_match_pass and family_labels_pass
        and structured_pass and control_pass and challenge_pass
        and library_pass and aggregate_pass and boundary_pass
        and main_gate_consistency_pass
    )
    independent_gate = relabel_pass and target_pass
    final_gate = evidence_integrity and expected_main_gate and independent_gate
    conclusion = (
        "VERIFIED_FRESH_OUT_OF_FAMILY_BOUNDED_CONCEPT_TRANSFER_GATE_PASS"
        if final_gate else
        "EVIDENCE_VALID_BUT_OUT_OF_FAMILY_GATE_NOT_PASSED"
        if evidence_integrity else "VERIFICATION_FAILED"
    )
    return {
        "Stage": "S132-K4B independent reconstruction and sealed audit",
        "SourceHashPass": source_hash_pass,
        "FreezeMaterializationOrderPass": phase_pass,
        "SequenceShapeAndOrderPass": sequence_shape_pass,
        "RankMatchedControlPass": rank_match_pass,
        "FamilyLabelsPass": family_labels_pass,
        "StructuredAudits": structured_audits,
        "ControlAudits": control_audits,
        "NearLawReconstructionAudits": challenge_audits,
        "StructuredReconstructionPass": structured_pass,
        "ControlReconstructionPass": control_pass,
        "NearLawReconstructionPass": challenge_pass,
        "FinalLibraryReconstructionPass": library_pass,
        "StateRelabelAudits": relabel_audits,
        "StateRelabelDiscoveryInvariancePass": relabel_pass,
        "NearLawTargetAudits": target_audits,
        "NearLawTargetsBrokenAndRepresentedPass": target_pass,
        "AggregateArithmeticPass": aggregate_pass,
        "ClaimBoundaryPass": boundary_pass,
        "ExpectedMainGatePass": expected_main_gate,
        "MainGateConsistencyPass": main_gate_consistency_pass,
        "IndependentOnlyGatePass": independent_gate,
        "EvidenceIntegrityPass": evidence_integrity,
        "FinalGatePass": final_gate,
        "FinalConclusion": conclusion,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    result = verify(package)
    output = package / "verification" / "S132K4B_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
