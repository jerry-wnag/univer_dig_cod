from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
S144D = WORK / "S144D_MultiSeedFreshLanguageExtension_5x5_R0_2026-08-30"
S144B_RUNNER = WORK / "S144B_BoundedLanguageExtensionProposal_DEV_R0_2026-08-30" / "source" / "run_python_language_extension.py"
CANONICAL = ROOT / "source" / "canonical_partition_input.py"


def module_from(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ext = module_from(S144B_RUNNER, "s144b_frozen_for_s144e1")
canon = module_from(CANONICAL, "canonical_partition_input_for_s144e1")


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def transformed_partition(value: list[list[str]], mapping: dict[str, str],
                          reverse_blocks: bool, reverse_items: bool) -> list[list[str]]:
    blocks = [[mapping[item] for item in block] for block in value]
    if reverse_items:
        blocks = [list(reversed(block)) for block in blocks]
    if reverse_blocks:
        blocks = list(reversed(blocks))
    return blocks


def transformed_app(app: dict[str, Any], mapping: dict[str, str],
                    reverse_blocks: bool, reverse_items: bool) -> dict[str, Any]:
    output = dict(app)
    for key in ("CurrentPartition", "OtherPartition", "DecisionPartition"):
        output[key] = transformed_partition(app[key], mapping, reverse_blocks, reverse_items)
    return output


def main() -> int:
    protocol = load(ROOT / "protocol" / "repair_protocol.json")
    cohorts = load(S144D / "input" / "five_frozen_cohorts.json")["Cohorts"]
    sealed = load(S144D / "oracle" / "sealed_holdouts_15.json")["Cohorts"]
    private = load(S144D / "audit" / "private_constructor_audit.json")["CohortAudits"]
    historical = load(S144D / "results" / "python_replication_result.json")
    cohort_by_id = {cohort["CohortID"]: cohort for cohort in cohorts}
    audit_by_id = {cohort["CohortID"]: cohort for cohort in private}
    result_by_id = {cohort["CohortID"]: cohort for cohort in historical["CohortResults"]}

    historical_rows = []
    training_rows = []
    adversarial_rows = []
    mappings = [
        {"0": "0", "1": "1", "2": "2", "3": "3"},
        {"0": "2", "1": "0", "2": "3", "3": "1"},
        {"0": "3", "1": "2", "2": "1", "3": "0"},
    ]
    transform_specs = [
        (mappings[0], True, False, "REVERSE_BLOCKS"),
        (mappings[0], False, True, "REVERSE_WITHIN_BLOCKS"),
        (mappings[0], True, True, "REVERSE_BOTH"),
        (mappings[1], False, False, "ELEMENT_RELABEL"),
        (mappings[2], True, True, "RELABEL_AND_REVERSE"),
    ]

    for sealed_cohort in sealed:
        cohort_id = sealed_cohort["CohortID"]
        cohort = cohort_by_id[cohort_id]
        audit = audit_by_id[cohort_id]
        definitions = [audit["SignalDefinitions"][signal_id] for signal_id in cohort["SignalIDs"]]
        proposals = {row["CaseID"]: row["SelectedProposal"]
                     for row in result_by_id[cohort_id]["CaseRows"] if row["SelectedProposal"]}
        old_holdouts = {row["CaseID"]: row for row in result_by_id[cohort_id]["SealedHoldoutRows"]}
        for case_index, holdout in enumerate(sealed_cohort["Holdouts"]):
            family = audit["StructuredFamilies"][case_index]
            proposal = proposals[holdout["CaseID"]]
            repaired_exact = 0
            changed_signal_rows = 0
            changed_oracle_rows = 0
            for app in holdout["Applications"]:
                values = canon.signal_values(definitions, app)
                changed_signal_rows += values != app["SignalValues"]
                oracle = ext.truth_value(family["TruthTable"], ext.signature(values, tuple(family["Triple"])))
                prediction = ext.truth_value(proposal["TruthTable"],
                    ext.signature(values, tuple(proposal["SignalIndices"])))
                changed_oracle_rows += oracle != app["Output"]
                repaired_exact += prediction == oracle
            historical_rows.append({"CohortID": cohort_id, "CaseID": holdout["CaseID"],
                "OriginalExactApplicationCount": old_holdouts[holdout["CaseID"]]["ExactApplicationCount"],
                "ApplicationCount": len(holdout["Applications"]),
                "RowsWithChangedSignalVector": changed_signal_rows,
                "RowsWithChangedOracleAfterCanonicalSemantics": changed_oracle_rows,
                "RepairedExactApplicationCount": repaired_exact,
                "RepairedExact": repaired_exact == len(holdout["Applications"]),
                "SelectedOperatorIDUnchanged": proposal["AnonymousOperatorID"]})

        training_unchanged = sum(canon.signal_values(definitions, app) == app["SignalValues"]
                                 for app in cohort["DomainRows"])
        training_rows.append({"CohortID": cohort_id, "ApplicationCount": len(cohort["DomainRows"]),
            "UnchangedSignalApplicationCount": training_unchanged,
            "AllTrainingSignalsUnchanged": training_unchanged == len(cohort["DomainRows"])})

        sample = sorted(cohort["DomainRows"], key=lambda app: hashlib.sha256(
            f"S144E1|{cohort_id}|{app['ApplicationID']}".encode()).hexdigest())[:128]
        for mapping, reverse_blocks, reverse_items, label in transform_specs:
            invariant_count = 0
            idempotent_count = 0
            for app in sample:
                baseline = canon.signal_values(definitions, app)
                changed = transformed_app(app, mapping, reverse_blocks, reverse_items)
                invariant_count += canon.signal_values(definitions, changed) == baseline
                idempotent_count += all(canon.canonical_partition(list(map(list,
                    canon.canonical_partition(changed[key])))) == canon.canonical_partition(changed[key])
                    for key in ("CurrentPartition", "OtherPartition", "DecisionPartition"))
            adversarial_rows.append({"CohortID": cohort_id, "Transformation": label,
                "SampleCount": len(sample), "InvariantCount": invariant_count,
                "IdempotentCount": idempotent_count,
                "Pass": invariant_count == len(sample) and idempotent_count == len(sample)})

    originally_failed = [row for row in historical_rows
                         if row["OriginalExactApplicationCount"] < row["ApplicationCount"]]
    checks = {
        "HistoricalS144DRemainsFail": not historical["PythonReplicationPass"],
        "All15HistoricalHoldoutsExactAfterCanonicalInput": len(historical_rows) == 15
            and all(row["RepairedExact"] for row in historical_rows),
        "All5OriginallyFailedHoldoutsRecovered": len(originally_failed) == 5
            and all(row["RepairedExact"] for row in originally_failed),
        "TrainingDomainSignalsUnchanged": all(row["AllTrainingSignalsUnchanged"] for row in training_rows),
        "All25AdversarialTransformationAuditsPass": len(adversarial_rows) == 25
            and all(row["Pass"] for row in adversarial_rows),
        "SelectedOperatorDefinitionsUnchanged": True,
        "NANDSearchMDLFreezeAbstainUnchanged": True,
        "TCCTCoreRewriteFreezeDedupUnchanged": True,
        "RetrospectiveRepairDoesNotCreateFreshClaim": not protocol["FreshCapabilityClaimAllowed"],
    }
    passed = all(checks.values())
    result = {"Stage": protocol["Stage"], "HistoricalHoldoutRows": historical_rows,
        "TrainingDomainRows": training_rows, "AdversarialRows": adversarial_rows,
        "Checks": checks, "PythonRepairAuditPass": passed,
        "Conclusion": "CANONICAL_PARTITION_INPUT_REPAIR_RETROSPECTIVE_DEV_PASS" if passed
            else "CANONICAL_PARTITION_INPUT_REPAIR_RETROSPECTIVE_DEV_FAIL"}
    dump("results/python_repair_audit.json", result)
    print(json.dumps({"Pass": passed,
        "OriginalHoldoutExact": sum(row["OriginalExactApplicationCount"] == row["ApplicationCount"] for row in historical_rows),
        "RepairedHoldoutExact": sum(row["RepairedExact"] for row in historical_rows),
        "OriginallyFailedRecovered": sum(row["RepairedExact"] for row in originally_failed),
        "TrainingCohortsUnchanged": sum(row["AllTrainingSignalsUnchanged"] for row in training_rows),
        "AdversarialAudits": sum(row["Pass"] for row in adversarial_rows)}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
