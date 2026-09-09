from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def digest(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


protocol = load("protocol/development_protocol.json")
constructor = load("audit/constructor_audit.json")
py = load("results/python_grammar_diagnostics_result.json")
wl = load("results/wolfram_grammar_diagnostics_audit.json")
certificate_path = ROOT / "results" / "candidate_elimination_certificates.json"
certificates = json.loads(certificate_path.read_text(encoding="utf-8"))
checks = {
    "ConstructorPass": constructor["ConstructorPass"] is True,
    "PythonDevelopmentPass": py["PythonDevelopmentPass"] is True,
    "WolframDevelopmentAuditPass": wl["WolframDevelopmentAuditPass"] is True,
    "PythonWolframStatusParity": wl["Checks"]["FiveStatusParity"] is True,
    "PythonWolframCandidateAndSemanticCountParity": wl["Checks"]["ExactCandidateCountParity"] is True
        and wl["Checks"]["SemanticClassCountParity"] is True,
    "FiveOfFiveDiagnosticStatusesCorrect": [row["Status"] for row in py["CaseRows"]]
        == protocol["ExpectedStatuses"],
    "ExactCaseFreezesOnlyAfterOneSemanticClass": py["CaseRows"][0]["Frozen"] is True
        and py["CaseRows"][0]["SemanticClassCount"] == 1,
    "AmbiguousCaseRetainsFourClassesAndDoesNotFreeze": py["CaseRows"][1]["Frozen"] is False
        and py["CaseRows"][1]["SemanticClassCount"] == 4,
    "BothLanguageInsufficiencyCasesEliminateAll11250Candidates": all(
        py["CaseRows"][index]["EliminatedCandidateCount"] == protocol["FrozenGrammarCandidateCount"]
        and len(certificates[f"S144A_CASE_0{index}"]) == protocol["FrozenGrammarCandidateCount"]
        for index in (2, 3)),
    "InconsistentCaseStopsBeforeGrammarSearch": py["CaseRows"][4]["GrammarSearchExecuted"] is False,
    "DeterministicRandomBehaviorDoesNotFreeze": py["RandomBehaviorControl"]["Status"]
        == "LANGUAGE_INSUFFICIENT" and py["RandomBehaviorControl"]["Frozen"] is False,
    "NearLawDoesNotFreeze": py["CaseRows"][2]["Status"] == "LANGUAGE_INSUFFICIENT",
    "NoLanguageExtensionClaim": protocol["LanguageExtensionClaimAllowed"] is False,
    "CoreMechanismUnchanged": py["Checks"]["CoreRewriteFreezeDedupUnchanged"] is True,
}
passed = all(checks.values())
artifacts = (
    "protocol/development_protocol.json",
    "source/construct_five_diagnostic_cases.py",
    "source/run_python_grammar_diagnostics.py",
    "source/run_wolfram_grammar_diagnostics_audit.wl",
    "input/five_diagnostic_cases.json",
    "input/random_behavior_control.json",
    "results/candidate_elimination_certificates.json",
    "results/python_grammar_diagnostics_result.json",
    "results/wolfram_grammar_diagnostics_audit.json",
)
result = {
    "Stage": protocol["Stage"], "StrictFiveCaseDevelopmentPass": passed,
    "Statuses": [row["Status"] for row in py["CaseRows"]],
    "ExactCandidateCounts": [row["ExactCandidateCount"] for row in py["CaseRows"]],
    "SemanticClassCounts": [row["SemanticClassCount"] for row in py["CaseRows"]],
    "ObservationCounts": constructor["CaseObservationCounts"],
    "GrammarCandidateCount": protocol["FrozenGrammarCandidateCount"],
    "RandomBehaviorStatus": py["RandomBehaviorControl"]["Status"],
    "Checks": checks,
    "Conclusion": "S144A_BOUNDED_GRAMMAR_INSUFFICIENCY_DETECTION_DEV_PASS" if passed
        else "S144A_BOUNDED_GRAMMAR_INSUFFICIENCY_DETECTION_DEV_FAIL",
    "PermittedClaim": "bounded development evidence that TCCT distinguishes exact, ambiguous, out-of-language, and inconsistent behavior under a frozen complete finite grammar",
    "ScopeBoundary": [
        "language insufficiency is relative to the frozen 11250-candidate grammar",
        "deterministic consistent out-of-grammar behavior is classified as language insufficient",
        "contradictory repeated observations are classified separately as inconsistent or noisy",
        "no new primitive or grammar extension is attempted in S144-A",
        "fresh and multi-seed confirmation remain untested"
    ],
    "ArtifactSHA256": {relative: digest(relative) for relative in artifacts},
}
(ROOT / "results" / "final_development_gate.json").write_text(
    json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"Pass": passed, "Statuses": result["Statuses"],
                  "ExactCandidates": result["ExactCandidateCounts"],
                  "SemanticClasses": result["SemanticClassCounts"],
                  "RandomStatus": result["RandomBehaviorStatus"]}, separators=(",", ":")))
raise SystemExit(0 if passed else 1)
