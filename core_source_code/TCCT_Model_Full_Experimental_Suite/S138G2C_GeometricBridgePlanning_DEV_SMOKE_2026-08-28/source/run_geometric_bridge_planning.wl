ClearAll["Global`*"];

rootDirectory = DirectoryName[DirectoryName[$InputFileName]];
protocolPath = FileNameJoin[{rootDirectory, "protocol", "frozen_protocol.json"}];
publicPath = FileNameJoin[{rootDirectory, "input", "public_tasks.json"}];
resultPath = FileNameJoin[{rootDirectory, "results", "kernel_geometric_planning_result.json"}];
oracleResponderPath = FileNameJoin[{rootDirectory, "source", "oracle_responder.py"}];
oracleRequestPath = FileNameJoin[{rootDirectory, "oracle", "runtime_request.json"}];
oracleResponsePath = FileNameJoin[{rootDirectory, "oracle", "runtime_response.json"}];
oracleLogPath = FileNameJoin[{rootDirectory, "oracle", "query_log.jsonl"}];
protocol = Import[protocolPath, "RawJSON"];
public = Import[publicPath, "RawJSON"];
protocolHash = IntegerString[FileHash[protocolPath, "SHA256"], 16, 64];
runnerHash = IntegerString[FileHash[$InputFileName, "SHA256"], 16, 64];
oracleHash = IntegerString[FileHash[oracleResponderPath, "SHA256"], 16, 64];
If[public["ProtocolSHA256"] =!= protocolHash, Print["FATAL: public/protocol boundary mismatch"]; Exit[2]];
If[runnerHash =!= protocol["FrozenWolframRunnerSHA256"], Print["FATAL: runner differs from frozen protocol"]; Exit[3]];
If[oracleHash =!= protocol["FrozenOracleResponderSHA256"], Print["FATAL: oracle differs from frozen protocol"]; Exit[4]];

GridDigestG2C[grid_List] := IntegerString[Hash[StringRiffle[ToString /@ Flatten[grid], ","], "SHA256"], 16, 64];

MakeInputG2C[task_Association, kind_String, slot_: Null] := Module[
  {h = task["GridHeight"], w = task["GridWidth"], grid, shape, top, left},
  grid = ConstantArray[0, {h, w}];
  Do[grid[[h, 3 + context]] = 6, {context, 0, task["ContextCount"] - 1}];
  shape = Which[kind === "TEST", task["TestShape"], kind === "TRAIN", task["TrainShape"], True, task["ProbeShape"]];
  top = task["TargetTop"]; left = task["TargetLeft"];
  Do[grid[[top + cell[[1]] + 1, left + cell[[2]] + 1]] = task["TargetColor"], {cell, shape}];
  Which[
    kind === "CALIBRATION", grid[[1, 1]] = 9,
    kind === "DECISION", grid[[1, 3 + slot]] = 8,
    kind === "NUISANCE", grid[[1, w]] = 7,
    kind === "TEST", grid[[1, w]] = 5,
    kind === "TRAIN", Null,
    True, Print["FATAL: unknown query kind"]; Exit[10]
  ]; grid
];

ApplyProgramG2C[task_Association, program_Association, kind_String, slot_: Null] := Module[
  {grid, output, positions, r0, r1, c0, c1, mapped, transform},
  grid = MakeInputG2C[task, kind, slot]; output = grid;
  If[kind === "CALIBRATION", output[[2, 3 + program["Context"]]] = 6; Return[output]];
  If[kind === "NUISANCE", output[[2, 9 + program["Nuisance"]]] = 6; Return[output]];
  transform = MemberQ[{"TRAIN", "TEST"}, kind] || (kind === "DECISION" && slot === program["Context"]);
  If[!transform, Return[output]];
  positions = Position[grid, task["TargetColor"], {2}];
  r0 = Min[positions[[All, 1]]]; r1 = Max[positions[[All, 1]]];
  c0 = Min[positions[[All, 2]]]; c1 = Max[positions[[All, 2]]];
  mapped = Switch[program["Decision"],
    0, positions,
    1, {#[[1]], c0 + c1 - #[[2]]} & /@ positions,
    2, {r0 + r1 - #[[1]], #[[2]]} & /@ positions];
  Do[output[[position[[1]], position[[2]]]] = 0, {position, positions}];
  Do[output[[position[[1]], position[[2]]]] = task["TargetColor"], {position, mapped}]; output
];

BuildQueriesG2C[task_Association] := Module[{specs, rows},
  specs = Join[{{"CALIBRATION", Null}}, ({"DECISION", #} & /@ task["InstrumentedContextSlots"]), {{"NUISANCE", Null}}];
  rows = Map[Function[spec, With[{grid = MakeInputG2C[task, spec[[1]], spec[[2]]]}, <|
      "Kind" -> spec[[1]], "Slot" -> spec[[2]], "Input" -> grid,
      "InputSHA256" -> GridDigestG2C[grid]|>]], specs];
  SortBy[rows, #1["InputSHA256"] &]
];

BuildModelsG2C[task_Association, queries_List] := Module[{programs, exact},
  programs = Flatten[Table[<|"Context" -> context, "Decision" -> decision, "Nuisance" -> nuisance|>,
    {context, 0, task["ContextCount"] - 1}, {decision, 0, 2}, {nuisance, 0, task["NuisanceCount"] - 1}], 2];
  exact = Select[programs, ApplyProgramG2C[task, #1, "TRAIN"] === task["InitialTrain"][[1]]["Output"] &];
  Map[Function[program, With[{prediction = ApplyProgramG2C[task, program, "TEST"]}, <|
    "Program" -> program, "DecisionLabel" -> GridDigestG2C[prediction], "TestPrediction" -> prediction,
    "QueryPredictions" -> Association@Map[Function[query,
      query["InputSHA256"] -> ApplyProgramG2C[task, program, query["Kind"], query["Slot"]]], queries]|>]], exact]
];

DecisionCountG2C[models_List] := Length[DeleteDuplicates[Lookup[models, "DecisionLabel"]]];
PredictionG2C[model_Association, queryHash_String] := model["QueryPredictions"][queryHash];
BranchesG2C[models_List, queryHash_String] := GatherBy[models, PredictionG2C[#, queryHash] &];
OneWorstG2C[models_List, queryHash_String] := Max[DecisionCountG2C /@ BranchesG2C[models, queryHash]];
OneSemanticWorstG2C[models_List, queryHash_String] := Max[Length /@ BranchesG2C[models, queryHash]];

ImmediateRowsG2C[models_List, queryHashes_List] := Module[{current = DecisionCountG2C[models]},
  SortBy[Select[Map[Function[queryHash, <|"InputSHA256" -> queryHash,
    "OneStepWorstDecisionClassCount" -> OneWorstG2C[models, queryHash],
    "OneStepWorstSemanticClassCount" -> OneSemanticWorstG2C[models, queryHash]|>], queryHashes],
    #1["OneStepWorstDecisionClassCount"] < current &],
    {#1["OneStepWorstDecisionClassCount"], #1["OneStepWorstSemanticClassCount"], #1["InputSHA256"]} &]
];

BestFollowupG2C[branch_List, queryHashes_List] := Module[{rows, current = DecisionCountG2C[branch]},
  rows = SortBy[Map[Function[queryHash, <|"InputSHA256" -> queryHash,
    "WorstDecisionClassCount" -> OneWorstG2C[branch, queryHash],
    "WorstSemanticClassCount" -> OneSemanticWorstG2C[branch, queryHash]|>], queryHashes],
    {#1["WorstDecisionClassCount"], #1["WorstSemanticClassCount"], #1["InputSHA256"]} &];
  If[Length[rows] === 0 || First[rows]["WorstDecisionClassCount"] >= current,
    <|"InputSHA256" -> Null, "WorstDecisionClassCount" -> current, "WorstSemanticClassCount" -> Length[branch]|>, First[rows]]
];

BridgeRowG2C[models_List, first_String, allHashes_List] := Module[{branches, followups, certificates},
  branches = BranchesG2C[models, first];
  followups = BestFollowupG2C[#, DeleteCases[allHashes, first]] & /@ branches;
  certificates = MapThread[Function[{branch, followup}, <|
    "FirstOutcome" -> PredictionG2C[First[branch], first],
    "BranchSemanticClassCount" -> Length[branch],
    "BranchDecisionClassCount" -> DecisionCountG2C[branch],
    "BestSecondInputSHA256" -> followup["InputSHA256"],
    "BestSecondWorstDecisionClassCount" -> followup["WorstDecisionClassCount"],
    "BestSecondWorstSemanticClassCount" -> followup["WorstSemanticClassCount"]|>], {branches, followups}];
  <|"InputSHA256" -> first, "OneStepWorstDecisionClassCount" -> OneWorstG2C[models, first],
    "OneStepWorstSemanticClassCount" -> OneSemanticWorstG2C[models, first],
    "TwoStepWorstDecisionClassCount" -> Max[Lookup[certificates, "BestSecondWorstDecisionClassCount"]],
    "BranchCertificates" -> certificates|>
];

BridgeRowsG2C[models_List, queryHashes_List] := Module[{current = DecisionCountG2C[models], rows},
  rows = BridgeRowG2C[models, #1, queryHashes] & /@ queryHashes;
  SortBy[Select[rows, #1["OneStepWorstDecisionClassCount"] >= current &&
      #1["TwoStepWorstDecisionClassCount"] < current &],
    {#1["TwoStepWorstDecisionClassCount"], #1["OneStepWorstSemanticClassCount"], #1["InputSHA256"]} &]
];

RunOracleG2C[mode_String, taskID_String : "NONE", queryNumber_String : "NONE"] := Module[{command},
  command = "set TCCT_ORACLE_MODE=" <> mode <> "&&set TCCT_TASK=" <> taskID <>
    "&&set TCCT_QUERY=" <> queryNumber <> "&&" <> protocol["PowerShellEngine"] <>
    " -NoProfile -NonInteractive -EncodedCommand " <> protocol["OracleBridgeEncodedCommand"];
  Run[command]
];

CallOracleG2C[taskID_String, queryNumber_String, query_Association] := Module[{request, response, exitCode},
  request = <|"ProtocolSHA256" -> protocolHash, "TaskID" -> taskID, "QueryNumber" -> queryNumber,
    "Input" -> query["Input"], "InputSHA256" -> query["InputSHA256"],
    "GeneratedByTCCTKernel" -> True, "TestOutputAccessed" -> False,
    "HiddenProgramAccessedByLearner" -> False|>;
  Export[oracleRequestPath, request, "RawJSON", "Compact" -> False];
  exitCode = RunOracleG2C["query", taskID, queryNumber];
  If[exitCode =!= 0, Print["FATAL: oracle query failed"]; Exit[20]];
  response = Import[oracleResponsePath, "RawJSON"];
  If[response["ProtocolSHA256"] =!= protocolHash || response["TaskID"] =!= taskID ||
      response["QueryNumber"] =!= queryNumber || response["Input"] =!= query["Input"] ||
      response["InputSHA256"] =!= query["InputSHA256"], Print["FATAL: invalid oracle response boundary"]; Exit[21]];
  response
];

EvaluateTaskG2C[task_Association] := Module[
  {queries, queryByHash, models, initialModels, unused, trace = {}, immediate, bridges,
   selected, admission, response, beforeDecision, beforeSemantic, queryNumber, keep,
   committed, runtime, value, stopReason, remainingImmediate, remainingBridges},
  queries = BuildQueriesG2C[task]; queryByHash = AssociationThread[Lookup[queries, "InputSHA256"] -> queries];
  models = BuildModelsG2C[task, queries]; initialModels = models; unused = Lookup[queries, "InputSHA256"];
  {runtime, value} = AbsoluteTiming[While[DecisionCountG2C[models] > 1 && Length[unused] > 0 &&
      Length[trace] < protocol["MaximumActiveQueriesPerTask"],
    immediate = ImmediateRowsG2C[models, unused];
    If[Length[immediate] > 0, selected = First[immediate]; admission = "IMMEDIATE_DECISION_GAIN",
      bridges = BridgeRowsG2C[models, unused];
      If[Length[bridges] === 0, stopReason = "NO_DEPTH2_DECISION_PLAN"; Break[]];
      selected = First[bridges]; admission = "TWO_STEP_BRIDGE_CERTIFICATE"];
    beforeDecision = DecisionCountG2C[models]; beforeSemantic = Length[models];
    queryNumber = "KQ" <> IntegerString[Length[trace] + 1, 10, 2];
    response = CallOracleG2C[task["TaskID"], queryNumber, queryByHash[selected["InputSHA256"]]];
    keep = PredictionG2C[#1, selected["InputSHA256"]] === response["Output"] & /@ models;
    models = Pick[models, keep, True];
    AppendTo[trace, <|"QueryNumber" -> queryNumber, "Input" -> queryByHash[selected["InputSHA256"]]["Input"],
      "InputSHA256" -> selected["InputSHA256"], "QueryKind" -> queryByHash[selected["InputSHA256"]]["Kind"],
      "QuerySlot" -> queryByHash[selected["InputSHA256"]]["Slot"], "AdmissionMode" -> admission,
      "DecisionClassCountBefore" -> beforeDecision, "SemanticClassCountBefore" -> beforeSemantic,
      "OneStepWorstDecisionClassCount" -> selected["OneStepWorstDecisionClassCount"],
      "TwoStepWorstDecisionClassCount" -> Lookup[selected, "TwoStepWorstDecisionClassCount", Null],
      "BridgeCertificate" -> Lookup[selected, "BranchCertificates", {}], "OracleOutput" -> response["Output"],
      "DecisionClassCountAfter" -> DecisionCountG2C[models], "SemanticClassCountAfter" -> Length[models],
      "GeneratedByTCCTKernel" -> True, "TestOutputAccessed" -> False,
      "HiddenProgramAccessedByLearner" -> False|>];
    unused = DeleteCases[unused, selected["InputSHA256"]];
  ]];
  committed = DecisionCountG2C[models] === 1;
  If[!StringQ[stopReason], stopReason = Which[committed, "DECISION_CERTIFIED", Length[unused] === 0,
    "QUERY_LANGUAGE_EXHAUSTED", Length[trace] >= protocol["MaximumActiveQueriesPerTask"],
    "RESOURCE_CAP_REACHED", True, "NO_DEPTH2_DECISION_PLAN"]];
  remainingImmediate = Length[ImmediateRowsG2C[models, unused]];
  remainingBridges = If[remainingImmediate === 0, Length[BridgeRowsG2C[models, unused]], Null];
  <|"TaskID" -> task["TaskID"], "RuntimeSeconds" -> runtime,
    "InitialSemanticClassCount" -> Length[initialModels], "InitialDecisionClassCount" -> DecisionCountG2C[initialModels],
    "FinalSemanticClassCount" -> Length[models], "FinalDecisionClassCount" -> DecisionCountG2C[models],
    "ActiveQueryCount" -> Length[trace], "ActiveQueryTrace" -> trace, "AdaptiveStopReason" -> stopReason,
    "DecisionCertified" -> committed, "TestPredictionCommitted" -> committed,
    "CommittedDecisionLabel" -> If[committed, First[models]["DecisionLabel"], Null],
    "CommittedTestPrediction" -> If[committed, First[models]["TestPrediction"], Null],
    "RemainingImmediateDecisionQueryCount" -> remainingImmediate,
    "RemainingTwoStepBridgeQueryCount" -> remainingBridges,
    "Status" -> If[committed, "DECISION_CERTIFIED", "DECISION_AMBIGUOUS_NO_DEPTH2_PLAN"],
    "TestOutputAccessed" -> False, "HiddenProgramAccessedByLearner" -> False|>
];

Print[protocol["Stage"]];
Print["Executable geometry + depth-2 decision-relevant minimax planning"];
resetCode = RunOracleG2C["reset"];
If[resetCode =!= 0, Print["FATAL: oracle reset failed"]; Exit[22]];
{totalRuntime, taskRows} = AbsoluteTiming[EvaluateTaskG2C /@ public["Tasks"]];
Do[Print[row["TaskID"], " status=", row["Status"], " queries=", row["ActiveQueryCount"],
  " decision=", row["InitialDecisionClassCount"], "->", row["FinalDecisionClassCount"]], {row, taskRows}];
tracePolicyPass = And @@ Flatten[Map[Function[row, Map[Function[q, Which[
  q["AdmissionMode"] === "IMMEDIATE_DECISION_GAIN", q["OneStepWorstDecisionClassCount"] < q["DecisionClassCountBefore"],
  q["AdmissionMode"] === "TWO_STEP_BRIDGE_CERTIFICATE", q["OneStepWorstDecisionClassCount"] >= q["DecisionClassCountBefore"] &&
    q["TwoStepWorstDecisionClassCount"] < q["DecisionClassCountBefore"], True, False]], row["ActiveQueryTrace"]]], taskRows]];
commitCount = Count[Lookup[taskRows, "TestPredictionCommitted"], True];
abstainCount = Count[Lookup[taskRows, "TestPredictionCommitted"], False];
bridgeCommitCount = Count[taskRows, row_ /; TrueQ[row["TestPredictionCommitted"]] &&
  Length[row["ActiveQueryTrace"]] === 2 && First[row["ActiveQueryTrace"]]["AdmissionMode"] === "TWO_STEP_BRIDGE_CERTIFICATE"];
safeStopCount = Count[taskRows, row_ /; !TrueQ[row["TestPredictionCommitted"]] && row["ActiveQueryCount"] === 0 &&
  row["AdaptiveStopReason"] === "NO_DEPTH2_DECISION_PLAN"];
oracleLogCount = Length@Select[StringSplit[Import[oracleLogPath, "Text"], "\n"], StringLength[#1] > 0 &];
preScorePass = tracePolicyPass && commitCount === 3 && abstainCount === 2 && bridgeCommitCount === 3 &&
  safeStopCount === 2 && oracleLogCount === Total[Lookup[taskRows, "ActiveQueryCount"]] &&
  !MemberQ[Lookup[taskRows, "TestOutputAccessed"], True] &&
  !MemberQ[Lookup[taskRows, "HiddenProgramAccessedByLearner"], True];
result = <|"Stage" -> protocol["Stage"], "EvidenceStatus" -> protocol["EvidenceStatus"],
  "ProtocolSHA256" -> protocolHash, "WolframRunnerSHA256" -> runnerHash,
  "OracleResponderSHA256" -> oracleHash, "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version, "RuntimeSeconds" -> totalRuntime, "TaskResults" -> taskRows,
  "ObservedActiveQueryCounts" -> Lookup[taskRows, "ActiveQueryCount"],
  "OracleQueryLogLineCount" -> oracleLogCount, "TracePolicyPreScorePass" -> tracePolicyPass,
  "BridgeCommitCount" -> bridgeCommitCount, "SafeStopCount" -> safeStopCount,
  "NativePreScorePass" -> preScorePass, "CoreRewriteFreezeDedupModified" -> False,
  "CandidateProgramsDerivedFromFrozenExecutableGeometryGrammar" -> True,
  "Conclusion" -> If[preScorePass, "GEOMETRIC_DEPTH2_COMPLETE_AWAITING_SEALED_SCORE", "NATIVE_PRESCORE_FAILURE"]|>;
Export[resultPath, result, "RawJSON", "Compact" -> False];
Print["native pre-score pass=", preScorePass, " runtime=", totalRuntime];
Exit[0];
