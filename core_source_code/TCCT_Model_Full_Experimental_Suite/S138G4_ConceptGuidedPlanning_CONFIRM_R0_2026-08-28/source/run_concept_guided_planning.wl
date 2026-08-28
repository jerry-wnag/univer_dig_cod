ClearAll["Global`*"];

rootDirectory = DirectoryName[DirectoryName[$InputFileName]];
protocolPath = FileNameJoin[{rootDirectory, "protocol", "frozen_protocol.json"}];
publicPath = FileNameJoin[{rootDirectory, "input", "public_tasks.json"}];
resultPath = FileNameJoin[{rootDirectory, "results", "kernel_concept_guided_result.json"}];
conceptLibraryPath = FileNameJoin[{rootDirectory, "library", "frozen_planning_concepts.json"}];
oracleResponderPath = FileNameJoin[{rootDirectory, "source", "oracle_responder.py"}];
oracleRequestPath = FileNameJoin[{rootDirectory, "oracle", "runtime_request.json"}];
oracleResponsePath = FileNameJoin[{rootDirectory, "oracle", "runtime_response.json"}];
oracleLogPath = FileNameJoin[{rootDirectory, "oracle", "query_log.jsonl"}];
protocol = Import[protocolPath, "RawJSON"];
public = Import[publicPath, "RawJSON"];
conceptLibrary = Import[conceptLibraryPath, "RawJSON"];
protocolHash = IntegerString[FileHash[protocolPath, "SHA256"], 16, 64];
runnerHash = IntegerString[FileHash[$InputFileName, "SHA256"], 16, 64];
oracleHash = IntegerString[FileHash[oracleResponderPath, "SHA256"], 16, 64];
conceptLibraryHash = IntegerString[FileHash[conceptLibraryPath, "SHA256"], 16, 64];
If[public["ProtocolSHA256"] =!= protocolHash, Print["FATAL: public/protocol mismatch"]; Exit[2]];
If[runnerHash =!= protocol["FrozenWolframRunnerSHA256"], Print["FATAL: runner differs from frozen protocol"]; Exit[3]];
If[oracleHash =!= protocol["FrozenOracleResponderSHA256"], Print["FATAL: oracle differs from frozen protocol"]; Exit[4]];
If[conceptLibraryHash =!= protocol["FrozenConceptLibrarySHA256"], Print["FATAL: concept library differs from frozen protocol"]; Exit[5]];

GridDigestG3[grid_List] := IntegerString[Hash[StringRiffle[ToString /@ Flatten[grid], ","], "SHA256"], 16, 64];
AllPrefixesG3[counts_List, 0] := {{}};
AllPrefixesG3[counts_List, length_Integer] := Tuples[Table[Range[0, counts[[index]] - 1], {index, length}]];

MakeInputG3[task_Association, spec_Association] := Module[
  {h = task["GridHeight"], w = task["GridWidth"], grid, shape, top, left, kind, prefix},
  grid = ConstantArray[0, {h, w}];
  Do[Do[grid[[h - level, 3 + 4 level + value]] = {6, 7, 9}[[level + 1]],
    {value, 0, task["ContextCounts"][[level + 1]] - 1}], {level, 0, Length[task["ContextCounts"]] - 1}];
  kind = spec["Kind"];
  shape = Which[kind === "TEST", task["TestShape"], kind === "TRAIN", task["TrainShape"], True, task["ProbeShape"]];
  top = task["TargetTop"]; left = task["TargetLeft"];
  Do[grid[[top + cell[[1]] + 1, left + cell[[2]] + 1]] = task["TargetColor"], {cell, shape}];
  prefix = Lookup[spec, "Prefix", {}];
  Do[grid[[2 + level, 3 + 4 level + prefix[[level + 1]]]] = 8, {level, 0, Length[prefix] - 1}];
  Which[
    kind === "CALIBRATE", grid[[1, spec["Level"] + 1]] = 9,
    kind === "DECISION", grid[[1, w]] = 8,
    kind === "NUISANCE", grid[[1, w]] = 7,
    kind === "TEST", grid[[1, w]] = 5,
    kind === "TRAIN", Null,
    True, Print["FATAL: unknown spec kind"]; Exit[10]
  ]; grid
];

ApplyProgramG3[task_Association, program_Association, spec_Association] := Module[
  {grid, output, kind, prefix, level, value, transform, positions, r0, r1, c0, c1, mapped},
  grid = MakeInputG3[task, spec]; output = grid; kind = spec["Kind"];
  prefix = Lookup[spec, "Prefix", {}];
  If[kind === "CALIBRATE", level = spec["Level"];
    If[Take[program["Keys"], level] === prefix, value = program["Keys"][[level + 1]];
      output[[6 + level, 3 + 4 level + value]] = {6, 7, 9}[[level + 1]]]; Return[output]];
  If[kind === "NUISANCE", output[[9, 13 + program["Nuisance"]]] = 9; Return[output]];
  transform = MemberQ[{"TRAIN", "TEST"}, kind] ||
    (kind === "DECISION" && Take[program["Keys"], Length[prefix]] === prefix);
  If[!transform, Return[output]];
  positions = Position[grid, task["TargetColor"], {2}];
  r0 = Min[positions[[All, 1]]]; r1 = Max[positions[[All, 1]]];
  c0 = Min[positions[[All, 2]]]; c1 = Max[positions[[All, 2]]];
  mapped = Switch[program["Decision"], 0, positions,
    1, {#[[1]], c0 + c1 - #[[2]]} & /@ positions,
    2, {r0 + r1 - #[[1]], #[[2]]} & /@ positions];
  Do[output[[position[[1]], position[[2]]]] = 0, {position, positions}];
  Do[output[[position[[1]], position[[2]]]] = task["TargetColor"], {position, mapped}]; output
];

BuildQueriesG3[task_Association] := Module[{depth, disabled, specs, trainHashes, rows},
  depth = Length[task["ContextCounts"]];
  disabled = Lookup[task, "DisabledCalibrationLevels", {}];
  specs = Flatten[Table[<|"Kind" -> "CALIBRATE", "Level" -> level, "Prefix" -> prefix|>,
    {level, Select[Range[0, depth - 1], !MemberQ[disabled, #] &]},
    {prefix, AllPrefixesG3[task["ContextCounts"], level]}], 1];
  specs = Join[specs, (<|"Kind" -> "DECISION", "Level" -> Null, "Prefix" -> #|> & /@
      AllPrefixesG3[task["ContextCounts"], depth]),
    {<|"Kind" -> "NUISANCE", "Level" -> Null, "Prefix" -> {}|>}];
  trainHashes = GridDigestG3 /@ Lookup[task["InitialTrain"], "Input"];
  rows = Map[Function[spec, With[{grid = MakeInputG3[task, spec]}, <|
    "Kind" -> spec["Kind"], "Level" -> spec["Level"], "Prefix" -> spec["Prefix"],
    "Input" -> grid, "InputSHA256" -> GridDigestG3[grid]|>]], specs];
  SortBy[Select[rows, !MemberQ[trainHashes, #1["InputSHA256"]] &], #1["InputSHA256"] &]
];

TrainingExactG3[task_Association, program_Association] := And @@ Map[
  ApplyProgramG3[task, program, #1["Spec"]] === #1["Output"] &, task["InitialTrain"]];

BuildModelsG3[task_Association, queries_List] := Module[{keyRows, programs, exact},
  keyRows = AllPrefixesG3[task["ContextCounts"], Length[task["ContextCounts"]]];
  programs = Flatten[Table[<|"Keys" -> keys, "Decision" -> decision, "Nuisance" -> nuisance|>,
    {keys, keyRows}, {decision, 0, 2}, {nuisance, 0, task["NuisanceCount"] - 1}], 2];
  exact = Select[programs, TrainingExactG3[task, #1] &];
  Map[Function[program, With[{testSpec = <|"Kind" -> "TEST", "Level" -> Null, "Prefix" -> {}|>},
    With[{prediction = ApplyProgramG3[task, program, testSpec]}, <|
      "ModelKey" -> StringRiffle[ToString /@ Join[program["Keys"], {program["Decision"], program["Nuisance"]}], ":"],
      "Program" -> program, "DecisionLabel" -> GridDigestG3[prediction], "TestPrediction" -> prediction,
      "QueryPredictions" -> Association@Map[Function[query, query["InputSHA256"] ->
        ApplyProgramG3[task, program, query]], queries]|>]]], exact]
];

DecisionCountG3[models_List] := Length[DeleteDuplicates[Lookup[models, "DecisionLabel"]]];
PredictionG3[model_Association, queryHash_String] := model["QueryPredictions"][queryHash];
BranchesG3[models_List, queryHash_String] := GatherBy[models, PredictionG3[#, queryHash] &];
UnsolvedG3[] := <|"Solvable" -> False, "RequiredDepth" -> Null, "FirstInputSHA256" -> Null|>;
$PlanMemoG3 = <||>;
$PlanCountersG4 = <||>;
$QueryByHashG4 = <||>;
$UseConceptsG4 = False;

ResetPlanCountersG4[] := ($PlanCountersG4 = <|
  "ExpandedStateCount" -> 0, "QueryEvaluationCount" -> 0,
  "OutcomeBranchEvaluationCount" -> 0, "ConceptMatchStateCount" -> 0,
  "ConceptInstantiatedStateCount" -> 0, "ConceptInstantiationMissCount" -> 0,
  "NoConceptMatchStateCount" -> 0|>);
IncrementCounterG4[key_String, amount_Integer : 1] :=
  ($PlanCountersG4[key] = $PlanCountersG4[key] + amount);

CommonPrefixG4[models_List] := Module[{keys, prefix = {}, values},
  keys = Lookup[Lookup[models, "Program"], "Keys"];
  Do[values = DeleteDuplicates[keys[[All, index]]];
    If[Length[values] =!= 1, Break[]]; AppendTo[prefix, First[values]],
    {index, 1, Length[First[keys]]}]; prefix
];

InstantiateConceptG4[models_List, unused_List] := Module[{prefix, matches, concept, candidates},
  prefix = CommonPrefixG4[models];
  matches = Select[conceptLibrary["Concepts"],
    #1["Feature"]["KnownPrefixLength"] === Length[prefix] &&
    DecisionCountG3[models] >= #1["Feature"]["DecisionClassMinimum"] &];
  If[Length[matches] === 0, Return[<|"Matched" -> False, "InputSHA256" -> Null|>]];
  concept = First[matches];
  candidates = Select[unused, With[{query = $QueryByHashG4[#1]},
    If[concept["QueryTemplate"] === "CALIBRATE_NEXT_UNKNOWN_CONTEXT",
      query["Kind"] === "CALIBRATE" && query["Level"] === Length[prefix] && query["Prefix"] === prefix,
      query["Kind"] === "DECISION" && query["Prefix"] === prefix]] &];
  <|"Matched" -> True, "ConceptID" -> concept["ConceptID"],
    "InputSHA256" -> If[Length[candidates] > 0, First@Sort[candidates], Null]|>
];

PreferredQueryG4[models_List, unused_List] := Module[{instantiation},
  If[!TrueQ[$UseConceptsG4], Return[Null]];
  instantiation = InstantiateConceptG4[models, unused];
  If[!TrueQ[instantiation["Matched"]], IncrementCounterG4["NoConceptMatchStateCount"]; Return[Null]];
  IncrementCounterG4["ConceptMatchStateCount"];
  If[!StringQ[instantiation["InputSHA256"]], IncrementCounterG4["ConceptInstantiationMissCount"]; Return[Null]];
  IncrementCounterG4["ConceptInstantiatedStateCount"]; instantiation["InputSHA256"]
];

SolveAtMostG4[models_List, unused_List, depth_Integer] := Module[
  {key, ordered, preferred, branchRows, remaining, allSolvable, child, result},
  If[DecisionCountG3[models] === 1, Return[<|"Solvable" -> True, "FirstInputSHA256" -> Null|>]];
  If[depth === 0 || Length[unused] === 0, Return[UnsolvedG3[]]];
  key = IntegerString[Hash[{Sort[Lookup[models, "ModelKey"]], Sort[unused], depth}, "SHA256"], 16, 64];
  If[KeyExistsQ[$PlanMemoG3, key], Return[$PlanMemoG3[key]]];
  IncrementCounterG4["ExpandedStateCount"];
  ordered = Sort[unused]; preferred = PreferredQueryG4[models, ordered];
  If[StringQ[preferred], ordered = Prepend[DeleteCases[ordered, preferred], preferred]];
  result = Catch[
    Do[
      IncrementCounterG4["QueryEvaluationCount"];
      branchRows = BranchesG3[models, queryHash];
      IncrementCounterG4["OutcomeBranchEvaluationCount", Length[branchRows]];
      remaining = DeleteCases[unused, queryHash]; allSolvable = True;
      Do[child = SolveAtMostG4[branch, remaining, depth - 1];
        If[!TrueQ[child["Solvable"]], allSolvable = False; Break[]], {branch, branchRows}];
      If[TrueQ[allSolvable],
        Throw[<|"Solvable" -> True, "FirstInputSHA256" -> queryHash|>, "PlanFound"]],
      {queryHash, ordered}];
    UnsolvedG3[],
    "PlanFound"
  ];
  AssociateTo[$PlanMemoG3, key -> result]; result
];

FindMinimalPlanG4[models_List, unused_List, maximumDepth_Integer, queryByHash_Association,
    useConcepts_] := Module[{found, plan},
  $PlanMemoG3 = <||>; ResetPlanCountersG4[]; $QueryByHashG4 = queryByHash;
  $UseConceptsG4 = TrueQ[useConcepts]; found = UnsolvedG3[];
  Do[plan = SolveAtMostG4[models, unused, depth]; If[TrueQ[plan["Solvable"]],
    found = Join[plan, <|"RequiredDepth" -> depth|>]; Break[]], {depth, 0, maximumDepth}];
  Join[found, <|"WorkCounters" -> $PlanCountersG4|>]
];

RunOracleG3[mode_String, taskID_String : "NONE", queryNumber_String : "NONE"] := Module[{command},
  command = "set TCCT_ORACLE_MODE=" <> mode <> "&&set TCCT_TASK=" <> taskID <>
    "&&set TCCT_QUERY=" <> queryNumber <> "&&" <> protocol["PowerShellEngine"] <>
    " -NoProfile -NonInteractive -EncodedCommand " <> protocol["OracleBridgeEncodedCommand"];
  Run[command]
];

CallOracleG3[taskID_String, queryNumber_String, query_Association] := Module[{request, response, exitCode},
  request = <|"ProtocolSHA256" -> protocolHash, "TaskID" -> taskID, "QueryNumber" -> queryNumber,
    "Input" -> query["Input"], "InputSHA256" -> query["InputSHA256"],
    "GeneratedByTCCTKernel" -> True, "TestOutputAccessed" -> False,
    "HiddenProgramAccessedByLearner" -> False|>;
  Export[oracleRequestPath, request, "RawJSON", "Compact" -> False];
  exitCode = RunOracleG3["query", taskID, queryNumber];
  If[exitCode =!= 0, Print["FATAL: oracle query failed"]; Exit[20]];
  response = Import[oracleResponsePath, "RawJSON"];
  If[response["ProtocolSHA256"] =!= protocolHash || response["TaskID"] =!= taskID ||
      response["QueryNumber"] =!= queryNumber || response["Input"] =!= query["Input"] ||
      response["InputSHA256"] =!= query["InputSHA256"], Print["FATAL: invalid oracle response"]; Exit[21]];
  response
];

EvaluateTaskG3[task_Association] := Module[
  {queries, queryByHash, models, initialModels, unused, trace = {}, initialGuided, initialBaseline,
   guided, baseline, remainingCap, query, response, keep, queryNumber, stopReason, committed,
   runtime, value, rootConcept, guidedTotal = 0, baselineTotal = 0,
   guidedStates = 0, baselineStates = 0, parity = True},
  queries = BuildQueriesG3[task]; queryByHash = AssociationThread[Lookup[queries, "InputSHA256"] -> queries];
  models = BuildModelsG3[task, queries]; initialModels = models; unused = Lookup[queries, "InputSHA256"];
  initialGuided = FindMinimalPlanG4[models, unused, protocol["MaximumPlanningDepth"], queryByHash, True];
  initialBaseline = FindMinimalPlanG4[models, unused, protocol["MaximumPlanningDepth"], queryByHash, False];
  parity = initialGuided["Solvable"] === initialBaseline["Solvable"] &&
    initialGuided["RequiredDepth"] === initialBaseline["RequiredDepth"];
  guidedTotal += initialGuided["WorkCounters"]["QueryEvaluationCount"];
  baselineTotal += initialBaseline["WorkCounters"]["QueryEvaluationCount"];
  guidedStates += initialGuided["WorkCounters"]["ExpandedStateCount"];
  baselineStates += initialBaseline["WorkCounters"]["ExpandedStateCount"];
  {runtime, value} = AbsoluteTiming[While[DecisionCountG3[models] > 1 && Length[trace] < protocol["MaximumActiveQueriesPerTask"],
    remainingCap = Min[protocol["MaximumPlanningDepth"], protocol["MaximumActiveQueriesPerTask"] - Length[trace]];
    If[Length[trace] === 0, guided = initialGuided; baseline = initialBaseline,
      guided = FindMinimalPlanG4[models, unused, remainingCap, queryByHash, True];
      baseline = FindMinimalPlanG4[models, unused, remainingCap, queryByHash, False];
      parity = parity && guided["Solvable"] === baseline["Solvable"] &&
        guided["RequiredDepth"] === baseline["RequiredDepth"];
      guidedTotal += guided["WorkCounters"]["QueryEvaluationCount"];
      baselineTotal += baseline["WorkCounters"]["QueryEvaluationCount"];
      guidedStates += guided["WorkCounters"]["ExpandedStateCount"];
      baselineStates += baseline["WorkCounters"]["ExpandedStateCount"]];
    If[!TrueQ[guided["Solvable"]] || guided["RequiredDepth"] === 0,
      stopReason = "NO_PLAN_WITHIN_RESOURCE_DEPTH"; Break[]];
    rootConcept = InstantiateConceptG4[models, unused];
    query = queryByHash[guided["FirstInputSHA256"]];
    queryNumber = "KQ" <> IntegerString[Length[trace] + 1, 10, 2];
    response = CallOracleG3[task["TaskID"], queryNumber, query];
    keep = PredictionG3[#1, query["InputSHA256"]] === response["Output"] & /@ models;
    AppendTo[trace, <|"QueryNumber" -> queryNumber, "Input" -> query["Input"],
      "InputSHA256" -> query["InputSHA256"], "QueryKind" -> query["Kind"],
      "QueryLevel" -> query["Level"], "QueryPrefix" -> query["Prefix"],
      "AdmissionMode" -> "CONCEPT_GUIDED_EXACT_DP_WITH_FALLBACK",
      "CertifiedMinimumDepthBefore" -> guided["RequiredDepth"],
      "BaselineCertifiedMinimumDepthBefore" -> baseline["RequiredDepth"],
      "BaselineFirstInputSHA256" -> baseline["FirstInputSHA256"],
      "RootConceptMatched" -> TrueQ[rootConcept["Matched"]],
      "RootConceptID" -> Lookup[rootConcept, "ConceptID", Null],
      "RootConceptPreferredInputSHA256" -> rootConcept["InputSHA256"],
      "SelectedQueryWasRootConceptPreference" ->
        StringQ[rootConcept["InputSHA256"]] && query["InputSHA256"] === rootConcept["InputSHA256"],
      "RootConceptFallbackUsed" -> TrueQ[rootConcept["Matched"]] && !StringQ[rootConcept["InputSHA256"]],
      "GuidedWorkCounters" -> guided["WorkCounters"],
      "BaselineWorkCounters" -> baseline["WorkCounters"],
      "DecisionClassCountBefore" -> DecisionCountG3[models], "SemanticClassCountBefore" -> Length[models],
      "OracleOutput" -> response["Output"], "DecisionClassCountAfter" -> DecisionCountG3[Pick[models, keep, True]],
      "SemanticClassCountAfter" -> Length[Pick[models, keep, True]], "GeneratedByTCCTKernel" -> True,
      "TestOutputAccessed" -> False, "HiddenProgramAccessedByLearner" -> False|>];
    models = Pick[models, keep, True]; unused = DeleteCases[unused, query["InputSHA256"]];
  ]];
  committed = DecisionCountG3[models] === 1;
  If[!StringQ[stopReason], stopReason = If[committed, "DECISION_CERTIFIED", "NO_PLAN_WITHIN_RESOURCE_DEPTH"]];
  <|"TaskID" -> task["TaskID"], "RuntimeSeconds" -> runtime,
    "InitialSemanticClassCount" -> Length[initialModels], "InitialDecisionClassCount" -> DecisionCountG3[initialModels],
    "InitialPlanExistsWithinCap" -> TrueQ[initialGuided["Solvable"]],
    "InitialCertifiedMinimumDepth" -> If[TrueQ[initialGuided["Solvable"]], initialGuided["RequiredDepth"], Null],
    "InitialBaselineCertifiedMinimumDepth" -> If[TrueQ[initialBaseline["Solvable"]], initialBaseline["RequiredDepth"], Null],
    "PairedDepthParity" -> parity,
    "GuidedQueryEvaluationCount" -> guidedTotal,
    "BaselineQueryEvaluationCount" -> baselineTotal,
    "GuidedExpandedStateCount" -> guidedStates,
    "BaselineExpandedStateCount" -> baselineStates,
    "FinalSemanticClassCount" -> Length[models], "FinalDecisionClassCount" -> DecisionCountG3[models],
    "ActiveQueryCount" -> Length[trace], "ActiveQueryTrace" -> trace, "AdaptiveStopReason" -> stopReason,
    "DecisionCertified" -> committed, "TestPredictionCommitted" -> committed,
    "CommittedTestPrediction" -> If[committed, First[models]["TestPrediction"], Null],
    "Status" -> If[committed, "DECISION_CERTIFIED", "NO_PLAN_WITHIN_RESOURCE_DEPTH"],
    "TestOutputAccessed" -> False, "HiddenProgramAccessedByLearner" -> False|>
];

Print[protocol["Stage"]];
Print["Frozen historical concepts guide exact iterative-deepening DP; full fallback retained"];
resetCode = RunOracleG3["reset"];
If[resetCode =!= 0, Print["FATAL: oracle reset failed"]; Exit[22]];
{totalRuntime, taskRows} = AbsoluteTiming[EvaluateTaskG3 /@ public["Tasks"]];
Do[Print[row["TaskID"], " depth=", row["InitialCertifiedMinimumDepth"], " queries=",
  row["ActiveQueryCount"], " status=", row["Status"]], {row, taskRows}];
initialDepths = Lookup[taskRows, "InitialCertifiedMinimumDepth"];
tracePolicyPass = And @@ Flatten[Map[Function[row, Map[Function[q,
  q["AdmissionMode"] === "CONCEPT_GUIDED_EXACT_DP_WITH_FALLBACK" &&
  IntegerQ[q["CertifiedMinimumDepthBefore"]] && q["CertifiedMinimumDepthBefore"] >= 1 &&
  q["BaselineCertifiedMinimumDepthBefore"] === q["CertifiedMinimumDepthBefore"]], row["ActiveQueryTrace"]]], taskRows]];
commitCount = Count[Lookup[taskRows, "TestPredictionCommitted"], True];
safeStopCount = Count[taskRows, row_ /; !TrueQ[row["TestPredictionCommitted"]] &&
  row["ActiveQueryCount"] === 0 && row["AdaptiveStopReason"] === "NO_PLAN_WITHIN_RESOURCE_DEPTH"];
oracleLogCount = Length@Select[StringSplit[Import[oracleLogPath, "Text"], "\n"], StringLength[#1] > 0 &];
guidedQueryEvaluations = Total[Lookup[taskRows, "GuidedQueryEvaluationCount"]];
baselineQueryEvaluations = Total[Lookup[taskRows, "BaselineQueryEvaluationCount"]];
pairedDepthParity = And @@ Lookup[taskRows, "PairedDepthParity"];
rootConceptUseCount = Count[Flatten[Lookup[taskRows, "ActiveQueryTrace"], 1], q_ /;
  TrueQ[q["SelectedQueryWasRootConceptPreference"]]];
rootFallbackCount = Count[Flatten[Lookup[taskRows, "ActiveQueryTrace"], 1], q_ /;
  TrueQ[q["RootConceptFallbackUsed"]]];
preScorePass = Sort[DeleteCases[initialDepths, Null]] === {1, 2, 2, 3} && Count[initialDepths, Null] === 1 &&
  tracePolicyPass && commitCount === 4 && safeStopCount === 1 &&
  pairedDepthParity && guidedQueryEvaluations < baselineQueryEvaluations &&
  rootConceptUseCount >= 3 && rootFallbackCount >= 1 &&
  oracleLogCount === Total[Lookup[taskRows, "ActiveQueryCount"]] &&
  !MemberQ[Lookup[taskRows, "TestOutputAccessed"], True] &&
  !MemberQ[Lookup[taskRows, "HiddenProgramAccessedByLearner"], True];
result = <|"Stage" -> protocol["Stage"], "EvidenceStatus" -> protocol["EvidenceStatus"],
  "ProtocolSHA256" -> protocolHash, "WolframRunnerSHA256" -> runnerHash,
  "OracleResponderSHA256" -> oracleHash, "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version, "RuntimeSeconds" -> totalRuntime, "TaskResults" -> taskRows,
  "ObservedActiveQueryCounts" -> Lookup[taskRows, "ActiveQueryCount"],
  "ObservedInitialCertifiedDepthsWithinCap" -> initialDepths,
  "AggregateGuidedQueryEvaluationCount" -> guidedQueryEvaluations,
  "AggregateBaselineQueryEvaluationCount" -> baselineQueryEvaluations,
  "DeterministicPlanningWorkReduced" -> (guidedQueryEvaluations < baselineQueryEvaluations),
  "PairedDepthParity" -> pairedDepthParity,
  "RootConceptSelectedQueryCount" -> rootConceptUseCount,
  "RootConceptFallbackCount" -> rootFallbackCount,
  "OracleQueryLogLineCount" -> oracleLogCount, "TracePolicyPreScorePass" -> tracePolicyPass,
  "NativePreScorePass" -> preScorePass, "CoreRewriteFreezeDedupModified" -> False,
  "Conclusion" -> If[preScorePass, "CONCEPT_GUIDED_PLANNING_COMPLETE_AWAITING_SEALED_SCORE", "NATIVE_PRESCORE_FAILURE"]|>;
Export[resultPath, result, "RawJSON", "Compact" -> False];
Print["native pre-score pass=", preScorePass, " runtime=", totalRuntime];
Exit[0];
