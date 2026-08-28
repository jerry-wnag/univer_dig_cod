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


def canonical_conditions(library: dict[str, Any]) -> list[str]:
    return sorted(json.dumps(row["Conditions"], sort_keys=True, separators=(",", ":"))
                  for row in library["Concepts"])


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    result = load(ROOT / "results" / "kernel_native_concept_result.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    certificate = load(ROOT / "diagnostic" / "kernel_concept_certificate.json")
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    target_scores = []
    for row in result["TargetTaskResults"]:
        truth = sealed_by[row["TaskID"]]
        exact = row["TestPredictionCommitted"] is True and row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"]
        depth = row["InitialCertifiedMinimumDepth"]
        baseline_depth = row["InitialBaselineCertifiedMinimumDepth"]
        target_scores.append({
            "TaskID": row["TaskID"], "Role": truth["ExpectedRole"],
            "ExpectedMinimumDepth": truth["ExpectedMinimumGuaranteedDepth"],
            "KernelMinimumDepth": depth, "BaselineMinimumDepth": baseline_depth,
            "ActiveQueryCount": row["ActiveQueryCount"], "CommittedExact": exact,
            "GuidedQueryEvaluationCount": row["GuidedQueryEvaluationCount"],
            "BaselineQueryEvaluationCount": row["BaselineQueryEvaluationCount"],
            "RootFallbackCount": sum(trace["RootConceptFallbackUsed"] is True for trace in row["ActiveQueryTrace"]),
            "InitialConceptPreferredQueryRejectedCount": row["InitialGuidedWorkCounters"]["ConceptPreferredQueryRejectedCount"],
            "RolePass": exact and depth == baseline_depth == truth["ExpectedMinimumGuaranteedDepth"],
        })
    role_by = {row["Role"]: row for row in target_scores}
    transfer_roles = {"SURFACE_PERMUTATION_TRANSFER", "COORDINATE_SCALE_TRANSFER",
                      "SEQUENTIAL_CONCEPT_COMPOSITION"}
    transfer_guided = sum(row["GuidedQueryEvaluationCount"] for row in target_scores if row["Role"] in transfer_roles)
    transfer_baseline = sum(row["BaselineQueryEvaluationCount"] for row in target_scores if row["Role"] in transfer_roles)
    concepts_match = canonical_conditions(result["KernelInducedConceptLibrary"]) == canonical_conditions(
        certificate["IndependentlyInducedConceptLibrary"])
    adversarial_row = role_by["ADVERSARIAL_CONCEPT_REJECTION"]
    adversarial_pass = adversarial_row["InitialConceptPreferredQueryRejectedCount"] > 0
    native_adversarial_row = next(row for row in result["TargetTaskResults"]
                                  if row["TaskID"] == adversarial_row["TaskID"])
    adversarial_safe_nonactivation = native_adversarial_row[
        "InitialGuidedWorkCounters"]["ConceptApplicableStateCount"] == 0
    adversarial_safe = adversarial_pass or adversarial_safe_nonactivation
    fallback_pass = role_by["NO_REUSABLE_CONCEPT_FALLBACK"]["RootFallbackCount"] > 0
    gate = all(row["RolePass"] for row in target_scores) and concepts_match and adversarial_safe and fallback_pass and \
        transfer_guided < transfer_baseline and certificate["DifficultyCertificatePass"] is True and \
        result["NativePreScorePass"] is True and result["CoreRewriteFreezeDedupModified"] is False
    score = {
        "Stage": protocol["Stage"] + " sealed score", "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "SourceTaskCount": 3, "FreshTargetWorldCount": 5,
        "KernelInducedConceptCount": result["KernelInducedConceptLibrary"]["ConceptCount"],
        "KernelAndIndependentConceptBodiesMatch": concepts_match,
        "ExactTargetPassCount": sum(row["RolePass"] for row in target_scores),
        "TransferGuidedQueryEvaluationCount": transfer_guided,
        "TransferBaselineQueryEvaluationCount": transfer_baseline,
        "TransferPlanningWorkReduced": transfer_guided < transfer_baseline,
        "AdversarialConceptRejectedByExactDP": adversarial_pass,
        "AdversarialConceptSafelyNotActivated": adversarial_safe_nonactivation,
        "AdversarialControlSafe": adversarial_safe,
        "NoReusableConceptFallbackExercised": fallback_pass,
        "TargetScores": target_scores, "CapabilityGatePass": gate,
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "VERIFIED_KERNEL_NATIVE_RELATIONAL_PLANNING_CONCEPT_FORMATION" if gate else
                      "KERNEL_NATIVE_CONCEPT_FORMATION_GATE_FAILURE",
    }
    destination = ROOT / "results" / "sealed_score.json"
    destination.write_text(json.dumps(score, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(score, separators=(",", ":")))
    return 0 if gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
