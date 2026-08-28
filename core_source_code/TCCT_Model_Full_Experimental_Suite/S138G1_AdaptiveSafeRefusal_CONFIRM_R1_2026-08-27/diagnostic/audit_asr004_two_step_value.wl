(* Diagnostic-only two-step decision-value audit of the already seen ASR004. *)

auditInputFile = $InputFileName;
auditRoot = DirectoryName[DirectoryName[auditInputFile]];
auditRunner = FileNameJoin[{auditRoot, "source", "run_adaptive_safe_refusal.wl"}];
auditRunnerText = Import[auditRunner, "Text"];
auditMarker = "Print[protocol[\"Stage\"]];";
auditMarkerPosition = First@First@StringPosition[auditRunnerText, auditMarker];
auditDefinitionText = StringReplace[
  StringTake[auditRunnerText, auditMarkerPosition - 1],
  "$InputFileName" -> ToString[auditRunner, InputForm]
];

(* The prefix begins with ClearAll["Global`*"]. The ToExpression argument is
   evaluated before that ClearAll runs. The text-only path substitution makes
   the frozen hash boundary inspect the original runner. *)
ToExpression[auditDefinitionText, InputForm];
diagnosticRunnerPath = FileNameJoin[{rootDirectory, "source",
  "run_adaptive_safe_refusal.wl"}];

result = Import[resultPath, "RawJSON"];
task = SelectFirst[public["Tasks"], #1["TaskID"] === "ASR004" &];
resultRow = SelectFirst[result["TaskResults"], #1["TaskID"] === "ASR004" &];
trace = resultRow["ActiveQueryTrace"];

If[Length[trace] =!= 2,
  Print["FATAL: ASR004 does not have the expected two-query trace"];
  Exit[41]
];

initialCandidates = (<|"AST" -> #1|> &) /@
  resultRow["InitialShadowHypothesisASTs"];
fullUniverse = KernelInterventionUniverse137[task, initialCandidates, {}];

firstQuery = trace[[1]];
secondQuery = trace[[2]];
firstKeepMask = (#1 === firstQuery["OracleOutput"] &) /@
  (PredictKernelIntervention137[#1, firstQuery["KernelGeneratedInput"]] & /@
    initialCandidates);
afterFirstCandidates = Pick[initialCandidates, firstKeepMask, True];
afterFirstState = SemanticDecisionState138D[
  task, afterFirstCandidates, fullUniverse];

If[afterFirstState["SemanticClassCount"] =!=
      firstQuery["SemanticClassCountAfter"] ||
    afterFirstState["DecisionClassCount"] =!=
      firstQuery["DecisionClassCountAfter"],
  Print["FATAL: reconstructed post-KQ01 state differs from frozen trace"];
  Exit[42]
];

universeHashes = Lookup[fullUniverse, "InputSHA256"];
firstIndex = First@First@Position[universeHashes, firstQuery["InputSHA256"]];
secondIndex = First@First@Position[universeHashes, secondQuery["InputSHA256"]];
usedBeforeBridge = {firstIndex};
availableFirstIndices = Complement[Range[Length[fullUniverse]], usedBeforeBridge];

predictionKeys = ((ToString[#1, InputForm] &) /@ #1 &) /@
  afterFirstState["ClassPredictionMatrix"];
testKeys = (ToString[#1, InputForm] &) /@
  afterFirstState["ClassTestPredictions"];
allClasses = Range[afterFirstState["SemanticClassCount"]];
currentDecisionCount = afterFirstState["DecisionClassCount"];

DecisionCountAudit[indices_List] :=
  Length[DeleteDuplicates[testKeys[[indices]]]];

BranchesAudit[indices_List, queryIndex_Integer] :=
  GatherBy[indices, predictionKeys[[#1, queryIndex]] &];

OneStepWorstAudit[indices_List, queryIndex_Integer] :=
  Max[DecisionCountAudit /@ BranchesAudit[indices, queryIndex]];

BestSecondWorstAudit[branch_List, excludedIndices_List] := Module[
  {secondIndices, worstRows},
  secondIndices = Complement[Range[Length[fullUniverse]], excludedIndices];
  worstRows = OneStepWorstAudit[branch, #1] & /@ secondIndices;
  If[Length[worstRows] === 0,
    DecisionCountAudit[branch],
    Min[Prepend[worstRows, DecisionCountAudit[branch]]]
  ]
];

TwoStepWorstAudit[queryIndex_Integer] := Module[
  {branches, branchOutcomes, branchDecisionCount},
  branches = BranchesAudit[allClasses, queryIndex];
  branchOutcomes = Map[
    Function[branch,
      branchDecisionCount = DecisionCountAudit[branch];
      If[branchDecisionCount < currentDecisionCount,
        branchDecisionCount,
        BestSecondWorstAudit[branch, {firstIndex, queryIndex}]
      ]
    ],
    branches
  ];
  Max[branchOutcomes]
];

semanticSplittingIndices = Select[
  availableFirstIndices,
  Length[BranchesAudit[allClasses, #1]] > 1 &
];
nonStrictIndices = Select[
  semanticSplittingIndices,
  OneStepWorstAudit[allClasses, #1] >= currentDecisionCount &
];

nonStrictRows = Map[
  Function[queryIndex,
    Module[{twoStepWorst = TwoStepWorstAudit[queryIndex]},
      <|
        "InputSHA256" -> universeHashes[[queryIndex]],
        "OneStepWorstDecisionClassCount" ->
          OneStepWorstAudit[allClasses, queryIndex],
        "TwoStepWorstDecisionClassCount" -> twoStepWorst,
        "CertifiedTwoStepBridge" -> (twoStepWorst < currentDecisionCount)
      |>
    ]
  ],
  nonStrictIndices
];

secondBranches = BranchesAudit[allClasses, secondIndex];
secondActualOutputKey = ToString[secondQuery["OracleOutput"], InputForm];
secondActualBranch = SelectFirst[
  secondBranches,
  predictionKeys[[First[#1], secondIndex]] === secondActualOutputKey &,
  {}
];
secondBranchRows = MapIndexed[
  Function[{branch, branchNumber},
    <|
      "BranchNumber" -> First[branchNumber],
      "SemanticClassCount" -> Length[branch],
      "DecisionClassCount" -> DecisionCountAudit[branch],
      "BestAtMostOneFurtherQueryWorstDecisionClassCount" ->
        BestSecondWorstAudit[branch, {firstIndex, secondIndex}],
      "MatchesActualOracleBranch" -> (branch === secondActualBranch)
    |>
  ],
  secondBranches
];

bridgeRows = Select[nonStrictRows, TrueQ[#1["CertifiedTwoStepBridge"]] &];
minimumTwoStepWorst = If[Length[nonStrictRows] === 0,
  Null,
  Min[Lookup[nonStrictRows, "TwoStepWorstDecisionClassCount"]]
];
actualBranchBestSecondWorst = If[Length[secondActualBranch] === 0,
  Null,
  BestSecondWorstAudit[secondActualBranch, {firstIndex, secondIndex}]
];

audit = <|
  "Stage" -> "S138-G1 ASR004 diagnostic-only two-step decision-value audit",
  "DiagnosticOnly" -> True,
  "UsesAlreadySeenFailedWorld" -> True,
  "ProspectiveCapabilityPass" -> False,
  "ProtocolSHA256" -> IntegerString[FileHash[protocolPath, "SHA256"], 16, 64],
  "FrozenRunnerSHA256" -> IntegerString[
    FileHash[diagnosticRunnerPath, "SHA256"], 16, 64],
  "TaskID" -> "ASR004",
  "ReconstructedPostKQ01SemanticClassCount" ->
    afterFirstState["SemanticClassCount"],
  "ReconstructedPostKQ01DecisionClassCount" -> currentDecisionCount,
  "AllowedInterventionUniverseCount" -> Length[fullUniverse],
  "ActualKQ02InputSHA256" -> secondQuery["InputSHA256"],
  "ActualKQ02OneStepWorstDecisionClassCount" ->
    OneStepWorstAudit[allClasses, secondIndex],
  "ActualKQ02ActualBranchDecisionClassCount" ->
    If[Length[secondActualBranch] === 0, Null, DecisionCountAudit[secondActualBranch]],
  "ActualKQ02ActualBranchBestOneFurtherQueryWorstDecisionClassCount" ->
    actualBranchBestSecondWorst,
  "ActualKQ02CertifiedTwoStepBridge" ->
    (TwoStepWorstAudit[secondIndex] < currentDecisionCount),
  "ActualKQ02BranchAudit" -> secondBranchRows,
  "SemanticSplittingAllowedQueryCountAfterKQ01" ->
    Length[semanticSplittingIndices],
  "NonStrictOneStepQueryCountAfterKQ01" -> Length[nonStrictRows],
  "CertifiedTwoStepBridgeQueryCountAfterKQ01" -> Length[bridgeRows],
  "MinimumTwoStepWorstDecisionClassCountAmongNonStrictQueries" ->
    minimumTwoStepWorst,
  "CertifiedTwoStepBridgeExamples" -> Take[bridgeRows, UpTo[10]],
  "Conclusion" -> Which[
    Length[bridgeRows] > 0,
      "CERTIFIED_TWO_STEP_BRIDGE_EXISTS_ONE_STEP_STOP_MAY_BE_PREMATURE",
    True,
      "NO_CERTIFIED_TWO_STEP_BRIDGE_IN_ASR004_ONE_STEP_STOP_IS_SUFFICIENT_HERE"
  ]
|>;

destination = FileNameJoin[{rootDirectory, "diagnostic",
  "asr004_two_step_value_audit.json"}];
Export[destination, audit, "RawJSON", "Compact" -> False];
Print[InputForm[audit]];
Exit[0];
