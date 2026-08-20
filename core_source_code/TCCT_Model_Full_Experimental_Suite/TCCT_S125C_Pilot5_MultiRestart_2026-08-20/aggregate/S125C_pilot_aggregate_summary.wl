<|"Stage" -> "S125-C-Pilot5", "Protocol" -> 
  "MultiRestartMatchedAndStrongTransformerComparison", 
 "BaseSourceSHA256" -> 
  "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
 "ManifestSHA256" -> 
  "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
 "WorldCount" -> 5, "CompletedWorlds" -> 5, "PilotPassedWorlds" -> 5, 
 "PilotFailedWorlds" -> 0, "PilotProtocolPassRate" -> 1., 
 "RequiredPassRate" -> 1., "PreWorldProtocolHashes" -> 
  {"\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""}, 
 "PreWorldProtocolHashStable" -> True, "ExecutionComplete" -> True, 
 "S125COverallPass" -> True, "Results" -> 
  {<|"Stage" -> "S125-C-Pilot5", "Completed" -> True, "RunIndex" -> 1, 
    "WorldSeed" -> 1258501, "BaseSourceSHA256" -> 
     "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
    "ManifestSHA256" -> 
     "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
    "GeneratedSourceSHA256" -> 
     "29fe516ed2d2e7a694d87d1c3447e5ed7af65fd2b3338ed275ef12753d239d0a", 
    "ProcessExitCode" -> 0, "ElapsedSeconds" -> 584.2998225, 
    "RunPassed" -> True, "Checks" -> <|"ProcessExitCodeZero" -> True, 
      "NoFatalMarker" -> True, "PilotProtocolPass" -> True, 
      "StrictProspective" -> True, "SharedPerception" -> True, 
      "MaximumTrainingInteractionOrderTwo" -> True, "NoHighOrderLeakage" -> 
       True, "PreWorldProtocolHashPresent" -> True, "ManifestEchoMatches" -> 
       True, "BaseSourceEchoMatches" -> True|>, 
    "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
       "True", "FreshWorldSeed" -> "1258501", "SharedPerception" -> "True", 
      "PreWorldProtocolHash" -> 
       "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""\
, "PerceptionValidationAccuracy" -> "1.", 
      "TrainingMembershipPerceptionAccuracy" -> "1.", 
      "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
      "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> 
       "0", "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 5, 3, 2}", 
      "LearnedInteractionEdges" -> "{4 -> 1, 3 -> 2}", 
      "ConditionalTransitionCells" -> "42", 
      "MembershipQueriesBeforeFreeze" -> "1842", 
      "ReasonValidationAccuracy" -> "0.8337182448036952", 
      "ReasonValidationBalancedAccuracy" -> "0.7293650793650794", 
      "FinalReasonTrainingAccuracy" -> "0.8447339847991314", 
      "FinalReasonTrainingBalancedAccuracy" -> "0.722614021525837", 
      "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
       "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> 
       "1.", "NeuralProbeAccuracy" -> "0.5781853281853282", 
      "NeuralZeroAccuracy" -> "0.7418918918918919", "NeuralOneAccuracy" -> 
       "0.16891891891891891", "NeuralBalancedAccuracy" -> 
       "0.4554054054054054", "HighOrderTransitionCases" -> "592", 
      "TCCTTransitionExactAccuracy" -> "1.", 
      "NeuralTransitionExactAccuracy" -> "0.", 
      "TCCTTransitionProbeAccuracy" -> "1.", 
      "NeuralTransitionProbeAccuracy" -> "0.589527027027027", 
      "NeuralTransitionZeroAccuracy" -> "0.7452702702702703", 
      "NeuralTransitionOneAccuracy" -> "0.20016891891891891", 
      "NeuralTransitionBalancedAccuracy" -> "0.47271959459459456", 
      "TCCTMinusNeuralExact" -> "1.", "TCCTMinusNeuralProbe" -> 
       "0.4218146718146718", "TCCTMinusNeuralTransitionExact" -> "1.", 
      "WinnerMargin" -> "0.02", "StrictProtocolPass" -> "True", 
      "GeneralizationDiagnosis" -> 
       "\"STRICT_FRESH_WORLD_TCCT_HIGH_ORDER_GENERALIZATION_ADVANTAGE\"", 
      "TCCTFreezeHash" -> 
       "\"5fe1bca879cfdbfee3429c5258d4538a5d94a86d03fd1de3c582cdda187b7763\""\
, "GlobalFreezeHash" -> 
       "\"e0b782b6757c6ac3bf2ab65f5381c064333edbd095225ad99559b3abbfa30943\""\
, "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
      "Protocol" -> "\"MultiRestartMatchedAndStrongTransformerComparison\"", 
      "MatchedRestartSpec" -> "<|\"SelectionSeeds\" -> {1258611, 1258612, \
1258613}, \"FinalSeeds\" -> {1258621, 1258622, 1258623}, \"SelectionMetric\" \
-> \"LowOrderValidationBalancedAccuracy\", \"FinalMetric\" -> \
\"LowOrderTrainingBalancedAccuracy\", \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"HighOrderUsedForSelection\" -> False, \
\"ArchitectureChanged\" -> False|>", "MatchedSelectionCandidateMetrics" -> "{\
<|\"Seed\" -> 1258611, \"ValidationAccuracy\" -> 0.8244803695150116, \
\"ValidationBalancedAccuracy\" -> 0.7097659402744149|>, <|\"Seed\" -> \
1258612, \"ValidationAccuracy\" -> 0.8337182448036952, \
\"ValidationBalancedAccuracy\" -> 0.7293650793650794|>, <|\"Seed\" -> \
1258613, \"ValidationAccuracy\" -> 0.8221709006928406, \
\"ValidationBalancedAccuracy\" -> 0.694928705945655|>}", 
      "MatchedFinalCandidateMetrics" -> "{<|\"Seed\" -> 1258621, \
\"TrainingAccuracy\" -> 0.8452768729641694, \"TrainingBalancedAccuracy\" -> \
0.7217413926384016|>, <|\"Seed\" -> 1258622, \"TrainingAccuracy\" -> \
0.8447339847991314, \"TrainingBalancedAccuracy\" -> 0.722614021525837|>, \
<|\"Seed\" -> 1258623, \"TrainingAccuracy\" -> 0.8447339847991314, \
\"TrainingBalancedAccuracy\" -> 0.7207453767021467|>}", 
      "MatchedSelectedSelectionSeed" -> "1258612", 
      "MatchedSelectedFinalSeed" -> "1258622", 
      "ExpectedConditionalTransitionCells" -> "42", 
      "MatchedReasonParameterCount" -> "85890", 
      "StrongReasonParameterCount" -> "339170", "StrongReasonSpec" -> "<|\"DM\
odel\" -> 96, \"Heads\" -> 4, \"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> \
0.1, \"LearningRate\" -> 0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \
\"Patience\" -> 6, \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"SelectSeed\" -> 1258102, \"FinalSeed\" -> \
1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
      "StrongReasonValidationAccuracy" -> "0.8406466512702079", 
      "StrongReasonValidationBalancedAccuracy" -> "0.7341269841269842", 
      "StrongFinalReasonTrainingAccuracy" -> "0.8648208469055375", 
      "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7700555985015163", 
      "StrongReasonFreezeFileHash" -> 
       "\"84a8c83877cb9b0ec901cebacbdc642aced05ef6853e211376940b02d88f32f2\""\
, "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
      "StrongProbeAccuracy" -> "0.5666023166023166", 
      "StrongProbeZeroAccuracy" -> "0.7256756756756757", 
      "StrongProbeOneAccuracy" -> "0.16891891891891891", 
      "StrongProbeBalancedAccuracy" -> "0.4472972972972973", 
      "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> 
       "0.", "StrongTransitionProbeAccuracy" -> "0.5897683397683398", 
      "StrongTransitionZeroAccuracy" -> "0.7383445945945946", 
      "StrongTransitionOneAccuracy" -> "0.21832770270270271", 
      "StrongTransitionBalancedAccuracy" -> "0.47833614864864865", 
      "BestNeuralStateExactAccuracy" -> "0.", 
      "BestNeuralTransitionExactAccuracy" -> "0.", 
      "TCCTMinusBestNeuralStateExact" -> "1.", 
      "TCCTMinusBestNeuralTransitionExact" -> "1.", "PilotProtocolPass" -> 
       "True", "PilotOutcome" -> 
       "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
      "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
       "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
      "S125BaseSourceSHA256" -> 
       "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
    "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_Readout\
Baseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_\
01_seed_1258501\\S125C_generated_multirestart_comparison_seed_1258501.wl", 
    "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutB\
aseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_0\
1_seed_1258501\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HAN\
DOFF_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_Multi\
RestartMatched_Output\\world_01_seed_1258501\\S125C_stderr.log"|>, 
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
      "MaximumTrainingInteractionOrderTwo" -> True, "NoHighOrderLeakage" -> 
       True, "PreWorldProtocolHashPresent" -> True, "ManifestEchoMatches" -> 
       True, "BaseSourceEchoMatches" -> True|>, 
    "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
       "True", "FreshWorldSeed" -> "1258502", "SharedPerception" -> "True", 
      "PreWorldProtocolHash" -> 
       "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""\
, "PerceptionValidationAccuracy" -> "1.", 
      "TrainingMembershipPerceptionAccuracy" -> "1.", 
      "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
      "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> 
       "0", "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 5, 3, 2}", 
      "LearnedInteractionEdges" -> "{3 -> 1, 4 -> 2}", 
      "ConditionalTransitionCells" -> "41", 
      "MembershipQueriesBeforeFreeze" -> "1836", 
      "ReasonValidationAccuracy" -> "0.8181818181818182", 
      "ReasonValidationBalancedAccuracy" -> "0.7209346929642297", 
      "FinalReasonTrainingAccuracy" -> "0.8393246187363834", 
      "FinalReasonTrainingBalancedAccuracy" -> "0.7342685415685483", 
      "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
       "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> 
       "1.", "NeuralProbeAccuracy" -> "0.5752895752895753", 
      "NeuralZeroAccuracy" -> "0.7297297297297297", "NeuralOneAccuracy" -> 
       "0.1891891891891892", "NeuralBalancedAccuracy" -> 
       "0.45945945945945943", "HighOrderTransitionCases" -> "592", 
      "TCCTTransitionExactAccuracy" -> "1.", 
      "NeuralTransitionExactAccuracy" -> "0.", 
      "TCCTTransitionProbeAccuracy" -> "1.", 
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
       "\"002c0bbf05e8435ec50ddffeff0d035d95c16b79e5a588bd4f67cf85d2646e01\""\
, "GlobalFreezeHash" -> 
       "\"2e6f5f858f45791dc732b3af9ed777503a0a3321d81dcab6c169c4a44cafc08f\""\
, "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
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
      "MatchedSelectedSelectionSeed" -> "1258611", 
      "MatchedSelectedFinalSeed" -> "1258621", 
      "ExpectedConditionalTransitionCells" -> "41", 
      "MatchedReasonParameterCount" -> "85890", 
      "StrongReasonParameterCount" -> "339170", "StrongReasonSpec" -> "<|\"DM\
odel\" -> 96, \"Heads\" -> 4, \"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> \
0.1, \"LearningRate\" -> 0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \
\"Patience\" -> 6, \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"SelectSeed\" -> 1258102, \"FinalSeed\" -> \
1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
      "StrongReasonValidationAccuracy" -> "0.8484848484848485", 
      "StrongReasonValidationBalancedAccuracy" -> "0.7503756033628488", 
      "StrongFinalReasonTrainingAccuracy" -> "0.8632897603485838", 
      "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7738164121195811", 
      "StrongReasonFreezeFileHash" -> 
       "\"b65ac15f06fec4eb0e193c3aa143265aeb19077564e7a272bd382ff33bc61afc\""\
, "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
      "StrongProbeAccuracy" -> "0.6496138996138996", 
      "StrongProbeZeroAccuracy" -> "0.8297297297297297", 
      "StrongProbeOneAccuracy" -> "0.19932432432432431", 
      "StrongProbeBalancedAccuracy" -> "0.514527027027027", 
      "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> 
       "0.", "StrongTransitionProbeAccuracy" -> "0.6463561776061776", 
      "StrongTransitionZeroAccuracy" -> "0.8216216216216217", 
      "StrongTransitionOneAccuracy" -> "0.20819256756756757", 
      "StrongTransitionBalancedAccuracy" -> "0.5149070945945946", 
      "BestNeuralStateExactAccuracy" -> "0.", 
      "BestNeuralTransitionExactAccuracy" -> "0.", 
      "TCCTMinusBestNeuralStateExact" -> "1.", 
      "TCCTMinusBestNeuralTransitionExact" -> "1.", "PilotProtocolPass" -> 
       "True", "PilotOutcome" -> 
       "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
      "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
       "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
      "S125BaseSourceSHA256" -> 
       "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
    "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_Readout\
Baseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_\
02_seed_1258502\\S125C_generated_multirestart_comparison_seed_1258502.wl", 
    "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutB\
aseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_0\
2_seed_1258502\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HAN\
DOFF_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_Multi\
RestartMatched_Output\\world_02_seed_1258502\\S125C_stderr.log"|>, 
   <|"Stage" -> "S125-C-Pilot5", "Completed" -> True, "RunIndex" -> 3, 
    "WorldSeed" -> 1258503, "BaseSourceSHA256" -> 
     "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
    "ManifestSHA256" -> 
     "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
    "GeneratedSourceSHA256" -> 
     "0c5fba4878575fac484f7a853f53081e4c43c13db7fec9426f433cefc80e323c", 
    "ProcessExitCode" -> 0, "ElapsedSeconds" -> 580.8706797, 
    "RunPassed" -> True, "Checks" -> <|"ProcessExitCodeZero" -> True, 
      "NoFatalMarker" -> True, "PilotProtocolPass" -> True, 
      "StrictProspective" -> True, "SharedPerception" -> True, 
      "MaximumTrainingInteractionOrderTwo" -> True, "NoHighOrderLeakage" -> 
       True, "PreWorldProtocolHashPresent" -> True, "ManifestEchoMatches" -> 
       True, "BaseSourceEchoMatches" -> True|>, 
    "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
       "True", "FreshWorldSeed" -> "1258503", "SharedPerception" -> "True", 
      "PreWorldProtocolHash" -> 
       "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""\
, "PerceptionValidationAccuracy" -> "1.", 
      "TrainingMembershipPerceptionAccuracy" -> "1.", 
      "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
      "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> 
       "0", "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 2, 3, 5}", 
      "LearnedInteractionEdges" -> "{2 -> 4, 3 -> 1}", 
      "ConditionalTransitionCells" -> "41", 
      "MembershipQueriesBeforeFreeze" -> "1846", 
      "ReasonValidationAccuracy" -> "0.8308457711442786", 
      "ReasonValidationBalancedAccuracy" -> "0.7314511437057905", 
      "FinalReasonTrainingAccuracy" -> "0.8429035752979415", 
      "FinalReasonTrainingBalancedAccuracy" -> "0.7310034062194222", 
      "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
       "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> 
       "1.", "NeuralProbeAccuracy" -> "0.6544401544401545", 
      "NeuralZeroAccuracy" -> "0.8486486486486486", "NeuralOneAccuracy" -> 
       "0.16891891891891891", "NeuralBalancedAccuracy" -> 
       "0.5087837837837837", "HighOrderTransitionCases" -> "592", 
      "TCCTTransitionExactAccuracy" -> "1.", 
      "NeuralTransitionExactAccuracy" -> "0.", 
      "TCCTTransitionProbeAccuracy" -> "1.", 
      "NeuralTransitionProbeAccuracy" -> "0.6613175675675675", 
      "NeuralTransitionZeroAccuracy" -> "0.8503378378378378", 
      "NeuralTransitionOneAccuracy" -> "0.18876689189189189", 
      "NeuralTransitionBalancedAccuracy" -> "0.5195523648648648", 
      "TCCTMinusNeuralExact" -> "1.", "TCCTMinusNeuralProbe" -> 
       "0.34555984555984554", "TCCTMinusNeuralTransitionExact" -> "1.", 
      "WinnerMargin" -> "0.02", "StrictProtocolPass" -> "True", 
      "GeneralizationDiagnosis" -> 
       "\"STRICT_FRESH_WORLD_TCCT_HIGH_ORDER_GENERALIZATION_ADVANTAGE\"", 
      "TCCTFreezeHash" -> 
       "\"bc81cfe06a0f5807ec428f32e2f08b70c45d2130104cb5f309e0a0e207c1f80d\""\
, "GlobalFreezeHash" -> 
       "\"c445a93878c750da360f96bc9987240c8bf41868d4139fd8e67f402e429be6f8\""\
, "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
      "Protocol" -> "\"MultiRestartMatchedAndStrongTransformerComparison\"", 
      "MatchedRestartSpec" -> "<|\"SelectionSeeds\" -> {1258611, 1258612, \
1258613}, \"FinalSeeds\" -> {1258621, 1258622, 1258623}, \"SelectionMetric\" \
-> \"LowOrderValidationBalancedAccuracy\", \"FinalMetric\" -> \
\"LowOrderTrainingBalancedAccuracy\", \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"HighOrderUsedForSelection\" -> False, \
\"ArchitectureChanged\" -> False|>", "MatchedSelectionCandidateMetrics" -> "{\
<|\"Seed\" -> 1258611, \"ValidationAccuracy\" -> 0.8308457711442786, \
\"ValidationBalancedAccuracy\" -> 0.7287564687509569|>, <|\"Seed\" -> \
1258612, \"ValidationAccuracy\" -> 0.8383084577114428, \
\"ValidationBalancedAccuracy\" -> 0.7231680803503078|>, <|\"Seed\" -> \
1258613, \"ValidationAccuracy\" -> 0.8308457711442786, \
\"ValidationBalancedAccuracy\" -> 0.7314511437057905|>}", 
      "MatchedFinalCandidateMetrics" -> "{<|\"Seed\" -> 1258621, \
\"TrainingAccuracy\" -> 0.8353196099674973, \"TrainingBalancedAccuracy\" -> \
0.7058956758333099|>, <|\"Seed\" -> 1258622, \"TrainingAccuracy\" -> \
0.8429035752979415, \"TrainingBalancedAccuracy\" -> 0.7310034062194222|>, \
<|\"Seed\" -> 1258623, \"TrainingAccuracy\" -> 0.8407367280606717, \
\"TrainingBalancedAccuracy\" -> 0.7276489980444956|>}", 
      "MatchedSelectedSelectionSeed" -> "1258613", 
      "MatchedSelectedFinalSeed" -> "1258622", 
      "ExpectedConditionalTransitionCells" -> "41", 
      "MatchedReasonParameterCount" -> "85890", 
      "StrongReasonParameterCount" -> "339170", "StrongReasonSpec" -> "<|\"DM\
odel\" -> 96, \"Heads\" -> 4, \"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> \
0.1, \"LearningRate\" -> 0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \
\"Patience\" -> 6, \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"SelectSeed\" -> 1258102, \"FinalSeed\" -> \
1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
      "StrongReasonValidationAccuracy" -> "0.8482587064676617", 
      "StrongReasonValidationBalancedAccuracy" -> "0.7462565453042227", 
      "StrongFinalReasonTrainingAccuracy" -> "0.8602383531960996", 
      "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7584604065850615", 
      "StrongReasonFreezeFileHash" -> 
       "\"29dc1f6ca110c044f3541a81b8c077e4dd9d29772dd13a541863cc4e33dd560d\""\
, "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
      "StrongProbeAccuracy" -> "0.6148648648648649", 
      "StrongProbeZeroAccuracy" -> "0.7918918918918919", 
      "StrongProbeOneAccuracy" -> "0.17229729729729729", 
      "StrongProbeBalancedAccuracy" -> "0.4820945945945946", 
      "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> 
       "0.", "StrongTransitionProbeAccuracy" -> "0.6225868725868726", 
      "StrongTransitionZeroAccuracy" -> "0.7891891891891892", 
      "StrongTransitionOneAccuracy" -> "0.20608108108108109", 
      "StrongTransitionBalancedAccuracy" -> "0.49763513513513513", 
      "BestNeuralStateExactAccuracy" -> "0.", 
      "BestNeuralTransitionExactAccuracy" -> "0.", 
      "TCCTMinusBestNeuralStateExact" -> "1.", 
      "TCCTMinusBestNeuralTransitionExact" -> "1.", "PilotProtocolPass" -> 
       "True", "PilotOutcome" -> 
       "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
      "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
       "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
      "S125BaseSourceSHA256" -> 
       "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
    "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_Readout\
Baseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_\
03_seed_1258503\\S125C_generated_multirestart_comparison_seed_1258503.wl", 
    "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutB\
aseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_0\
3_seed_1258503\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HAN\
DOFF_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_Multi\
RestartMatched_Output\\world_03_seed_1258503\\S125C_stderr.log"|>, 
   <|"Stage" -> "S125-C-Pilot5", "Completed" -> True, "RunIndex" -> 4, 
    "WorldSeed" -> 1258504, "BaseSourceSHA256" -> 
     "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b", 
    "ManifestSHA256" -> 
     "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
    "GeneratedSourceSHA256" -> 
     "b155055961bcac1feaed2f4489e16e22eae51ac53750aff57a4cde3bda565e53", 
    "ProcessExitCode" -> 0, "ElapsedSeconds" -> 576.7678172, 
    "RunPassed" -> True, "Checks" -> <|"ProcessExitCodeZero" -> True, 
      "NoFatalMarker" -> True, "PilotProtocolPass" -> True, 
      "StrictProspective" -> True, "SharedPerception" -> True, 
      "MaximumTrainingInteractionOrderTwo" -> True, "NoHighOrderLeakage" -> 
       True, "PreWorldProtocolHashPresent" -> True, "ManifestEchoMatches" -> 
       True, "BaseSourceEchoMatches" -> True|>, 
    "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
       "True", "FreshWorldSeed" -> "1258504", "SharedPerception" -> "True", 
      "PreWorldProtocolHash" -> 
       "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""\
, "PerceptionValidationAccuracy" -> "1.", 
      "TrainingMembershipPerceptionAccuracy" -> "1.", 
      "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
      "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> 
       "0", "InferredFactors" -> "4", "LocalStateCounts" -> "{3, 4, 5, 2}", 
      "LearnedInteractionEdges" -> "{4 -> 3, 1 -> 2}", 
      "ConditionalTransitionCells" -> "41", 
      "MembershipQueriesBeforeFreeze" -> "1846", 
      "ReasonValidationAccuracy" -> "0.8197530864197531", 
      "ReasonValidationBalancedAccuracy" -> "0.7231028003394351", 
      "FinalReasonTrainingAccuracy" -> "0.8499458288190682", 
      "FinalReasonTrainingBalancedAccuracy" -> "0.7345998469347725", 
      "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
       "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> 
       "1.", "NeuralProbeAccuracy" -> "0.61003861003861", 
      "NeuralZeroAccuracy" -> "0.7878378378378378", "NeuralOneAccuracy" -> 
       "0.16554054054054054", "NeuralBalancedAccuracy" -> 
       "0.4766891891891892", "HighOrderTransitionCases" -> "592", 
      "TCCTTransitionExactAccuracy" -> "1.", 
      "NeuralTransitionExactAccuracy" -> "0.", 
      "TCCTTransitionProbeAccuracy" -> "1.", 
      "NeuralTransitionProbeAccuracy" -> "0.6181225868725869", 
      "NeuralTransitionZeroAccuracy" -> "0.7826013513513513", 
      "NeuralTransitionOneAccuracy" -> "0.20692567567567569", 
      "NeuralTransitionBalancedAccuracy" -> "0.4947635135135135", 
      "TCCTMinusNeuralExact" -> "1.", "TCCTMinusNeuralProbe" -> 
       "0.38996138996138996", "TCCTMinusNeuralTransitionExact" -> "1.", 
      "WinnerMargin" -> "0.02", "StrictProtocolPass" -> "True", 
      "GeneralizationDiagnosis" -> 
       "\"STRICT_FRESH_WORLD_TCCT_HIGH_ORDER_GENERALIZATION_ADVANTAGE\"", 
      "TCCTFreezeHash" -> 
       "\"861c8fea08b4afa1f07dbc02cf465d6df73abddfbdeacf69a00b9fea1bfe12d6\""\
, "GlobalFreezeHash" -> 
       "\"cf10bcbda35cb3341eacd1cbf19d513157af2ee35334ec532808b9ddeea7c8eb\""\
, "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
      "Protocol" -> "\"MultiRestartMatchedAndStrongTransformerComparison\"", 
      "MatchedRestartSpec" -> "<|\"SelectionSeeds\" -> {1258611, 1258612, \
1258613}, \"FinalSeeds\" -> {1258621, 1258622, 1258623}, \"SelectionMetric\" \
-> \"LowOrderValidationBalancedAccuracy\", \"FinalMetric\" -> \
\"LowOrderTrainingBalancedAccuracy\", \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"HighOrderUsedForSelection\" -> False, \
\"ArchitectureChanged\" -> False|>", "MatchedSelectionCandidateMetrics" -> "{\
<|\"Seed\" -> 1258611, \"ValidationAccuracy\" -> 0.8197530864197531, \
\"ValidationBalancedAccuracy\" -> 0.7231028003394351|>, <|\"Seed\" -> \
1258612, \"ValidationAccuracy\" -> 0.8074074074074075, \
\"ValidationBalancedAccuracy\" -> 0.7009789065341253|>, <|\"Seed\" -> \
1258613, \"ValidationAccuracy\" -> 0.817283950617284, \
\"ValidationBalancedAccuracy\" -> 0.7024033216147412|>}", 
      "MatchedFinalCandidateMetrics" -> "{<|\"Seed\" -> 1258621, \
\"TrainingAccuracy\" -> 0.847237269772481, \"TrainingBalancedAccuracy\" -> \
0.7321166078732371|>, <|\"Seed\" -> 1258622, \"TrainingAccuracy\" -> \
0.8499458288190682, \"TrainingBalancedAccuracy\" -> 0.7345998469347725|>, \
<|\"Seed\" -> 1258623, \"TrainingAccuracy\" -> 0.8353196099674973, \
\"TrainingBalancedAccuracy\" -> 0.7108695555631216|>}", 
      "MatchedSelectedSelectionSeed" -> "1258611", 
      "MatchedSelectedFinalSeed" -> "1258622", 
      "ExpectedConditionalTransitionCells" -> "41", 
      "MatchedReasonParameterCount" -> "85890", 
      "StrongReasonParameterCount" -> "339170", "StrongReasonSpec" -> "<|\"DM\
odel\" -> 96, \"Heads\" -> 4, \"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> \
0.1, \"LearningRate\" -> 0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \
\"Patience\" -> 6, \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"SelectSeed\" -> 1258102, \"FinalSeed\" -> \
1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
      "StrongReasonValidationAccuracy" -> "0.8419753086419753", 
      "StrongReasonValidationBalancedAccuracy" -> "0.7303764092617288", 
      "StrongFinalReasonTrainingAccuracy" -> "0.8656554712892741", 
      "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7715094392690764", 
      "StrongReasonFreezeFileHash" -> 
       "\"cdc732d3709dbe15a1da6e68b2c2c367b590b992f9e815463fa31f4b6467087e\""\
, "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
      "StrongProbeAccuracy" -> "0.6592664092664092", 
      "StrongProbeZeroAccuracy" -> "0.8391891891891892", 
      "StrongProbeOneAccuracy" -> "0.20945945945945946", 
      "StrongProbeBalancedAccuracy" -> "0.5243243243243243", 
      "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> 
       "0.", "StrongTransitionProbeAccuracy" -> "0.6580598455598455", 
      "StrongTransitionZeroAccuracy" -> "0.8405405405405405", 
      "StrongTransitionOneAccuracy" -> "0.20185810810810811", 
      "StrongTransitionBalancedAccuracy" -> "0.5211993243243243", 
      "BestNeuralStateExactAccuracy" -> "0.", 
      "BestNeuralTransitionExactAccuracy" -> "0.", 
      "TCCTMinusBestNeuralStateExact" -> "1.", 
      "TCCTMinusBestNeuralTransitionExact" -> "1.", "PilotProtocolPass" -> 
       "True", "PilotOutcome" -> 
       "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
      "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
       "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
      "S125BaseSourceSHA256" -> 
       "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
    "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_Readout\
Baseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_\
04_seed_1258504\\S125C_generated_multirestart_comparison_seed_1258504.wl", 
    "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutB\
aseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_0\
4_seed_1258504\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HAN\
DOFF_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_Multi\
RestartMatched_Output\\world_04_seed_1258504\\S125C_stderr.log"|>, 
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
      "MaximumTrainingInteractionOrderTwo" -> True, "NoHighOrderLeakage" -> 
       True, "PreWorldProtocolHashPresent" -> True, "ManifestEchoMatches" -> 
       True, "BaseSourceEchoMatches" -> True|>, 
    "Metrics" -> <|"Stage" -> "\"S125-C-Pilot5\"", "StrictProspective" -> 
       "True", "FreshWorldSeed" -> "1258505", "SharedPerception" -> "True", 
      "PreWorldProtocolHash" -> 
       "\"617486249f59e31d4f5576eba9cdc59fd6ca3b1238d448f6ef566c70ca891bf9\""\
, "PerceptionValidationAccuracy" -> "1.", 
      "TrainingMembershipPerceptionAccuracy" -> "1.", 
      "MaximumTrainingInteractionOrder" -> "2", "TrueJointStates" -> "120", 
      "HighOrderHoldoutStates" -> "74", "HighOrderTouchedBeforeFreeze" -> 
       "0", "InferredFactors" -> "4", "LocalStateCounts" -> "{4, 3, 5, 2}", 
      "LearnedInteractionEdges" -> "{4 -> 3, 2 -> 1}", 
      "ConditionalTransitionCells" -> "41", 
      "MembershipQueriesBeforeFreeze" -> "1846", 
      "ReasonValidationAccuracy" -> "0.8199513381995134", 
      "ReasonValidationBalancedAccuracy" -> "0.7165171942745144", 
      "FinalReasonTrainingAccuracy" -> "0.8369447453954496", 
      "FinalReasonTrainingBalancedAccuracy" -> "0.7250428923110629", 
      "TCCTHighOrderExactAccuracy" -> "1.", "NeuralHighOrderExactAccuracy" -> 
       "0.", "TCCTProbeAccuracy" -> "1.", "TCCTProbeBalancedAccuracy" -> 
       "1.", "NeuralProbeAccuracy" -> "0.5588803088803089", 
      "NeuralZeroAccuracy" -> "0.7108108108108108", "NeuralOneAccuracy" -> 
       "0.17905405405405406", "NeuralBalancedAccuracy" -> 
       "0.4449324324324324", "HighOrderTransitionCases" -> "592", 
      "TCCTTransitionExactAccuracy" -> "1.", 
      "NeuralTransitionExactAccuracy" -> "0.", 
      "TCCTTransitionProbeAccuracy" -> "1.", 
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
       "\"9d7b85a3060dc1f1a805cefc291d9e2aa2c541aa61552608e9a0da46d6f3b3eb\""\
, "GlobalFreezeHash" -> 
       "\"fb88ad5f1df8036c85149c49d1360d0a7378258bf6518d5745e1e2c5ce751c13\""\
, "HighOrderOutputsOpenedAfterAllModelsFrozen" -> "True", 
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
      "MatchedSelectedSelectionSeed" -> "1258612", 
      "MatchedSelectedFinalSeed" -> "1258623", 
      "ExpectedConditionalTransitionCells" -> "41", 
      "MatchedReasonParameterCount" -> "85890", 
      "StrongReasonParameterCount" -> "339170", "StrongReasonSpec" -> "<|\"DM\
odel\" -> 96, \"Heads\" -> 4, \"Layers\" -> 3, \"FF\" -> 384, \"Dropout\" -> \
0.1, \"LearningRate\" -> 0.0003, \"BatchSize\" -> 64, \"Rounds\" -> 35, \
\"Patience\" -> 6, \"ValidationBalancedGate\" -> 0.6, \
\"TrainingBalancedGate\" -> 0.7, \"SelectSeed\" -> 1258102, \"FinalSeed\" -> \
1258103, \"ComparisonRole\" -> \
\"Approximately4xMatchedTransformerReasoner\"|>", 
      "StrongReasonValidationAccuracy" -> "0.8126520681265207", 
      "StrongReasonValidationBalancedAccuracy" -> "0.7169774900516719", 
      "StrongFinalReasonTrainingAccuracy" -> "0.8613217768147345", 
      "StrongFinalReasonTrainingBalancedAccuracy" -> "0.7629354180205439", 
      "StrongReasonFreezeFileHash" -> 
       "\"12dde7b246b59afda32213855c7a597690726b115fb5bdfb714b0f1a87c0870d\""\
, "StrongHighOrderExact" -> "0", "StrongHighOrderExactAccuracy" -> "0.", 
      "StrongProbeAccuracy" -> "0.640926640926641", 
      "StrongProbeZeroAccuracy" -> "0.8297297297297297", 
      "StrongProbeOneAccuracy" -> "0.16891891891891891", 
      "StrongProbeBalancedAccuracy" -> "0.4993243243243243", 
      "StrongTransitionExact" -> "0", "StrongTransitionExactAccuracy" -> 
       "0.", "StrongTransitionProbeAccuracy" -> "0.6558880308880309", 
      "StrongTransitionZeroAccuracy" -> "0.8388513513513514", 
      "StrongTransitionOneAccuracy" -> "0.19847972972972974", 
      "StrongTransitionBalancedAccuracy" -> "0.5186655405405406", 
      "BestNeuralStateExactAccuracy" -> "0.", 
      "BestNeuralTransitionExactAccuracy" -> "0.", 
      "TCCTMinusBestNeuralStateExact" -> "1.", 
      "TCCTMinusBestNeuralTransitionExact" -> "1.", "PilotProtocolPass" -> 
       "True", "PilotOutcome" -> 
       "\"TCCT_ADVANTAGE_OVER_BEST_NEURAL_BASELINE\"", 
      "AllModelsFrozenBeforeHighOrder" -> "True", "S125ManifestHash" -> 
       "c987844978c4feebef2bd4c5cbb598595d4aad33c5e773a805376d46db78f540", 
      "S125BaseSourceSHA256" -> 
       "9a306f0b2e53eb932416e7c02f481ed275a8aa5d6b1870933d36f47b9946d99b"|>, 
    "GeneratedSourceFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_Readout\
Baseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_\
05_seed_1258505\\S125C_generated_multirestart_comparison_seed_1258505.wl", 
    "StandardOutputFile" -> "E:\\TCCT_CODEX_HANDOFF_2026-08-13\\S97A_ReadoutB\
aseline_Development\\S125C_Jupyter_Pilot5_MultiRestartMatched_Output\\world_0\
5_seed_1258505\\S125C_stdout.log", "StandardErrorFile" -> "E:\\TCCT_CODEX_HAN\
DOFF_2026-08-13\\S97A_ReadoutBaseline_Development\\S125C_Jupyter_Pilot5_Multi\
RestartMatched_Output\\world_05_seed_1258505\\S125C_stderr.log"|>}|>
