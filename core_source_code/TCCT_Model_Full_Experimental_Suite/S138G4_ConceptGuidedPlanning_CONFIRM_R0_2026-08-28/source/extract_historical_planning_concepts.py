from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from adaptive_geometry import models  # noqa: E402

SOURCES = [
    ROOT.parent / "S138G3_AdaptiveDepthPlanning_DEV_SMOKE_2026-08-28",
    ROOT.parent / "S138G3_AdaptiveDepthPlanning_CONFIRM_R0_2026-08-28",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def common_prefix(rows: list[dict[str, Any]]) -> list[int]:
    keys = [row["Program"]["Keys"] for row in rows]
    prefix = []
    for index in range(len(keys[0])):
        values = {key[index] for key in keys}
        if len(values) != 1:
            break
        prefix.append(next(iter(values)))
    return prefix


def main() -> int:
    events = []
    source_receipts = []
    for package in SOURCES:
        verification_path = package / "verification" / "independent_verification.json"
        verification = load(verification_path)
        if verification.get("CapabilityGatePass") is not True:
            raise RuntimeError(f"historical source did not pass: {package.name}")
        public = load(package / "input" / "public_tasks.json")
        result = load(package / "results" / "kernel_adaptive_depth_result.json")
        public_by = {row["TaskID"]: row for row in public["Tasks"]}
        source_receipts.append({
            "Package": package.name,
            "PublicSHA256": digest(package / "input" / "public_tasks.json"),
            "ResultSHA256": digest(package / "results" / "kernel_adaptive_depth_result.json"),
            "VerificationSHA256": digest(verification_path),
        })
        for task_row in result["TaskResults"]:
            task = public_by[task_row["TaskID"]]
            rows = models(task)
            for trace in task_row["ActiveQueryTrace"]:
                prefix = common_prefix(rows)
                query_kind = trace["QueryKind"]
                if len(prefix) < len(task["ContextCounts"]):
                    valid = query_kind == "CALIBRATE" and trace["QueryLevel"] == len(prefix) and trace["QueryPrefix"] == prefix
                    template = "CALIBRATE_NEXT_UNKNOWN_CONTEXT"
                else:
                    valid = query_kind == "DECISION" and trace["QueryPrefix"] == prefix
                    template = "DECIDE_AT_BOUND_CONTEXT"
                if not valid:
                    raise RuntimeError((package.name, task_row["TaskID"], prefix, trace))
                events.append({"SourcePackage": package.name, "TaskID": task_row["TaskID"],
                               "KnownPrefixLength": len(prefix), "Template": template})
                output = trace["OracleOutput"]
                rows = [row for row in rows
                        if row["QueryPredictions"][trace["InputSHA256"]] == output]
    concepts = []
    for known_length in (1, 2, 3):
        matching = [event for event in events if event["KnownPrefixLength"] == known_length]
        templates = {event["Template"] for event in matching}
        if len(matching) < 2 or len(templates) != 1 or len({event["SourcePackage"] for event in matching}) < 2:
            raise RuntimeError((known_length, matching))
        body = {"Feature": {"KnownPrefixLength": known_length, "DecisionClassMinimum": 2},
                "QueryTemplate": next(iter(templates)),
                "BindingPolicy": "INSTANTIATE_WITH_CURRENT_COMMON_CONTEXT_PREFIX"}
        concept_id = "PC_" + hashlib.sha256(json.dumps(body, sort_keys=True,
            separators=(",", ":")).encode("utf-8")).hexdigest()[:16]
        concepts.append({"ConceptID": concept_id, **body, "HistoricalSupportEventCount": len(matching),
                         "DistinctHistoricalPackageSupportCount": len({event["SourcePackage"] for event in matching})})
    library = {
        "LibraryType": "FROZEN_ANONYMOUS_PLANNING_QUERY_PRIORITY_CONCEPTS",
        "CreationPolicy": "AUTOMATIC_ABSTRACTION_FROM_VERIFIED_HISTORICAL_NATIVE_TRACES",
        "ConceptCount": len(concepts), "Concepts": concepts,
        "SourceReceipts": source_receipts, "ConceptsMayPruneModels": False,
        "ConceptsMaySuppressFallbackQueries": False,
        "ExactDynamicProgrammingFallbackRequired": True,
    }
    destination = ROOT / "library" / "frozen_planning_concepts.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(library, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"ExtractedConceptCount": len(concepts),
                      "SupportEvents": len(events), "Path": str(destination)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
