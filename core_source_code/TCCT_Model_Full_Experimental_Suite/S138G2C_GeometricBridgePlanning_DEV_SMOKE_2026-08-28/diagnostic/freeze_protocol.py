from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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
    seed = int(os.environ.get("TCCT_PROTOCOL_SEED", "1389949"))
    dev = "TCCT_PROTOCOL_SEED" in os.environ
    protocol = {
        "Stage": ("S138-G2C DEV native smoke" if dev else
                  "S138-G2C CONFIRM R0 five fresh executable geometric depth-2 worlds"),
        "EvidenceStatus": ("DEVELOPMENT_ONLY" if dev else
                           "PROSPECTIVE_LOCAL_CONFIRMATORY_EXECUTABLE_GEOMETRY_DEPTH2_PLANNING"),
        "ProtocolFrozenBeforeTaskMaterialization": True,
        "AllLearnerSourcesFrozenBeforeTaskMaterialization": True,
        "FreshWorldsMaterializedAfterProtocolFreeze": True,
        "FreshTaskGeneratorSeed": seed,
        "TaskOrder": [f"GB{index:03d}" for index in range(1, 6)],
        "ExpectedGeometricTwoStepBridgeWorldCount": 3,
        "ExpectedGeometricIrreducibleControlCount": 2,
        "TaskRolesHiddenFromLearner": True,
        "MaximumActiveQueriesPerTask": 4,
        "MaximumActiveQueriesMeaning": "RESOURCE_SAFETY_CAP_ONLY_NOT_A_REQUIRED_QUERY_COUNT",
        "QueryCountPredeclaredAsCapabilityConstant": False,
        "ImmediateQueryAdmissionRule": "WORST_CASE_REMAINING_DECISION_CLASSES_STRICTLY_DECREASES",
        "BridgeQueryAdmissionRule": "NO_IMMEDIATE_QUERY_EXISTS_AND_DEPTH2_MINIMAX_STRICTLY_DECREASES_DECISION_CLASSES",
        "QuerySelectionPriority": "IMMEDIATE_GAIN_THEN_CERTIFIED_DEPTH2_BRIDGE_THEN_SAFE_ABSTENTION",
        "KernelInterventionGrammar": "CALIBRATION_CONTEXT_PROBE_PLUS_CONTEXT_CONDITIONAL_GEOMETRIC_DECISION_PROBE_PLUS_NUISANCE_PROBE",
        "PublicQueryPoolSize": 0,
        "InterventionsSynthesizedByKernel": True,
        "CandidateProgramGrammar": "CONTEXT_X_IDENTITY_OR_HORIZONTAL_OR_VERTICAL_REFLECTION_X_NUISANCE",
        "CandidateProgramsMustExecuteOnTrainingGrid": True,
        "DecisionQuotient": "EXACT_TEST_GRID_PREDICTION",
        "PostSeedWorldFilteringAllowed": False,
        "NoWorldReplacementAfterMaterialization": True,
        "FreshnessBoundary": "FRESH_ROLE_ORDER_CONTEXT_NUISANCE_HIDDEN_PROGRAM_COLOR_PLACEMENT_AND_UNIQUE_TEST_SHAPE_WITHIN_COHORT",
        "BenchmarkScope": "CONTROLLED_ARC_LIKE_EXECUTABLE_GEOMETRY_PLANNING_INTEGRATION_TEST_NOT_OFFICIAL_ARC_AGI",
        "PythonEngine": str(PYTHON), "WolframEngine": r"E:\engine_wolf\math.exe",
        "PowerShellEngine": "C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe",
        "OracleBridgeEncodedCommand": encoded_bridge(),
        "FrozenGeometryLibrarySHA256": digest(ROOT / "source" / "geometry_world.py"),
        "FrozenTaskBuilderSHA256": digest(ROOT / "source" / "build_geometric_bridge_tasks.py"),
        "FrozenWolframRunnerSHA256": digest(ROOT / "source" / "run_geometric_bridge_planning.wl"),
        "FrozenOracleResponderSHA256": digest(ROOT / "source" / "oracle_responder.py"),
        "FrozenDifficultyAuditorSHA256": digest(ROOT / "diagnostic" / "prove_geometric_bridge_difficulty.py"),
        "FrozenReplayLibrarySHA256": digest(ROOT / "source" / "geometric_replay.py"),
        "FrozenScorerSHA256": digest(ROOT / "source" / "score_geometric_bridge.py"),
        "FrozenVerifierSHA256": digest(ROOT / "source" / "verify_geometric_bridge.py"),
        "CanonicalTCCTModified": False, "CoreRewriteFreezeDedupModified": False,
        "OfficialARCDataTouched": False, "ARCAGI2Claimed": False, "PDFRequested": False,
        "GateRequirements": {
            "ExactlyFiveFreshWorldsEvaluated": True,
            "ExactlyThreeGeometricBridgeAndTwoIrreducibleControls": True,
            "PositiveWorldsHaveNoOneStepGainButCertifiedDepth2Gain": True,
            "PositiveWorldsCommitExactSealedGridAfterTwoQueries": True,
            "ControlsAbstainBeforeAnyOracleQuery": True,
            "AllCandidateProgramsExecuteTrainingExactly": True,
            "IndependentPythonReplayOfNativeWolframTrace": True,
            "NoPostSeedFilteringOrWorldReplacement": True,
            "CoreRewriteFreezeAndDedupUnchanged": True,
        },
    }
    destination = ROOT / "protocol" / "frozen_protocol.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"FrozenProtocol": True, "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
                      "Path": str(destination)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
