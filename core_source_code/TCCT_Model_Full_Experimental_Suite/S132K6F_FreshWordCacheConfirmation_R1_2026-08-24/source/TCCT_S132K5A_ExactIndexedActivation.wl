(* ::Package:: *)

(* S132-K5A: retrospective exact event-indexed concept activation. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K5A_frozen_manifest.json"}], "RawJSON"];
k4bManifest = Import[FileNameJoin[{rootDirectory, "input",
  "S132K4B_frozen_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "input",
  "S132K4B_oracle_sequences.json"}], "RawJSON"];
frozenK4BResult = Import[FileNameJoin[{rootDirectory, "input",
  "S132K4B_frozen_result.json"}], "RawJSON"];

initialFraction = k4bManifest["InitialDirectObservationFraction"];
batchFraction = k4bManifest["DirectQueryBatchFraction"];
minimumWitnesses = k4bManifest[
  "MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = k4bManifest["MaximumConceptWordLength"];

(* Load the frozen K3B primitives and frozen K4A concept mechanism only. *)
k3bPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K3B_PartialObservationTransfer.wl"}];
k3bText = Import[k3bPath, "Text"];
k3bStart = First@First@StringPosition[k3bText,
  "CellKeyK3B[state_Integer, action_Integer]"];
k3bEnd = First@First@StringPosition[k3bText,
  "Print[\"S132-K3B PARTIAL-OBSERVATION CONCEPT TRANSFER\"]"];
ToExpression[StringTake[k3bText, {k3bStart, k3bEnd - 1}], InputForm];

k4aPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K4A_FreshOnlineConceptCreation.wl"}];
k4aText = Import[k4aPath, "Text"];
k4aStart = First@First@StringPosition[k4aText, "WordKeyK4[word_List]"];
k4aEnd = First@First@StringPosition[k4aText,
  "Print[\"S132-K4A FRESH ONLINE BOUNDED CONCEPT CREATION\"]"];
ToExpression[StringTake[k4aText, {k4aStart, k4aEnd - 1}], InputForm];

TraceWordIndexedK5A[start_Integer, word_List,
  values_Association] := Module[
  {state = start, key, record, provenance = {}, index,
   early = Missing["NoEarlyResult"]},
  If[Length[word] == 0,
    Return[<|"Status" -> "Complete", "Target" -> state,
      "Provenance" -> {}|>]];
  Do[
    key = CellKeyK3B[state, word[[index]]];
    If[!KeyExistsQ[values, key],
      early = <|"Status" -> If[index == Length[word],
          "MissingFinal", "Blocked"], "MissingKey" -> key,
        "Provenance" -> DeleteDuplicates[provenance]|>;
      Break[]];
    record = values[key];
    provenance = Join[provenance, Lookup[record, "Provenance", {}]];
    state = record["Target"],
    {index, Length[word]}];
  If[AssociationQ[early], early,
    <|"Status" -> "Complete", "Target" -> state,
      "Provenance" -> DeleteDuplicates[provenance]|>]
];

DirectWitnessAuditIndexedK5A[instance_Association,
  direct_Association, stateCount_Integer] := Module[
  {left, right, witnesses = 0, contradiction = False, checks = 0},
  Do[
    checks++;
    left = TraceWordK3B[state, instance["Long"], direct];
    right = TraceWordK3B[state, instance["Short"], direct];
    If[left["Status"] === "Complete" &&
        right["Status"] === "Complete",
      If[left["Target"] === right["Target"], witnesses++,
        contradiction = True; Break[]]],
    {state, stateCount}];
  <|"Witnesses" -> witnesses, "Contradiction" -> contradiction,
    "StateChecks" -> checks|>
];

SetAttributes[AddWaiterK5A, HoldFirst];
AddWaiterK5A[waiters_, key_String, item_List] :=
  AssociateTo[waiters, key -> Append[Lookup[waiters, key, {}], item]];

BuildClosureIndexedK5A[direct_Association, instances_List,
  rejectedInput_List, stateCount_Integer] := Module[
  {rejected = AssociationThread[rejectedInput -> ConstantArray[True,
      Length[rejectedInput]]], values, initialActive, active, audits,
   admissible, instanceByID, queue, waiters, changedKeys, left, right,
   proposals, grouped, key, candidates, targets, implicated, record,
   conflictGroups, inferenceCreated = 0, internalRollbackCount = 0,
   directRejected = 0, conflictRejected = 0, restart, item, instance,
   state, newKeys, actualItemEvaluations = 0,
   fullScanEquivalentItemEvaluations = 0, actualDirectAuditChecks = 0,
   fullRescanEquivalentDirectAuditChecks = 0, indexedWakeups = 0,
   peakQueueSize = 0, fullScanWaveCount = 0, makeProposal},

  makeProposal[cellKey_String, target_Integer, provenance_List] :=
    <|"CellKey" -> cellKey, "Target" -> target,
      "Provenance" -> Sort@DeleteDuplicates[provenance]|>;

  initialActive = Select[instances, !KeyExistsQ[rejected,
      #["InstanceID"]] &];
  audits = Association@Table[
    instance["InstanceID"] -> DirectWitnessAuditIndexedK5A[
      instance, direct, stateCount], {instance, initialActive}];
  actualDirectAuditChecks = If[Length[initialActive] > 0,
    Total[(audits[#["InstanceID"]]["StateChecks"] &) /@
      initialActive], 0];

  While[True,
    values = Association[direct];
    active = Select[initialActive, !KeyExistsQ[rejected,
        #["InstanceID"]] &];
    fullRescanEquivalentDirectAuditChecks += If[Length[active] > 0,
      Total[(audits[#["InstanceID"]]["StateChecks"] &) /@ active], 0];
    implicated = Select[active,
      audits[#["InstanceID"]]["Contradiction"] &];
    If[Length[implicated] > 0,
      Do[AssociateTo[rejected, row["InstanceID"] -> True],
        {row, implicated}];
      directRejected += Length[implicated];
      internalRollbackCount++;
      Continue[]];

    admissible = Select[active,
      audits[#["InstanceID"]]["Witnesses"] >= minimumWitnesses &];
    instanceByID = Association@Map[
      #["InstanceID"] -> # &, admissible];
    queue = Flatten[Table[
      {instance["InstanceID"], state}, {instance, admissible},
      {state, stateCount}], 1];
    waiters = <||>;
    restart = False;

    While[Length[queue] > 0 && !restart,
      peakQueueSize = Max[peakQueueSize, Length[queue]];
      fullScanWaveCount++;
      fullScanEquivalentItemEvaluations +=
        Length[admissible] stateCount;
      proposals = {};
      Do[
        actualItemEvaluations++;
        item = queueItem;
        instance = instanceByID[item[[1]]];
        state = item[[2]];
        left = TraceWordIndexedK5A[state, instance["Long"], values];
        right = TraceWordIndexedK5A[state, instance["Short"], values];
        If[left["Status"] === "Complete" &&
            right["Status"] === "MissingFinal",
          AppendTo[proposals, makeProposal[right["MissingKey"],
            left["Target"], Join[{instance["InstanceID"]},
              left["Provenance"], right["Provenance"]]]]];
        If[right["Status"] === "Complete" &&
            left["Status"] === "MissingFinal",
          AppendTo[proposals, makeProposal[left["MissingKey"],
            right["Target"], Join[{instance["InstanceID"]},
              left["Provenance"], right["Provenance"]]]]];
        If[MemberQ[{"Blocked", "MissingFinal"}, left["Status"]],
          AddWaiterK5A[waiters, left["MissingKey"], item]];
        If[MemberQ[{"Blocked", "MissingFinal"}, right["Status"]],
          AddWaiterK5A[waiters, right["MissingKey"], item]],
        {queueItem, queue}];

      grouped = GroupBy[proposals, #["CellKey"] &];
      conflictGroups = Select[Values[grouped],
        Length[DeleteDuplicates[Lookup[#, "Target"]]] > 1 &];
      If[Length[conflictGroups] > 0,
        implicated = Sort@DeleteDuplicates@Flatten[
          Lookup[Flatten[conflictGroups, 1], "Provenance"]];
        Do[AssociateTo[rejected, id -> True], {id, implicated}];
        conflictRejected += Length[implicated];
        internalRollbackCount++;
        restart = True;
        Break[]];

      newKeys = {};
      Do[
        candidates = grouped[key];
        targets = DeleteDuplicates[Lookup[candidates, "Target"]];
        record = <|"Target" -> First[targets],
          "Provenance" -> Sort@DeleteDuplicates@Flatten[
            Lookup[candidates, "Provenance"]]|>;
        If[KeyExistsQ[values, key],
          If[values[key]["Target"] =!= record["Target"],
            implicated = Sort@DeleteDuplicates@Join[
              record["Provenance"], values[key]["Provenance"]];
            Do[AssociateTo[rejected, id -> True], {id, implicated}];
            conflictRejected += Length[implicated];
            internalRollbackCount++;
            restart = True;
            Break[]],
          AssociateTo[values, key -> <|"Target" -> record["Target"],
            "Direct" -> False, "Provenance" -> record["Provenance"]|>];
          AppendTo[newKeys, key];
          inferenceCreated++],
        {key, Sort[Keys[grouped]]}];
      If[restart, Break[]];

      If[Length[newKeys] == 0,
        queue = {},
        queue = DeleteDuplicates@Flatten[
          Lookup[waiters, newKeys, {}], 1];
        KeyDropFrom[waiters, newKeys];
        indexedWakeups += Length[queue];
        If[Length[queue] == 0,
          fullScanWaveCount++;
          fullScanEquivalentItemEvaluations +=
            Length[admissible] stateCount]];
    ];
    If[!restart, Break[]]
  ];

  <|"Values" -> values, "RejectedInstanceIDs" -> Keys[rejected],
    "ActiveAdmissibleInstanceCount" -> Length[admissible],
    "InferenceCreatedCount" -> inferenceCreated,
    "InternalRollbackCount" -> internalRollbackCount,
    "DirectContradictionRejectedCount" -> directRejected,
    "InferenceConflictRejectedCount" -> conflictRejected,
    "ActualIndexedClosureItemEvaluations" -> actualItemEvaluations,
    "FullScanEquivalentClosureItemEvaluations" ->
      fullScanEquivalentItemEvaluations,
    "ActualDirectAuditStateChecks" -> actualDirectAuditChecks,
    "FullRescanEquivalentDirectAuditStateChecks" ->
      fullRescanEquivalentDirectAuditChecks,
    "IndexedWakeupItemCount" -> indexedWakeups,
    "PeakIndexedQueueSize" -> peakQueueSize,
    "FullScanWaveCount" -> fullScanWaveCount|>
];

RunLearnerIndexedK5A[world_Association, seed_Integer,
  transferEnabled_] := Module[
  {table = world["TransitionTable"], stateCount = world["StateCount"],
   actionCount = world["ActionCount"], totalCells, allKeys, order,
   initialCount, batchSize, direct = <||>, values = <||>, instances,
   rejected = {}, membershipQueries = 0, equivalenceCalls = 0,
   equivalenceCells = 0, counterexamples = 0, rollbacks = 0,
   inferenceCreated = 0, internalRollbacks = 0,
   directContradictionRejected = 0, conflictRejected = 0,
   closure, missing, batch, eq, provenance, exact = False,
   finalInferred, uniqueDirect, logicalCost, concreteCost,
   indexedEvaluations = 0, fullScanEquivalentEvaluations = 0,
   directAuditChecks = 0, fullDirectAuditChecks = 0,
   wakeups = 0, peakQueue = 0, fullScanWaves = 0},
  totalCells = stateCount actionCount;
  allKeys = Flatten@Table[CellKeyK3B[state, action],
    {state, stateCount}, {action, actionCount}];
  SeedRandom[seed, Method -> "MersenneTwister"];
  order = RandomSample[allKeys];
  initialCount = If[TrueQ[transferEnabled],
    Ceiling[initialFraction totalCells], totalCells];
  batchSize = Max[1, Ceiling[batchFraction totalCells]];
  instances = If[TrueQ[transferEnabled],
    InstantiateSchemasK3B[actionCount], {}];
  Do[AddDirectK3B[direct, table, key]; membershipQueries++,
    {key, Take[order, initialCount]}];

  While[!exact,
    closure = BuildClosureIndexedK5A[
      direct, instances, rejected, stateCount];
    values = closure["Values"];
    rejected = closure["RejectedInstanceIDs"];
    inferenceCreated += closure["InferenceCreatedCount"];
    internalRollbacks += closure["InternalRollbackCount"];
    directContradictionRejected +=
      closure["DirectContradictionRejectedCount"];
    conflictRejected += closure["InferenceConflictRejectedCount"];
    indexedEvaluations +=
      closure["ActualIndexedClosureItemEvaluations"];
    fullScanEquivalentEvaluations +=
      closure["FullScanEquivalentClosureItemEvaluations"];
    directAuditChecks += closure["ActualDirectAuditStateChecks"];
    fullDirectAuditChecks +=
      closure["FullRescanEquivalentDirectAuditStateChecks"];
    wakeups += closure["IndexedWakeupItemCount"];
    peakQueue = Max[peakQueue, closure["PeakIndexedQueueSize"]];
    fullScanWaves += closure["FullScanWaveCount"];
    missing = Select[order, !KeyExistsQ[values, #] &];
    If[Length[missing] > 0,
      batch = Take[missing, UpTo[batchSize]];
      Do[AddDirectK3B[direct, table, key]; membershipQueries++,
        {key, batch}];
      Continue[]];
    equivalenceCalls++;
    eq = EquivalenceOracleK3B[values, table];
    equivalenceCells += eq["InspectedCells"];
    If[TrueQ[eq["Exact"]], exact = True; Break[]];
    counterexamples++;
    provenance = Lookup[eq, "Provenance", {}];
    If[Length[provenance] > 0,
      rejected = DeleteDuplicates@Join[rejected, provenance]];
    AddDirectK3B[direct, table, eq["MismatchKey"]];
    rollbacks++;
  ];
  finalInferred = Count[Values[values], row_ /; !TrueQ[row["Direct"]]];
  uniqueDirect = Length[direct];
  logicalCost = membershipQueries + equivalenceCalls;
  concreteCost = membershipQueries + equivalenceCells;
  <|"Mode" -> If[TrueQ[transferEnabled], "TRANSFER_ENABLED",
      "SCHEMA_DISABLED_BASELINE"],
    "Seed" -> seed, "StateCount" -> stateCount,
    "ActionCount" -> actionCount, "TotalTransitionCells" -> totalCells,
    "InitialDirectObservationCount" -> initialCount,
    "ProposedSchemaInstanceCount" -> Length[instances],
    "QueryOrder" -> order,
    "MembershipQueries" -> membershipQueries,
    "EquivalenceOracleCalls" -> equivalenceCalls,
    "EquivalenceCounterexampleCount" -> counterexamples,
    "EquivalenceCellsInspected" -> equivalenceCells,
    "LogicalInteractionCost" -> logicalCost,
    "ConcreteOracleCellCost" -> concreteCost,
    "UniqueDirectObservationCount" -> uniqueDirect,
    "FinalInferredTransitionCount" -> finalInferred,
    "RejectedSchemaInstanceCount" -> Length[rejected],
    "CounterexampleRollbackCount" -> rollbacks,
    "InternalRollbackCount" -> internalRollbacks,
    "DirectContradictionRejectedCount" -> directContradictionRejected,
    "InferenceConflictRejectedCount" -> conflictRejected,
    "CumulativeInferenceCreatedCount" -> inferenceCreated,
    "FinalExact" -> exact,
    "UnsafeCommittedInferenceCount" -> If[exact, 0, finalInferred],
    "ActualIndexedClosureItemEvaluations" -> indexedEvaluations,
    "FullScanEquivalentClosureItemEvaluations" ->
      fullScanEquivalentEvaluations,
    "ActualDirectAuditStateChecks" -> directAuditChecks,
    "FullRescanEquivalentDirectAuditStateChecks" -> fullDirectAuditChecks,
    "IndexedWakeupItemCount" -> wakeups,
    "PeakIndexedQueueSize" -> peakQueue,
    "FullScanWaveCount" -> fullScanWaves|>
];

RunOnlineStreamIndexedK5A[worlds_List, seeds_List,
  streamName_String] := Module[
  {library = <||>, nextID = 0, rows = {}, available, transfer,
   baseline, discovered, update, newCount, world, seed, mqSavings,
   logicalSavings, concreteSavings},
  Do[
    world = worlds[[index]];
    seed = seeds[[index]];
    available = SortBy[Values[library], #["SchemaID"] &];
    transfer = Block[{schemas = available},
      RunLearnerIndexedK5A[world, seed, True]];
    baseline = Block[{schemas = {}},
      RunLearnerIndexedK5A[world, seed, False]];
    discovered = DiscoverSchemasK4[world["TransitionTable"]];
    update = UpdateLibraryK4[library, nextID, discovered,
      world["WorldID"]];
    nextID = update["NextID"];
    newCount = update["NewCount"];
    mqSavings = baseline["MembershipQueries"] -
      transfer["MembershipQueries"];
    logicalSavings = baseline["LogicalInteractionCost"] -
      transfer["LogicalInteractionCost"];
    concreteSavings = baseline["ConcreteOracleCellCost"] -
      transfer["ConcreteOracleCellCost"];
    AppendTo[rows, <|"Stream" -> streamName,
      "SequenceIndex" -> index, "WorldID" -> world["WorldID"],
      "LibraryBeforeCount" -> Length[available],
      "SchemasDiscoveredThisWorld" -> Length[discovered],
      "NewSchemaCount" -> newCount,
      "LibraryAfterCount" -> Length[library],
      "PriorCreatedConceptUsed" ->
        transfer["FinalInferredTransitionCount"] > 0,
      "Transfer" -> transfer, "Baseline" -> baseline,
      "MembershipQuerySavings" -> mqSavings,
      "LogicalInteractionCostSavings" -> logicalSavings,
      "ConcreteOracleCellCostSavings" -> concreteSavings|>],
    {index, Length[worlds]}];
  <|"Rows" -> rows,
    "FinalLibrary" -> SortBy[Values[library], #["SchemaID"] &]|>
];

RunChallengesIndexedK5A[worlds_List, seeds_List, library_List] := Module[
  {rows = {}, world, transfer, baseline},
  Do[
    world = worlds[[index]];
    transfer = Block[{schemas = library},
      RunLearnerIndexedK5A[world, seeds[[index]], True]];
    baseline = Block[{schemas = {}},
      RunLearnerIndexedK5A[world, seeds[[index]], False]];
    AppendTo[rows, <|"WorldID" -> world["WorldID"],
      "AvailableStructuredConceptCount" -> Length[library],
      "Transfer" -> transfer, "Baseline" -> baseline,
      "MembershipQuerySavings" ->
        baseline["MembershipQueries"] - transfer["MembershipQueries"],
      "LogicalInteractionCostSavings" ->
        baseline["LogicalInteractionCost"] -
          transfer["LogicalInteractionCost"],
      "ConcreteOracleCellCostSavings" ->
        baseline["ConcreteOracleCellCost"] -
          transfer["ConcreteOracleCellCost"]|>],
    {index, Length[worlds]}];
  rows
];

OriginalFieldMatchK5A[new_Association, old_Association] :=
  KeyTake[new, Keys[old]] === old;

StreamRowsMatchK5A[newRows_List, oldRows_List] :=
  Length[newRows] === Length[oldRows] && And @@ MapThread[
    Function[{new, old},
      new["WorldID"] === old["WorldID"] &&
      OriginalFieldMatchK5A[new["Transfer"], old["Transfer"]] &&
      OriginalFieldMatchK5A[new["Baseline"], old["Baseline"]] &&
      And @@ Table[new[key] === old[key], {key,
        Complement[Intersection[Keys[new], Keys[old]],
          {"Transfer", "Baseline", "Stream"}]}]],
    {newRows, oldRows}];

Print["S132-K5A RETROSPECTIVE EXACT INDEXED ACTIVATION"];
Print["Concept set unchanged=True; core modified=False; fresh claim=False"];

{runtimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunOnlineStreamIndexedK5A[
    oracleInput["StructuredWorlds"], k4bManifest["QueryOrderSeeds"],
    "INDEXED_STRUCTURED"];
  controlStream = RunOnlineStreamIndexedK5A[
    oracleInput["RankMatchedControls"],
    k4bManifest["ControlQueryOrderSeeds"], "INDEXED_CONTROL"];
  challengeRows = RunChallengesIndexedK5A[
    oracleInput["NearLawChallenges"],
    k4bManifest["ChallengeQueryOrderSeeds"],
    structuredStream["FinalLibrary"]];
  {structuredStream, controlStream, challengeRows}
];

familyMap = Association@Map[
  #["WorldID"] -> #["Family"] &,
  k4bManifest["StructuredWorldSpecifications"]];
structuredRows = Map[
  Join[#, <|"Family" -> familyMap[#["WorldID"]]|>] &,
  structuredStream["Rows"]];
controlRows = controlStream["Rows"];

structuredMatch = StreamRowsMatchK5A[
  structuredRows, frozenK4BResult["StructuredResults"]];
controlMatch = StreamRowsMatchK5A[
  controlRows, frozenK4BResult["ControlResults"]];
challengeMatch = StreamRowsMatchK5A[
  challengeRows, frozenK4BResult["NearLawChallengeResults"]];
libraryMatch = structuredStream["FinalLibrary"] ===
    frozenK4BResult["FinalStructuredLibrary"] &&
  controlStream["FinalLibrary"] ===
    frozenK4BResult["FinalControlLibrary"];

allTransferRows = Join[structuredRows, controlRows, challengeRows];
actualIndexedEvaluations = Total[Lookup[
  Lookup[allTransferRows, "Transfer"],
  "ActualIndexedClosureItemEvaluations"]];
fullScanEquivalentEvaluations = Total[Lookup[
  Lookup[allTransferRows, "Transfer"],
  "FullScanEquivalentClosureItemEvaluations"]];
actualDirectAuditChecks = Total[Lookup[
  Lookup[allTransferRows, "Transfer"],
  "ActualDirectAuditStateChecks"]];
fullDirectAuditChecks = Total[Lookup[
  Lookup[allTransferRows, "Transfer"],
  "FullRescanEquivalentDirectAuditStateChecks"]];
allExact = And @@ Join[
  Lookup[Lookup[allTransferRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[allTransferRows, "Baseline"], "FinalExact"]];
unsafeCount = Total[Lookup[Lookup[allTransferRows, "Transfer"],
  "UnsafeCommittedInferenceCount"]];
runtimeImproved = runtimeSeconds < frozenK4BResult["RuntimeSeconds"];
deterministicWorkReduced = actualIndexedEvaluations <
    fullScanEquivalentEvaluations &&
  actualDirectAuditChecks <= fullDirectAuditChecks;
retrospectivePass = structuredMatch && controlMatch && challengeMatch &&
  libraryMatch && allExact && unsafeCount === 0 &&
  deterministicWorkReduced && runtimeImproved;

Do[Print[row["WorldID"], " indexed eval=",
    row["Transfer"]["ActualIndexedClosureItemEvaluations"],
    " full-equivalent=",
    row["Transfer"]["FullScanEquivalentClosureItemEvaluations"],
    " exact=", row["Transfer"]["FinalExact"]],
  {row, structuredRows}];

result = <|
  "Stage" -> "S132-K5A retrospective exact indexed activation",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "RuntimeSeconds" -> runtimeSeconds,
  "FrozenK4BRuntimeSeconds" -> frozenK4BResult["RuntimeSeconds"],
  "RuntimeImproved" -> runtimeImproved,
  "RetrospectiveOpenedWorldsOnly" -> True,
  "FreshGeneralizationClaimAllowed" -> False,
  "ConceptSetChanged" -> False,
  "ConceptActivationSemanticsIntendedEquivalent" -> True,
  "CanonicalTCCTModified" -> False,
  "FrozenK3BAndK4AConceptDiscoveryModified" -> False,
  "StructuredTraceAndCounterMatch" -> structuredMatch,
  "ControlTraceAndCounterMatch" -> controlMatch,
  "NearLawTraceAndCounterMatch" -> challengeMatch,
  "FinalLibraryMatch" -> libraryMatch,
  "AllFinalModelsExact" -> allExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
  "ActualIndexedClosureItemEvaluations" -> actualIndexedEvaluations,
  "FullScanEquivalentClosureItemEvaluations" ->
    fullScanEquivalentEvaluations,
  "IndexedClosureEvaluationReduction" ->
    fullScanEquivalentEvaluations - actualIndexedEvaluations,
  "IndexedClosureEvaluationReductionFraction" -> If[
    fullScanEquivalentEvaluations > 0,
    N[1 - actualIndexedEvaluations/fullScanEquivalentEvaluations], 0.],
  "ActualDirectAuditStateChecks" -> actualDirectAuditChecks,
  "FullRescanEquivalentDirectAuditStateChecks" ->
    fullDirectAuditChecks,
  "DirectAuditCheckReduction" ->
    fullDirectAuditChecks - actualDirectAuditChecks,
  "DeterministicWorkReduced" -> deterministicWorkReduced,
  "RetrospectiveExactIndexedActivationGatePass" -> retrospectivePass,
  "StructuredResults" -> structuredRows,
  "ControlResults" -> controlRows,
  "NearLawChallengeResults" -> challengeRows,
  "FinalStructuredLibrary" -> structuredStream["FinalLibrary"],
  "FinalControlLibrary" -> controlStream["FinalLibrary"],
  "Conclusion" -> If[retrospectivePass,
    "RETROSPECTIVE_EXACT_INDEXED_ACTIVATION_GATE_PASS",
    "RETROSPECTIVE_EXACT_INDEXED_ACTIVATION_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K5A_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K5A COMPLETE pass=", retrospectivePass,
  " runtime=", runtimeSeconds, " old=",
  frozenK4BResult["RuntimeSeconds"], " indexed eval=",
  actualIndexedEvaluations, " full-equivalent=",
  fullScanEquivalentEvaluations];
Exit[If[retrospectivePass, 0, 1]];
