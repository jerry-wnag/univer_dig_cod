from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from adaptive_geometry import models, query_specs  # noqa: E402
from build_concept_guided_tasks import (CONTEXT_PATTERNS, DISCRIMINATING_SHAPES,
                                        build_task)  # noqa: E402
from concept_dp import find_plan  # noqa: E402


def main() -> int:
    library = json.loads((ROOT / "library" / "frozen_planning_concepts.json").read_text(encoding="utf-8"))
    roles = ["CONCEPT_TRANSFER_DEPTH1", "CONCEPT_TRANSFER_DEPTH2", "CONCEPT_TRANSFER_DEPTH3",
             "CONCEPT_MISMATCH_FALLBACK_DEPTH2", "DEPTH4_BUDGET_CONTROL"]
    expected_by = {"CONCEPT_TRANSFER_DEPTH1": 1, "CONCEPT_TRANSFER_DEPTH2": 2,
                   "CONCEPT_TRANSFER_DEPTH3": 3, "CONCEPT_MISMATCH_FALLBACK_DEPTH2": 2,
                   "DEPTH4_BUDGET_CONTROL": 4}
    rows = []
    for seed in (1387001, 1387002):
        rng = random.Random(seed)
        shuffled = roles[:]
        rng.shuffle(shuffled)
        for index, (role, shape, counts) in enumerate(zip(
                shuffled, rng.sample(DISCRIMINATING_SHAPES, 5), rng.sample(CONTEXT_PATTERNS, 5)), 1):
            task, _, _ = build_task(rng, f"D{seed}_{index}", role, shape, counts)
            hypotheses, queries = models(task), query_specs(task)
            baseline = find_plan(hypotheses, queries, 4, None)
            guided = find_plan(hypotheses, queries, 4, library)
            expected = expected_by[role]
            if not all([baseline["Solvable"], guided["Solvable"],
                        baseline["RequiredDepth"] == expected,
                        guided["RequiredDepth"] == expected]):
                raise RuntimeError((seed, role, baseline, guided))
            rows.append({"Role": role,
                         "BaselineQueries": baseline["WorkCounters"]["QueryEvaluationCount"],
                         "GuidedQueries": guided["WorkCounters"]["QueryEvaluationCount"],
                         "InstantiationMisses": guided["WorkCounters"]["ConceptInstantiationMissCount"]})
    baseline_total = sum(row["BaselineQueries"] for row in rows)
    guided_total = sum(row["GuidedQueries"] for row in rows)
    if guided_total >= baseline_total:
        raise RuntimeError((baseline_total, guided_total))
    if not any(row["Role"] == "CONCEPT_MISMATCH_FALLBACK_DEPTH2" and row["InstantiationMisses"] > 0 for row in rows):
        raise RuntimeError("mismatch fallback was not exercised")
    print({"DevelopmentWorldsAudited": len(rows), "ExactDepthParity": True,
           "BaselineQueryEvaluations": baseline_total, "GuidedQueryEvaluations": guided_total,
           "DeterministicWorkReduced": guided_total < baseline_total,
           "MismatchFallbackExercised": True, "FormalSeedTouched": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
