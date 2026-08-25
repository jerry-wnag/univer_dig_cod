"""Independent semantic replay for retrospective S132-K6B optimization."""

from __future__ import annotations

import argparse
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


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def trace_direct(k3, start: int, word: list[int], direct: dict[str, dict[str, Any]]):
    state = start
    lookups = 0
    if not word:
        return {"Status": "Complete", "Target": state}, lookups
    for index, action in enumerate(word):
        lookups += 1
        key = k3.cell_key(state, action)
        if key not in direct:
            return {
                "Status": "MissingFinal" if index == len(word) - 1 else "Blocked",
                "MissingKey": key,
            }, lookups
        state = int(direct[key]["Target"])
    return {"Status": "Complete", "Target": state}, lookups


def make_audit(instances: list[dict[str, Any]], rejected: set[int]):
    items_by_instance = {
        int(row["InstanceID"]): [] for row in instances
        if int(row["InstanceID"]) not in rejected
    }
    return {
        "Instances": {int(row["InstanceID"]): row for row in instances},
        "ItemsByInstance": items_by_instance,
        "Witnesses": defaultdict(int),
        "Contradicted": set(),
        "FirstContradictionState": {},
        "Resolved": set(),
        "WaitingByItem": {},
        "WaitersByKey": defaultdict(set),
        "Evaluations": 0,
        "TraceCellLookups": 0,
        "Wakeups": 0,
        "PeakWakeBatch": 0,
        "InitialEvaluations": 0,
    }


def remove_waiting(audit, item):
    for key in audit["WaitingByItem"].pop(item, set()):
        bucket = audit["WaitersByKey"].get(key)
        if bucket is not None:
            bucket.discard(item)
            if not bucket:
                audit["WaitersByKey"].pop(key, None)


def deactivate_instance(audit, instance_id: int):
    for item in audit["ItemsByInstance"].get(instance_id, []):
        remove_waiting(audit, item)


def sync_rejected(audit, rejected: set[int]):
    for instance_id in rejected:
        deactivate_instance(audit, int(instance_id))


def evaluate_audit_item(k3, audit, item, direct, rejected: set[int]):
    instance_id, state = item
    if (
        instance_id in rejected
        or instance_id in audit["Contradicted"]
        or item in audit["Resolved"]
    ):
        remove_waiting(audit, item)
        return
    remove_waiting(audit, item)
    instance = audit["Instances"][instance_id]
    left, left_lookups = trace_direct(k3, state, instance["Long"], direct)
    right, right_lookups = trace_direct(k3, state, instance["Short"], direct)
    audit["Evaluations"] += 1
    audit["TraceCellLookups"] += left_lookups + right_lookups
    if left["Status"] == right["Status"] == "Complete":
        audit["Resolved"].add(item)
        if left["Target"] == right["Target"]:
            audit["Witnesses"][instance_id] += 1
        else:
            audit["Contradicted"].add(instance_id)
            audit["FirstContradictionState"][instance_id] = state
            deactivate_instance(audit, instance_id)
        return
    missing = {
        row["MissingKey"] for row in (left, right)
        if row["Status"] in {"Blocked", "MissingFinal"}
    }
    audit["WaitingByItem"][item] = missing
    for key in missing:
        audit["WaitersByKey"][key].add(item)


def initialize_audit(k3, instances, direct, state_count, rejected: set[int]):
    audit = make_audit(instances, rejected)
    for instance in instances:
        instance_id = int(instance["InstanceID"])
        if instance_id in rejected:
            continue
        items = [(instance_id, state) for state in range(1, state_count + 1)]
        audit["ItemsByInstance"][instance_id] = items
        for item in items:
            evaluate_audit_item(k3, audit, item, direct, rejected)
            if instance_id in audit["Contradicted"]:
                break
    audit["InitialEvaluations"] = audit["Evaluations"]
    return audit


def advance_audit(k3, audit, new_keys, direct, rejected: set[int]):
    items = sorted({
        item for key in new_keys
        for item in audit["WaitersByKey"].get(key, set())
    })
    audit["Wakeups"] += len(items)
    audit["PeakWakeBatch"] = max(audit["PeakWakeBatch"], len(items))
    for item in items:
        evaluate_audit_item(k3, audit, item, direct, rejected)


def audit_state_check_cost(audit, instance_id: int, state_count: int) -> int:
    return int(audit["FirstContradictionState"].get(instance_id, state_count))


def closure_persistent(
    k3, k5, direct, instances, rejected_input, state_count,
    minimum_witnesses, audit,
):
    rejected = set(map(int, rejected_input))
    initial_active = [row for row in instances if int(row["InstanceID"]) not in rejected]
    k5_actual_direct_checks = sum(
        audit_state_check_cost(audit, int(row["InstanceID"]), state_count)
        for row in initial_active
    )
    full_direct_checks = 0
    inference_created = internal_rollbacks = direct_rejected = conflict_rejected = 0
    actual_evaluations = full_scan_evaluations = wakeups = 0
    peak_queue = full_scan_waves = 0

    while True:
        values = {key: dict(value) for key, value in direct.items()}
        active = [row for row in initial_active if int(row["InstanceID"]) not in rejected]
        full_direct_checks += sum(
            audit_state_check_cost(audit, int(row["InstanceID"]), state_count)
            for row in active
        )
        contradicted = [
            row for row in active
            if int(row["InstanceID"]) in audit["Contradicted"]
        ]
        if contradicted:
            ids = {int(row["InstanceID"]) for row in contradicted}
            rejected.update(ids)
            direct_rejected += len(ids)
            internal_rollbacks += 1
            continue

        admissible = [
            row for row in active
            if int(audit["Witnesses"][int(row["InstanceID"])]) >= minimum_witnesses
        ]
        by_id = {int(row["InstanceID"]): row for row in admissible}
        queue = [
            (int(row["InstanceID"]), state)
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
                left = k5.trace_indexed(k3, state, instance["Long"], values)
                right = k5.trace_indexed(k3, state, instance["Short"], values)
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
                "K5AEquivalentDirectAuditStateChecks": k5_actual_direct_checks,
                "FullRescanEquivalentDirectAuditStateChecks": full_direct_checks,
                "IndexedWakeupItemCount": wakeups,
                "PeakIndexedQueueSize": peak_queue,
                "FullScanWaveCount": full_scan_waves,
            }


def replay_persistent(
    k3, k5, table, schemas, order, transfer_enabled,
    initial_fraction, batch_fraction, minimum_witnesses,
):
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
    audit = initialize_audit(k3, instances, direct, state_count, set())
    eq_calls = eq_cells = counterexamples = rollback_count = 0
    inference_created = internal_rollbacks = direct_rejected = conflict_rejected = 0
    actual_eval = full_eval = k5_direct_checks = full_direct_checks = 0
    wakeups = peak_queue = full_waves = 0
    exact = False
    values: dict[str, dict[str, Any]] = {}
    while not exact:
        closed = closure_persistent(
            k3, k5, direct, instances, rejected, state_count,
            minimum_witnesses, audit,
        )
        values = closed["Values"]
        rejected = closed["RejectedInstanceIDs"]
        sync_rejected(audit, set(rejected))
        inference_created += int(closed["InferenceCreatedCount"])
        internal_rollbacks += int(closed["InternalRollbackCount"])
        direct_rejected += int(closed["DirectContradictionRejectedCount"])
        conflict_rejected += int(closed["InferenceConflictRejectedCount"])
        actual_eval += int(closed["ActualIndexedClosureItemEvaluations"])
        full_eval += int(closed["FullScanEquivalentClosureItemEvaluations"])
        k5_direct_checks += int(closed["K5AEquivalentDirectAuditStateChecks"])
        full_direct_checks += int(closed["FullRescanEquivalentDirectAuditStateChecks"])
        wakeups += int(closed["IndexedWakeupItemCount"])
        peak_queue = max(peak_queue, int(closed["PeakIndexedQueueSize"]))
        full_waves += int(closed["FullScanWaveCount"])
        missing = [key for key in order if key not in values]
        if missing:
            batch_keys = missing[:batch_size]
            for key in batch_keys:
                k3.add_direct(direct, table, key)
                membership += 1
            advance_audit(k3, audit, batch_keys, direct, set(rejected))
            continue
        check = k3.equivalence(values, table)
        eq_calls += 1
        eq_cells += int(check["InspectedCells"])
        if check["Exact"]:
            exact = True
            break
        counterexamples += 1
        rejected = sorted(set(rejected) | set(check.get("Provenance", [])))
        sync_rejected(audit, set(rejected))
        key = check["MismatchKey"]
        k3.add_direct(direct, table, key)
        advance_audit(k3, audit, [key], direct, set(rejected))
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
        "K5AEquivalentDirectAuditStateChecks": k5_direct_checks,
        "FullRescanEquivalentDirectAuditStateChecks": full_direct_checks,
        "IndexedWakeupItemCount": wakeups,
        "PeakIndexedQueueSize": peak_queue,
        "FullScanWaveCount": full_waves,
        "ActualPersistentDirectAuditItemEvaluations": audit["Evaluations"],
        "InitialPersistentDirectAuditItemEvaluations": audit["InitialEvaluations"],
        "IncrementalPersistentDirectAuditItemEvaluations": (
            audit["Evaluations"] - audit["InitialEvaluations"]
        ),
        "ActualPersistentDirectAuditTraceCellLookups": audit["TraceCellLookups"],
        "PersistentDirectAuditWakeupItemCount": audit["Wakeups"],
        "PeakPersistentDirectAuditWakeBatch": audit["PeakWakeBatch"],
    }


def mapped_k5_mismatches(k6_run, k5_run):
    mismatches = []
    for key, value in k5_run.items():
        mapped = (
            "K5AEquivalentDirectAuditStateChecks"
            if key == "ActualDirectAuditStateChecks" else key
        )
        if k6_run.get(mapped) != value:
            mismatches.append(key)
    return mismatches


def common_report_mismatches(rebuilt, reported):
    return [key for key, value in rebuilt.items() if key in reported and reported[key] != value]


def load_context(package: Path):
    source = package / "source"
    k3 = load_module(source / "TCCT_S132K3B_IndependentVerifier.py", "s132k6b_k3")
    k4 = load_module(source / "TCCT_S132K4A_IndependentVerifier.py", "s132k6b_k4")
    k5 = load_module(source / "TCCT_S132K5A_IndependentVerifier.py", "s132k6b_k5")
    old_manifest = json.loads(
        (package / "input" / "S132K5B_frozen_manifest.json").read_text(encoding="utf-8")
    )
    old_result = json.loads(
        (package / "input" / "S132K5B_frozen_result.json").read_text(encoding="utf-8")
    )
    oracle = json.loads(
        (package / "input" / "S132K5B_oracle_sequences.json").read_text(encoding="utf-8")
    )
    return k3, k4, k5, old_manifest, old_result, oracle


def replay_stream(k3, k4, k5, worlds, rows, initial, batch, witnesses, maximum):
    library: dict[Any, dict[str, Any]] = {}
    next_id = 0
    audits = []
    for world, row in zip(worlds, rows):
        available = sorted(library.values(), key=lambda record: record["SchemaID"])
        query_order = row["K6B"]["QueryOrder"] if "K6B" in row else row["IndexedTransfer"]["QueryOrder"]
        k6_run = replay_persistent(
            k3, k5, world["TransitionTable"], available, query_order, True,
            initial, batch, witnesses,
        )
        k5_run = k5.replay_indexed(
            k3, world["TransitionTable"], available, query_order, True,
            initial, batch, witnesses,
        )
        discovered = k4.discover(world["TransitionTable"], maximum)
        before = len(available)
        next_id, new_count = k4.update_library(library, next_id, discovered, world["WorldID"])
        audit = {
            "WorldID": world["WorldID"],
            "K6BK5AFieldMatch": not mapped_k5_mismatches(k6_run, k5_run),
            "K6BK5AMismatchFields": mapped_k5_mismatches(k6_run, k5_run),
            "LibraryBeforeCount": before,
            "LibraryAfterCount": len(library),
            "NewSchemaCount": new_count,
            "K6BRebuilt": k6_run,
            "K5ARebuilt": k5_run,
        }
        if "K6B" in row:
            audit["K6BReportMismatchFields"] = common_report_mismatches(k6_run, row["K6B"])
            audit["K5AReportMismatchFields"] = common_report_mismatches(k5_run, row["K5A"])
            audit["QueryOrderMatch"] = row["K6B"]["QueryOrder"] == row["K5A"]["QueryOrder"]
            audit["LibraryTrajectoryMatch"] = (
                row["LibraryBeforeCount"] == before
                and row["LibraryAfterCount"] == len(library)
                and row["NewSchemaCount"] == new_count
                and row["SchemasDiscoveredThisWorld"] == len(discovered)
            )
        audits.append(audit)
    return audits, sorted(library.values(), key=lambda record: record["SchemaID"])


def replay_challenges(k3, k5, worlds, rows, library, initial, batch, witnesses):
    audits = []
    for world, row in zip(worlds, rows):
        query_order = row["K6B"]["QueryOrder"] if "K6B" in row else row["IndexedTransfer"]["QueryOrder"]
        k6_run = replay_persistent(
            k3, k5, world["TransitionTable"], library, query_order, True,
            initial, batch, witnesses,
        )
        k5_run = k5.replay_indexed(
            k3, world["TransitionTable"], library, query_order, True,
            initial, batch, witnesses,
        )
        audit = {
            "WorldID": world["WorldID"],
            "K6BK5AFieldMatch": not mapped_k5_mismatches(k6_run, k5_run),
            "K6BK5AMismatchFields": mapped_k5_mismatches(k6_run, k5_run),
            "K6BRebuilt": k6_run,
            "K5ARebuilt": k5_run,
        }
        if "K6B" in row:
            audit["K6BReportMismatchFields"] = common_report_mismatches(k6_run, row["K6B"])
            audit["K5AReportMismatchFields"] = common_report_mismatches(k5_run, row["K5A"])
            audit["QueryOrderMatch"] = row["K6B"]["QueryOrder"] == row["K5A"]["QueryOrder"]
            audit["AvailableLibraryCountMatch"] = row["AvailableStructuredConceptCount"] == len(library)
        audits.append(audit)
    return audits


def prototype(package: Path) -> dict[str, Any]:
    k3, k4, k5, old_manifest, old_result, oracle = load_context(package)
    initial = float(old_manifest["InitialDirectObservationFraction"])
    batch = float(old_manifest["DirectQueryBatchFraction"])
    witnesses = int(old_manifest["MinimumDirectPositiveWitnessesBeforeInference"])
    maximum = int(old_manifest["MaximumConceptWordLength"])
    structured, structured_library = replay_stream(
        k3, k4, k5, oracle["StructuredWorlds"], old_result["StructuredResults"],
        initial, batch, witnesses, maximum,
    )
    controls, _ = replay_stream(
        k3, k4, k5, oracle["RankMatchedControls"], old_result["ControlResults"],
        initial, batch, witnesses, maximum,
    )
    challenges = replay_challenges(
        k3, k5, oracle["NearLawChallenges"], old_result["NearLawChallengeResults"],
        structured_library, initial, batch, witnesses,
    )
    rows = structured + controls + challenges
    actual = sum(row["K6BRebuilt"]["ActualPersistentDirectAuditItemEvaluations"] for row in rows)
    k5_checks = sum(row["K5ARebuilt"]["ActualDirectAuditStateChecks"] for row in rows)
    return {
        "WorldCount": len(rows),
        "AllK6BK5AFieldsMatch": all(row["K6BK5AFieldMatch"] for row in rows),
        "MismatchRows": [
            {"WorldID": row["WorldID"], "Fields": row["K6BK5AMismatchFields"]}
            for row in rows if not row["K6BK5AFieldMatch"]
        ],
        "ActualPersistentDirectAuditItemEvaluations": actual,
        "K5AActualDirectAuditStateChecks": k5_checks,
        "StrictReduction": actual < k5_checks,
        "ReductionFraction": 1 - actual / k5_checks if k5_checks else 0.0,
    }


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K6B_frozen_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(
        (package / "protocol" / "S132K6B_freeze_receipt.json").read_text(encoding="utf-8")
    )
    result = json.loads(
        (package / "results" / "S132K6B_result.json").read_text(encoding="utf-8")
    )
    k3, k4, k5, old_manifest, old_result, oracle = load_context(package)
    source_hash_pass = {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir()) if path.is_file()
    } == manifest["SourceHashes"]
    input_hash_pass = {
        path.name: sha256(path)
        for path in sorted((package / "input").iterdir()) if path.is_file()
    } == manifest["InputHashes"]
    manifest_hash_pass = sha256(manifest_path) == receipt["ManifestSHA256"]
    initial = float(old_manifest["InitialDirectObservationFraction"])
    batch = float(old_manifest["DirectQueryBatchFraction"])
    witnesses = int(old_manifest["MinimumDirectPositiveWitnessesBeforeInference"])
    maximum = int(old_manifest["MaximumConceptWordLength"])

    structured, structured_library = replay_stream(
        k3, k4, k5, oracle["StructuredWorlds"], result["StructuredResults"],
        initial, batch, witnesses, maximum,
    )
    controls, control_library = replay_stream(
        k3, k4, k5, oracle["RankMatchedControls"], result["ControlResults"],
        initial, batch, witnesses, maximum,
    )
    challenges = replay_challenges(
        k3, k5, oracle["NearLawChallenges"], result["NearLawChallengeResults"],
        structured_library, initial, batch, witnesses,
    )
    audits = structured + controls + challenges
    reconstruction_pass = all(
        row["K6BK5AFieldMatch"]
        and not row.get("K6BReportMismatchFields", [])
        and not row.get("K5AReportMismatchFields", [])
        and row.get("QueryOrderMatch", False)
        for row in audits
    )
    library_pass = (
        structured_library == result["FinalStructuredLibrary"]
        and control_library == result["FinalControlLibrary"]
        and all(row.get("LibraryTrajectoryMatch", True) for row in structured + controls)
        and all(row.get("AvailableLibraryCountMatch", True) for row in challenges)
    )

    new_rows = result["StructuredResults"] + result["ControlResults"] + result["NearLawChallengeResults"]
    frozen_rows = old_result["StructuredResults"] + old_result["ControlResults"] + old_result["NearLawChallengeResults"]
    frozen_reproduction = all(
        not mapped_k5_mismatches(k6, old["IndexedTransfer"])
        for k6, old in zip((row["K6B"] for row in new_rows), frozen_rows)
    )
    actual = sum(row["K6B"]["ActualPersistentDirectAuditItemEvaluations"] for row in new_rows)
    k5_checks = sum(row["K5A"]["ActualDirectAuditStateChecks"] for row in new_rows)
    trace_lookups = sum(row["K6B"]["ActualPersistentDirectAuditTraceCellLookups"] for row in new_rows)
    k6_runtime = sum(float(row["K6BRuntimeSeconds"]) for row in new_rows)
    k5_runtime = sum(float(row["K5ARuntimeSeconds"]) for row in new_rows)
    all_exact = all(row[label]["FinalExact"] for row in new_rows for label in ("K6B", "K5A"))
    unsafe = sum(row[label]["UnsafeCommittedInferenceCount"] for row in new_rows for label in ("K6B", "K5A"))
    all_arrays_packed = all(row["K6B"]["AllNumericAuditArraysPacked"] for row in new_rows)
    strict_work_reduction = actual < k5_checks
    runtime_improved = k6_runtime < k5_runtime
    recomputed_gate = (
        reconstruction_pass and library_pass and frozen_reproduction
        and all_exact and unsafe == 0 and strict_work_reduction and runtime_improved
        and all_arrays_packed
    )
    aggregate_checks = {
        "AllK6BK5AFieldsMatch": result["AllK6BK5AFieldsMatch"] == reconstruction_pass,
        "FrozenK5BTransferRowsReproduced": result["FrozenK5BTransferRowsReproduced"] == frozen_reproduction,
        "AllFinalModelsExact": result["AllFinalModelsExact"] == all_exact,
        "UnsafeCommittedInferenceCount": result["UnsafeCommittedInferenceCount"] == unsafe,
        "ActualPersistentDirectAuditItemEvaluations": result["ActualPersistentDirectAuditItemEvaluations"] == actual,
        "K5AActualDirectAuditStateChecks": result["K5AActualDirectAuditStateChecks"] == k5_checks,
        "ActualPersistentDirectAuditTraceCellLookups": result["ActualPersistentDirectAuditTraceCellLookups"] == trace_lookups,
        "AggregateK6BRuntimeSeconds": abs(float(result["AggregateK6BRuntimeSeconds"]) - k6_runtime) < 1e-8,
        "AggregateK5ARuntimeSeconds": abs(float(result["AggregateK5ARuntimeSeconds"]) - k5_runtime) < 1e-8,
        "RuntimeImproved": result["RuntimeImproved"] == runtime_improved,
        "AllNumericAuditArraysPacked": result["AllNumericAuditArraysPacked"] == all_arrays_packed,
        "PackedOptimizationGatePass": result["PackedOptimizationGatePass"] == recomputed_gate,
    }
    aggregate_pass = all(aggregate_checks.values())
    evidence_integrity = (
        source_hash_pass and input_hash_pass and manifest_hash_pass
        and reconstruction_pass and library_pass and frozen_reproduction
        and aggregate_pass
    )
    scientific_pass = evidence_integrity and recomputed_gate
    conclusion = (
        "VERIFIED_RETROSPECTIVE_EXACT_PACKED_WITNESS_OPTIMIZATION_GATE_PASS"
        if scientific_pass else
        "VERIFIED_RETROSPECTIVE_PACKED_WITNESS_OPTIMIZATION_GATE_NOT_PASSED"
    )
    verification = {
        "Stage": "S132-K6B independent semantic and aggregate replay",
        "SourceHashPass": source_hash_pass,
        "InputHashPass": input_hash_pass,
        "ManifestHashPass": manifest_hash_pass,
        "AllPythonTraceReconstructionsExact": reconstruction_pass,
        "FinalLibraryReconstructionPass": library_pass,
        "FrozenK5BTransferRowsReproduced": frozen_reproduction,
        "AggregateRecomputationPass": aggregate_pass,
        "EvidenceIntegrityPass": evidence_integrity,
        "ScientificGatePass": scientific_pass,
        "RecomputedPackedOptimizationGatePass": recomputed_gate,
        "StructuredAudits": structured,
        "ControlAudits": controls,
        "NearLawAudits": challenges,
        "AggregateChecks": aggregate_checks,
        "RecomputedMetrics": {
            "ActualPersistentDirectAuditItemEvaluations": actual,
            "K5AActualDirectAuditStateChecks": k5_checks,
            "PersistentAuditReductionFraction": 1 - actual / k5_checks if k5_checks else 0.0,
            "ActualPersistentDirectAuditTraceCellLookups": trace_lookups,
            "AggregateK6BRuntimeSeconds": k6_runtime,
            "AggregateK5ARuntimeSeconds": k5_runtime,
            "PairedRuntimeSpeedup": k5_runtime / k6_runtime if k6_runtime else 0.0,
        },
        "RetrospectiveOpenedWorldsOnly": True,
        "CanonicalTCCTModified": False,
        "FinalConclusion": conclusion,
    }
    dump(package / "verification" / "S132K6B_independent_verification.json", verification)
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--prototype", action="store_true")
    args = parser.parse_args()
    package = args.package.resolve()
    if args.prototype:
        output = prototype(package)
        print(json.dumps(output, ensure_ascii=False))
        raise SystemExit(0 if output["AllK6BK5AFieldsMatch"] else 1)
    output = verify(package)
    print(json.dumps({
        "EvidenceIntegrityPass": output["EvidenceIntegrityPass"],
        "ScientificGatePass": output["ScientificGatePass"],
        "FinalConclusion": output["FinalConclusion"],
    }, ensure_ascii=False))
    raise SystemExit(0 if output["EvidenceIntegrityPass"] else 1)


if __name__ == "__main__":
    main()
