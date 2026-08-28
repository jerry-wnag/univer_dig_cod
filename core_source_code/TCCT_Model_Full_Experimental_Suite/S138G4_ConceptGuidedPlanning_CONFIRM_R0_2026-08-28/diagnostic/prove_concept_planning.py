from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from adaptive_geometry import models, query_specs, training_exact  # noqa: E402
from concept_dp import decision_count, find_plan  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    public = load(ROOT / "input" / "public_tasks.json")
    sealed = load(ROOT / "sealed" / "test_outputs.json")
    library = load(ROOT / "library" / "frozen_planning_concepts.json")
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    audits = []
    for task in public["Tasks"]:
        hypotheses, queries = models(task), query_specs(task)
        expected = sealed_by[task["TaskID"]]["ExpectedMinimumGuaranteedDepth"]
        baseline = find_plan(hypotheses, queries, 4, None)
        guided = find_plan(hypotheses, queries, 4, library)
        exact_training = all(training_exact(task, row["Program"]) for row in hypotheses)
        parity = baseline["Solvable"] and guided["Solvable"] and baseline["RequiredDepth"] == expected \
            and guided["RequiredDepth"] == expected
        audits.append({
            "TaskID": task["TaskID"], "ExpectedRole": sealed_by[task["TaskID"]]["ExpectedRole"],
            "ExpectedMinimumGuaranteedDepth": expected,
            "BaselineCertifiedMinimumDepth": baseline["RequiredDepth"],
            "ConceptGuidedCertifiedMinimumDepth": guided["RequiredDepth"],
            "RetainedCandidateProgramCount": len(hypotheses), "SynthesizedQueryCount": len(queries),
            "InitialDecisionClassCount": decision_count(hypotheses),
            "BaselineQueryEvaluationCount": baseline["WorkCounters"]["QueryEvaluationCount"],
            "ConceptGuidedQueryEvaluationCount": guided["WorkCounters"]["QueryEvaluationCount"],
            "ConceptInstantiationMissCount": guided["WorkCounters"]["ConceptInstantiationMissCount"],
            "AllRetainedProgramsTrainingExact": exact_training,
            "ExactDepthParityPass": parity, "AuditPass": parity and exact_training,
        })
    baseline_total = sum(row["BaselineQueryEvaluationCount"] for row in audits)
    guided_total = sum(row["ConceptGuidedQueryEvaluationCount"] for row in audits)
    mismatch = [row for row in audits if row["ExpectedRole"] == "CONCEPT_MISMATCH_FALLBACK_DEPTH2"]
    passed = all(row["AuditPass"] for row in audits) and guided_total < baseline_total \
        and len(mismatch) == 1 and mismatch[0]["ConceptInstantiationMissCount"] > 0
    result = {
        "Stage": protocol["Stage"], "CertificateType": "PAIRED_EXACT_DP_CONCEPT_ORDERING_AUDIT",
        "ExactDepthParityAllFive": all(row["ExactDepthParityPass"] for row in audits),
        "AggregateBaselineQueryEvaluationCount": baseline_total,
        "AggregateConceptGuidedQueryEvaluationCount": guided_total,
        "DeterministicPlanningWorkReduced": guided_total < baseline_total,
        "MismatchFallbackExercised": len(mismatch) == 1 and mismatch[0]["ConceptInstantiationMissCount"] > 0,
        "PostSeedWorldFilteringUsed": False, "DifficultyCertificatePass": passed,
        "TaskAudits": audits,
    }
    destination = ROOT / "diagnostic" / "concept_planning_certificate.json"
    destination.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
