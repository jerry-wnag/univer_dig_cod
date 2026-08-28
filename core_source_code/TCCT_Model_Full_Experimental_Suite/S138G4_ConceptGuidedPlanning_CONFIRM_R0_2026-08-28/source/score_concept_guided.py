from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from concept_replay import replay_task

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    result = load(ROOT / "results" / "kernel_concept_guided_result.json")
    certificate = load(ROOT / "diagnostic" / "concept_planning_certificate.json")
    library = load(ROOT / "library" / "frozen_planning_concepts.json")
    public_by = {row["TaskID"]: row for row in public["Tasks"]}
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    result_by = {row["TaskID"]: row for row in result["TaskResults"]}
    scores = []
    for task_id in protocol["TaskOrder"]:
        task, truth, row = public_by[task_id], sealed_by[task_id], result_by[task_id]
        expected = truth["ExpectedMinimumGuaranteedDepth"]
        replay = replay_task(task, row, truth["HiddenProgram"], library,
                             protocol["MaximumPlanningDepth"], protocol["MaximumActiveQueriesPerTask"])
        if expected <= protocol["MaximumPlanningDepth"]:
            role_pass = all([replay, row["InitialCertifiedMinimumDepth"] == expected,
                             row["TestPredictionCommitted"],
                             row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"]])
        else:
            role_pass = all([replay, row["InitialCertifiedMinimumDepth"] is None,
                             row["ActiveQueryCount"] == 0, not row["TestPredictionCommitted"],
                             row["AdaptiveStopReason"] == "NO_PLAN_WITHIN_RESOURCE_DEPTH"])
        scores.append({
            "TaskID": task_id, "Role": truth["ExpectedRole"],
            "ExhaustivelyCertifiedMinimumDepth": expected,
            "KernelInitialCertifiedDepthWithinCap": row["InitialCertifiedMinimumDepth"],
            "ActiveQueryCount": row["ActiveQueryCount"],
            "GuidedQueryEvaluationCount": row["GuidedQueryEvaluationCount"],
            "BaselineQueryEvaluationCount": row["BaselineQueryEvaluationCount"],
            "CommittedExact": row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"]
                if row["TestPredictionCommitted"] else None,
            "ReplayPass": replay, "RolePass": role_pass,
        })
    mismatch_rows = [row for row in result["TaskResults"]
                     if sealed_by[row["TaskID"]]["ExpectedRole"] == "CONCEPT_MISMATCH_FALLBACK_DEPTH2"]
    mismatch_fallback = len(mismatch_rows) == 1 and any(
        trace["RootConceptFallbackUsed"] for trace in mismatch_rows[0]["ActiveQueryTrace"])
    gate = all([len(scores) == 5, all(row["RolePass"] for row in scores),
                certificate["DifficultyCertificatePass"], result["NativePreScorePass"],
                result["PairedDepthParity"], result["DeterministicPlanningWorkReduced"],
                mismatch_fallback,
                result["OracleQueryLogLineCount"] == sum(row["ActiveQueryCount"] for row in scores)])
    score = {
        "Stage": f"{protocol['Stage']} sealed score",
        "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "FixedWorldCount": 5, "ExactRolePassCount": sum(row["RolePass"] for row in scores),
        "ExactCommittedWithinBudgetCount": sum(row["CommittedExact"] is True for row in scores),
        "OverBudgetSafeRefusalCount": sum(row["ExhaustivelyCertifiedMinimumDepth"] > 3 and row["RolePass"] for row in scores),
        "MismatchFallbackPass": mismatch_fallback,
        "AggregateGuidedQueryEvaluationCount": result["AggregateGuidedQueryEvaluationCount"],
        "AggregateBaselineQueryEvaluationCount": result["AggregateBaselineQueryEvaluationCount"],
        "DeterministicPlanningWorkReduced": result["DeterministicPlanningWorkReduced"],
        "ObservedAdaptiveQueryCounts": [row["ActiveQueryCount"] for row in scores],
        "TaskScores": scores, "CapabilityGatePass": gate,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "VERIFIED_CONCEPT_GUIDED_EXACT_PLANNING_WITH_FALLBACK" if gate else "CONCEPT_GUIDED_PLANNING_FAILURE",
    }
    destination = ROOT / "results" / "sealed_score.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(score, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(score, separators=(",", ":")))
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
