from __future__ import annotations

import json
from typing import Any


def outcome_key(value: list[list[int]]) -> str:
    return json.dumps(value, separators=(",", ":"))


def decision_count(rows: list[dict[str, Any]]) -> int:
    return len({row["DecisionLabel"] for row in rows})


def branches(rows: list[dict[str, Any]], query_hash: str) -> list[list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        groups.setdefault(outcome_key(row["QueryPredictions"][query_hash]), []).append(row)
    return list(groups.values())


def common_prefix(rows: list[dict[str, Any]]) -> list[int]:
    keys = [row["Program"]["Keys"] for row in rows]
    prefix = []
    for index in range(len(keys[0])):
        values = {key[index] for key in keys}
        if len(values) != 1:
            break
        prefix.append(next(iter(values)))
    return prefix


def instantiate_concept(rows: list[dict[str, Any]], unused: list[str],
                        queries: dict[str, dict[str, Any]],
                        concepts: dict[str, Any]) -> dict[str, Any]:
    prefix = common_prefix(rows)
    matches = [concept for concept in concepts["Concepts"]
               if concept["Feature"]["KnownPrefixLength"] == len(prefix)
               and decision_count(rows) >= concept["Feature"]["DecisionClassMinimum"]]
    if not matches:
        return {"Matched": False, "ConceptID": None, "InputSHA256": None}
    concept = matches[0]
    if concept["QueryTemplate"] == "CALIBRATE_NEXT_UNKNOWN_CONTEXT":
        candidates = [query_hash for query_hash in unused
                      if queries[query_hash]["Kind"] == "CALIBRATE"
                      and queries[query_hash]["Level"] == len(prefix)
                      and queries[query_hash]["Prefix"] == prefix]
    else:
        candidates = [query_hash for query_hash in unused
                      if queries[query_hash]["Kind"] == "DECISION"
                      and queries[query_hash]["Prefix"] == prefix]
    return {"Matched": True, "ConceptID": concept["ConceptID"],
            "InputSHA256": min(candidates) if candidates else None}


class Planner:
    def __init__(self, queries: list[dict[str, Any]], concepts: dict[str, Any] | None):
        self.queries = {row["InputSHA256"]: row for row in queries}
        self.concepts = concepts
        self.memo: dict[tuple, tuple[bool, str | None]] = {}
        self.counters = {
            "ExpandedStateCount": 0, "QueryEvaluationCount": 0,
            "OutcomeBranchEvaluationCount": 0, "ConceptMatchStateCount": 0,
            "ConceptInstantiatedStateCount": 0, "ConceptInstantiationMissCount": 0,
            "NoConceptMatchStateCount": 0,
        }

    def preferred(self, rows: list[dict[str, Any]], unused: list[str]) -> str | None:
        if self.concepts is None:
            return None
        instantiation = instantiate_concept(rows, unused, self.queries, self.concepts)
        if not instantiation["Matched"]:
            self.counters["NoConceptMatchStateCount"] += 1
            return None
        self.counters["ConceptMatchStateCount"] += 1
        if instantiation["InputSHA256"] is None:
            self.counters["ConceptInstantiationMissCount"] += 1
            return None
        self.counters["ConceptInstantiatedStateCount"] += 1
        return instantiation["InputSHA256"]

    def solve(self, rows: list[dict[str, Any]], unused: list[str], depth: int) -> tuple[bool, str | None]:
        if decision_count(rows) == 1:
            return True, None
        if depth == 0 or not unused:
            return False, None
        key = (tuple(sorted(row["ModelKey"] for row in rows)), tuple(sorted(unused)), depth)
        if key in self.memo:
            return self.memo[key]
        self.counters["ExpandedStateCount"] += 1
        ordered = sorted(unused)
        preferred = self.preferred(rows, ordered)
        if preferred is not None:
            ordered = [preferred] + [query for query in ordered if query != preferred]
        for query_hash in ordered:
            self.counters["QueryEvaluationCount"] += 1
            branch_rows = branches(rows, query_hash)
            self.counters["OutcomeBranchEvaluationCount"] += len(branch_rows)
            remaining = [query for query in unused if query != query_hash]
            if all(self.solve(branch, remaining, depth - 1)[0] for branch in branch_rows):
                self.memo[key] = (True, query_hash)
                return self.memo[key]
        self.memo[key] = (False, None)
        return self.memo[key]

    def find_minimal(self, rows: list[dict[str, Any]], unused: list[str], maximum_depth: int) -> dict[str, Any]:
        for depth in range(maximum_depth + 1):
            solvable, query_hash = self.solve(rows, unused, depth)
            if solvable:
                return {"Solvable": True, "RequiredDepth": depth,
                        "FirstInputSHA256": query_hash, "WorkCounters": dict(self.counters)}
        return {"Solvable": False, "RequiredDepth": None,
                "FirstInputSHA256": None, "WorkCounters": dict(self.counters)}


def find_plan(rows: list[dict[str, Any]], queries: list[dict[str, Any]],
              maximum_depth: int, concepts: dict[str, Any] | None) -> dict[str, Any]:
    planner = Planner(queries, concepts)
    return planner.find_minimal(rows, [row["InputSHA256"] for row in queries], maximum_depth)
