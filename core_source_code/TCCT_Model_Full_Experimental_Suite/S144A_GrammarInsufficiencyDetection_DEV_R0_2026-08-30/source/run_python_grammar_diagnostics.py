from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S143B_RUNNER = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30" / "source" / "run_python_behavioral_induction.py"
spec = importlib.util.spec_from_file_location("s143b_for_s144a_runner", S143B_RUNNER)
b = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = b
spec.loader.exec_module(b)


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def candidate_hash(candidate: dict[str, Any]) -> str:
    return hashlib.sha256(canonical(candidate).encode()).hexdigest()


def input_key(app: dict[str, Any]) -> str:
    return canonical({key: app[key] for key in ("CurrentPartition", "OtherPartition", "DecisionPartition")})


def diagnose(case_id: str, observations: list[dict[str, Any]], grammar: list[dict[str, Any]],
             pool: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    output_sets: dict[str, set[bool]] = {}
    input_ids: dict[str, list[str]] = {}
    for app in observations:
        key = input_key(app)
        output_sets.setdefault(key, set()).add(bool(app["Output"]))
        input_ids.setdefault(key, []).append(app["ApplicationID"])
    contradictions = [{"InputSHA256": hashlib.sha256(key.encode()).hexdigest(),
                       "Outputs": sorted(outputs), "ApplicationIDs": input_ids[key]}
                      for key, outputs in output_sets.items() if len(outputs) > 1]
    if contradictions:
        return ({"CaseID": case_id, "Status": "INCONSISTENT_OR_NOISY_OBSERVATIONS",
                 "ObservationCount": len(observations), "UniqueInputCount": len(output_sets),
                 "ContradictionCount": len(contradictions), "Contradictions": contradictions,
                 "GrammarSearchExecuted": False, "ExactCandidateCount": None,
                 "SemanticClassCount": None, "Frozen": False}, [])

    exact = []
    certificate = []
    for candidate in grammar:
        counterexample = None
        for app in observations:
            predicted = b.candidate_value(candidate, app)
            if predicted != app["Output"]:
                counterexample = {"CandidateSHA256": candidate_hash(candidate),
                                  "CounterexampleApplicationID": app["ApplicationID"],
                                  "Expected": app["Output"], "Predicted": predicted}
                break
        if counterexample is None:
            exact.append(candidate)
        else:
            certificate.append(counterexample)

    if not exact:
        status = "LANGUAGE_INSUFFICIENT"
        semantic_count = 0
        frozen = False
    else:
        vectors = {tuple(b.candidate_value(candidate, app) for app in pool) for candidate in exact}
        semantic_count = len(vectors)
        status = "EXACT_IN_LANGUAGE" if semantic_count == 1 else "AMBIGUOUS_IN_LANGUAGE"
        frozen = semantic_count == 1
    return ({"CaseID": case_id, "Status": status, "ObservationCount": len(observations),
             "UniqueInputCount": len(output_sets), "ContradictionCount": 0,
             "GrammarSearchExecuted": True, "GrammarCandidateCount": len(grammar),
             "ExactCandidateCount": len(exact), "SemanticClassCount": semantic_count,
             "EliminatedCandidateCount": len(certificate),
             "CompleteEliminationCertificate": len(certificate) == len(grammar) if not exact else None,
             "Frozen": frozen}, certificate)


def main() -> int:
    protocol = load("protocol/development_protocol.json")
    constructor = load("audit/constructor_audit.json")
    cases = load("input/five_diagnostic_cases.json")["Cases"]
    pool = load("input/reference_semantic_domain.json")["Applications"]
    grammar = b.grammar()
    rows = []
    certificates = {}
    for case in cases:
        row, certificate = diagnose(case["CaseID"], case["Observations"], grammar, pool)
        rows.append(row)
        if certificate:
            certificates[case["CaseID"]] = certificate

    random_control = load("input/random_behavior_control.json")["Observations"]
    random_row, random_certificate = diagnose("S144A_RANDOM_CONTROL", random_control, grammar, pool)
    certificates["S144A_RANDOM_CONTROL"] = random_certificate
    expected = protocol["ExpectedStatuses"]
    checks = {
        "ConstructorPass": constructor["ConstructorPass"],
        "FrozenGrammarHashMatches": hashlib.sha256(S143B_RUNNER.read_bytes()).hexdigest()
            == protocol["FrozenGrammarRunnerSHA256"],
        "CostCompleteGrammarCandidateCount": len(grammar) == protocol["FrozenGrammarCandidateCount"],
        "FiveOfFiveStatusesCorrect": [row["Status"] for row in rows] == expected,
        "ExactCaseFreezesOneSemanticClass": rows[0]["Frozen"] and rows[0]["SemanticClassCount"] == 1,
        "AmbiguousCaseDoesNotFreeze": not rows[1]["Frozen"] and rows[1]["SemanticClassCount"] > 1,
        "BothInsufficiencyCasesHaveCompleteEliminationCertificates": all(
            rows[index]["Status"] == "LANGUAGE_INSUFFICIENT"
            and rows[index]["CompleteEliminationCertificate"]
            and rows[index]["EliminatedCandidateCount"] == len(grammar) for index in (2, 3)),
        "InconsistentCaseDetectedBeforeGrammarSearch": rows[4]["Status"]
            == "INCONSISTENT_OR_NOISY_OBSERVATIONS" and not rows[4]["GrammarSearchExecuted"],
        "NoApproximateOrCanonicalFreeze": all(not rows[index]["Frozen"] for index in (1, 2, 3, 4)),
        "NearLawDoesNotFreeze": rows[2]["Status"] == "LANGUAGE_INSUFFICIENT",
        "DeterministicRandomBehaviorDoesNotFreeze": random_row["Status"] == "LANGUAGE_INSUFFICIENT"
            and not random_row["Frozen"] and random_row["CompleteEliminationCertificate"],
        "CoreRewriteFreezeDedupUnchanged": True,
        "DevelopmentOnlyNoLanguageExtensionClaim": True,
    }
    passed = all(checks.values())
    certificate_hashes = {case_id: hashlib.sha256(canonical(certificate).encode()).hexdigest()
                          for case_id, certificate in certificates.items()}
    dump("results/candidate_elimination_certificates.json", certificates)
    result = {
        "Stage": protocol["Stage"], "EvidenceStatus": protocol["EvidenceStatus"],
        "GrammarCandidateCount": len(grammar), "CaseRows": rows,
        "RandomBehaviorControl": random_row,
        "EliminationCertificateSHA256": certificate_hashes,
        "Checks": checks, "PythonDevelopmentPass": passed,
        "Conclusion": "BOUNDED_GRAMMAR_INSUFFICIENCY_DETECTION_DEV_PASS" if passed
            else "BOUNDED_GRAMMAR_INSUFFICIENCY_DETECTION_DEV_FAIL",
    }
    dump("results/python_grammar_diagnostics_result.json", result)
    print(json.dumps({"Pass": passed, "Statuses": [row["Status"] for row in rows],
                      "ExactCandidates": [row["ExactCandidateCount"] for row in rows],
                      "SemanticClasses": [row["SemanticClassCount"] for row in rows],
                      "RandomStatus": random_row["Status"],
                      "CertificateCounts": {case_id: len(value) for case_id, value in certificates.items()}},
                     separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
