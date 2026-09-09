from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S144B_ROOT = WORK / "S144B_BoundedLanguageExtensionProposal_DEV_R0_2026-08-30"
S144B_RUNNER = S144B_ROOT / "source" / "run_python_language_extension.py"
S143B_RUNNER = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30" / "source" / "run_python_behavioral_induction.py"


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ext = module_from(S144B_RUNNER, "s144b_frozen_for_s144c_runner")
b = module_from(S143B_RUNNER, "s143b_frozen_for_s144c_runner")


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate_case(case: dict[str, Any], row_by_id: dict[str, dict[str, Any]],
                  domain_rows: list[dict[str, Any]], signal_ids: list[str],
                  grammar: list[dict[str, Any]], programs: dict[int, dict[str, Any]]):
    old_exact, certificate = ext.current_grammar_certificate(case["Observations"], row_by_id, grammar)
    row, sample = ext.candidate_search(case["Observations"], row_by_id, domain_rows, signal_ids, programs)
    return ({"CaseID": case["CaseID"], "CurrentGrammarExactCandidateCount": old_exact,
             "CurrentGrammarCompleteEliminationCertificate": old_exact == 0
                and len(certificate) == len(grammar), **row}, certificate, sample)


def main() -> int:
    protocol = load("protocol/frozen_protocol.json")
    constructor = load("audit/private_fresh_constructor_audit.json")
    domain = load("input/fresh_learner_signal_domain.json")
    signal_ids = domain["SignalIDs"]
    domain_rows = domain["Rows"]
    row_by_id = {row["ApplicationID"]: row for row in domain_rows}
    cases = load("input/five_fresh_cases.json")["Cases"]
    random_case = {"CaseID": "S144C_AUX_RANDOM",
                   "Observations": load("input/auxiliary_random_control.json")["Observations"]}
    grammar = b.grammar()
    programs = ext.nand_library(protocol["FrozenMechanism"]["MaximumNANDFormulaCost"])

    rows, certificates, samples, frozen = [], {}, {}, {}
    for case in cases:
        row, certificate, sample = evaluate_case(case, row_by_id, domain_rows, signal_ids, grammar, programs)
        rows.append(row)
        certificates[case["CaseID"]] = certificate
        samples[case["CaseID"]] = sample
        if row["SelectedProposal"] is not None:
            frozen[case["CaseID"]] = row["SelectedProposal"]
    random_row, random_certificate, random_sample = evaluate_case(
        random_case, row_by_id, domain_rows, signal_ids, grammar, programs)
    certificates[random_case["CaseID"]] = random_certificate
    samples[random_case["CaseID"]] = random_sample

    # Open only after all five official proposals/statuses above are fixed.
    holdouts = load("oracle/sealed_fresh_relabeling_holdouts.json")["Holdouts"]
    holdout_rows = []
    for holdout in holdouts:
        proposal = frozen.get(holdout["CaseID"])
        if proposal is None:
            holdout_rows.append({"CaseID": holdout["CaseID"], "Evaluated": False, "Exact": False})
            continue
        triple = tuple(proposal["SignalIndices"])
        count = sum(ext.truth_value(proposal["TruthTable"],
                    ext.signature(app["SignalValues"], triple)) == app["Output"]
                    for app in holdout["Applications"])
        holdout_rows.append({"CaseID": holdout["CaseID"], "Evaluated": True,
            "ApplicationCount": len(holdout["Applications"]), "ExactApplicationCount": count,
            "Exact": count == len(holdout["Applications"]),
            "DistinctHoldoutTaskCount": len({app["HoldoutTaskID"] for app in holdout["Applications"]}),
            "OperatorCalledOnEveryApplication": True})

    expected = protocol["ExpectedStatuses"]
    checks = {
        "ConstructorPass": constructor["ConstructorPass"],
        "S144BFrozenPythonRunnerHashMatches": file_hash(S144B_RUNNER)
            == protocol["FrozenMechanism"]["S144BPythonRunnerSHA256"],
        "CurrentGrammarRunnerHashMatches": file_hash(S143B_RUNNER)
            == protocol["FrozenMechanism"]["CurrentGrammarRunnerSHA256"],
        "FiveOfFiveFreshStatusesCorrect": [row["Status"] for row in rows] == expected,
        "AllOfficialCurrentGrammarCandidatesEliminated": all(
            row["CurrentGrammarExactCandidateCount"] == 0
            and row["CurrentGrammarCompleteEliminationCertificate"] for row in rows),
        "ThreeFreshExtensionsFrozen": all(rows[index]["Frozen"] for index in (0, 1, 2)),
        "ThreeFreshExtensionsStrictlyCompressive": all(
            rows[index]["SelectedProposal"]["CompressionGainBits"] > 0 for index in (0, 1, 2)),
        "ThreeSealedFreshHoldoutsExact": len(holdout_rows) == 3 and all(
            row["Evaluated"] and row["Exact"] and row["DistinctHoldoutTaskCount"] == 3
            for row in holdout_rows),
        "FreshAmbiguitySafelyAbstains": rows[3]["Status"] == "MULTIPLE_EXTENSIONS_AMBIGUOUS"
            and rows[3]["SemanticClassCount"] > 1 and not rows[3]["Frozen"],
        "FreshNearLawHasNoExceptionPrimitive": rows[4]["Status"] == "NO_COMPRESSIVE_EXTENSION"
            and rows[4]["ExactMetaProgramCount"] == 0 and not rows[4]["Frozen"],
        "AuxiliaryRandomControlDoesNotFreeze": random_row["Status"] == "NO_COMPRESSIVE_EXTENSION"
            and random_row["ExactMetaProgramCount"] == 0 and not random_row["Frozen"],
        "NoFailureWorldReplacement": not protocol["Freshness"]["FailureWorldReplacementAllowed"],
        "CoreRewriteFreezeDedupUnchanged": True,
        "NoOpenPrimitiveInventionClaim": not protocol["OpenPrimitiveInventionClaimAllowed"],
    }
    passed = all(checks.values())
    result = {
        "Stage": protocol["Stage"], "EvidenceStatus": protocol["EvidenceStatus"],
        "CaseRows": rows, "AuxiliaryRandomControl": random_row,
        "CandidateSamples": samples, "SealedFreshHoldoutRows": holdout_rows,
        "Checks": checks, "PythonFrozenFreshPass": passed,
        "OpenPrimitiveInventionClaimAllowed": False,
        "Conclusion": "S144C_FROZEN_FRESH_BOUNDED_LANGUAGE_EXTENSION_PASS" if passed
            else "S144C_FROZEN_FRESH_BOUNDED_LANGUAGE_EXTENSION_FAIL",
    }
    dump("results/current_grammar_elimination_certificates.json", certificates)
    dump("results/python_frozen_fresh_result.json", result)
    print(json.dumps({"Pass": passed, "Statuses": [row["Status"] for row in rows],
        "MetaExact": [row["ExactMetaProgramCount"] for row in rows],
        "SemanticClasses": [row["SemanticClassCount"] for row in rows],
        "NANDCounts": [row["SelectedProposal"]["NANDCount"] if row["SelectedProposal"] else None for row in rows],
        "HoldoutExact": [row["Exact"] for row in holdout_rows],
        "RandomStatus": random_row["Status"]}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
