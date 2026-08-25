(* ::Package:: *)

(* S132-K6F: frozen fresh confirmation of the exact K6E action-word cache. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K6F_pre_world_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "oracle",
  "S132K6F_oracle_sequences.json"}], "RawJSON"];

initialFraction = manifest["InitialDirectObservationFraction"];
batchFraction = manifest["DirectQueryBatchFraction"];
minimumWitnesses = manifest[
  "MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = manifest["MaximumConceptWordLength"];
worldLimitText = Environment["K6F_WORLD_LIMIT"];
worldLimit = If[StringQ[worldLimitText] &&
    StringMatchQ[worldLimitText, NumberString],
  Clip[ToExpression[worldLimitText], {1, 20}], 20];
selectedStructuredWorlds = Take[oracleInput["StructuredWorlds"],
  UpTo[worldLimit]];
selectedControlWorlds = Take[oracleInput["RankMatchedControls"],
  UpTo[worldLimit]];
fullFreshProfile = worldLimit === 20 &&
  Length[selectedStructuredWorlds] === 8 &&
  Length[selectedControlWorlds] === 8 &&
  Length[oracleInput["NearLawChallenges"]] === 4;
selectedChallengeWorlds = If[fullFreshProfile,
  oracleInput["NearLawChallenges"], {}];

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

(* Keep a simultaneous unmodified K6B baseline by renaming the complete frozen
   K6B mechanism segment before the K6E cache patch is loaded. *)
k6bPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K6B_PackedWitnessScheduler.wl"}];
k6bText = Import[k6bPath, "Text"];
k6bStart = First@First@StringPosition[k6bText, "K6BLongWordsSlot = 1;"];
k6bEnd = First@First@StringPosition[k6bText,
  "RunPairedLearnersK6B[world_Association"];
k6bSegment = StringTake[k6bText, {k6bStart, k6bEnd - 1}];
ToExpression[k6bSegment, InputForm];
ToExpression[StringReplace[k6bSegment, "K6B" -> "K6FBase"], InputForm];

k6ePath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K6E_ExactWordCachePatch.wl"}];
Get[k6ePath];
acceptedK6ESourceHash = IntegerString[
  FileHash[k6ePath, "SHA256"], 16, 64];
k6eSourceHashMatch = ToLowerCase[acceptedK6ESourceHash] ===
  ToLowerCase[manifest["AcceptedK6ESourceSHA256"]];

behaviorKeys = {
  "Mode", "Seed", "StateCount", "ActionCount",
  "TotalTransitionCells", "InitialDirectObservationCount",
  "ProposedSchemaInstanceCount", "QueryOrder", "MembershipQueries",
  "EquivalenceOracleCalls", "EquivalenceCounterexampleCount",
  "EquivalenceCellsInspected", "LogicalInteractionCost",
  "ConcreteOracleCellCost", "UniqueDirectObservationCount",
  "FinalInferredTransitionCount", "RejectedSchemaInstanceCount",
  "CounterexampleRollbackCount", "InternalRollbackCount",
  "DirectContradictionRejectedCount", "InferenceConflictRejectedCount",
  "CumulativeInferenceCreatedCount", "FinalExact",
  "UnsafeCommittedInferenceCount", "ActualIndexedClosureItemEvaluations",
  "FullScanEquivalentClosureItemEvaluations",
  "K5AEquivalentDirectAuditStateChecks",
  "FullRescanEquivalentDirectAuditStateChecks", "IndexedWakeupItemCount",
  "PeakIndexedQueueSize", "FullScanWaveCount",
  "ActualPersistentDirectAuditItemEvaluations",
  "InitialPersistentDirectAuditItemEvaluations",
  "IncrementalPersistentDirectAuditItemEvaluations",
  "ActualPersistentDirectAuditTraceCellLookups",
  "PersistentDirectAuditWakeupItemCount",
  "PeakPersistentDirectAuditWakeBatch", "AuditAdvanceCallCount"};

K6EK6BBehaviorMatchK6F[k6e_Association, k6b_Association] :=
  KeyTake[k6e, behaviorKeys] === KeyTake[k6b, behaviorKeys];

RunThreeLearnersK6F[world_Association, seed_Integer,
  available_List, sequenceIndex_Integer] := Module[
  {k6e, k6b, k5a, k6eSeconds = 0., k6bSeconds = 0.,
   k5aSeconds = 0., order, runE, runB, run5},
  runE[] := ({k6eSeconds, k6e} = AbsoluteTiming[
    Block[{schemas = available},
      RunLearnerWordCacheK6E[world, seed, True]]]);
  runB[] := ({k6bSeconds, k6b} = AbsoluteTiming[
    Block[{schemas = available},
      RunLearnerPackedK6FBase[world, seed, True]]]);
  run5[] := ({k5aSeconds, k5a} = AbsoluteTiming[
    Block[{schemas = available},
      RunLearnerIndexedK5A[world, seed, True]]]);
  order = Switch[Mod[sequenceIndex - 1, 3],
    0, {"K6E", "K6B", "K5A"},
    1, {"K6B", "K5A", "K6E"},
    _, {"K5A", "K6E", "K6B"}];
  Do[Switch[label, "K6E", runE[], "K6B", runB[], "K5A", run5[]],
    {label, order}];
  <|"ExecutionOrder" -> order, "K6E" -> k6e, "K6B" -> k6b,
    "K5A" -> k5a, "K6ERuntimeSeconds" -> k6eSeconds,
    "K6BRuntimeSeconds" -> k6bSeconds,
    "K5ARuntimeSeconds" -> k5aSeconds,
    "K6EK5AFieldMatch" -> K6BK5AFieldMatch[k6e, k5a],
    "K6BK5AFieldMatch" -> K6FBaseK5AFieldMatch[k6b, k5a],
    "K6EK6BBehaviorMatch" -> K6EK6BBehaviorMatchK6F[k6e, k6b]|>
];

RunOnlineStreamK6F[worlds_List, seeds_List, streamName_String] := Module[
  {library = <||>, nextID = 0, rows = {}, world, available,
   triple, discovered, update, row},
  Do[
    world = worlds[[index]];
    available = SortBy[Values[library], #1["SchemaID"] &];
    triple = RunThreeLearnersK6F[
      world, seeds[[index]], available, index];
    discovered = DiscoverSchemasK4[world["TransitionTable"]];
    update = UpdateLibraryK4[library, nextID, discovered,
      world["WorldID"]];
    nextID = update["NextID"];
    row = Join[<|"Stream" -> streamName,
       "SequenceIndex" -> index, "WorldID" -> world["WorldID"],
       "LibraryBeforeCount" -> Length[available],
       "SchemasDiscoveredThisWorld" -> Length[discovered],
       "NewSchemaCount" -> update["NewCount"],
       "LibraryAfterCount" -> Length[library],
       "PriorCreatedConceptUsed" -> Length[available] > 0 &&
         triple["K6E"]["FinalInferredTransitionCount"] > 0|>, triple];
    AppendTo[rows, row];
    Print[streamName, " ", world["WorldID"], " triple=",
      row["K6EK5AFieldMatch"] && row["K6BK5AFieldMatch"] &&
        row["K6EK6BBehaviorMatch"], " exact=",
      row["K6E"]["FinalExact"], " hit=",
      row["K6E"]["ExactWordCacheHitFraction"], " E/B/5=",
      row["K6ERuntimeSeconds"], "/", row["K6BRuntimeSeconds"], "/",
      row["K5ARuntimeSeconds"], " order=", row["ExecutionOrder"]],
    {index, Length[worlds]}];
  <|"Rows" -> rows,
    "FinalLibrary" -> SortBy[Values[library], #1["SchemaID"] &]|>
];

RunChallengesK6F[worlds_List, seeds_List, library_List] := Module[
  {rows = {}, world, triple, row},
  Do[
    world = worlds[[index]];
    triple = RunThreeLearnersK6F[
      world, seeds[[index]], library, index];
    row = Join[<|"WorldID" -> world["WorldID"],
       "AvailableStructuredConceptCount" -> Length[library]|>, triple];
    AppendTo[rows, row];
    Print["NEAR_LAW ", world["WorldID"], " triple=",
      row["K6EK5AFieldMatch"] && row["K6BK5AFieldMatch"] &&
        row["K6EK6BBehaviorMatch"], " exact=",
      row["K6E"]["FinalExact"], " hit=",
      row["K6E"]["ExactWordCacheHitFraction"], " E/B/5=",
      row["K6ERuntimeSeconds"], "/", row["K6BRuntimeSeconds"], "/",
      row["K5ARuntimeSeconds"]],
    {index, Length[worlds]}];
  rows
];

Print["S132-K6F FRESH EXACT ACTION-WORD CACHE CONFIRMATION"];
Print["Core modified=False; fresh worlds=True; K6E hash match=",
  k6eSourceHashMatch];

{totalRuntimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunOnlineStreamK6F[
    selectedStructuredWorlds, manifest["QueryOrderSeeds"],
    "FRESH_STRUCTURED"];
  controlStream = RunOnlineStreamK6F[
    selectedControlWorlds,
    manifest["ControlQueryOrderSeeds"], "RANK_MATCHED_CONTROL"];
  challengeRows = RunChallengesK6F[
    selectedChallengeWorlds,
    manifest["ChallengeQueryOrderSeeds"],
    structuredStream["FinalLibrary"]];
  {structuredStream, controlStream, challengeRows}
];

familyMap = Association@Map[#1["WorldID"] -> #1["Family"] &,
  manifest["StructuredWorldSpecifications"]];
structuredRows = Map[
  Join[#1, <|"Family" -> familyMap[#1["WorldID"]]|>] &,
  structuredStream["Rows"]];
controlRows = controlStream["Rows"];
allRows = Join[structuredRows, controlRows, challengeRows];
k6eRows = Lookup[allRows, "K6E"];
k6bRows = Lookup[allRows, "K6B"];
k5aRows = Lookup[allRows, "K5A"];

allTripleFieldMatch = And @@ Map[
  #1["K6EK5AFieldMatch"] && #1["K6BK5AFieldMatch"] &&
    #1["K6EK6BBehaviorMatch"] &, allRows];
allExact = And @@ Join[Lookup[k6eRows, "FinalExact"],
  Lookup[k6bRows, "FinalExact"], Lookup[k5aRows, "FinalExact"]];
unsafeCount = Total@Join[
  Lookup[k6eRows, "UnsafeCommittedInferenceCount"],
  Lookup[k6bRows, "UnsafeCommittedInferenceCount"],
  Lookup[k5aRows, "UnsafeCommittedInferenceCount"]];
logicalRequests = Total@Lookup[k6eRows, "LogicalTraceRequestCount"];
cacheHits = Total@Lookup[k6eRows, "ExactWordCacheHitCount"];
physicalEvaluations = Total@Lookup[k6eRows,
  "PhysicalTraceEvaluationCount"];
logicalTraceLookups = Total@Lookup[k6eRows,
  "ActualPersistentDirectAuditTraceCellLookups"];
physicalTraceLookups = Total@Lookup[k6eRows,
  "PhysicalTraceCellLookupCount"];
cacheAccountingPass = And @@ Map[
  #1["LogicalTraceRequestCount"] ===
      2 #1["ActualPersistentDirectAuditItemEvaluations"] &&
    #1["ExactWordCacheHitCount"] +
      #1["PhysicalTraceEvaluationCount"] ===
        #1["LogicalTraceRequestCount"] &&
    #1["PhysicalTraceCellLookupCount"] <=
      #1["ActualPersistentDirectAuditTraceCellLookups"] &,
  k6eRows];
physicalWorkReduced = physicalTraceLookups < logicalTraceLookups;
cacheExercised = logicalRequests > 0 && cacheHits > 0 &&
  physicalEvaluations < logicalRequests;
allArraysPacked = And @@ Join[
  Lookup[k6eRows, "AllNumericAuditArraysPacked"],
  Lookup[k6eRows, "AllExactWordCacheArraysPacked"],
  Lookup[k6bRows, "AllNumericAuditArraysPacked"]];
k6eRuntimeSeconds = Total@Lookup[allRows, "K6ERuntimeSeconds"];
k6bRuntimeSeconds = Total@Lookup[allRows, "K6BRuntimeSeconds"];
k5aRuntimeSeconds = Total@Lookup[allRows, "K5ARuntimeSeconds"];
fasterThanK6B = k6eRuntimeSeconds < k6bRuntimeSeconds;
fasterThanK5A = k6eRuntimeSeconds < k5aRuntimeSeconds;
priorConceptUsed = AnyTrue[structuredRows,
  TrueQ[#1["PriorCreatedConceptUsed"]] &];
startingEmpty = First[structuredRows]["LibraryBeforeCount"] === 0 &&
  First[controlRows]["LibraryBeforeCount"] === 0;
structuredLibraryNonempty = Length[
  structuredStream["FinalLibrary"]] > 0;
nearLawExact = If[challengeRows === {}, True,
  And @@ Join[
    Lookup[Lookup[challengeRows, "K6E"], "FinalExact"],
    Lookup[Lookup[challengeRows, "K6B"], "FinalExact"],
    Lookup[Lookup[challengeRows, "K5A"], "FinalExact"]]];

mainGatePass = fullFreshProfile && k6eSourceHashMatch && startingEmpty &&
  structuredLibraryNonempty && priorConceptUsed && allTripleFieldMatch &&
  allExact && unsafeCount === 0 && cacheAccountingPass &&
  physicalWorkReduced && cacheExercised && allArraysPacked &&
  fasterThanK6B && fasterThanK5A && nearLawExact;

result = <|
  "Stage" -> "S132-K6F fresh exact action-word cache confirmation",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "Profile" -> manifest["Profile"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "TotalRuntimeSeconds" -> totalRuntimeSeconds,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "FullFreshProfile" -> fullFreshProfile,
  "WorldLimit" -> worldLimit,
  "AcceptedK6ESourceHashMatch" -> k6eSourceHashMatch,
  "AcceptedK6ESourceSHA256" -> acceptedK6ESourceHash,
  "CanonicalTCCTModified" -> False,
  "K3BK4AK5AK6BMechanismsModified" -> False,
  "OnlyRepeatedActionWordTraceExecutionChanged" -> True,
  "StartingConceptLibraryCount" -> 0,
  "MaximumConceptWordLength" -> maximumConceptWordLength,
  "AllK6EK6BK5AFieldsExactlyEqual" -> allTripleFieldMatch,
  "AllFinalModelsExact" -> allExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
  "CacheAccountingConservationPass" -> cacheAccountingPass,
  "LogicalTraceRequestCount" -> logicalRequests,
  "ExactWordCacheHitCount" -> cacheHits,
  "ExactWordCacheHitFraction" -> If[logicalRequests > 0,
    N[cacheHits/logicalRequests], 0.],
  "PhysicalTraceEvaluationCount" -> physicalEvaluations,
  "LogicalTraceCellLookupCount" -> logicalTraceLookups,
  "PhysicalTraceCellLookupCount" -> physicalTraceLookups,
  "PhysicalTraceCellLookupReductionFraction" -> If[
    logicalTraceLookups > 0,
    N[1 - physicalTraceLookups/logicalTraceLookups], 0.],
  "PhysicalTraceWorkStrictlyReduced" -> physicalWorkReduced,
  "ExactWordCacheActuallyExercised" -> cacheExercised,
  "AllBaseAndCacheNumericArraysPacked" -> allArraysPacked,
  "AggregateK6ERuntimeSeconds" -> k6eRuntimeSeconds,
  "AggregateK6BRuntimeSeconds" -> k6bRuntimeSeconds,
  "AggregateK5ARuntimeSeconds" -> k5aRuntimeSeconds,
  "K6ERuntimeStrictlyLowerThanK6B" -> fasterThanK6B,
  "K6ERuntimeStrictlyLowerThanK5A" -> fasterThanK5A,
  "SpeedupVersusK6B" -> If[k6eRuntimeSeconds > 0,
    N[k6bRuntimeSeconds/k6eRuntimeSeconds], 0.],
  "SpeedupVersusK5A" -> If[k6eRuntimeSeconds > 0,
    N[k5aRuntimeSeconds/k6eRuntimeSeconds], 0.],
  "FinalStructuredLibraryCount" ->
    Length[structuredStream["FinalLibrary"]],
  "FinalControlLibraryCount" -> Length[controlStream["FinalLibrary"]],
  "PriorCreatedConceptUsedOnLaterWorld" -> priorConceptUsed,
  "AllNearLawChallengesExact" -> nearLawExact,
  "MainGatePass" -> mainGatePass,
  "StructuredResults" -> structuredRows,
  "ControlResults" -> controlRows,
  "NearLawChallengeResults" -> challengeRows,
  "FinalStructuredLibrary" -> structuredStream["FinalLibrary"],
  "FinalControlLibrary" -> controlStream["FinalLibrary"],
  "OpenEndedPrimitiveOrLanguageInventionProven" -> False,
  "Conclusion" -> If[mainGatePass,
    "FRESH_EXACT_WORD_CACHE_CONFIRMATION_GATE_PASS",
    "FRESH_EXACT_WORD_CACHE_CONFIRMATION_GATE_NOT_PASSED"]|>;

resultFileName = If[fullFreshProfile, "S132K6F_result.json",
  "S132K6F_smoke_result.json"];
Export[FileNameJoin[{rootDirectory, "results", resultFileName}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K6F COMPLETE pass=", mainGatePass, " triple=",
  allTripleFieldMatch, " E/B/5=", k6eRuntimeSeconds, "/",
  k6bRuntimeSeconds, "/", k5aRuntimeSeconds, " hit=", cacheHits,
  "/", logicalRequests];
Exit[If[mainGatePass, 0, 1]];
