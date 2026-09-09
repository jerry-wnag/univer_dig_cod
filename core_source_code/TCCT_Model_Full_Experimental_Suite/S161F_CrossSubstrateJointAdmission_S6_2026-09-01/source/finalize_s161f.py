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
    local = {k: file_hash(STAGE / rel) for k, rel in protocol["FrozenSourceFiles"].items()}
    external = {k: file_hash(ROOT / rel) for k, rel in protocol["FrozenExternalFiles"].items()}
    evidence = {k: file_hash(ROOT / rel) for k, rel in protocol["HistoricalEvidenceFiles"].items()}
    checks = {
        "FrozenLocalSourcesIntact": local == protocol["FrozenSourceHashes"],
        "FrozenGenericJointMechanismIntact": external == protocol["FrozenExternalHashes"],
        "HistoricalEvidenceIntact": evidence == protocol["HistoricalEvidenceHashes"],
        "ProtocolFrozenBeforeMaterialization": materialization["ProtocolFrozenBeforeMaterialization"],
        "NoWorldReplacement": not materialization["FailedWorldReplacementAllowed"],
        "FiveDistinctNonAuditOrbits": materialization["SelectedDistinctOrbitCount"] == 5 and materialization["SelectedAuditOverlap"] == 0,
        "PythonReplicationPass": python["PythonReplicationPass"],
        "WolframIndependentPass": wolfram["WolframIndependentPass"],
        "FiveOfFiveCohortsPass": all(c["CohortPass"] for c in python["Cohorts"]),
        "ThirtyFiveCasesExecuted": sum(len(c["Rows"]) for c in python["Cohorts"]) == 35,
        "CoreRewriteFreezeDedupUnchanged": python["Checks"]["CoreRewriteFreezeDedupUnchanged"],
    }
    passed = all(checks.values())
    out = {"Stage": "S161-F", "EvidenceLevel": "CROSS_SUBSTRATE_FROZEN_MULTI_SEED_REPLICATION",
           "CarrierSize": 6, "Checks": checks, "StrictReplicationPass": passed,
           "Conclusion": "S161F_CROSS_SUBSTRATE_REPLICATED_EVIDENCE_GATED_RESIDUAL_CONSTRUCTOR_FORMATION_PASS"
           if passed else "S161F_STRICT_CROSS_SUBSTRATE_REPLICATION_FAIL",
           "S161CDisposition": "PRESERVED_STRICT_S5_MULTI_SEED_REPLICATION_FAIL",
           "ClaimBoundary": "Five frozen fresh S6 permutation cohorts under a fixed bounded constructor grammar. Not unbounded or open-ended primitive invention."}
    path = STAGE / "results/final_gate.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"Conclusion": out["Conclusion"], "Checks": checks}, sort_keys=True))
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
