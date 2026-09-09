root = DirectoryName[DirectoryName[$InputFileName]];
work = DirectoryName[root];
s144d = FileNameJoin[{work, "S144D_MultiSeedFreshLanguageExtension_5x5_R0_2026-08-30"}];
cohortData = Import[FileNameJoin[{s144d, "input", "five_frozen_cohorts.json"}], "RawJSON"]["Cohorts"];
sealedData = Import[FileNameJoin[{s144d, "oracle", "sealed_holdouts_15.json"}], "RawJSON"]["Cohorts"];
privateData = Import[FileNameJoin[{s144d, "audit", "private_constructor_audit.json"}], "RawJSON"]["CohortAudits"];
historical = Import[FileNameJoin[{s144d, "results", "python_replication_result.json"}], "RawJSON"];
pyRepair = Import[FileNameJoin[{root, "results", "python_repair_audit.json"}], "RawJSON"];
sealedByID = AssociationThread[Lookup[sealedData, "CohortID"], sealedData];
privateByID = AssociationThread[Lookup[privateData, "CohortID"], privateData];
historicalByID = AssociationThread[Lookup[historical["CohortResults"], "CohortID"],
  historical["CohortResults"]];

truthValue[table_Integer, sig_Integer] := TrueQ[BitGet[table, sig] == 1];
signatureFor[values_List, triple_List] := Sum[
  If[TrueQ[values[[triple[[bit]]]]], 2^(bit - 1), 0], {bit, 1, 3}];
canonicalPartition[value_List] := Sort[Sort /@ value];
meetPartition[left_List, right_List] := Sort[Select[Flatten[
  Table[Sort[Intersection[x, y]], {x, left}, {y, right}], 1], Length[#] > 0 &]];
refinesPartition[left_List, right_List] := AllTrue[left,
  Function[block, AnyTrue[right, SubsetQ[#, block] &]]];
termValue[term_Association, app_Association] := If[term["Op"] === "Var",
  canonicalPartition[app[term["Name"]]], meetPartition @@ (termValue[#, app] & /@ term["Args"])] ;
atomValue[atom_Association, app_Association] := Module[{left, right},
  {left, right} = termValue[#, app] & /@ atom["Args"];
  Which[atom["Name"] === "Equal", left === right,
    atom["Name"] === "PartitionRefines", refinesPartition[left, right],
    atom["Name"] === "StrictPartitionRefines", left =!= right && refinesPartition[left, right]]
];
signalValues[definitions_List, app_Association] := atomValue[#, app] & /@ definitions;

transformPartition[value_List, mapping_Association, reverseBlocks_, reverseItems_] := Module[{blocks},
  blocks = (Lookup[mapping, #] & /@ #) & /@ value;
  If[TrueQ[reverseItems], blocks = Reverse /@ blocks];
  If[TrueQ[reverseBlocks], blocks = Reverse[blocks]];
  blocks
];
transformApp[app_Association, mapping_Association, reverseBlocks_, reverseItems_] :=
  Join[app, Association[Table[field -> transformPartition[app[field], mapping,
    reverseBlocks, reverseItems], {field,
      {"CurrentPartition", "OtherPartition", "DecisionPartition"}}]]];

identity = <|"0" -> "0", "1" -> "1", "2" -> "2", "3" -> "3"|>;
mapA = <|"0" -> "2", "1" -> "0", "2" -> "3", "3" -> "1"|>;
mapB = <|"0" -> "3", "1" -> "2", "2" -> "1", "3" -> "0"|>;
transforms = {
  {identity, True, False, "REVERSE_BLOCKS"},
  {identity, False, True, "REVERSE_WITHIN_BLOCKS"},
  {identity, True, True, "REVERSE_BOTH"},
  {mapA, False, False, "ELEMENT_RELABEL"},
  {mapB, True, True, "RELABEL_AND_REVERSE"}
};

holdoutRows = {}; trainingRows = {}; adversarialRows = {};
Do[
  cohortID = cohort["CohortID"];
  audit = privateByID[cohortID];
  definitions = Lookup[audit["SignalDefinitions"], cohort["SignalIDs"]];
  historicalCohort = historicalByID[cohortID];
  proposalByID = AssociationThread[Lookup[historicalCohort["CaseRows"], "CaseID"],
    Lookup[historicalCohort["CaseRows"], "SelectedProposal"]];
  oldHoldoutByID = AssociationThread[Lookup[historicalCohort["SealedHoldoutRows"], "CaseID"],
    historicalCohort["SealedHoldoutRows"]];
  Do[
    holdout = sealedByID[cohortID]["Holdouts"][[caseIndex]];
    family = audit["StructuredFamilies"][[caseIndex]];
    proposal = proposalByID[holdout["CaseID"]];
    hiddenTriple = family["Triple"] + 1;
    selectedTriple = proposal["SignalIndices"] + 1;
    repairedExact = Count[holdout["Applications"], app_ /; Module[{values, oracle, prediction},
      values = signalValues[definitions, app];
      oracle = truthValue[family["TruthTable"], signatureFor[values, hiddenTriple]];
      prediction = truthValue[proposal["TruthTable"], signatureFor[values, selectedTriple]];
      oracle === prediction]];
    AppendTo[holdoutRows, <|"CohortID" -> cohortID, "CaseID" -> holdout["CaseID"],
      "OriginalExactApplicationCount" -> oldHoldoutByID[holdout["CaseID"]]["ExactApplicationCount"],
      "ApplicationCount" -> Length[holdout["Applications"]],
      "RepairedExactApplicationCount" -> repairedExact,
      "RepairedExact" -> (repairedExact == Length[holdout["Applications"]])|>],
    {caseIndex, 1, 3}];
  trainingUnchanged = Count[cohort["DomainRows"], app_ /;
    signalValues[definitions, app] === app["SignalValues"]];
  AppendTo[trainingRows, <|"CohortID" -> cohortID,
    "ApplicationCount" -> Length[cohort["DomainRows"]],
    "UnchangedSignalApplicationCount" -> trainingUnchanged,
    "AllTrainingSignalsUnchanged" -> (trainingUnchanged == Length[cohort["DomainRows"]])|>];
  sample = Take[cohort["DomainRows"], 128];
  Do[
    invariant = Count[sample, app_ /; signalValues[definitions,
      transformApp[app, transform[[1]], transform[[2]], transform[[3]]]] ===
        signalValues[definitions, app]];
    idempotent = Count[sample, app_ /; AllTrue[
      {"CurrentPartition", "OtherPartition", "DecisionPartition"},
      canonicalPartition[canonicalPartition[app[#]]] === canonicalPartition[app[#]] &]];
    AppendTo[adversarialRows, <|"CohortID" -> cohortID, "Transformation" -> transform[[4]],
      "SampleCount" -> Length[sample], "InvariantCount" -> invariant,
      "IdempotentCount" -> idempotent,
      "Pass" -> (invariant == Length[sample] && idempotent == Length[sample])|>],
    {transform, transforms}],
  {cohort, cohortData}];

checks = <|
  "HistoricalS144DStillFails" -> !TrueQ[historical["PythonReplicationPass"]],
  "All15HistoricalHoldoutsExactAfterRepair" -> (Length[holdoutRows] == 15 &&
    AllTrue[holdoutRows, TrueQ[# ["RepairedExact"]] &]),
  "ExactlyFiveOriginallyFailedAndRecovered" -> (Count[holdoutRows,
    row_ /; row["OriginalExactApplicationCount"] < row["ApplicationCount"] &&
      TrueQ[row["RepairedExact"]]] == 5),
  "AllFiveTrainingDomainsUnchanged" -> AllTrue[trainingRows,
    TrueQ[# ["AllTrainingSignalsUnchanged"]] &],
  "All25AdversarialAuditsPass" -> (Length[adversarialRows] == 25 &&
    AllTrue[adversarialRows, TrueQ[# ["Pass"]] &]),
  "PythonRepairPassObserved" -> TrueQ[pyRepair["PythonRepairAuditPass"]]
|>;
pass = AllTrue[Values[checks], TrueQ];
result = <|"Stage" -> pyRepair["Stage"], "HistoricalHoldoutRows" -> holdoutRows,
  "TrainingDomainRows" -> trainingRows, "AdversarialRows" -> adversarialRows,
  "Checks" -> checks, "WolframRepairAuditPass" -> pass,
  "Conclusion" -> If[pass, "WOLFRAM_CANONICAL_PARTITION_REPAIR_PARITY_PASS",
    "WOLFRAM_CANONICAL_PARTITION_REPAIR_PARITY_FAIL"]|>;
Export[FileNameJoin[{root, "results", "wolfram_repair_audit.json"}], result, "RawJSON"];
Print[ExportString[<|"Pass" -> pass,
  "OriginalHoldoutExact" -> Count[holdoutRows, row_ /;
    row["OriginalExactApplicationCount"] == row["ApplicationCount"]],
  "RepairedHoldoutExact" -> Count[holdoutRows, row_ /; TrueQ[row["RepairedExact"]]],
  "TrainingCohortsUnchanged" -> Count[trainingRows, row_ /; TrueQ[row["AllTrainingSignalsUnchanged"]]],
  "AdversarialAudits" -> Count[adversarialRows, row_ /; TrueQ[row["Pass"]]]|>, "RawJSON"]];
If[pass, Exit[0], Exit[1]];
