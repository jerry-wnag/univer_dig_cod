from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = ROOT.parent / "S138G3_AdaptiveDepthPlanning_CONFIRM_R0_2026-08-28"
PYTHON = Path(r"E:\anaconda\python.exe")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encoded_bridge() -> str:
    root_b64 = base64.b64encode(str(ROOT).encode("utf-8")).decode("ascii")
    script = (
        f"$root=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{root_b64}'));"
        f"$python='{PYTHON}';$responder=Join-Path $root 'source\\oracle_responder.py';"
        "if($env:TCCT_ORACLE_MODE -eq 'reset'){& $python $responder --reset;exit $LASTEXITCODE};"
        "& $python $responder --task-id $env:TCCT_TASK --query-id $env:TCCT_QUERY;exit $LASTEXITCODE"
    )
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def main() -> int:
    seed = int(os.environ.get("TCCT_PROTOCOL_SEED", "1390107"))
    dev = "TCCT_PROTOCOL_SEED" in os.environ
    protocol = {
        "Stage": "S138-G4 DEV native smoke" if dev else "S138-G4 CONFIRM R0 historical-concept-guided epistemic planning",
        "EvidenceStatus": "DEVELOPMENT_ONLY" if dev else "PROSPECTIVE_LOCAL_CONFIRMATORY_CONCEPT_GUIDED_PLANNING",
        "ProtocolFrozenBeforeTaskMaterialization": True,
        "HistoricalConceptLibraryFrozenBeforeTaskMaterialization": True,
        "AllLearnerSourcesFrozenBeforeTaskMaterialization": True,
        "FreshWorldsMaterializedAfterProtocolFreeze": True,
        "FreshTaskGeneratorSeed": seed, "TaskOrder": [f"CG{index:03d}" for index in range(1, 6)],
        "MaximumPlanningDepth": 3, "MaximumActiveQueriesPerTask": 3,
        "MaximumPlanningDepthMeaning": "RESOURCE_CAP_ONLY_NOT_TASK_SPECIFIC_REQUIRED_DEPTH",
        "ConceptRole": "QUERY_ORDERING_ONLY",
        "ConceptMayPruneModels": False, "ConceptMaySuppressFallbackQueries": False,
        "Fallback": "COMPLETE_HASH_ORDERED_ITERATIVE_DEEPENING_DYNAMIC_PROGRAMMING",
        "PairedBaseline": "SAME_VERSION_SPACE_SAME_DEPTH_CAP_SAME_STATE_WITH_CONCEPT_LIBRARY_DISABLED",
        "WorkMetric": "EXACT_QUERY_CANDIDATE_EVALUATIONS_DURING_DYNAMIC_PROGRAMMING",
        "WorkReductionThreshold": "STRICTLY_POSITIVE_ONLY_NO_POSTHOC_PERCENTAGE",
        "PostSeedWorldFilteringAllowed": False, "NoWorldReplacementAfterMaterialization": True,
        "PublicQueryPoolSize": 0, "InterventionsSynthesizedByKernel": True,
        "BenchmarkScope": "CONTROLLED_EXECUTABLE_GEOMETRY_CONCEPT_GUIDED_PLANNING_NOT_OFFICIAL_ARC_AGI",
        "PythonEngine": str(PYTHON), "WolframEngine": r"E:\engine_wolf\math.exe",
        "PowerShellEngine": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "OracleBridgeEncodedCommand": encoded_bridge(),
        "FrozenConceptLibrarySHA256": digest(ROOT / "library" / "frozen_planning_concepts.json"),
        "FrozenGeometryLibrarySHA256": digest(ROOT / "source" / "adaptive_geometry.py"),
        "FrozenConceptDynamicProgrammingSHA256": digest(ROOT / "source" / "concept_dp.py"),
        "FrozenTaskBuilderSHA256": digest(ROOT / "source" / "build_concept_guided_tasks.py"),
        "FrozenWolframRunnerSHA256": digest(ROOT / "source" / "run_concept_guided_planning.wl"),
        "FrozenOracleResponderSHA256": digest(ROOT / "source" / "oracle_responder.py"),
        "FrozenConceptExtractorSHA256": digest(ROOT / "source" / "extract_historical_planning_concepts.py"),
        "FrozenPlanningAuditorSHA256": digest(ROOT / "diagnostic" / "prove_concept_planning.py"),
        "FrozenReplayLibrarySHA256": digest(ROOT / "source" / "concept_replay.py"),
        "FrozenScorerSHA256": digest(ROOT / "source" / "score_concept_guided.py"),
        "FrozenVerifierSHA256": digest(ROOT / "source" / "verify_concept_guided.py"),
        "FrozenPredecessorG3ProtocolSHA256": digest(PREDECESSOR / "protocol" / "frozen_protocol.json"),
        "FrozenPredecessorG3ResultSHA256": digest(PREDECESSOR / "results" / "kernel_adaptive_depth_result.json"),
        "FrozenPredecessorG3VerificationSHA256": digest(PREDECESSOR / "verification" / "independent_verification.json"),
        "CanonicalTCCTModified": False, "CoreRewriteFreezeDedupModified": False,
        "OfficialARCDataTouched": False, "ARCAGI2Claimed": False, "PDFRequested": False,
        "GateRequirements": {
            "ExactlyFiveFreshWorlds": True, "AllGuidedAndBaselineMinimumDepthsIdentical": True,
            "AllBudgetSolvableWorldsCommitExact": True, "DepthFourWorldSafelyRefused": True,
            "HistoricalConceptsStrictlyReduceAggregateDeterministicPlanningWork": True,
            "MismatchWorldExercisesCompleteFallbackAndRemainsExact": True,
            "ConceptsNeverPruneVersionSpace": True, "IndependentPythonReplaysNativeWolfram": True,
            "NoPostSeedFilteringOrReplacement": True, "CoreRewriteFreezeDedupUnchanged": True,
        },
    }
    destination = ROOT / "protocol" / "frozen_protocol.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"FrozenProtocol": True, "FreshTaskGeneratorSeed": seed,
                      "Path": str(destination)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
