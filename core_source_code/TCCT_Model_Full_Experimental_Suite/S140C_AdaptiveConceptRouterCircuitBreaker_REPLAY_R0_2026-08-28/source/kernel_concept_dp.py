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


STATE_FEATURES = (
    "KnownPrefixLength",
    "CoordinateCount",
    "RemainingCoordinateCount",
    "PlanningBudget",
    "CurrentDecisionClassCount",
)
QUERY_FEATURES = (
    "WorstCaseKnownPrefixGain",
    "WorstCaseDecisionClassReduction",
    "WorstCaseRemainingDecisionClasses",
    "OutcomeBranchCount",
)
OPERATORS = ("Equal", "GreaterEqual", "LessEqual")


def relational_features(rows: list[dict[str, Any]], query_hash: str,
                        planning_depth: int) -> dict[str, int]:
    known = len(common_prefix(rows))
    coordinate_count = len(rows[0]["Program"]["Keys"])
    query_branches = branches(rows, query_hash)
    branch_known = [len(common_prefix(branch)) for branch in query_branches]
    branch_decisions = [decision_count(branch) for branch in query_branches]
    current_decisions = decision_count(rows)
    worst_known = min(branch_known) if branch_known else known
    worst_decisions = max(branch_decisions) if branch_decisions else current_decisions
    return {
        "KnownPrefixLength": known,
        "CoordinateCount": coordinate_count,
        "RemainingCoordinateCount": coordinate_count - known,
        "PlanningBudget": planning_depth,
        "CurrentDecisionClassCount": current_decisions,
        "WorstCaseKnownPrefixGain": worst_known - known,
        "WorstCaseDecisionClassReduction": current_decisions - worst_decisions,
        "WorstCaseRemainingDecisionClasses": worst_decisions,
        "OutcomeBranchCount": len(query_branches),
    }


def atom_matches(atom: list[Any], features: dict[str, int]) -> bool:
    feature, operator, threshold = atom
    value = features[feature]
    if operator == "Equal":
        return value == threshold
    if operator == "GreaterEqual":
        return value >= threshold
    if operator == "LessEqual":
        return value <= threshold
    raise ValueError(f"unknown predicate operator: {operator}")


def rule_matches(rule: dict[str, Any], features: dict[str, int]) -> bool:
    return all(atom_matches(atom, features) for atom in rule["Conditions"])


def _invent_atoms(feature_rows: list[dict[str, int]]) -> list[list[Any]]:
    atoms: list[list[Any]] = []
    for feature in (*STATE_FEATURES, *QUERY_FEATURES):
        for threshold in sorted({row[feature] for row in feature_rows}):
            atoms.extend([[feature, operator, threshold] for operator in OPERATORS])
    return atoms


def _candidate_rules(atoms: list[list[Any]]) -> list[dict[str, Any]]:
    query_atoms = [atom for atom in atoms if atom[0] in QUERY_FEATURES]
    rows = [{"Conditions": [atom]} for atom in query_atoms]
    for left, right in itertools.combinations(atoms, 2):
        if left[0] == right[0]:
            continue
        if left[0] not in QUERY_FEATURES and right[0] not in QUERY_FEATURES:
            continue
        rows.append({"Conditions": [left, right]})
    canonical: dict[str, dict[str, Any]] = {}
    for row in rows:
        row["Conditions"] = sorted(row["Conditions"])
        key = json.dumps(row["Conditions"], separators=(",", ":"))
        canonical[key] = row
    return [canonical[key] for key in sorted(canonical)]


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
    feature_rows = [features for _, _, features in positives] + [features for _, features in negatives]
    invented_atoms = _invent_atoms(feature_rows)
    valid = []
    for rule in _candidate_rules(invented_atoms):
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
    source_activation_rows = []
    maximum_numerator, maximum_denominator = 0, 1
    for event in events:
        unused = event["UnusedInputSHA256"]
        matched = [query_hash for query_hash in unused if any(
            rule_matches(concept, relational_features(event["Rows"], query_hash,
                                                       event["PlanningDepth"]))
            for concept in selected)]
        numerator, denominator = len(matched), max(1, len(unused))
        source_activation_rows.append({"TaskID": event["TaskID"],
                                       "Numerator": numerator, "Denominator": denominator})
        if numerator * maximum_denominator > maximum_numerator * denominator:
            maximum_numerator, maximum_denominator = numerator, denominator
    return {
        "LibraryType": "KERNEL_INVENTED_NUMERIC_RELATIONAL_PREDICATE_CONCEPTS",
        "InductionMethod": "DATA_DERIVED_THRESHOLD_ATOMS_PLUS_MDL_ZERO_FALSE_POSITIVE_SET_COVER",
        "PrimitiveNumericStateFeatures": list(STATE_FEATURES),
        "PrimitiveNumericQueryFeatures": list(QUERY_FEATURES),
        "PrimitiveComparisonOperators": list(OPERATORS),
        "PredeclaredNamedBooleanPredicates": [],
        "InventedAtomicPredicateCount": len(invented_atoms),
        "InventedAtomicPredicates": invented_atoms,
        "SourceEventCount": len(events), "SourceOptimalQueryExampleCount": len(positives),
        "UnabstractedOptimalQueryExampleCount": len(uncovered),
        "ConceptCount": len(selected), "Concepts": selected,
        "RouterActivationCalibration": {
            "Rule": "PREFERRED_FRACTION_NOT_ABOVE_MAXIMUM_SOURCE_EVENT_FRACTION",
            "MaximumSourcePreferredFractionNumerator": maximum_numerator,
            "MaximumSourcePreferredFractionDenominator": maximum_denominator,
            "SourceEventFractions": source_activation_rows,
        },
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
            "ConceptActivationEnvelopeRejectedStateCount": 0,
            "ConceptActivationEnvelopeRejectedQueryCount": 0,
        }

    def preferred(self, rows: list[dict[str, Any]], unused: list[str], depth: int) -> list[str]:
        if self.concepts is None:
            return []
        preferred: list[str] = []
        for concept in self.concepts["Concepts"]:
            matches = [query_hash for query_hash in sorted(unused)
                       if rule_matches(concept, relational_features(rows, query_hash, depth))]
            preferred.extend(query_hash for query_hash in matches if query_hash not in preferred)
        calibration = self.concepts.get("RouterActivationCalibration")
        if preferred and calibration is not None:
            numerator = calibration["MaximumSourcePreferredFractionNumerator"]
            denominator = calibration["MaximumSourcePreferredFractionDenominator"]
            if len(preferred) * denominator > len(unused) * numerator:
                self.counters["ConceptActivationEnvelopeRejectedStateCount"] += 1
                self.counters["ConceptActivationEnvelopeRejectedQueryCount"] += len(preferred)
                self.counters["ConceptNoCandidateStateCount"] += 1
                return []
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
