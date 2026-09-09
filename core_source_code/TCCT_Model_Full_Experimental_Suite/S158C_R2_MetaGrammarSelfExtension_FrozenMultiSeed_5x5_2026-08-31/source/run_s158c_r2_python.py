from __future__ import annotations

import hashlib
import importlib
import json
import sys
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]
R0 = ROOT / "work" / "S158C_MetaGrammarSelfExtension_FrozenMultiSeed_5x5_2026-08-31"
sys.path.insert(0, str(R0 / "source"))
base = importlib.import_module("run_s158c_python")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")


def world_fingerprint(row) -> str:
    semantic_world = {
        "FreshTargetRuleActionSignature": row["FreshTargetRuleActionSignature"],
        "FormationSourceSemantics": row["FormationSourceSemantics"],
        "FormationTargetSemantics": row["FormationTargetSemantics"],
        "NestedReuseTargetSemantics": row["NestedReuseTargetSemantics"],
        "NegativeControlCoefficients": row["NegativeControlCoefficients"],
    }
    payload = json.dumps(semantic_world, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main():
    # Reuse the exact frozen S158-C learner/materializer implementation with only its stage root rebound.
    base.STAGE = STAGE
    base.main()
    result_path = STAGE / "results" / "python_multiseed_result.json"
    result = load(result_path)
    new_holdout = load(STAGE / "oracle" / "sealed_exact_holdout.json")["Cohorts"]
    old_holdout = load(R0 / "oracle" / "sealed_exact_holdout.json")["Cohorts"]
    new_fingerprints = [world_fingerprint(row) for row in new_holdout]
    old_fingerprints = {world_fingerprint(row) for row in old_holdout}
    no_collision = all(value not in old_fingerprints for value in new_fingerprints)
    result["Checks"]["NoFullWorldSemanticCollisionWithS158C_R0"] = no_collision
    result["Checks"]["FiveDistinctFullWorldSemanticFingerprints"] = (
        len(set(new_fingerprints)) == 5)
    result["PythonMultiSeedPass"] = all(result["Checks"].values())
    result["Stage"] = "S158-C-R2"
    result["EvidenceLevel"] = "NEW_SEEDS_FROZEN_MULTI_SEED_5x5"
    result["WorldSemanticFingerprints"] = new_fingerprints
    result["Conclusion"] = ("S158C_R2_NEW_SEEDS_FROZEN_MULTI_SEED_5X5_PYTHON_PASS"
                            if result["PythonMultiSeedPass"] else
                            "S158C_R2_NEW_SEEDS_FROZEN_MULTI_SEED_5X5_PYTHON_FAIL")
    dump(result_path, result)
    audit_path = STAGE / "audit" / "construction_audit.json"
    audit = load(audit_path)
    audit["Stage"] = "S158-C-R2"
    audit["NoFullWorldSemanticCollisionWithS158C_R0"] = no_collision
    audit["WorldSemanticFingerprints"] = new_fingerprints
    dump(audit_path, audit)
    print({"Conclusion": result["Conclusion"], "FreshWorldFingerprintsDistinct":
           len(set(new_fingerprints)) == 5, "NoR0WorldCollision": no_collision})
    if not result["PythonMultiSeedPass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
