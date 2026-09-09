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
        raise RuntimeError("S158-C-R2 frozen hash mismatch")
    python = load(STAGE / "results" / "python_multiseed_result.json")
    wolfram = load(STAGE / "results" / "wolfram_multiseed_audit.json")
    strict = python["PythonMultiSeedPass"] and wolfram["WolframIndependentPass"]
    out = {
        "Stage": "S158-C-R2", "EvidenceLevel": "NEW_SEEDS_FROZEN_MULTI_SEED_5x5",
        "StrictMultiSeedPass": strict,
        "Conclusion": ("S158C_R2_REPLICATED_BOUNDED_META_GRAMMAR_SELF_EXTENSION_PASS"
                       if strict else "S158C_R2_FROZEN_MULTI_SEED_FAIL"),
        "Claim": "Replicated bounded meta-grammar self-extension",
        "ClaimBoundary": ("Five new full-world instances cover the five distinct nonhistorical "
                          "rule semantics satisfying the unchanged depth-3 contract. The finite "
                          "meta-meta-language remains fixed and human supplied."),
        "PreservedHistory": {
            "S158C_R0": "INFRASTRUCTURE_VERIFIER_FAIL",
            "S158C_R1": "RETROSPECTIVE_VERIFIER_REPAIR_ONLY",
            "S158B_R2": "SINGLE_COHORT_FROZEN_FRESH_PASS"
        },
        "NextIfPass": "GRAMMAR_CONSTRUCTOR_BOOTSTRAPPING",
        "ArtifactHashes": {
            "python": file_hash(STAGE / "results" / "python_multiseed_result.json"),
            "wolfram": file_hash(STAGE / "results" / "wolfram_multiseed_audit.json")
        }
    }
    dump(STAGE / "results" / "final_gate.json", out)
    dump(STAGE / "audit" / "provenance.json", {
        "Stage": "S158-C-R2", "ProtocolFrozenBeforeMaterialization": True,
        "NewSeedsAfterRetrospectiveRepair": True,
        "NoCohortReplacementAfterFailure": True,
        "ExactBaseLearnerAndRunnerReused": True,
        "HistoricalFailuresPreserved": True,
        "Result": out["Conclusion"]
    })
    print(out)
    if not strict:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
