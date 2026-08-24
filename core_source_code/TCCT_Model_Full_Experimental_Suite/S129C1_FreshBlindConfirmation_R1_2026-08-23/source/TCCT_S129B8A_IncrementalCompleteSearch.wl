(* ::Package:: *)

(* S129-B8A: incremental survivor maintenance over the frozen B7 basis. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
b7RunnerPath = FileNameJoin[{sourceDirectory, "TCCT_S129B7_CostCompleteSearchAudit.wl"}];
b7Text = Import[b7RunnerPath, "Text"];
marker = "Print[\"S129-B7 bounded cost-complete search audit R1\"]";
markerPosition = First@First@StringPosition[b7Text, marker];
ToExpression[StringTake[b7Text, markerPosition - 1], InputForm];

b8Manifest = Import[FileNameJoin[{rootDirectory, "protocol", "S129B8A_manifest.json"}],
  "RawJSON"];
b7Frozen = Import[FileNameJoin[{rootDirectory, "input", "frozen_S129B7_result.json"}],
  "RawJSON"];
b7ByID = AssociationThread[Lookup[b7Frozen["FormalResults"], "WorldID"] ->
  b7Frozen["FormalResults"]];
resultDirectory = FileNameJoin[{rootDirectory, "results"}];
controlDirectory = FileNameJoin[{rootDirectory, "negative_controls"}];
If[!DirectoryQ[resultDirectory], CreateDirectory[resultDirectory]];
If[!DirectoryQ[controlDirectory], CreateDirectory[controlDirectory]];

UniverseIndicesB8[ints_List, dimensions_List] := Table[
  Select[Range[Length[ints]],
    Min[ints[[#, "Values"]]] >= 0 && Max[ints[[#, "Values"]]] < dimension &],
  {dimension, dimensions}];

InitializePoolsB8[world_Association, basis_Association,
  predicates_List] := Module[
  {universes, pools, selectedPredicates,
   componentCount = Length[world["CoordinateDimensions"]]},
  universes = UniverseIndicesB8[basis["Ints"], world["CoordinateDimensions"]];
  selectedPredicates = Take[predicates, UpTo[predicateSearchCap]];
  pools = Table[<|"DirectIndices" -> universes[[component]],
      "PredicateBranches" -> Table[
        <|"TrueIndices" -> universes[[component]],
          "FalseIndices" -> universes[[component]],
          "TrueObservationCount" -> 0,
          "FalseObservationCount" -> 0|>,
        {Length[selectedPredicates]}],
      "ObservationCount" -> 0|>,
    {action, world["ActionCount"]}, {component, componentCount}];
  <|"Universes" -> universes, "SelectedPredicates" -> selectedPredicates,
    "Pools" -> pools|>
];

UpdatePoolsB8[pools_List, ints_List, predicates_List,
  record_Association] := Module[
  {copy = pools, action = record["Action"], state = record["State"],
   target = record["TargetCoordinate"], direct, branches, branch, truth,
   key, checks = 0, component, predicateIndex},
  Do[
    direct = copy[[action, component, "DirectIndices"]];
    checks += Length[direct];
    direct = Select[direct,
      ints[[#, "Values", state]] === target[[component]] &];
    branches = copy[[action, component, "PredicateBranches"]];
    Do[
      truth = TrueQ[predicates[[predicateIndex, "Values", state]]];
      key = If[truth, "TrueIndices", "FalseIndices"];
      branch = branches[[predicateIndex, key]];
      checks += Length[branch];
      branches[[predicateIndex, key]] = Select[branch,
        ints[[#, "Values", state]] === target[[component]] &];
      If[truth,
        branches[[predicateIndex, "TrueObservationCount"]]++,
        branches[[predicateIndex, "FalseObservationCount"]]++],
      {predicateIndex, Length[predicates]}];
    copy[[action, component, "DirectIndices"]] = direct;
    copy[[action, component, "PredicateBranches"]] = branches;
    copy[[action, component, "ObservationCount"]] =
      copy[[action, component, "ObservationCount"]] + 1,
    {component, Length[target]}];
  <|"Pools" -> copy, "FilterChecks" -> checks|>
];

PoolPanelB8[pool_Association, ints_List, predicates_List] := Module[
  {store = <||>, directPanel, branches, yesLeaves, noLeaves, predicate,
   yes, no, candidate, ranked, predicateIndex},
  directPanel = ints[[Take[pool["DirectIndices"], UpTo[candidateCap]]]];
  Do[AddBestB6[store, item], {item, directPanel}];
  If[pool["ObservationCount"] >= 2,
    branches = pool["PredicateBranches"];
    Do[
      If[branches[[predicateIndex, "TrueObservationCount"]] === 0 ||
          branches[[predicateIndex, "FalseObservationCount"]] === 0,
        Continue[]];
      predicate = predicates[[predicateIndex]];
      yesLeaves = ints[[Take[branches[[predicateIndex, "TrueIndices"]], UpTo[2]]]];
      noLeaves = ints[[Take[branches[[predicateIndex, "FalseIndices"]], UpTo[2]]]];
      Do[
        candidate = MakeExprB6[
          {"If", predicate["AST"], yes["AST"], no["AST"]},
          1 + predicate["Nodes"] + yes["Nodes"] + no["Nodes"],
          5 + predicate["Bits"] + yes["Bits"] + no["Bits"],
          MapThread[If, {predicate["Values"], yes["Values"], no["Values"]}],
          "Int"];
        AddBestB6[store, candidate],
        {yes, yesLeaves}, {no, noLeaves}],
      {predicateIndex, Length[predicates]}]];
  ranked = SortBy[Values[store], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}];
  Take[ranked, UpTo[candidateCap]]
];
PanelMatrixB8[pools_List, ints_List, predicates_List] :=
  Map[PoolPanelB8[#, ints, predicates] &, pools, {2}];

RunIncrementalLearnerB8[world_Association, table_List, basis_Association,
  predicates_List, mode_String] := Module[
  {started = AbsoluteTime[], initialized, pools, selectedPredicates,
   observations = {},
   trace = {}, update, query, unqueried, panel, ranked, maxScore,
   programs = Null, errors, counterexample, outcome = "BUDGET_EXHAUSTED_FALLBACK",
   exact = False, equivalenceCalls = 0, equivalenceCounterexamples = 0,
   filterChecks = 0, programBits = Null,
   tableBits, phiBits, totalBits, ratio, state, action, record,
   panelCounts},
  initialized = InitializePoolsB8[world, basis, predicates];
  selectedPredicates = initialized["SelectedPredicates"];
  pools = initialized["Pools"];
  Do[
    record = <|"State" -> world["StartState"], "Action" -> action,
      "TargetCoordinate" -> OracleTargetB6[world, table, world["StartState"], action],
      "Source" -> "INITIAL_SEED"|>;
    observations = Append[observations, record];
    update = UpdatePoolsB8[pools, basis["Ints"], selectedPredicates,
      record]; pools = update["Pools"];
    filterChecks += update["FilterChecks"],
    {action, world["ActionCount"]}];
  While[Length[observations] <= membershipBudget && equivalenceCalls <= equivalenceBudget,
    panel = PanelMatrixB8[pools, basis["Ints"], selectedPredicates];
    If[!MatrixNonemptyB6[panel], outcome = "NO_SURVIVING_PROGRAM_FALLBACK"; Break[]];
    panelCounts = Map[Length, panel, {2}];
    unqueried = Select[Flatten[Table[{state, action},
        {state, world["StateCount"]}, {action, world["ActionCount"]}], 1],
      Function[pair, !AnyTrue[observations,
        Function[item, item["State"] === pair[[1]] &&
          item["Action"] === pair[[2]]]]]];
    ranked = If[Length[unqueried] === 0, {}, SortBy[
      Table[{DisagreementScoreB6[panel, pair[[1]], pair[[2]]],
        pair[[1]], pair[[2]]}, {pair, unqueried}],
      Function[row, {-row[[1]], row[[2]], row[[3]]}]]];
    maxScore = If[Length[ranked] === 0, 0., ranked[[1, 1]]];
    If[Length[unqueried] > 0 && (mode === "PASSIVE_INCREMENTAL" || maxScore > 0),
      query = If[mode === "PASSIVE_INCREMENTAL", First[unqueried],
        ranked[[1, {2, 3}]]];
      record = <|"State" -> query[[1]], "Action" -> query[[2]],
        "TargetCoordinate" -> OracleTargetB6[world, table, query[[1]], query[[2]]],
        "Source" -> If[mode === "PASSIVE_INCREMENTAL", "PASSIVE_QUERY",
          "MAX_DISAGREEMENT_QUERY"]|>;
      observations = Append[observations, record];
      update = UpdatePoolsB8[pools, basis["Ints"], selectedPredicates,
        record]; pools = update["Pools"];
      filterChecks += update["FilterChecks"];
      AppendTo[trace, <|"Round" -> Length[trace] + 1,
        "Event" -> record["Source"], "State" -> query[[1]],
        "Action" -> query[[2]], "DisagreementBits" -> N[maxScore],
        "CandidateCounts" -> panelCounts|>];
      Continue[]];
    programs = WinnerProgramsB6[panel];
    programBits = WinnerProgramBitsB6[panel];
    equivalenceCalls++; errors = ProgramErrorsB6[world, table, programs];
    If[Length[errors] === 0,
      exact = True; outcome = "EXACT_PROGRAM_FROZEN";
      AppendTo[trace, <|"Round" -> Length[trace] + 1,
        "Event" -> "EQUIVALENCE_CERTIFICATE", "MismatchCount" -> 0|>]; Break[]];
    counterexample = First[errors]; equivalenceCounterexamples++;
    If[AnyTrue[observations, #State === counterexample["State"] &&
        #Action === counterexample["Action"] &],
      outcome = "REPEATED_COUNTEREXAMPLE_FALLBACK"; Break[]];
    record = Join[counterexample, <|"Source" -> "EQUIVALENCE_COUNTEREXAMPLE"|>];
    observations = Append[observations, record];
    update = UpdatePoolsB8[pools, basis["Ints"], selectedPredicates,
      record]; pools = update["Pools"];
    filterChecks += update["FilterChecks"];
    AppendTo[trace, <|"Round" -> Length[trace] + 1,
      "Event" -> "EQUIVALENCE_COUNTEREXAMPLE",
      "State" -> record["State"], "Action" -> record["Action"],
      "CandidateCounts" -> panelCounts|>];
  ];
  tableBits = world["StateCount"] world["ActionCount"]
    Ceiling[Log[2, world["StateCount"]]];
  phiBits = Ceiling[Log[2, Factorial[world["StateCount"]]]];
  totalBits = If[exact, phiBits + programBits, Null];
  ratio = If[exact, N[totalBits/tableBits], Null];
  <|"Mode" -> mode, "Outcome" -> outcome, "ExactCertified" -> exact,
    "MembershipQueryCount" -> Length[observations],
    "EquivalenceOracleCalls" -> equivalenceCalls,
    "EquivalenceCounterexampleCount" -> equivalenceCounterexamples,
    "IncrementalFilterChecks" -> filterChecks,
    "FinalCandidateCounts" -> Map[Length, panel, {2}],
    "Programs" -> If[exact, programs, Null],
    "ProgramBits" -> If[exact, programBits, Null],
    "TransitionTableBits" -> tableBits, "PhiBits" -> phiBits,
    "PhiProgramBits" -> totalBits, "CompressionRatio" -> ratio,
    "CompressionReduction" -> If[exact, N[1 - ratio], Null],
    "Observations" -> observations, "Trace" -> trace,
    "RuntimeSeconds" -> N[AbsoluteTime[] - started],
    "AutomatonFallbackRetained" -> True|>
];

Print["S129-B8A incremental bounded-complete search R1"];
Print["Worlds/DSL/basis/controller changed=False; survivor maintenance=incremental"];

ObservationSignatureB8[run_Association] :=
  ({#["State"], #["Action"], #["Source"]} &) /@ run["Observations"];

formalResultsB8 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  built = GetBasisB7[world]; old = b7ByID[world["WorldID"]];
  Print["B8A WORLD START ", world["WorldID"]];
  active = RunIncrementalLearnerB8[world, table, built["Basis"], built["Predicates"],
    "ACTIVE_INCREMENTAL"];
  passive = RunIncrementalLearnerB8[world, table, built["Basis"], built["Predicates"],
    "PASSIVE_INCREMENTAL"];
  activeSequenceSame = ObservationSignatureB8[active] ===
    ObservationSignatureB8[old["Active"]];
  passiveSequenceSame = ObservationSignatureB8[passive] ===
    ObservationSignatureB8[old["Passive"]];
  activeProgramsSame = active["Programs"] === old["Active"]["Programs"];
  passiveProgramsSame = passive["Programs"] === old["Passive"]["Programs"];
  speedup = If[TrueQ[active["ExactCertified"]] &&
      TrueQ[old["Active"]["ExactCertified"]],
    N[old["Active"]["RuntimeSeconds"]/active["RuntimeSeconds"]], Null];
  Print["B8A WORLD END ", world["WorldID"], " active=", active["Outcome"],
    " q=", active["MembershipQueryCount"], " sec=", active["RuntimeSeconds"],
    " B7sec=", old["Active"]["RuntimeSeconds"], " speedup=", speedup];
  <|"WorldID" -> world["WorldID"], "StateCount" -> world["StateCount"],
    "CoordinateDimensions" -> world["CoordinateDimensions"],
    "BasisStatistics" -> built["Basis"]["Statistics"],
    "B7ActiveOutcome" -> old["Active"]["Outcome"],
    "B7ActiveQueries" -> old["Active"]["MembershipQueryCount"],
    "B7ActiveRuntimeSeconds" -> old["Active"]["RuntimeSeconds"],
    "ActiveObservationSequenceSameAsB7" -> activeSequenceSame,
    "PassiveObservationSequenceSameAsB7" -> passiveSequenceSame,
    "ActiveProgramsSameAsB7" -> activeProgramsSame,
    "PassiveProgramsSameAsB7" -> passiveProgramsSame,
    "Active" -> active, "Passive" -> passive,
    "ActiveRuntimeSpeedupVsB7" -> speedup|>,
  {index, Length[publicWorlds]}];

randomResultsB8 = Table[
  world = publicWorlds[[index]];
  table = RandomReachableTableB6[world["StateCount"], world["ActionCount"],
    world["StartState"], 1299100 + index]; built = GetBasisB7[world];
  If[table === $Failed,
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> True,
      "ExactCertified" -> False|>,
    randomRun = RunIncrementalLearnerB8[world, table, built["Basis"],
      built["Predicates"], "ACTIVE_INCREMENTAL"];
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> False,
      "Outcome" -> randomRun["Outcome"], "ExactCertified" -> randomRun["ExactCertified"],
      "MembershipQueryCount" -> randomRun["MembershipQueryCount"],
      "RuntimeSeconds" -> randomRun["RuntimeSeconds"],
      "Programs" -> randomRun["Programs"]|>],
  {index, Length[publicWorlds]}];

nearLawResultsB8 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  active = formalResultsB8[[index, "Active"]]; mutated = Map[Identity, table];
  oldTarget = mutated[[1, 1]]; mutated[[1, 1]] = Mod[oldTarget, world["StateCount"]] + 1;
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[world, mutated, active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"], "Applicable" -> TrueQ[active["ExactCertified"]],
    "BaseProgramMismatchCount" -> Length[errors],
    "MutationDetected" -> (!TrueQ[active["ExactCertified"]] || Length[errors] >= 1)|>,
  {index, Length[publicWorlds]}];

relabelResultsB8 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  relabeled = RelabelWorldB6[world, table, 1299200 + index];
  active = formalResultsB8[[index, "Active"]];
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[relabeled["World"], relabeled["Table"], active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"],
    "CoordinateDatasetHashInvariant" ->
      (CoordinateDatasetHashB6[world, table] ===
        CoordinateDatasetHashB6[relabeled["World"], relabeled["Table"]]),
    "FrozenProgramStillExact" -> (!TrueQ[active["ExactCertified"]] || Length[errors] === 0)|>,
  {index, Length[publicWorlds]}];

activeExactCountB8 = Count[Lookup[Lookup[formalResultsB8, "Active"],
  "ExactCertified"], True];
passiveExactCountB8 = Count[Lookup[Lookup[formalResultsB8, "Passive"],
  "ExactCertified"], True];
randomExactCountB8 = Count[Lookup[randomResultsB8, "ExactCertified"], True];
speedupsB8 = DeleteCases[Lookup[formalResultsB8, "ActiveRuntimeSpeedupVsB7"], Null];
totalB7ActiveSeconds = Total[Lookup[formalResultsB8, "B7ActiveRuntimeSeconds"]];
totalB8ActiveSeconds = Total[Lookup[Lookup[formalResultsB8, "Active"], "RuntimeSeconds"]];
nearPassB8 = And @@ Lookup[nearLawResultsB8, "MutationDetected"];
relabelPassB8 = And @@ Flatten[{Lookup[relabelResultsB8,
  "CoordinateDatasetHashInvariant"], Lookup[relabelResultsB8,
  "FrozenProgramStillExact"]}];

resultB8 = <|
  "Stage" -> b8Manifest["Stage"], "EvidenceStatus" -> b8Manifest["EvidenceStatus"],
  "WolframVersion" -> $Version, "NativeWolframExecution" -> True,
  "CanonicalTCCTModified" -> False, "S128BModified" -> False,
  "WorldsChangedFromB7" -> False, "DSLChangedFromB7" -> False,
  "BoundedCompleteBasisChangedFromB7" -> False,
  "TCCTPolicyChangedFromB7" -> False,
  "PriorBestProgramsLoaded" -> False, "GeneratorTruthRead" -> False,
  "PerWorldRulesAdded" -> False,
  "ActiveExactCount" -> activeExactCountB8,
  "PassiveExactCount" -> passiveExactCountB8,
  "RandomControlExactCount" -> randomExactCountB8,
  "AllB7ExactOutcomesPreserved" -> And @@ Table[
    formalResultsB8[[index, "Active", "ExactCertified"]] ===
      b7ByID[formalResultsB8[[index, "WorldID"]]]["Active"]["ExactCertified"],
    {index, Length[formalResultsB8]}],
  "AllActiveObservationSequencesSameAsB7" ->
    And @@ Lookup[formalResultsB8, "ActiveObservationSequenceSameAsB7"],
  "AllPassiveObservationSequencesSameAsB7" ->
    And @@ Lookup[formalResultsB8, "PassiveObservationSequenceSameAsB7"],
  "AllActiveProgramsSameAsB7" ->
    And @@ Lookup[formalResultsB8, "ActiveProgramsSameAsB7"],
  "AllPassiveProgramsSameAsB7" ->
    And @@ Lookup[formalResultsB8, "PassiveProgramsSameAsB7"],
  "TotalB7ActiveRuntimeSeconds" -> totalB7ActiveSeconds,
  "TotalB8ActiveRuntimeSeconds" -> totalB8ActiveSeconds,
  "AggregateActiveRuntimeSpeedup" -> N[totalB7ActiveSeconds/totalB8ActiveSeconds],
  "MedianPerWorldActiveRuntimeSpeedup" -> Median[speedupsB8],
  "NearLawPass" -> nearPassB8, "StateRelabelingPass" -> relabelPassB8,
  "AutomatonFallbackRetained" -> True,
  "FormalResults" -> formalResultsB8, "RandomControls" -> randomResultsB8,
  "NearLawControls" -> nearLawResultsB8,
  "StateRelabelingControls" -> relabelResultsB8|>;

Export[FileNameJoin[{resultDirectory, "S129B8A_result.json"}], resultB8,
  "RawJSON", "Compact" -> False];
Export[FileNameJoin[{resultDirectory, "S129B8A_per_world.csv"}], Table[
  {row["WorldID"], row["Active"]["Outcome"], row["Active"]["MembershipQueryCount"],
    row["B7ActiveRuntimeSeconds"], row["Active"]["RuntimeSeconds"],
    row["ActiveRuntimeSpeedupVsB7"], row["Active"]["IncrementalFilterChecks"],
    row["ActiveObservationSequenceSameAsB7"], row["ActiveProgramsSameAsB7"]},
    {row, formalResultsB8}], "CSV",
  "TableHeadings" -> {{}, {"WorldID", "Outcome", "ActiveQueries", "B7Seconds",
    "B8Seconds", "Speedup", "FilterChecks", "SameQuerySequence", "SamePrograms"}}];
Export[FileNameJoin[{controlDirectory, "S129B8A_random_controls.json"}],
  randomResultsB8, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B8A_near_law_controls.json"}],
  nearLawResultsB8, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B8A_state_relabeling_controls.json"}],
  relabelResultsB8, "RawJSON", "Compact" -> False];
Print["S129-B8A COMPLETE exact=", activeExactCountB8, "/", Length[formalResultsB8],
  " aggregateSpeedup=", resultB8["AggregateActiveRuntimeSpeedup"],
  " randomExact=", randomExactCountB8];
