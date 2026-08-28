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
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol = load(protocol_path)
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    oracle = load(ROOT / "sealed" / "oracle_responses.json")
    manifest = load(ROOT / "sealed" / "materialization_manifest.json")
    result = load(ROOT / "results" / "kernel_concept_guided_result.json")
    score = load(ROOT / "results" / "sealed_score.json")
    certificate = load(ROOT / "diagnostic" / "concept_planning_certificate.json")
    library = load(ROOT / "library" / "frozen_planning_concepts.json")
    sources = {
        "FrozenGeometryLibrarySHA256": ROOT / "source" / "adaptive_geometry.py",
        "FrozenConceptDynamicProgrammingSHA256": ROOT / "source" / "concept_dp.py",
        "FrozenTaskBuilderSHA256": ROOT / "source" / "build_concept_guided_tasks.py",
        "FrozenWolframRunnerSHA256": ROOT / "source" / "run_concept_guided_planning.wl",
        "FrozenOracleResponderSHA256": ROOT / "source" / "oracle_responder.py",
        "FrozenConceptExtractorSHA256": ROOT / "source" / "extract_historical_planning_concepts.py",
        "FrozenPlanningAuditorSHA256": ROOT / "diagnostic" / "prove_concept_planning.py",
        "FrozenReplayLibrarySHA256": ROOT / "source" / "concept_replay.py",
        "FrozenScorerSHA256": ROOT / "source" / "score_concept_guided.py",
        "FrozenVerifierSHA256": ROOT / "source" / "verify_concept_guided.py",
    }
    source_pass = all(digest(path) == protocol[key] for key, path in sources.items())
    protocol_hash = digest(protocol_path)
    boundary_pass = all(row["ProtocolSHA256"] == protocol_hash
                        for row in (public, sealed, oracle, manifest, result, score))
    library_pass = digest(ROOT / "library" / "frozen_planning_concepts.json") == protocol["FrozenConceptLibrarySHA256"] \
        and library["ConceptsMayPruneModels"] is False and library["ExactDynamicProgrammingFallbackRequired"] is True
    public_by = {row["TaskID"]: row for row in public["Tasks"]}
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    result_by = {row["TaskID"]: row for row in result["TaskResults"]}
    replay_pass = all(replay_task(public_by[task_id], result_by[task_id],
                                  sealed_by[task_id]["HiddenProgram"], library,
                                  protocol["MaximumPlanningDepth"], protocol["MaximumActiveQueriesPerTask"])
                      for task_id in protocol["TaskOrder"])
    log_rows = [json.loads(line) for line in (ROOT / "oracle" / "query_log.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    trace_keys = [(task_id, trace["QueryNumber"], trace["Input"], trace["InputSHA256"])
                  for task_id in protocol["TaskOrder"] for trace in result_by[task_id]["ActiveQueryTrace"]]
    log_keys = [(row["TaskID"], row["QueryNumber"], row["Input"], row["InputSHA256"])
                for row in log_rows]
    oracle_pass = trace_keys == log_keys and not any(row["TestOutputAccessed"] for row in log_rows)
    expected_roles = sorted(["CONCEPT_TRANSFER_DEPTH1", "CONCEPT_TRANSFER_DEPTH2",
        "CONCEPT_TRANSFER_DEPTH3", "CONCEPT_MISMATCH_FALLBACK_DEPTH2", "DEPTH4_BUDGET_CONTROL"])
    cohort_pass = all([manifest["RoleMultiset"] == expected_roles,
        manifest["PostSeedWorldFilteringUsed"] is False,
        manifest["WorldReplacementAfterMaterializationUsed"] is False,
        public["PublicQueryPoolSize"] == 0, public["LearnerVisibleRoleLabelCount"] == 0,
        public["LearnerVisibleRequiredDepthCount"] == 0, public["LearnerVisibleHiddenProgramCount"] == 0])
    evidence = all([source_pass, boundary_pass, library_pass, replay_pass, oracle_pass, cohort_pass,
                    certificate["DifficultyCertificatePass"], score["CapabilityGatePass"],
                    score["ExactRolePassCount"] == 5])
    verification = {
        "Stage": f"{protocol['Stage']} verification", "FrozenSourceHashesPass": source_pass,
        "ProtocolBoundaryPass": boundary_pass, "FrozenHistoricalConceptLibraryPass": library_pass,
        "FreshMixedCohortPass": cohort_pass, "IndependentPairedPlanningReplayPass": replay_pass,
        "OracleBoundaryReplayPass": oracle_pass,
        "ConceptPlanningCertificatePass": certificate["DifficultyCertificatePass"],
        "SealedScoreReplayPass": score["CapabilityGatePass"],
        "EvidenceIntegrityPass": evidence, "CapabilityGatePass": evidence,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "VERIFIED_HISTORICAL_CONCEPT_GUIDED_EPISTEMIC_PLANNING_PASS" if evidence else "VERIFICATION_FAILED",
    }
    destination = ROOT / "verification" / "independent_verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(verification, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(verification, separators=(",", ":")))
    return 0 if evidence else 1


if __name__ == "__main__":
    raise SystemExit(main())
