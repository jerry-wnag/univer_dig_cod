from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_is_strict(row: dict[str, Any]) -> bool:
    expected_before = row["InitialDecisionClassCount"]
    hashes: list[str] = []
    for query in row["ActiveQueryTrace"]:
        before = query["DecisionClassCountBefore"]
        after = query["DecisionClassCountAfter"]
        worst_case = query["SelectedScore"][
            "WorstCaseRemainingDecisionClassCount"
        ]
        if not all(
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
        ):
            return False
        hashes.append(query["InputSHA256"])
        expected_before = after
    return all(
        [
            expected_before == row["FinalDecisionClassCount"],
            len(row["ActiveQueryTrace"]) == row["ActiveQueryCount"],
            len(hashes) == len(set(hashes)),
        ]
    )


def main() -> int:
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol = load(protocol_path)
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    manifest = load(ROOT / "sealed" / "materialization_manifest.json")
    result = load(ROOT / "results" / "kernel_intervention_result.json")
    score = load(ROOT / "results" / "sealed_score.json")
    difficulty = load(ROOT / "diagnostic" / "difficulty_certificate.json")
    log_path = ROOT / "oracle" / "query_log.jsonl"
    log_rows = [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    frozen_sources = {
        "FrozenTaskBuilderSHA256": ROOT
        / "source"
        / "build_adaptive_safe_refusal_tasks.py",
        "FrozenWolframRunnerSHA256": ROOT
        / "source"
        / "run_adaptive_safe_refusal.wl",
        "FrozenOracleResponderSHA256": ROOT / "source" / "oracle_responder.py",
        "FrozenDifficultyAuditorSHA256": ROOT
        / "diagnostic"
        / "prove_adaptive_support_trap.py",
        "FrozenScorerSHA256": ROOT
        / "source"
        / "score_adaptive_safe_refusal.py",
        "FrozenVerifierSHA256": ROOT
        / "source"
        / "verify_adaptive_safe_refusal.py",
    }
    source_hash_pass = all(
        digest(path) == protocol[key] for key, path in frozen_sources.items()
    )
    protocol_hash = digest(protocol_path)
    protocol_boundary_pass = all(
        artifact["ProtocolSHA256"] == protocol_hash
        for artifact in (public, sealed, manifest, result)
    )
    task_ids = protocol["ControlTaskIDs"]
    result_by_id = {row["TaskID"]: row for row in result["TaskResults"]}
    score_by_id = {row["TaskID"]: row for row in score["TaskScores"]}
    cohort_pass = all(
        [
            len(task_ids) == 5,
            protocol["DiscoveryTaskIDs"] == [],
            [row["TaskID"] for row in public["Tasks"]] == task_ids,
            [row["TaskID"] for row in result["TaskResults"]] == task_ids,
            all("DifficultyConstructionAxis" not in task for task in public["Tasks"]),
            manifest["PostSeedWorldFilteringUsed"] is False,
            manifest["S138GTestShapesExcluded"],
        ]
    )
    trace_pass = all(trace_is_strict(result_by_id[task_id]) for task_id in task_ids)
    flattened_trace = [
        query
        for task_id in task_ids
        for query in result_by_id[task_id]["ActiveQueryTrace"]
    ]
    trace_keys = [
        (result_by_id[task_id]["TaskID"], query["QueryID"], query["InputSHA256"])
        for task_id in task_ids
        for query in result_by_id[task_id]["ActiveQueryTrace"]
    ]
    log_keys = [
        (row["TaskID"], row["QueryID"], row["InputSHA256"]) for row in log_rows
    ]
    oracle_replay_pass = all(
        [
            trace_keys == log_keys,
            len(log_rows) == len(flattened_trace),
            len(log_rows) == result["OracleQueryLogLineCount"],
            all(row["GeneratedByTCCTKernel"] for row in log_rows),
            not any(row["TestOutputAccessed"] for row in log_rows),
            not any(row["GeneratorFamilyAccessed"] for row in log_rows),
        ]
    )
    refusal_replay_pass = all(
        all(
            [
                score_by_id[task_id]["AdaptiveSafeRefusal"],
                result_by_id[task_id]["InitialDecisionClassCount"] > 1,
                result_by_id[task_id]["FinalDecisionClassCount"] > 1,
                result_by_id[task_id]["RemainingInformativeInterventionCount"]
                == 0,
                result_by_id[task_id]["RemainingUnusedInterventionCount"] > 0,
                not result_by_id[task_id]["TestPredictionCommitted"],
                result_by_id[task_id]["AdaptiveStopReason"]
                == "NO_INFORMATIVE_QUERY",
                result_by_id[task_id]["Status"]
                == "DECISION_AMBIGUOUS_NO_INFORMATIVE_QUERY",
            ]
        )
        for task_id in task_ids
    )
    challenge_pass = all(
        [
            difficulty["DifficultyCertificatePass"],
            difficulty[
                "AllFiveStructuralTriosIndistinguishableOnAllowedInterventions"
            ],
            difficulty["AllFiveTestsHaveThreeDistinctStructuralPredictions"],
            difficulty["AllPublicDifficultyAxesAbsent"],
            score["UsefulQueryTaskCount"]
            >= protocol["MinimumTasksRequiringUsefulAdaptiveQueries"],
            score["AdaptiveChallengePass"],
        ]
    )
    score_replay_pass = all(
        [
            score["AdaptiveSafeRefusalCount"] == 5,
            score["OracleQueryCount"] == len(log_rows),
            score["AdaptiveSafeRefusalCapabilityGatePass"],
            score["CapabilityGatePass"],
        ]
    )
    evidence_integrity = all(
        [
            source_hash_pass,
            protocol_boundary_pass,
            cohort_pass,
            challenge_pass,
            trace_pass,
            oracle_replay_pass,
            refusal_replay_pass,
            score_replay_pass,
        ]
    )
    verification = {
        "Stage": f"{protocol['Stage']} independent verification",
        "FrozenSourceHashesPass": source_hash_pass,
        "ProtocolBoundaryPass": protocol_boundary_pass,
        "FiveFreshControlWorldCohortPass": cohort_pass,
        "StructuralSupportTrapChallengePass": challenge_pass,
        "StrictDecisionReductionTraceReplayPass": trace_pass,
        "OracleBoundaryReplayPass": oracle_replay_pass,
        "AdaptiveSafeRefusalReplayPass": refusal_replay_pass,
        "SealedScoreReplayPass": score_replay_pass,
        "EvidenceIntegrityPass": evidence_integrity,
        "CapabilityGatePass": score["CapabilityGatePass"],
        "Conclusion": (
            "VERIFIED_ADAPTIVE_SAFE_REFUSAL_PASS"
            if evidence_integrity and score["CapabilityGatePass"]
            else "VERIFICATION_FAILED"
        ),
    }
    destination = ROOT / "verification" / "independent_verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(verification, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(verification, ensure_ascii=False, separators=(",", ":")))
    return 0 if evidence_integrity else 1


if __name__ == "__main__":
    raise SystemExit(main())
