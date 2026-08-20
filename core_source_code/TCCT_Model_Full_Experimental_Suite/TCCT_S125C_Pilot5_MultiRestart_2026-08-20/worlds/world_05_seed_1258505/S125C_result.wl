<|"Stage" -> "S125-C-Pilot5", "Completed" -> True, "RunIndex" -> 5, 
 "WorldSeed" -> 1258505, "BaseSourceSHA256" -> 
  "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
 "ManifestSHA256" -> 
  "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
 "GeneratedSourceSHA256" -> 
  "bb830cec1e5a08d150bd0ac094c3f6c2a675183b6d4f336d08a2332db0667c75", 
 "ProcessExitCode" -> 0, "ElapsedSeconds" -> 581.2770719, 
 "RunPassed" -> True, "Checks" -> <|"ProcessExitCodeZero" -> True, 
   "NoFatalMarker" -> True, "PilotProtocolPass" -> True, 
   "StrictProspective" -> True, "SharedPerception" -> True, 
   "MaximumTrainingInteractionOrderTwo" -> True, 
   "NoHighOrderLeakage" -> True, "PreWorldProtocolHashPresent" -> True, 
   "ManifestEchoMatches" -> True, "BaseSourceEchoMatches" -> True|>, 
 "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
    "True", "FreshWorldSeed" -> "1258505", "SharedPerception" -> "True", 
   "PreWorldProtocolHash" -> 
    "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\"", 
   "PerceptionValidationAccuracy" -> "1.", 
   "TrainingMembershipPerceptionAccuracy" -> "1.", 
   "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
   "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> "0", 
   "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 3, 5, 2}", 
   "LearnedInteractionEdges" -> "{4 -> 3, 2 -> 1}", 
   "ConditionalTransitionCells" -> "41", "MembershipQueriesBeforeFreeze" -> 
    "1846", "ReasonValidationAccuracy" -> "0.8199513381995134", 
   "ReasonValidationBalancedAccuracy" -> "0.7165171942745144", 
   "FinalReasonTrainingAccuracy" -> "0.8369447453954496", 
   "FinalReasonTrainingBalancedAccuracy" -> "0.7250428923110629", 
   "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
    "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> "1.", 
   "NeuralProbeAccuracy" -> "0.5588803088803089", 
   "NeuralZeroAccuracy" -> "0.7108108108108108", 
   "NeuralOneAccuracy" -> "0.17905405405405406", "NeuralBalancedAccuracy" -> 
    "0.4449324324324324", "HighOrderTransitionCases" -> "592", 
   "TCCTTransitionExactAccuracy" -> "1.", "NeuralTransitionExactAccuracy" -> 
    "0.", "TCCTTransitionProbeAccuracy" -> "1.", 
   "NeuralTransitionProbeAccuracy" -> "0.5793918918918919", 
   "NeuralTransitionZeroAccuracy" -> "0.7189189189189189", 
   "NeuralTransitionOneAccuracy" -> "0.23057432432432431", 
   "NeuralTransitionBalancedAccuracy" -> "0.4747466216216216", 
   "TCCTMinusNeuralExact" -> "1.", "TCCTMinusNeuralProbe" -> 
    "0.44111969111969107", "TCCTMinusNeuralTransitionExact" -> "1.", 
   "WinnerMargin" -> "0.02", "StrictProtocolPass" -> "True", 
   "GeneralizationDiagnosis" -> 
    "\"STRICT_FRESH_WORLD_TCCT_HIGH_ORDER_GENERALIZATION_ADVANTAGE\"", 
   "TCCTFreezeHash" -> 
    "\"9d7b85a3060dc1f1a805cefc291d9e2aa2c541aa61552608e9a0da46d6f3b3eb\"", 
   "GlobalFreezeHash" -> 
    "\"fb88ad5f1df8036c85149c49d1360d0a7378258bf6518d5745e1e2c5ce751c13\"", 
   "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
   "Protocol" -> "\"MultiRestartMatchedAndStrongTransformerComparison\"", 
   "MatchedRestartSpec" -> "<|\"SelectionSeeds\" -> {1258611, 1258612, \
1258613}, \"FinalSeeds\" -> {1258621, 1258622, 1258623}, \"SelectionMetric\" \
-> \"LowOrderValidationBalancedAccuracy\", \"FinalMetric\" -> \
\"LowOrderTrainingBalancedAccuracy\", \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"HighOrderUsedForSelection\" -> False, \
\"ArchitectureChanged\" -> False|>", "MatchedSelectionCandidateMetrics" -> "{\
<|\"Seed\" -> 1258611, \"ValidationAccuracy\" -> 0.8223844282238443, \
\"ValidationBalancedAccuracy\" -> 0.7127011937993705|>, <|\"Seed\" -> \
1258612, \"ValidationAccuracy\" -> 0.8199513381995134, \
\"ValidationBalancedAccuracy\" -> 0.7165171942745144|>, <|\"Seed\" -> \
1258613, \"ValidationAccuracy\" -> 0.8223844282238443, \
\"ValidationBalancedAccuracy\" -> 0.7099542673873017|>}", 
   "MatchedFinalCandidateMetrics" -> "{<|\"Seed\" -> 1258621, \
\"TrainingAccuracy\" -> 0.8407367280606717, \"TrainingBalancedAccuracy\" -> \
0.7232968532809102|>, <|\"Seed\" -> 1258622, \"TrainingAccuracy\" -> \
0.8374864572047671, \"TrainingBalancedAccuracy\" -> 0.7104935539406895|>, \
<|\"Seed\" -> 1258623, \"TrainingAccuracy\" -> 0.8369447453954496, \
\"TrainingBalancedAccuracy\" -> 0.7250428923110629|>}", 
   "MatchedSelectedSelectionSeed" -> "1258612", "MatchedSelectedFinalSeed" -> 
    "1258623", "ExpectedConditionalTransitionCells" -> "41", 
   "MatchedReasonParameterCount" -> "85890", "StrongReasonParameterCount" -> 
    "339170", "StrongReasonSpec" -> "<|\"DModel\" -> 96, \"Heads\" -> 4, \
\"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> 0.1, \"LearningRate\" -> \
0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \"Patience\" -> 6, \
\"ValidationBalancedGate\" -> 0.6, \"TrainingBalancedGate\" -> 0.7, \
\"SelectSeed\" -> 1258102, \"FinalSeed\" -> 1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
   "StrongReasonValidationAccuracy" -> "0.8126520681265207", 
   "StrongReasonValidationBalancedAccuracy" -> "0.7169774900516719", 
   "StrongFinalReasonTrainingAccuracy" -> "0.8613217768147345", 
   "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7629354180205439", 
   "StrongReasonFreezeFileHash" -> 
    "\"12dde7b246b59afda32213855c7a597690726b115fb5bdfb714b0f1a87c0870d\"", 
   "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
   "StrongProbeAccuracy" -> "0.640926640926641", "StrongProbeZeroAccuracy" -> 
    "0.8297297297297297", "StrongProbeOneAccuracy" -> "0.16891891891891891", 
   "StrongProbeBalancedAccuracy" -> "0.4993243243243243", 
   "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> "0.", 
   "StrongTransitionProbeAccuracy" -> "0.6558880308880309", 
   "StrongTransitionZeroAccuracy" -> "0.8388513513513514", 
   "StrongTransitionOneAccuracy" -> "0.19847972972972974", 
   "StrongTransitionBalancedAccuracy" -> "0.5186655405405406", 
   "BestNeuralStateExactAccuracy" -> "0.", 
   "BestNeuralTransitionExactAccuracy" -> "0.", 
   "TCCTMinusBestNeuralStateExact" -> "1.", 
   "TCCTMinusBestNeuralTransitionExact" -> "1.", 
   "PilotProtocolPass" -> "True", "PilotOutcome" -> 
    "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
   "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
    "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
   "S125BaseSourceSHA256" -> 
    "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
 "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutBas\
eline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_05_\
seed_1258505\\S125C_generated_multirestart_comparison_seed_1258505.wl", 
 "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutBase\
line_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_05_s\
eed_1258505\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HANDOF\
F_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_MultiRes\
tartMatched_Output\\world_05_seed_1258505\\S125C_stderr.log"|>
