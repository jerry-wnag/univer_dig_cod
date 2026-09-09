root = DirectoryName[DirectoryName[$InputFileName]];
work = DirectoryName[root];
frozenSourcePath = FileNameJoin[{work, "S143C_ActiveOperatorDisambiguation_DEV_R0_2026-08-30",
  "source", "run_wolfram_active_trajectory_audit.wl"}];
frozenSource = Import[frozenSourcePath, "Text"];
definitionStart = First[First[StringPosition[frozenSource, "key[x_] :="]]];
definitionEnd = First[First[StringPosition[frozenSource, "exactCandidates ="]]] - 1;
ToExpression[StringTake[frozenSource, {definitionStart, definitionEnd}]];

caseData = Import[FileNameJoin[{root, "input", "five_diagnostic_cases.json"}], "RawJSON"]["Cases"];
pool = Import[FileNameJoin[{root, "input", "reference_semantic_domain.json"}], "RawJSON"]["Applications"];
randomObservations = Import[FileNameJoin[{root, "input", "random_behavior_control.json"}], "RawJSON"]["Observations"];
py = Import[FileNameJoin[{root, "results", "python_grammar_diagnostics_result.json"}], "RawJSON"];

inputKey[app_Association] := key[KeyTake[app,
  {"CurrentPartition", "OtherPartition", "DecisionPartition"}]];

diagnoseCase[caseID_String, observations_List] := Module[
  {groups, contradictionGroups, exact, semanticVectors, semanticCount, status, frozen},
  groups = GatherBy[observations, inputKey];
  contradictionGroups = Select[groups, Length[DeleteDuplicates[TrueQ /@ Lookup[#, "Output"]]] > 1 &];
  If[Length[contradictionGroups] > 0,
    Return[<|"CaseID" -> caseID, "Status" -> "INCONSISTENT_OR_NOISY_OBSERVATIONS",
      "ObservationCount" -> Length[observations], "UniqueInputCount" -> Length[groups],
      "ContradictionCount" -> Length[contradictionGroups], "GrammarSearchExecuted" -> False,
      "ExactCandidateCount" -> Null, "SemanticClassCount" -> Null, "Frozen" -> False|>]
  ];
  exact = Select[candidates, Function[candidate,
    AllTrue[observations, candidateValue[candidate, #] === TrueQ[# ["Output"]] &]]];
  If[Length[exact] == 0,
    status = "LANGUAGE_INSUFFICIENT"; semanticCount = 0; frozen = False,
    semanticVectors = DeleteDuplicates[Table[candidateValue[candidate, #] & /@ pool,
      {candidate, exact}]];
    semanticCount = Length[semanticVectors];
    If[semanticCount == 1, status = "EXACT_IN_LANGUAGE"; frozen = True,
      status = "AMBIGUOUS_IN_LANGUAGE"; frozen = False]
  ];
  <|"CaseID" -> caseID, "Status" -> status, "ObservationCount" -> Length[observations],
    "UniqueInputCount" -> Length[groups], "ContradictionCount" -> 0,
    "GrammarSearchExecuted" -> True, "GrammarCandidateCount" -> Length[candidates],
    "ExactCandidateCount" -> Length[exact], "SemanticClassCount" -> semanticCount,
    "EliminatedCandidateCount" -> Length[candidates] - Length[exact], "Frozen" -> frozen|>
];

rows = diagnoseCase[#["CaseID"], #["Observations"]] & /@ caseData;
randomRow = diagnoseCase["S144A_RANDOM_CONTROL", randomObservations];
pyRows = AssociationThread[Lookup[py["CaseRows"], "CaseID"], py["CaseRows"]];
statusParity = AllTrue[rows, #["Status"] === pyRows[#["CaseID"]]["Status"] &];
candidateCountParity = AllTrue[rows, #["ExactCandidateCount"] ===
  pyRows[#["CaseID"]]["ExactCandidateCount"] &];
semanticCountParity = AllTrue[rows, #["SemanticClassCount"] ===
  pyRows[#["CaseID"]]["SemanticClassCount"] &];

checks = <|
  "GrammarCandidateCountParity" -> (Length[candidates] === py["GrammarCandidateCount"]),
  "FiveStatusParity" -> statusParity, "ExactCandidateCountParity" -> candidateCountParity,
  "SemanticClassCountParity" -> semanticCountParity,
  "ExpectedStatusSequence" -> (Lookup[rows, "Status"] === {"EXACT_IN_LANGUAGE",
    "AMBIGUOUS_IN_LANGUAGE", "LANGUAGE_INSUFFICIENT", "LANGUAGE_INSUFFICIENT",
    "INCONSISTENT_OR_NOISY_OBSERVATIONS"}),
  "TwoCompleteGrammarEliminations" -> (rows[[3]]["EliminatedCandidateCount"] === Length[candidates]
    && rows[[4]]["EliminatedCandidateCount"] === Length[candidates]),
  "InconsistencyDetectedBeforeSearch" -> (rows[[5]]["GrammarSearchExecuted"] === False),
  "RandomBehaviorLanguageInsufficient" -> (randomRow["Status"] === "LANGUAGE_INSUFFICIENT"
    && randomRow["ExactCandidateCount"] === 0),
  "PythonDevelopmentPassObserved" -> TrueQ[py["PythonDevelopmentPass"]]
|>;
pass = AllTrue[Values[checks], TrueQ];
result = <|"Stage" -> py["Stage"], "GrammarCandidateCount" -> Length[candidates],
  "CaseRows" -> rows, "RandomBehaviorControl" -> randomRow, "Checks" -> checks,
  "WolframDevelopmentAuditPass" -> pass,
  "Conclusion" -> If[pass, "WOLFRAM_GRAMMAR_INSUFFICIENCY_DIAGNOSTIC_PARITY_PASS",
    "WOLFRAM_GRAMMAR_INSUFFICIENCY_DIAGNOSTIC_PARITY_FAIL"]|>;
Export[FileNameJoin[{root, "results", "wolfram_grammar_diagnostics_audit.json"}], result, "RawJSON"];
Print[ExportString[<|"Pass" -> pass, "Statuses" -> Lookup[rows, "Status"],
  "ExactCandidates" -> Lookup[rows, "ExactCandidateCount"],
  "SemanticClasses" -> Lookup[rows, "SemanticClassCount"],
  "RandomStatus" -> randomRow["Status"]|>, "RawJSON"]];
If[pass, Exit[0], Exit[1]];
