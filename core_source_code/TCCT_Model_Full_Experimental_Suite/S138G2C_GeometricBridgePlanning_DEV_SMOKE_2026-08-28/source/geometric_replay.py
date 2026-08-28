from __future__ import annotations

import json
from typing import Any

from geometry_world import apply_program, models as build_models, queries as build_queries


def outcome_key(value: list[list[int]]) -> str:
    return json.dumps(value, separators=(",", ":"))


def decision_count(rows: list[dict[str, Any]]) -> int:
    return len({row["DecisionLabel"] for row in rows})


def branches(rows: list[dict[str, Any]], query_hash: str) -> list[list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(outcome_key(row["QueryPredictions"][query_hash]), []).append(row)
    return list(groups.values())


def one_worst(rows: list[dict[str, Any]], query_hash: str) -> int:
    return max(decision_count(branch) for branch in branches(rows, query_hash))


def semantic_worst(rows: list[dict[str, Any]], query_hash: str) -> int:
    return max(len(branch) for branch in branches(rows, query_hash))


def immediate_rows(rows: list[dict[str, Any]], query_hashes: list[str]) -> list[dict]:
    current = decision_count(rows)
    candidates = [{
        "InputSHA256": query_hash,
        "OneStepWorstDecisionClassCount": one_worst(rows, query_hash),
        "OneStepWorstSemanticClassCount": semantic_worst(rows, query_hash),
    } for query_hash in query_hashes]
    return sorted(
        [row for row in candidates if row["OneStepWorstDecisionClassCount"] < current],
        key=lambda row: (row["OneStepWorstDecisionClassCount"],
                         row["OneStepWorstSemanticClassCount"], row["InputSHA256"]),
    )


def best_followup(rows: list[dict[str, Any]], query_hashes: list[str]) -> dict:
    current = decision_count(rows)
    candidates = sorted([{
        "InputSHA256": query_hash,
        "WorstDecisionClassCount": one_worst(rows, query_hash),
        "WorstSemanticClassCount": semantic_worst(rows, query_hash),
    } for query_hash in query_hashes], key=lambda row: (
        row["WorstDecisionClassCount"], row["WorstSemanticClassCount"], row["InputSHA256"]))
    if not candidates or candidates[0]["WorstDecisionClassCount"] >= current:
        return {"InputSHA256": None, "WorstDecisionClassCount": current,
                "WorstSemanticClassCount": len(rows)}
    return candidates[0]


def bridge_row(rows: list[dict[str, Any]], first: str, query_hashes: list[str]) -> dict:
    remaining = [query for query in query_hashes if query != first]
    certificates = []
    for branch in branches(rows, first):
        followup = best_followup(branch, remaining)
        certificates.append({
            "FirstOutcome": branch[0]["QueryPredictions"][first],
            "BranchSemanticClassCount": len(branch),
            "BranchDecisionClassCount": decision_count(branch),
            "BestSecondInputSHA256": followup["InputSHA256"],
            "BestSecondWorstDecisionClassCount": followup["WorstDecisionClassCount"],
            "BestSecondWorstSemanticClassCount": followup["WorstSemanticClassCount"],
        })
    return {
        "InputSHA256": first,
        "OneStepWorstDecisionClassCount": one_worst(rows, first),
        "OneStepWorstSemanticClassCount": semantic_worst(rows, first),
        "TwoStepWorstDecisionClassCount": max(
            certificate["BestSecondWorstDecisionClassCount"] for certificate in certificates),
        "BranchCertificates": certificates,
    }


def bridge_rows(rows: list[dict[str, Any]], query_hashes: list[str]) -> list[dict]:
    current = decision_count(rows)
    candidates = [bridge_row(rows, query_hash, query_hashes) for query_hash in query_hashes]
    return sorted(
        [row for row in candidates
         if row["OneStepWorstDecisionClassCount"] >= current
         and row["TwoStepWorstDecisionClassCount"] < current],
        key=lambda row: (row["TwoStepWorstDecisionClassCount"],
                         row["OneStepWorstSemanticClassCount"], row["InputSHA256"]),
    )


def replay_task(task: dict, row: dict, hidden_program: dict[str, int]) -> bool:
    models = build_models(task)
    query_rows = build_queries(task)
    query_by_hash = {query["InputSHA256"]: query for query in query_rows}
    unused = [query["InputSHA256"] for query in query_rows]
    if row["InitialSemanticClassCount"] != len(models) or row["InitialDecisionClassCount"] != decision_count(models):
        return False
    for index, trace in enumerate(row["ActiveQueryTrace"], 1):
        immediate = immediate_rows(models, unused)
        if immediate:
            expected, mode = immediate[0], "IMMEDIATE_DECISION_GAIN"
        else:
            bridges = bridge_rows(models, unused)
            if not bridges:
                return False
            expected, mode = bridges[0], "TWO_STEP_BRIDGE_CERTIFICATE"
        query_hash = expected["InputSHA256"]
        query = query_by_hash[query_hash]
        oracle_output = apply_program(task, hidden_program, query["Kind"], query["Slot"])
        if not all([
            trace["QueryNumber"] == f"KQ{index:02d}",
            trace["AdmissionMode"] == mode,
            trace["InputSHA256"] == query_hash,
            trace["Input"] == query["Input"],
            trace["QueryKind"] == query["Kind"], trace["QuerySlot"] == query["Slot"],
            trace["DecisionClassCountBefore"] == decision_count(models),
            trace["SemanticClassCountBefore"] == len(models),
            trace["OneStepWorstDecisionClassCount"] == expected["OneStepWorstDecisionClassCount"],
            trace["TwoStepWorstDecisionClassCount"] == expected.get("TwoStepWorstDecisionClassCount"),
            trace["OracleOutput"] == oracle_output,
            trace["GeneratedByTCCTKernel"], not trace["TestOutputAccessed"],
            not trace["HiddenProgramAccessedByLearner"],
        ]):
            return False
        models = [model for model in models
                  if model["QueryPredictions"][query_hash] == oracle_output]
        unused.remove(query_hash)
        if trace["DecisionClassCountAfter"] != decision_count(models) or trace["SemanticClassCountAfter"] != len(models):
            return False
    committed = decision_count(models) == 1
    expected_prediction = models[0]["TestPrediction"] if committed else None
    no_plan = not immediate_rows(models, unused) and not bridge_rows(models, unused)
    return all([
        row["FinalSemanticClassCount"] == len(models),
        row["FinalDecisionClassCount"] == decision_count(models),
        row["DecisionCertified"] == committed,
        row["TestPredictionCommitted"] == committed,
        row["CommittedTestPrediction"] == expected_prediction,
        row["AdaptiveStopReason"] == ("DECISION_CERTIFIED" if committed else "NO_DEPTH2_DECISION_PLAN"),
        committed or no_plan,
    ])
