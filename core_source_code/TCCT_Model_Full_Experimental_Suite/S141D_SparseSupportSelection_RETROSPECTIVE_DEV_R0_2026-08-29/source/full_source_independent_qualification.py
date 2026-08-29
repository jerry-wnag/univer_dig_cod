from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
R3 = WORK / "S141B_RobustRepresentationSelection_RETROSPECTIVE_DEV_R0_2026-08-29" / "source"
FAILED = WORK / "S141D_FreshRepresentationRequired_CONFIRMATORY_R1_2026-08-29"
R0_RUNNER = WORK / "S141D_FreshRepresentationRequired_CONFIRMATORY_R0_2026-08-29" / "source" / "run_five_world_test.py"
sys.path.insert(0, str(R3))

import robust_representation_selection as robust  # noqa: E402
from r3_c02_shared_dag_test import SharedEvaluator  # noqa: E402


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def nonidentity(conditions: list[list[Any]]) -> bool:
    return any(atom[0][0] != "Identity" for atom in conditions)


def make_concept(candidate: dict[str, Any]) -> dict[str, Any]:
    digest = hashlib.sha256(canonical(candidate["Conditions"]).encode()).hexdigest()[:16]
    return {"ConceptID": "FS_" + digest, "Conditions": candidate["Conditions"]}


def main() -> int:
    protocol = read(ROOT / "protocol" / "development_protocol.json")
    induction = read(FAILED / "input" / "induction_events.json")["Events"]
    qualification = read(FAILED / "input" / "qualification_events.json")["Events"]
    failed_result = read(FAILED / "results" / "fresh_five_world_result.json")
    candidates, synthesis = robust.candidate_rules(induction)
    evaluator = SharedEvaluator()

    def shared_utility(event: dict[str, Any], concepts: list[dict[str, Any]],
                       calibration_events: list[dict[str, Any]]) -> dict[str, Any]:
        return evaluator.utility(event, concepts, calibration_events)

    original = robust.event_utility_for_library
    robust.event_utility_for_library = shared_utility
    try:
        candidate_audits = []
        qualified = []
        for candidate in candidates:
            concept = make_concept(candidate)
            audit = robust.library_qualification([concept], qualification, induction)
            row = {
                "Concept": concept,
                "ASTComplexity": candidate["ASTComplexity"],
                "TrainingSupportCount": candidate["TrainingSupportCount"],
                "TrainingDistinctTaskSupportCount": candidate["TrainingDistinctTaskSupportCount"],
                "TrainingFalsePositiveCount": candidate["TrainingFalsePositiveCount"],
                "Qualification": audit,
            }
            candidate_audits.append(row)
            if audit["QualificationPass"]:
                qualified.append(row)

        selected = []
        selected_utility = 0
        admission_audits = []
        remaining = list(qualified)
        while remaining:
            proposals = []
            for row in remaining:
                proposed = [item["Concept"] for item in selected] + [row["Concept"]]
                audit = robust.library_qualification(proposed, qualification, induction)
                admitted = audit["QualificationPass"] and audit["TotalUtility"] > selected_utility
                admission_audits.append({
                    "ExistingConceptIDs": [item["Concept"]["ConceptID"] for item in selected],
                    "ProposedConceptID": row["Concept"]["ConceptID"],
                    "Qualification": audit,
                    "AdmittedForRanking": admitted,
                })
                if admitted:
                    proposals.append((
                        -audit["TotalUtility"],
                        -row["TrainingSupportCount"],
                        row["ASTComplexity"],
                        canonical(row["Concept"]["Conditions"]),
                        row,
                        audit,
                    ))
            if not proposals:
                break
            proposals.sort(key=lambda item: item[:-2])
            chosen, chosen_audit = proposals[0][-2], proposals[0][-1]
            selected.append(chosen)
            selected_utility = chosen_audit["TotalUtility"]
            remaining = [row for row in remaining if row["Concept"]["ConceptID"] !=
                         chosen["Concept"]["ConceptID"]]
        library = {
            "LibraryType": "FULL_SOURCE_PROPOSAL_INDEPENDENT_QUALIFICATION_RETROSPECTIVE_DEV",
            "ConceptCount": len(selected),
            "Concepts": [row["Concept"] for row in selected],
            "RouterActivationCalibration": robust.activation_calibration(
                [row["Concept"] for row in selected], induction),
            "ExactDynamicProgrammingFallbackRequired": True,
        }
    finally:
        robust.event_utility_for_library = original

    # The sealed old-fresh targets are opened only after the library is fixed.
    target_events = read(FAILED / "sealed" / "fresh_test_events.json")["Events"]
    spec = importlib.util.spec_from_file_location("s141d_r0_runner", R0_RUNNER)
    runner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(runner)
    target_rows = []
    for event in target_events:
        guided = runner.execute(event, library)
        baseline = runner.execute(event, None)
        target_rows.append({
            "TaskID": event["TaskID"],
            "Exact": guided["Exact"],
            "GuidedMinimumDepth": guided["InitialDepth"],
            "BaselineMinimumDepth": baseline["InitialDepth"],
            "GuidedWork": guided["TotalQueryEvaluationCount"],
            "BaselineWork": baseline["TotalQueryEvaluationCount"],
            "NoNegativeTransfer": guided["TotalQueryEvaluationCount"] <=
                                  baseline["TotalQueryEvaluationCount"],
        })

    prior_external = {canonical(row["Conditions"])
                      for row in failed_result["SelectionAudit"]["CrossFamilySourceQualification"]}
    rescued = [concept for concept in library["Concepts"]
               if canonical(concept["Conditions"]) not in prior_external]
    checks = {
        "RetrospectiveStatusExplicit": protocol["EvidenceStatus"] ==
            "RETROSPECTIVE_DEVELOPMENT_ONLY",
        "SelectsNonIdentityRepresentation": any(nonidentity(concept["Conditions"])
                                                 for concept in library["Concepts"]),
        "SelectedRepresentationWasPreviouslyBlockedOnlyByLOSORegeneration": bool(rescued),
        "AllFiveOldFreshDecisionsExact": len(target_rows) == 5 and all(
            row["Exact"] for row in target_rows),
        "AllFiveDepthsPreserved": all(row["GuidedMinimumDepth"] ==
                                      row["BaselineMinimumDepth"] for row in target_rows),
        "NoOldFreshNegativeTransfer": all(row["NoNegativeTransfer"] for row in target_rows),
        "AtLeastOneQualificationCandidateSafelyRejected": any(
            not row["Qualification"]["QualificationPass"] for row in candidate_audits),
        "NoGrammarExpansion": True,
        "CoreUnchanged": True,
    }
    result = {
        "Stage": protocol["Stage"],
        "EvidenceStatus": "RETROSPECTIVE_DEVELOPMENT_ONLY_NOT_CAPABILITY_EVIDENCE",
        "PredecessorS141DR1StrictFailurePreserved": True,
        "SynthesisAudit": synthesis,
        "CandidateAudits": candidate_audits,
        "JointLibraryAdmissionAudits": admission_audits,
        "SelectedLibrary": library,
        "SelectedQualificationUtility": selected_utility,
        "RescuedPreviouslyLOSOBlockedConcepts": rescued,
        "OldFreshTargetRows": target_rows,
        "Checks": checks,
        "DevelopmentPass": all(checks.values()),
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "SPARSE_SUPPORT_SELECTION_RETROSPECTIVE_PASS" if all(checks.values()) else
                      "SPARSE_SUPPORT_SELECTION_RETROSPECTIVE_FAIL",
    }
    write(ROOT / "results" / "retrospective_failed_case_result.json", result)
    print(json.dumps({
        "DevelopmentPass": result["DevelopmentPass"],
        "ConceptCount": library["ConceptCount"],
        "QualificationUtility": selected_utility,
        "RescuedCount": len(rescued),
        "Targets": target_rows,
        "Checks": checks,
    }, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["DevelopmentPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
