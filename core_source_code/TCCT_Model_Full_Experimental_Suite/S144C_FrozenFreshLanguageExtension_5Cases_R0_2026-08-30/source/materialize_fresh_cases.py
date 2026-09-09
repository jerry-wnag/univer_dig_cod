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
S144B_ROOT = WORK / "S144B_BoundedLanguageExtensionProposal_DEV_R0_2026-08-30"
S144B_RUNNER = S144B_ROOT / "source" / "run_python_language_extension.py"
S143B_RUNNER = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30" / "source" / "run_python_behavioral_induction.py"
S144A_ROOT = WORK / "S144A_GrammarInsufficiencyDetection_DEV_R0_2026-08-30"


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ext = module_from(S144B_RUNNER, "s144b_frozen_for_s144c_constructor")
b = module_from(S143B_RUNNER, "s143b_frozen_for_s144c_constructor")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def target_bit(table: int, values: list[bool]) -> bool:
    sig = sum((1 << index) for index, value in enumerate(values) if value)
    return bool((table >> sig) & 1)


def exact_old_count(grammar: list[dict[str, Any]], rows: list[dict[str, Any]],
                    labels: dict[str, bool]) -> int:
    return sum(all(b.candidate_value(candidate, row) == labels[row["ApplicationID"]]
                   for row in rows) for candidate in grammar)


def permute_partition(partition: list[list[str]], mapping: dict[str, str]) -> list[list[str]]:
    return [[mapping[item] for item in block] for block in partition]


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    seed = protocol["Freshness"]["Seed"]
    pool = load(S144A_ROOT / "input" / "reference_semantic_domain.json")["Applications"]
    old_grammar = b.grammar()
    old_private = load(S144B_ROOT / "audit" / "constructor_private_audit.json")
    excluded_tables = set(old_private["StructuredCaseHiddenTruthTables"].values())
    programs = ext.nand_library(protocol["FrozenMechanism"]["MaximumNANDFormulaCost"])

    atom_map = {canonical(literal["Atom"]): literal["Atom"]
                for candidate in old_grammar for literal in candidate["Literals"]}
    vectors = {key: tuple(b.atom_value(atom, row) for row in pool) for key, atom in atom_map.items()}
    representatives: dict[tuple[bool, ...], str] = {}
    for key in sorted(vectors):
        representatives.setdefault(vectors[key], key)
    bank_keys = list(representatives.values())
    bank_keys.sort(key=lambda key: hashlib.sha256(f"{seed}|BANK|{key}".encode()).hexdigest())
    bank_keys = bank_keys[:protocol["FrozenMechanism"]["ObservableBankSize"]]
    bank_keys.sort(key=lambda key: hashlib.sha256(f"{seed}|ANON|{key}".encode()).hexdigest())
    signal_ids = [f"FSIG{index:02d}" for index in range(len(bank_keys))]
    signal_atoms = [atom_map[key] for key in bank_keys]
    domain_rows = [{
        "ApplicationID": raw["ApplicationID"],
        "FormationTaskID": f"FRESH_FORM_{index % 4}",
        "CurrentPartition": raw["CurrentPartition"],
        "OtherPartition": raw["OtherPartition"],
        "DecisionPartition": raw["DecisionPartition"],
        "SignalValues": [b.atom_value(atom, raw) for atom in signal_atoms],
    } for index, raw in enumerate(pool)]

    def labels_for(triple: tuple[int, int, int], table: int,
                   rows: list[dict[str, Any]]) -> dict[str, bool]:
        return {row["ApplicationID"]: target_bit(table,
            [row["SignalValues"][index] for index in triple]) for row in rows}

    # A frozen hashed search implements only the pre-registered difficulty contract.
    # It does not optimize learner outcome or replace a materialized failure.
    tables = [table for table, record in programs.items()
              if 4 <= record["NANDCount"] <= 11 and table not in excluded_tables
              and table not in (0, 255)]
    pairs = list(itertools.product(itertools.combinations(range(len(signal_ids)), 3), tables))
    pairs.sort(key=lambda pair: hashlib.sha256(f"{seed}|PAIR|{pair}".encode()).hexdigest())
    structured = []
    used_vectors = set()
    for triple, table in pairs:
        labels = labels_for(triple, table, domain_rows)
        vector_hash = hashlib.sha256(bytes(labels[row["ApplicationID"]] for row in domain_rows)).hexdigest()
        if vector_hash in used_vectors or len(set(labels.values())) < 2:
            continue
        if exact_old_count(old_grammar, domain_rows, labels) != 0:
            continue
        structured.append({"Triple": triple, "TruthTable": table, "Labels": labels,
                           "SemanticSHA256": vector_hash, "NANDCount": programs[table]["NANDCount"]})
        used_vectors.add(vector_hash)
        if len(structured) == 4:
            break
    if len(structured) != 4:
        raise RuntimeError("frozen difficulty constructor could not materialize four structured families")

    official = []
    for index in range(3):
        item = structured[index]
        official.append({"CaseID": f"S144C_CASE_0{index}", "Observations": [
            {"ApplicationID": row["ApplicationID"], "Output": item["Labels"][row["ApplicationID"]]}
            for row in domain_rows]})

    ambiguous_source = structured[3]
    signature_groups: dict[int, list[dict[str, Any]]] = {}
    for row in domain_rows:
        sig = ext.signature(row["SignalValues"], ambiguous_source["Triple"])
        signature_groups.setdefault(sig, []).append(row)
    ambiguous_rows = None
    withheld_signature = None
    for sig in sorted(signature_groups, key=lambda value: hashlib.sha256(
            f"{seed}|WITHHOLD|{value}".encode()).hexdigest()):
        rows = [row for row in domain_rows if row not in signature_groups[sig]]
        labels = {row["ApplicationID"]: ambiguous_source["Labels"][row["ApplicationID"]] for row in rows}
        if exact_old_count(old_grammar, rows, labels) == 0:
            ambiguous_rows, withheld_signature = rows, sig
            break
    if ambiguous_rows is None:
        raise RuntimeError("frozen ambiguity constructor could not satisfy the current-grammar exclusion")
    official.append({"CaseID": "S144C_CASE_03", "Observations": [
        {"ApplicationID": row["ApplicationID"],
         "Output": ambiguous_source["Labels"][row["ApplicationID"]]} for row in ambiguous_rows]})

    near_source = structured[0]
    flip_row = min(domain_rows, key=lambda row: hashlib.sha256(
        f"{seed}|NEAR|{row['ApplicationID']}".encode()).hexdigest())
    near_labels = dict(near_source["Labels"])
    near_labels[flip_row["ApplicationID"]] = not near_labels[flip_row["ApplicationID"]]
    official.append({"CaseID": "S144C_CASE_04", "Observations": [
        {"ApplicationID": row["ApplicationID"], "Output": near_labels[row["ApplicationID"]]}
        for row in domain_rows]})

    random_rows = sorted(domain_rows, key=lambda row: hashlib.sha256(
        f"{seed}|RANDOM_ROW|{row['ApplicationID']}".encode()).hexdigest())[:512]
    random_observations = [{"ApplicationID": row["ApplicationID"],
        "Output": int(hashlib.sha256(f"{seed}|RANDOM_LABEL|{row['ApplicationID']}".encode()).hexdigest(), 16) % 2 == 0}
        for row in random_rows]

    holdout_source = sorted(domain_rows, key=lambda row: hashlib.sha256(
        f"{seed}|HOLDOUT|{row['ApplicationID']}".encode()).hexdigest())[:384]
    permutations = [
        {"0": "3", "1": "1", "2": "0", "3": "2"},
        {"0": "2", "1": "3", "2": "1", "3": "0"},
        {"0": "1", "1": "0", "2": "3", "3": "2"},
    ]
    holdouts = []
    for case_index, item in enumerate(structured[:3]):
        apps = []
        for index, source in enumerate(holdout_source):
            mapping = permutations[case_index]
            app = {
                "ApplicationID": f"S144C_H{case_index}_{index:04d}",
                "HoldoutTaskID": f"FRESH_HOLDOUT_{case_index}_{index % 3}",
                "CurrentPartition": permute_partition(source["CurrentPartition"], mapping),
                "OtherPartition": permute_partition(source["OtherPartition"], mapping),
                "DecisionPartition": permute_partition(source["DecisionPartition"], mapping),
            }
            app["SignalValues"] = [b.atom_value(atom, app) for atom in signal_atoms]
            app["Output"] = target_bit(item["TruthTable"],
                [app["SignalValues"][signal] for signal in item["Triple"]])
            apps.append(app)
        holdouts.append({"CaseID": f"S144C_CASE_0{case_index}", "Applications": apps})

    official_old_exact = []
    for case in official:
        labels = {obs["ApplicationID"]: obs["Output"] for obs in case["Observations"]}
        rows = [next(row for row in domain_rows if row["ApplicationID"] == obs["ApplicationID"])
                for obs in case["Observations"]]
        official_old_exact.append(exact_old_count(old_grammar, rows, labels))
    random_labels = {obs["ApplicationID"]: obs["Output"] for obs in random_observations}
    random_old_exact = exact_old_count(old_grammar, random_rows, random_labels)
    checks = {
        "SeedFrozen": protocol["Freshness"]["SeedFrozenBeforeMaterialization"],
        "FiveCasesMaterializedOnce": len(official) == 5,
        "FreshBankHasTwelveUniqueSemanticSignals": len(bank_keys) == 12
            and len({vectors[key] for key in bank_keys}) == 12,
        "ThreePositiveTruthTablesExcludedFromS144B": all(item["TruthTable"] not in excluded_tables
            for item in structured[:3]),
        "FourStructuredSemanticFamiliesDistinct": len({item["SemanticSHA256"] for item in structured}) == 4,
        "AllOfficialCasesOutsideCurrentGrammar": official_old_exact == [0, 0, 0, 0, 0],
        "AuxiliaryRandomOutsideCurrentGrammar": random_old_exact == 0,
        "NearLawExactlyOneException": sum(near_labels[key] != near_source["Labels"][key]
            for key in near_labels) == 1,
        "CoreUnchanged": True,
    }
    dump("input/fresh_learner_signal_domain.json", {"SignalIDs": signal_ids, "Rows": domain_rows})
    dump("input/five_fresh_cases.json", {"Cases": official})
    dump("input/auxiliary_random_control.json", {"Observations": random_observations})
    dump("oracle/sealed_fresh_relabeling_holdouts.json", {"Holdouts": holdouts})
    dump("audit/private_fresh_constructor_audit.json", {
        "SignalDefinitions": dict(zip(signal_ids, signal_atoms, strict=True)),
        "StructuredFamilies": [{key: value for key, value in item.items() if key != "Labels"}
                               for item in structured],
        "AmbiguousWithheldSignature": withheld_signature,
        "NearLawFlippedApplicationID": flip_row["ApplicationID"],
        "OfficialCurrentGrammarExactCounts": official_old_exact,
        "AuxiliaryRandomCurrentGrammarExactCount": random_old_exact,
        "Checks": checks, "ConstructorPass": all(checks.values()),
    })
    print(json.dumps({"Pass": all(checks.values()), "StatusesExpected": protocol["ExpectedStatuses"],
                      "ObservationCounts": [len(case["Observations"]) for case in official],
                      "StructuredNANDCosts": [item["NANDCount"] for item in structured],
                      "OldExact": official_old_exact, "RandomOldExact": random_old_exact}, separators=(",", ":")))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
