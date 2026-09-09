from __future__ import annotations

import hashlib
import json
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = load(STAGE / "protocol" / "frozen_protocol.json")
    local = {name: file_hash(STAGE / path)
             for name, path in protocol["FrozenSourceFiles"].items()}
    external = {name: file_hash(ROOT / path)
                for name, path in protocol["FrozenExternalFiles"].items()}
    if local != protocol["FrozenSourceHashes"] or external != protocol["FrozenExternalHashes"]:
        raise RuntimeError("S158-B-R2 frozen hash mismatch")
    python = load(STAGE / "results" / "python_fresh_result.json")
    wolfram = load(STAGE / "results" / "wolfram_fresh_audit.json")
    strict = python["PythonFreshPass"] and wolfram["WolframIndependentPass"]
    out = {
        "Stage": "S158-B-R2",
        "EvidenceLevel": "NEW_SEED_SINGLE_COHORT_FROZEN_FRESH",
        "StrictFreshPass": strict,
        "Conclusion": ("S158B_R2_SINGLE_COHORT_FROZEN_FRESH_BOUNDED_META_GRAMMAR_SELF_EXTENSION_PASS"
                       if strict else "S158B_R2_FROZEN_FRESH_FAIL"),
        "ClaimBoundary": ("Single-cohort frozen-fresh bounded meta-grammar self-extension; "
                          "not replicated and not open-ended substrate invention."),
        "PreservedHistory": {
            "S158B_R0": "INFRASTRUCTURE_VERIFIER_FAIL",
            "S158B_R1": "RETROSPECTIVE_VERIFIER_REPAIR_PASS_NOT_FRESH"
        },
        "NextIfPass": "S158-C_5x5_FROZEN_MULTI_SEED_REPLICATION",
        "ArtifactHashes": {
            "python": file_hash(STAGE / "results" / "python_fresh_result.json"),
            "wolfram": file_hash(STAGE / "results" / "wolfram_fresh_audit.json")
        }
    }
    dump(STAGE / "results" / "final_gate.json", out)
    dump(STAGE / "audit" / "provenance.json", {
        "Stage": "S158-B-R2", "ProtocolFrozenBeforeMaterialization": True,
        "RepairedVerifierFrozenBeforeMaterialization": True,
        "NewSeedAfterRetrospectiveRepair": True,
        "NoWorldReplacementAfterFailure": True,
        "S158B_R0_RemainsInfrastructureFail": True,
        "S158B_R1_RemainsRetrospectiveOnly": True,
        "LearnerChangedFromS158A": False,
        "CandidateSubstrateChangedFromS158A": False,
        "Result": out["Conclusion"]
    })
    print(out)
    if not strict:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
