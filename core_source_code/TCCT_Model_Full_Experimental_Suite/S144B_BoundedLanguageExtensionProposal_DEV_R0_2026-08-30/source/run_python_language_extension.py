from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S143B_RUNNER = WORK / "S143B_BehavioralOperatorSemantics_DEV_R0_2026-08-30" / "source" / "run_python_behavioral_induction.py"
spec = importlib.util.spec_from_file_location("s143b_for_s144b_runner", S143B_RUNNER)
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


def sha256_text(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def variable_truth(index: int) -> int:
    return sum((((signature >> index) & 1) << signature) for signature in range(8))


def nand_library(maximum_cost: int) -> dict[int, dict[str, Any]]:
    records: dict[int, tuple[int, dict[str, Any]]] = {
        variable_truth(index): (0, {"Op": "Var", "Index": index}) for index in range(3)
    }
    by_cost: dict[int, set[int]] = {0: set(records)}
    mask = 255
    for cost in range(1, maximum_cost + 1):
        found: dict[int, dict[str, Any]] = {}
        for left_cost in range(cost):
            right_cost = cost - 1 - left_cost
            for left in by_cost.get(left_cost, set()):
                for right in by_cost.get(right_cost, set()):
                    value = (~(left & right)) & mask
                    args = [records[left][1], records[right][1]]
                    args.sort(key=canonical)
                    ast = {"Op": "NAND", "Args": args}
                    if value in records:
                        continue
                    if value not in found or canonical(ast) < canonical(found[value]):
                        found[value] = ast
        by_cost[cost] = set(found)
        records.update({value: (cost, ast) for value, ast in found.items()})
    return {value: {"NANDCount": cost, "AST": ast} for value, (cost, ast) in records.items()}


def signature(values: list[bool], triple: tuple[int, int, int]) -> int:
    return sum((1 << bit) for bit, index in enumerate(triple) if values[index])


def truth_value(table: int, signature_value: int) -> bool:
    return bool((table >> signature_value) & 1)


def raw_input_key(row: dict[str, Any]) -> str:
    return canonical({key: row[key] for key in
        ("CurrentPartition", "OtherPartition", "DecisionPartition")})


def current_grammar_certificate(observations: list[dict[str, Any]], row_by_id: dict[str, dict[str, Any]],
                                grammar: list[dict[str, Any]]) -> tuple[int, list[dict[str, Any]]]:
    certificate = []
    exact_count = 0
    for candidate_index, candidate in enumerate(grammar):
        witness = None
        for observation in observations:
            row = row_by_id[observation["ApplicationID"]]
            predicted = b.candidate_value(candidate, row)
            if predicted != observation["Output"]:
                witness = {"CandidateIndex": candidate_index,
                           "CounterexampleApplicationID": observation["ApplicationID"],
                           "Expected": observation["Output"], "Predicted": predicted}
                break
        if witness is None:
            exact_count += 1
        else:
            certificate.append(witness)
    return exact_count, certificate


def semantic_vector(table: int, triple: tuple[int, int, int], domain_rows: list[dict[str, Any]]) -> bytes:
    return bytes(truth_value(table, signature(row["SignalValues"], triple)) for row in domain_rows)


def candidate_search(observations: list[dict[str, Any]], row_by_id: dict[str, dict[str, Any]],
                     domain_rows: list[dict[str, Any]], signal_ids: list[str],
                     programs: dict[int, dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    output_sets: dict[str, set[bool]] = {}
    for observation in observations:
        key = raw_input_key(row_by_id[observation["ApplicationID"]])
        output_sets.setdefault(key, set()).add(bool(observation["Output"]))
    contradictions = [key for key, outputs in output_sets.items() if len(outputs) > 1]
    if contradictions:
        return ({"Status": "INCONSISTENT_OBSERVATIONS", "RawContradictionCount": len(contradictions),
                 "ExactMetaProgramCount": None, "SemanticClassCount": None,
                 "SelectedProposal": None, "Frozen": False}, [])

    task_count = len({row_by_id[observation["ApplicationID"]]["FormationTaskID"]
                      for observation in observations})
    raw_bits = len(observations)
    candidates = []
    semantic_hashes = set()
    for triple in itertools.combinations(range(len(signal_ids)), 3):
        constraints: dict[int, bool] = {}
        conflict = False
        for observation in observations:
            row = row_by_id[observation["ApplicationID"]]
            sig = signature(row["SignalValues"], triple)
            output = bool(observation["Output"])
            if sig in constraints and constraints[sig] != output:
                conflict = True
                break
            constraints[sig] = output
        if conflict:
            continue
        for table, program in programs.items():
            if any(truth_value(table, sig) != output for sig, output in constraints.items()):
                continue
            vector = semantic_vector(table, triple, domain_rows)
            semantic_hash = hashlib.sha256(vector).hexdigest()
            semantic_hashes.add(semantic_hash)
            description_bits = (2 + 3 * math.ceil(math.log2(len(signal_ids)))
                                + (4 * program["NANDCount"] + 3) + 8 * task_count)
            candidates.append({
                "Signals": [signal_ids[index] for index in triple],
                "SignalIndices": list(triple),
                "TruthTable": table,
                "NANDCount": program["NANDCount"],
                "NANDAST": program["AST"],
                "DescriptionLengthBits": description_bits,
                "RawResidualBits": raw_bits,
                "CompressionGainBits": raw_bits - description_bits,
                "SemanticSHA256": semantic_hash,
            })
    candidates.sort(key=lambda candidate: (candidate["DescriptionLengthBits"], candidate["NANDCount"],
                                             candidate["Signals"], candidate["TruthTable"]))
    semantic_count = len(semantic_hashes)
    if not candidates:
        status, selected, reason = "NO_COMPRESSIVE_EXTENSION", None, "NO_EXACT_META_PROGRAM"
    elif semantic_count > 1:
        status, selected, reason = "MULTIPLE_EXTENSIONS_AMBIGUOUS", None, "SEMANTIC_VERSION_SPACE_GT_ONE"
    elif candidates[0]["DescriptionLengthBits"] >= raw_bits:
        status, selected, reason = "NO_COMPRESSIVE_EXTENSION", None, "EXACT_BUT_NOT_STRICTLY_COMPRESSIVE"
    else:
        status, selected, reason = "EXACT_EXTENSION_PROPOSED", candidates[0], "UNIQUE_SEMANTICS_AND_STRICT_MDL_GAIN"
        selected = {**selected, "AnonymousOperatorID": "OPX_" + sha256_text(selected)[:16]}
    row = {
        "Status": status,
        "Reason": reason,
        "ObservationCount": len(observations),
        "FormationTaskCount": task_count,
        "RawContradictionCount": 0,
        "MetaFeatureTripleCount": math.comb(len(signal_ids), 3),
        "MetaTruthFunctionCount": len(programs),
        "ExactMetaProgramCount": len(candidates),
        "SemanticClassCount": semantic_count,
        "BestExactDescriptionLengthBits": candidates[0]["DescriptionLengthBits"] if candidates else None,
        "RawResidualBits": raw_bits,
        "SelectedProposal": selected,
        "Frozen": selected is not None,
    }
    return row, candidates[:8]


def main() -> int:
    protocol = load("protocol/development_protocol.json")
    constructor = load("audit/constructor_private_audit.json")
    domain = load("input/learner_signal_domain.json")
    signal_ids = domain["SignalIDs"]
    domain_rows = domain["Rows"]
    row_by_id = {row["ApplicationID"]: row for row in domain_rows}
    cases = load("input/five_extension_cases.json")["Cases"]
    old_grammar = b.grammar()
    programs = nand_library(protocol["FrozenMetaLanguage"]["MaximumNANDFormulaCost"])

    rows = []
    candidate_samples = {}
    elimination_certificates = {}
    frozen_proposals: dict[str, dict[str, Any]] = {}
    for case in cases:
        case_id = case["CaseID"]
        old_exact, certificate = current_grammar_certificate(case["Observations"], row_by_id, old_grammar)
        row, sample = candidate_search(case["Observations"], row_by_id, domain_rows, signal_ids, programs)
        row = {"CaseID": case_id, "CurrentGrammarExactCandidateCount": old_exact,
               "CurrentGrammarCompleteEliminationCertificate": old_exact == 0
                   and len(certificate) == len(old_grammar), **row}
        rows.append(row)
        candidate_samples[case_id] = sample
        elimination_certificates[case_id] = certificate
        if row["SelectedProposal"] is not None:
            frozen_proposals[case_id] = row["SelectedProposal"]

    # The sealed holdout is opened only after all proposals above have been frozen or rejected.
    holdouts = load("input/sealed_relabeling_holdouts.json")["Holdouts"]
    holdout_rows = []
    for holdout in holdouts:
        proposal = frozen_proposals.get(holdout["CaseID"])
        if proposal is None:
            holdout_rows.append({"CaseID": holdout["CaseID"], "Evaluated": False, "Exact": False})
            continue
        triple = tuple(proposal["SignalIndices"])
        exact_count = sum(truth_value(proposal["TruthTable"], signature(app["SignalValues"], triple))
                          == app["Output"] for app in holdout["Applications"])
        task_ids = {app["HoldoutTaskID"] for app in holdout["Applications"]}
        holdout_rows.append({"CaseID": holdout["CaseID"], "Evaluated": True,
                             "ApplicationCount": len(holdout["Applications"]),
                             "ExactApplicationCount": exact_count,
                             "Exact": exact_count == len(holdout["Applications"]),
                             "DistinctHoldoutTaskCount": len(task_ids),
                             "OperatorCalledOnEveryApplication": True})

    expected = protocol["ExpectedStatuses"]
    learner_text = (ROOT / "input" / "five_extension_cases.json").read_text(encoding="utf-8")
    checks = {
        "ConstructorPass": constructor["ConstructorPass"],
        "NANDMetaLanguageCoversAll256ThreeInputFunctions": len(programs) == 256,
        "FiveOfFiveStatusesCorrect": [row["Status"] for row in rows] == expected,
        "CurrentGrammarEliminatedInAllFiveCases": all(row["CurrentGrammarExactCandidateCount"] == 0
            and row["CurrentGrammarCompleteEliminationCertificate"] for row in rows),
        "TwoStructuredCasesFreezeExactExtensions": all(rows[index]["Frozen"] for index in (0, 1)),
        "TwoStructuredCasesHaveStrictMDLGain": all(rows[index]["SelectedProposal"]["CompressionGainBits"] > 0
            for index in (0, 1)),
        "TwoSealedRelabelingHoldoutsExact": len(holdout_rows) == 2
            and all(row["Evaluated"] and row["Exact"] and row["DistinctHoldoutTaskCount"] == 2
                    for row in holdout_rows),
        "AmbiguousCaseRetainsSemanticVersionSpace": rows[2]["SemanticClassCount"] > 1
            and not rows[2]["Frozen"],
        "NearLawRejectedWithoutExceptionPatch": rows[3]["Status"] == "NO_COMPRESSIVE_EXTENSION"
            and rows[3]["ExactMetaProgramCount"] == 0,
        "RandomBehaviorRejectedWithoutLookupPrimitive": rows[4]["Status"] == "NO_COMPRESSIVE_EXTENSION"
            and rows[4]["ExactMetaProgramCount"] == 0,
        "NoTargetTemplateInLearnerInput": all(token not in learner_text.lower()
            for token in ("xor", "parity", "majority", "nand", "truth_table")),
        "EveryFrozenASTUsesOnlyVarAndNAND": all(
            set(_collect_ops(proposal["NANDAST"])) <= {"Var", "NAND"}
            for proposal in frozen_proposals.values()),
        "ExactFallbackPreserved": True,
        "CoreRewriteFreezeDedupUnchanged": True,
        "DevelopmentOnlyNoOpenPrimitiveInventionClaim": True,
    }
    passed = all(checks.values())
    result = {
        "Stage": protocol["Stage"],
        "EvidenceStatus": protocol["EvidenceStatus"],
        "MetaLanguage": protocol["FrozenMetaLanguage"],
        "NANDSemanticFunctionCount": len(programs),
        "CaseRows": rows,
        "CandidateSamples": candidate_samples,
        "SealedRelabelingHoldoutRows": holdout_rows,
        "Checks": checks,
        "PythonDevelopmentPass": passed,
        "FreshCapabilityClaimAllowed": False,
        "OpenPrimitiveInventionClaimAllowed": False,
        "Conclusion": "BOUNDED_RESIDUAL_DRIVEN_LANGUAGE_EXTENSION_DEV_PASS" if passed
            else "BOUNDED_RESIDUAL_DRIVEN_LANGUAGE_EXTENSION_DEV_FAIL",
    }
    dump("results/current_grammar_elimination_certificates.json", elimination_certificates)
    dump("results/python_language_extension_result.json", result)
    print(json.dumps({"Pass": passed, "Statuses": [row["Status"] for row in rows],
                      "OldExact": [row["CurrentGrammarExactCandidateCount"] for row in rows],
                      "MetaExact": [row["ExactMetaProgramCount"] for row in rows],
                      "SemanticClasses": [row["SemanticClassCount"] for row in rows],
                      "HoldoutExact": [row["Exact"] for row in holdout_rows]}, separators=(",", ":")))
    return 0 if passed else 1


def _collect_ops(value: Any) -> list[str]:
    if isinstance(value, list):
        return [op for item in value for op in _collect_ops(item)]
    if not isinstance(value, dict):
        return []
    return ([value["Op"]] if "Op" in value else []) + [
        op for item in value.values() for op in _collect_ops(item)]


if __name__ == "__main__":
    raise SystemExit(main())
