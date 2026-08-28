from __future__ import annotations

from typing import Any

from adaptive_geometry import apply_program, models as build_models, query_specs
from concept_dp import decision_count, find_plan, instantiate_concept


def replay_task(task: dict[str, Any], row: dict[str, Any], hidden: dict[str, Any],
                library: dict[str, Any], depth_cap: int, query_cap: int) -> bool:
    models = build_models(task)
    queries = query_specs(task)
    query_by_hash = {query["InputSHA256"]: query for query in queries}
    unused = [query["InputSHA256"] for query in queries]
    guided = find_plan(models, queries, depth_cap, library)
    baseline = find_plan(models, queries, depth_cap, None)
    guided_total = guided["WorkCounters"]["QueryEvaluationCount"]
    baseline_total = baseline["WorkCounters"]["QueryEvaluationCount"]
    guided_states = guided["WorkCounters"]["ExpandedStateCount"]
    baseline_states = baseline["WorkCounters"]["ExpandedStateCount"]
    parity = guided["Solvable"] == baseline["Solvable"] and guided["RequiredDepth"] == baseline["RequiredDepth"]
    if not all([
        row["InitialSemanticClassCount"] == len(models),
        row["InitialDecisionClassCount"] == decision_count(models),
        row["InitialCertifiedMinimumDepth"] == guided["RequiredDepth"],
        row["InitialBaselineCertifiedMinimumDepth"] == baseline["RequiredDepth"],
    ]):
        return False
    for index, trace in enumerate(row["ActiveQueryTrace"]):
        if index > 0:
            remaining_cap = min(depth_cap, query_cap - index)
            current_queries = [query_by_hash[query_hash] for query_hash in unused]
            guided = find_plan(models, current_queries, remaining_cap, library)
            baseline = find_plan(models, current_queries, remaining_cap, None)
            guided_total += guided["WorkCounters"]["QueryEvaluationCount"]
            baseline_total += baseline["WorkCounters"]["QueryEvaluationCount"]
            guided_states += guided["WorkCounters"]["ExpandedStateCount"]
            baseline_states += baseline["WorkCounters"]["ExpandedStateCount"]
            parity = parity and guided["Solvable"] == baseline["Solvable"] \
                and guided["RequiredDepth"] == baseline["RequiredDepth"]
        if not guided["Solvable"] or guided["RequiredDepth"] == 0:
            return False
        query_hash = guided["FirstInputSHA256"]
        query = query_by_hash[query_hash]
        concept = instantiate_concept(models, unused, query_by_hash, library)
        output = apply_program(task, hidden, query)
        if not all([
            trace["QueryNumber"] == f"KQ{index + 1:02d}",
            trace["Input"] == query["Input"], trace["InputSHA256"] == query_hash,
            trace["QueryKind"] == query["Kind"], trace["QueryLevel"] == query.get("Level"),
            trace["QueryPrefix"] == query.get("Prefix", []),
            trace["AdmissionMode"] == "CONCEPT_GUIDED_EXACT_DP_WITH_FALLBACK",
            trace["CertifiedMinimumDepthBefore"] == guided["RequiredDepth"],
            trace["BaselineCertifiedMinimumDepthBefore"] == baseline["RequiredDepth"],
            trace["BaselineFirstInputSHA256"] == baseline["FirstInputSHA256"],
            trace["RootConceptMatched"] == concept["Matched"],
            trace["RootConceptID"] == concept["ConceptID"],
            trace["RootConceptPreferredInputSHA256"] == concept["InputSHA256"],
            trace["SelectedQueryWasRootConceptPreference"] == (
                concept["InputSHA256"] is not None and query_hash == concept["InputSHA256"]),
            trace["RootConceptFallbackUsed"] == (
                concept["Matched"] and concept["InputSHA256"] is None),
            trace["GuidedWorkCounters"] == guided["WorkCounters"],
            trace["BaselineWorkCounters"] == baseline["WorkCounters"],
            trace["DecisionClassCountBefore"] == decision_count(models),
            trace["SemanticClassCountBefore"] == len(models), trace["OracleOutput"] == output,
            trace["GeneratedByTCCTKernel"], not trace["TestOutputAccessed"],
            not trace["HiddenProgramAccessedByLearner"],
        ]):
            return False
        models = [model for model in models if model["QueryPredictions"][query_hash] == output]
        unused.remove(query_hash)
        if trace["DecisionClassCountAfter"] != decision_count(models) or trace["SemanticClassCountAfter"] != len(models):
            return False
    committed = decision_count(models) == 1
    return all([
        row["PairedDepthParity"] == parity,
        row["GuidedQueryEvaluationCount"] == guided_total,
        row["BaselineQueryEvaluationCount"] == baseline_total,
        row["GuidedExpandedStateCount"] == guided_states,
        row["BaselineExpandedStateCount"] == baseline_states,
        row["FinalSemanticClassCount"] == len(models),
        row["FinalDecisionClassCount"] == decision_count(models),
        row["DecisionCertified"] == committed, row["TestPredictionCommitted"] == committed,
        row["CommittedTestPrediction"] == (models[0]["TestPrediction"] if committed else None),
        row["AdaptiveStopReason"] == ("DECISION_CERTIFIED" if committed else "NO_PLAN_WITHIN_RESOURCE_DEPTH"),
    ])
