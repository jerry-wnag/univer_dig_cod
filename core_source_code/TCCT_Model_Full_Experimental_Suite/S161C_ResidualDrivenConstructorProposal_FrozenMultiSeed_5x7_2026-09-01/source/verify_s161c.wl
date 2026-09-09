stage = DirectoryName[DirectoryName[$InputFileName]];
carrier = Range[0, 4]; semKey[s_] := StringRiffle[ToString /@ s, ","];
compose[outer_, inner_] := outer[[inner + 1]];
evalWord[word_, atoms_] := Fold[compose[Lookup[atoms, #2], #1] &, carrier, word];
enumerate[atoms_, max_] := Module[{words, rows, groups},
  words = Join[{{}}, Flatten[Table[Tuples[Sort[Keys[atoms]], {n}], {n, 1, max}], 1]];
  rows = (<|"Word" -> #, "Sem" -> evalWord[#, atoms]|> &) /@ words;
  groups = GatherBy[rows, semKey[#Sem] &];
  (<|"Sem" -> First[#]["Sem"], "Words" -> (#Word & /@ #)|> &) /@ groups];
proposalSpace[base_] := Module[{current, c0, constructors, entries = {}, extended},
  current = enumerate[base, 2]; c0 = #Sem & /@ current;
  constructors = #Sem & /@ Select[current, Min[Length /@ #Words] == 2 &];
  Do[extended = enumerate[Append[base, "R" -> constructor], 2];
    Do[If[! MemberQ[c0, row["Sem"]] && AnyTrue[row["Words"], MemberQ[#, "R"] &],
      AppendTo[entries, {constructor, row["Sem"]}]], {row, extended}], {constructor, constructors}];
  <|"Current" -> c0, "Constructors" -> SortBy[DeleteDuplicates[constructors], semKey],
    "Entries" -> SortBy[DeleteDuplicates[entries], semKey[First[#]] <> ":" <> semKey[Last[#]] &]|>];
matches[sem_, target_, inputs_] := And @@ ((sem[[# + 1]] == target[[# + 1]]) & /@ inputs);
classes[space_, target_, inputs_] := SortBy[DeleteDuplicates[First /@
  Select[space["Entries"], matches[Last[#], target, inputs] &]], semKey];
exactClasses[space_, target_] := SortBy[DeleteDuplicates[First /@
  Select[space["Entries"], Last[#] == target &]], semKey];
currentMatches[space_, target_, inputs_] := Count[space["Current"], s_ /; matches[s, target, inputs]];

truth = Import[FileNameJoin[{stage, "oracle", "sealed_exact_holdout.json"}], "RawJSON"];
python = Import[FileNameJoin[{stage, "results", "python_replication_result.json"}], "RawJSON"];
auditWorld[world_, cohort_] := Module[{base, space, row, activeEntries, activeCounts, reduced, pi, inv,
    conj, relSpace, relTarget, relInputs, expectedRel, checks},
  base = Association[world["BaseAtoms"]]; space = proposalSpace[base];
  row[id_] := First@Select[cohort["Rows"], #["CaseID"] == id &];
  activeEntries = Select[space["Entries"], matches[Last[#], world["ActiveTarget"], world["ActiveInputs"]] &];
  activeCounts = {Length[DeleteDuplicates[First /@ activeEntries]]};
  Do[activeEntries = Select[activeEntries, Last[#][[q["Input"] + 1]] == q["TaskOutput"] &];
    AppendTo[activeCounts, Length[DeleteDuplicates[First /@ activeEntries]]], {q, row["ACTIVE"]["Queries"]}];
  reduced = DeleteCases[world["CausalInputs"], world["CausalRemovedInput"]];
  pi = world["RelabelPermutation"]; inv = Ordering[pi] - 1; conj[s_] := compose[pi, compose[s, inv]];
  relSpace = proposalSpace[Map[conj, base]]; relTarget = conj[world["UniqueTarget"]];
  relInputs = (pi[[# + 1]] &) /@ world["UniqueInputs"];
  expectedRel = conj[First[exactClasses[space, world["UniqueTarget"]]]];
  checks = <|
    "OrbitFresh" -> ! TrueQ[world["SelectedOrbitWasHistorical"]],
    "ConstructorCountParity" -> Length[space["Constructors"]] == world["RuntimeConstructorCount"],
    "EntryCountParity" -> Length[space["Entries"]] == world["ExplanationEntryCount"],
    "NoExtensionCurrent" -> MemberQ[space["Current"], world["NoExtensionTarget"]],
    "UniqueOneClass" -> (currentMatches[space, world["UniqueTarget"], world["UniqueInputs"]] == 0 &&
      Length[classes[space, world["UniqueTarget"], world["UniqueInputs"]]] == 1 &&
      Length[exactClasses[space, world["UniqueTarget"]]] == 1),
    "ActiveStartsAtLeastThree" -> First[activeCounts] >= 3,
    "ActiveStrictReduction" -> And @@ Thread[Rest[activeCounts] < Most[activeCounts]],
    "ActiveEndsUnique" -> (Last[activeCounts] == 1 && Length[exactClasses[space, world["ActiveTarget"]]] == 1),
    "AmbiguousMultipleExact" -> Length[exactClasses[space, world["AmbiguousTarget"]]] > 1,
    "InsufficientZeroExact" -> Length[exactClasses[space, world["InsufficientTarget"]]] == 0,
    "ResidualCausalShift" -> classes[space, world["CausalTarget"], world["CausalInputs"]] =!=
      classes[space, world["CausalTarget"], reduced],
    "RelabelConjugacy" -> (classes[relSpace, relTarget, relInputs] == {expectedRel} &&
      exactClasses[relSpace, relTarget] == {expectedRel}),
    "PythonCohortPass" -> TrueQ[cohort["CohortPass"]]
  |>;
  <|"CohortID" -> world["CohortID"], "ActiveTrajectory" -> activeCounts,
    "Checks" -> checks, "Pass" -> And @@ Values[checks]|>
];
audits = MapThread[auditWorld, {truth["Worlds"], python["Cohorts"]}];
checks = <|"FiveCohortsAudited" -> Length[audits] == 5,
  "AllCohortsIndependentPass" -> And @@ audits[[All, "Pass"]],
  "ThirtyFivePythonCases" -> Total[Length[#Rows] & /@ python["Cohorts"]] == 35,
  "PythonReplicationPass" -> TrueQ[python["PythonReplicationPass"]]|>;
out = <|"Stage" -> "S161-C", "Verifier" -> "NATIVE_WOLFRAM_MULTI_COHORT_RECONSTRUCTION",
  "CohortAudits" -> audits, "Checks" -> checks, "WolframIndependentPass" -> And @@ Values[checks],
  "Conclusion" -> If[And @@ Values[checks], "S161C_WOLFRAM_MULTI_SEED_REPLICATION_PASS",
    "S161C_WOLFRAM_MULTI_SEED_REPLICATION_FAIL"]|>;
Export[FileNameJoin[{stage, "results", "wolfram_replication_audit.json"}], out, "RawJSON"];
Print[ExportString[<|"Conclusion" -> out["Conclusion"],
  "ActiveTrajectories" -> (#["ActiveTrajectory"] & /@ audits)|>, "RawJSON"]];
If[! TrueQ[out["WolframIndependentPass"]], Exit[1]];
