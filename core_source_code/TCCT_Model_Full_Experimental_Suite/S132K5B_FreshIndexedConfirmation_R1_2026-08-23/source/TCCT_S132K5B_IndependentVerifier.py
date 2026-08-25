"""Independent Python replay for S132-K5B fresh paired confirmation."""

from __future__ import annotations

import argparse
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


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compare_rebuilt(rebuilt: dict[str, Any], reported: dict[str, Any]) -> list[str]:
    return [key for key, value in rebuilt.items() if reported.get(key) != value]


def paired_original_match(indexed: dict[str, Any], full: dict[str, Any]) -> bool:
    return all(key in indexed and indexed[key] == value for key, value in full.items())


def schema_key(record: dict[str, Any]):
    long, short = record["Schema"]
    return tuple(long), tuple(short)


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K5B_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K5B_freeze_receipt.json"
    public_path = package / "input" / "S132K5B_public_input.json"
    oracle_path = package / "oracle" / "S132K5B_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K5B_generator_truth.json"
    result_path = package / "results" / "S132K5B_result.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))

    k3 = load_module(
        package / "source" / "TCCT_S132K3B_IndependentVerifier.py",
        "s132k5b_k3",
    )
    k4 = load_module(
        package / "source" / "TCCT_S132K4A_IndependentVerifier.py",
        "s132k5b_k4",
    )
    k5 = load_module(
        package / "source" / "TCCT_S132K5A_IndependentVerifier.py",
        "s132k5b_k5",
    )

    current_source_hashes = {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir())
        if path.is_file()
    }
    source_hash_pass = current_source_hashes == manifest["SourceHashes"]
    manifest_hash_pass = sha256(manifest_path) == receipt["ManifestSHA256"]
    materialization_hash_pass = (
        sha256(public_path) == receipt["PublicInputSHA256"]
        and sha256(oracle_path) == receipt["OracleSHA256"]
        and sha256(truth_path) == receipt["SealedTruthSHA256"]
    )
    freeze_order_pass = (
        manifest["FrozenBeforeWorldMaterialization"] is True
        and receipt["WorldsMaterialized"] is True
        and receipt["MaterializedAfterManifestFreeze"] is True
    )
    forbidden_public_fields = {"TransitionTable", "GeneratorParameters", "Seed", "Family"}
    public_separation_pass = all(
        not (forbidden_public_fields & set(world)) for world in public["Worlds"]
    )

    initial = float(manifest["InitialDirectObservationFraction"])
    batch = float(manifest["DirectQueryBatchFraction"])
    witnesses = int(manifest["MinimumDirectPositiveWitnessesBeforeInference"])
    maximum = int(manifest["MaximumConceptWordLength"])

    def reconstruct_stream(worlds, rows):
        library: dict[Any, dict[str, Any]] = {}
        next_id = 0
        audits = []
        for world, row in zip(worlds, rows):
            available = sorted(library.values(), key=lambda record: record["SchemaID"])
            indexed_report = row["IndexedTransfer"]
            full_report = row["FullScanTransfer"]
            baseline_report = row["Baseline"]
            indexed = k5.replay_indexed(
                k3, world["TransitionTable"], available,
                indexed_report["QueryOrder"], True,
                initial, batch, witnesses,
            )
            full = k3.replay(
                world["TransitionTable"], available,
                full_report["QueryOrder"], True,
                initial, batch, witnesses,
            )
            baseline = k3.replay(
                world["TransitionTable"], [],
                baseline_report["QueryOrder"], False,
                initial, batch, witnesses,
            )
            indexed_mismatch = compare_rebuilt(indexed, indexed_report)
            full_mismatch = compare_rebuilt(full, full_report)
            baseline_mismatch = compare_rebuilt(baseline, baseline_report)
            discovered = k4.discover(world["TransitionTable"], maximum)
            before = len(available)
            next_id, new_count = k4.update_library(
                library, next_id, discovered, world["WorldID"]
            )
            query_order_match = (
                indexed_report["QueryOrder"] == full_report["QueryOrder"]
                == baseline_report["QueryOrder"]
            )
            savings_match = (
                row["MembershipQuerySavings"]
                == baseline_report["MembershipQueries"] - indexed_report["MembershipQueries"]
                and row["LogicalInteractionCostSavings"]
                == baseline_report["LogicalInteractionCost"] - indexed_report["LogicalInteractionCost"]
                and row["ConcreteOracleCellCostSavings"]
                == baseline_report["ConcreteOracleCellCost"] - indexed_report["ConcreteOracleCellCost"]
            )
            row_library_match = (
                row["LibraryBeforeCount"] == before
                and row["SchemasDiscoveredThisWorld"] == len(discovered)
                and row["NewSchemaCount"] == new_count
                and row["LibraryAfterCount"] == len(library)
            )
            pair_match = paired_original_match(indexed_report, full_report)
            audits.append({
                "WorldID": world["WorldID"],
                "IndexedReconstructionPass": not indexed_mismatch,
                "IndexedMismatchFields": indexed_mismatch,
                "FullScanReconstructionPass": not full_mismatch,
                "FullScanMismatchFields": full_mismatch,
                "BaselineReconstructionPass": not baseline_mismatch,
                "BaselineMismatchFields": baseline_mismatch,
                "QueryOrdersIdentical": query_order_match,
                "PairedOriginalFieldsExactlyEqual": pair_match,
                "ReportedPairFlagCorrect": row["PairedOriginalFieldsExactlyEqual"] == pair_match,
                "LibraryTrajectoryPass": row_library_match,
                "SavingsArithmeticPass": savings_match,
            })
        final_library = sorted(library.values(), key=lambda record: record["SchemaID"])
        return audits, final_library

    structured_audits, structured_library = reconstruct_stream(
        oracle["StructuredWorlds"], result["StructuredResults"]
    )
    control_audits, control_library = reconstruct_stream(
        oracle["RankMatchedControls"], result["ControlResults"]
    )

    challenge_audits = []
    for world, row in zip(
        oracle["NearLawChallenges"], result["NearLawChallengeResults"]
    ):
        indexed_report = row["IndexedTransfer"]
        full_report = row["FullScanTransfer"]
        baseline_report = row["Baseline"]
        indexed = k5.replay_indexed(
            k3, world["TransitionTable"], structured_library,
            indexed_report["QueryOrder"], True,
            initial, batch, witnesses,
        )
        full = k3.replay(
            world["TransitionTable"], structured_library,
            full_report["QueryOrder"], True,
            initial, batch, witnesses,
        )
        baseline = k3.replay(
            world["TransitionTable"], [], baseline_report["QueryOrder"], False,
            initial, batch, witnesses,
        )
        indexed_mismatch = compare_rebuilt(indexed, indexed_report)
        full_mismatch = compare_rebuilt(full, full_report)
        baseline_mismatch = compare_rebuilt(baseline, baseline_report)
        pair_match = paired_original_match(indexed_report, full_report)
        query_order_match = (
            indexed_report["QueryOrder"] == full_report["QueryOrder"]
            == baseline_report["QueryOrder"]
        )
        savings_match = (
            row["MembershipQuerySavings"]
            == baseline_report["MembershipQueries"] - indexed_report["MembershipQueries"]
            and row["LogicalInteractionCostSavings"]
            == baseline_report["LogicalInteractionCost"] - indexed_report["LogicalInteractionCost"]
            and row["ConcreteOracleCellCostSavings"]
            == baseline_report["ConcreteOracleCellCost"] - indexed_report["ConcreteOracleCellCost"]
        )
        challenge_audits.append({
            "WorldID": world["WorldID"],
            "IndexedReconstructionPass": not indexed_mismatch,
            "IndexedMismatchFields": indexed_mismatch,
            "FullScanReconstructionPass": not full_mismatch,
            "FullScanMismatchFields": full_mismatch,
            "BaselineReconstructionPass": not baseline_mismatch,
            "BaselineMismatchFields": baseline_mismatch,
            "QueryOrdersIdentical": query_order_match,
            "PairedOriginalFieldsExactlyEqual": pair_match,
            "ReportedPairFlagCorrect": row["PairedOriginalFieldsExactlyEqual"] == pair_match,
            "AvailableLibraryCountPass": row["AvailableStructuredConceptCount"] == len(structured_library),
            "SavingsArithmeticPass": savings_match,
        })

    all_audits = structured_audits + control_audits + challenge_audits
    all_reconstruction_pass = all(
        audit["IndexedReconstructionPass"]
        and audit["FullScanReconstructionPass"]
        and audit["BaselineReconstructionPass"]
        and audit["QueryOrdersIdentical"]
        and audit["PairedOriginalFieldsExactlyEqual"]
        and audit["ReportedPairFlagCorrect"]
        and audit["SavingsArithmeticPass"]
        for audit in all_audits
    )
    library_pass = (
        structured_library == result["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"]
        and all(audit["LibraryTrajectoryPass"] for audit in structured_audits + control_audits)
        and all(audit["AvailableLibraryCountPass"] for audit in challenge_audits)
    )

    rank_audits = []
    for target, control in zip(
        oracle["StructuredWorlds"], oracle["RankMatchedControls"]
    ):
        target_ranks = k4.action_ranks(target["TransitionTable"])
        control_ranks = k4.action_ranks(control["TransitionTable"])
        rank_audits.append({
            "WorldID": target["WorldID"],
            "TargetRanks": target_ranks,
            "ControlRanks": control_ranks,
            "Pass": target_ranks == control_ranks
            == control["TargetActionImageRanks"]
            == control["ControlActionImageRanks"],
        })
    rank_match_pass = all(row["Pass"] for row in rank_audits)

    relabel_audits = []
    for world, hidden in zip(
        oracle["StructuredWorlds"], truth["StructuredWorlds"]
    ):
        original = k4.discover(world["TransitionTable"], maximum)
        alternate = k4.discover(hidden["AlternateRelabeledTransitionTable"], maximum)
        relabel_audits.append({
            "WorldID": world["WorldID"],
            "OriginalSchemaCount": len(original),
            "AlternateSchemaCount": len(alternate),
            "Pass": original == alternate,
        })
    relabel_pass = all(row["Pass"] for row in relabel_audits)

    library_keys = {schema_key(record) for record in structured_library}
    near_target_audits = []
    for world, hidden in zip(
        oracle["NearLawChallenges"], truth["NearLawChallenges"]
    ):
        long = tuple(hidden["TargetLong"])
        short = tuple(hidden["TargetShort"])
        anonymous = tuple(tuple(word) for word in hidden["TargetAnonymousSchema"])
        left = k4.transform(world["TransitionTable"], long)
        right = k4.transform(world["TransitionTable"], short)
        mismatch_count = sum(a != b for a, b in zip(left, right))
        near_target_audits.append({
            "WorldID": world["WorldID"],
            "TargetBroken": mismatch_count > 0,
            "MismatchCount": mismatch_count,
            "ReportedMismatchCountMatch": mismatch_count == hidden["TargetMismatchCount"],
            "TargetRepresentedInStructuredLibrary": anonymous in library_keys,
        })
    near_targets_broken = all(
        row["TargetBroken"] and row["ReportedMismatchCountMatch"]
        for row in near_target_audits
    )
    near_targets_represented = all(
        row["TargetRepresentedInStructuredLibrary"] for row in near_target_audits
    )

    all_rows = (
        result["StructuredResults"]
        + result["ControlResults"]
        + result["NearLawChallengeResults"]
    )
    all_pair_match = all(row["PairedOriginalFieldsExactlyEqual"] for row in all_rows)
    all_exact = all(
        row[label]["FinalExact"]
        for row in all_rows
        for label in ("IndexedTransfer", "FullScanTransfer", "Baseline")
    )
    unsafe_count = sum(
        row[label]["UnsafeCommittedInferenceCount"]
        for row in all_rows
        for label in ("IndexedTransfer", "FullScanTransfer", "Baseline")
    )
    actual_eval = sum(
        row["IndexedTransfer"]["ActualIndexedClosureItemEvaluations"]
        for row in all_rows
    )
    full_equivalent_eval = sum(
        row["IndexedTransfer"]["FullScanEquivalentClosureItemEvaluations"]
        for row in all_rows
    )
    actual_direct = sum(
        row["IndexedTransfer"]["ActualDirectAuditStateChecks"]
        for row in all_rows
    )
    full_direct = sum(
        row["IndexedTransfer"]["FullRescanEquivalentDirectAuditStateChecks"]
        for row in all_rows
    )
    deterministic_reduction = actual_eval < full_equivalent_eval and actual_direct <= full_direct
    indexed_runtime = sum(float(row["IndexedRuntimeSeconds"]) for row in all_rows)
    full_runtime = sum(float(row["FullScanRuntimeSeconds"]) for row in all_rows)
    baseline_runtime = sum(float(row["BaselineRuntimeSeconds"]) for row in all_rows)
    runtime_improved = indexed_runtime < full_runtime

    structured_rows = result["StructuredResults"]
    control_rows = result["ControlResults"]
    challenge_rows = result["NearLawChallengeResults"]
    families = manifest["GeneratorFamilies"]
    family_positive = {
        family: any(
            row["Family"] == family
            and row["LibraryBeforeCount"] > 0
            and row["MembershipQuerySavings"] > 0
            for row in structured_rows
        )
        for family in families
    }
    positive_family_count = sum(family_positive.values())
    structured_mq = sum(row["MembershipQuerySavings"] for row in structured_rows)
    structured_logical = sum(row["LogicalInteractionCostSavings"] for row in structured_rows)
    structured_concrete = sum(row["ConcreteOracleCellCostSavings"] for row in structured_rows)
    control_mq = sum(row["MembershipQuerySavings"] for row in control_rows)
    control_concrete = sum(row["ConcreteOracleCellCostSavings"] for row in control_rows)
    challenge_mq = sum(row["MembershipQuerySavings"] for row in challenge_rows)
    challenge_concrete = sum(row["ConcreteOracleCellCostSavings"] for row in challenge_rows)
    prior_used = any(
        row["LibraryBeforeCount"] > 0
        and row["IndexedTransfer"]["FinalInferredTransitionCount"] > 0
        for row in structured_rows
    )
    starting_empty = (
        structured_rows[0]["LibraryBeforeCount"] == 0
        and control_rows[0]["LibraryBeforeCount"] == 0
    )
    near_exact = all(
        row[label]["FinalExact"]
        for row in challenge_rows
        for label in ("IndexedTransfer", "FullScanTransfer", "Baseline")
    )
    transfer_gate = (
        starting_empty and len(structured_library) > 0 and prior_used
        and positive_family_count >= 3 and structured_mq > 0
        and structured_concrete > 0
        and structured_concrete > control_concrete
    )
    recomputed_main_gate = (
        all_pair_match and all_exact and unsafe_count == 0
        and deterministic_reduction and runtime_improved
        and transfer_gate and near_exact
    )

    aggregate_checks = {
        "PairedOriginalFieldsExactlyEqual": result["PairedOriginalFieldsExactlyEqual"] == all_pair_match,
        "AllFinalModelsExact": result["AllFinalModelsExact"] == all_exact,
        "UnsafeCommittedInferenceCount": result["UnsafeCommittedInferenceCount"] == unsafe_count,
        "ActualIndexedClosureItemEvaluations": result["ActualIndexedClosureItemEvaluations"] == actual_eval,
        "FullScanEquivalentClosureItemEvaluations": result["FullScanEquivalentClosureItemEvaluations"] == full_equivalent_eval,
        "ActualDirectAuditStateChecks": result["ActualDirectAuditStateChecks"] == actual_direct,
        "FullRescanEquivalentDirectAuditStateChecks": result["FullRescanEquivalentDirectAuditStateChecks"] == full_direct,
        "DeterministicWorkReduced": result["DeterministicWorkReduced"] == deterministic_reduction,
        "AggregateIndexedRuntimeSeconds": abs(float(result["AggregateIndexedRuntimeSeconds"]) - indexed_runtime) < 1e-8,
        "AggregateFullScanRuntimeSeconds": abs(float(result["AggregateFullScanRuntimeSeconds"]) - full_runtime) < 1e-8,
        "AggregateBaselineRuntimeSeconds": abs(float(result["AggregateBaselineRuntimeSeconds"]) - baseline_runtime) < 1e-8,
        "IndexedRuntimeStrictlyLower": result["IndexedRuntimeStrictlyLower"] == runtime_improved,
        "PositiveSavingsFamilyCoverage": result["PositiveSavingsFamilyCoverage"] == family_positive,
        "PositiveSavingsFamilyCount": result["PositiveSavingsFamilyCount"] == positive_family_count,
        "AggregateStructuredMembershipQuerySavings": result["AggregateStructuredMembershipQuerySavings"] == structured_mq,
        "AggregateStructuredLogicalInteractionCostSavings": result["AggregateStructuredLogicalInteractionCostSavings"] == structured_logical,
        "AggregateStructuredConcreteOracleCellCostSavings": result["AggregateStructuredConcreteOracleCellCostSavings"] == structured_concrete,
        "AggregateControlMembershipQuerySavings": result["AggregateControlMembershipQuerySavings"] == control_mq,
        "AggregateControlConcreteOracleCellCostSavings": result["AggregateControlConcreteOracleCellCostSavings"] == control_concrete,
        "AggregateNearLawMembershipQuerySavings": result["AggregateNearLawMembershipQuerySavings"] == challenge_mq,
        "AggregateNearLawConcreteOracleCellCostSavings": result["AggregateNearLawConcreteOracleCellCostSavings"] == challenge_concrete,
        "FreshStructuredTransferGatePass": result["FreshStructuredTransferGatePass"] == transfer_gate,
        "AllNearLawChallengesExact": result["AllNearLawChallengesExact"] == near_exact,
        "MainGatePass": result["MainGatePass"] == recomputed_main_gate,
    }
    aggregate_pass = all(aggregate_checks.values())

    evidence_integrity_pass = (
        source_hash_pass and manifest_hash_pass and materialization_hash_pass
        and freeze_order_pass and public_separation_pass and rank_match_pass
        and all_reconstruction_pass and library_pass and aggregate_pass
    )
    independent_scientific_audit_pass = (
        relabel_pass and near_targets_broken and near_targets_represented
    )
    scientific_gate_pass = (
        evidence_integrity_pass and independent_scientific_audit_pass
        and recomputed_main_gate
    )
    final_conclusion = (
        "VERIFIED_FRESH_EXACT_INDEXED_CONFIRMATION_GATE_PASS"
        if scientific_gate_pass
        else "VERIFIED_FRESH_EXACT_INDEXED_CONFIRMATION_GATE_NOT_PASSED"
    )
    verification = {
        "Stage": "S132-K5B independent paired replay and audit",
        "Profile": manifest["Profile"],
        "SourceHashPass": source_hash_pass,
        "ManifestHashPass": manifest_hash_pass,
        "MaterializationHashPass": materialization_hash_pass,
        "FreezeBeforeMaterializationPass": freeze_order_pass,
        "PublicSeparationPass": public_separation_pass,
        "RankMatchedControlPass": rank_match_pass,
        "AllPythonTraceReconstructionsExact": all_reconstruction_pass,
        "LibraryReconstructionPass": library_pass,
        "AggregateRecomputationPass": aggregate_pass,
        "StateRelabelDiscoveryInvariancePass": relabel_pass,
        "NearLawTargetsBrokenPass": near_targets_broken,
        "NearLawTargetsRepresentedInStructuredLibraryPass": near_targets_represented,
        "RecomputedMainGatePass": recomputed_main_gate,
        "EvidenceIntegrityPass": evidence_integrity_pass,
        "IndependentScientificAuditPass": independent_scientific_audit_pass,
        "ScientificGatePass": scientific_gate_pass,
        "StructuredReconstructionAudits": structured_audits,
        "ControlReconstructionAudits": control_audits,
        "NearLawReconstructionAudits": challenge_audits,
        "RankAudits": rank_audits,
        "StateRelabelAudits": relabel_audits,
        "NearLawTargetAudits": near_target_audits,
        "AggregateChecks": aggregate_checks,
        "RecomputedMetrics": {
            "ActualIndexedClosureItemEvaluations": actual_eval,
            "FullScanEquivalentClosureItemEvaluations": full_equivalent_eval,
            "AggregateIndexedRuntimeSeconds": indexed_runtime,
            "AggregateFullScanRuntimeSeconds": full_runtime,
            "PairedRuntimeSpeedup": full_runtime / indexed_runtime if indexed_runtime else 0.0,
            "AggregateStructuredMembershipQuerySavings": structured_mq,
            "AggregateStructuredConcreteOracleCellCostSavings": structured_concrete,
            "AggregateControlConcreteOracleCellCostSavings": control_concrete,
            "PositiveSavingsFamilyCount": positive_family_count,
        },
        "CanonicalTCCTModified": False,
        "OpenEndedLanguageInventionProven": False,
        "FinalConclusion": final_conclusion,
    }
    dump(
        package / "verification" / "S132K5B_independent_verification.json",
        verification,
    )
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    verification = verify(args.package.resolve())
    print(json.dumps({
        "EvidenceIntegrityPass": verification["EvidenceIntegrityPass"],
        "ScientificGatePass": verification["ScientificGatePass"],
        "FinalConclusion": verification["FinalConclusion"],
    }, ensure_ascii=False))
    raise SystemExit(0 if verification["EvidenceIntegrityPass"] else 1)


if __name__ == "__main__":
    main()
