(* ::Package:: *)

(* S132-K4B: fresh out-of-family bounded concept-transfer stress test. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K4B_pre_world_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "oracle",
  "S132K4B_oracle_sequences.json"}], "RawJSON"];

initialFraction = manifest["InitialDirectObservationFraction"];
batchFraction = manifest["DirectQueryBatchFraction"];
minimumWitnesses = manifest["MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = manifest["MaximumConceptWordLength"];

(* Load the frozen K3B learner without executing its old experiment. *)
k3bPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K3B_PartialObservationTransfer.wl"}];
k3bText = Import[k3bPath, "Text"];
k3bStart = First@First@StringPosition[k3bText,
  "CellKeyK3B[state_Integer, action_Integer]"];
k3bEnd = First@First@StringPosition[k3bText,
  "Print[\"S132-K3B PARTIAL-OBSERVATION CONCEPT TRANSFER\"]"];
ToExpression[StringTake[k3bText, {k3bStart, k3bEnd - 1}], InputForm];

(* Load the frozen K4A discovery/library/online-stream functions only. *)
k4aPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K4A_FreshOnlineConceptCreation.wl"}];
k4aText = Import[k4aPath, "Text"];
k4aStart = First@First@StringPosition[k4aText, "WordKeyK4[word_List]"];
k4aEnd = First@First@StringPosition[k4aText,
  "Print[\"S132-K4A FRESH ONLINE BOUNDED CONCEPT CREATION\"]"];
ToExpression[StringTake[k4aText, {k4aStart, k4aEnd - 1}], InputForm];

RunNearLawChallengesK4B[worlds_List, seeds_List, library_List] := Module[
  {rows = {}, world, seed, transfer, baseline},
  Do[
    world = worlds[[index]];
    seed = seeds[[index]];
    transfer = Block[{schemas = library},
      RunLearnerK3B[world, seed, True]];
    baseline = Block[{schemas = {}},
      RunLearnerK3B[world, seed, False]];
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

Print["S132-K4B OUT-OF-FAMILY CONCEPT TRANSFER STRESS TEST"];
Print["K4A learner unchanged=True; starting library=0; core modified=False"];

{runtimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunOnlineStreamK4[
    oracleInput["StructuredWorlds"], manifest["QueryOrderSeeds"],
    "OUT_OF_FAMILY_STRUCTURED"];
  controlStream = RunOnlineStreamK4[
    oracleInput["RankMatchedControls"],
    manifest["ControlQueryOrderSeeds"], "RANK_MATCHED_RANDOM"];
  challengeRows = RunNearLawChallengesK4B[
    oracleInput["NearLawChallenges"],
    manifest["ChallengeQueryOrderSeeds"],
    structuredStream["FinalLibrary"]];
  {structuredStream, controlStream, challengeRows}
];

familyMap = Association@Map[
  #1["WorldID"] -> #1["Family"] &,
  manifest["StructuredWorldSpecifications"]];
structuredRows = Map[
  Join[#1, <|"Family" -> familyMap[#1["WorldID"]]|>] &,
  structuredStream["Rows"]];
controlRows = controlStream["Rows"];

Do[Print[row["WorldID"], " family=", row["Family"],
    " library=", row["LibraryBeforeCount"], "->",
    row["LibraryAfterCount"], " MQ saved=",
    row["MembershipQuerySavings"], " concrete saved=",
    row["ConcreteOracleCellCostSavings"], " exact=",
    row["Transfer"]["FinalExact"]], {row, structuredRows}];
Do[Print[row["WorldID"], " near-law MQ saved=",
    row["MembershipQuerySavings"], " CE=",
    row["Transfer"]["EquivalenceCounterexampleCount"], " exact=",
    row["Transfer"]["FinalExact"]], {row, challengeRows}];

allExact = And @@ Join[
  Lookup[Lookup[structuredRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[structuredRows, "Baseline"], "FinalExact"],
  Lookup[Lookup[controlRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[controlRows, "Baseline"], "FinalExact"],
  Lookup[Lookup[challengeRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[challengeRows, "Baseline"], "FinalExact"]];
unsafeCount = Total@Join[
  Lookup[Lookup[structuredRows, "Transfer"],
    "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[controlRows, "Transfer"],
    "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[challengeRows, "Transfer"],
    "UnsafeCommittedInferenceCount"]];

families = manifest["GeneratorFamilies"];
familyPositiveSavings = Association@Table[
  family -> AnyTrue[
    Select[structuredRows, #1["Family"] === family &&
      #1["LibraryBeforeCount"] > 0 &],
    #1["MembershipQuerySavings"] > 0 &], {family, families}];
positiveFamilyCount = Count[Values[familyPositiveSavings], True];

structuredMQSavings = Total[Lookup[structuredRows,
  "MembershipQuerySavings"]];
structuredLogicalSavings = Total[Lookup[structuredRows,
  "LogicalInteractionCostSavings"]];
structuredConcreteSavings = Total[Lookup[structuredRows,
  "ConcreteOracleCellCostSavings"]];
controlMQSavings = Total[Lookup[controlRows, "MembershipQuerySavings"]];
controlConcreteSavings = Total[Lookup[controlRows,
  "ConcreteOracleCellCostSavings"]];
challengeMQSavings = Total[Lookup[challengeRows,
  "MembershipQuerySavings"]];
challengeConcreteSavings = Total[Lookup[challengeRows,
  "ConcreteOracleCellCostSavings"]];
priorConceptUsed = AnyTrue[structuredRows,
  #1["LibraryBeforeCount"] > 0 &&
    #1["Transfer"]["FinalInferredTransitionCount"] > 0 &];
startingEmpty = First[structuredRows]["LibraryBeforeCount"] === 0 &&
  First[controlRows]["LibraryBeforeCount"] === 0;
nearLawExact = And @@ Join[
  Lookup[Lookup[challengeRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[challengeRows, "Baseline"], "FinalExact"]];

mainGatePass = startingEmpty && allExact && unsafeCount === 0 &&
  Length[structuredStream["FinalLibrary"]] > 0 && priorConceptUsed &&
  positiveFamilyCount >= 3 && structuredMQSavings > 0 &&
  structuredConcreteSavings > 0 &&
  structuredConcreteSavings > controlConcreteSavings && nearLawExact;

result = <|
  "Stage" -> "S132-K4B fresh out-of-family bounded concept transfer stress test",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "RuntimeSeconds" -> runtimeSeconds,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "StartingConceptLibraryCount" -> 0,
  "PreloadedK4ASchemaCount" -> 0,
  "MaximumConceptWordLength" -> maximumConceptWordLength,
  "CanonicalTCCTModified" -> False,
  "FrozenK3BAndK4ALearnerModified" -> False,
  "GeneratorTruthReadByLearner" -> False,
  "AllFinalModelsExact" -> allExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
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
    "OUT_OF_FAMILY_BOUNDED_CONCEPT_TRANSFER_MAIN_GATE_PASS",
    "OUT_OF_FAMILY_BOUNDED_CONCEPT_TRANSFER_MAIN_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K4B_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K4B COMPLETE pass=", mainGatePass,
  " structured MQ saved=", structuredMQSavings,
  " structured concrete saved=", structuredConcreteSavings,
  " control concrete saved=", controlConcreteSavings];
Exit[If[mainGatePass, 0, 1]];
