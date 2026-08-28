from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = ROOT.parent / "S138G4_ConceptGuidedPlanning_CONFIRM_R0_2026-08-28"
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
    seed = int(os.environ.get("TCCT_PROTOCOL_SEED", "1391837"))
    dev = "TCCT_PROTOCOL_SEED" in os.environ
    source_files = {
        "FrozenGeometrySHA256": ROOT / "source" / "adaptive_geometry.py",
        "FrozenConceptDPSHA256": ROOT / "source" / "kernel_concept_dp.py",
        "FrozenTaskBuilderSHA256": ROOT / "source" / "build_kernel_concept_tasks.py",
        "FrozenWolframRunnerSHA256": ROOT / "source" / "run_kernel_concept_formation.wl",
        "FrozenOracleResponderSHA256": ROOT / "source" / "oracle_responder.py",
        "FrozenAuditorSHA256": ROOT / "diagnostic" / "prove_kernel_concept_formation.py",
        "FrozenScorerSHA256": ROOT / "source" / "score_kernel_concept_formation.py",
        "FrozenVerifierSHA256": ROOT / "source" / "verify_kernel_concept_formation.py",
    }
    protocol = {
        "Stage": "S139-A DEV R3 native smoke" if dev else
                 "S139-A CONFIRM R3 kernel-native relational planning concept formation",
        "EvidenceStatus": "DEVELOPMENT_ONLY" if dev else
                          "PROSPECTIVE_LOCAL_CONFIRMATORY_KERNEL_CONCEPT_FORMATION",
        "ProtocolFrozenBeforeTaskMaterialization": True,
        "AllLearnerAndInductionSourcesFrozenBeforeTaskMaterialization": True,
        "FreshTasksMaterializedAfterProtocolFreeze": True,
        "FreshTaskGeneratorSeed": seed,
        "SourceTaskOrder": ["SRC001", "SRC002", "SRC003"],
        "TargetTaskIDs": [f"KT{index:03d}" for index in range(1, 6)],
        "MaximumPlanningDepth": 3, "MaximumActiveQueriesPerTask": 3,
        "ConceptFormationLocation": "NATIVE_WOLFRAM_KERNEL_DURING_RUN",
        "ConceptHypothesisLanguage": "FINITE_RELATIONAL_CONJUNCTION_DSL_WITH_PLANNING_DEPTH_PREDICATES",
        "ConceptInduction": "ZERO_TRAINING_FALSE_POSITIVE_MDL_ORDERED_SET_COVER",
        "ConceptMinimumSupportEvents": 2, "ConceptMinimumDistinctSourceTasks": 2,
        "ConceptRole": "QUERY_ORDERING_ONLY",
        "ConceptMayPruneModels": False, "ConceptMaySuppressFallbackQueries": False,
        "Fallback": "COMPLETE_HASH_ORDERED_ITERATIVE_DEEPENING_DYNAMIC_PROGRAMMING",
        "PairedBaseline": "SAME_VERSION_SPACE_SAME_DEPTH_CAP_CONCEPTS_DISABLED",
        "FormalTargetWorldCount": 5, "SourceCurriculumWorldCount": 3,
        "PostSeedWorldFilteringAllowed": False, "NoWorldReplacementAfterMaterialization": True,
        "PublicQueryPoolSize": 0, "InterventionsSynthesizedByKernel": True,
        "OpenEndedConceptLanguageClaimed": False,
        "BenchmarkScope": "CONTROLLED_EXECUTABLE_GEOMETRY_NOT_OFFICIAL_ARC_AGI",
        "PythonEngine": str(PYTHON), "WolframEngine": r"E:\engine_wolf\math.exe",
        "PowerShellEngine": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "OracleBridgeEncodedCommand": encoded_bridge(),
        **{key: digest(path) for key, path in source_files.items()},
        "FrozenPredecessorProtocolSHA256": digest(PREDECESSOR / "protocol" / "frozen_protocol.json"),
        "FrozenPredecessorVerificationSHA256": digest(PREDECESSOR / "verification" / "independent_verification.json"),
        "CanonicalTCCTModified": False, "CoreRewriteFreezeDedupModified": False,
        "OfficialARCDataTouched": False, "ARCAGI2Claimed": False, "PDFRequested": False,
        "GateRequirements": {
            "ExactlyThreeSourceAndFiveFreshTargetWorlds": True,
            "ConceptBodiesCreatedOnlyByNativeKernel": True,
            "EveryConceptHasTwoEventsAndTwoSourceTasks": True,
            "ZeroTrainingFalsePositiveConcepts": True,
            "AllFiveTargetAnswersExact": True,
            "AllGuidedAndBaselineMinimumDepthsIdentical": True,
            "SurfaceScaleAndSequentialTransferPass": True,
            "AdversarialPreferredConceptRejectedByExactDP": True,
            "NoReusableConceptWorldUsesCompleteFallback": True,
            "IndependentPythonReproducesConceptsAndNativeResults": True,
            "NoPostSeedFilteringOrReplacement": True,
            "CoreRewriteFreezeDedupUnchanged": True,
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
