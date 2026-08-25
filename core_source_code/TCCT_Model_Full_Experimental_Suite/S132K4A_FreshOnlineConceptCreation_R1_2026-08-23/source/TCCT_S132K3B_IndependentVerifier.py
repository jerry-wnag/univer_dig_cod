"""Independent Python reconstruction of S132-K3B partial-observation learning."""

from __future__ import annotations

import hashlib
import itertools
import json
import math
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_key(state: int, action: int) -> str:
    return f"{state}:{action}"


def instantiate(schemas: list[dict[str, Any]], action_count: int) -> list[dict[str, Any]]:
    instances = []
    for row in schemas:
        long_pattern, short_pattern = row["Schema"]
        variable_count = max(long_pattern + short_pattern, default=0)
        if variable_count > action_count:
            continue
        for assignment in itertools.permutations(range(1, action_count + 1), variable_count):
            instances.append({
                "SchemaID": int(row["SchemaID"]),
                "Long": [assignment[index - 1] for index in long_pattern],
                "Short": [assignment[index - 1] for index in short_pattern],
            })
    instances.sort(key=lambda row: (row["SchemaID"], row["Long"], row["Short"]))
    for next_id, row in enumerate(instances, start=1):
        row["InstanceID"] = next_id
    return instances


def trace(start: int, word: list[int], values: dict[str, dict[str, Any]]) -> dict[str, Any]:
    state = start
    provenance: list[int] = []
    if not word:
        return {"Status": "Complete", "Target": state, "Provenance": []}
    for index, action in enumerate(word):
        key = cell_key(state, action)
        if key not in values:
            status = "MissingFinal" if index == len(word) - 1 else "Blocked"
            output = {"Status": status, "Provenance": sorted(set(provenance))}
            if status == "MissingFinal":
                output["CellKey"] = key
            return output
        record = values[key]
        provenance.extend(record.get("Provenance", []))
        state = int(record["Target"])
    return {"Status": "Complete", "Target": state, "Provenance": sorted(set(provenance))}


def witness_audit(instance: dict[str, Any], direct: dict[str, dict[str, Any]], state_count: int) -> tuple[int, bool]:
    witnesses = 0
    for state in range(1, state_count + 1):
        left = trace(state, instance["Long"], direct)
        right = trace(state, instance["Short"], direct)
        if left["Status"] == right["Status"] == "Complete":
            if left["Target"] != right["Target"]:
                return witnesses, True
            witnesses += 1
    return witnesses, False


def add_direct(direct: dict[str, dict[str, Any]], table: list[list[int]], key: str) -> None:
    state, action = map(int, key.split(":"))
    direct[key] = {"Target": table[state - 1][action - 1], "Direct": True, "Provenance": []}


def closure(direct: dict[str, dict[str, Any]], instances: list[dict[str, Any]], rejected_input: list[int], state_count: int, minimum_witnesses: int) -> dict[str, Any]:
    rejected = set(map(int, rejected_input))
    inference_created = 0
    internal_rollbacks = 0
    direct_rejected = 0
    conflict_rejected = 0
    while True:
        values = {key: dict(value) for key, value in direct.items()}
        active = [row for row in instances if row["InstanceID"] not in rejected]
        audits = {row["InstanceID"]: witness_audit(row, direct, state_count) for row in active}
        contradicted = [row for row in active if audits[row["InstanceID"]][1]]
        if contradicted:
            ids = {row["InstanceID"] for row in contradicted}
            rejected.update(ids)
            direct_rejected += len(ids)
            internal_rollbacks += 1
            continue
        admissible = [row for row in active if audits[row["InstanceID"]][0] >= minimum_witnesses]
        restart = False
        changed = True
        while changed and not restart:
            changed = False
            proposals: list[dict[str, Any]] = []
            for instance in admissible:
                for state in range(1, state_count + 1):
                    left = trace(state, instance["Long"], values)
                    right = trace(state, instance["Short"], values)
                    if left["Status"] == "Complete" and right["Status"] == "MissingFinal":
                        proposals.append({
                            "CellKey": right["CellKey"], "Target": left["Target"],
                            "Provenance": sorted(set([instance["InstanceID"]] + left["Provenance"] + right["Provenance"])),
                        })
                    if right["Status"] == "Complete" and left["Status"] == "MissingFinal":
                        proposals.append({
                            "CellKey": left["CellKey"], "Target": right["Target"],
                            "Provenance": sorted(set([instance["InstanceID"]] + left["Provenance"] + right["Provenance"])),
                        })
            grouped: dict[str, list[dict[str, Any]]] = {}
            for proposal in proposals:
                grouped.setdefault(proposal["CellKey"], []).append(proposal)
            conflict_groups = [
                candidates for candidates in grouped.values()
                if len({row["Target"] for row in candidates}) > 1
            ]
            if conflict_groups:
                implicated = set().union(*(
                    set(row["Provenance"])
                    for candidates in conflict_groups for row in candidates
                ))
                rejected.update(implicated)
                conflict_rejected += len(implicated)
                internal_rollbacks += 1
                restart = True
            else:
                for key in sorted(grouped):
                    candidates = grouped[key]
                    record = {
                        "Target": candidates[0]["Target"],
                        "Provenance": sorted(set().union(*(
                            set(row["Provenance"]) for row in candidates
                        ))),
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
                        values[key] = {"Target": record["Target"], "Direct": False, "Provenance": list(record["Provenance"])}
                        inference_created += 1
                        changed = True
        if not restart:
            return {
                "Values": values,
                "RejectedInstanceIDs": sorted(rejected),
                "InferenceCreatedCount": inference_created,
                "InternalRollbackCount": internal_rollbacks,
                "DirectContradictionRejectedCount": direct_rejected,
                "InferenceConflictRejectedCount": conflict_rejected,
            }


def equivalence(values: dict[str, dict[str, Any]], table: list[list[int]]) -> dict[str, Any]:
    inspected = 0
    for state, row in enumerate(table, start=1):
        for action, target in enumerate(row, start=1):
            inspected += 1
            key = cell_key(state, action)
            if key not in values:
                return {"Exact": False, "InspectedCells": inspected, "MismatchKey": key}
            if int(values[key]["Target"]) != int(target):
                return {"Exact": False, "InspectedCells": inspected, "MismatchKey": key, "Provenance": list(values[key]["Provenance"])}
    return {"Exact": True, "InspectedCells": inspected}


def replay(table: list[list[int]], schemas: list[dict[str, Any]], order: list[str], transfer_enabled: bool, initial_fraction: float, batch_fraction: float, minimum_witnesses: int) -> dict[str, int | bool]:
    state_count = len(table)
    action_count = len(table[0])
    total = state_count * action_count
    initial = math.ceil(initial_fraction * total) if transfer_enabled else total
    batch_size = max(1, math.ceil(batch_fraction * total))
    instances = instantiate(schemas, action_count) if transfer_enabled else []
    direct: dict[str, dict[str, Any]] = {}
    membership = 0
    for key in order[:initial]:
        add_direct(direct, table, key)
        membership += 1
    rejected: list[int] = []
    eq_calls = eq_cells = counterexamples = rollback_count = 0
    inference_created = internal_rollbacks = direct_rejected = conflict_rejected = 0
    exact = False
    values: dict[str, dict[str, Any]] = {}
    while not exact:
        closed = closure(direct, instances, rejected, state_count, minimum_witnesses)
        values = closed["Values"]
        rejected = closed["RejectedInstanceIDs"]
        inference_created += int(closed["InferenceCreatedCount"])
        internal_rollbacks += int(closed["InternalRollbackCount"])
        direct_rejected += int(closed["DirectContradictionRejectedCount"])
        conflict_rejected += int(closed["InferenceConflictRejectedCount"])
        missing = [key for key in order if key not in values]
        if missing:
            for key in missing[:batch_size]:
                add_direct(direct, table, key)
                membership += 1
            continue
        check = equivalence(values, table)
        eq_calls += 1
        eq_cells += int(check["InspectedCells"])
        if check["Exact"]:
            exact = True
            break
        counterexamples += 1
        rejected = sorted(set(rejected) | set(check.get("Provenance", [])))
        add_direct(direct, table, check["MismatchKey"])
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
    }


def compare_run(rebuilt: dict[str, Any], reported: dict[str, Any]) -> tuple[bool, list[str]]:
    mismatches = [key for key, value in rebuilt.items() if value != reported[key]]
    return not mismatches, mismatches


def verify(package: Path) -> dict[str, Any]:
    manifest = json.loads((package / "protocol" / "S132K3B_frozen_manifest.json").read_text(encoding="utf-8"))
    result = json.loads((package / "results" / "S132K3B_result.json").read_text(encoding="utf-8"))
    schema_input = json.loads((package / "input" / "S132K3B_schema_library.json").read_text(encoding="utf-8"))
    test_input = json.loads((package / "input" / "S132K3B_test_automata.json").read_text(encoding="utf-8"))
    control_input = json.loads((package / "input" / "S132K3B_control_automata.json").read_text(encoding="utf-8"))
    schemas = schema_input["Schemas"]
    tests = {row["WorldID"]: row for row in test_input["Automata"]}
    controls = {row["WorldID"]: row for row in control_input["Controls"]}
    source_hash_pass = all(sha256(package / "source" / name) == expected for name, expected in manifest["SourceHashes"].items())
    input_hash_pass = all(sha256(package / "input" / name) == expected for name, expected in manifest["InputHashes"].items())
    schema_pass = int(schema_input["SchemaCount"]) == int(manifest["SchemaCount"]) == len(schemas) == 134

    def reconstruct(row: dict[str, Any], world: dict[str, Any]) -> dict[str, Any]:
        audit = {"WorldID": row["WorldID"]}
        for label, enabled in (("Transfer", True), ("Baseline", False)):
            rebuilt = replay(world["TransitionTable"], schemas, row[label]["QueryOrder"], enabled, float(manifest["InitialDirectObservationFraction"]), float(manifest["DirectQueryBatchFraction"]), int(manifest["MinimumDirectPositiveWitnessesBeforeInference"]))
            passed, mismatches = compare_run(rebuilt, row[label])
            audit[label + "ReconstructionPass"] = passed
            audit[label + "MismatchFields"] = mismatches
        audit["PairedArithmeticPass"] = (
            int(row["MembershipQuerySavings"]) == int(row["Baseline"]["MembershipQueries"]) - int(row["Transfer"]["MembershipQueries"])
            and int(row["LogicalInteractionCostSavings"]) == int(row["Baseline"]["LogicalInteractionCost"]) - int(row["Transfer"]["LogicalInteractionCost"])
            and int(row["ConcreteOracleCellCostSavings"]) == int(row["Baseline"]["ConcreteOracleCellCost"]) - int(row["Transfer"]["ConcreteOracleCellCost"])
        )
        return audit

    test_audits = [reconstruct(row, tests[row["WorldID"]]) for row in result["TestResults"]]
    control_audits = [reconstruct(row, controls[row["WorldID"]]) for row in result["ControlResults"]]
    tests_pass = all(row["TransferReconstructionPass"] and row["BaselineReconstructionPass"] and row["PairedArithmeticPass"] for row in test_audits)
    controls_pass = all(row["TransferReconstructionPass"] and row["BaselineReconstructionPass"] and row["PairedArithmeticPass"] for row in control_audits)
    mq_savings = sum(int(row["MembershipQuerySavings"]) for row in result["TestResults"])
    logical_savings = sum(int(row["LogicalInteractionCostSavings"]) for row in result["TestResults"])
    concrete_savings = sum(int(row["ConcreteOracleCellCostSavings"]) for row in result["TestResults"])
    positive_worlds = sum(int(row["MembershipQuerySavings"]) > 0 for row in result["TestResults"])
    aggregate_pass = int(result["AggregateMembershipQuerySavings"]) == mq_savings and int(result["AggregateLogicalInteractionCostSavings"]) == logical_savings and int(result["AggregateConcreteOracleCellCostSavings"]) == concrete_savings and int(result["PositiveMembershipQuerySavingsWorldCount"]) == positive_worlds
    expected_gate = tests_pass and controls_pass and int(result["UnsafeCommittedInferenceCount"]) == 0 and positive_worlds >= 4 and mq_savings > 0 and concrete_savings > 0
    boundary_pass = result["K2WorldsOpenedBeforeProtocolFreeze"] is True and result["CanonicalTCCTModified"] is False and result["CompleteTransitionTableUsedForSchemaPrefilter"] is False and result["B8ASymbolicLearnerIntegrationProven"] is False and result["FreshWorldTransferProven"] is False and result["OpenEndedLanguageInventionProven"] is False
    integrity = source_hash_pass and input_hash_pass and schema_pass and tests_pass and controls_pass and aggregate_pass and boundary_pass and bool(result["RetrospectivePartialObservationGatePass"]) == expected_gate
    conclusion = "VERIFIED_RETROSPECTIVE_PARTIAL_OBSERVATION_TRANSFER_GATE_PASS" if integrity and expected_gate else "EVIDENCE_VALID_BUT_PARTIAL_OBSERVATION_GATE_NOT_PASSED" if integrity else "VERIFICATION_FAILED"
    return {
        "Stage": "S132-K3B independent Python reconstruction",
        "SourceHashPass": source_hash_pass,
        "InputHashPass": input_hash_pass,
        "FrozenSchemaLibraryPass": schema_pass,
        "TestAudits": test_audits,
        "ControlAudits": control_audits,
        "IndependentTestReconstructionPass": tests_pass,
        "IndependentControlReconstructionPass": controls_pass,
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
    output = package / "verification" / "S132K3B_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
