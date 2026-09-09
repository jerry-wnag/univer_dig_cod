from __future__ import annotations

import hashlib
import json
from pathlib import Path

STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def file_hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = load(STAGE / "protocol/frozen_protocol.json")
    python = load(STAGE / "results/python_replication_result.json")
    wolfram = load(STAGE / "results/wolfram_replication_audit.json")
    materialization = load(STAGE / "audit/materialization_audit.json")
    local = {k: file_hash(STAGE / v) for k, v in protocol["FrozenSourceFiles"].items()}
    external = {k: file_hash(ROOT / v) for k, v in protocol["FrozenExternalFiles"].items()}
    historical = {k: file_hash(ROOT / v) for k, v in protocol["HistoricalEvidenceFiles"].items()}
    checks = {
        "FrozenLocalSourcesIntact": local == protocol["FrozenSourceHashes"],
        "FrozenS161MechanismIntact": external == protocol["FrozenExternalHashes"],
        "HistoricalEvidenceIntact": historical == protocol["HistoricalEvidenceHashes"],
        "ProtocolFrozenBeforeMaterialization": materialization["ProtocolFrozenBeforeMaterialization"],
        "NoWorldReplacement": not materialization["FailedWorldReplacementAllowed"],
        "FiveDistinctFreshOrbits": materialization["SelectedDistinctOrbitCount"] == 5 and materialization["AllSelectedOrbitsFresh"],
        "PythonReplicationPass": python["PythonReplicationPass"],
        "WolframIndependentPass": wolfram["WolframIndependentPass"],
        "FiveOfFiveCohortsPass": all(c["CohortPass"] for c in python["Cohorts"]),
        "ThirtyFiveCasesExecuted": sum(len(c["Rows"]) for c in python["Cohorts"]) == 35,
        "CoreRewriteFreezeDedupUnchanged": python["Checks"]["CoreRewriteFreezeDedupUnchanged"],
        "NoHiddenConstructorTargetOracle": python["Checks"]["NoHiddenConstructorTargetOracle"],
    }
    passed = all(checks.values())
    out = {"Stage": "S161-C", "EvidenceLevel": "FROZEN_MULTI_SEED_REPLICATION", "Checks": checks,
           "StrictReplicationPass": passed,
           "Conclusion": "S161C_REPLICATED_BOUNDED_RESIDUAL_DRIVEN_GRAMMAR_CONSTRUCTOR_PROPOSAL_PASS"
           if passed else "S161C_STRICT_MULTI_SEED_REPLICATION_FAIL",
           "ClaimBoundary": "Five frozen fresh unseen S5 permutation cohorts. Bounded fixed substrate; not open-ended primitive or substrate invention.",
           "ArtifactHashes": {name: file_hash(STAGE / rel) for name, rel in {
               "holdout": "oracle/sealed_exact_holdout.json", "python": "results/python_replication_result.json",
               "wolfram": "results/wolfram_replication_audit.json"}.items()}}
    path = STAGE / "results/final_gate.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"Conclusion": out["Conclusion"], "Checks": checks}, sort_keys=True))
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
