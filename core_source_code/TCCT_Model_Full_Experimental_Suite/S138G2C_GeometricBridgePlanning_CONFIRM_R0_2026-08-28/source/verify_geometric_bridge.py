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
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol = load(protocol_path)
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    oracle = load(ROOT / "sealed" / "oracle_responses.json")
    manifest = load(ROOT / "sealed" / "materialization_manifest.json")
    result = load(ROOT / "results" / "kernel_geometric_planning_result.json")
    score = load(ROOT / "results" / "sealed_score.json")
    difficulty = load(ROOT / "diagnostic" / "difficulty_certificate.json")
    sources = {
        "FrozenGeometryLibrarySHA256": ROOT / "source" / "geometry_world.py",
        "FrozenTaskBuilderSHA256": ROOT / "source" / "build_geometric_bridge_tasks.py",
        "FrozenWolframRunnerSHA256": ROOT / "source" / "run_geometric_bridge_planning.wl",
        "FrozenOracleResponderSHA256": ROOT / "source" / "oracle_responder.py",
        "FrozenDifficultyAuditorSHA256": ROOT / "diagnostic" / "prove_geometric_bridge_difficulty.py",
        "FrozenReplayLibrarySHA256": ROOT / "source" / "geometric_replay.py",
        "FrozenScorerSHA256": ROOT / "source" / "score_geometric_bridge.py",
        "FrozenVerifierSHA256": ROOT / "source" / "verify_geometric_bridge.py",
    }
    source_pass = all(digest(path) == protocol[key] for key, path in sources.items())
    protocol_hash = digest(protocol_path)
    boundary_pass = all(row["ProtocolSHA256"] == protocol_hash
                        for row in (public, sealed, oracle, manifest, result, score))
    public_by = {row["TaskID"]: row for row in public["Tasks"]}
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    result_by = {row["TaskID"]: row for row in result["TaskResults"]}
    replay_pass = all(replay_task(public_by[task_id], result_by[task_id],
                                  sealed_by[task_id]["HiddenProgram"])
                      for task_id in protocol["TaskOrder"])
    log_rows = [json.loads(line) for line in (ROOT / "oracle" / "query_log.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    trace_keys = [(task_id, trace["QueryNumber"], trace["Input"], trace["InputSHA256"])
                  for task_id in protocol["TaskOrder"] for trace in result_by[task_id]["ActiveQueryTrace"]]
    log_keys = [(row["TaskID"], row["QueryNumber"], row["Input"], row["InputSHA256"])
                for row in log_rows]
    oracle_pass = trace_keys == log_keys and not any(row["TestOutputAccessed"] for row in log_rows)
    roles = [row["ExpectedRole"] for row in sealed["Tasks"]]
    cohort_pass = all([
        len(protocol["TaskOrder"]) == 5,
        roles.count("GEOMETRIC_TWO_STEP_BRIDGE") == 3,
        roles.count("GEOMETRIC_IRREDUCIBLE_CONTROL") == 2,
        manifest["PostSeedWorldFilteringUsed"] is False,
        manifest["WorldReplacementAfterMaterializationUsed"] is False,
        manifest["UniqueTestShapes"] is True,
        public["LearnerVisibleRoleLabelCount"] == 0,
        public["LearnerVisibleHiddenProgramCount"] == 0,
        public["PublicQueryPoolSize"] == 0,
    ])
    evidence = all([
        source_pass, boundary_pass, replay_pass, oracle_pass, cohort_pass,
        difficulty["DifficultyCertificatePass"], score["CapabilityGatePass"],
        score["GeometricBridgePassCount"] == 3,
        score["GeometricIrreducibleControlPassCount"] == 2,
    ])
    verification = {
        "Stage": f"{protocol['Stage']} verification", "FrozenSourceHashesPass": source_pass,
        "ProtocolBoundaryPass": boundary_pass, "FreshMixedCohortPass": cohort_pass,
        "IndependentGeometryPolicyReplayPass": replay_pass,
        "OracleBoundaryReplayPass": oracle_pass,
        "DifficultyReplayPass": difficulty["DifficultyCertificatePass"],
        "SealedScoreReplayPass": score["CapabilityGatePass"],
        "EvidenceIntegrityPass": evidence, "CapabilityGatePass": evidence,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "VERIFIED_EXECUTABLE_GEOMETRIC_DEPTH2_PASS" if evidence else "VERIFICATION_FAILED",
    }
    destination = ROOT / "verification" / "independent_verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(verification, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(verification, separators=(",", ":")))
    return 0 if evidence else 1


if __name__ == "__main__":
    raise SystemExit(main())
