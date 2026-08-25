(* ::Package:: *)

(* S132-K5B: fresh paired confirmation of exact indexed activation. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K5B_pre_world_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "oracle",
  "S132K5B_oracle_sequences.json"}], "RawJSON"];

initialFraction = manifest["InitialDirectObservationFraction"];
batchFraction = manifest["DirectQueryBatchFraction"];
minimumWitnesses = manifest[
  "MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = manifest["MaximumConceptWordLength"];

(* Load the frozen full-scan K3B learner without executing its experiment. *)
k3bPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K3B_PartialObservationTransfer.wl"}];
k3bText = Import[k3bPath, "Text"];
k3bStart = First@First@StringPosition[k3bText,
  "CellKeyK3B[state_Integer, action_Integer]"];
k3bEnd = First@First@StringPosition[k3bText,
  "Print[\"S132-K3B PARTIAL-OBSERVATION CONCEPT TRANSFER\"]"];
ToExpression[StringTake[k3bText, {k3bStart, k3bEnd - 1}], InputForm];

(* Load the frozen K4A discovery and library mechanism only. *)
k4aPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K4A_FreshOnlineConceptCreation.wl"}];
k4aText = Import[k4aPath, "Text"];
k4aStart = First@First@StringPosition[k4aText, "WordKeyK4[word_List]"];
k4aEnd = First@First@StringPosition[k4aText,
  "Print[\"S132-K4A FRESH ONLINE BOUNDED CONCEPT CREATION\"]"];
ToExpression[StringTake[k4aText, {k4aStart, k4aEnd - 1}], InputForm];

(* Load exactly the retrospective-certified K5A indexed implementation. *)
k5aPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K5A_ExactIndexedActivation.wl"}];
k5aText = Import[k5aPath, "Text"];
k5aStart = First@First@StringPosition[k5aText,
  "TraceWordIndexedK5A[start_Integer, word_List,"];
k5aEnd = First@First@StringPosition[k5aText,
  "Print[\"S132-K5A RETROSPECTIVE EXACT INDEXED ACTIVATION\"]"];
ToExpression[StringTake[k5aText, {k5aStart, k5aEnd - 1}], InputForm];

OriginalFieldMatchK5B[indexed_Association, full_Association] :=
  KeyTake[indexed, Keys[full]] === full;

RunPairedLearnersK5B[world_Association, seed_Integer,
  available_List, sequenceIndex_Integer] := Module[
  {indexed, full, baseline, indexedSeconds, fullSeconds,
   baselineSeconds},
  If[OddQ[sequenceIndex],
    {indexedSeconds, indexed} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerIndexedK5A[world, seed, True]]];
    {fullSeconds, full} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerK3B[world, seed, True]]],
    {fullSeconds, full} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerK3B[world, seed, True]]];
    {indexedSeconds, indexed} = AbsoluteTiming[
      Block[{schemas = available},
        RunLearnerIndexedK5A[world, seed, True]]]
  ];
  {baselineSeconds, baseline} = AbsoluteTiming[
    Block[{schemas = {}}, RunLearnerK3B[world, seed, False]]];
  <|"IndexedTransfer" -> indexed, "FullScanTransfer" -> full,
    "Baseline" -> baseline, "IndexedRuntimeSeconds" -> indexedSeconds,
    "FullScanRuntimeSeconds" -> fullSeconds,
    "BaselineRuntimeSeconds" -> baselineSeconds,
    "PairedOriginalFieldsExactlyEqual" ->
      OriginalFieldMatchK5B[indexed, full]|>
];

RunPairedOnlineStreamK5B[worlds_List, seeds_List,
  streamName_String] := Module[
  {library = <||>, nextID = 0, rows = {}, world, available,
   paired, discovered, update, newCount, row},
  Do[
    world = worlds[[index]];
    available = SortBy[Values[library], #["SchemaID"] &];
    paired = RunPairedLearnersK5B[
      world, seeds[[index]], available, index];
    discovered = DiscoverSchemasK4[world["TransitionTable"]];
    update = UpdateLibraryK4[library, nextID, discovered,
      world["WorldID"]];
    nextID = update["NextID"];
    newCount = update["NewCount"];
    row = Join[<|"Stream" -> streamName,
       "SequenceIndex" -> index, "WorldID" -> world["WorldID"],
       "LibraryBeforeCount" -> Length[available],
       "SchemasDiscoveredThisWorld" -> Length[discovered],
       "NewSchemaCount" -> newCount,
       "LibraryAfterCount" -> Length[library],
       "PriorCreatedConceptUsed" ->
         paired["IndexedTransfer"]["FinalInferredTransitionCount"] > 0,
       "MembershipQuerySavings" ->
         paired["Baseline"]["MembershipQueries"] -
           paired["IndexedTransfer"]["MembershipQueries"],
       "LogicalInteractionCostSavings" ->
         paired["Baseline"]["LogicalInteractionCost"] -
           paired["IndexedTransfer"]["LogicalInteractionCost"],
       "ConcreteOracleCellCostSavings" ->
         paired["Baseline"]["ConcreteOracleCellCost"] -
           paired["IndexedTransfer"]["ConcreteOracleCellCost"]|>,
      paired];
    AppendTo[rows, row];
    Print[streamName, " ", world["WorldID"], " paired=",
      row["PairedOriginalFieldsExactlyEqual"], " exact=",
      row["IndexedTransfer"]["FinalExact"], " indexedSec=",
      row["IndexedRuntimeSeconds"], " fullSec=",
      row["FullScanRuntimeSeconds"], " library=",
      row["LibraryBeforeCount"], "->", row["LibraryAfterCount"]],
    {index, Length[worlds]}];
  <|"Rows" -> rows,
    "FinalLibrary" -> SortBy[Values[library], #["SchemaID"] &]|>
];

RunPairedChallengesK5B[worlds_List, seeds_List, library_List] := Module[
  {rows = {}, world, paired, row},
  Do[
    world = worlds[[index]];
    paired = RunPairedLearnersK5B[
      world, seeds[[index]], library, index];
    row = Join[<|"WorldID" -> world["WorldID"],
       "AvailableStructuredConceptCount" -> Length[library],
       "MembershipQuerySavings" ->
         paired["Baseline"]["MembershipQueries"] -
           paired["IndexedTransfer"]["MembershipQueries"],
       "LogicalInteractionCostSavings" ->
         paired["Baseline"]["LogicalInteractionCost"] -
           paired["IndexedTransfer"]["LogicalInteractionCost"],
       "ConcreteOracleCellCostSavings" ->
         paired["Baseline"]["ConcreteOracleCellCost"] -
           paired["IndexedTransfer"]["ConcreteOracleCellCost"]|>,
      paired];
    AppendTo[rows, row];
    Print["NEAR_LAW ", world["WorldID"], " paired=",
      row["PairedOriginalFieldsExactlyEqual"], " exact=",
      row["IndexedTransfer"]["FinalExact"], " indexedSec=",
      row["IndexedRuntimeSeconds"], " fullSec=",
      row["FullScanRuntimeSeconds"]],
    {index, Length[worlds]}];
  rows
];

Print["S132-K5B FRESH PAIRED EXACT INDEXED CONFIRMATION"];
Print["Core modified=False; concept mechanism modified=False; paired fresh worlds=True"];

{totalRuntimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunPairedOnlineStreamK5B[
    oracleInput["StructuredWorlds"], manifest["QueryOrderSeeds"],
    "FRESH_STRUCTURED"];
  controlStream = RunPairedOnlineStreamK5B[
    oracleInput["RankMatchedControls"],
    manifest["ControlQueryOrderSeeds"], "RANK_MATCHED_CONTROL"];
  challengeRows = RunPairedChallengesK5B[
    oracleInput["NearLawChallenges"],
    manifest["ChallengeQueryOrderSeeds"],
    structuredStream["FinalLibrary"]];
  {structuredStream, controlStream, challengeRows}
];

familyMap = Association@Map[
  #["WorldID"] -> #["Family"] &,
  manifest["StructuredWorldSpecifications"]];
structuredRows = Map[
  Join[#, <|"Family" -> familyMap[#["WorldID"]]|>] &,
  structuredStream["Rows"]];
controlRows = controlStream["Rows"];
allRows = Join[structuredRows, controlRows, challengeRows];

allPairedMatch = And @@ Lookup[allRows,
  "PairedOriginalFieldsExactlyEqual"];
allExact = And @@ Join[
  Lookup[Lookup[allRows, "IndexedTransfer"], "FinalExact"],
  Lookup[Lookup[allRows, "FullScanTransfer"], "FinalExact"],
  Lookup[Lookup[allRows, "Baseline"], "FinalExact"]];
unsafeCount = Total@Join[
  Lookup[Lookup[allRows, "IndexedTransfer"],
    "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[allRows, "FullScanTransfer"],
    "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[allRows, "Baseline"],
    "UnsafeCommittedInferenceCount"]];

actualIndexedEvaluations = Total@Lookup[
  Lookup[allRows, "IndexedTransfer"],
  "ActualIndexedClosureItemEvaluations"];
fullScanEquivalentEvaluations = Total@Lookup[
  Lookup[allRows, "IndexedTransfer"],
  "FullScanEquivalentClosureItemEvaluations"];
actualDirectAuditChecks = Total@Lookup[
  Lookup[allRows, "IndexedTransfer"],
  "ActualDirectAuditStateChecks"];
fullDirectAuditChecks = Total@Lookup[
  Lookup[allRows, "IndexedTransfer"],
  "FullRescanEquivalentDirectAuditStateChecks"];
deterministicWorkReduced = actualIndexedEvaluations <
    fullScanEquivalentEvaluations &&
  actualDirectAuditChecks <= fullDirectAuditChecks;

indexedRuntimeSeconds = Total@Lookup[allRows,
  "IndexedRuntimeSeconds"];
fullScanRuntimeSeconds = Total@Lookup[allRows,
  "FullScanRuntimeSeconds"];
baselineRuntimeSeconds = Total@Lookup[allRows,
  "BaselineRuntimeSeconds"];
runtimeImproved = indexedRuntimeSeconds < fullScanRuntimeSeconds;

families = manifest["GeneratorFamilies"];
familyPositiveSavings = Association@Table[
  family -> AnyTrue[
    Select[structuredRows, #["Family"] === family &&
      #["LibraryBeforeCount"] > 0 &],
    #["MembershipQuerySavings"] > 0 &], {family, families}];
positiveFamilyCount = Count[Values[familyPositiveSavings], True];
structuredMQSavings = Total@Lookup[structuredRows,
  "MembershipQuerySavings"];
structuredLogicalSavings = Total@Lookup[structuredRows,
  "LogicalInteractionCostSavings"];
structuredConcreteSavings = Total@Lookup[structuredRows,
  "ConcreteOracleCellCostSavings"];
controlMQSavings = Total@Lookup[controlRows, "MembershipQuerySavings"];
controlConcreteSavings = Total@Lookup[controlRows,
  "ConcreteOracleCellCostSavings"];
challengeMQSavings = Total@Lookup[challengeRows,
  "MembershipQuerySavings"];
challengeConcreteSavings = Total@Lookup[challengeRows,
  "ConcreteOracleCellCostSavings"];
priorConceptUsed = AnyTrue[structuredRows,
  #["LibraryBeforeCount"] > 0 &&
    #["IndexedTransfer"]["FinalInferredTransitionCount"] > 0 &];
startingEmpty = First[structuredRows]["LibraryBeforeCount"] === 0 &&
  First[controlRows]["LibraryBeforeCount"] === 0;
nearLawExact = And @@ Join[
  Lookup[Lookup[challengeRows, "IndexedTransfer"], "FinalExact"],
  Lookup[Lookup[challengeRows, "FullScanTransfer"], "FinalExact"],
  Lookup[Lookup[challengeRows, "Baseline"], "FinalExact"]];
freshTransferGate = startingEmpty &&
  Length[structuredStream["FinalLibrary"]] > 0 && priorConceptUsed &&
  positiveFamilyCount >= 3 && structuredMQSavings > 0 &&
  structuredConcreteSavings > 0 &&
  structuredConcreteSavings > controlConcreteSavings;

mainGatePass = allPairedMatch && allExact && unsafeCount === 0 &&
  deterministicWorkReduced && runtimeImproved && freshTransferGate &&
  nearLawExact;

result = <|
  "Stage" -> "S132-K5B fresh paired exact indexed activation confirmation",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "Profile" -> manifest["Profile"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "TotalRuntimeSeconds" -> totalRuntimeSeconds,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "CanonicalTCCTModified" -> False,
  "FrozenK3BK4AAndK5AMechanismsModified" -> False,
  "OnlyExecutionStrategyChanged" -> True,
  "StartingConceptLibraryCount" -> 0,
  "MaximumConceptWordLength" -> maximumConceptWordLength,
  "PairedOriginalFieldsExactlyEqual" -> allPairedMatch,
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
  "DeterministicWorkReduced" -> deterministicWorkReduced,
  "AggregateIndexedRuntimeSeconds" -> indexedRuntimeSeconds,
  "AggregateFullScanRuntimeSeconds" -> fullScanRuntimeSeconds,
  "AggregateBaselineRuntimeSeconds" -> baselineRuntimeSeconds,
  "IndexedRuntimeStrictlyLower" -> runtimeImproved,
  "PairedRuntimeSpeedup" -> If[indexedRuntimeSeconds > 0,
    N[fullScanRuntimeSeconds/indexedRuntimeSeconds], 0.],
  "FinalStructuredLibraryCount" ->
    Length[structuredStream["FinalLibrary"]],
  "FinalControlLibraryCount" -> Length[controlStream["FinalLibrary"]],
  "PriorCreatedConceptUsedOnLaterWorld" -> priorConceptUsed,
  "PositiveSavingsFamilyCoverage" -> familyPositiveSavings,
  "PositiveSavingsFamilyCount" -> positiveFamilyCount,
  "AggregateStructuredMembershipQuerySavings" -> structuredMQSavings,
  "AggregateStructuredLogicalInteractionCostSavings" ->
    structuredLogicalSavings,
  "AggregateStructuredConcreteOracleCellCostSavings" ->
    structuredConcreteSavings,
  "AggregateControlMembershipQuerySavings" -> controlMQSavings,
  "AggregateControlConcreteOracleCellCostSavings" ->
    controlConcreteSavings,
  "AggregateNearLawMembershipQuerySavings" -> challengeMQSavings,
  "AggregateNearLawConcreteOracleCellCostSavings" ->
    challengeConcreteSavings,
  "FreshStructuredTransferGatePass" -> freshTransferGate,
  "AllNearLawChallengesExact" -> nearLawExact,
  "MainGatePass" -> mainGatePass,
  "StateRelabelDiscoveryInvariancePendingIndependentAudit" -> True,
  "OpenEndedPrimitiveOrLanguageInventionProven" -> False,
  "ObservationNoiseRobustnessProven" -> False,
  "WorldSizeUnknownToLearner" -> False,
  "StructuredResults" -> structuredRows,
  "ControlResults" -> controlRows,
  "NearLawChallengeResults" -> challengeRows,
  "FinalStructuredLibrary" -> structuredStream["FinalLibrary"],
  "FinalControlLibrary" -> controlStream["FinalLibrary"],
  "Conclusion" -> If[mainGatePass,
    "FRESH_EXACT_INDEXED_CONFIRMATION_GATE_PASS",
    "FRESH_EXACT_INDEXED_CONFIRMATION_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K5B_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K5B COMPLETE pass=", mainGatePass,
  " paired=", allPairedMatch, " speedup=",
  result["PairedRuntimeSpeedup"], " indexed eval=",
  actualIndexedEvaluations, " full-equivalent=",
  fullScanEquivalentEvaluations];
Exit[If[mainGatePass, 0, 1]];
