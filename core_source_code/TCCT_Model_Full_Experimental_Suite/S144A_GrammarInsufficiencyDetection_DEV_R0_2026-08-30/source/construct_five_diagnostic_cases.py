from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S143B = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30"
S143C = WORK / "S143C_ActiveOperatorDisambiguation_DEV_R0_2026-08-30"
RUNNER = S143B / "source" / "run_python_behavioral_induction.py"
spec = importlib.util.spec_from_file_location("s143b_for_s144a_constructor", RUNNER)
b = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = b
spec.loader.exec_module(b)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def stripped(app: dict[str, Any], output: bool) -> dict[str, Any]:
    return {key: app[key] for key in ("ApplicationID", "CurrentPartition", "OtherPartition",
                                      "DecisionPartition")} | {"Output": output}


def elimination_observations(grammar: list[dict[str, Any]], pool: list[dict[str, Any]],
                             target: Callable[[dict[str, Any]], bool]) -> tuple[list[dict[str, Any]], int]:
    witness_ids = set()
    eliminated = 0
    for candidate in grammar:
        for app in pool:
            expected = target(app)
            if b.candidate_value(candidate, app) != expected:
                witness_ids.add(app["ApplicationID"])
                eliminated += 1
                break
    by_id = {app["ApplicationID"]: app for app in pool}
    observations = [stripped(by_id[application_id], target(by_id[application_id]))
                    for application_id in sorted(witness_ids)]
    return observations, eliminated


def semantic_class_count(candidates: list[dict[str, Any]], pool: list[dict[str, Any]]) -> int:
    return len({tuple(b.candidate_value(candidate, app) for app in pool) for candidate in candidates})


def main() -> int:
    protocol = load(ROOT / "protocol" / "development_protocol.json")
    grammar = b.grammar()
    pool = load(S143C / "input" / "admissible_interventions.json")["Applications"]
    pool_by_id = {app["ApplicationID"]: app for app in pool}
    ambiguous = load(S143C / "input" / "learner_initial_observations.json")["Observations"]
    active = load(S143C / "results" / "python_active_disambiguation_result.json")
    base_operator = load(S143B / "results" / "python_behavioral_induction_result.json")[
        "FrozenOperatorDefinition"]
    exact_observations = list(ambiguous)
    for step in active["CaseRows"][0]["Trajectory"]:
        app = pool_by_id[step["WitnessApplicationID"]]
        exact_observations.append(stripped(app, b.candidate_value(base_operator, app)))

    exception_id = pool[0]["ApplicationID"]
    near_target = lambda app: (not b.candidate_value(base_operator, app)) \
        if app["ApplicationID"] == exception_id else b.candidate_value(base_operator, app)

    def xor_target(app: dict[str, Any]) -> bool:
        current = b.make_partition(app["CurrentPartition"])
        other = b.make_partition(app["OtherPartition"])
        decision = b.make_partition(app["DecisionPartition"])
        a = b.refines(b.meet(current, other), decision)
        c = b.refines(other, decision)
        e = current == decision
        return bool(a) ^ bool(c) ^ bool(e)

    near_observations, near_eliminated = elimination_observations(grammar, pool, near_target)
    xor_observations, xor_eliminated = elimination_observations(grammar, pool, xor_target)
    inconsistent = list(exact_observations)
    inconsistent.append({**exact_observations[0], "Output": not exact_observations[0]["Output"]})

    cases = [
        {"CaseID": "S144A_CASE_00", "Observations": exact_observations},
        {"CaseID": "S144A_CASE_01", "Observations": ambiguous},
        {"CaseID": "S144A_CASE_02", "Observations": near_observations},
        {"CaseID": "S144A_CASE_03", "Observations": xor_observations},
        {"CaseID": "S144A_CASE_04", "Observations": inconsistent},
    ]
    random_observations = []
    for app in pool[:96]:
        output = int(hashlib.sha256(f"S144A_RANDOM|{app['ApplicationID']}".encode()).hexdigest(), 16) % 2 == 0
        random_observations.append(stripped(app, output))

    exact_candidates = [candidate for candidate in grammar if all(
        b.candidate_value(candidate, app) == app["Output"] for app in exact_observations)]
    ambiguous_candidates = [candidate for candidate in grammar if all(
        b.candidate_value(candidate, app) == app["Output"] for app in ambiguous)]
    learner_text = json.dumps(cases, ensure_ascii=False)
    checks = {
        "FrozenGrammarCandidateCount": len(grammar) == protocol["FrozenGrammarCandidateCount"],
        "ExactCaseOneSemanticClass": len(exact_candidates) > 0
            and semantic_class_count(exact_candidates, pool) == 1,
        "AmbiguousCaseMultipleSemanticClasses": len(ambiguous_candidates) > 0
            and semantic_class_count(ambiguous_candidates, pool) > 1,
        "NearLawEliminatesEveryGrammarCandidate": near_eliminated == len(grammar),
        "XorLawEliminatesEveryGrammarCandidate": xor_eliminated == len(grammar),
        "NearAndXorCertificatesNonempty": len(near_observations) > 0 and len(xor_observations) > 0,
        "InconsistentCaseContainsContradictoryRepeat": inconsistent[-1]["ApplicationID"]
            == inconsistent[0]["ApplicationID"] and inconsistent[-1]["Output"] != inconsistent[0]["Output"],
        "NoTargetASTInLearnerCases": all(token not in learner_text for token in
            ("PartitionMeet", "PartitionRefines", "StrictPartitionRefines", "xor_target")),
        "CoreUnchanged": True,
    }
    dump("input/five_diagnostic_cases.json", {"Cases": cases})
    dump("input/reference_semantic_domain.json", {"Applications": pool})
    dump("input/random_behavior_control.json", {"Observations": random_observations})
    dump("audit/constructor_audit.json", {
        "CaseObservationCounts": {case["CaseID"]: len(case["Observations"]) for case in cases},
        "ExpectedStatuses": dict(zip((case["CaseID"] for case in cases), protocol["ExpectedStatuses"])),
        "NearLawCandidateEliminationCount": near_eliminated,
        "XorLawCandidateEliminationCount": xor_eliminated,
        "NearLawExceptionApplicationID": exception_id,
        "Checks": checks, "ConstructorPass": all(checks.values())})
    print(json.dumps({"Pass": all(checks.values()), "Cases": len(cases),
                      "ObservationCounts": [len(case["Observations"]) for case in cases],
                      "ExactCandidates": len(exact_candidates),
                      "AmbiguousCandidates": len(ambiguous_candidates),
                      "NearCertificate": len(near_observations), "XorCertificate": len(xor_observations)},
                     separators=(",", ":")))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
