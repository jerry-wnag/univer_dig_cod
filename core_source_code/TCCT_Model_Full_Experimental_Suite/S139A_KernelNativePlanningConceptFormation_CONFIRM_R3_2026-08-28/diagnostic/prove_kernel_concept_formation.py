from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from adaptive_geometry import apply_program, models, query_specs  # noqa: E402
from kernel_concept_dp import Planner, branches, decision_count, find_plan, induce_concepts  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def optimal_inputs(rows: list[dict[str, Any]], unused: list[str], depth: int,
                   queries: list[dict[str, Any]]) -> list[str]:
    optimal = []
    for query_hash in sorted(unused):
        remaining = [item for item in unused if item != query_hash]
        planner = Planner(queries, None)
        if all(planner.solve(branch, remaining, depth - 1)[0] for branch in branches(rows, query_hash)):
            optimal.append(query_hash)
    return optimal


def execute(task: dict[str, Any], hidden: dict[str, Any], concepts: dict[str, Any] | None,
            collect_events: bool) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    queries = query_specs(task)
    query_by = {row["InputSHA256"]: row for row in queries}
    rows, unused, trace, events = models(task), [row["InputSHA256"] for row in queries], [], []
    total_work = 0
    initial = find_plan(rows, queries, 3, concepts, unused)
    initial_depth = initial["RequiredDepth"]
    while decision_count(rows) > 1 and len(trace) < 3:
        plan = initial if not trace else find_plan(rows, queries, 3 - len(trace), concepts, unused)
        total_work += plan["WorkCounters"]["QueryEvaluationCount"]
        if not plan["Solvable"] or plan["RequiredDepth"] == 0:
            break
        query_hash = plan["FirstInputSHA256"]
        if collect_events:
            events.append({"TaskID": task["TaskID"], "Rows": rows,
                           "UnusedInputSHA256": list(unused),
                           "PlanningDepth": plan["RequiredDepth"],
                           "OptimalInputSHA256": optimal_inputs(rows, unused, plan["RequiredDepth"], queries)})
        query = query_by[query_hash]
        output = apply_program(task, hidden, query)
        rows = [row for row in rows if row["QueryPredictions"][query_hash] == output]
        unused.remove(query_hash)
        trace.append(query_hash)
    return {
        "InitialDepth": initial_depth, "ActiveQueryCount": len(trace),
        "DecisionCertified": decision_count(rows) == 1,
        "Prediction": rows[0]["TestPrediction"] if decision_count(rows) == 1 else None,
        "InitialWorkCounters": initial["WorkCounters"], "TotalQueryEvaluationCount": total_work,
    }, events


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    oracle = load(ROOT / "sealed" / "oracle_responses.json")
    hidden_by = {row["TaskID"]: row["HiddenProgram"] for row in oracle["Tasks"]}
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    source_rows, events = [], []
    for task in public["SourceTasks"]:
        result, task_events = execute(task, hidden_by[task["TaskID"]], None, True)
        source_rows.append({"TaskID": task["TaskID"], **result})
        events.extend(task_events)
    concepts = induce_concepts(events)
    target_rows = []
    for task in public["TargetTasks"]:
        guided, _ = execute(task, hidden_by[task["TaskID"]], concepts, False)
        baseline, _ = execute(task, hidden_by[task["TaskID"]], None, False)
        sealed_row = sealed_by[task["TaskID"]]
        exact = guided["Prediction"] == sealed_row["TestOutputs"][0]["Output"]
        target_rows.append({
            "TaskID": task["TaskID"], "Role": sealed_row["ExpectedRole"],
            "ExpectedMinimumDepth": sealed_row["ExpectedMinimumGuaranteedDepth"],
            "GuidedInitialDepth": guided["InitialDepth"], "BaselineInitialDepth": baseline["InitialDepth"],
            "GuidedActiveQueryCount": guided["ActiveQueryCount"], "Exact": exact,
            "GuidedInitialWorkCounters": guided["InitialWorkCounters"],
            "BaselineInitialWorkCounters": baseline["InitialWorkCounters"],
            "GuidedTotalQueryEvaluationCount": guided["TotalQueryEvaluationCount"],
            "BaselineTotalQueryEvaluationCount": baseline["TotalQueryEvaluationCount"],
        })
    role_by = {row["Role"]: row for row in target_rows}
    all_depth = all(row["GuidedInitialDepth"] == row["BaselineInitialDepth"] ==
                    row["ExpectedMinimumDepth"] for row in target_rows)
    all_exact = all(row["Exact"] for row in target_rows)
    transfer_roles = {"SURFACE_PERMUTATION_TRANSFER", "COORDINATE_SCALE_TRANSFER",
                      "SEQUENTIAL_CONCEPT_COMPOSITION"}
    transfer_reduction = sum(row["GuidedTotalQueryEvaluationCount"] for row in target_rows
                             if row["Role"] in transfer_roles) < sum(
        row["BaselineTotalQueryEvaluationCount"] for row in target_rows if row["Role"] in transfer_roles)
    adversarial_rejection = role_by["ADVERSARIAL_CONCEPT_REJECTION"][
        "GuidedInitialWorkCounters"]["ConceptPreferredQueryRejectedCount"] > 0
    no_reuse_fallback = role_by["NO_REUSABLE_CONCEPT_FALLBACK"][
        "GuidedInitialWorkCounters"]["ConceptNoCandidateStateCount"] > 0
    source_depths = [row["InitialDepth"] for row in source_rows]
    concept_support = concepts["ConceptCount"] >= 2 and all(
        concept["SupportEventCount"] >= 2 and concept["DistinctSourceTaskSupportCount"] >= 2 and
        concept["TrainingFalsePositiveCount"] == 0 for concept in concepts["Concepts"])
    passed = source_depths == [3, 2, 1] and len(events) >= 3 and concept_support and all_depth and all_exact and \
        transfer_reduction and adversarial_rejection and no_reuse_fallback
    certificate = {
        "Stage": protocol["Stage"], "CertificateType": "INDEPENDENT_KERNEL_CONCEPT_DIFFICULTY_AUDIT",
        "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "SourceResults": source_rows, "SourcePlanningEventCount": len(events),
        "IndependentlyInducedConceptLibrary": concepts, "TargetAudits": target_rows,
        "AllMinimumDepthsExact": all_depth, "AllTargetAnswersExact": all_exact,
        "TransferPlanningWorkReduced": transfer_reduction,
        "AdversarialConceptRejectedByExactDP": adversarial_rejection,
        "NoReusableConceptFallbackExercised": no_reuse_fallback,
        "PostSeedWorldFilteringUsed": False, "DifficultyCertificatePass": passed,
    }
    destination = ROOT / "diagnostic" / "kernel_concept_certificate.json"
    destination.write_text(json.dumps(certificate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: certificate[key] for key in (
        "SourcePlanningEventCount", "AllMinimumDepthsExact", "AllTargetAnswersExact",
        "TransferPlanningWorkReduced", "AdversarialConceptRejectedByExactDP",
        "NoReusableConceptFallbackExercised", "DifficultyCertificatePass")}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
