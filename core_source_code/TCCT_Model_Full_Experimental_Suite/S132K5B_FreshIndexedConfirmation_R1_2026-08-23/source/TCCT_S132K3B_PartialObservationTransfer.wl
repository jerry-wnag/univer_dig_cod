(* ::Package:: *)

(* S132-K3B: retrospective partial-observation concept transfer with rollback. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K3B_frozen_manifest.json"}], "RawJSON"];
schemaInput = Import[FileNameJoin[{rootDirectory, "input",
  "S132K3B_schema_library.json"}], "RawJSON"];
testInput = Import[FileNameJoin[{rootDirectory, "input",
  "S132K3B_test_automata.json"}], "RawJSON"];
controlInput = Import[FileNameJoin[{rootDirectory, "input",
  "S132K3B_control_automata.json"}], "RawJSON"];

initialFraction = manifest["InitialDirectObservationFraction"];
batchFraction = manifest["DirectQueryBatchFraction"];
minimumWitnesses = manifest["MinimumDirectPositiveWitnessesBeforeInference"];
schemas = schemaInput["Schemas"];

CellKeyK3B[state_Integer, action_Integer] :=
  ToString[state] <> ":" <> ToString[action];

CellFromKeyK3B[key_String] := ToExpression /@ StringSplit[key, ":"];

InstantiateSchemasK3B[actionCount_Integer] := Module[
  {instances = {}, schema, pattern, variableCount, assignments, long, short,
   nextID = 0, sorted},
  Do[
    pattern = schema["Schema"];
    variableCount = Max[Flatten[pattern], 0];
    assignments = If[variableCount <= actionCount,
      Permutations[Range[actionCount], {variableCount}], {}];
    Do[
      long = (assignment[[#]] &) /@ pattern[[1]];
      short = (assignment[[#]] &) /@ pattern[[2]];
      nextID++;
      AppendTo[instances, <|"InstanceID" -> nextID,
        "SchemaID" -> schema["SchemaID"], "Long" -> long,
        "Short" -> short|>],
      {assignment, assignments}],
    {schema, schemas}];
  sorted = SortBy[instances, Function[row,
    {row["SchemaID"], row["Long"], row["Short"]}]];
  MapIndexed[Join[KeyDrop[#1, {"InstanceID"}],
      <|"InstanceID" -> First[#2]|>] &, sorted]
];

TraceWordK3B[start_Integer, word_List, values_Association] := Module[
  {state = start, key, record, provenance = {}, index,
   early = Missing["NoEarlyResult"]},
  If[Length[word] == 0,
    Return[<|"Status" -> "Complete", "Target" -> state,
      "Provenance" -> {}|>]];
  Do[
    key = CellKeyK3B[state, word[[index]]];
    If[!KeyExistsQ[values, key],
      early = If[index == Length[word],
        <|"Status" -> "MissingFinal", "CellKey" -> key,
          "Provenance" -> DeleteDuplicates[provenance]|>,
        <|"Status" -> "Blocked", "Provenance" ->
          DeleteDuplicates[provenance]|>];
      Break[]];
    record = values[key];
    provenance = Join[provenance, Lookup[record, "Provenance", {}]];
    state = record["Target"],
    {index, Length[word]}];
  If[AssociationQ[early], early,
    <|"Status" -> "Complete", "Target" -> state,
      "Provenance" -> DeleteDuplicates[provenance]|>]
];

DirectWitnessAuditK3B[instance_Association, direct_Association,
  stateCount_Integer] := Module[{left, right, witnesses = 0,
  contradiction = False},
  Do[
    left = TraceWordK3B[state, instance["Long"], direct];
    right = TraceWordK3B[state, instance["Short"], direct];
    If[left["Status"] === "Complete" && right["Status"] === "Complete",
      If[left["Target"] === right["Target"], witnesses++,
        contradiction = True; Break[]]],
    {state, stateCount}];
  <|"Witnesses" -> witnesses, "Contradiction" -> contradiction|>
];

SetAttributes[AddDirectK3B, HoldFirst];
AddDirectK3B[direct_, table_List, key_String] := Module[{cell},
  cell = CellFromKeyK3B[key];
  AssociateTo[direct, key -> <|"Target" -> table[[cell[[1]], cell[[2]]]],
    "Direct" -> True, "Provenance" -> {}|>]
];

BuildClosureK3B[direct_Association, instances_List, rejectedInput_List,
  stateCount_Integer] := Module[
  {rejected = AssociationThread[rejectedInput -> ConstantArray[True,
      Length[rejectedInput]]], values, active, audits, admissible,
   changed, restart, left, right, proposals, grouped, key, candidates,
   targets, implicated, record, conflictGroups, inferenceCreated = 0,
   internalRollbackCount = 0, directRejected = 0, conflictRejected = 0,
   makeProposal},

  makeProposal[cellKey_String, target_Integer, provenance_List] :=
    <|"CellKey" -> cellKey, "Target" -> target,
      "Provenance" -> Sort@DeleteDuplicates[provenance]|>;

  While[True,
    values = Association[direct];
    active = Select[instances, !KeyExistsQ[rejected,
        #["InstanceID"]] &];
    audits = Association@Table[
      instance["InstanceID"] ->
        DirectWitnessAuditK3B[instance, direct, stateCount],
      {instance, active}];
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
    restart = False;
    changed = True;
    While[changed && !restart,
      changed = False;
      proposals = {};
      Do[
        Do[
          left = TraceWordK3B[state, instance["Long"], values];
          right = TraceWordK3B[state, instance["Short"], values];
          If[left["Status"] === "Complete" &&
              right["Status"] === "MissingFinal",
            AppendTo[proposals, makeProposal[right["CellKey"],
              left["Target"], Join[{instance["InstanceID"]},
                left["Provenance"], right["Provenance"]]]]];
          If[right["Status"] === "Complete" &&
              left["Status"] === "MissingFinal",
            AppendTo[proposals, makeProposal[left["CellKey"],
              right["Target"], Join[{instance["InstanceID"]},
                left["Provenance"], right["Provenance"]]]]],
          {state, stateCount}],
        {instance, admissible}];
      grouped = GroupBy[proposals, #CellKey &];
      conflictGroups = Select[Values[grouped],
        Length[DeleteDuplicates[Lookup[#, "Target"]]] > 1 &];
      If[Length[conflictGroups] > 0,
        implicated = Sort@DeleteDuplicates@Flatten[
          Lookup[Flatten[conflictGroups, 1], "Provenance"]];
        Do[AssociateTo[rejected, id -> True], {id, implicated}];
        conflictRejected += Length[implicated];
        internalRollbackCount++;
        restart = True,
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
              restart = True; Break[]],
            AssociateTo[values, key -> <|"Target" -> record["Target"],
              "Direct" -> False, "Provenance" -> record["Provenance"]|>];
            inferenceCreated++;
            changed = True],
          {key, Sort[Keys[grouped]]}]
      ];
    ];
    If[!restart, Break[]]
  ];
  <|"Values" -> values, "RejectedInstanceIDs" -> Keys[rejected],
    "ActiveAdmissibleInstanceCount" -> Length[admissible],
    "InferenceCreatedCount" -> inferenceCreated,
    "InternalRollbackCount" -> internalRollbackCount,
    "DirectContradictionRejectedCount" -> directRejected,
    "InferenceConflictRejectedCount" -> conflictRejected|>
];

EquivalenceOracleK3B[values_Association, table_List] := Module[
  {stateCount = Length[table], actionCount = Length[First[table]],
   inspected = 0, key, predicted},
  Catch[
    Do[
      inspected++;
      key = CellKeyK3B[state, action];
      If[!KeyExistsQ[values, key],
        Throw[<|"Exact" -> False, "InspectedCells" -> inspected,
          "MismatchKey" -> key, "Reason" -> "MISSING"|>]];
      predicted = values[key]["Target"];
      If[predicted =!= table[[state, action]],
        Throw[<|"Exact" -> False, "InspectedCells" -> inspected,
          "MismatchKey" -> key, "Reason" -> "WRONG",
          "PredictedTarget" -> predicted,
          "TrueTarget" -> table[[state, action]],
          "Provenance" -> values[key]["Provenance"]|>]],
      {state, stateCount}, {action, actionCount}];
    <|"Exact" -> True, "InspectedCells" -> inspected|>]
];

RunLearnerK3B[world_Association, seed_Integer, transferEnabled_] := Module[
  {table = world["TransitionTable"], stateCount = world["StateCount"],
   actionCount = world["ActionCount"], totalCells, allKeys, order,
   initialCount, batchSize, direct = <||>, values = <||>, instances,
   rejected = {}, membershipQueries = 0, equivalenceCalls = 0,
   equivalenceCells = 0, counterexamples = 0, rollbacks = 0,
   inferenceCreated = 0, internalRollbacks = 0,
   directContradictionRejected = 0, conflictRejected = 0,
   closure, missing, batch, eq, provenance, exact = False,
   finalInferred, uniqueDirect, logicalCost, concreteCost},
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
    closure = BuildClosureK3B[direct, instances, rejected, stateCount];
    values = closure["Values"];
    rejected = closure["RejectedInstanceIDs"];
    inferenceCreated += closure["InferenceCreatedCount"];
    internalRollbacks += closure["InternalRollbackCount"];
    directContradictionRejected +=
      closure["DirectContradictionRejectedCount"];
    conflictRejected += closure["InferenceConflictRejectedCount"];
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
    "UnsafeCommittedInferenceCount" -> If[exact, 0, finalInferred]|>
];

EvaluateWorldK3B[world_Association, seed_Integer] := Module[
  {transfer, baseline},
  transfer = RunLearnerK3B[world, seed, True];
  baseline = RunLearnerK3B[world, seed, False];
  <|"WorldID" -> world["WorldID"], "Seed" -> seed,
    "Transfer" -> transfer, "Baseline" -> baseline,
    "MembershipQuerySavings" ->
      baseline["MembershipQueries"] - transfer["MembershipQueries"],
    "LogicalInteractionCostSavings" ->
      baseline["LogicalInteractionCost"] - transfer["LogicalInteractionCost"],
    "ConcreteOracleCellCostSavings" ->
      baseline["ConcreteOracleCellCost"] - transfer["ConcreteOracleCellCost"]|>
];

Print["S132-K3B PARTIAL-OBSERVATION CONCEPT TRANSFER"];
Print["Retrospective=True; full-state schema prefilter=False; core modified=False"];

testWorlds = testInput["Automata"];
testSeeds = manifest["QueryOrderSeeds"];
testResults = MapThread[EvaluateWorldK3B, {testWorlds, testSeeds}];
Do[Print[row["WorldID"], " MQ saved=", row["MembershipQuerySavings"],
    " concrete saved=", row["ConcreteOracleCellCostSavings"],
    " CE=", row["Transfer"]["EquivalenceCounterexampleCount"],
    " exact=", row["Transfer"]["FinalExact"]], {row, testResults}];

controlWorlds = controlInput["Controls"];
controlSeeds = manifest["ControlQueryOrderSeeds"];
controlResults = MapThread[EvaluateWorldK3B, {controlWorlds, controlSeeds}];

structuredExact = And @@ Lookup[Lookup[testResults, "Transfer"], "FinalExact"];
baselineExact = And @@ Lookup[Lookup[testResults, "Baseline"], "FinalExact"];
controlExact = And @@ Lookup[Lookup[controlResults, "Transfer"], "FinalExact"];
unsafeCount = Total[Lookup[Lookup[testResults, "Transfer"],
  "UnsafeCommittedInferenceCount"]] +
  Total[Lookup[Lookup[controlResults, "Transfer"],
    "UnsafeCommittedInferenceCount"]];
positiveMQWorlds = Count[Lookup[testResults, "MembershipQuerySavings"],
  value_ /; value > 0];
aggregateMQSavings = Total[Lookup[testResults, "MembershipQuerySavings"]];
aggregateLogicalSavings = Total[Lookup[testResults,
  "LogicalInteractionCostSavings"]];
aggregateConcreteSavings = Total[Lookup[testResults,
  "ConcreteOracleCellCostSavings"]];

gatePass = structuredExact && baselineExact && controlExact &&
  unsafeCount === 0 && positiveMQWorlds >= 4 && aggregateMQSavings > 0 &&
  aggregateConcreteSavings > 0;

result = <|
  "Stage" -> "S132-K3B retrospective partial-observation concept transfer",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "K2WorldsOpenedBeforeProtocolFreeze" -> True,
  "CanonicalTCCTModified" -> False,
  "GeneratorTruthReadByLearner" -> False,
  "ProgramASTReadByLearner" -> False,
  "CompleteTransitionTableUsedForSchemaPrefilter" -> False,
  "FrozenSchemaCount" -> Length[schemas],
  "StructuredWorldCount" -> Length[testResults],
  "RandomControlCount" -> Length[controlResults],
  "AllStructuredFinalModelsExact" -> structuredExact,
  "AllBaselineFinalModelsExact" -> baselineExact,
  "AllRandomControlFinalModelsExact" -> controlExact,
  "UnsafeCommittedInferenceCount" -> unsafeCount,
  "PositiveMembershipQuerySavingsWorldCount" -> positiveMQWorlds,
  "AggregateMembershipQuerySavings" -> aggregateMQSavings,
  "AggregateLogicalInteractionCostSavings" -> aggregateLogicalSavings,
  "AggregateConcreteOracleCellCostSavings" -> aggregateConcreteSavings,
  "RetrospectivePartialObservationGatePass" -> gatePass,
  "B8ASymbolicLearnerIntegrationProven" -> False,
  "FreshWorldTransferProven" -> False,
  "OpenEndedLanguageInventionProven" -> False,
  "TestResults" -> testResults,
  "ControlResults" -> controlResults,
  "Conclusion" -> If[gatePass,
    "RETROSPECTIVE_PARTIAL_OBSERVATION_TRANSFER_GATE_PASS",
    "RETROSPECTIVE_PARTIAL_OBSERVATION_TRANSFER_GATE_NOT_PASSED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K3B_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K3B COMPLETE pass=", gatePass,
  " aggregate MQ saved=", aggregateMQSavings,
  " concrete saved=", aggregateConcreteSavings];
Exit[If[gatePass, 0, 1]];
