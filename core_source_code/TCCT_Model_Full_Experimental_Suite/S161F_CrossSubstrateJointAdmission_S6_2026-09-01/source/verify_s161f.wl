stage = DirectoryName[DirectoryName[$InputFileName]];
carrier = Range[0, 5]; semKey[s_] := StringRiffle[ToString /@ s, ","];
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
currentSet[space_, target_, inputs_] := Select[space["Current"], matches[#, target, inputs] &];
entrySet[space_, target_, inputs_] := Select[space["Entries"], matches[Last[#], target, inputs] &];
constructorClasses[entries_] := SortBy[DeleteDuplicates[First /@ entries], semKey];
decisionCount[current_, entries_] := If[Length[current] > 0, 1, 0] + Length[constructorClasses[entries]];
exactClasses[space_, target_] := constructorClasses[Select[space["Entries"], Last[#] == target &]];

truth = Import[FileNameJoin[{stage, "oracle", "sealed_exact_holdout.json"}], "RawJSON"];
python = Import[FileNameJoin[{stage, "results", "python_replication_result.json"}], "RawJSON"];
auditWorld[world_, cohort_] := Module[{base, space, row, current, entries, counts, q, y, reduced,
    causalFullCurrent, causalFullClasses, causalReducedCurrent, causalReducedClasses, pi, inv,
    conj, relSpace, relTarget, relInputs, expectedRel, checks},
  base = Association[world["BaseAtoms"]]; space = proposalSpace[base];
  row[id_] := First@Select[cohort["Rows"], #["CaseID"] == id &];
  current = currentSet[space, world["JointActiveTarget"], world["JointActiveInputs"]];
  entries = entrySet[space, world["JointActiveTarget"], world["JointActiveInputs"]];
  counts = {decisionCount[current, entries]};
  Do[q = query["Input"]; y = query["TaskOutput"];
    current = Select[current, #[[q + 1]] == y &]; entries = Select[entries, Last[#][[q + 1]] == y &];
    AppendTo[counts, decisionCount[current, entries]], {query, row["JOINT_ACTIVE"]["Queries"]}];
  reduced = DeleteCases[world["CausalInputs"], world["CausalRemovedInput"]];
  causalFullCurrent = currentSet[space, world["CausalTarget"], world["CausalInputs"]];
  causalFullClasses = constructorClasses[entrySet[space, world["CausalTarget"], world["CausalInputs"]]];
  causalReducedCurrent = currentSet[space, world["CausalTarget"], reduced];
  causalReducedClasses = constructorClasses[entrySet[space, world["CausalTarget"], reduced]];
  pi = world["RelabelPermutation"]; inv = Ordering[pi] - 1; conj[s_] := compose[pi, compose[s, inv]];
  relSpace = proposalSpace[Map[conj, base]]; relTarget = conj[world["UniqueTarget"]];
  relInputs = (pi[[# + 1]] &) /@ world["UniqueInputs"];
  expectedRel = conj[First[exactClasses[space, world["UniqueTarget"]]]];
  checks = <|
    "ConstructorCountParity" -> Length[space["Constructors"]] == world["RuntimeConstructorCount"],
    "EntryCountParity" -> Length[space["Entries"]] == world["ExplanationEntryCount"],
    "NoExtensionCurrent" -> MemberQ[space["Current"], world["NoExtensionTarget"]],
    "UniqueCurrentEliminated" -> Length[currentSet[space, world["UniqueTarget"], world["UniqueInputs"]]] == 0,
    "UniqueOneConstructor" -> Length[constructorClasses[entrySet[space, world["UniqueTarget"], world["UniqueInputs"]]]] == 1,
    "JointInitiallyMixed" -> (row["JOINT_ACTIVE"]["InitialCurrentGrammarCandidateCount"] > 0 &&
      row["JOINT_ACTIVE"]["InitialConstructorClassCount"] > 0),
    "JointStrictReduction" -> And @@ Thread[Rest[counts] < Most[counts]],
    "JointEndsOneClass" -> Last[counts] == 1,
    "CausalFullUniqueExtension" -> (Length[causalFullCurrent] == 0 && Length[causalFullClasses] == 1),
    "CausalReducedCurrentCompatible" -> Length[causalReducedCurrent] > 0,
    "CausalReducedNoPromotion" -> ! TrueQ[row["CURRENT_COMPATIBLE_CAUSAL"]["Reduced"]["Promoted"]],
    "AmbiguityMultipleExact" -> Length[exactClasses[space, world["AmbiguousTarget"]]] > 1,
    "InsufficiencyZeroExact" -> Length[exactClasses[space, world["InsufficientTarget"]]] == 0,
    "RelabelConjugacy" -> (Length[currentSet[relSpace, relTarget, relInputs]] == 0 &&
      constructorClasses[entrySet[relSpace, relTarget, relInputs]] == {expectedRel}),
    "PythonCohortPass" -> TrueQ[cohort["CohortPass"]]
  |>;
  <|"CohortID" -> world["CohortID"], "JointTrajectory" -> counts,
    "CausalReducedCounts" -> {Length[causalReducedCurrent], Length[causalReducedClasses]},
    "Checks" -> checks, "Pass" -> And @@ Values[checks]|>
];
audits = MapThread[auditWorld, {truth["Worlds"], python["Cohorts"]}];
checks = <|"CarrierSizeSix" -> truth["CarrierSize"] == 6,
  "FiveCohortsAudited" -> Length[audits] == 5,
  "FiveOfFiveIndependentPass" -> And @@ audits[[All, "Pass"]],
  "ThirtyFiveCases" -> Total[Length[#Rows] & /@ python["Cohorts"]] == 35,
  "PythonReplicationPass" -> TrueQ[python["PythonReplicationPass"]]|>;
out = <|"Stage" -> "S161-F", "Verifier" -> "NATIVE_WOLFRAM_S6_MULTI_COHORT_RECONSTRUCTION",
  "CohortAudits" -> audits, "Checks" -> checks, "WolframIndependentPass" -> And @@ Values[checks],
  "Conclusion" -> If[And @@ Values[checks], "S161F_WOLFRAM_CROSS_SUBSTRATE_REPLICATION_PASS",
    "S161F_WOLFRAM_CROSS_SUBSTRATE_REPLICATION_FAIL"]|>;
Export[FileNameJoin[{stage, "results", "wolfram_replication_audit.json"}], out, "RawJSON"];
Print[ExportString[<|"Conclusion" -> out["Conclusion"],
  "JointTrajectories" -> (#["JointTrajectory"] & /@ audits)|>, "RawJSON"]];
If[! TrueQ[out["WolframIndependentPass"]], Exit[1]];
