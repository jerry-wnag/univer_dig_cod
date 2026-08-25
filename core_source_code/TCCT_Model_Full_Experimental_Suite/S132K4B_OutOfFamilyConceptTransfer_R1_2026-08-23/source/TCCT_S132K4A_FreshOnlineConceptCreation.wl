(* ::Package:: *)

(* S132-K4A: fresh sequential bounded concept creation from an empty library. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K4A_pre_world_manifest.json"}], "RawJSON"];
oracleInput = Import[FileNameJoin[{rootDirectory, "oracle",
  "S132K4A_oracle_sequences.json"}], "RawJSON"];

initialFraction = manifest["InitialDirectObservationFraction"];
batchFraction = manifest["DirectQueryBatchFraction"];
minimumWitnesses = manifest["MinimumDirectPositiveWitnessesBeforeInference"];
maximumConceptWordLength = manifest["MaximumConceptWordLength"];

(* Load the frozen and already independently verified K3B partial learner only. *)
k3bPath = FileNameJoin[{sourceDirectory,
  "TCCT_S132K3B_PartialObservationTransfer.wl"}];
k3bText = Import[k3bPath, "Text"];
k3bStart = First@First@StringPosition[k3bText,
  "CellKeyK3B[state_Integer, action_Integer]"];
k3bEnd = First@First@StringPosition[k3bText,
  "Print[\"S132-K3B PARTIAL-OBSERVATION CONCEPT TRANSFER\"]"];
ToExpression[StringTake[k3bText, {k3bStart, k3bEnd - 1}], InputForm];

WordKeyK4[word_List] := ToString[InputForm[word]];

WordTransformK4[table_List, word_List] := Fold[
  Function[{mapping, action}, table[[mapping, action]]],
  Range[Length[table]], word];

CanonicalizeEquationK4[long_List, short_List] := Module[
  {mapping = <||>, next = 0, canonicalize},
  canonicalize[word_List] := Table[
    If[!KeyExistsQ[mapping, action], next++;
      AssociateTo[mapping, action -> next]];
    mapping[action], {action, word}];
  {canonicalize[long], canonicalize[short]}
];

SchemaSortKeyK4[schema_List] :=
  {Length[schema[[1]]], schema[[1]], Length[schema[[2]]], schema[[2]]};

SchemaKeyK4[schema_List] := ToString[InputForm[schema]];

DiscoverSchemasK4[table_List] := Module[
  {actionCount = Length[First[table]], words, groups, equations = {},
   representative, longer},
  words = Join[{{}}, Flatten[Table[
    Tuples[Range[actionCount], length],
    {length, 1, maximumConceptWordLength}], 1]];
  groups = GatherBy[words, WordTransformK4[table, #] &];
  Do[
    representative = First@SortBy[group, Function[word,
      {Length[word], word}]];
    longer = Select[group, Length[#] > Length[representative] &];
    equations = Join[equations,
      CanonicalizeEquationK4[#, representative] & /@ longer],
    {group, groups}];
  SortBy[DeleteDuplicates[equations], SchemaSortKeyK4]
];

(* The library is updated in place; the counter is returned explicitly. *)
SetAttributes[UpdateLibraryK4, HoldFirst];
UpdateLibraryK4[library_, currentID_Integer, discovered_List,
  worldID_String] := Module[{key, nextID = currentID, newCount = 0, record},
  Do[
    key = SchemaKeyK4[schema];
    If[!KeyExistsQ[library, key],
      nextID++;
      AssociateTo[library, key -> <|"SchemaID" -> nextID,
        "Schema" -> schema, "FirstCreatedAfterWorld" -> worldID,
        "SupportWorlds" -> {worldID}|>];
      newCount++,
      record = library[key];
      AssociateTo[record, "SupportWorlds" ->
        Sort@DeleteDuplicates@Append[record["SupportWorlds"], worldID]];
      AssociateTo[library, key -> record]],
    {schema, discovered}];
  <|"NextID" -> nextID, "NewCount" -> newCount|>
];

RunOnlineStreamK4[worlds_List, seeds_List, streamName_String] := Module[
  {library = <||>, nextID = 0, rows = {}, available, transfer,
   baseline, discovered, update, newCount, world, seed, mqSavings,
   logicalSavings, concreteSavings},
  Do[
    world = worlds[[index]];
    seed = seeds[[index]];
    available = SortBy[Values[library], #["SchemaID"] &];
    transfer = Block[{schemas = available},
      RunLearnerK3B[world, seed, True]];
    baseline = Block[{schemas = {}},
      RunLearnerK3B[world, seed, False]];
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

Print["S132-K4A FRESH ONLINE BOUNDED CONCEPT CREATION"];
Print["Starting library=0; preloaded K3A schemas=False; core modified=False"];

{runtimeSeconds, streams} = AbsoluteTiming[
  structuredStream = RunOnlineStreamK4[
    oracleInput["StructuredWorlds"], manifest["QueryOrderSeeds"],
    "STRUCTURED"];
  controlStream = RunOnlineStreamK4[
    oracleInput["RankMatchedControls"],
    manifest["ControlQueryOrderSeeds"], "RANK_MATCHED_CONTROL"];
  {structuredStream, controlStream}
];

structuredRows = structuredStream["Rows"];
controlRows = controlStream["Rows"];
Do[Print[row["WorldID"], " library=", row["LibraryBeforeCount"],
    "->", row["LibraryAfterCount"], " MQ saved=",
    row["MembershipQuerySavings"], " exact=",
    row["Transfer"]["FinalExact"]], {row, structuredRows}];

allExact = And @@ Join[
  Lookup[Lookup[structuredRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[structuredRows, "Baseline"], "FinalExact"],
  Lookup[Lookup[controlRows, "Transfer"], "FinalExact"],
  Lookup[Lookup[controlRows, "Baseline"], "FinalExact"]];
unsafeCount = Total@Join[
  Lookup[Lookup[structuredRows, "Transfer"],
    "UnsafeCommittedInferenceCount"],
  Lookup[Lookup[controlRows, "Transfer"],
    "UnsafeCommittedInferenceCount"]];
eligibleRows = Select[structuredRows, #["LibraryBeforeCount"] > 0 &];
positiveEligible = Count[Lookup[eligibleRows, "MembershipQuerySavings"],
  value_ /; value > 0];
eligibleFraction = If[Length[eligibleRows] > 0,
  N[positiveEligible/Length[eligibleRows]], 0.];
structuredMQSavings = Total[Lookup[structuredRows,
  "MembershipQuerySavings"]];
structuredLogicalSavings = Total[Lookup[structuredRows,
  "LogicalInteractionCostSavings"]];
structuredConcreteSavings = Total[Lookup[structuredRows,
  "ConcreteOracleCellCostSavings"]];
controlMQSavings = Total[Lookup[controlRows, "MembershipQuerySavings"]];
controlConcreteSavings = Total[Lookup[controlRows,
  "ConcreteOracleCellCostSavings"]];
priorConceptUsed = Count[Lookup[structuredRows, "PriorCreatedConceptUsed"],
  True] > 0;
startingEmpty = First[structuredRows]["LibraryBeforeCount"] === 0 &&
  First[controlRows]["LibraryBeforeCount"] === 0;

gatePass = startingEmpty && allExact && unsafeCount === 0 &&
  Length[structuredStream["FinalLibrary"]] > 0 && priorConceptUsed &&
  eligibleFraction >= 0.5 && structuredMQSavings > 0 &&
  structuredConcreteSavings > 0 &&
  structuredConcreteSavings > controlConcreteSavings;

result = <|
  "Stage" -> "S132-K4A fresh online bounded concept creation",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "RuntimeSeconds" -> runtimeSeconds,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "StartingConceptLibraryCount" -> 0,
  "PreloadedK3ASchemaCount" -> 0,
  "CanonicalTCCTModified" -> False,
  "GeneratorTruthReadByLearner" -> False,
  "MaximumConceptWordLength" -> maximumConceptWordLength,
  "AllFinalModelsExact" -> allExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
  "FinalStructuredLibraryCount" ->
    Length[structuredStream["FinalLibrary"]],
  "FinalControlLibraryCount" -> Length[controlStream["FinalLibrary"]],
  "PriorCreatedConceptUsedOnLaterWorld" -> priorConceptUsed,
  "EligibleStructuredWorldCount" -> Length[eligibleRows],
  "PositiveSavingsEligibleWorldCount" -> positiveEligible,
  "PositiveSavingsEligibleWorldFraction" -> eligibleFraction,
  "AggregateStructuredMembershipQuerySavings" -> structuredMQSavings,
  "AggregateStructuredLogicalInteractionCostSavings" ->
    structuredLogicalSavings,
  "AggregateStructuredConcreteOracleCellCostSavings" ->
    structuredConcreteSavings,
  "AggregateControlMembershipQuerySavings" -> controlMQSavings,
  "AggregateControlConcreteOracleCellCostSavings" ->
    controlConcreteSavings,
  "FreshOnlineBoundedConceptCreationGatePass" -> gatePass,
  "OpenEndedPrimitiveOrLanguageInventionProven" -> False,
  "B8ASymbolicLearnerQueryReductionProven" -> False,
  "StructuredResults" -> structuredRows,
  "ControlResults" -> controlRows,
  "FinalStructuredLibrary" -> structuredStream["FinalLibrary"],
  "FinalControlLibrary" -> controlStream["FinalLibrary"],
  "Conclusion" -> If[gatePass,
    "FRESH_ONLINE_BOUNDED_CONCEPT_CREATION_GATE_PASS",
    "FRESH_ONLINE_BOUNDED_CONCEPT_CREATION_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K4A_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K4A COMPLETE pass=", gatePass,
  " structured MQ saved=", structuredMQSavings,
  " control MQ saved=", controlMQSavings];
Exit[If[gatePass, 0, 1]];
