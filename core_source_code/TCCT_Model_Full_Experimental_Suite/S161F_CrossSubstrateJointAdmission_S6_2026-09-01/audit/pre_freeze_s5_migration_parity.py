from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SRC = Path(__file__).resolve().parents[1] / "source"
sys.path.insert(0, str(SRC))
from generic_joint_admission_engine import compose, joint_residual_propose  # noqa: E402


def load(path): return json.loads(path.read_text(encoding="utf-8"))


def main():
    stage = ROOT / "work/S161E_JointResidualAdmission_FrozenFresh_2026-09-01"
    truth = load(stage / "oracle/sealed_exact_holdout.json")
    old = load(stage / "results/python_fresh_result.json")
    base = {name: tuple(atom) for name, atom in truth["BaseAtoms"].items()}; carrier = tuple(range(5))
    inputs = {
        "NO_EXTENSION": (tuple(truth["NoExtensionTarget"]), carrier, 5),
        "UNIQUE": (tuple(truth["UniqueTarget"]), tuple(truth["UniqueInputs"]), 5),
        "JOINT_ACTIVE": (tuple(truth["JointActiveTarget"]), tuple(truth["JointActiveInputs"]), 5),
        "AMBIGUOUS": (tuple(truth["AmbiguousTarget"]), carrier, 5),
        "INSUFFICIENT": (tuple(truth["InsufficientTarget"]), carrier, 5),
    }
    comparisons = {}
    for case_id, arguments in inputs.items():
        new = joint_residual_propose(base, *arguments, carrier)
        previous = next(row for row in old["Rows"] if row["CaseID"] == case_id)
        comparisons[case_id] = all((new["Status"] == previous["Status"],
                                    new["ProposedConstructor"] == previous["ProposedConstructor"],
                                    new["Queries"] == previous["Queries"],
                                    new["InitialJointDecisionClassCount"] == previous["InitialJointDecisionClassCount"],
                                    new["FinalJointDecisionClassCount"] == previous["FinalJointDecisionClassCount"]))
    causal = next(row for row in old["Rows"] if row["CaseID"] == "CURRENT_COMPATIBLE_CAUSAL")
    reduced = tuple(x for x in truth["CausalInputs"] if x != truth["CausalRemovedInput"])
    new_full = joint_residual_propose(base, tuple(truth["CausalTarget"]), tuple(truth["CausalInputs"]), 0, carrier)
    new_reduced = joint_residual_propose(base, tuple(truth["CausalTarget"]), reduced, 0, carrier)
    comparisons["CAUSAL_FULL"] = new_full["Status"] == causal["Full"]["Status"]
    comparisons["CAUSAL_REDUCED"] = new_reduced["Status"] == causal["Reduced"]["Status"]
    pi = tuple(truth["RelabelPermutation"]); inv = [0] * len(pi)
    for i, v in enumerate(pi): inv[v] = i
    conjugate = lambda semantics: compose(pi, compose(semantics, tuple(inv)))
    relbase = {name: conjugate(atom) for name, atom in base.items()}
    reltarget = conjugate(tuple(truth["UniqueTarget"])); relinputs = tuple(pi[x] for x in truth["UniqueInputs"])
    new_rel = joint_residual_propose(relbase, reltarget, relinputs, 5, carrier)
    old_rel = next(row for row in old["Rows"] if row["CaseID"] == "RELABEL")
    comparisons["RELABEL"] = (new_rel["Status"] == old_rel["Status"] and
                               new_rel["ProposedConstructor"] == old_rel["ProposedConstructor"])
    out = {"AuditType": "PRE_FREEZE_S5_GENERIC_ENGINE_MIGRATION_PARITY",
           "Comparisons": comparisons, "AllTrajectoriesParity": all(comparisons.values()),
           "S6FutureSeedsMaterialized": False}
    output = Path(__file__).with_name("s5_migration_parity.json")
    output.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps(out, sort_keys=True))
    if not out["AllTrajectoriesParity"]: raise SystemExit(1)


if __name__ == "__main__": main()
