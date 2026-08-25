(* ::Package:: *)

(* S132-K6E development patch: exact per-direct-snapshot cache for repeated
   (start state, action word) traces.  It leaves the accepted K6B waiter
   scheduler, audit semantics, closure, and verification unchanged. *)

K6EUniqueWordsSlot = 35;
K6ELongWordIDsSlot = 36;
K6EShortWordIDsSlot = 37;
K6ECacheStampSlot = 38;
K6ECacheStatusSlot = 39;
K6ECacheValueSlot = 40;
K6ECacheLookupsSlot = 41;
K6ECacheGenerationSlot = 42;

SetAttributes[TraceDirectCachedK6E, HoldFirst];
TraceDirectCachedK6E[audit_, start_Integer, wordID_Integer] := Module[
  {stateCount = audit[[K6BStateCountSlot]], cacheIndex, generation,
   result},
  $K6ETraceRequestCount++;
  cacheIndex = (wordID - 1) stateCount + start;
  generation = audit[[K6ECacheGenerationSlot]];
  If[audit[[K6ECacheStampSlot, cacheIndex]] == generation,
    $K6ECacheHitCount++;
    Return[{audit[[K6ECacheStatusSlot, cacheIndex]],
      audit[[K6ECacheValueSlot, cacheIndex]],
      audit[[K6ECacheLookupsSlot, cacheIndex]]}]];
  result = TraceDirectPackedK6B[start,
    audit[[K6EUniqueWordsSlot, wordID]],
    audit[[K6BDirectTargetsSlot]], audit[[K6BActionCountSlot]]];
  audit[[K6ECacheStampSlot, cacheIndex]] = generation;
  audit[[K6ECacheStatusSlot, cacheIndex]] = result[[1]];
  audit[[K6ECacheValueSlot, cacheIndex]] = result[[2]];
  audit[[K6ECacheLookupsSlot, cacheIndex]] = result[[3]];
  $K6EPhysicalTraceEvaluationCount++;
  $K6EPhysicalTraceCellLookupCount += result[[3]];
  result
];

SetAttributes[EvaluateAuditItemK6B, HoldFirst];
EvaluateAuditItemK6B[audit_, itemID_Integer,
  rejectedMask_List] := Module[
  {stateCount = audit[[K6BStateCountSlot]], instanceID, state,
   version, left, right, missingLeft = 0, missingRight = 0},
  instanceID = Quotient[itemID - 1, stateCount] + 1;
  state = Mod[itemID - 1, stateCount] + 1;
  If[rejectedMask[[instanceID]] == 1 ||
      audit[[K6BContradictedSlot, instanceID]] == 1 ||
      audit[[K6BResolvedSlot, itemID]] == 1, Return[Null]];
  version = audit[[K6BVersionsSlot, itemID]] + 1;
  audit[[K6BVersionsSlot, itemID]] = version;
  left = TraceDirectCachedK6E[audit, state,
    audit[[K6ELongWordIDsSlot, instanceID]]];
  right = TraceDirectCachedK6E[audit, state,
    audit[[K6EShortWordIDsSlot, instanceID]]];
  audit[[K6BEvaluationsSlot]]++;
  (* Preserve the accepted logical-work counter even on a physical cache hit. *)
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
   instanceID, itemID, longWords, shortWords, uniqueWords, wordMap,
   longWordIDs, shortWordIDs, cacheSize},
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
  longWords = If[instanceCount > 0, Lookup[instances, "Long"], {}];
  shortWords = If[instanceCount > 0, Lookup[instances, "Short"], {}];
  uniqueWords = DeleteDuplicates@Join[longWords, shortWords];
  wordMap = AssociationThread[WordKeyK4 /@ uniqueWords ->
    Range[Length[uniqueWords]]];
  longWordIDs = Developer`ToPackedArray@If[instanceCount > 0,
    Lookup[wordMap, WordKeyK4 /@ longWords], {}];
  shortWordIDs = Developer`ToPackedArray@If[instanceCount > 0,
    Lookup[wordMap, WordKeyK4 /@ shortWords], {}];
  cacheSize = Length[uniqueWords] stateCount;
  $K6ETraceRequestCount = 0;
  $K6ECacheHitCount = 0;
  $K6EPhysicalTraceEvaluationCount = 0;
  $K6EPhysicalTraceCellLookupCount = 0;
  $K6EUniqueWordCount = Length[uniqueWords];
  audit = {
    longWords, shortWords,
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
    0, 0, 0, 0, capacity,
    uniqueWords, longWordIDs, shortWordIDs,
    Developer`ToPackedArray@ConstantArray[0, cacheSize],
    Developer`ToPackedArray@ConstantArray[0, cacheSize],
    Developer`ToPackedArray@ConstantArray[0, cacheSize],
    Developer`ToPackedArray@ConstantArray[0, cacheSize], 1};
  $K6ECacheArraysPacked = And @@ ((Length[#1] == 0 ||
        Developer`PackedArrayQ[#1]) & /@
    audit[[{K6ELongWordIDsSlot, K6EShortWordIDsSlot,
      K6ECacheStampSlot, K6ECacheStatusSlot, K6ECacheValueSlot,
      K6ECacheLookupsSlot}]]);
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
  audit[[K6ECacheGenerationSlot]]++;
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

PackedAuditStorageByteCountK6B[audit_List] := Total[
  ByteCount /@ audit[[{K6BWitnessesSlot, K6BContradictedSlot,
    K6BFirstContradictionSlot, K6BResolvedSlot, K6BVersionsSlot,
    K6BHeadsSlot, K6BRecordItemsSlot, K6BRecordVersionsSlot,
    K6BRecordNextSlot, K6BDirectTargetsSlot, K6BWakeStampSlot,
    K6ELongWordIDsSlot, K6EShortWordIDsSlot, K6ECacheStampSlot,
    K6ECacheStatusSlot, K6ECacheValueSlot, K6ECacheLookupsSlot}]]] +
  ByteCount[audit[[K6EUniqueWordsSlot]]];

RunLearnerWordCacheK6E[world_Association, seed_Integer,
  transferEnabled_] := Module[{row},
  row = RunLearnerPackedK6B[world, seed, transferEnabled];
  Join[row, <|
    "UniqueActionWordCount" -> $K6EUniqueWordCount,
    "LogicalTraceRequestCount" -> $K6ETraceRequestCount,
    "ExactWordCacheHitCount" -> $K6ECacheHitCount,
    "ExactWordCacheHitFraction" -> If[$K6ETraceRequestCount > 0,
      N[$K6ECacheHitCount/$K6ETraceRequestCount], 0.],
    "PhysicalTraceEvaluationCount" ->
      $K6EPhysicalTraceEvaluationCount,
    "PhysicalTraceCellLookupCount" ->
      $K6EPhysicalTraceCellLookupCount,
    "PhysicalTraceCellLookupReductionFraction" -> If[
      row["ActualPersistentDirectAuditTraceCellLookups"] > 0,
      N[1 - $K6EPhysicalTraceCellLookupCount/
        row["ActualPersistentDirectAuditTraceCellLookups"]], 0.],
    "AllExactWordCacheArraysPacked" -> $K6ECacheArraysPacked|>]
];

K6EExactWordCachePatchLoaded = True;
