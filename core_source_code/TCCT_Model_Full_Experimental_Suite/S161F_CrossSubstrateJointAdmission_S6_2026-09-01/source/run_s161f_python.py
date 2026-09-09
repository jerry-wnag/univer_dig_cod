from __future__ import annotations

import hashlib
import itertools
import json
import sys
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]
sys.path.insert(0, str(STAGE / "source"))
from generic_joint_admission_engine import (all_subsets, canonical_pair, compatible_joint, compose,  # noqa: E402
    constructor_classes, identity, joint_residual_propose, proposal_space, semantic_hash)


CARRIER = tuple(range(6))
def load(path): return json.loads(path.read_text(encoding="utf-8"))
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
def file_hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rank(seed, label, values): return hashlib.sha256((f"{seed}:{label}:" + ":".join(values)).encode()).hexdigest()


def candidate(seed, counter, permutations):
    digest = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
    first = int.from_bytes(digest[:8], "big") % len(permutations)
    second = int.from_bytes(digest[8:16], "big") % (len(permutations) - 1)
    if second >= first: second += 1
    return permutations[first], permutations[second]


def audit_exclusion_keys(protocol, permutations):
    keys = set(); counter = 0
    while len(keys) < protocol["AuditExclusion"]["DistinctOrbitCount"]:
        keys.add(canonical_pair(*candidate(protocol["AuditExclusion"]["Seed"], counter, permutations), CARRIER))
        counter += 1
    return keys


def counts(current, entries, target, subset):
    observations = {x: target[x] for x in subset}
    current_matches, constructor_matches = compatible_joint(current, entries, observations)
    return len(current_matches), len(constructor_classes(constructor_matches))


def analyze(base):
    current, constructors, entries = proposal_space(base, CARRIER)
    support = {}
    for constructor, target in entries: support.setdefault(target, set()).add(constructor)
    unique, joint_active, causal = [], [], []
    for target, exact_classes in support.items():
        if len(exact_classes) != 1: continue
        for subset in all_subsets(CARRIER):
            current_count, constructor_count = counts(current, entries, target, subset)
            if current_count == 0 and constructor_count == 1:
                unique.append((target, subset))
                for point in subset:
                    reduced = tuple(x for x in subset if x != point)
                    reduced_current, _ = counts(current, entries, target, reduced)
                    if reduced_current > 0:
                        full_run = joint_residual_propose(base, target, subset, 0, CARRIER)
                        reduced_run = joint_residual_propose(base, target, reduced, 0, CARRIER)
                        if full_run["Promoted"] and reduced_run["Status"] == "RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL":
                            causal.append((target, subset, point)); break
            if current_count > 0 and constructor_count > 0:
                run = joint_residual_propose(base, target, subset, 6, CARRIER)
                if run["Promoted"] and run["Queries"]: joint_active.append((target, subset))
    ambiguous = [target for target, classes in support.items() if len(classes) >= 2]
    insufficient = [target for target in itertools.permutations(CARRIER) if target not in current and target not in support]
    return current, constructors, entries, unique, joint_active, causal, ambiguous, insufficient


def pick(seed, label, rows):
    return min(rows, key=lambda row: rank(seed, label, [semantic_hash(row[0]), str(row[1:])]))


def execute(cohort_id, base, analysis, task_seed):
    current, constructors, entries, unique_cases, active_cases, causal_cases, ambiguous, insufficient = analysis
    unique_case = pick(task_seed, "UNIQUE", unique_cases)
    active_case = pick(task_seed, "JOINT_ACTIVE", active_cases)
    causal_case = pick(task_seed, "CAUSAL", causal_cases)
    ambiguous_target = pick(task_seed, "AMBIGUOUS", [(target,) for target in ambiguous])[0]
    insufficient_target = pick(task_seed, "INSUFFICIENT", [(target,) for target in insufficient])[0]
    no_extension = joint_residual_propose(base, base["A"], CARRIER, 6, CARRIER)
    unique = joint_residual_propose(base, unique_case[0], unique_case[1], 6, CARRIER)
    active = joint_residual_propose(base, active_case[0], active_case[1], 6, CARRIER)
    causal_full = joint_residual_propose(base, causal_case[0], causal_case[1], 0, CARRIER)
    reduced_inputs = tuple(x for x in causal_case[1] if x != causal_case[2])
    causal_reduced = joint_residual_propose(base, causal_case[0], reduced_inputs, 0, CARRIER)
    ambiguous_result = joint_residual_propose(base, ambiguous_target, CARRIER, 6, CARRIER)
    insufficient_result = joint_residual_propose(base, insufficient_target, CARRIER, 6, CARRIER)
    pi = (1, 2, 3, 4, 5, 0); inverse = [0] * len(pi)
    for index, value in enumerate(pi): inverse[value] = index
    conjugate = lambda semantics: compose(pi, compose(semantics, tuple(inverse)))
    relabeled_base = {name: conjugate(atom) for name, atom in base.items()}
    relabeled_target = conjugate(unique_case[0]); relabeled_inputs = tuple(pi[x] for x in unique_case[1])
    relabeled = joint_residual_propose(relabeled_base, relabeled_target, relabeled_inputs, 6, CARRIER)
    expected_relabeled = conjugate(tuple(unique["ProposedConstructor"]))
    rows = [
        {"CaseID": "NO_EXTENSION", **no_extension}, {"CaseID": "UNIQUE", **unique},
        {"CaseID": "JOINT_ACTIVE", **active},
        {"CaseID": "CURRENT_COMPATIBLE_CAUSAL", "Full": causal_full, "Reduced": causal_reduced,
         "RemovedInput": causal_case[2]},
        {"CaseID": "AMBIGUOUS", **ambiguous_result}, {"CaseID": "INSUFFICIENT", **insufficient_result},
        {"CaseID": "RELABEL", "ExpectedConstructor": list(expected_relabeled), **relabeled},
    ]
    checks = {
        "NoExtensionNoProposal": no_extension["Status"] == "CURRENT_GRAMMAR_SUFFICIENT_NO_PROPOSAL",
        "UniquePromoted": unique["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED",
        "JointActiveStartsMixed": active["InitialCurrentGrammarCandidateCount"] > 0 and active["InitialConstructorClassCount"] > 0,
        "JointActivePromotesAfterQueries": bool(active["Queries"]) and active["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED",
        "EveryJointQueryStrictlyReduces": all(step["AfterJointDecisionClasses"] < step["BeforeJointDecisionClasses"]
                                               for step in active["Trace"][1:]),
        "CausalFullPromotes": causal_full["Promoted"],
        "CausalReducedBlocksPromotion": causal_reduced["Status"] == "RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL" and not causal_reduced["Promoted"],
        "AmbiguityAbstains": ambiguous_result["Status"] == "IRREDUCIBLE_CONSTRUCTOR_AMBIGUITY_ABSTAIN",
        "InsufficiencyRejects": insufficient_result["Status"] == "CONSTRUCTOR_SUBSTRATE_INSUFFICIENT_REJECT",
        "RelabelConjugacy": relabeled["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED" and tuple(relabeled["ProposedConstructor"]) == expected_relabeled,
    }
    result = {"CohortID": cohort_id, "Rows": rows, "Checks": checks, "CohortPass": all(checks.values()),
              "Counts": {"CurrentGrammar": len(current), "Constructors": len(constructors), "Entries": len(entries)}}
    holdout = {"CohortID": cohort_id, "BaseAtoms": {k: list(v) for k, v in base.items()},
               "NoExtensionTarget": list(base["A"]), "UniqueTarget": list(unique_case[0]),
               "UniqueInputs": list(unique_case[1]), "JointActiveTarget": list(active_case[0]),
               "JointActiveInputs": list(active_case[1]), "CausalTarget": list(causal_case[0]),
               "CausalInputs": list(causal_case[1]), "CausalRemovedInput": causal_case[2],
               "AmbiguousTarget": list(ambiguous_target), "InsufficientTarget": list(insufficient_target),
               "RelabelPermutation": list(pi), "RuntimeConstructorCount": len(constructors),
               "ExplanationEntryCount": len(entries)}
    return result, holdout


def main():
    protocol = load(STAGE / "protocol/frozen_protocol.json")
    local = {k: file_hash(STAGE / rel) for k, rel in protocol["FrozenSourceFiles"].items()}
    external = {k: file_hash(ROOT / rel) for k, rel in protocol["FrozenExternalFiles"].items()}
    evidence = {k: file_hash(ROOT / rel) for k, rel in protocol["HistoricalEvidenceFiles"].items()}
    if local != protocol["FrozenSourceHashes"]: raise RuntimeError("local source drift")
    if external != protocol["FrozenExternalHashes"]: raise RuntimeError("external mechanism drift")
    if evidence != protocol["HistoricalEvidenceHashes"]: raise RuntimeError("historical evidence drift")
    permutations = [tuple(p) for p in itertools.permutations(CARRIER) if tuple(p) != identity(CARRIER)]
    excluded = audit_exclusion_keys(protocol, permutations); selected = set(); results = []; worlds = []; attempts = []
    for index, seeds in enumerate(protocol["CohortSeeds"]):
        chosen = None; local_seen = set()
        for counter in range(protocol["MaterializationPolicy"]["MaximumCandidateAttemptsPerCohort"]):
            key = canonical_pair(*candidate(seeds["World"], counter, permutations), CARRIER)
            if key in excluded or key in selected or key in local_seen: continue
            local_seen.add(key); analysis = analyze({"A": key[0], "B": key[1]})
            if all(analysis[i] for i in (3, 4, 5, 6, 7)):
                chosen = (key, analysis, counter + 1); break
        if chosen is None: raise RuntimeError(f"cohort {index + 1} materialization exhausted")
        key, analysis, attempt_count = chosen; selected.add(key); attempts.append(attempt_count)
        result, holdout = execute(f"C{index + 1:02d}", {"A": key[0], "B": key[1]}, analysis, seeds["Tasks"])
        holdout["SelectedOrbitKey"] = [list(key[0]), list(key[1])]; holdout["MaterializationAttempts"] = attempt_count
        results.append(result); worlds.append(holdout)
    checks = {"FiveDistinctNonAuditOrbits": len(selected) == 5 and not (selected & excluded),
              "FiveOfFiveCohortsPass": all(result["CohortPass"] for result in results),
              "ThirtyFiveCasesExecuted": sum(len(result["Rows"]) for result in results) == 35,
              "AllCohortsJointActive": all(bool(result["Rows"][2]["Queries"]) for result in results),
              "AllCausalReducedBlockPromotion": all(not result["Rows"][3]["Reduced"]["Promoted"] for result in results),
              "ZeroFalsePromotionControls": all(not result["Rows"][4]["Promoted"] and not result["Rows"][5]["Promoted"] for result in results),
              "CoreRewriteFreezeDedupUnchanged": True}
    passed = all(checks.values())
    output = {"Stage": "S161-F", "EvidenceLevel": "CROSS_SUBSTRATE_FROZEN_MULTI_SEED_REPLICATION",
              "CarrierSize": 6, "Cohorts": results, "Checks": checks, "PythonReplicationPass": passed,
              "Conclusion": "S161F_CROSS_SUBSTRATE_REPLICATED_EVIDENCE_GATED_RESIDUAL_CONSTRUCTOR_FORMATION_PASS"
              if passed else "S161F_CROSS_SUBSTRATE_MULTI_SEED_REPLICATION_FAIL"}
    dump(STAGE / "oracle/sealed_exact_holdout.json", {"Stage": "S161-F", "CarrierSize": 6, "Worlds": worlds})
    dump(STAGE / "results/python_replication_result.json", output)
    dump(STAGE / "audit/materialization_audit.json", {"ProtocolFrozenBeforeMaterialization": True,
        "FailedWorldReplacementAllowed": False, "AuditOrbitCountExcluded": len(excluded),
        "SelectedDistinctOrbitCount": len(selected), "SelectedAuditOverlap": len(selected & excluded),
        "AttemptsPerCohort": attempts, "CohortSeeds": protocol["CohortSeeds"]})
    print(json.dumps({"Conclusion": output["Conclusion"], "CohortPasses": [r["CohortPass"] for r in results],
        "JointTrajectories": [[row["InitialJointDecisionClassCount"], row["FinalJointDecisionClassCount"]]
                              for row in (result["Rows"][2] for result in results)],
        "Attempts": attempts, "Counts": [r["Counts"] for r in results]}, sort_keys=True))
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
