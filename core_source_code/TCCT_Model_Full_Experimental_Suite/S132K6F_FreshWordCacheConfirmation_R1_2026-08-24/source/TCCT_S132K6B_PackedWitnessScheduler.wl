(* ::Package:: *)

(* S132-K6B: exact packed-integer persistent direct-witness scheduler. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K6B_frozen_manifest.json"}], "RawJSON"];
k5bManifest = Import[FileNameJoin[{rootDirectory, "input",
  "S132K5B_frozen_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "input",
  "S132K5B_oracle_sequences.json"}], "RawJSON"];
frozenK5BResult = Import[FileNameJoin[{rootDirectory, "input",
  "S132K5B_frozen_result.json"}], "RawJSON"];
frozenK6PResult = Import[FileNameJoin[{rootDirectory, "input",
  "S132K6P_frozen_result.json"}], "RawJSON"];

initialFraction = k5bManifest["InitialDirectObservationFraction"];
batchFraction = k5bManifest["DirectQueryBatchFraction"];
minimumWitnesses = k5bManifest[
  "MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = k5bManifest["MaximumConceptWordLength"];

(* Load frozen K3B, K4A, and K5A mechanisms without old experiments. *)
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

k5aPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K5A_ExactIndexedActivation.wl"}];
k5aText = Import[k5aPath, "Text"];
k5aStart = First@First@StringPosition[k5aText,
  "TraceWordIndexedK5A[start_Integer, word_List,"];
k5aEnd = First@First@StringPosition[k5aText,
  "Print[\"S132-K5A RETROSPECTIVE EXACT INDEXED ACTIVATION\"]"];
ToExpression[StringTake[k5aText, {k5aStart, k5aEnd - 1}], InputForm];

K6BLongWordsSlot = 1; K6BShortWordsSlot = 2;
K6BWitnessesSlot = 3; K6BContradictedSlot = 4;
K6BFirstContradictionSlot = 5; K6BResolvedSlot = 6;
K6BVersionsSlot = 7; K6BHeadsSlot = 8;
K6BRecordItemsSlot = 9; K6BRecordVersionsSlot = 10;
K6BRecordNextSlot = 11; K6BRecordCountSlot = 12;
K6BRecordCapacitySlot = 13; K6BDirectTargetsSlot = 14;
K6BActionCountSlot = 15; K6BStateCountSlot = 16;
K6BInstanceCountSlot = 17; K6BTotalItemsSlot = 18;
K6BEvaluationsSlot = 19; K6BInitialEvaluationsSlot = 20;
K6BTraceLookupsSlot = 21; K6BWakeupsSlot = 22;
K6BPeakWakeBatchSlot = 23; K6BRecordsCreatedSlot = 24;
K6BRecordsReadSlot = 25; K6BActiveRecordsReadSlot = 26;
K6BStaleRecordsReadSlot = 27; K6BAdvanceCallsSlot = 28;
K6BWakeStampSlot = 29; K6BGenerationSlot = 30;
K6BCurrentWaiterRecordsSlot = 31; K6BPeakWaiterRecordsSlot = 32;
K6BGrowCountSlot = 33; K6BPeakCapacitySlot = 34;

CellIDK6B[state_Integer, action_Integer, actionCount_Integer] :=
  (state - 1) actionCount + action;

TraceDirectPackedK6B[start_Integer, word_List, targets_List,
  actionCount_Integer] := Module[
  {state = start, cellID, target, lookups = 0, missing = 0},
  Do[
    lookups++;
    cellID = CellIDK6B[state, word[[index]], actionCount];
    target = targets[[cellID]];
    If[target == 0, missing = cellID; Break[]];
    state = target,
    {index, Length[word]}];
  If[missing > 0, {0, missing, lookups}, {1, state, lookups}]
];

SetAttributes[EnsureRecordCapacityK6B, HoldFirst];
EnsureRecordCapacityK6B[audit_, needed_Integer] := Module[
  {oldCapacity, newCapacity, growth, slot},
  oldCapacity = audit[[K6BRecordCapacitySlot]];
  If[needed <= oldCapacity, Return[Null]];
  newCapacity = Max[needed, 2 oldCapacity, 16];
  growth = newCapacity - oldCapacity;
  Do[
    audit[[slot]] = Developer`ToPackedArray@Join[
      audit[[slot]], ConstantArray[0, growth]],
    {slot, {K6BRecordItemsSlot, K6BRecordVersionsSlot,
      K6BRecordNextSlot}}];
  audit[[K6BRecordCapacitySlot]] = newCapacity;
  audit[[K6BPeakCapacitySlot]] = Max[
    audit[[K6BPeakCapacitySlot]], newCapacity];
  audit[[K6BGrowCountSlot]]++;
  Null
];

SetAttributes[RegisterWaiterK6B, HoldFirst];
RegisterWaiterK6B[audit_, cellID_Integer, itemID_Integer,
  version_Integer] := Module[{recordID},
  recordID = audit[[K6BRecordCountSlot]] + 1;
  EnsureRecordCapacityK6B[audit, recordID];
  audit[[K6BRecordCountSlot]] = recordID;
  audit[[K6BRecordItemsSlot, recordID]] = itemID;
  audit[[K6BRecordVersionsSlot, recordID]] = version;
  audit[[K6BRecordNextSlot, recordID]] =
    audit[[K6BHeadsSlot, cellID]];
  audit[[K6BHeadsSlot, cellID]] = recordID;
  audit[[K6BRecordsCreatedSlot]]++;
  audit[[K6BCurrentWaiterRecordsSlot]]++;
  audit[[K6BPeakWaiterRecordsSlot]] = Max[
    audit[[K6BPeakWaiterRecordsSlot]],
    audit[[K6BCurrentWaiterRecordsSlot]]];
  Null
];

SetAttributes[EvaluateAuditItemK6B, HoldFirst];
EvaluateAuditItemK6B[audit_, itemID_Integer,
  rejectedMask_List] := Module[
  {stateCount = audit[[K6BStateCountSlot]],
   actionCount = audit[[K6BActionCountSlot]], instanceID, state,
   version, left, right, missingLeft = 0, missingRight = 0},
  instanceID = Quotient[itemID - 1, stateCount] + 1;
  state = Mod[itemID - 1, stateCount] + 1;
  If[rejectedMask[[instanceID]] == 1 ||
      audit[[K6BContradictedSlot, instanceID]] == 1 ||
      audit[[K6BResolvedSlot, itemID]] == 1, Return[Null]];
  version = audit[[K6BVersionsSlot, itemID]] + 1;
  audit[[K6BVersionsSlot, itemID]] = version;
  left = TraceDirectPackedK6B[state,
    audit[[K6BLongWordsSlot, instanceID]],
    audit[[K6BDirectTargetsSlot]], actionCount];
  right = TraceDirectPackedK6B[state,
    audit[[K6BShortWordsSlot, instanceID]],
    audit[[K6BDirectTargetsSlot]], actionCount];
  audit[[K6BEvaluationsSlot]]++;
  audit[[K6BTraceLookupsSlot]] += left[[3]] + right[[3]];
  If[left[[1]] == 1 && right[[1]] == 1,
    audit[[K6BResolvedSlot, itemID]] = 1;
    If[left[[2]] == right[[2]],
      audit[[K6BWitnessesSlot, instanceID]]++,
      audit[[K6BContradictedSlot, instanceID]] = 1;
      audit[[K6BFirstContradictionSlot, instanceID]] = state];
    Return[Null]];
  If[left[[1]] == 0, missingLeft = left[[2]]];
  If[right[[1]] == 0, missingRight = right[[2]]];
  If[missingLeft > 0,
    RegisterWaiterK6B[audit, missingLeft, itemID, version]];
  If[missingRight > 0 && missingRight != missingLeft,
    RegisterWaiterK6B[audit, missingRight, itemID, version]];
  Null
];

InitializeAuditK6B[instances_List, direct_Association,
  stateCount_Integer, actionCount_Integer,
  rejectedInput_List] := Module[
  {instanceCount = Length[instances], totalItems, totalCells,
   capacity, directTargets, rejectedMask, audit, cell, cellID,
   instanceID, itemID},
  totalItems = instanceCount stateCount;
  totalCells = stateCount actionCount;
  capacity = Max[16, 2 totalItems];
  directTargets = Developer`ToPackedArray@ConstantArray[0, totalCells];
  KeyValueMap[
    (cell = CellFromKeyK3B[#1];
      cellID = CellIDK6B[cell[[1]], cell[[2]], actionCount];
      directTargets[[cellID]] = #2["Target"]) &, direct];
  rejectedMask = Developer`ToPackedArray@ConstantArray[0,
    instanceCount];
  If[Length[rejectedInput] > 0,
    rejectedMask[[rejectedInput]] = 1];
  audit = {
    Lookup[instances, "Long"], Lookup[instances, "Short"],
    Developer`ToPackedArray@ConstantArray[0, instanceCount],
    Developer`ToPackedArray@ConstantArray[0, instanceCount],
    Developer`ToPackedArray@ConstantArray[0, instanceCount],
    Developer`ToPackedArray@ConstantArray[0, totalItems],
    Developer`ToPackedArray@ConstantArray[0, totalItems],
    Developer`ToPackedArray@ConstantArray[0, totalCells],
    Developer`ToPackedArray@ConstantArray[0, capacity],
    Developer`ToPackedArray@ConstantArray[0, capacity],
    Developer`ToPackedArray@ConstantArray[0, capacity],
    0, capacity, directTargets, actionCount, stateCount,
    instanceCount, totalItems, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    Developer`ToPackedArray@ConstantArray[0, totalItems],
    0, 0, 0, 0, capacity};
  Do[
    instanceID = instance["InstanceID"];
    If[rejectedMask[[instanceID]] == 0,
      Do[
        itemID = (instanceID - 1) stateCount + state;
        EvaluateAuditItemK6B[audit, itemID, rejectedMask];
        If[audit[[K6BContradictedSlot, instanceID]] == 1,
          Break[]],
        {state, stateCount}]],
    {instance, instances}];
  audit[[K6BInitialEvaluationsSlot]] = audit[[K6BEvaluationsSlot]];
  audit
];

SetAttributes[AdvanceAuditK6B, HoldFirst];
AdvanceAuditK6B[audit_, newKeys_List, direct_Association,
  rejectedInput_List] := Module[
  {stateCount = audit[[K6BStateCountSlot]],
   actionCount = audit[[K6BActionCountSlot]],
   instanceCount = audit[[K6BInstanceCountSlot]],
   totalItems = audit[[K6BTotalItemsSlot]], rejectedMask,
   newCellIDs, cell, cellID, node, next, itemID, instanceID,
   active, queue, queueCount = 0, generation, consumed = 0,
   items},
  rejectedMask = Developer`ToPackedArray@ConstantArray[0,
    instanceCount];
  If[Length[rejectedInput] > 0,
    rejectedMask[[rejectedInput]] = 1];
  newCellIDs = DeleteDuplicates@Table[
    cell = CellFromKeyK3B[key];
    cellID = CellIDK6B[cell[[1]], cell[[2]], actionCount];
    audit[[K6BDirectTargetsSlot, cellID]] = direct[key]["Target"];
    cellID,
    {key, newKeys}];
  audit[[K6BAdvanceCallsSlot]]++;
  generation = audit[[K6BGenerationSlot]] + 1;
  audit[[K6BGenerationSlot]] = generation;
  queue = Developer`ToPackedArray@ConstantArray[0, totalItems];
  Do[
    node = audit[[K6BHeadsSlot, cellID]];
    audit[[K6BHeadsSlot, cellID]] = 0;
    While[node > 0,
      consumed++;
      next = audit[[K6BRecordNextSlot, node]];
      itemID = audit[[K6BRecordItemsSlot, node]];
      instanceID = Quotient[itemID - 1, stateCount] + 1;
      active = audit[[K6BRecordVersionsSlot, node]] ==
          audit[[K6BVersionsSlot, itemID]] &&
        rejectedMask[[instanceID]] == 0 &&
        audit[[K6BContradictedSlot, instanceID]] == 0 &&
        audit[[K6BResolvedSlot, itemID]] == 0;
      If[TrueQ[active],
        audit[[K6BActiveRecordsReadSlot]]++;
        If[audit[[K6BWakeStampSlot, itemID]] != generation,
          audit[[K6BWakeStampSlot, itemID]] = generation;
          queueCount++;
          queue[[queueCount]] = itemID],
        audit[[K6BStaleRecordsReadSlot]]++];
      node = next],
    {cellID, newCellIDs}];
  audit[[K6BRecordsReadSlot]] += consumed;
  audit[[K6BCurrentWaiterRecordsSlot]] -= consumed;
  items = If[queueCount > 0, Sort[Take[queue, queueCount]], {}];
  audit[[K6BWakeupsSlot]] += Length[items];
  audit[[K6BPeakWakeBatchSlot]] = Max[
    audit[[K6BPeakWakeBatchSlot]], Length[items]];
  Do[EvaluateAuditItemK6B[audit, itemID, rejectedMask],
    {itemID, items}];
  Null
];

AuditStateCheckCostK6B[audit_List, instanceID_Integer,
  stateCount_Integer] := If[
  audit[[K6BContradictedSlot, instanceID]] == 1,
  audit[[K6BFirstContradictionSlot, instanceID]], stateCount];

PackedAuditStorageByteCountK6B[audit_List] := Total[
  ByteCount /@ audit[[{K6BWitnessesSlot, K6BContradictedSlot,
    K6BFirstContradictionSlot, K6BResolvedSlot, K6BVersionsSlot,
    K6BHeadsSlot, K6BRecordItemsSlot, K6BRecordVersionsSlot,
    K6BRecordNextSlot, K6BDirectTargetsSlot, K6BWakeStampSlot}]]];

BuildClosurePersistentK6B[direct_Association, instances_List,
  rejectedInput_List, stateCount_Integer, audit_List] := Module[
  {rejected = AssociationThread[rejectedInput -> ConstantArray[True,
      Length[rejectedInput]]], values, initialActive, active,
   admissible, instanceByID, queue, waiters, left, right, proposals,
   grouped, key, candidates, targets, implicated, record,
   conflictGroups, inferenceCreated = 0, internalRollbackCount = 0,
   directRejected = 0, conflictRejected = 0, restart, item,
   instance, state, newKeys, actualItemEvaluations = 0,
   fullScanEquivalentItemEvaluations = 0,
   k5AEquivalentDirectAuditChecks = 0,
   fullRescanEquivalentDirectAuditChecks = 0,
   indexedWakeups = 0, peakQueueSize = 0, fullScanWaveCount = 0,
   makeProposal},

  makeProposal[cellKey_String, target_Integer, provenance_List] :=
    <|"CellKey" -> cellKey, "Target" -> target,
      "Provenance" -> Sort@DeleteDuplicates[provenance]|>;

  initialActive = Select[instances, !KeyExistsQ[rejected,
      #["InstanceID"]] &];
  k5AEquivalentDirectAuditChecks = If[Length[initialActive] > 0,
    Total[AuditStateCheckCostK6B[audit, #["InstanceID"],
      stateCount] & /@ initialActive], 0];

  While[True,
    values = Association[direct];
    active = Select[initialActive, !KeyExistsQ[rejected,
        #["InstanceID"]] &];
    fullRescanEquivalentDirectAuditChecks += If[Length[active] > 0,
      Total[AuditStateCheckCostK6B[audit, #["InstanceID"],
        stateCount] & /@ active], 0];
    implicated = Select[active,
      audit[[K6BContradictedSlot, #["InstanceID"]]] == 1 &];
    If[Length[implicated] > 0,
      Do[AssociateTo[rejected, row["InstanceID"] -> True],
        {row, implicated}];
      directRejected += Length[implicated];
      internalRollbackCount++;
      Continue[]];

    admissible = Select[active,
      audit[[K6BWitnessesSlot, #["InstanceID"]]] >=
        minimumWitnesses &];
    instanceByID = Association@Map[#["InstanceID"] -> # &,
      admissible];
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
    "K5AEquivalentDirectAuditStateChecks" ->
      k5AEquivalentDirectAuditChecks,
    "FullRescanEquivalentDirectAuditStateChecks" ->
      fullRescanEquivalentDirectAuditChecks,
    "IndexedWakeupItemCount" -> indexedWakeups,
    "PeakIndexedQueueSize" -> peakQueueSize,
    "FullScanWaveCount" -> fullScanWaveCount|>
];

RunLearnerPackedK6B[world_Association, seed_Integer,
  transferEnabled_] := Module[
  {table = world["TransitionTable"], stateCount = world["StateCount"],
   actionCount = world["ActionCount"], totalCells, allKeys, order,
   initialCount, batchSize, direct = <||>, values = <||>, instances,
   rejected = {}, membershipQueries = 0, equivalenceCalls = 0,
   equivalenceCells = 0, counterexamples = 0, rollbacks = 0,
   inferenceCreated = 0, internalRollbacks = 0,
   directContradictionRejected = 0, conflictRejected = 0,
   closure, missing, batch, eq, provenance, exact = False,
   finalInferred, uniqueDirect, logicalCost, concreteCost, audit,
   indexedEvaluations = 0, fullScanEquivalentEvaluations = 0,
   k5AEquivalentDirectChecks = 0, fullDirectAuditChecks = 0,
   wakeups = 0, peakQueue = 0, fullScanWaves = 0,
   instanceBuildSeconds = 0., auditInitializeSeconds = 0.,
   auditAdvanceSeconds = 0., closureSeconds = 0.,
   equivalenceSeconds = 0., elapsed = 0., packedStorageBytes,
   coreArraysPacked},
  totalCells = stateCount actionCount;
  allKeys = Flatten@Table[CellKeyK3B[state, action],
    {state, stateCount}, {action, actionCount}];
  SeedRandom[seed, Method -> "MersenneTwister"];
  order = RandomSample[allKeys];
  initialCount = If[TrueQ[transferEnabled],
    Ceiling[initialFraction totalCells], totalCells];
  batchSize = Max[1, Ceiling[batchFraction totalCells]];
  {instanceBuildSeconds, instances} = AbsoluteTiming[
    If[TrueQ[transferEnabled], InstantiateSchemasK3B[actionCount], {}]];
  Do[AddDirectK3B[direct, table, key]; membershipQueries++,
    {key, Take[order, initialCount]}];
  {auditInitializeSeconds, audit} = AbsoluteTiming[
    InitializeAuditK6B[instances, direct, stateCount, actionCount,
      rejected]];

  While[!exact,
    {elapsed, closure} = AbsoluteTiming[
      BuildClosurePersistentK6B[
        direct, instances, rejected, stateCount, audit]];
    closureSeconds += elapsed;
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
    k5AEquivalentDirectChecks +=
      closure["K5AEquivalentDirectAuditStateChecks"];
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
      elapsed = First@AbsoluteTiming[
        AdvanceAuditK6B[audit, batch, direct, rejected]];
      auditAdvanceSeconds += elapsed;
      Continue[]];
    equivalenceCalls++;
    {elapsed, eq} = AbsoluteTiming[
      EquivalenceOracleK3B[values, table]];
    equivalenceSeconds += elapsed;
    equivalenceCells += eq["InspectedCells"];
    If[TrueQ[eq["Exact"]], exact = True; Break[]];
    counterexamples++;
    provenance = Lookup[eq, "Provenance", {}];
    If[Length[provenance] > 0,
      rejected = DeleteDuplicates@Join[rejected, provenance]];
    AddDirectK3B[direct, table, eq["MismatchKey"]];
    elapsed = First@AbsoluteTiming[
      AdvanceAuditK6B[audit, {eq["MismatchKey"]}, direct, rejected]];
    auditAdvanceSeconds += elapsed;
    rollbacks++;
  ];
  finalInferred = Count[Values[values], row_ /; !TrueQ[row["Direct"]]];
  uniqueDirect = Length[direct];
  logicalCost = membershipQueries + equivalenceCalls;
  concreteCost = membershipQueries + equivalenceCells;
  packedStorageBytes = PackedAuditStorageByteCountK6B[audit];
  coreArraysPacked = And @@ ((Length[#] == 0 ||
        Developer`PackedArrayQ[#]) & /@
    audit[[{K6BWitnessesSlot, K6BContradictedSlot,
      K6BFirstContradictionSlot, K6BResolvedSlot, K6BVersionsSlot,
      K6BHeadsSlot, K6BRecordItemsSlot, K6BRecordVersionsSlot,
      K6BRecordNextSlot, K6BDirectTargetsSlot, K6BWakeStampSlot}]]);
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
    "K5AEquivalentDirectAuditStateChecks" ->
      k5AEquivalentDirectChecks,
    "FullRescanEquivalentDirectAuditStateChecks" ->
      fullDirectAuditChecks,
    "IndexedWakeupItemCount" -> wakeups,
    "PeakIndexedQueueSize" -> peakQueue,
    "FullScanWaveCount" -> fullScanWaves,
    "ActualPersistentDirectAuditItemEvaluations" ->
      audit[[K6BEvaluationsSlot]],
    "InitialPersistentDirectAuditItemEvaluations" ->
      audit[[K6BInitialEvaluationsSlot]],
    "IncrementalPersistentDirectAuditItemEvaluations" ->
      audit[[K6BEvaluationsSlot]] - audit[[K6BInitialEvaluationsSlot]],
    "ActualPersistentDirectAuditTraceCellLookups" ->
      audit[[K6BTraceLookupsSlot]],
    "PersistentDirectAuditWakeupItemCount" ->
      audit[[K6BWakeupsSlot]],
    "PeakPersistentDirectAuditWakeBatch" ->
      audit[[K6BPeakWakeBatchSlot]],
    "SchemaInstanceBuildSeconds" -> instanceBuildSeconds,
    "AuditInitializeSeconds" -> auditInitializeSeconds,
    "AuditAdvanceSeconds" -> auditAdvanceSeconds,
    "IndexedClosureSeconds" -> closureSeconds,
    "EquivalenceOracleSeconds" -> equivalenceSeconds,
    "ProfiledAlgorithmSeconds" -> instanceBuildSeconds +
      auditInitializeSeconds + auditAdvanceSeconds + closureSeconds +
      equivalenceSeconds,
    "AuditAdvanceCallCount" -> audit[[K6BAdvanceCallsSlot]],
    "WaiterRecordsCreated" -> audit[[K6BRecordsCreatedSlot]],
    "WaiterRecordsRead" -> audit[[K6BRecordsReadSlot]],
    "ActiveWaiterRecordsRead" -> audit[[K6BActiveRecordsReadSlot]],
    "StaleWaiterRecordsRead" -> audit[[K6BStaleRecordsReadSlot]],
    "PeakWaiterRecordCount" -> audit[[K6BPeakWaiterRecordsSlot]],
    "FinalWaiterRecordCount" ->
      audit[[K6BCurrentWaiterRecordsSlot]],
    "WaiterRecordPoolGrowCount" -> audit[[K6BGrowCountSlot]],
    "WaiterRecordPoolCapacity" -> audit[[K6BRecordCapacitySlot]],
    "PeakWaiterRecordPoolCapacity" -> audit[[K6BPeakCapacitySlot]],
    "PackedAuditStorageByteCount" -> packedStorageBytes,
    "AllNumericAuditArraysPacked" -> coreArraysPacked|>
];

MappedK5ValueK6B[k6_Association, key_String] := If[
  key === "ActualDirectAuditStateChecks",
  k6["K5AEquivalentDirectAuditStateChecks"], Lookup[k6, key,
    Missing["Absent", key]]];

K6BK5AFieldMatch[k6_Association, k5_Association] :=
  And @@ KeyValueMap[MappedK5ValueK6B[k6, #1] === #2 &, k5];

RunPairedLearnersK6B[world_Association, seed_Integer,
  available_List, sequenceIndex_Integer] := Module[
  {k6, k5, k6Seconds, k5Seconds},
  If[OddQ[sequenceIndex],
    {k6Seconds, k6} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerPackedK6B[world, seed, True]]];
    {k5Seconds, k5} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerIndexedK5A[world, seed, True]]],
    {k5Seconds, k5} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerIndexedK5A[world, seed, True]]];
    {k6Seconds, k6} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerPackedK6B[world, seed, True]]]
  ];
  <|"K6B" -> k6, "K5A" -> k5,
    "K6BRuntimeSeconds" -> k6Seconds,
    "K5ARuntimeSeconds" -> k5Seconds,
    "K6BK5AFieldMatch" -> K6BK5AFieldMatch[k6, k5]|>
];

RunPairedStreamK6B[worlds_List, seeds_List, oldRows_List,
  streamName_String] := Module[
  {library = <||>, nextID = 0, rows = {}, world, available,
   paired, discovered, update, newCount, frozenMatch, row},
  Do[
    world = worlds[[index]];
    available = SortBy[Values[library], #["SchemaID"] &];
    paired = RunPairedLearnersK6B[
      world, seeds[[index]], available, index];
    discovered = DiscoverSchemasK4[world["TransitionTable"]];
    update = UpdateLibraryK4[library, nextID, discovered,
      world["WorldID"]];
    nextID = update["NextID"];
    newCount = update["NewCount"];
    frozenMatch = K6BK5AFieldMatch[
      paired["K6B"], oldRows[[index]]["IndexedTransfer"]];
    row = Join[<|"Stream" -> streamName,
       "SequenceIndex" -> index, "WorldID" -> world["WorldID"],
       "LibraryBeforeCount" -> Length[available],
       "SchemasDiscoveredThisWorld" -> Length[discovered],
       "NewSchemaCount" -> newCount,
       "LibraryAfterCount" -> Length[library],
       "FrozenK5BTransferRowReproduced" -> frozenMatch|>, paired];
    AppendTo[rows, row];
    Print[streamName, " ", world["WorldID"], " fields=",
      row["K6BK5AFieldMatch"], " frozen=", frozenMatch,
      " exact=", row["K6B"]["FinalExact"], " K6BSec=",
      row["K6BRuntimeSeconds"], " K5Sec=", row["K5ARuntimeSeconds"],
      " audit=", row["K6B"]["ActualPersistentDirectAuditItemEvaluations"],
      "/", row["K5A"]["ActualDirectAuditStateChecks"]],
    {index, Length[worlds]}];
  <|"Rows" -> rows,
    "FinalLibrary" -> SortBy[Values[library], #["SchemaID"] &]|>
];

RunPairedChallengesK6B[worlds_List, seeds_List, oldRows_List,
  library_List] := Module[{rows = {}, world, paired, frozenMatch, row},
  Do[
    world = worlds[[index]];
    paired = RunPairedLearnersK6B[
      world, seeds[[index]], library, index];
    frozenMatch = K6BK5AFieldMatch[
      paired["K6B"], oldRows[[index]]["IndexedTransfer"]];
    row = Join[<|"WorldID" -> world["WorldID"],
       "AvailableStructuredConceptCount" -> Length[library],
       "FrozenK5BTransferRowReproduced" -> frozenMatch|>, paired];
    AppendTo[rows, row];
    Print["NEAR_LAW ", world["WorldID"], " fields=",
      row["K6BK5AFieldMatch"], " frozen=", frozenMatch,
      " exact=", row["K6B"]["FinalExact"], " K6BSec=",
      row["K6BRuntimeSeconds"], " K5Sec=", row["K5ARuntimeSeconds"],
      " audit=", row["K6B"]["ActualPersistentDirectAuditItemEvaluations"],
      "/", row["K5A"]["ActualDirectAuditStateChecks"]],
    {index, Length[worlds]}];
  rows
];

Print["S132-K6B PACKED-INTEGER PERSISTENT WITNESS SCHEDULER"];
Print["Core modified=False; audit semantics modified=False; fresh claim=False"];

{totalRuntimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunPairedStreamK6B[
    oracleInput["StructuredWorlds"], k5bManifest["QueryOrderSeeds"],
    frozenK5BResult["StructuredResults"], "STRUCTURED"];
  controlStream = RunPairedStreamK6B[
    oracleInput["RankMatchedControls"],
    k5bManifest["ControlQueryOrderSeeds"],
    frozenK5BResult["ControlResults"], "RANK_MATCHED_CONTROL"];
  challengeRows = RunPairedChallengesK6B[
    oracleInput["NearLawChallenges"],
    k5bManifest["ChallengeQueryOrderSeeds"],
    frozenK5BResult["NearLawChallengeResults"],
    structuredStream["FinalLibrary"]];
  {structuredStream, controlStream, challengeRows}
];

structuredRows = structuredStream["Rows"];
controlRows = controlStream["Rows"];
allRows = Join[structuredRows, controlRows, challengeRows];
allFieldMatch = And @@ Lookup[allRows, "K6BK5AFieldMatch"];
frozenReproduced = And @@ Lookup[allRows,
  "FrozenK5BTransferRowReproduced"];
libraryMatch = structuredStream["FinalLibrary"] ===
    frozenK5BResult["FinalStructuredLibrary"] &&
  controlStream["FinalLibrary"] ===
    frozenK5BResult["FinalControlLibrary"];
allExact = And @@ Join[
  Lookup[Lookup[allRows, "K6B"], "FinalExact"],
  Lookup[Lookup[allRows, "K5A"], "FinalExact"]];
unsafeCount = Total@Join[
  Lookup[Lookup[allRows, "K6B"], "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[allRows, "K5A"], "UnsafeCommittedInferenceCount"]];
actualPersistentEvaluations = Total@Lookup[
  Lookup[allRows, "K6B"],
  "ActualPersistentDirectAuditItemEvaluations"];
k5AActualDirectChecks = Total@Lookup[
  Lookup[allRows, "K5A"], "ActualDirectAuditStateChecks"];
actualPersistentLookups = Total@Lookup[
  Lookup[allRows, "K6B"],
  "ActualPersistentDirectAuditTraceCellLookups"];
workReduced = actualPersistentEvaluations < k5AActualDirectChecks;
k6RuntimeSeconds = Total@Lookup[allRows, "K6BRuntimeSeconds"];
k5RuntimeSeconds = Total@Lookup[allRows, "K5ARuntimeSeconds"];
runtimeImproved = k6RuntimeSeconds < k5RuntimeSeconds;
retrospectivePass = allFieldMatch && frozenReproduced && libraryMatch &&
  allExact && unsafeCount === 0 && workReduced && runtimeImproved;
packedIntegrityPass = allFieldMatch && frozenReproduced && libraryMatch &&
  allExact && unsafeCount === 0;
k6Rows = Lookup[allRows, "K6B"];
schemaBuildSeconds = Total@Lookup[k6Rows, "SchemaInstanceBuildSeconds"];
auditInitializeSeconds = Total@Lookup[k6Rows, "AuditInitializeSeconds"];
auditAdvanceSeconds = Total@Lookup[k6Rows, "AuditAdvanceSeconds"];
closureSeconds = Total@Lookup[k6Rows, "IndexedClosureSeconds"];
equivalenceSeconds = Total@Lookup[k6Rows, "EquivalenceOracleSeconds"];
profiledAlgorithmSeconds = Total@Lookup[k6Rows,
  "ProfiledAlgorithmSeconds"];
unattributedK6Seconds = k6RuntimeSeconds - profiledAlgorithmSeconds;
waiterRecordsCreated = Total@Lookup[k6Rows, "WaiterRecordsCreated"];
waiterRecordsRead = Total@Lookup[k6Rows, "WaiterRecordsRead"];
activeWaiterRecordsRead = Total@Lookup[
  k6Rows, "ActiveWaiterRecordsRead"];
staleWaiterRecordsRead = Total@Lookup[k6Rows, "StaleWaiterRecordsRead"];
advanceCallCount = Total@Lookup[k6Rows, "AuditAdvanceCallCount"];
peakWaiterRecordCount = Max@Lookup[k6Rows, "PeakWaiterRecordCount"];
peakPackedAuditStorageBytes = Max@Lookup[
  k6Rows, "PackedAuditStorageByteCount"];
allArraysPacked = And @@ Lookup[k6Rows, "AllNumericAuditArraysPacked"];
totalPoolGrowCount = Total@Lookup[k6Rows, "WaiterRecordPoolGrowCount"];
peakPoolCapacity = Max@Lookup[k6Rows,
  "PeakWaiterRecordPoolCapacity"];
optimizationPass = retrospectivePass && packedIntegrityPass &&
  allArraysPacked;
k6pRuntimeSeconds = frozenK6PResult["AggregateK6ARuntimeSeconds"];
k6pPeakWaiterBytes = frozenK6PResult[
  "PeakWaiterByteCountAcrossWorlds"];

result = <|
  "Stage" -> "S132-K6B exact packed-integer persistent witness scheduler",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "TotalRuntimeSeconds" -> totalRuntimeSeconds,
  "RetrospectiveOpenedWorldsOnly" -> True,
  "FreshGeneralizationClaimAllowed" -> False,
  "CanonicalTCCTModified" -> False,
  "K3BConceptSemanticsModified" -> False,
  "K4AConceptSetModified" -> False,
  "K5AClosureActivationModified" -> False,
  "OnlyDirectWitnessStorageRepresentationChanged" -> True,
  "DirectWitnessAuditSemanticsModified" -> False,
  "PackedIntegrityPass" -> packedIntegrityPass,
  "AllK6BK5AFieldsMatch" -> allFieldMatch,
  "FrozenK5BTransferRowsReproduced" -> frozenReproduced,
  "FinalLibrariesIdentical" -> libraryMatch,
  "AllFinalModelsExact" -> allExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
  "ActualPersistentDirectAuditItemEvaluations" ->
    actualPersistentEvaluations,
  "K5AActualDirectAuditStateChecks" -> k5AActualDirectChecks,
  "PersistentDirectAuditEvaluationReduction" ->
    k5AActualDirectChecks - actualPersistentEvaluations,
  "PersistentDirectAuditEvaluationReductionFraction" -> If[
    k5AActualDirectChecks > 0,
    N[1 - actualPersistentEvaluations/k5AActualDirectChecks], 0.],
  "ActualPersistentDirectAuditTraceCellLookups" ->
    actualPersistentLookups,
  "DeterministicWitnessWorkReduced" -> workReduced,
  "AggregateK6BRuntimeSeconds" -> k6RuntimeSeconds,
  "AggregateK5ARuntimeSeconds" -> k5RuntimeSeconds,
  "RuntimeImproved" -> runtimeImproved,
  "PairedRuntimeSpeedup" -> If[k6RuntimeSeconds > 0,
    N[k5RuntimeSeconds/k6RuntimeSeconds], 0.],
  "DiagnosticSpeedupVersusFrozenK6P" -> If[k6RuntimeSeconds > 0,
    N[k6pRuntimeSeconds/k6RuntimeSeconds], 0.],
  "FrozenK6PRuntimeSeconds" -> k6pRuntimeSeconds,
  "PackedOptimizationGatePass" -> optimizationPass,
  "AggregateSchemaInstanceBuildSeconds" -> schemaBuildSeconds,
  "AggregateAuditInitializeSeconds" -> auditInitializeSeconds,
  "AggregateAuditAdvanceSeconds" -> auditAdvanceSeconds,
  "AggregateIndexedClosureSeconds" -> closureSeconds,
  "AggregateEquivalenceOracleSeconds" -> equivalenceSeconds,
  "AggregateProfiledAlgorithmSeconds" -> profiledAlgorithmSeconds,
  "AggregateUnattributedK6BSeconds" -> unattributedK6Seconds,
  "WaiterRecordsCreated" -> waiterRecordsCreated,
  "WaiterRecordsRead" -> waiterRecordsRead,
  "ActiveWaiterRecordsRead" -> activeWaiterRecordsRead,
  "StaleWaiterRecordsRead" -> staleWaiterRecordsRead,
  "AuditAdvanceCallCount" -> advanceCallCount,
  "PeakWaiterRecordCountAcrossWorlds" -> peakWaiterRecordCount,
  "PeakPackedAuditStorageByteCountAcrossWorlds" ->
    peakPackedAuditStorageBytes,
  "FrozenK6PPeakWaiterByteCountAcrossWorlds" -> k6pPeakWaiterBytes,
  "DiagnosticStorageReductionVersusFrozenK6P" -> If[
    k6pPeakWaiterBytes > 0,
    N[1 - peakPackedAuditStorageBytes/k6pPeakWaiterBytes], 0.],
  "AllNumericAuditArraysPacked" -> allArraysPacked,
  "TotalWaiterRecordPoolGrowCount" -> totalPoolGrowCount,
  "PeakWaiterRecordPoolCapacityAcrossWorlds" -> peakPoolCapacity,
  "StructuredResults" -> structuredRows,
  "ControlResults" -> controlRows,
  "NearLawChallengeResults" -> challengeRows,
  "FinalStructuredLibrary" -> structuredStream["FinalLibrary"],
  "FinalControlLibrary" -> controlStream["FinalLibrary"],
  "OpenEndedPrimitiveOrLanguageInventionProven" -> False,
  "Conclusion" -> If[optimizationPass,
    "RETROSPECTIVE_EXACT_PACKED_WITNESS_OPTIMIZATION_GATE_PASS",
    "RETROSPECTIVE_PACKED_WITNESS_OPTIMIZATION_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K6B_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K6B COMPLETE pass=", optimizationPass,
  " fields=", allFieldMatch, " audit=", actualPersistentEvaluations,
  "/", k5AActualDirectChecks, " initSec=", auditInitializeSeconds,
  " advanceSec=", auditAdvanceSeconds, " closureSec=", closureSeconds];
Exit[If[optimizationPass, 0, 1]];
