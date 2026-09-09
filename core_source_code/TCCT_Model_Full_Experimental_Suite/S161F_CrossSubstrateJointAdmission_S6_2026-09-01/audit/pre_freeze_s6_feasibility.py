from __future__ import annotations

import hashlib
import itertools
import json
import sys
import time
from pathlib import Path


SRC = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SRC))
from generic_joint_admission_engine import (all_subsets, canonical_pair, compatible_joint,  # noqa: E402
    constructor_classes, identity, joint_residual_propose, proposal_space)


CARRIER = tuple(range(6))
AUDIT_SEED = "S161F-S6-FEASIBILITY-AUDIT-ONLY-20260901"
TARGET_DISTINCT_ORBITS = 300
MAX_COUNTER = 3000


def candidate(seed, counter, permutations):
    digest = hashlib.sha256(f"{seed}:{counter}".encode()).digest()
    first = int.from_bytes(digest[:8], "big") % len(permutations)
    second = int.from_bytes(digest[8:16], "big") % (len(permutations) - 1)
    if second >= first: second += 1
    return permutations[first], permutations[second]


def counts(current, entries, target, subset):
    observations = {x: target[x] for x in subset}
    current_matches, constructor_matches = compatible_joint(current, entries, observations)
    return len(current_matches), len(constructor_classes(constructor_matches))


def qualification(base):
    current, constructors, entries = proposal_space(base, CARRIER)
    support = {}
    for constructor, target in entries: support.setdefault(target, set()).add(constructor)
    unique_ready = active_ready = causal_ready = False
    for target, exact_classes in support.items():
        if len(exact_classes) != 1: continue
        for subset in all_subsets(CARRIER):
            current_count, constructor_count = counts(current, entries, target, subset)
            if current_count == 0 and constructor_count == 1:
                unique_ready = True
                for point in subset:
                    reduced = tuple(x for x in subset if x != point)
                    reduced_current, _ = counts(current, entries, target, reduced)
                    if reduced_current > 0:
                        full_run = joint_residual_propose(base, target, subset, 0, CARRIER)
                        reduced_run = joint_residual_propose(base, target, reduced, 0, CARRIER)
                        if full_run["Promoted"] and reduced_run["Status"] == "RESIDUAL_NOT_ESTABLISHED_NO_PROPOSAL":
                            causal_ready = True; break
            if current_count > 0 and constructor_count > 0:
                run = joint_residual_propose(base, target, subset, 5, CARRIER)
                if run["Promoted"] and run["Queries"]: active_ready = True
            if unique_ready and active_ready and causal_ready: break
        if unique_ready and active_ready and causal_ready: break
    ambiguous = any(len(classes) >= 2 for classes in support.values())
    insufficient = len(set(itertools.permutations(CARRIER)) - set(current) - set(support)) > 0
    return unique_ready and active_ready and causal_ready and ambiguous and insufficient, {
        "Current": len(current), "Constructors": len(constructors), "Entries": len(entries)}


def main():
    started = time.perf_counter()
    permutations = [tuple(p) for p in itertools.permutations(CARRIER) if tuple(p) != identity(CARRIER)]
    seen = set(); qualified = []; summaries = []
    for counter in range(MAX_COUNTER):
        first, second = candidate(AUDIT_SEED, counter, permutations)
        key = canonical_pair(first, second, CARRIER)
        if key in seen: continue
        seen.add(key)
        passed, summary = qualification({"A": key[0], "B": key[1]})
        summaries.append(summary)
        if passed: qualified.append(key)
        if len(seen) >= TARGET_DISTINCT_ORBITS: break
    out = {
        "AuditType": "PRE_FREEZE_S6_FEASIBILITY_SAMPLE",
        "CarrierSize": 6,
        "AuditSeed": AUDIT_SEED,
        "DistinctNonIsomorphicWorldsAudited": len(seen),
        "QualifyingSevenCaseWorlds": len(qualified),
        "FiveCohortsFeasibleInAuditSample": len(qualified) >= 5,
        "QualificationRate": len(qualified) / len(seen) if seen else 0,
        "CurrentGrammarSemanticCountRange": [min(s["Current"] for s in summaries), max(s["Current"] for s in summaries)],
        "RuntimeConstructorCountRange": [min(s["Constructors"] for s in summaries), max(s["Constructors"] for s in summaries)],
        "ExplanationEntryCountRange": [min(s["Entries"] for s in summaries), max(s["Entries"] for s in summaries)],
        "ElapsedSeconds": time.perf_counter() - started,
        "FutureCohortSeedsMaterialized": False,
        "AuditWorldsExcludedFromFutureCohorts": True,
    }
    output = Path(__file__).with_name("s6_feasibility_summary.json")
    output.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if not out["FiveCohortsFeasibleInAuditSample"]: raise SystemExit(1)


if __name__ == "__main__": main()
