from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    protocol = json.loads(
        (ROOT / "predecessor_s138g" / "frozen_protocol_s138g.json").read_text(
            encoding="utf-8"
        )
    )
    task_ids = [f"ASR{index:03d}" for index in range(1, 6)]
    protocol.update(
        {
            "Stage": "S138-G1 CONFIRM R0 five fresh adaptive safe-refusal traps",
            "EvidenceStatus": "PROSPECTIVE_LOCAL_CONFIRMATORY_ADAPTIVE_SAFE_REFUSAL",
            "ProtocolFrozenBeforeTaskMaterialization": True,
            "AllLearnerSourcesFrozenBeforeTaskMaterialization": True,
            "FreshWorldsMaterializedAfterProtocolFreeze": True,
            "FreshTaskGeneratorSeed": 1389817,
            "TaskGeneratorSeed": 1389817,
            "TaskConstruction": "DUAL_AXIS_SYMMETRIC_TRAIN_AND_ALLOWED_INTERVENTIONS_WITH_DUAL_AXIS_ASYMMETRIC_TEST",
            "TaskOrder": task_ids,
            "DiscoveryTaskIDs": [],
            "TransferTaskIDs": [],
            "ControlTaskIDs": task_ids,
            "ActiveTaskIDs": task_ids,
            "FixedDiscoveryCohortSize": 0,
            "MinimumDiscoveryInterventionOpportunityCount": 0,
            "MaximumActiveQueriesPerTask": 400,
            "MaximumActiveQueriesMeaning": "RESOURCE_SAFETY_CAP_ONLY_NOT_A_REQUIRED_QUERY_COUNT",
            "QueryCountPredeclaredAsCapabilityConstant": False,
            "AdaptiveStoppingRule": "QUERY_ONLY_WHILE_A_FROZEN_ALLOWED_INTERVENTION_STRICTLY_REDUCES_WORST_CASE_DECISION_CLASSES_THEN_REFUSE_WHEN_NONE_REMAINS",
            "AdaptiveSafeRefusalDefinition": "FINAL_DECISION_CLASSES_GT_1_AND_ZERO_REMAINING_INFORMATIVE_INTERVENTIONS_AND_NO_TEST_COMMIT",
            "StrictQueryGainRequirement": "EVERY_SELECTED_QUERY_HAS_WORST_CASE_DECISION_CLASS_COUNT_STRICTLY_BELOW_ITS_PRE_QUERY_COUNT_AND_ACTUAL_POST_QUERY_COUNT_STRICTLY_DECREASES",
            "FinalInformationExhaustionRequirement": "ZERO_REMAINING_INFORMATIVE_INTERVENTIONS_WITH_AT_LEAST_ONE_UNUSED_ALLOWED_INTERVENTION",
            "MinimumTasksRequiringUsefulAdaptiveQueries": 3,
            "UnnecessaryQueryRequirement": "EVERY_ORACLE_QUERY_MUST_STRICTLY_REDUCE_THE_DECISION_VERSION_SPACE",
            "KernelInterventionSamplingPolicy": "400_DOUBLE_AXIS_SYMMETRIC_SUPPORT_TRAP_INPUTS_HASH_ORDERED",
            "SupportTrapDoubleNeutralQuota": 400,
            "LearnerVisibleDifficultyAxisCount": 0,
            "PublicDifficultyAxisForbidden": True,
            "ExpectedInventedConceptCount": 0,
            "ConceptLibraryIsCapabilityGate": False,
            "PostSeedWorldFilteringAllowed": False,
            "NoWorldReplacementAfterMaterialization": True,
            "FrozenTaskBuilderSHA256": digest(
                ROOT / "source" / "build_adaptive_safe_refusal_tasks.py"
            ),
            "FrozenWolframRunnerSHA256": digest(
                ROOT / "source" / "run_adaptive_safe_refusal.wl"
            ),
            "FrozenOracleResponderSHA256": digest(ROOT / "source" / "oracle_responder.py"),
            "FrozenDifficultyAuditorSHA256": digest(
                ROOT / "diagnostic" / "prove_adaptive_support_trap.py"
            ),
            "FrozenScorerSHA256": digest(
                ROOT / "source" / "score_adaptive_safe_refusal.py"
            ),
            "FrozenVerifierSHA256": digest(
                ROOT / "source" / "verify_adaptive_safe_refusal.py"
            ),
            "FrozenPredecessorS138FProtocolSHA256": digest(
                ROOT / "predecessor_s138f" / "frozen_protocol_s138f.json"
            ),
            "FrozenPredecessorS138FTestOutputsSHA256": digest(
                ROOT / "predecessor_s138f" / "test_outputs_s138f.json"
            ),
            "FrozenPredecessorS138GProtocolSHA256": digest(
                ROOT / "predecessor_s138g" / "frozen_protocol_s138g.json"
            ),
            "FrozenPredecessorS138GTestOutputsSHA256": digest(
                ROOT / "predecessor_s138g" / "test_outputs_s138g.json"
            ),
            "CanonicalTCCTModified": False,
            "CoreRewriteFreezeDedupModified": False,
            "OfficialARCDataTouched": False,
            "ARCAGI2Claimed": False,
            "PDFRequested": False,
        }
    )
    protocol["GateRequirements"] = {
        "ExactlyFiveFreshSupportTrapControlsEvaluated": True,
        "NoPublicDifficultyAxis": True,
        "EveryAllowedInterventionPreservesBothAxesForTheStructuralTrio": True,
        "IdentityHorizontalVerticalPredictionsIdenticalOnAllAllowedInterventions": True,
        "IdentityHorizontalVerticalPredictionsDistinctOnEveryTest": True,
        "EveryTaskRetainsMultipleDecisionClasses": True,
        "AtLeastThreeTasksRequireUsefulAdaptiveQueries": True,
        "EverySelectedQueryStrictlyReducesDecisionClasses": True,
        "EverySelectedQueryHasStrictWorstCaseDecisionGain": True,
        "EveryTaskEndsWithZeroRemainingInformativeInterventions": True,
        "EveryTaskStopsBeforeExhaustingTheAllowedUniverse": True,
        "EveryTaskSafelyRefusesToCommit": True,
        "EveryStopReasonIsNoInformativeQuery": True,
        "NoConceptFreeze": True,
        "NoPostSeedFilteringOrWorldReplacement": True,
        "CoreRewriteFreezeAndDedupUnchanged": True,
    }
    destination = ROOT / "protocol" / "frozen_protocol.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(protocol, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "FrozenProtocol": True,
                "FreshTaskGeneratorSeed": protocol["FreshTaskGeneratorSeed"],
                "Path": str(destination),
            },
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
