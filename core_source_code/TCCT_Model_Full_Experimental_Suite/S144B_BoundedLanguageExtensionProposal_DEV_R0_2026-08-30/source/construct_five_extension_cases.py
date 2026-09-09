from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S143B_RUNNER = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30" / "source" / "run_python_behavioral_induction.py"
S144A_ROOT = WORK / "S144A_GrammarInsufficiencyDetection_DEV_R0_2026-08-30"
spec = importlib.util.spec_from_file_location("s143b_for_s144b_constructor", S143B_RUNNER)
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


def var(name: str) -> dict[str, Any]:
    return {"Op": "Var", "Name": name}


def relation(name: str, left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    args = [left, right]
    if name == "Equal":
        args = sorted(args, key=canonical)
    return {"Op": "Relation", "Name": name, "Args": args}


def target_basis_atoms() -> list[dict[str, Any]]:
    current, other, decision = (var(name) for name in
        ("CurrentPartition", "OtherPartition", "DecisionPartition"))
    meet = {"Op": "PartitionMeet", "Args": sorted([current, other], key=canonical)}
    return [
        relation("PartitionRefines", meet, decision),
        relation("PartitionRefines", other, decision),
        relation("Equal", current, decision),
    ]


def target_bit(table: int, values: list[bool]) -> bool:
    signature = sum((1 << index) for index, value in enumerate(values) if value)
    return bool((table >> signature) & 1)


def parity_table() -> int:
    return sum((bin(signature).count("1") % 2) << signature for signature in range(8))


def majority_table() -> int:
    return sum((bin(signature).count("1") >= 2) << signature for signature in range(8))


def exact_old_candidates(grammar: list[dict[str, Any]], rows: list[dict[str, Any]],
                         labels: dict[str, bool]) -> list[int]:
    exact = []
    for index, candidate in enumerate(grammar):
        if all(b.candidate_value(candidate, row) == labels[row["ApplicationID"]] for row in rows):
            exact.append(index)
    return exact


def permute_partition(partition: list[list[str]], mapping: dict[str, str]) -> list[list[str]]:
    return [[mapping[item] for item in block] for block in partition]


def main() -> int:
    protocol = load(ROOT / "protocol" / "development_protocol.json")
    pool = load(S144A_ROOT / "input" / "reference_semantic_domain.json")["Applications"]
    old_grammar = b.grammar()
    atom_map = {canonical(literal["Atom"]): literal["Atom"]
                for candidate in old_grammar for literal in candidate["Literals"]}
    atom_vectors: dict[str, tuple[bool, ...]] = {
        key: tuple(b.atom_value(atom, row) for row in pool) for key, atom in atom_map.items()
    }
    semantic_representatives: dict[tuple[bool, ...], str] = {}
    for key in sorted(atom_vectors):
        semantic_representatives.setdefault(atom_vectors[key], key)

    required_keys = [canonical(atom) for atom in target_basis_atoms()]
    if any(key not in atom_map for key in required_keys):
        raise RuntimeError("required learner-visible relation atom missing from frozen bank")
    distractors = [key for key in semantic_representatives.values() if key not in required_keys]
    distractors.sort(key=lambda key: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|BANK|{key}".encode()).hexdigest())
    bank_keys = required_keys + distractors[:protocol["FrozenObservableBankSize"] - len(required_keys)]
    bank_keys.sort(key=lambda key: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|ANON|{key}".encode()).hexdigest())
    signal_ids = [f"SIG{index:02d}" for index in range(len(bank_keys))]
    key_to_signal = dict(zip(bank_keys, signal_ids, strict=True))
    signal_atoms = [atom_map[key] for key in bank_keys]

    domain_rows = []
    for index, raw in enumerate(pool):
        domain_rows.append({
            "ApplicationID": raw["ApplicationID"],
            "FormationTaskID": f"FORM_{index % 3}",
            "CurrentPartition": raw["CurrentPartition"],
            "OtherPartition": raw["OtherPartition"],
            "DecisionPartition": raw["DecisionPartition"],
            "SignalValues": [b.atom_value(atom, raw) for atom in signal_atoms],
        })
    row_by_id = {row["ApplicationID"]: row for row in domain_rows}
    required_signal_ids = [key_to_signal[key] for key in required_keys]
    required_indices = [signal_ids.index(signal_id) for signal_id in required_signal_ids]

    def labels_for(indices: tuple[int, int, int] | list[int], table: int,
                   rows: list[dict[str, Any]]) -> dict[str, bool]:
        return {row["ApplicationID"]: target_bit(table, [row["SignalValues"][i] for i in indices])
                for row in rows}

    case0_indices = tuple(required_indices)
    case0_table = parity_table()
    case0_labels = labels_for(case0_indices, case0_table, domain_rows)

    # The independent difficulty constructor chooses the first hashed triple whose majority behavior
    # is outside the current grammar. The learner never receives this hidden triple or the word majority.
    majority_candidates = list(itertools.combinations(range(len(signal_ids)), 3))
    majority_candidates.sort(key=lambda triple: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|MAJORITY|{triple}".encode()).hexdigest())
    case1_indices = None
    case1_labels = None
    for triple in majority_candidates:
        if set(triple) == set(case0_indices):
            continue
        labels = labels_for(triple, majority_table(), domain_rows)
        if len(set(labels.values())) == 2 and not exact_old_candidates(old_grammar, domain_rows, labels):
            case1_indices, case1_labels = triple, labels
            break
    if case1_indices is None or case1_labels is None:
        raise RuntimeError("could not materialize the second representation-required family")

    # Ambiguity is created by withholding one entire learner-visible signature, not by canonical order.
    signature_groups: dict[int, list[dict[str, Any]]] = {}
    for row in domain_rows:
        signature = sum((1 << bit) for bit, index in enumerate(case0_indices)
                        if row["SignalValues"][index])
        signature_groups.setdefault(signature, []).append(row)
    case2_rows = None
    withheld_signature = None
    for signature in sorted(signature_groups, key=lambda value: hashlib.sha256(
            f"{protocol['ConstructorSeed']}|WITHHOLD|{value}".encode()).hexdigest()):
        candidate_rows = [row for row in domain_rows if row not in signature_groups[signature]]
        candidate_labels = {row["ApplicationID"]: case0_labels[row["ApplicationID"]]
                            for row in candidate_rows}
        if not exact_old_candidates(old_grammar, candidate_rows, candidate_labels):
            case2_rows, withheld_signature = candidate_rows, signature
            break
    if case2_rows is None:
        raise RuntimeError("could not materialize an ambiguity case outside the current grammar")
    case2_labels = {row["ApplicationID"]: case0_labels[row["ApplicationID"]] for row in case2_rows}

    # One deterministic raw application is flipped. No exception key or raw ID is available to the meta-language.
    flip_row = min(domain_rows, key=lambda row: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|NEAR|{row['ApplicationID']}".encode()).hexdigest())
    case3_labels = dict(case0_labels)
    case3_labels[flip_row["ApplicationID"]] = not case3_labels[flip_row["ApplicationID"]]

    random_rows = sorted(domain_rows, key=lambda row: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|RANDOM_ROW|{row['ApplicationID']}".encode()).hexdigest())[:512]
    case4_labels = {row["ApplicationID"]: int(hashlib.sha256(
        f"{protocol['ConstructorSeed']}|RANDOM_LABEL|{row['ApplicationID']}".encode()).hexdigest(), 16) % 2 == 0
        for row in random_rows}

    case_specs = [
        ("S144B_CASE_00", domain_rows, case0_labels),
        ("S144B_CASE_01", domain_rows, case1_labels),
        ("S144B_CASE_02", case2_rows, case2_labels),
        ("S144B_CASE_03", domain_rows, case3_labels),
        ("S144B_CASE_04", random_rows, case4_labels),
    ]
    cases = [{"CaseID": case_id, "Observations": [
        {"ApplicationID": row["ApplicationID"], "Output": labels[row["ApplicationID"]]}
        for row in rows]} for case_id, rows, labels in case_specs]

    # Sealed reuse tests use new application IDs and two independent element relabelings.
    holdout_source = sorted(domain_rows, key=lambda row: hashlib.sha256(
        f"{protocol['ConstructorSeed']}|HOLDOUT|{row['ApplicationID']}".encode()).hexdigest())[:512]
    permutations = [
        {"0": "2", "1": "0", "2": "3", "3": "1"},
        {"0": "1", "1": "3", "2": "0", "3": "2"},
    ]
    holdouts = []
    for case_index, (indices, table) in enumerate(((case0_indices, case0_table),
                                                    (case1_indices, majority_table()))):
        mapping = permutations[case_index]
        apps = []
        for index, source in enumerate(holdout_source):
            raw = {
                "ApplicationID": f"S144B_H{case_index}_{index:04d}",
                "HoldoutTaskID": f"HOLDOUT_{case_index}_{index % 2}",
                "CurrentPartition": permute_partition(source["CurrentPartition"], mapping),
                "OtherPartition": permute_partition(source["OtherPartition"], mapping),
                "DecisionPartition": permute_partition(source["DecisionPartition"], mapping),
            }
            raw["SignalValues"] = [b.atom_value(atom, raw) for atom in signal_atoms]
            raw["Output"] = target_bit(table, [raw["SignalValues"][i] for i in indices])
            apps.append(raw)
        holdouts.append({"CaseID": f"S144B_CASE_0{case_index}", "Applications": apps})

    old_exact_counts = []
    for _, rows, labels in case_specs:
        old_exact_counts.append(len(exact_old_candidates(old_grammar, rows, labels)))
    checks = {
        "CurrentGrammarCandidateCountFrozen": len(old_grammar) == protocol["FrozenCurrentGrammarCandidateCount"],
        "TwelveAnonymousSignals": len(signal_ids) == protocol["FrozenObservableBankSize"],
        "SignalsHaveUniqueFullDomainSemantics": len({atom_vectors[key] for key in bank_keys}) == len(bank_keys),
        "AllFiveCasesOutsideCurrentGrammar": old_exact_counts == [0, 0, 0, 0, 0],
        "TwoStructuredFamiliesDiffer": case0_labels != case1_labels,
        "AmbiguityWithholdsNonemptySignature": withheld_signature is not None
            and len(signature_groups[withheld_signature]) > 0,
        "NearLawHasExactlyOneRawException": sum(case0_labels[key] != case3_labels[key]
            for key in case0_labels) == 1,
        "RandomControlHasBothLabels": len(set(case4_labels.values())) == 2,
        "NoTargetNamesInLearnerSignalIDs": all(token not in canonical(signal_ids).lower()
            for token in ("xor", "majority", "parity", "meet", "refine")),
        "CoreUnchanged": True,
    }
    dump("input/learner_signal_domain.json", {"SignalIDs": signal_ids, "Rows": domain_rows})
    dump("input/five_extension_cases.json", {"Cases": cases})
    dump("input/sealed_relabeling_holdouts.json", {"Holdouts": holdouts})
    dump("audit/constructor_private_audit.json", {
        "SignalDefinitions": dict(zip(signal_ids, signal_atoms, strict=True)),
        "StructuredCaseHiddenSignalIDs": {
            "S144B_CASE_00": [signal_ids[i] for i in case0_indices],
            "S144B_CASE_01": [signal_ids[i] for i in case1_indices],
        },
        "StructuredCaseHiddenTruthTables": {
            "S144B_CASE_00": case0_table,
            "S144B_CASE_01": majority_table(),
        },
        "AmbiguousWithheldSignature": withheld_signature,
        "NearLawFlippedApplicationID": flip_row["ApplicationID"],
        "OldGrammarExactCandidateCounts": old_exact_counts,
        "Checks": checks,
        "ConstructorPass": all(checks.values()),
    })
    print(json.dumps({"Pass": all(checks.values()), "Cases": len(cases),
                      "SignalCount": len(signal_ids), "ObservationCounts": [len(c["Observations"]) for c in cases],
                      "OldExactCounts": old_exact_counts, "WithheldSignature": withheld_signature},
                     separators=(",", ":")))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
