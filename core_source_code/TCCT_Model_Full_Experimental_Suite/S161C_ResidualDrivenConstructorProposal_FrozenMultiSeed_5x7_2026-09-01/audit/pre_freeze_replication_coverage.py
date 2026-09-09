from __future__ import annotations

import importlib.util
import itertools
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
S160 = ROOT / "work/S160A_AdaptiveDepthGrammarConstructorBootstrapping_DEV_5Cases_2026-08-31/source"
S161 = ROOT / "work/S161A_ResidualDrivenConstructorProposal_DEV_7Cases_2026-09-01/source"
sys.path[:0] = [str(S161), str(S160)]
from constructor_bootstrap_engine import CARRIER  # noqa: E402
from run_s160a_python import canonical_orbit_key  # noqa: E402

S161B_RUNNER = ROOT / "work/S161B_ResidualDrivenConstructorProposal_FrozenFresh_7Cases_2026-09-01/source/run_s161b_python.py"
spec = importlib.util.spec_from_file_location("s161b_frozen_runner", S161B_RUNNER)
s161b = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(s161b)


def load(path): return json.loads(path.read_text(encoding="utf-8"))


def historical_keys():
    protocol = load(ROOT / "work/S161B_ResidualDrivenConstructorProposal_FrozenFresh_7Cases_2026-09-01/protocol/frozen_protocol.json")
    history = set(s161b.historical_keys(protocol))
    holdout = load(ROOT / "work/S161B_ResidualDrivenConstructorProposal_FrozenFresh_7Cases_2026-09-01/oracle/sealed_exact_holdout.json")
    history.add(canonical_orbit_key(tuple(holdout["BaseAtoms"]["A"]), tuple(holdout["BaseAtoms"]["B"])))
    return history


def main():
    history = historical_keys()
    permutations = [tuple(p) for p in itertools.permutations(CARRIER) if tuple(p) != tuple(CARRIER)]
    remaining = sorted({canonical_orbit_key(a, b) for a in permutations for b in permutations
                        if a != b and canonical_orbit_key(a, b) not in history})
    qualified = []
    for key in remaining:
        analysis = s161b.analyze({"A": key[0], "B": key[1]})
        if all(analysis[i] for i in (3, 4, 5, 6, 7)):
            qualified.append((key, analysis))
    out = {
        "AuditType": "READ_ONLY_PRE_FREEZE_S161C_MULTI_SEED_COVERAGE",
        "HistoricalOrbitCountExcluded": len(history),
        "RemainingUnseenOrbitCount": len(remaining),
        "QualifyingFreshSevenCaseOrbitCount": len(qualified),
        "RequiredCohortCount": 5,
        "FiveDistinctCohortsFeasible": len(qualified) >= 5,
        "CurrentGrammarSemanticCountRange": [min(len(a[1][0]) for a in qualified), max(len(a[1][0]) for a in qualified)] if qualified else [],
        "RuntimeConstructorCountRange": [min(len(a[1][1]) for a in qualified), max(len(a[1][1]) for a in qualified)] if qualified else [],
        "ExplanationEntryCountRange": [min(len(a[1][2]) for a in qualified), max(len(a[1][2]) for a in qualified)] if qualified else [],
        "FutureSeedsMaterialized": False,
        "AuditDidNotSelectWorldsOrTasks": True,
    }
    output = Path(__file__).with_name("replication_coverage_summary.json")
    output.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if not out["FiveDistinctCohortsFeasible"]:
        raise SystemExit(1)


if __name__ == "__main__": main()
