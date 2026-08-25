"""Independent replay and protocol audit for fresh S132-K6F."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def hashes(folder: Path) -> dict[str, str]:
    return {path.name: sha256(path) for path in sorted(folder.iterdir()) if path.is_file()}


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def schema_key(record: dict[str, Any]):
    long, short = record["Schema"]
    return tuple(long), tuple(short)


def cache_accounting(report: dict[str, Any]) -> bool:
    logical = report["LogicalTraceRequestCount"]
    return (
        logical == 2 * report["ActualPersistentDirectAuditItemEvaluations"]
        and report["ExactWordCacheHitCount"]
        + report["PhysicalTraceEvaluationCount"] == logical
        and report["PhysicalTraceCellLookupCount"]
        <= report["ActualPersistentDirectAuditTraceCellLookups"]
        and report["AllExactWordCacheArraysPacked"] is True
    )


def verify(package: Path) -> dict[str, Any]:
    protocol = package / "protocol"
    source = package / "source"
    manifest_path = protocol / "S132K6F_pre_world_manifest.json"
    receipt_path = protocol / "S132K6F_freeze_receipt.json"
    public_path = package / "input" / "S132K6F_public_input.json"
    oracle_path = package / "oracle" / "S132K6F_oracle_sequences.json"
    truth_path = package / "sealed" / "S132K6F_generator_truth.json"
    result_path = package / "results" / "S132K6F_result.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))

    k3 = load_module(source / "TCCT_S132K3B_IndependentVerifier.py", "k6f_k3")
    k4 = load_module(source / "TCCT_S132K4A_IndependentVerifier.py", "k6f_k4")
    k5 = load_module(source / "TCCT_S132K5A_IndependentVerifier.py", "k6f_k5")
    k6 = load_module(source / "TCCT_S132K6B_IndependentVerifier.py", "k6f_k6")

    source_hash_pass = hashes(source) == manifest["SourceHashes"]
    accepted_input_hash_pass = all(
        sha256(package / "input" / name) == digest
        for name, digest in manifest["InputHashes"].items()
    )
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
    forbidden = {"TransitionTable", "GeneratorParameters", "Seed", "Family"}
    public_separation_pass = all(not (forbidden & set(world)) for world in public["Worlds"])
    k6e_hash = sha256(source / "TCCT_S132K6E_ExactWordCachePatch.wl")
    accepted_k6e_source_pass = (
        k6e_hash == manifest["AcceptedK6ESourceSHA256"]
        == result["AcceptedK6ESourceSHA256"]
        and result["AcceptedK6ESourceHashMatch"] is True
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
            e_report, b_report, five_report = row["K6E"], row["K6B"], row["K5A"]
            same_order = e_report["QueryOrder"] == b_report["QueryOrder"] == five_report["QueryOrder"]
            rebuilt_b = k6.replay_persistent(
                k3, k5, world["TransitionTable"], available,
                b_report["QueryOrder"], True, initial, batch, witnesses,
            )
            rebuilt_5 = k5.replay_indexed(
                k3, world["TransitionTable"], available,
                five_report["QueryOrder"], True, initial, batch, witnesses,
            )
            e_mismatch = k6.common_report_mismatches(rebuilt_b, e_report)
            b_mismatch = k6.common_report_mismatches(rebuilt_b, b_report)
            five_mismatch = k6.common_report_mismatches(rebuilt_5, five_report)
            paired_mismatch = k6.mapped_k5_mismatches(rebuilt_b, rebuilt_5)
            discovered = k4.discover(world["TransitionTable"], maximum)
            before = len(available)
            next_id, new_count = k4.update_library(
                library, next_id, discovered, world["WorldID"]
            )
            library_ok = (
                row["LibraryBeforeCount"] == before
                and row["SchemasDiscoveredThisWorld"] == len(discovered)
                and row["NewSchemaCount"] == new_count
                and row["LibraryAfterCount"] == len(library)
            )
            functional = not e_mismatch and not b_mismatch and not five_mismatch and not paired_mismatch
            audits.append({
                "WorldID": world["WorldID"],
                "K6EReconstructionPass": not e_mismatch,
                "K6EMismatchFields": e_mismatch,
                "K6BReconstructionPass": not b_mismatch,
                "K6BMismatchFields": b_mismatch,
                "K5AReconstructionPass": not five_mismatch,
                "K5AMismatchFields": five_mismatch,
                "TripleFunctionalMatch": functional,
                "ReportedTripleFlagsCorrect": (
                    row["K6EK5AFieldMatch"] == functional
                    and row["K6BK5AFieldMatch"] == functional
                    and row["K6EK6BBehaviorMatch"] == functional
                ),
                "QueryOrdersIdentical": same_order,
                "CacheAccountingPass": cache_accounting(e_report),
                "LibraryTrajectoryPass": library_ok,
            })
        return audits, sorted(library.values(), key=lambda record: record["SchemaID"])

    structured_audits, structured_library = reconstruct_stream(
        oracle["StructuredWorlds"], result["StructuredResults"]
    )
    control_audits, control_library = reconstruct_stream(
        oracle["RankMatchedControls"], result["ControlResults"]
    )

    challenge_audits = []
    for world, row in zip(oracle["NearLawChallenges"], result["NearLawChallengeResults"]):
        e_report, b_report, five_report = row["K6E"], row["K6B"], row["K5A"]
        rebuilt_b = k6.replay_persistent(
            k3, k5, world["TransitionTable"], structured_library,
            b_report["QueryOrder"], True, initial, batch, witnesses,
        )
        rebuilt_5 = k5.replay_indexed(
            k3, world["TransitionTable"], structured_library,
            five_report["QueryOrder"], True, initial, batch, witnesses,
        )
        e_mismatch = k6.common_report_mismatches(rebuilt_b, e_report)
        b_mismatch = k6.common_report_mismatches(rebuilt_b, b_report)
        five_mismatch = k6.common_report_mismatches(rebuilt_5, five_report)
        paired_mismatch = k6.mapped_k5_mismatches(rebuilt_b, rebuilt_5)
        functional = not e_mismatch and not b_mismatch and not five_mismatch and not paired_mismatch
        challenge_audits.append({
            "WorldID": world["WorldID"],
            "TripleFunctionalMatch": functional,
            "K6EMismatchFields": e_mismatch,
            "K6BMismatchFields": b_mismatch,
            "K5AMismatchFields": five_mismatch,
            "ReportedTripleFlagsCorrect": (
                row["K6EK5AFieldMatch"] == functional
                and row["K6BK5AFieldMatch"] == functional
                and row["K6EK6BBehaviorMatch"] == functional
            ),
            "QueryOrdersIdentical": e_report["QueryOrder"] == b_report["QueryOrder"] == five_report["QueryOrder"],
            "CacheAccountingPass": cache_accounting(e_report),
            "AvailableLibraryCountPass": row["AvailableStructuredConceptCount"] == len(structured_library),
        })

    all_audits = structured_audits + control_audits + challenge_audits
    all_reconstruction_pass = all(
        row["TripleFunctionalMatch"]
        and row["ReportedTripleFlagsCorrect"]
        and row["QueryOrdersIdentical"]
        and row["CacheAccountingPass"]
        for row in all_audits
    )
    library_pass = (
        structured_library == result["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"]
        and all(row["LibraryTrajectoryPass"] for row in structured_audits + control_audits)
        and all(row["AvailableLibraryCountPass"] for row in challenge_audits)
    )

    rank_audits = []
    for target, control in zip(oracle["StructuredWorlds"], oracle["RankMatchedControls"]):
        target_ranks = k4.action_ranks(target["TransitionTable"])
        control_ranks = k4.action_ranks(control["TransitionTable"])
        passed = target_ranks == control_ranks == control["TargetActionImageRanks"] == control["ControlActionImageRanks"]
        rank_audits.append({"WorldID": target["WorldID"], "Pass": passed})
    rank_match_pass = all(row["Pass"] for row in rank_audits)

    relabel_audits = []
    for world, hidden in zip(oracle["StructuredWorlds"], truth["StructuredWorlds"]):
        original = k4.discover(world["TransitionTable"], maximum)
        alternate = k4.discover(hidden["AlternateRelabeledTransitionTable"], maximum)
        relabel_audits.append({
            "WorldID": world["WorldID"], "OriginalSchemaCount": len(original),
            "AlternateSchemaCount": len(alternate), "Pass": original == alternate,
        })
    relabel_pass = all(row["Pass"] for row in relabel_audits)

    library_keys = {schema_key(record) for record in structured_library}
    near_audits = []
    for world, hidden in zip(oracle["NearLawChallenges"], truth["NearLawChallenges"]):
        left = k4.transform(world["TransitionTable"], tuple(hidden["TargetLong"]))
        right = k4.transform(world["TransitionTable"], tuple(hidden["TargetShort"]))
        mismatch_count = sum(a != b for a, b in zip(left, right))
        anonymous = tuple(tuple(word) for word in hidden["TargetAnonymousSchema"])
        near_audits.append({
            "WorldID": world["WorldID"], "TargetBroken": mismatch_count > 0,
            "MismatchCountPass": mismatch_count == hidden["TargetMismatchCount"],
            "TargetRepresented": anonymous in library_keys,
        })
    near_scientific_pass = all(
        row["TargetBroken"] and row["MismatchCountPass"] and row["TargetRepresented"]
        for row in near_audits
    )

    all_rows = result["StructuredResults"] + result["ControlResults"] + result["NearLawChallengeResults"]
    e_rows = [row["K6E"] for row in all_rows]
    b_rows = [row["K6B"] for row in all_rows]
    five_rows = [row["K5A"] for row in all_rows]
    all_triple = all(
        row["K6EK5AFieldMatch"] and row["K6BK5AFieldMatch"] and row["K6EK6BBehaviorMatch"]
        for row in all_rows
    )
    all_exact = all(report["FinalExact"] for report in e_rows + b_rows + five_rows)
    unsafe = sum(report["UnsafeCommittedInferenceCount"] for report in e_rows + b_rows + five_rows)
    logical_requests = sum(row["LogicalTraceRequestCount"] for row in e_rows)
    hits = sum(row["ExactWordCacheHitCount"] for row in e_rows)
    physical_evaluations = sum(row["PhysicalTraceEvaluationCount"] for row in e_rows)
    logical_lookups = sum(row["ActualPersistentDirectAuditTraceCellLookups"] for row in e_rows)
    physical_lookups = sum(row["PhysicalTraceCellLookupCount"] for row in e_rows)
    cache_pass = all(cache_accounting(row) for row in e_rows)
    cache_exercised = logical_requests > 0 and hits > 0 and physical_evaluations < logical_requests
    physical_reduced = physical_lookups < logical_lookups
    arrays_packed = all(row["AllNumericAuditArraysPacked"] and row["AllExactWordCacheArraysPacked"] for row in e_rows) and all(row["AllNumericAuditArraysPacked"] for row in b_rows)
    e_runtime = sum(float(row["K6ERuntimeSeconds"]) for row in all_rows)
    b_runtime = sum(float(row["K6BRuntimeSeconds"]) for row in all_rows)
    five_runtime = sum(float(row["K5ARuntimeSeconds"]) for row in all_rows)
    faster_b, faster_five = e_runtime < b_runtime, e_runtime < five_runtime
    prior_used = any(row["PriorCreatedConceptUsed"] for row in result["StructuredResults"])
    starting_empty = result["StructuredResults"][0]["LibraryBeforeCount"] == 0 and result["ControlResults"][0]["LibraryBeforeCount"] == 0
    near_exact = all(report["FinalExact"] for row in result["NearLawChallengeResults"] for report in (row["K6E"], row["K6B"], row["K5A"]))
    recomputed_main_gate = (
        accepted_k6e_source_pass and starting_empty and len(structured_library) > 0
        and prior_used and all_triple and all_exact and unsafe == 0 and cache_pass
        and physical_reduced and cache_exercised and arrays_packed
        and faster_b and faster_five and near_exact
    )

    aggregate_checks = {
        "AllK6EK6BK5AFieldsExactlyEqual": result["AllK6EK6BK5AFieldsExactlyEqual"] == all_triple,
        "AllFinalModelsExact": result["AllFinalModelsExact"] == all_exact,
        "UnsafeCommittedInferenceCount": result["UnsafeCommittedInferenceCount"] == unsafe,
        "CacheAccountingConservationPass": result["CacheAccountingConservationPass"] == cache_pass,
        "LogicalTraceRequestCount": result["LogicalTraceRequestCount"] == logical_requests,
        "ExactWordCacheHitCount": result["ExactWordCacheHitCount"] == hits,
        "PhysicalTraceEvaluationCount": result["PhysicalTraceEvaluationCount"] == physical_evaluations,
        "LogicalTraceCellLookupCount": result["LogicalTraceCellLookupCount"] == logical_lookups,
        "PhysicalTraceCellLookupCount": result["PhysicalTraceCellLookupCount"] == physical_lookups,
        "AggregateK6ERuntimeSeconds": abs(float(result["AggregateK6ERuntimeSeconds"]) - e_runtime) < 1e-8,
        "AggregateK6BRuntimeSeconds": abs(float(result["AggregateK6BRuntimeSeconds"]) - b_runtime) < 1e-8,
        "AggregateK5ARuntimeSeconds": abs(float(result["AggregateK5ARuntimeSeconds"]) - five_runtime) < 1e-8,
        "RuntimeGates": result["K6ERuntimeStrictlyLowerThanK6B"] == faster_b and result["K6ERuntimeStrictlyLowerThanK5A"] == faster_five,
        "FinalLibraries": result["FinalStructuredLibraryCount"] == len(structured_library) and result["FinalControlLibraryCount"] == len(control_library),
        "MainGatePass": result["MainGatePass"] == recomputed_main_gate,
    }
    aggregate_pass = all(aggregate_checks.values())

    evidence_integrity_pass = (
        source_hash_pass and accepted_input_hash_pass and manifest_hash_pass
        and materialization_hash_pass and freeze_order_pass and public_separation_pass
        and accepted_k6e_source_pass and rank_match_pass and all_reconstruction_pass
        and library_pass and aggregate_pass
    )
    independent_scientific_pass = relabel_pass and near_scientific_pass
    scientific_gate_pass = evidence_integrity_pass and independent_scientific_pass and recomputed_main_gate
    conclusion = (
        "VERIFIED_FRESH_EXACT_WORD_CACHE_CONFIRMATION_GATE_PASS"
        if scientific_gate_pass
        else "VERIFIED_FRESH_EXACT_WORD_CACHE_CONFIRMATION_GATE_NOT_PASSED"
    )
    verification = {
        "Stage": "S132-K6F independent fresh replay and protocol audit",
        "SourceHashPass": source_hash_pass,
        "AcceptedInputHashPass": accepted_input_hash_pass,
        "ManifestHashPass": manifest_hash_pass,
        "MaterializationHashPass": materialization_hash_pass,
        "FreezeBeforeMaterializationPass": freeze_order_pass,
        "PublicSeparationPass": public_separation_pass,
        "AcceptedK6ESourceHashPass": accepted_k6e_source_pass,
        "RankMatchedControlPass": rank_match_pass,
        "AllPythonTraceReconstructionsExact": all_reconstruction_pass,
        "LibraryReconstructionPass": library_pass,
        "AggregateRecomputationPass": aggregate_pass,
        "StateRelabelDiscoveryInvariancePass": relabel_pass,
        "NearLawScientificAuditPass": near_scientific_pass,
        "RecomputedMainGatePass": recomputed_main_gate,
        "EvidenceIntegrityPass": evidence_integrity_pass,
        "IndependentScientificAuditPass": independent_scientific_pass,
        "ScientificGatePass": scientific_gate_pass,
        "StructuredReconstructionAudits": structured_audits,
        "ControlReconstructionAudits": control_audits,
        "NearLawReconstructionAudits": challenge_audits,
        "RankAudits": rank_audits,
        "StateRelabelAudits": relabel_audits,
        "NearLawTargetAudits": near_audits,
        "AggregateChecks": aggregate_checks,
        "RecomputedMetrics": {
            "AggregateK6ERuntimeSeconds": e_runtime,
            "AggregateK6BRuntimeSeconds": b_runtime,
            "AggregateK5ARuntimeSeconds": five_runtime,
            "ExactWordCacheHitCount": hits,
            "LogicalTraceRequestCount": logical_requests,
            "PhysicalTraceCellLookupCount": physical_lookups,
            "LogicalTraceCellLookupCount": logical_lookups,
        },
        "CanonicalTCCTModified": False,
        "FinalConclusion": conclusion,
    }
    dump(package / "verification" / "S132K6F_independent_verification.json", verification)
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
