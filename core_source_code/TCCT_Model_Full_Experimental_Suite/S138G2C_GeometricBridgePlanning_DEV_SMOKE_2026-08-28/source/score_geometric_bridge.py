from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from geometric_replay import replay_task

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    result = load(ROOT / "results" / "kernel_geometric_planning_result.json")
    difficulty = load(ROOT / "diagnostic" / "difficulty_certificate.json")
    public_by = {row["TaskID"]: row for row in public["Tasks"]}
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    result_by = {row["TaskID"]: row for row in result["TaskResults"]}
    scores = []
    for task_id in protocol["TaskOrder"]:
        task, truth, row = public_by[task_id], sealed_by[task_id], result_by[task_id]
        replay = replay_task(task, row, truth["HiddenProgram"])
        if truth["ExpectedRole"] == "GEOMETRIC_TWO_STEP_BRIDGE":
            role_pass = all([
                replay, row["ActiveQueryCount"] == 2,
                row["ActiveQueryTrace"][0]["AdmissionMode"] == "TWO_STEP_BRIDGE_CERTIFICATE",
                row["ActiveQueryTrace"][1]["AdmissionMode"] == "IMMEDIATE_DECISION_GAIN",
                row["TestPredictionCommitted"],
                row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"],
            ])
        else:
            role_pass = all([
                replay, row["ActiveQueryCount"] == 0, not row["TestPredictionCommitted"],
                row["FinalDecisionClassCount"] > 1,
                row["AdaptiveStopReason"] == "NO_DEPTH2_DECISION_PLAN",
                row["RemainingImmediateDecisionQueryCount"] == 0,
                row["RemainingTwoStepBridgeQueryCount"] == 0,
            ])
        scores.append({
            "TaskID": task_id, "Role": truth["ExpectedRole"], "RolePass": role_pass,
            "ReplayPass": replay, "ActiveQueryCount": row["ActiveQueryCount"],
            "InitialDecisionClassCount": row["InitialDecisionClassCount"],
            "FinalDecisionClassCount": row["FinalDecisionClassCount"],
            "CommittedExact": row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"]
                if row["TestPredictionCommitted"] else None,
        })
    positives = [row for row in scores if row["Role"] == "GEOMETRIC_TWO_STEP_BRIDGE"]
    controls = [row for row in scores if row["Role"] == "GEOMETRIC_IRREDUCIBLE_CONTROL"]
    gate = all([
        len(positives) == 3, len(controls) == 2, all(row["RolePass"] for row in scores),
        difficulty["DifficultyCertificatePass"], result["NativePreScorePass"],
        result["OracleQueryLogLineCount"] == sum(row["ActiveQueryCount"] for row in scores),
    ])
    score = {
        "Stage": f"{protocol['Stage']} sealed score", "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "FixedWorldCount": 5, "GeometricBridgePassCount": sum(row["RolePass"] for row in positives),
        "GeometricIrreducibleControlPassCount": sum(row["RolePass"] for row in controls),
        "OracleQueryCount": sum(row["ActiveQueryCount"] for row in scores),
        "ObservedAdaptiveQueryCounts": [row["ActiveQueryCount"] for row in scores],
        "TaskScores": scores, "CapabilityGatePass": gate,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "THREE_GEOMETRIC_BRIDGE_TWO_CONTROL_PASS" if gate else "GEOMETRIC_BRIDGE_FIVE_WORLD_FAILURE",
    }
    destination = ROOT / "results" / "sealed_score.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(score, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(score, separators=(",", ":")))
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
