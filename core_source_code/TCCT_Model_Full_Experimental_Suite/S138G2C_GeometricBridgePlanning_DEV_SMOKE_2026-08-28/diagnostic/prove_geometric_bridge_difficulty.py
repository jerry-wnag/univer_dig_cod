from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from geometry_world import apply_program, models, queries  # noqa: E402


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dcount(rows: list[dict]) -> int:
    return len({row["DecisionLabel"] for row in rows})


def branches(rows: list[dict], query_hash: str) -> list[list[dict]]:
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = json.dumps(row["QueryPredictions"][query_hash], separators=(",", ":"))
        groups.setdefault(key, []).append(row)
    return list(groups.values())


def worst(rows: list[dict], query_hash: str) -> int:
    return max(dcount(branch) for branch in branches(rows, query_hash))


def best_one(rows: list[dict], query_hashes: list[str]) -> int:
    return min([dcount(rows)] + [worst(rows, query) for query in query_hashes])


def two_worst(rows: list[dict], first: str, query_hashes: list[str]) -> int:
    remaining = [query for query in query_hashes if query != first]
    return max(best_one(branch, remaining) for branch in branches(rows, first))


def main() -> int:
    protocol = load(ROOT / "protocol" / "frozen_protocol.json")
    public, sealed = load(ROOT / "input" / "public_tasks.json"), load(ROOT / "sealed" / "test_outputs.json")
    sealed_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    audits = []
    for task in public["Tasks"]:
        rows, query_rows = models(task), queries(task)
        query_hashes = [row["InputSHA256"] for row in query_rows]
        current = dcount(rows)
        best1 = best_one(rows, query_hashes)
        best2 = min([current] + [two_worst(rows, query, query_hashes) for query in query_hashes])
        role = sealed_by[task["TaskID"]]["ExpectedRole"]
        expected_positive = role == "GEOMETRIC_TWO_STEP_BRIDGE"
        role_pass = best1 == current and (best2 == 1 if expected_positive else best2 == current)
        training_exact = all(
            apply_program(task, model["Program"], "TRAIN")
            == task["InitialTrain"][0]["Output"]
            for model in rows
        )
        audits.append({
            "TaskID": task["TaskID"], "ExpectedRole": role,
            "CandidateProgramCount": len(rows), "SynthesizedQueryCount": len(query_rows),
            "InitialDecisionClassCount": current,
            "BestOneStepWorstDecisionClassCount": best1,
            "BestTwoStepWorstDecisionClassCount": best2,
            "AllCandidateProgramsTrainingExact": training_exact,
            "RoleDifficultyPass": role_pass and training_exact,
        })
    passed = all(row["RoleDifficultyPass"] for row in audits)
    result = {
        "Stage": protocol["Stage"], "CertificateType": "EXECUTABLE_GEOMETRY_DEPTH2_MINIMAX",
        "PositiveCount": sum(row["ExpectedRole"] == "GEOMETRIC_TWO_STEP_BRIDGE" for row in audits),
        "ControlCount": sum(row["ExpectedRole"] == "GEOMETRIC_IRREDUCIBLE_CONTROL" for row in audits),
        "AllPositiveWorldsRequireGeometricBridgePass": all(row["RoleDifficultyPass"] for row in audits if row["ExpectedRole"] == "GEOMETRIC_TWO_STEP_BRIDGE"),
        "AllControlsGeometricallyIrreduciblePass": all(row["RoleDifficultyPass"] for row in audits if row["ExpectedRole"] == "GEOMETRIC_IRREDUCIBLE_CONTROL"),
        "PostSeedWorldFilteringUsed": False, "DifficultyCertificatePass": passed,
        "TaskAudits": audits,
    }
    destination = ROOT / "diagnostic" / "difficulty_certificate.json"
    destination.write_text(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps(result, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
