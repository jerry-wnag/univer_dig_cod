<|"Stage" -> "S125-C-Pilot5", "Completed" -> True, "RunIndex" -> 2, 
 "WorldSeed" -> 1258502, "BaseSourceSHA256" -> 
  "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
 "ManifestSHA256" -> 
  "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
 "GeneratedSourceSHA256" -> 
  "c3b1c80c1b115d4155fa2a700be7875fbc45ade4e628b4620230d266097f53b1", 
 "ProcessExitCode" -> 0, "ElapsedSeconds" -> 597.7494209, 
 "RunPassed" -> True, "Checks" -> <|"ProcessExitCodeZero" -> True, 
   "NoFatalMarker" -> True, "PilotProtocolPass" -> True, 
   "StrictProspective" -> True, "SharedPerception" -> True, 
   "MaximumTrainingInteractionOrderTwo" -> True, 
   "NoHighOrderLeakage" -> True, "PreWorldProtocolHashPresent" -> True, 
   "ManifestEchoMatches" -> True, "BaseSourceEchoMatches" -> True|>, 
 "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
    "True", "FreshWorldSeed" -> "1258502", "SharedPerception" -> "True", 
   "PreWorldProtocolHash" -> 
    "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\"", 
   "PerceptionValidationAccuracy" -> "1.", 
   "TrainingMembershipPerceptionAccuracy" -> "1.", 
   "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
   "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> "0", 
   "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 5, 3, 2}", 
   "LearnedInteractionEdges" -> "{3 -> 1, 4 -> 2}", 
   "ConditionalTransitionCells" -> "41", "MembershipQueriesBeforeFreeze" -> 
    "1836", "ReasonValidationAccuracy" -> "0.8181818181818182", 
   "ReasonValidationBalancedAccuracy" -> "0.7209346929642297", 
   "FinalReasonTrainingAccuracy" -> "0.8393246187363834", 
   "FinalReasonTrainingBalancedAccuracy" -> "0.7342685415685483", 
   "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
    "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> "1.", 
   "NeuralProbeAccuracy" -> "0.5752895752895753", 
   "NeuralZeroAccuracy" -> "0.7297297297297297", 
   "NeuralOneAccuracy" -> "0.1891891891891892", "NeuralBalancedAccuracy" -> 
    "0.45945945945945943", "HighOrderTransitionCases" -> "592", 
   "TCCTTransitionExactAccuracy" -> "1.", "NeuralTransitionExactAccuracy" -> 
    "0.", "TCCTTransitionProbeAccuracy" -> "1.", 
   "NeuralTransitionProbeAccuracy" -> "0.582046332046332", 
   "NeuralTransitionZeroAccuracy" -> "0.7207770270270271", 
   "NeuralTransitionOneAccuracy" -> "0.2352195945945946", 
   "NeuralTransitionBalancedAccuracy" -> "0.47799831081081084", 
   "TCCTMinusNeuralExact" -> "1.", "TCCTMinusNeuralProbe" -> 
    "0.42471042471042475", "TCCTMinusNeuralTransitionExact" -> "1.", 
   "WinnerMargin" -> "0.02", "StrictProtocolPass" -> "True", 
   "GeneralizationDiagnosis" -> 
    "\"STRICT_FRESH_WORLD_TCCT_HIGH_ORDER_GENERALIZATION_ADVANTAGE\"", 
   "TCCTFreezeHash" -> 
    "\"002c0bbf05e8435ec50ddffeff0d035d95c16b79e5a588bd4f67cf85d2646e01\"", 
   "GlobalFreezeHash" -> 
    "\"2e6f5f858f45791dc732b3af9ed777503a0a3321d81dcab6c169c4a44cafc08f\"", 
   "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
   "Protocol" -> "\"MultiRestartMatchedAndStrongTransformerComparison\"", 
   "MatchedRestartSpec" -> "<|\"SelectionSeeds\" -> {1258611, 1258612, \
1258613}, \"FinalSeeds\" -> {1258621, 1258622, 1258623}, \"SelectionMetric\" \
-> \"LowOrderValidationBalancedAccuracy\", \"FinalMetric\" -> \
\"LowOrderTrainingBalancedAccuracy\", \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"HighOrderUsedForSelection\" -> False, \
\"ArchitectureChanged\" -> False|>", "MatchedSelectionCandidateMetrics" -> "{\
<|\"Seed\" -> 1258611, \"ValidationAccuracy\" -> 0.8181818181818182, \
\"ValidationBalancedAccuracy\" -> 0.7209346929642297|>, <|\"Seed\" -> \
1258612, \"ValidationAccuracy\" -> 0.8207070707070707, \
\"ValidationBalancedAccuracy\" -> 0.6913819007128472|>, <|\"Seed\" -> \
1258613, \"ValidationAccuracy\" -> 0.8358585858585859, \
\"ValidationBalancedAccuracy\" -> 0.7160598408081067|>}", 
   "MatchedFinalCandidateMetrics" -> "{<|\"Seed\" -> 1258621, \
\"TrainingAccuracy\" -> 0.8393246187363834, \"TrainingBalancedAccuracy\" -> \
0.7342685415685483|>, <|\"Seed\" -> 1258622, \"TrainingAccuracy\" -> \
0.8453159041394336, \"TrainingBalancedAccuracy\" -> 0.7234250599923748|>, \
<|\"Seed\" -> 1258623, \"TrainingAccuracy\" -> 0.8338779956427015, \
\"TrainingBalancedAccuracy\" -> 0.7062078091008993|>}", 
   "MatchedSelectedSelectionSeed" -> "1258611", "MatchedSelectedFinalSeed" -> 
    "1258621", "ExpectedConditionalTransitionCells" -> "41", 
   "MatchedReasonParameterCount" -> "85890", "StrongReasonParameterCount" -> 
    "339170", "StrongReasonSpec" -> "<|\"DModel\" -> 96, \"Heads\" -> 4, \
\"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> 0.1, \"LearningRate\" -> \
0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \"Patience\" -> 6, \
\"ValidationBalancedGate\" -> 0.6, \"TrainingBalancedGate\" -> 0.7, \
\"SelectSeed\" -> 1258102, \"FinalSeed\" -> 1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
   "StrongReasonValidationAccuracy" -> "0.8484848484848485", 
   "StrongReasonValidationBalancedAccuracy" -> "0.7503756033628488", 
   "StrongFinalReasonTrainingAccuracy" -> "0.8632897603485838", 
   "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7738164121195811", 
   "StrongReasonFreezeFileHash" -> 
    "\"b65ac15f06fec4eb0e193c3aa143265aeb19077564e7a272bd382ff33bc61afc\"", 
   "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
   "StrongProbeAccuracy" -> "0.6496138996138996", 
   "StrongProbeZeroAccuracy" -> "0.8297297297297297", 
   "StrongProbeOneAccuracy" -> "0.19932432432432431", 
   "StrongProbeBalancedAccuracy" -> "0.514527027027027", 
   "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> "0.", 
   "StrongTransitionProbeAccuracy" -> "0.6463561776061776", 
   "StrongTransitionZeroAccuracy" -> "0.8216216216216217", 
   "StrongTransitionOneAccuracy" -> "0.20819256756756757", 
   "StrongTransitionBalancedAccuracy" -> "0.5149070945945946", 
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
eline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_02_\
seed_1258502\\S125C_generated_multirestart_comparison_seed_1258502.wl", 
 "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutBase\
line_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_02_s\
eed_1258502\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HANDOF\
F_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_MultiRes\
tartMatched_Output\\world_02_seed_1258502\\S125C_stderr.log"|>
