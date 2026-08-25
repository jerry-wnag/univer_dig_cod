"""Independent event-indexed reconstruction for retrospective S132-K5A."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
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


def trace_indexed(k3, start: int, word: list[int], values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = start
    provenance: list[int] = []
    if not word:
        return {"Status": "Complete", "Target": state, "Provenance": []}
    for index, action in enumerate(word):
        key = k3.cell_key(state, action)
        if key not in values:
            return {
                "Status": "MissingFinal" if index == len(word) - 1 else "Blocked",
                "MissingKey": key,
                "Provenance": sorted(set(provenance)),
            }
        record = values[key]
        provenance.extend(record.get("Provenance", []))
        state = int(record["Target"])
    return {"Status": "Complete", "Target": state,
            "Provenance": sorted(set(provenance))}


def witness_audit_indexed(k3, instance, direct, state_count):
    witnesses = 0
    checks = 0
    for state in range(1, state_count + 1):
        checks += 1
        left = k3.trace(state, instance["Long"], direct)
        right = k3.trace(state, instance["Short"], direct)
        if left["Status"] == right["Status"] == "Complete":
            if left["Target"] != right["Target"]:
                return witnesses, True, checks
            witnesses += 1
    return witnesses, False, checks


def closure_indexed(k3, direct, instances, rejected_input, state_count, minimum_witnesses):
    rejected = set(map(int, rejected_input))
    initial_active = [row for row in instances if row["InstanceID"] not in rejected]
    audits = {
        row["InstanceID"]: witness_audit_indexed(k3, row, direct, state_count)
        for row in initial_active
    }
    actual_direct_checks = sum(audit[2] for audit in audits.values())
    full_direct_checks = 0
    inference_created = internal_rollbacks = direct_rejected = conflict_rejected = 0
    actual_evaluations = full_scan_evaluations = wakeups = 0
    peak_queue = full_scan_waves = 0

    while True:
        values = {key: dict(value) for key, value in direct.items()}
        active = [row for row in initial_active if row["InstanceID"] not in rejected]
        full_direct_checks += sum(audits[row["InstanceID"]][2] for row in active)
        contradicted = [row for row in active if audits[row["InstanceID"]][1]]
        if contradicted:
            ids = {row["InstanceID"] for row in contradicted}
            rejected.update(ids)
            direct_rejected += len(ids)
            internal_rollbacks += 1
            continue

        admissible = [
            row for row in active
            if audits[row["InstanceID"]][0] >= minimum_witnesses
        ]
        by_id = {row["InstanceID"]: row for row in admissible}
        queue = [
            (row["InstanceID"], state)
            for row in admissible for state in range(1, state_count + 1)
        ]
        waiters: dict[str, list[tuple[int, int]]] = defaultdict(list)
        restart = False

        while queue and not restart:
            peak_queue = max(peak_queue, len(queue))
            full_scan_waves += 1
            full_scan_evaluations += len(admissible) * state_count
            proposals: list[dict[str, Any]] = []
            for item in queue:
                actual_evaluations += 1
                instance = by_id[item[0]]
                state = item[1]
                left = trace_indexed(k3, state, instance["Long"], values)
                right = trace_indexed(k3, state, instance["Short"], values)
                if left["Status"] == "Complete" and right["Status"] == "MissingFinal":
                    proposals.append({
                        "CellKey": right["MissingKey"],
                        "Target": left["Target"],
                        "Provenance": sorted(set(
                            [instance["InstanceID"]]
                            + left["Provenance"] + right["Provenance"]
                        )),
                    })
                if right["Status"] == "Complete" and left["Status"] == "MissingFinal":
                    proposals.append({
                        "CellKey": left["MissingKey"],
                        "Target": right["Target"],
                        "Provenance": sorted(set(
                            [instance["InstanceID"]]
                            + left["Provenance"] + right["Provenance"]
                        )),
                    })
                if left["Status"] in {"Blocked", "MissingFinal"}:
                    waiters[left["MissingKey"]].append(item)
                if right["Status"] in {"Blocked", "MissingFinal"}:
                    waiters[right["MissingKey"]].append(item)

            grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for proposal in proposals:
                grouped[proposal["CellKey"]].append(proposal)
            conflicts = [
                rows for rows in grouped.values()
                if len({row["Target"] for row in rows}) > 1
            ]
            if conflicts:
                implicated = {
                    provenance
                    for rows in conflicts for row in rows
                    for provenance in row["Provenance"]
                }
                rejected.update(implicated)
                conflict_rejected += len(implicated)
                internal_rollbacks += 1
                restart = True
                break

            new_keys: list[str] = []
            for key in sorted(grouped):
                candidates = grouped[key]
                record = {
                    "Target": candidates[0]["Target"],
                    "Provenance": sorted({
                        provenance for row in candidates
                        for provenance in row["Provenance"]
                    }),
                }
                if key in values:
                    if values[key]["Target"] != record["Target"]:
                        implicated = set(record["Provenance"]) | set(values[key]["Provenance"])
                        rejected.update(implicated)
                        conflict_rejected += len(implicated)
                        internal_rollbacks += 1
                        restart = True
                        break
                else:
                    values[key] = {
                        "Target": record["Target"], "Direct": False,
                        "Provenance": list(record["Provenance"]),
                    }
                    new_keys.append(key)
                    inference_created += 1
            if restart:
                break
            if not new_keys:
                queue = []
            else:
                flattened = [item for key in new_keys for item in waiters.get(key, [])]
                queue = list(dict.fromkeys(flattened))
                for key in new_keys:
                    waiters.pop(key, None)
                wakeups += len(queue)
                if not queue:
                    full_scan_waves += 1
                    full_scan_evaluations += len(admissible) * state_count
        if not restart:
            return {
                "Values": values,
                "RejectedInstanceIDs": sorted(rejected),
                "InferenceCreatedCount": inference_created,
                "InternalRollbackCount": internal_rollbacks,
                "DirectContradictionRejectedCount": direct_rejected,
                "InferenceConflictRejectedCount": conflict_rejected,
                "ActualIndexedClosureItemEvaluations": actual_evaluations,
                "FullScanEquivalentClosureItemEvaluations": full_scan_evaluations,
                "ActualDirectAuditStateChecks": actual_direct_checks,
                "FullRescanEquivalentDirectAuditStateChecks": full_direct_checks,
                "IndexedWakeupItemCount": wakeups,
                "PeakIndexedQueueSize": peak_queue,
                "FullScanWaveCount": full_scan_waves,
            }


def replay_indexed(k3, table, schemas, order, transfer_enabled,
                   initial_fraction, batch_fraction, minimum_witnesses):
    state_count = len(table)
    action_count = len(table[0])
    total = state_count * action_count
    initial = math.ceil(initial_fraction * total) if transfer_enabled else total
    batch_size = max(1, math.ceil(batch_fraction * total))
    instances = k3.instantiate(schemas, action_count) if transfer_enabled else []
    direct: dict[str, dict[str, Any]] = {}
    membership = 0
    for key in order[:initial]:
        k3.add_direct(direct, table, key)
        membership += 1
    rejected: list[int] = []
    eq_calls = eq_cells = counterexamples = rollback_count = 0
    inference_created = internal_rollbacks = direct_rejected = conflict_rejected = 0
    actual_eval = full_eval = direct_checks = full_direct_checks = 0
    wakeups = peak_queue = full_waves = 0
    exact = False
    values: dict[str, dict[str, Any]] = {}
    while not exact:
        closed = closure_indexed(
            k3, direct, instances, rejected, state_count, minimum_witnesses
        )
        values = closed["Values"]
        rejected = closed["RejectedInstanceIDs"]
        inference_created += int(closed["InferenceCreatedCount"])
        internal_rollbacks += int(closed["InternalRollbackCount"])
        direct_rejected += int(closed["DirectContradictionRejectedCount"])
        conflict_rejected += int(closed["InferenceConflictRejectedCount"])
        actual_eval += int(closed["ActualIndexedClosureItemEvaluations"])
        full_eval += int(closed["FullScanEquivalentClosureItemEvaluations"])
        direct_checks += int(closed["ActualDirectAuditStateChecks"])
        full_direct_checks += int(closed["FullRescanEquivalentDirectAuditStateChecks"])
        wakeups += int(closed["IndexedWakeupItemCount"])
        peak_queue = max(peak_queue, int(closed["PeakIndexedQueueSize"]))
        full_waves += int(closed["FullScanWaveCount"])
        missing = [key for key in order if key not in values]
        if missing:
            for key in missing[:batch_size]:
                k3.add_direct(direct, table, key)
                membership += 1
            continue
        check = k3.equivalence(values, table)
        eq_calls += 1
        eq_cells += int(check["InspectedCells"])
        if check["Exact"]:
            exact = True
            break
        counterexamples += 1
        rejected = sorted(set(rejected) | set(check.get("Provenance", [])))
        k3.add_direct(direct, table, check["MismatchKey"])
        rollback_count += 1
    final_inferred = sum(not bool(row["Direct"]) for row in values.values())
    return {
        "MembershipQueries": membership,
        "EquivalenceOracleCalls": eq_calls,
        "EquivalenceCounterexampleCount": counterexamples,
        "EquivalenceCellsInspected": eq_cells,
        "LogicalInteractionCost": membership + eq_calls,
        "ConcreteOracleCellCost": membership + eq_cells,
        "UniqueDirectObservationCount": len(direct),
        "FinalInferredTransitionCount": final_inferred,
        "ProposedSchemaInstanceCount": len(instances),
        "RejectedSchemaInstanceCount": len(rejected),
        "CounterexampleRollbackCount": rollback_count,
        "InternalRollbackCount": internal_rollbacks,
        "DirectContradictionRejectedCount": direct_rejected,
        "InferenceConflictRejectedCount": conflict_rejected,
        "CumulativeInferenceCreatedCount": inference_created,
        "FinalExact": exact,
        "UnsafeCommittedInferenceCount": 0 if exact else final_inferred,
        "ActualIndexedClosureItemEvaluations": actual_eval,
        "FullScanEquivalentClosureItemEvaluations": full_eval,
        "ActualDirectAuditStateChecks": direct_checks,
        "FullRescanEquivalentDirectAuditStateChecks": full_direct_checks,
        "IndexedWakeupItemCount": wakeups,
        "PeakIndexedQueueSize": peak_queue,
        "FullScanWaveCount": full_waves,
    }


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K5A_frozen_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    result = json.loads((package / "results" / "S132K5A_result.json").read_text(encoding="utf-8"))
    old = json.loads((package / "input" / "S132K4B_frozen_result.json").read_text(encoding="utf-8"))
    old_manifest = json.loads((package / "input" / "S132K4B_frozen_manifest.json").read_text(encoding="utf-8"))
    oracle = json.loads((package / "input" / "S132K4B_oracle_sequences.json").read_text(encoding="utf-8"))
    k3 = load_module(package / "source" / "TCCT_S132K3B_IndependentVerifier.py", "k5a_k3")
    k4 = load_module(package / "source" / "TCCT_S132K4A_IndependentVerifier.py", "k5a_k4")

    source_pass = {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir()) if path.is_file()
    } == manifest["SourceHashes"]
    input_pass = {
        path.name: sha256(path)
        for path in sorted((package / "input").iterdir()) if path.is_file()
    } == manifest["InputHashes"]
    initial = float(old_manifest["InitialDirectObservationFraction"])
    batch = float(old_manifest["DirectQueryBatchFraction"])
    witnesses = int(old_manifest["MinimumDirectPositiveWitnessesBeforeInference"])
    maximum = int(old_manifest["MaximumConceptWordLength"])

    def reconstruct_stream(worlds, new_rows, old_rows):
        library: dict[Any, dict[str, Any]] = {}
        next_id = 0
        audits = []
        for world, new_row, old_row in zip(worlds, new_rows, old_rows):
            available = sorted(library.values(), key=lambda record: record["SchemaID"])
            run_audits = {}
            for label, enabled, schema_input in (
                ("Transfer", True, available), ("Baseline", False, []),
            ):
                rebuilt = replay_indexed(
                    k3, world["TransitionTable"], schema_input,
                    new_row[label]["QueryOrder"], enabled,
                    initial, batch, witnesses,
                )
                mismatches = [
                    key for key, value in rebuilt.items()
                    if new_row[label][key] != value
                ]
                old_mismatches = [
                    key for key, value in old_row[label].items()
                    if new_row[label][key] != value
                ]
                run_audits[label + "IndependentMismatchFields"] = mismatches
                run_audits[label + "FrozenK4BMismatchFields"] = old_mismatches
            schemas = k4.discover(world["TransitionTable"], maximum)
            before = len(library)
            next_id, new_count = k4.update_library(
                library, next_id, schemas, world["WorldID"]
            )
            excluded = {"Transfer", "Baseline", "Stream"}
            outer_mismatches = [
                key for key in set(new_row).intersection(old_row) - excluded
                if new_row[key] != old_row[key]
            ]
            trajectory = (
                int(new_row["LibraryBeforeCount"]) == before
                and int(new_row["SchemasDiscoveredThisWorld"]) == len(schemas)
                and int(new_row["NewSchemaCount"]) == new_count
                and int(new_row["LibraryAfterCount"]) == len(library)
            )
            audits.append({
                "WorldID": world["WorldID"],
                **run_audits,
                "OuterFrozenK4BMismatchFields": sorted(outer_mismatches),
                "LibraryTrajectoryPass": trajectory,
            })
        records = sorted(library.values(), key=lambda record: record["SchemaID"])
        passed = all(
            not row["TransferIndependentMismatchFields"]
            and not row["BaselineIndependentMismatchFields"]
            and not row["TransferFrozenK4BMismatchFields"]
            and not row["BaselineFrozenK4BMismatchFields"]
            and not row["OuterFrozenK4BMismatchFields"]
            and row["LibraryTrajectoryPass"]
            for row in audits
        )
        return audits, records, passed

    structured_audits, structured_library, structured_pass = reconstruct_stream(
        oracle["StructuredWorlds"], result["StructuredResults"], old["StructuredResults"]
    )
    control_audits, control_library, control_pass = reconstruct_stream(
        oracle["RankMatchedControls"], result["ControlResults"], old["ControlResults"]
    )

    challenge_audits = []
    for world, new_row, old_row in zip(
        oracle["NearLawChallenges"], result["NearLawChallengeResults"],
        old["NearLawChallengeResults"],
    ):
        fields = {}
        for label, enabled, schema_input in (
            ("Transfer", True, structured_library), ("Baseline", False, []),
        ):
            rebuilt = replay_indexed(
                k3, world["TransitionTable"], schema_input,
                new_row[label]["QueryOrder"], enabled,
                initial, batch, witnesses,
            )
            fields[label + "IndependentMismatchFields"] = [
                key for key, value in rebuilt.items() if new_row[label][key] != value
            ]
            fields[label + "FrozenK4BMismatchFields"] = [
                key for key, value in old_row[label].items()
                if new_row[label][key] != value
            ]
        excluded = {"Transfer", "Baseline", "Stream"}
        outer = [
            key for key in set(new_row).intersection(old_row) - excluded
            if new_row[key] != old_row[key]
        ]
        challenge_audits.append({
            "WorldID": world["WorldID"], **fields,
            "OuterFrozenK4BMismatchFields": sorted(outer),
        })
    challenge_pass = all(
        not row["TransferIndependentMismatchFields"]
        and not row["BaselineIndependentMismatchFields"]
        and not row["TransferFrozenK4BMismatchFields"]
        and not row["BaselineFrozenK4BMismatchFields"]
        and not row["OuterFrozenK4BMismatchFields"]
        for row in challenge_audits
    )

    library_pass = (
        structured_library == result["FinalStructuredLibrary"] == old["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"] == old["FinalControlLibrary"]
    )
    all_rows = (
        result["StructuredResults"] + result["ControlResults"]
        + result["NearLawChallengeResults"]
    )
    transfers = [row["Transfer"] for row in all_rows]
    actual_eval = sum(int(row["ActualIndexedClosureItemEvaluations"]) for row in transfers)
    full_eval = sum(int(row["FullScanEquivalentClosureItemEvaluations"]) for row in transfers)
    direct_checks = sum(int(row["ActualDirectAuditStateChecks"]) for row in transfers)
    full_direct_checks = sum(
        int(row["FullRescanEquivalentDirectAuditStateChecks"]) for row in transfers
    )
    arithmetic_pass = (
        int(result["ActualIndexedClosureItemEvaluations"]) == actual_eval
        and int(result["FullScanEquivalentClosureItemEvaluations"]) == full_eval
        and int(result["IndexedClosureEvaluationReduction"]) == full_eval - actual_eval
        and abs(float(result["IndexedClosureEvaluationReductionFraction"])
                - (1 - actual_eval / full_eval if full_eval else 0.0)) < 1e-12
        and int(result["ActualDirectAuditStateChecks"]) == direct_checks
        and int(result["FullRescanEquivalentDirectAuditStateChecks"]) == full_direct_checks
        and int(result["DirectAuditCheckReduction"]) == full_direct_checks - direct_checks
    )
    exact = all(
        row[label]["FinalExact"] for row in all_rows
        for label in ("Transfer", "Baseline")
    )
    unsafe = sum(int(row["Transfer"]["UnsafeCommittedInferenceCount"]) for row in all_rows)
    work_reduced = actual_eval < full_eval and direct_checks <= full_direct_checks
    runtime_improved = float(result["RuntimeSeconds"]) < float(old["RuntimeSeconds"])
    boundary_pass = (
        result["RetrospectiveOpenedWorldsOnly"] is True
        and result["FreshGeneralizationClaimAllowed"] is False
        and result["ConceptSetChanged"] is False
        and result["CanonicalTCCTModified"] is False
        and result["FrozenK3BAndK4AConceptDiscoveryModified"] is False
    )
    expected_gate = (
        structured_pass and control_pass and challenge_pass and library_pass
        and exact and unsafe == 0 and work_reduced and runtime_improved
    )
    gate_consistency = (
        bool(result["RuntimeImproved"]) == runtime_improved
        and bool(result["DeterministicWorkReduced"]) == work_reduced
        and bool(result["RetrospectiveExactIndexedActivationGatePass"]) == expected_gate
    )
    integrity = (
        source_pass and input_pass and structured_pass and control_pass
        and challenge_pass and library_pass and arithmetic_pass
        and boundary_pass and gate_consistency
    )
    conclusion = (
        "VERIFIED_RETROSPECTIVE_EXACT_INDEXED_ACTIVATION_GATE_PASS"
        if integrity and expected_gate else
        "EVIDENCE_VALID_BUT_EXACT_INDEXED_ACTIVATION_GATE_NOT_PASSED"
        if integrity else "VERIFICATION_FAILED"
    )
    return {
        "Stage": "S132-K5A independent event-indexed reconstruction",
        "SourceHashPass": source_pass,
        "InputHashPass": input_pass,
        "StructuredAudits": structured_audits,
        "ControlAudits": control_audits,
        "NearLawAudits": challenge_audits,
        "StructuredReconstructionPass": structured_pass,
        "ControlReconstructionPass": control_pass,
        "NearLawReconstructionPass": challenge_pass,
        "FinalLibraryIdentityPass": library_pass,
        "WorkMetricArithmeticPass": arithmetic_pass,
        "ClaimBoundaryPass": boundary_pass,
        "ExpectedGatePass": expected_gate,
        "GateConsistencyPass": gate_consistency,
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
    output = package / "verification" / "S132K5A_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
