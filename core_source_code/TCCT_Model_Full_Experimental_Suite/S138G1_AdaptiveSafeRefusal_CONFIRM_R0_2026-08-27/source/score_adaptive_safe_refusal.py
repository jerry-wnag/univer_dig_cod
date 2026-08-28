from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_trace_audit(row: dict[str, Any]) -> dict[str, Any]:
    trace = row["ActiveQueryTrace"]
    chain_ok = True
    expected_before = row["InitialDecisionClassCount"]
    hashes: list[str] = []
    for query in trace:
        before = query["DecisionClassCountBefore"]
        after = query["DecisionClassCountAfter"]
        worst_case = query["SelectedScore"][
            "WorstCaseRemainingDecisionClassCount"
        ]
        chain_ok = chain_ok and all(
            [
                before == expected_before,
                after < before,
                worst_case < before,
                after <= worst_case,
                query["GeneratedByTCCTKernel"],
                query["Derivation"]
                == "PROOF_CONSTRUCTED_SYMMETRY_PRESERVING_SUPPORT_TRAP",
                not query["TestOutputAccessed"],
                not query["GeneratorFamilyAccessed"],
            ]
        )
        hashes.append(query["InputSHA256"])
        expected_before = after
    chain_ok = chain_ok and expected_before == row["FinalDecisionClassCount"]
    return {
        "StrictDecisionReductionTracePass": chain_ok,
        "QueryTraceCountPass": len(trace) == row["ActiveQueryCount"],
        "UniqueQueryInputPass": len(hashes) == len(set(hashes)),
    }


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    result = load(ROOT / "results" / "kernel_intervention_result.json")
    difficulty = load(ROOT / "diagnostic" / "difficulty_certificate.json")
    by_id = {row["TaskID"]: row for row in result["TaskResults"]}
    task_scores = []
    for task_id in protocol["ControlTaskIDs"]:
        row = by_id[task_id]
        trace_audit = strict_trace_audit(row)
        adaptive_safe_refusal = all(
            [
                row["InitialDecisionClassCount"] > 1,
                row["FinalDecisionClassCount"] > 1,
                not row["DecisionCertified"],
                not row["ModelIdentified"],
                not row["TestPredictionCommitted"],
                row["ActiveQueryCount"]
                <= protocol["MaximumActiveQueriesPerTask"],
                row["ActiveQueryCount"]
                <= row["FrozenInterventionUniverseCount"],
                row["RemainingUnusedInterventionCount"] > 0,
                row["RemainingInformativeInterventionCount"] == 0,
                row["EverySelectedQueryStrictlyReducedDecisionClasses"],
                row["EverySelectedQueryHadStrictWorstCaseDecisionGain"],
                trace_audit["StrictDecisionReductionTracePass"],
                trace_audit["QueryTraceCountPass"],
                trace_audit["UniqueQueryInputPass"],
                row["AdaptiveStopReason"] == "NO_INFORMATIVE_QUERY",
                row["Status"] == "DECISION_AMBIGUOUS_NO_INFORMATIVE_QUERY",
                row["FrozenInterventionUniverseCount"]
                == protocol["SupportTrapDoubleNeutralQuota"],
            ]
        )
        task_scores.append(
            {
                "TaskID": task_id,
                "AdaptiveSafeRefusal": adaptive_safe_refusal,
                "InitialSemanticClassCount": row["InitialSemanticClassCount"],
                "InitialDecisionClassCount": row["InitialDecisionClassCount"],
                "FinalSemanticClassCount": row["FinalSemanticClassCount"],
                "FinalDecisionClassCount": row["FinalDecisionClassCount"],
                "ActiveQueryCount": row["ActiveQueryCount"],
                "RemainingInformativeInterventionCount": row[
                    "RemainingInformativeInterventionCount"
                ],
                "RemainingUnusedInterventionCount": row[
                    "RemainingUnusedInterventionCount"
                ],
                "StrictDecisionReductionTracePass": trace_audit[
                    "StrictDecisionReductionTracePass"
                ],
                "AdaptiveStopReason": row["AdaptiveStopReason"],
                "Status": row["Status"],
            }
        )

    refusal_count = sum(row["AdaptiveSafeRefusal"] for row in task_scores)
    useful_query_task_count = sum(row["ActiveQueryCount"] > 0 for row in task_scores)
    total_queries = sum(row["ActiveQueryCount"] for row in task_scores)
    challenge_pass = useful_query_task_count >= protocol[
        "MinimumTasksRequiringUsefulAdaptiveQueries"
    ]
    gate = all(
        [
            len(task_scores) == 5,
            refusal_count == 5,
            challenge_pass,
            difficulty["DifficultyCertificatePass"],
            difficulty[
                "AllFiveStructuralTriosIndistinguishableOnAllowedInterventions"
            ],
            difficulty["AllFiveTestsHaveThreeDistinctStructuralPredictions"],
            result["NativePreScorePass"],
            result["OracleQueryLogLineCount"] == total_queries,
            result["InventedConceptLibrary"] == [],
        ]
    )
    score = {
        "Stage": f"{protocol['Stage']} sealed adaptive-refusal score",
        "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "FixedControlWorldCount": len(task_scores),
        "AdaptiveSafeRefusalCount": refusal_count,
        "UsefulQueryTaskCount": useful_query_task_count,
        "MinimumUsefulQueryTaskCount": protocol[
            "MinimumTasksRequiringUsefulAdaptiveQueries"
        ],
        "OracleQueryCount": total_queries,
        "AdaptiveChallengePass": challenge_pass,
        "StructuralSupportTrapCertificatePass": difficulty[
            "AllFiveStructuralTriosIndistinguishableOnAllowedInterventions"
        ],
        "ThreeDistinctTestPredictionsCertificatePass": difficulty[
            "AllFiveTestsHaveThreeDistinctStructuralPredictions"
        ],
        "AdaptiveSafeRefusalCapabilityGatePass": gate,
        "CapabilityGatePass": gate,
        "TaskScores": task_scores,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": (
            "FIVE_WORLD_ADAPTIVE_SAFE_REFUSAL_PASS"
            if gate
            else "FIVE_WORLD_ADAPTIVE_SAFE_REFUSAL_FAILURE"
        ),
    }
    write(ROOT / "results" / "sealed_score.json", score)
    print(json.dumps(score, ensure_ascii=False, separators=(",", ":")))
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
