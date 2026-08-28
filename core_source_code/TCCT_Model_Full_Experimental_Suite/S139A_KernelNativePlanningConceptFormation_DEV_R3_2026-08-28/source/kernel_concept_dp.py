from __future__ import annotations

import hashlib
import itertools
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
    prefix: list[int] = []
    if not keys:
        return prefix
    for index in range(len(keys[0])):
        values = {key[index] for key in keys}
        if len(values) != 1:
            break
        prefix.append(next(iter(values)))
    return prefix


STATE_LITERALS = ("RemainingCoordinatesPositive", "RemainingCoordinatesZero",
                  "PlanningDepthGreaterThanOne", "PlanningDepthEqualOne")
QUERY_LITERALS = (
    "GuaranteedKnownPrefixGain",
    "GuaranteedDecisionResolution",
    "GuaranteedDecisionProgress",
    "NonTrivialOutcomePartition",
)


def relational_features(rows: list[dict[str, Any]], query_hash: str,
                        planning_depth: int) -> dict[str, bool]:
    known = len(common_prefix(rows))
    coordinate_count = len(rows[0]["Program"]["Keys"])
    query_branches = branches(rows, query_hash)
    branch_known = [len(common_prefix(branch)) for branch in query_branches]
    branch_decisions = [decision_count(branch) for branch in query_branches]
    current_decisions = decision_count(rows)
    return {
        "RemainingCoordinatesPositive": known < coordinate_count,
        "RemainingCoordinatesZero": known == coordinate_count,
        "PlanningDepthGreaterThanOne": planning_depth > 1,
        "PlanningDepthEqualOne": planning_depth == 1,
        "GuaranteedKnownPrefixGain": bool(branch_known) and min(branch_known) > known,
        "GuaranteedDecisionResolution": bool(branch_decisions) and max(branch_decisions) == 1,
        "GuaranteedDecisionProgress": bool(branch_decisions) and max(branch_decisions) < current_decisions,
        "NonTrivialOutcomePartition": len(query_branches) > 1,
    }


def rule_matches(rule: dict[str, Any], features: dict[str, bool]) -> bool:
    return all(features.get(key) is value for key, value in rule["Conditions"])


def _candidate_rules() -> list[dict[str, Any]]:
    rows = []
    for state_key in STATE_LITERALS:
        for count in (1, 2):
            for query_keys in itertools.combinations(QUERY_LITERALS, count):
                rows.append({"Conditions": [[state_key, True], *[[key, True] for key in query_keys]]})
    return rows


def induce_concepts(events: list[dict[str, Any]]) -> dict[str, Any]:
    if not events:
        raise RuntimeError("no kernel planning events supplied")
    positives = []
    negatives = []
    positive_index = 0
    for event_index, event in enumerate(events):
        rows, planning_depth = event["Rows"], event["PlanningDepth"]
        chosen_set = set(event["OptimalInputSHA256"])
        for chosen in event["OptimalInputSHA256"]:
            positives.append((positive_index, event["TaskID"],
                              relational_features(rows, chosen, planning_depth)))
            positive_index += 1
        for query_hash in event["UnusedInputSHA256"]:
            if query_hash not in chosen_set:
                negatives.append((event_index, relational_features(rows, query_hash, planning_depth)))
    valid = []
    for rule in _candidate_rules():
        covered = [(index, task_id) for index, task_id, features in positives
                   if rule_matches(rule, features)]
        false_positive_count = sum(rule_matches(rule, features) for _, features in negatives)
        distinct_tasks = len({task_id for _, task_id in covered})
        if len(covered) >= 2 and distinct_tasks >= 2 and false_positive_count == 0:
            valid.append({**rule, "CoveredEventIndices": [index for index, _ in covered],
                          "SupportEventCount": len(covered),
                          "DistinctSourceTaskSupportCount": distinct_tasks,
                          "TrainingFalsePositiveCount": 0})
    uncovered = set(range(len(positives)))
    selected = []
    while uncovered:
        ranked = []
        for rule in valid:
            new_cover = uncovered.intersection(rule["CoveredEventIndices"])
            if new_cover:
                canonical = json.dumps(rule["Conditions"], sort_keys=True, separators=(",", ":"))
                ranked.append((-len(new_cover), len(rule["Conditions"]), canonical, rule))
        if not ranked:
            break
        chosen = min(ranked)[-1]
        body = {"Conditions": chosen["Conditions"]}
        concept_id = "KC_" + hashlib.sha256(json.dumps(
            body, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:16]
        selected.append({"ConceptID": concept_id, **body,
                         "SupportEventCount": chosen["SupportEventCount"],
                         "DistinctSourceTaskSupportCount": chosen["DistinctSourceTaskSupportCount"],
                         "TrainingFalsePositiveCount": 0})
        uncovered.difference_update(chosen["CoveredEventIndices"])
        valid = [rule for rule in valid if rule["Conditions"] != chosen["Conditions"]]
    return {
        "LibraryType": "KERNEL_INDUCED_ANONYMOUS_RELATIONAL_PLANNING_CONCEPTS",
        "InductionMethod": "MDL_ORDERED_ZERO_FALSE_POSITIVE_CONJUNCTIVE_SET_COVER",
        "PrimitiveStatePredicates": list(STATE_LITERALS),
        "PrimitiveQueryPredicates": list(QUERY_LITERALS),
        "SourceEventCount": len(events), "SourceOptimalQueryExampleCount": len(positives),
        "UnabstractedOptimalQueryExampleCount": len(uncovered),
        "ConceptCount": len(selected), "Concepts": selected,
        "ConceptsMayPruneModels": False, "ConceptsMaySuppressFallbackQueries": False,
        "ExactDynamicProgrammingFallbackRequired": True,
    }


class Planner:
    def __init__(self, queries: list[dict[str, Any]], concepts: dict[str, Any] | None):
        self.queries = {row["InputSHA256"]: row for row in queries}
        self.concepts = concepts
        self.memo: dict[tuple, tuple[bool, str | None]] = {}
        self.counters = {
            "ExpandedStateCount": 0, "QueryEvaluationCount": 0,
            "OutcomeBranchEvaluationCount": 0, "ConceptApplicableStateCount": 0,
            "ConceptInstantiatedQueryCount": 0, "ConceptNoCandidateStateCount": 0,
            "ConceptPreferredQueryRejectedCount": 0,
        }

    def preferred(self, rows: list[dict[str, Any]], unused: list[str], depth: int) -> list[str]:
        if self.concepts is None:
            return []
        preferred: list[str] = []
        for concept in self.concepts["Concepts"]:
            matches = [query_hash for query_hash in sorted(unused)
                       if rule_matches(concept, relational_features(rows, query_hash, depth))]
            preferred.extend(query_hash for query_hash in matches if query_hash not in preferred)
        if preferred:
            self.counters["ConceptApplicableStateCount"] += 1
            self.counters["ConceptInstantiatedQueryCount"] += len(preferred)
        else:
            self.counters["ConceptNoCandidateStateCount"] += 1
        return preferred

    def solve(self, rows: list[dict[str, Any]], unused: list[str], depth: int) -> tuple[bool, str | None]:
        if decision_count(rows) == 1:
            return True, None
        if depth == 0 or not unused:
            return False, None
        key = (tuple(sorted(row["ModelKey"] for row in rows)), tuple(sorted(unused)), depth)
        if key in self.memo:
            return self.memo[key]
        self.counters["ExpandedStateCount"] += 1
        preferred = self.preferred(rows, unused, depth)
        ordered = preferred + [query_hash for query_hash in sorted(unused) if query_hash not in preferred]
        for query_hash in ordered:
            self.counters["QueryEvaluationCount"] += 1
            query_branches = branches(rows, query_hash)
            self.counters["OutcomeBranchEvaluationCount"] += len(query_branches)
            remaining = [query for query in unused if query != query_hash]
            if all(self.solve(branch, remaining, depth - 1)[0] for branch in query_branches):
                self.memo[key] = (True, query_hash)
                return self.memo[key]
            if query_hash in preferred:
                self.counters["ConceptPreferredQueryRejectedCount"] += 1
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
              maximum_depth: int, concepts: dict[str, Any] | None,
              unused: list[str] | None = None) -> dict[str, Any]:
    planner = Planner(queries, concepts)
    return planner.find_minimal(rows, unused if unused is not None else
                                [row["InputSHA256"] for row in queries], maximum_depth)
