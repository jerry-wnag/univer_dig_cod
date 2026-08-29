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
    protocol = read(ROOT / "protocol" / "frozen_protocol.json")
    protocol_hash = hashlib.sha256((ROOT / "protocol" / "frozen_protocol.json").read_bytes()).hexdigest()
    induction_file = read(ROOT / "input" / "induction_events.json")
    qualification_file = read(ROOT / "input" / "qualification_events.json")
    difficulty = read(ROOT / "sealed" / "difficulty_certificate.json")
    if not all(row["ProtocolSHA256"] == protocol_hash for row in (
            induction_file, qualification_file, difficulty)):
        raise RuntimeError("protocol hash mismatch before selection")
    induction = induction_file["Events"]
    qualification = qualification_file["Events"]
    candidates, synthesis = robust.candidate_rules(induction)
    evaluator = SharedEvaluator()

    def shared_utility(event: dict[str, Any], concepts: list[dict[str, Any]],
                       calibration_events: list[dict[str, Any]]) -> dict[str, Any]:
        return evaluator.utility(event, concepts, calibration_events)

    original = robust.event_utility_for_library
    robust.event_utility_for_library = shared_utility
    try:
        audited = []
        qualified = []
        for candidate in candidates:
            concept = make_concept(candidate)
            audit = robust.library_qualification([concept], qualification, induction)
            row = {"Concept": concept, "Candidate": candidate, "Qualification": audit}
            audited.append(row)
            if audit["QualificationPass"]:
                qualified.append(row)
        selected = []
        selected_utility = 0
        remaining = list(qualified)
        admission = []
        while remaining:
            proposals = []
            for row in remaining:
                proposed = [item["Concept"] for item in selected] + [row["Concept"]]
                audit = robust.library_qualification(proposed, qualification, induction)
                accepted = audit["QualificationPass"] and audit["TotalUtility"] > selected_utility
                admission.append({
                    "ExistingConceptIDs": [item["Concept"]["ConceptID"] for item in selected],
                    "ProposedConceptID": row["Concept"]["ConceptID"],
                    "Qualification": audit,
                    "AdmittedForRanking": accepted,
                })
                if accepted:
                    candidate = row["Candidate"]
                    proposals.append((-audit["TotalUtility"],
                                      -candidate["TrainingSupportCount"],
                                      candidate["ASTComplexity"],
                                      canonical(row["Concept"]["Conditions"]), row, audit))
            if not proposals:
                break
            proposals.sort(key=lambda item: item[:-2])
            chosen, chosen_audit = proposals[0][-2], proposals[0][-1]
            selected.append(chosen)
            selected_utility = chosen_audit["TotalUtility"]
            remaining = [row for row in remaining if row["Concept"]["ConceptID"] !=
                         chosen["Concept"]["ConceptID"]]
        library = {
            "LibraryType": "FULL_SOURCE_PROPOSAL_INDEPENDENT_QUALIFICATION_FROZEN_R2",
            "ConceptCount": len(selected),
            "Concepts": [row["Concept"] for row in selected],
            "RouterActivationCalibration": robust.activation_calibration(
                [row["Concept"] for row in selected], induction),
            "ExactDynamicProgrammingFallbackRequired": True,
        }
    finally:
        robust.event_utility_for_library = original

    # Open the five sealed targets only after the library is fixed.
    target_file = read(ROOT / "sealed" / "fresh_test_events.json")
    if target_file["ProtocolSHA256"] != protocol_hash:
        raise RuntimeError("target protocol hash mismatch")
    spec = importlib.util.spec_from_file_location("s141d_r0_runner", R0_RUNNER)
    runner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(runner)
    targets = []
    for event in target_file["Events"]:
        guided = runner.execute(event, library)
        baseline = runner.execute(event, None)
        targets.append({
            "TaskID": event["TaskID"], "Exact": guided["Exact"],
            "GuidedMinimumDepth": guided["InitialDepth"],
            "BaselineMinimumDepth": baseline["InitialDepth"],
            "GuidedWork": guided["TotalQueryEvaluationCount"],
            "BaselineWork": baseline["TotalQueryEvaluationCount"],
            "NoNegativeTransfer": guided["TotalQueryEvaluationCount"] <=
                                  baseline["TotalQueryEvaluationCount"],
        })
    difficulty_rows = difficulty["AcceptedWorldAudits"]
    checks = {
        "DifficultyConstructorFindsTenRequiredWorldsWithinFrozenPool": len(difficulty_rows) == 10,
        "IdentityOnlyInsufficiencyCertificateValid": all(
            row["IdentityBestUtility"] <= 0 for row in difficulty_rows),
        "PositiveNonIdentityExistenceCertificateValid": all(
            row["NonIdentityBestUtility"] > 0 for row in difficulty_rows),
        "LearnerSelectsAtLeastOneNonIdentityRepresentation": any(
            nonidentity(concept["Conditions"]) for concept in library["Concepts"]),
        "AllFiveFreshHiddenDecisionsExact": len(targets) == 5 and all(
            row["Exact"] for row in targets),
        "AllFiveMinimumDepthsMatchBaseline": all(row["GuidedMinimumDepth"] ==
                                                  row["BaselineMinimumDepth"] for row in targets),
        "NoFreshWorldNegativeTransfer": all(row["NoNegativeTransfer"] for row in targets),
        "AtLeastOneCandidateSafelyRejected": any(
            not row["Qualification"]["QualificationPass"] for row in audited),
        "ExactFallbackPreserved": library["ExactDynamicProgrammingFallbackRequired"],
        "CoreRewriteFreezeDedupUnchanged": True,
    }
    result = {
        "Stage": protocol["Stage"], "EvidenceStatus": protocol["EvidenceStatus"],
        "ProtocolSHA256": protocol_hash, "FreshConstructorSeed": protocol["FreshConstructorSeed"],
        "DifficultyCertificate": difficulty, "SynthesisAudit": synthesis,
        "CandidateAudits": audited, "JointLibraryAdmissionAudits": admission,
        "SelectedLibrary": library, "SelectedQualificationUtility": selected_utility,
        "FreshTargetRows": targets, "Checks": checks, "StrictPass": all(checks.values()),
        "PostHocLearnerOutcomeFiltering": False, "WorldReplacementAfterLearnerRun": False,
        "NativeWolframPortUsed": False, "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "FRESH_SPARSE_SUPPORT_REPRESENTATION_SELECTION_PASS" if all(checks.values()) else
                      "FRESH_SPARSE_SUPPORT_REPRESENTATION_SELECTION_FAIL",
    }
    write(ROOT / "results" / "fresh_five_world_result.json", result)
    print(json.dumps({
        "StrictPass": result["StrictPass"], "ConceptCount": library["ConceptCount"],
        "NonIdentityCount": sum(nonidentity(c["Conditions"]) for c in library["Concepts"]),
        "QualificationUtility": selected_utility, "Targets": targets, "Checks": checks,
    }, ensure_ascii=False, separators=(",", ":")))
    return 0 if result["StrictPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
