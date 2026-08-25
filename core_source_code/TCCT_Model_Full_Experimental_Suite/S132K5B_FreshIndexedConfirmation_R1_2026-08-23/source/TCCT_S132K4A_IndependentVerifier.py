"""Independent reconstruction of S132-K4A online bounded concept creation."""

from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
from collections import defaultdict
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


def transform(table: list[list[int]], word: tuple[int, ...]) -> tuple[int, ...]:
    mapping = list(range(len(table)))
    for action in word:
        mapping = [table[state][action - 1] - 1 for state in mapping]
    return tuple(mapping)


def action_ranks(table: list[list[int]]) -> list[int]:
    return [
        len({row[action] for row in table})
        for action in range(len(table[0]))
    ]


def anonymize(long: tuple[int, ...], short: tuple[int, ...]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    mapping: dict[int, int] = {}
    next_value = 1
    output = []
    for word in (long, short):
        row = []
        for action in word:
            if action not in mapping:
                mapping[action] = next_value
                next_value += 1
            row.append(mapping[action])
        output.append(tuple(row))
    return output[0], output[1]


def discover(table: list[list[int]], maximum: int) -> list[tuple[tuple[int, ...], tuple[int, ...]]]:
    action_count = len(table[0])
    groups: dict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
    for length in range(maximum + 1):
        for word in itertools.product(range(1, action_count + 1), repeat=length):
            groups[transform(table, word)].append(word)
    schemas = set()
    for words in groups.values():
        representative = min(words, key=lambda word: (len(word), word))
        for word in words:
            if len(word) > len(representative):
                schemas.add(anonymize(word, representative))
    return sorted(schemas, key=lambda schema: (
        len(schema[0]), schema[0], len(schema[1]), schema[1]
    ))


def update_library(
    library: dict[Any, dict[str, Any]], next_id: int,
    schemas: list[tuple[tuple[int, ...], tuple[int, ...]]], world_id: str,
) -> tuple[int, int]:
    new_count = 0
    for schema in schemas:
        if schema not in library:
            next_id += 1
            library[schema] = {
                "SchemaID": next_id,
                "Schema": [list(schema[0]), list(schema[1])],
                "FirstCreatedAfterWorld": world_id,
                "SupportWorlds": [world_id],
            }
            new_count += 1
        elif world_id not in library[schema]["SupportWorlds"]:
            library[schema]["SupportWorlds"].append(world_id)
            library[schema]["SupportWorlds"].sort()
    return next_id, new_count


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K4A_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K4A_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    result = json.loads((package / "results" / "S132K4A_result.json").read_text(encoding="utf-8"))
    oracle = json.loads((package / "oracle" / "S132K4A_oracle_sequences.json").read_text(encoding="utf-8"))
    helper = load_module(
        package / "source" / "TCCT_S132K3B_IndependentVerifier.py",
        "s132k4a_k3b_helper",
    )
    source_hash_pass = {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir()) if path.is_file()
    } == manifest["SourceHashes"]
    phase_pass = (
        sha256(manifest_path) == receipt["ManifestSHA256"]
        and receipt["WorldsMaterialized"] is True
        and receipt["MaterializedAfterManifestFreeze"] is True
        and sha256(package / "input" / "S132K4A_public_input.json")
        == receipt["PublicInputSHA256"]
        and sha256(package / "oracle" / "S132K4A_oracle_sequences.json")
        == receipt["OracleSHA256"]
        and sha256(package / "sealed" / "S132K4A_generator_truth.json")
        == receipt["SealedTruthSHA256"]
    )
    maximum = int(manifest["MaximumConceptWordLength"])

    expected_ids = [row["WorldID"] for row in manifest["WorldSpecifications"]]
    structured_ids = [row["WorldID"] for row in oracle["StructuredWorlds"]]
    control_ids = [row["WorldID"] for row in oracle["RankMatchedControls"]]
    sequence_shape_pass = (
        expected_ids == structured_ids == control_ids
        and len(result["StructuredResults"]) == len(expected_ids)
        and len(result["ControlResults"]) == len(expected_ids)
    )
    rank_match_pass = all(
        action_ranks(structured["TransitionTable"])
        == action_ranks(control["TransitionTable"])
        == control["TargetActionImageRanks"]
        == control["ControlActionImageRanks"]
        for structured, control in zip(
            oracle["StructuredWorlds"], oracle["RankMatchedControls"]
        )
    )

    def reconstruct_stream(worlds, rows, stream_name):
        library: dict[Any, dict[str, Any]] = {}
        next_id = 0
        audits = []
        for world, row in zip(worlds, rows):
            available = sorted(library.values(), key=lambda record: record["SchemaID"])
            transfer = helper.replay(
                world["TransitionTable"], available, row["Transfer"]["QueryOrder"], True,
                float(manifest["InitialDirectObservationFraction"]),
                float(manifest["DirectQueryBatchFraction"]),
                int(manifest["MinimumDirectPositiveWitnessesBeforeInference"]),
            )
            baseline = helper.replay(
                world["TransitionTable"], [], row["Baseline"]["QueryOrder"], False,
                float(manifest["InitialDirectObservationFraction"]),
                float(manifest["DirectQueryBatchFraction"]),
                int(manifest["MinimumDirectPositiveWitnessesBeforeInference"]),
            )
            transfer_mismatch = [key for key, value in transfer.items() if row["Transfer"][key] != value]
            baseline_mismatch = [key for key, value in baseline.items() if row["Baseline"][key] != value]
            schemas = discover(world["TransitionTable"], maximum)
            before = len(library)
            next_id, new_count = update_library(library, next_id, schemas, world["WorldID"])
            expected_mq = baseline["MembershipQueries"] - transfer["MembershipQueries"]
            expected_logical = baseline["LogicalInteractionCost"] - transfer["LogicalInteractionCost"]
            expected_concrete = baseline["ConcreteOracleCellCost"] - transfer["ConcreteOracleCellCost"]
            trajectory = (
                int(row["LibraryBeforeCount"]) == before
                and int(row["SchemasDiscoveredThisWorld"]) == len(schemas)
                and int(row["NewSchemaCount"]) == new_count
                and int(row["LibraryAfterCount"]) == len(library)
                and bool(row["PriorCreatedConceptUsed"]) == (transfer["FinalInferredTransitionCount"] > 0)
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
        final_records = sorted(library.values(), key=lambda record: record["SchemaID"])
        stream_pass = all(
            row["TransferReconstructionPass"] and row["BaselineReconstructionPass"]
            and row["LibraryTrajectoryPass"] for row in audits
        )
        return audits, final_records, stream_pass

    structured_audits, structured_library, structured_pass = reconstruct_stream(
        oracle["StructuredWorlds"], result["StructuredResults"], "STRUCTURED"
    )
    control_audits, control_library, control_pass = reconstruct_stream(
        oracle["RankMatchedControls"], result["ControlResults"], "RANK_MATCHED_CONTROL"
    )
    library_pass = (
        structured_library == result["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"]
    )
    structured_rows = result["StructuredResults"]
    control_rows = result["ControlResults"]
    all_exact = all(
        row[mode]["FinalExact"]
        for rows in (structured_rows, control_rows)
        for row in rows for mode in ("Transfer", "Baseline")
    )
    unsafe = sum(
        int(row["Transfer"]["UnsafeCommittedInferenceCount"])
        for rows in (structured_rows, control_rows) for row in rows
    )
    eligible = [row for row in structured_rows if int(row["LibraryBeforeCount"]) > 0]
    positive = sum(int(row["MembershipQuerySavings"]) > 0 for row in eligible)
    fraction = positive / len(eligible) if eligible else 0.0
    structured_mq = sum(int(row["MembershipQuerySavings"]) for row in structured_rows)
    structured_logical = sum(int(row["LogicalInteractionCostSavings"]) for row in structured_rows)
    structured_concrete = sum(int(row["ConcreteOracleCellCostSavings"]) for row in structured_rows)
    control_mq = sum(int(row["MembershipQuerySavings"]) for row in control_rows)
    control_concrete = sum(int(row["ConcreteOracleCellCostSavings"]) for row in control_rows)
    prior_used = any(row["PriorCreatedConceptUsed"] for row in structured_rows)
    starting_empty = (
        bool(structured_rows) and bool(control_rows)
        and int(structured_rows[0]["LibraryBeforeCount"]) == 0
        and int(control_rows[0]["LibraryBeforeCount"]) == 0
    )
    expected_gate = (
        sequence_shape_pass and rank_match_pass and starting_empty
        and structured_pass and control_pass and library_pass and all_exact and unsafe == 0
        and len(structured_library) > 0 and prior_used and fraction >= 0.5
        and structured_mq > 0 and structured_concrete > 0
        and structured_concrete > control_concrete
    )
    aggregate_pass = (
        int(result["AggregateStructuredMembershipQuerySavings"]) == structured_mq
        and int(result["AggregateStructuredLogicalInteractionCostSavings"]) == structured_logical
        and int(result["AggregateStructuredConcreteOracleCellCostSavings"]) == structured_concrete
        and int(result["AggregateControlMembershipQuerySavings"]) == control_mq
        and int(result["AggregateControlConcreteOracleCellCostSavings"]) == control_concrete
        and int(result["PositiveSavingsEligibleWorldCount"]) == positive
        and abs(float(result["PositiveSavingsEligibleWorldFraction"]) - fraction) < 1e-12
    )
    boundary_pass = (
        result["FreshWorldsMaterializedAfterProtocolFreeze"] is True
        and int(result["StartingConceptLibraryCount"]) == 0
        and int(result["PreloadedK3ASchemaCount"]) == 0
        and result["CanonicalTCCTModified"] is False
        and result["GeneratorTruthReadByLearner"] is False
        and result["OpenEndedPrimitiveOrLanguageInventionProven"] is False
        and result["B8ASymbolicLearnerQueryReductionProven"] is False
    )
    integrity = (
        source_hash_pass and phase_pass and sequence_shape_pass and rank_match_pass
        and structured_pass and control_pass
        and library_pass and aggregate_pass and boundary_pass
        and bool(result["FreshOnlineBoundedConceptCreationGatePass"]) == expected_gate
    )
    conclusion = (
        "VERIFIED_FRESH_ONLINE_BOUNDED_CONCEPT_CREATION_GATE_PASS"
        if integrity and expected_gate else
        "EVIDENCE_VALID_BUT_ONLINE_CONCEPT_CREATION_GATE_NOT_PASSED"
        if integrity else "VERIFICATION_FAILED"
    )
    return {
        "Stage": "S132-K4A independent reconstruction",
        "SourceHashPass": source_hash_pass,
        "FreezeMaterializationOrderPass": phase_pass,
        "SequenceShapeAndOrderPass": sequence_shape_pass,
        "RankMatchedControlPass": rank_match_pass,
        "StructuredAudits": structured_audits,
        "ControlAudits": control_audits,
        "StructuredReconstructionPass": structured_pass,
        "ControlReconstructionPass": control_pass,
        "FinalLibraryReconstructionPass": library_pass,
        "AggregateArithmeticPass": aggregate_pass,
        "ClaimBoundaryPass": boundary_pass,
        "ExpectedGatePass": expected_gate,
        "EvidenceIntegrityPass": integrity,
        "FinalConclusion": conclusion,
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    result = verify(package)
    output = package / "verification" / "S132K4A_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
