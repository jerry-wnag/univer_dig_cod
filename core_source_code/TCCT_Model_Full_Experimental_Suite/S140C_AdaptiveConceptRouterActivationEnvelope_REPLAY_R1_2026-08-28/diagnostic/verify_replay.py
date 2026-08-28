from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "original_failure"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_conditions(library: dict[str, Any]) -> list[str]:
    return sorted(json.dumps(row["Conditions"], sort_keys=True, separators=(",", ":"))
                  for row in library["Concepts"])


def main() -> int:
    protocol = read(ROOT / "protocol" / "frozen_protocol.json")
    public, original_public = read(ROOT / "input" / "public_tasks.json"), read(
        ARCHIVE / "input" / "public_tasks.json")
    sealed, original_sealed = read(ROOT / "sealed" / "test_outputs.json"), read(
        ARCHIVE / "sealed" / "test_outputs.json")
    native, original_native = read(ROOT / "results" / "kernel_native_concept_result.json"), read(
        ARCHIVE / "kernel_native_concept_result.json")
    certificate = read(ROOT / "diagnostic" / "kernel_concept_certificate.json")
    truth_by = {row["TaskID"]: row for row in sealed["Tasks"]}
    native_by = {row["TaskID"]: row for row in native["TargetTaskResults"]}
    original_by = {row["TaskID"]: row for row in original_native["TargetTaskResults"]}
    transfer_roles = {"SURFACE_PERMUTATION_TRANSFER", "COORDINATE_SCALE_TRANSFER",
                      "SEQUENTIAL_CONCEPT_COMPOSITION"}
    target_rows = []
    for task_id, row in native_by.items():
        truth = truth_by[task_id]
        exact = row["CommittedTestPrediction"] == truth["TestOutputs"][0]["Output"]
        target_rows.append({
            "TaskID": task_id, "Role": truth["ExpectedRole"], "Exact": exact,
            "ExpectedDepth": truth["ExpectedMinimumGuaranteedDepth"],
            "ObservedDepth": row["InitialCertifiedMinimumDepth"],
            "GuidedWork": row["GuidedQueryEvaluationCount"],
            "BaselineWork": row["BaselineQueryEvaluationCount"],
            "OriginalFailedGuidedWork": original_by[task_id]["GuidedQueryEvaluationCount"],
            "EnvelopeRejectedStateCount": row["InitialGuidedWorkCounters"].get(
                "ConceptActivationEnvelopeRejectedStateCount", 0),
            "RootFallbackCount": sum(trace["RootConceptFallbackUsed"] is True
                                     for trace in row["ActiveQueryTrace"]),
        })
    transfer = [row for row in target_rows if row["Role"] in transfer_roles]
    sequential = next(row for row in target_rows if row["Role"] == "SEQUENTIAL_CONCEPT_COMPOSITION")
    no_reuse = next(row for row in target_rows if row["Role"] == "NO_REUSABLE_CONCEPT_FALLBACK")
    native_library = native["KernelInducedConceptLibrary"]
    independent_library = certificate["IndependentlyInducedConceptLibrary"]
    calibration = native_library["RouterActivationCalibration"]
    checks = {
        "RetrospectiveStatusExplicit": protocol["RetrospectiveReplay"] is True and
            protocol["ProtocolFrozenBeforeTaskMaterialization"] is False,
        "OriginalFailureHashesPreserved": protocol["OriginalFailedProtocolSHA256"] == digest(
            ARCHIVE / "frozen_protocol.json") and protocol["OriginalFailedNativeResultSHA256"] == digest(
            ARCHIVE / "kernel_native_concept_result.json"),
        "TaskBodiesUnchanged": public["SourceTasks"] == original_public["SourceTasks"] and
            public["TargetTasks"] == original_public["TargetTasks"] and sealed["Tasks"] == original_sealed["Tasks"],
        "FrozenRepairHashesPass": protocol["FrozenWolframRunnerSHA256"] == digest(
            ROOT / "source" / "run_kernel_concept_formation.wl") and
            protocol["FrozenConceptDPSHA256"] == digest(ROOT / "source" / "kernel_concept_dp.py") and
            protocol["FrozenReplayVerifierSHA256"] == digest(Path(__file__)),
        "NativePythonConceptBodiesMatch": canonical_conditions(native_library) ==
            canonical_conditions(independent_library),
        "SourceDerivedActivationEnvelopeMatch": calibration == independent_library[
            "RouterActivationCalibration"] and calibration[
            "Rule"] == "PREFERRED_FRACTION_NOT_ABOVE_MAXIMUM_SOURCE_EVENT_FRACTION",
        "AllFiveAnswersAndDepthsExact": len(target_rows) == 5 and all(
            row["Exact"] and row["ObservedDepth"] == row["ExpectedDepth"] for row in target_rows),
        "TransferWorkBelowBaseline": sum(row["GuidedWork"] for row in transfer) <
            sum(row["BaselineWork"] for row in transfer),
        "SequentialFailureRepaired": sequential["GuidedWork"] < sequential["BaselineWork"] and
            sequential["GuidedWork"] < sequential["OriginalFailedGuidedWork"],
        "NoReuseControlFallsBack": no_reuse["RootFallbackCount"] >= 1 and
            no_reuse["GuidedWork"] == no_reuse["BaselineWork"],
        "EnvelopeActuallyExercised": sum(row["EnvelopeRejectedStateCount"] for row in target_rows) > 0,
        "NativePreScorePass": native["NativePreScorePass"] is True,
        "CoreUnchanged": native["CoreRewriteFreezeDedupModified"] is False,
    }
    result = {
        "Stage": protocol["Stage"] + " independent replay verification",
        "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "OriginalS140BFailureStillValid": True,
        "RetrospectiveReplayOnly": True,
        "ActivationEnvelope": calibration,
        "TargetComparisons": target_rows,
        "Checks": checks,
        "RepairReplayPass": all(checks.values()),
        "CoreRewriteFreezeDedupModified": False,
        "Conclusion": "RETROSPECTIVE_HIGH_PREFIX_ROUTER_REPAIR_PASS" if all(checks.values()) else
                      "RETROSPECTIVE_HIGH_PREFIX_ROUTER_REPAIR_FAIL",
    }
    destination = ROOT / "verification" / "repair_replay_verification.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"RepairReplayPass": result["RepairReplayPass"],
                      "SequentialGuidedWork": sequential["GuidedWork"],
                      "SequentialBaselineWork": sequential["BaselineWork"],
                      "SequentialOriginalFailedWork": sequential["OriginalFailedGuidedWork"]},
                     separators=(",", ":")))
    return 0 if result["RepairReplayPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
