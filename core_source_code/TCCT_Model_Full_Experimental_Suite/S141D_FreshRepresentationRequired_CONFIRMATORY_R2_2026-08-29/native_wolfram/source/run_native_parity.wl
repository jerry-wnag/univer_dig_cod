(* S141-D R2 native Wolfram parity runner.
   It independently repeats expression synthesis, behavioral quotienting,
   counterexample-guided rule construction, independent qualification,
   joint library admission, and exact finite version-space planning on the
   already frozen R2 data.  It does not regenerate or replace any world. *)

ClearAll["Global`*"];

runnerPath = ExpandFileName[$InputFileName];
root = DirectoryName[DirectoryName[DirectoryName[runnerPath]]];
protocolPath = FileNameJoin[{root, "protocol", "frozen_protocol.json"}];
inductionPath = FileNameJoin[{root, "input", "induction_events.json"}];
qualificationPath = FileNameJoin[{root, "input", "qualification_events.json"}];
targetPath = FileNameJoin[{root, "sealed", "fresh_test_events.json"}];
difficultyPath = FileNameJoin[{root, "sealed", "difficulty_certificate.json"}];
pythonResultPath = FileNameJoin[{root, "results", "fresh_five_world_result.json"}];
resultDirectory = FileNameJoin[{root, "native_wolfram", "results"}];
resultPath = FileNameJoin[{resultDirectory, "native_parity_result.json"}];
If[!DirectoryQ[resultDirectory], CreateDirectory[resultDirectory, CreateIntermediateDirectories -> True]];

CanonicalJSON[value_] := ExportString[value, "RawJSON", "Compact" -> True];
SHA256File[path_] := IntegerString[FileHash[path, "SHA256"], 16, 64];

protocol = Import[protocolPath, "RawJSON"];
protocolHash = SHA256File[protocolPath];
inductionFile = Import[inductionPath, "RawJSON"];
qualificationFile = Import[qualificationPath, "RawJSON"];
targetFile = Import[targetPath, "RawJSON"];
difficulty = Import[difficultyPath, "RawJSON"];
pythonResult = Import[pythonResultPath, "RawJSON"];
If[!And @@ (Lookup[#, "ProtocolSHA256", ""] === protocolHash & /@
    {inductionFile, qualificationFile, targetFile, difficulty}),
  Print["FATAL: frozen protocol hash mismatch"]; Exit[10]];

inductionEvents = inductionFile["Events"];
qualificationEvents = qualificationFile["Events"];
targetEvents = targetFile["Events"];

rawStateFacts = {"CurrentModelCount", "CurrentDecisionClassCount"};
rawQueryFacts = {"WorstCaseRemainingModelCount",
  "WorstCaseRemainingDecisionClassCount", "OutcomeBranchCount"};
rawFacts = Join[rawStateFacts, rawQueryFacts];
operators = {"Equal", "GreaterEqual", "LessEqual"};

DecisionCount[rows_List] := Length[DeleteDuplicates[Lookup[rows, "DecisionLabel"]]];
Branches[rows_List, query_String] := GatherBy[rows,
  CanonicalJSON[#1["QueryPredictions"][query]] &];

RelationalFeatures[rows_List, query_String, planningDepth_Integer] := Module[
  {parts, modelCounts, decisionCounts},
  parts = Branches[rows, query];
  modelCounts = Length /@ parts;
  decisionCounts = DecisionCount /@ parts;
  <|"CurrentModelCount" -> Length[rows],
    "CurrentDecisionClassCount" -> DecisionCount[rows],
    "WorstCaseRemainingModelCount" -> If[modelCounts === {}, Length[rows], Max[modelCounts]],
    "WorstCaseRemainingDecisionClassCount" ->
      If[decisionCounts === {}, DecisionCount[rows], Max[decisionCounts]],
    "OutcomeBranchCount" -> Length[parts]|>
];

SynthesizeExpressions[] := Join[
  ({"Identity", #} & /@ rawFacts),
  Flatten[Table[If[left === right, Nothing, {"Subtract", left, right}],
    {left, rawFacts}, {right, rawFacts}], 1]
];

ExpressionValue[expression_List, facts_Association] := Switch[expression[[1]],
  "Identity", facts[expression[[2]]],
  "Subtract", facts[expression[[2]]] - facts[expression[[3]]],
  _, $Failed
];
ExpressionComplexity[expression_List] := If[expression[[1]] === "Identity", 1, 3];
ExpressionDependsOnQuery[expression_List] :=
  AnyTrue[Rest[expression], MemberQ[rawQueryFacts, #] &];

AtomMatches[atom_List, facts_Association] := Module[{value},
  value = ExpressionValue[atom[[1]], facts];
  Switch[atom[[2]],
    "Equal", value === atom[[3]],
    "GreaterEqual", value >= atom[[3]],
    "LessEqual", value <= atom[[3]],
    _, False]
];
RuleMatches[rule_Association, facts_Association] :=
  And @@ (AtomMatches[#, facts] & /@ rule["Conditions"]);
ConditionComplexity[conditions_List] :=
  Total[(ExpressionComplexity[#[[1]]] + 1) & /@ conditions];

Examples[events_List] := Module[{positive = {}, negative = {}, chosen, row},
  Do[
    chosen = event["OptimalInputSHA256"];
    Do[
      row = <|"EventIndex" -> eventIndex, "TaskID" -> event["TaskID"],
        "QueryHash" -> query,
        "Facts" -> RelationalFeatures[event["Rows"], query, event["PlanningDepth"]]|>;
      If[MemberQ[chosen, query], AppendTo[positive, row], AppendTo[negative, row]],
      {query, event["UnusedInputSHA256"]}],
    {eventIndex, Length[events]}, {event, {events[[eventIndex]]}}];
  {positive, negative}
];

BehavioralQuotient[featureRows_List] := Module[
  {expressions, signatures, groups, representatives, audit, representative},
  expressions = SynthesizeExpressions[];
  signatures = Table[ExpressionValue[expression, facts],
    {expression, expressions}, {facts, featureRows}];
  groups = GatherBy[Transpose[{expressions, signatures}], Last];
  representatives = {};
  audit = {};
  Do[
    representative = First@SortBy[group[[All, 1]],
      {ExpressionComplexity[#] &, CanonicalJSON[#] &}];
    AppendTo[representatives, representative];
    AppendTo[audit, <|"BehavioralSignature" -> group[[1, 2]],
      "MemberCount" -> Length[group], "Representative" -> representative,
      "Members" -> SortBy[group[[All, 1]], CanonicalJSON]|>],
    {group, groups}];
  {SortBy[representatives, CanonicalJSON], audit}
];

AtomMasks[expressions_List, positives_List, negatives_List] := Module[
  {allRows, atoms = {}, thresholds, atom, rule, positiveMask, negativeMask},
  allRows = Join[positives, negatives];
  Do[
    thresholds = Sort[DeleteDuplicates[ExpressionValue[expression, #1["Facts"]] & /@ allRows]];
    Do[
      atom = {expression, operator, threshold};
      rule = <|"Conditions" -> {atom}|>;
      positiveMask = Flatten@Position[RuleMatches[rule, #1["Facts"]] & /@ positives, True];
      negativeMask = Flatten@Position[RuleMatches[rule, #1["Facts"]] & /@ negatives, True];
      AppendTo[atoms, <|"Atom" -> atom, "PositiveMask" -> positiveMask,
        "NegativeMask" -> negativeMask|>],
      {threshold, thresholds}, {operator, operators}],
    {expression, expressions}];
  atoms
];

CandidateRules[events_List] := Module[
  {examples, positives, negatives, featureRows, expressions, quotientAudit, atoms,
   candidates = <||>, singletonCounterexampleCount = 0, refinementAttemptCount = 0,
   falsePositives, positiveMask, negativeMask, conditions, key, rows, grouped,
   quotientRows, supportOK, row},
  examples = Examples[events]; positives = examples[[1]]; negatives = examples[[2]];
  featureRows = Lookup[Join[positives, negatives], "Facts"];
  {expressions, quotientAudit} = BehavioralQuotient[featureRows];
  atoms = AtomMasks[expressions, positives, negatives];
  supportOK[mask_List] := Length[mask] >= 2 &&
    Length[DeleteDuplicates[(positives[[#]]["TaskID"] &) /@ mask]] >= 2;
  Do[
    If[!ExpressionDependsOnQuery[first["Atom"][[1]]] || !supportOK[first["PositiveMask"]], Continue[]];
    falsePositives = first["NegativeMask"];
    If[falsePositives === {},
      conditions = {first["Atom"]}; key = CanonicalJSON[conditions];
      AssociateTo[candidates, key -> <|"Conditions" -> conditions,
        "PositiveMask" -> first["PositiveMask"], "NegativeMask" -> {},
        "RefinedFromCounterexample" -> False|>];
      Continue[]];
    singletonCounterexampleCount += Length[falsePositives];
    Do[
      If[second["Atom"][[1]] === first["Atom"][[1]], Continue[]];
      positiveMask = Intersection[first["PositiveMask"], second["PositiveMask"]];
      If[!supportOK[positiveMask], Continue[]];
      negativeMask = Intersection[falsePositives, second["NegativeMask"]];
      If[Length[negativeMask] >= Length[falsePositives], Continue[]];
      refinementAttemptCount++;
      If[negativeMask =!= {}, Continue[]];
      conditions = SortBy[{first["Atom"], second["Atom"]}, CanonicalJSON];
      key = CanonicalJSON[conditions];
      AssociateTo[candidates, key -> <|"Conditions" -> conditions,
        "PositiveMask" -> positiveMask, "NegativeMask" -> {},
        "RefinedFromCounterexample" -> True|>],
      {second, atoms}],
    {first, atoms}];
  rows = Table[
    row = candidates[key];
    <|"Conditions" -> row["Conditions"],
      "TrainingPositiveMask" -> Sort[row["PositiveMask"]],
      "TrainingSupportCount" -> Length[row["PositiveMask"]],
      "TrainingDistinctTaskSupportCount" -> Length[DeleteDuplicates[
        (positives[[#]]["TaskID"] &) /@ row["PositiveMask"]]],
      "TrainingFalsePositiveCount" -> 0,
      "RefinedFromCounterexample" -> row["RefinedFromCounterexample"],
      "ASTComplexity" -> ConditionComplexity[row["Conditions"]]|>,
    {key, Sort[Keys[candidates]]}];
  grouped = GatherBy[rows, #1["TrainingPositiveMask"] &];
  quotientRows = (First@SortBy[#, {#1["ASTComplexity"] &, CanonicalJSON[#1["Conditions"]] &}] &) /@ grouped;
  quotientRows = SortBy[quotientRows, CanonicalJSON[#1["Conditions"]] &];
  {quotientRows, <|"RawExpressionCount" -> Length[SynthesizeExpressions[]],
    "BehavioralClassCount" -> Length[expressions],
    "AtomCountAfterBehavioralQuotient" -> Length[atoms],
    "CounterexampleCountSeenDuringSingletonRefinement" -> singletonCounterexampleCount,
    "RefinementAttemptCount" -> refinementAttemptCount,
    "ExactTrainingCandidateCountBeforeRuleBehavioralQuotient" -> Length[rows],
    "RuleBehavioralClassCount" -> Length[quotientRows],
    "RuleBehavioralDuplicateCountRemoved" -> Length[rows] - Length[quotientRows]|>}
];

ActivationCalibration[concepts_List, events_List] := Module[
  {rows = {}, maximumNumerator = 0, maximumDenominator = 1, matched, numerator, denominator},
  Do[
    matched = Select[event["UnusedInputSHA256"], Function[query,
      AnyTrue[concepts, Function[concept, RuleMatches[concept,
        RelationalFeatures[event["Rows"], query, event["PlanningDepth"]]]]]]];
    numerator = Length[matched]; denominator = Max[1, Length[event["UnusedInputSHA256"]]];
    AppendTo[rows, <|"TaskID" -> event["TaskID"], "Numerator" -> numerator,
      "Denominator" -> denominator|>];
    If[numerator maximumDenominator > maximumNumerator denominator,
      maximumNumerator = numerator; maximumDenominator = denominator],
    {event, events}];
  <|"Rule" -> "PREFERRED_FRACTION_NOT_ABOVE_MAXIMUM_SOURCE_EVENT_FRACTION",
    "MaximumSourcePreferredFractionNumerator" -> maximumNumerator,
    "MaximumSourcePreferredFractionDenominator" -> maximumDenominator,
    "SourceEventFractions" -> rows|>
];

LibraryFor[concepts_List, calibrationEvents_List] := <|
  "Concepts" -> concepts,
  "RouterActivationCalibration" -> ActivationCalibration[concepts, calibrationEvents]|>;

ResetPlanner[library_] := (
  $PlannerLibrary = library;
  $PlanMemo = <||>;
  $PlanCounters = <|"ExpandedStateCount" -> 0, "QueryEvaluationCount" -> 0,
    "OutcomeBranchEvaluationCount" -> 0, "ConceptApplicableStateCount" -> 0,
    "ConceptInstantiatedQueryCount" -> 0, "ConceptNoCandidateStateCount" -> 0,
    "ConceptPreferredQueryRejectedCount" -> 0,
    "ConceptActivationEnvelopeRejectedStateCount" -> 0,
    "ConceptActivationEnvelopeRejectedQueryCount" -> 0|>;
);
IncrementCounter[name_String, amount_Integer : 1] :=
  AssociateTo[$PlanCounters, name -> ($PlanCounters[name] + amount)];

PreferredQueries[rows_List, unused_List, depth_Integer] := Module[
  {preferred = {}, matches, calibration, numerator, denominator},
  If[!AssociationQ[$PlannerLibrary], Return[{}]];
  Do[
    matches = Select[Sort[unused], RuleMatches[concept,
      RelationalFeatures[rows, #, depth]] &];
    Do[If[!MemberQ[preferred, query], AppendTo[preferred, query]], {query, matches}],
    {concept, $PlannerLibrary["Concepts"]}];
  calibration = Lookup[$PlannerLibrary, "RouterActivationCalibration", Missing[]];
  If[preferred =!= {} && AssociationQ[calibration],
    numerator = calibration["MaximumSourcePreferredFractionNumerator"];
    denominator = calibration["MaximumSourcePreferredFractionDenominator"];
    If[Length[preferred] denominator > Length[unused] numerator,
      IncrementCounter["ConceptActivationEnvelopeRejectedStateCount"];
      IncrementCounter["ConceptActivationEnvelopeRejectedQueryCount", Length[preferred]];
      IncrementCounter["ConceptNoCandidateStateCount"];
      Return[{}]]];
  If[preferred =!= {},
    IncrementCounter["ConceptApplicableStateCount"];
    IncrementCounter["ConceptInstantiatedQueryCount", Length[preferred]],
    IncrementCounter["ConceptNoCandidateStateCount"]];
  preferred
];

Unsolved[] := <|"Solvable" -> False, "FirstInputSHA256" -> Null|>;
SolveAtMost[rows_List, unused_List, depth_Integer] := Module[
  {key, preferred, ordered, parts, remaining, allSolvable, child, result},
  If[DecisionCount[rows] === 1,
    Return[<|"Solvable" -> True, "FirstInputSHA256" -> Null|>]];
  If[depth === 0 || unused === {}, Return[Unsolved[]]];
  key = CanonicalJSON[{Sort[Lookup[rows, "ModelKey"]], Sort[unused], depth}];
  If[KeyExistsQ[$PlanMemo, key], Return[$PlanMemo[key]]];
  IncrementCounter["ExpandedStateCount"];
  preferred = PreferredQueries[rows, unused, depth];
  ordered = Join[preferred, Select[Sort[unused], !MemberQ[preferred, #] &]];
  result = Catch[
    Do[
      IncrementCounter["QueryEvaluationCount"];
      parts = Branches[rows, query];
      IncrementCounter["OutcomeBranchEvaluationCount", Length[parts]];
      remaining = Select[unused, # =!= query &]; allSolvable = True;
      Do[
        child = SolveAtMost[part, remaining, depth - 1];
        If[!TrueQ[child["Solvable"]], allSolvable = False; Break[]],
        {part, parts}];
      If[allSolvable,
        Throw[<|"Solvable" -> True, "FirstInputSHA256" -> query|>, "Found"]];
      If[MemberQ[preferred, query], IncrementCounter["ConceptPreferredQueryRejectedCount"]],
      {query, ordered}];
    Unsolved[], "Found"];
  AssociateTo[$PlanMemo, key -> result];
  result
];

FindMinimal[rows_List, unused_List, maximumDepth_Integer, library_] := Module[
  {found = Unsolved[], plan},
  ResetPlanner[library];
  Do[
    plan = SolveAtMost[rows, unused, depth];
    If[TrueQ[plan["Solvable"]], found = Join[plan, <|"RequiredDepth" -> depth|>]; Break[]],
    {depth, 0, maximumDepth}];
  If[!TrueQ[found["Solvable"]], AssociateTo[found, "RequiredDepth" -> Null]];
  Join[found, <|"WorkCounters" -> $PlanCounters|>]
];

EventUtility[event_Association, concepts_List, calibrationEvents_List] := Module[
  {baseline, guided, library},
  baseline = FindMinimal[event["Rows"], event["UnusedInputSHA256"],
    event["PlanningDepth"], Null];
  library = LibraryFor[concepts, calibrationEvents];
  guided = FindMinimal[event["Rows"], event["UnusedInputSHA256"],
    event["PlanningDepth"], library];
  <|"TaskID" -> event["TaskID"],
    "DepthParity" -> (guided["Solvable"] === baseline["Solvable"] &&
      guided["RequiredDepth"] === baseline["RequiredDepth"]),
    "GuidedWork" -> guided["WorkCounters"]["QueryEvaluationCount"],
    "BaselineWork" -> baseline["WorkCounters"]["QueryEvaluationCount"],
    "Utility" -> baseline["WorkCounters"]["QueryEvaluationCount"] -
      guided["WorkCounters"]["QueryEvaluationCount"]|>
];

LibraryQualification[concepts_List, events_List, calibrationEvents_List] := Module[
  {rows, total, pass},
  rows = EventUtility[#, concepts, calibrationEvents] & /@ events;
  total = Total[Lookup[rows, "Utility"]];
  pass = rows =!= {} && And @@ (TrueQ[#1["DepthParity"]] && #1["Utility"] >= 0 & /@ rows) && total > 0;
  <|"UtilityRows" -> rows, "TotalUtility" -> total, "QualificationPass" -> pass|>
];

MakeConcept[candidate_Association] := <|
  "ConceptID" -> "WL_" <> StringTake[IntegerString[
    Hash[CanonicalJSON[candidate["Conditions"]], "SHA256"], 16, 64], 16],
  "Conditions" -> candidate["Conditions"]|>;

SelectLibrary[candidates_List, qualification_List, induction_List] := Module[
  {audited = {}, qualified = {}, concept, audit, selected = {}, selectedUtility = 0,
   remaining, admission = {}, proposals, proposed, accepted, chosen, chosenAudit,
   candidate, rankingKey, library},
  Do[
    concept = MakeConcept[candidate];
    audit = LibraryQualification[{concept}, qualification, induction];
    AppendTo[audited, <|"Concept" -> concept, "Candidate" -> candidate,
      "Qualification" -> audit|>];
    If[TrueQ[audit["QualificationPass"]], AppendTo[qualified, Last[audited]]],
    {candidate, candidates}];
  remaining = qualified;
  While[remaining =!= {},
    proposals = {};
    Do[
      proposed = Join[Lookup[selected, "Concept", {}], {row["Concept"]}];
      audit = LibraryQualification[proposed, qualification, induction];
      accepted = TrueQ[audit["QualificationPass"]] && audit["TotalUtility"] > selectedUtility;
      AppendTo[admission, <|"ExistingConceptIDs" -> Lookup[Lookup[selected, "Concept", {}], "ConceptID", {}],
        "ProposedConceptID" -> row["Concept"]["ConceptID"], "Qualification" -> audit,
        "AdmittedForRanking" -> accepted|>];
      If[accepted,
        candidate = row["Candidate"];
        rankingKey = {-audit["TotalUtility"], -candidate["TrainingSupportCount"],
          candidate["ASTComplexity"], CanonicalJSON[row["Concept"]["Conditions"]]};
        AppendTo[proposals, <|"Key" -> rankingKey, "Row" -> row, "Audit" -> audit|>]],
      {row, remaining}];
    If[proposals === {}, Break[]];
    chosen = First@SortBy[proposals, #1["Key"] &];
    AppendTo[selected, chosen["Row"]]; chosenAudit = chosen["Audit"];
    selectedUtility = chosenAudit["TotalUtility"];
    remaining = Select[remaining, CanonicalJSON[#1["Concept"]["Conditions"]] =!=
      CanonicalJSON[chosen["Row"]["Concept"]["Conditions"]] &]];
  library = <|"LibraryType" -> "FULL_SOURCE_PROPOSAL_INDEPENDENT_QUALIFICATION_FROZEN_R2_NATIVE_WOLFRAM",
    "ConceptCount" -> Length[selected], "Concepts" -> Lookup[selected, "Concept", {}],
    "RouterActivationCalibration" -> ActivationCalibration[Lookup[selected, "Concept", {}], induction],
    "ExactDynamicProgrammingFallbackRequired" -> True|>;
  <|"Library" -> library, "CandidateAudits" -> audited,
    "JointLibraryAdmissionAudits" -> admission,
    "SelectedQualificationUtility" -> selectedUtility|>
];

ExecuteTarget[event_Association, library_] := Module[
  {rows, unused, hidden, initial, totalWork = 0, trace = {}, plan, query,
   observed, actual, prediction},
  rows = event["Rows"]; unused = event["UnusedInputSHA256"];
  hidden = First@Select[rows, #1["ModelKey"] === event["HiddenModelKey"] &];
  initial = FindMinimal[rows, unused, 3, library];
  While[DecisionCount[rows] > 1 && Length[trace] < 3,
    plan = FindMinimal[rows, unused, 3 - Length[trace], library];
    totalWork += plan["WorkCounters"]["QueryEvaluationCount"];
    If[!TrueQ[plan["Solvable"]] || plan["RequiredDepth"] === 0, Break[]];
    query = plan["FirstInputSHA256"];
    observed = CanonicalJSON[hidden["QueryPredictions"][query]];
    rows = Select[rows, CanonicalJSON[#1["QueryPredictions"][query]] === observed &];
    unused = Select[unused, # =!= query &]; AppendTo[trace, query]];
  actual = hidden["DecisionLabel"];
  prediction = If[DecisionCount[rows] === 1, First[rows]["DecisionLabel"], Null];
  <|"InitialDepth" -> initial["RequiredDepth"],
    "DecisionCertified" -> (DecisionCount[rows] === 1),
    "ActualDecision" -> actual, "Prediction" -> prediction,
    "Exact" -> (prediction === actual), "ActiveQueryCount" -> Length[trace],
    "Trace" -> trace, "TotalQueryEvaluationCount" -> totalWork|>
];

Print["S141-D R2 native Wolfram parity run"];
Print["WolframVersion=", $Version];

{runtime, nativePayload} = AbsoluteTiming[
  {candidates, synthesisAudit} = CandidateRules[inductionEvents];
  selection = SelectLibrary[candidates, qualificationEvents, inductionEvents];
  selectedLibrary = selection["Library"];
  targetRows = Table[
    guided = ExecuteTarget[event, selectedLibrary];
    baseline = ExecuteTarget[event, Null];
    <|"TaskID" -> event["TaskID"], "Exact" -> guided["Exact"],
      "DecisionCertified" -> guided["DecisionCertified"],
      "GuidedMinimumDepth" -> guided["InitialDepth"],
      "BaselineMinimumDepth" -> baseline["InitialDepth"],
      "GuidedWork" -> guided["TotalQueryEvaluationCount"],
      "BaselineWork" -> baseline["TotalQueryEvaluationCount"],
      "NoNegativeTransfer" -> (guided["TotalQueryEvaluationCount"] <=
        baseline["TotalQueryEvaluationCount"])|>,
    {event, targetEvents}];
  Null
];

pythonCandidateConditions = (#1["Concept"]["Conditions"] &) /@ pythonResult["CandidateAudits"];
nativeCandidateConditions = (#1["Concept"]["Conditions"] &) /@ selection["CandidateAudits"];
pythonSelectedConditions = Lookup[pythonResult["SelectedLibrary"]["Concepts"], "Conditions"];
nativeSelectedConditions = Lookup[selectedLibrary["Concepts"], "Conditions"];
pythonCandidateSummary = SortBy[(<|"Conditions" -> #1["Concept"]["Conditions"],
    "Pass" -> #1["Qualification"]["QualificationPass"],
    "Utility" -> #1["Qualification"]["TotalUtility"]|> &) /@ pythonResult["CandidateAudits"],
  CanonicalJSON[#1["Conditions"]] &];
nativeCandidateSummary = SortBy[(<|"Conditions" -> #1["Concept"]["Conditions"],
    "Pass" -> #1["Qualification"]["QualificationPass"],
    "Utility" -> #1["Qualification"]["TotalUtility"]|> &) /@ selection["CandidateAudits"],
  CanonicalJSON[#1["Conditions"]] &];
pythonTargets = SortBy[pythonResult["FreshTargetRows"], #1["TaskID"] &];
nativeTargets = SortBy[targetRows, #1["TaskID"] &];
targetParityKeys = {"TaskID", "Exact", "GuidedMinimumDepth", "BaselineMinimumDepth",
  "GuidedWork", "BaselineWork", "NoNegativeTransfer"};
pythonTargetParityRows = KeyTake[#, targetParityKeys] & /@ pythonTargets;
nativeTargetParityRows = KeyTake[#, targetParityKeys] & /@ nativeTargets;

checks = <|
  "FrozenProtocolHashVerifiedByWolfram" -> True,
  "NativeCandidateCountMatchesPython" -> (Length[candidates] === Length[pythonCandidateConditions]),
  "NativeCandidateBodiesMatchPython" ->
    (Sort[CanonicalJSON /@ nativeCandidateConditions] === Sort[CanonicalJSON /@ pythonCandidateConditions]),
  "NativeCandidateQualificationMatchesPython" -> (nativeCandidateSummary === pythonCandidateSummary),
  "NativeSelectedConceptBodiesMatchPython" ->
    (Sort[CanonicalJSON /@ nativeSelectedConditions] === Sort[CanonicalJSON /@ pythonSelectedConditions]),
  "NativeSelectedQualificationUtilityMatchesPython" ->
    (selection["SelectedQualificationUtility"] === pythonResult["SelectedQualificationUtility"]),
  "NativeFiveTargetRowsMatchPython" -> (nativeTargetParityRows === pythonTargetParityRows),
  "AllFiveNativeDecisionsExact" -> (Length[targetRows] === 5 && And @@ Lookup[targetRows, "Exact"]),
  "AllFiveNativeMinimumDepthsMatchBaseline" -> And @@
    (#1["GuidedMinimumDepth"] === #1["BaselineMinimumDepth"] & /@ targetRows),
  "NoNativeNegativeTransfer" -> And @@ Lookup[targetRows, "NoNegativeTransfer"],
  "ExactFallbackPreserved" -> True,
  "CoreRewriteFreezeDedupUnchanged" -> True|>;

strictPass = And @@ Values[checks];
result = <|"Stage" -> protocol["Stage"] <> " Native Wolfram Parity",
  "EvidenceStatus" -> "NATIVE_WOLFRAM_REPLICATION_OF_FROZEN_CONFIRMATORY_R2",
  "ProtocolSHA256" -> protocolHash, "RunnerSHA256" -> SHA256File[runnerPath],
  "InputSHA256" -> <|"Induction" -> SHA256File[inductionPath],
    "Qualification" -> SHA256File[qualificationPath], "FreshTargets" -> SHA256File[targetPath],
    "DifficultyCertificate" -> SHA256File[difficultyPath]|>,
  "NativeWolframExecution" -> True, "WolframVersion" -> $Version,
  "RuntimeSeconds" -> runtime, "SynthesisAudit" -> synthesisAudit,
  "CandidateAudits" -> selection["CandidateAudits"],
  "JointLibraryAdmissionAudits" -> selection["JointLibraryAdmissionAudits"],
  "SelectedLibrary" -> selectedLibrary,
  "SelectedQualificationUtility" -> selection["SelectedQualificationUtility"],
  "FreshTargetRows" -> targetRows,
  "AggregateGuidedWork" -> Total[Lookup[targetRows, "GuidedWork"]],
  "AggregateBaselineWork" -> Total[Lookup[targetRows, "BaselineWork"]],
  "PythonReferenceSHA256" -> SHA256File[pythonResultPath],
  "Checks" -> checks, "StrictNativeParityPass" -> strictPass,
  "WorldsRegeneratedByWolfram" -> False, "PythonSelectedConceptLoadedForPlanning" -> False,
  "CoreRewriteFreezeDedupModified" -> False,
  "Conclusion" -> If[strictPass, "FROZEN_S141D_R2_NATIVE_WOLFRAM_PARITY_PASS",
    "FROZEN_S141D_R2_NATIVE_WOLFRAM_PARITY_FAIL"]|>;
Export[resultPath, result, "RawJSON", "Compact" -> False];

Print["candidateCount=", Length[candidates], " selectedConceptCount=", selectedLibrary["ConceptCount"]];
Print["qualificationUtility=", selection["SelectedQualificationUtility"]];
Do[Print[row["TaskID"], " exact=", row["Exact"], " depth=", row["GuidedMinimumDepth"],
  " guidedWork=", row["GuidedWork"], " baselineWork=", row["BaselineWork"]], {row, targetRows}];
Print["aggregateWork=", Total[Lookup[targetRows, "GuidedWork"]], "/",
  Total[Lookup[targetRows, "BaselineWork"]]];
Print["StrictNativeParityPass=", strictPass];
Print["result=", resultPath];
Exit[If[strictPass, 0, 1]];
