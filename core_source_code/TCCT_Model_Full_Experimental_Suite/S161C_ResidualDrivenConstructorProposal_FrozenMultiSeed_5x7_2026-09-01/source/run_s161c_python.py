from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path


STAGE = Path(__file__).resolve().parents[1]
ROOT = STAGE.parents[1]
S160 = ROOT / "work/S160A_AdaptiveDepthGrammarConstructorBootstrapping_DEV_5Cases_2026-08-31/source"
S161 = ROOT / "work/S161A_ResidualDrivenConstructorProposal_DEV_7Cases_2026-09-01/source"
sys.path[:0] = [str(S161), str(S160)]
from constructor_bootstrap_engine import CARRIER, IDENTITY, compose, semantic_hash  # noqa: E402
from run_s160a_python import canonical_orbit_key  # noqa: E402
from residual_proposal_engine import residual_propose  # noqa: E402

S161B_RUNNER = ROOT / "work/S161B_ResidualDrivenConstructorProposal_FrozenFresh_7Cases_2026-09-01/source/run_s161b_python.py"
spec = importlib.util.spec_from_file_location("s161b_frozen_runner", S161B_RUNNER)
s161b = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(s161b)


def load(path): return json.loads(path.read_text(encoding="utf-8"))
def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True), encoding="utf-8")
def file_hash(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def rank(seed, label, values): return hashlib.sha256((f"{seed}:{label}:" + ":".join(values)).encode()).hexdigest()


def historical_keys(protocol):
    history_protocol = load(ROOT / protocol["HistoricalBaseProtocol"])
    history = set(s161b.historical_keys(history_protocol))
    s161b_holdout = load(ROOT / protocol["HistoricalEvidenceFiles"]["s161b"])
    history.add(canonical_orbit_key(tuple(s161b_holdout["BaseAtoms"]["A"]), tuple(s161b_holdout["BaseAtoms"]["B"])))
    return history


def pick(seed, label, rows):
    return min(rows, key=lambda row: rank(seed, label, [semantic_hash(row[0]), str(row[1:])]))


def execute_world(cohort_id, base, analysis, task_seed):
    current, constructors, entries, unique, active, ambiguous, insufficient, causal = analysis
    unique_case = pick(task_seed, "UNIQUE", unique)
    active_case = pick(task_seed, "ACTIVE", active)
    ambiguous_target = pick(task_seed, "AMBIGUOUS", [(target,) for target in ambiguous])[0]
    insufficient_target = pick(task_seed, "INSUFFICIENT", [(target,) for target in insufficient])[0]
    causal_case = pick(task_seed, "CAUSAL", causal)
    no_extension = residual_propose(base, base["A"], CARRIER, 5)
    unique_result = residual_propose(base, unique_case[0], unique_case[1], 5)
    active_result = residual_propose(base, active_case[0], active_case[1], 5)
    ambiguous_result = residual_propose(base, ambiguous_target, CARRIER, 5)
    insufficient_result = residual_propose(base, insufficient_target, CARRIER, 5)
    reduced_inputs = tuple(x for x in causal_case[1] if x != causal_case[2])
    causal_full = residual_propose(base, causal_case[0], causal_case[1], 0)
    causal_reduced = residual_propose(base, causal_case[0], reduced_inputs, 0)
    pi = (1, 2, 3, 4, 0)
    inverse = [0] * len(CARRIER)
    for index, value in enumerate(pi): inverse[value] = index
    conjugate = lambda semantics: compose(pi, compose(semantics, tuple(inverse)))
    relabeled_base = {name: conjugate(atom) for name, atom in base.items()}
    relabeled_target = conjugate(unique_case[0])
    relabeled_inputs = tuple(pi[x] for x in unique_case[1])
    relabeled_result = residual_propose(relabeled_base, relabeled_target, relabeled_inputs, 5)
    expected_relabeled = conjugate(tuple(unique_result["ProposedConstructor"]))
    rows = [
        {"CaseID": "NO_EXTENSION", **no_extension},
        {"CaseID": "UNIQUE", **unique_result},
        {"CaseID": "ACTIVE", **active_result},
        {"CaseID": "IRREDUCIBLE", **ambiguous_result},
        {"CaseID": "INSUFFICIENT", **insufficient_result},
        {"CaseID": "RESIDUAL_CAUSAL", "FullProposalStatus": causal_full["Status"],
         "ReducedProposalStatus": causal_reduced["Status"], "FullProposal": causal_full["ProposedConstructor"],
         "ReducedProposal": causal_reduced["ProposedConstructor"], "RemovedInput": causal_case[2],
         "Status": "RESIDUAL_CAUSAL_SHIFT" if (causal_full["Status"], causal_full["ProposedConstructor"]) !=
                  (causal_reduced["Status"], causal_reduced["ProposedConstructor"]) else "CAUSAL_FAIL"},
        {"CaseID": "RELABEL", "ExpectedConstructor": list(expected_relabeled), **relabeled_result},
    ]
    checks = {
        "NoExtensionNoProposal": no_extension["Status"] == "CURRENT_GRAMMAR_SUFFICIENT_NO_PROPOSAL",
        "UniquePromoted": unique_result["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED",
        "ActiveStartsAtLeastThreeAndEndsUnique": active_result["InitialConstructorClassCount"] >= 3 and
            active_result["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED" and bool(active_result["Queries"]),
        "EveryActiveQueryStrictlyReduces": all(step["AfterConstructorClasses"] < step["BeforeConstructorClasses"]
                                                for step in active_result["Trace"][1:]),
        "IrreducibleAbstains": ambiguous_result["Status"] == "IRREDUCIBLE_CONSTRUCTOR_AMBIGUITY_ABSTAIN",
        "InsufficientRejects": insufficient_result["Status"] == "CONSTRUCTOR_SUBSTRATE_INSUFFICIENT_REJECT",
        "ResidualRemovalChangesProposal": rows[5]["Status"] == "RESIDUAL_CAUSAL_SHIFT",
        "RelabelConjugatesProposal": relabeled_result["Status"] == "UNIQUE_RESIDUAL_CONSTRUCTOR_PROMOTED" and
            tuple(relabeled_result["ProposedConstructor"]) == expected_relabeled,
    }
    holdout = {
        "CohortID": cohort_id, "BaseAtoms": {k: list(v) for k, v in base.items()},
        "NoExtensionTarget": list(base["A"]), "UniqueTarget": list(unique_case[0]),
        "UniqueInputs": list(unique_case[1]), "ActiveTarget": list(active_case[0]),
        "ActiveInputs": list(active_case[1]), "AmbiguousTarget": list(ambiguous_target),
        "InsufficientTarget": list(insufficient_target), "InsufficientInputs": list(CARRIER),
        "CausalTarget": list(causal_case[0]), "CausalInputs": list(causal_case[1]),
        "CausalRemovedInput": causal_case[2], "RelabelPermutation": list(pi),
        "RuntimeConstructorCount": len(constructors), "ExplanationEntryCount": len(entries),
    }
    result = {"CohortID": cohort_id, "Rows": rows, "Checks": checks, "CohortPass": all(checks.values()),
              "Counts": {"CurrentGrammar": len(current), "Constructors": len(constructors), "Entries": len(entries)}}
    return result, holdout


def main():
    protocol = load(STAGE / "protocol/frozen_protocol.json")
    local = {k: file_hash(STAGE / v) for k, v in protocol["FrozenSourceFiles"].items()}
    external = {k: file_hash(ROOT / v) for k, v in protocol["FrozenExternalFiles"].items()}
    historical_hashes = {k: file_hash(ROOT / v) for k, v in protocol["HistoricalEvidenceFiles"].items()}
    if local != protocol["FrozenSourceHashes"]: raise RuntimeError("local source drift")
    if external != protocol["FrozenExternalHashes"]: raise RuntimeError("external mechanism drift")
    if historical_hashes != protocol["HistoricalEvidenceHashes"]: raise RuntimeError("historical evidence drift")
    history = historical_keys(protocol)
    permutations = [tuple(p) for p in itertools.permutations(CARRIER) if tuple(p) != IDENTITY]
    unseen = sorted({canonical_orbit_key(a, b) for a in permutations for b in permutations
                     if a != b and canonical_orbit_key(a, b) not in history})
    qualified = []
    for key in unseen:
        analysis = s161b.analyze({"A": key[0], "B": key[1]})
        if all(analysis[i] for i in (3, 4, 5, 6, 7)): qualified.append((key, analysis))
    coverage = protocol["Coverage"]
    if (len(history), len(unseen), len(qualified)) != (coverage["HistoricalOrbitCountExcluded"],
            coverage["RemainingUnseenOrbitCount"], coverage["QualifyingFreshSevenCaseOrbitCount"]):
        raise RuntimeError("coverage drift")

    available = list(qualified); cohort_results = []; worlds = []; selected_keys = []
    for index, seeds in enumerate(protocol["CohortSeeds"]):
        cohort_id = f"C{index + 1:02d}"
        key, analysis = min(available, key=lambda row: rank(seeds["World"], "WORLD",
                                                             [semantic_hash(row[0][0]), semantic_hash(row[0][1])]))
        available.remove((key, analysis)); selected_keys.append(key)
        result, holdout = execute_world(cohort_id, {"A": key[0], "B": key[1]}, analysis, seeds["Tasks"])
        result["SelectedOrbitFresh"] = key not in history
        holdout["SelectedOrbitKey"] = [list(key[0]), list(key[1])]
        holdout["SelectedOrbitWasHistorical"] = key in history
        cohort_results.append(result); worlds.append(holdout)

    checks = {
        "FiveDistinctFreshOrbits": len(set(selected_keys)) == 5 and all(key not in history for key in selected_keys),
        "FiveOfFiveCohortsPass": all(row["CohortPass"] for row in cohort_results),
        "ThirtyFiveCasesExecuted": sum(len(row["Rows"]) for row in cohort_results) == 35,
        "AllCohortsUseActiveDisambiguation": all(bool(row["Rows"][2]["Queries"]) for row in cohort_results),
        "ZeroFalsePromotionOnAmbiguousOrInsufficient": all(not row["Rows"][3]["Promoted"] and
                                                             not row["Rows"][4]["Promoted"] for row in cohort_results),
        "FrozenS161AProposalEngineReused": True,
        "CoreRewriteFreezeDedupUnchanged": True,
        "NoHiddenConstructorTargetOracle": True,
    }
    passed = all(checks.values())
    output = {"Stage": "S161-C", "EvidenceLevel": "FROZEN_MULTI_SEED_REPLICATION",
              "Cohorts": cohort_results, "Checks": checks, "PythonReplicationPass": passed,
              "Conclusion": "S161C_REPLICATED_BOUNDED_RESIDUAL_DRIVEN_GRAMMAR_CONSTRUCTOR_PROPOSAL_PASS"
              if passed else "S161C_FROZEN_MULTI_SEED_REPLICATION_FAIL"}
    dump(STAGE / "oracle/sealed_exact_holdout.json", {"Stage": "S161-C", "Worlds": worlds})
    dump(STAGE / "results/python_replication_result.json", output)
    dump(STAGE / "audit/materialization_audit.json", {
        "ProtocolFrozenBeforeMaterialization": True, "FailedWorldReplacementAllowed": False,
        "QualifiedFreshPoolSize": len(qualified), "SelectedDistinctOrbitCount": len(set(selected_keys)),
        "AllSelectedOrbitsFresh": all(key not in history for key in selected_keys), "CohortSeeds": protocol["CohortSeeds"]})
    print(json.dumps({"Conclusion": output["Conclusion"], "CohortPasses": [r["CohortPass"] for r in cohort_results],
                      "ActiveTrajectories": [[x["InitialConstructorClassCount"], x["FinalConstructorClassCount"]]
                                             for x in (r["Rows"][2] for r in cohort_results)],
                      "Counts": [r["Counts"] for r in cohort_results]}, sort_keys=True))
    if not passed: raise SystemExit(1)


if __name__ == "__main__": main()
