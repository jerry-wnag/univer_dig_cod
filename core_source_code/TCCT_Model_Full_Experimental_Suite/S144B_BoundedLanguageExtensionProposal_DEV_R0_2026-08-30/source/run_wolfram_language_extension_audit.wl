root = DirectoryName[DirectoryName[$InputFileName]];
work = DirectoryName[root];
frozenSourcePath = FileNameJoin[{work, "S143C_ActiveOperatorDisambiguation_DEV_R0_2026-08-30",
  "source", "run_wolfram_active_trajectory_audit.wl"}];
frozenSource = Import[frozenSourcePath, "Text"];
definitionStart = First[First[StringPosition[frozenSource, "key[x_] :="]]];
definitionEnd = First[First[StringPosition[frozenSource, "exactCandidates ="]]] - 1;
ToExpression[StringTake[frozenSource, {definitionStart, definitionEnd}]];

domain = Import[FileNameJoin[{root, "input", "learner_signal_domain.json"}], "RawJSON"];
domainRows = domain["Rows"];
signalIDs = domain["SignalIDs"];
domainByID = AssociationThread[Lookup[domainRows, "ApplicationID"], domainRows];
caseData = Import[FileNameJoin[{root, "input", "five_extension_cases.json"}], "RawJSON"]["Cases"];
holdouts = Import[FileNameJoin[{root, "input", "sealed_relabeling_holdouts.json"}], "RawJSON"]["Holdouts"];
certificates = Import[FileNameJoin[{root, "results", "current_grammar_elimination_certificates.json"}], "RawJSON"];
py = Import[FileNameJoin[{root, "results", "python_language_extension_result.json"}], "RawJSON"];

varTruth[index_Integer] := Sum[BitShiftLeft[BitGet[signature, index], signature], {signature, 0, 7}];
costs = ConstantArray[Infinity, 256];
Do[costs[[varTruth[index] + 1]] = 0, {index, 0, 2}];
Do[
  Do[
    If[NumberQ[costs[[left + 1]]] && NumberQ[costs[[right + 1]]] &&
       costs[[left + 1]] + costs[[right + 1]] + 1 == cost,
      value = BitAnd[BitNot[BitAnd[left, right]], 255];
      If[!NumberQ[costs[[value + 1]]], costs[[value + 1]] = cost]
    ],
    {left, 0, 255}, {right, 0, 255}],
  {cost, 1, 14}];

signatureFor[row_Association, triple_List] := Sum[
  If[TrueQ[row["SignalValues"][[triple[[bit]]]]], 2^(bit - 1), 0], {bit, 1, 3}];
truthValue[table_Integer, sig_Integer] := TrueQ[BitGet[table, sig] == 1];
rawInputKey[row_Association] := key[KeyTake[row,
  {"CurrentPartition", "OtherPartition", "DecisionPartition"}]];

searchCase[case_Association] := Module[
  {observations, pairs, rawGroups, contradictions, taskCount, rawBits, triples,
   exactCount = 0, semanticVectors = {}, bestBits = Infinity, triple, grouped,
   conflict, constraints, table, compatible, vector, descriptionBits, status},
  observations = case["Observations"];
  pairs = {domainByID[# ["ApplicationID"]], TrueQ[# ["Output"]]} & /@ observations;
  rawGroups = GatherBy[pairs, rawInputKey[First[#]] &];
  contradictions = Select[rawGroups, Length[DeleteDuplicates[Last /@ #]] > 1 &];
  If[Length[contradictions] > 0,
    Return[<|"CaseID" -> case["CaseID"], "Status" -> "INCONSISTENT_OBSERVATIONS",
      "ExactMetaProgramCount" -> Null, "SemanticClassCount" -> Null,
      "BestExactDescriptionLengthBits" -> Null|>]
  ];
  taskCount = Length[DeleteDuplicates[Lookup[First /@ pairs, "FormationTaskID"]]];
  rawBits = Length[observations];
  triples = Subsets[Range[Length[signalIDs]], {3}];
  Do[
    grouped = GatherBy[pairs, signatureFor[First[#], triple] &];
    conflict = AnyTrue[grouped, Length[DeleteDuplicates[Last /@ #]] > 1 &];
    If[!conflict,
      constraints = Association[Table[ToString[signatureFor[First[group[[1]]], triple]] ->
        Last[group[[1]]], {group, grouped}]];
      compatible = Select[Range[0, 255], Function[t,
        AllTrue[Normal[constraints], truthValue[t, ToExpression[First[#]]] === Last[#] &]]];
      Do[
        exactCount++;
        vector = truthValue[table, signatureFor[#, triple]] & /@ domainRows;
        AppendTo[semanticVectors, vector];
        descriptionBits = 2 + 12 + (4 costs[[table + 1]] + 3) + 8 taskCount;
        bestBits = Min[bestBits, descriptionBits],
        {table, compatible}]
    ],
    {triple, triples}];
  semanticCount = Length[DeleteDuplicates[semanticVectors]];
  status = Which[
    exactCount == 0, "NO_COMPRESSIVE_EXTENSION",
    semanticCount > 1, "MULTIPLE_EXTENSIONS_AMBIGUOUS",
    bestBits >= rawBits, "NO_COMPRESSIVE_EXTENSION",
    True, "EXACT_EXTENSION_PROPOSED"];
  <|"CaseID" -> case["CaseID"], "Status" -> status,
    "ExactMetaProgramCount" -> exactCount, "SemanticClassCount" -> semanticCount,
    "BestExactDescriptionLengthBits" -> If[NumberQ[bestBits], bestBits, Null]|>
];

rows = searchCase /@ caseData;
pyRows = AssociationThread[Lookup[py["CaseRows"], "CaseID"], py["CaseRows"]];

currentGrammarAudit[case_Association] := Module[{caseID, observations, cert, exact},
  caseID = case["CaseID"];
  observations = case["Observations"];
  cert = certificates[caseID];
  exact = Select[candidates, Function[candidate,
    AllTrue[observations, candidateValue[candidate,
      domainByID[# ["ApplicationID"]]] === TrueQ[# ["Output"]] &]]];
  <|"CaseID" -> caseID, "ExactCandidateCount" -> Length[exact],
    "CertificateEntryCount" -> Length[cert],
    "CompleteElimination" -> (Length[exact] == 0 && Length[cert] == Length[candidates])|>
];

proposalExactAndMinimal[case_Association, wolframRow_Association] := Module[
  {pyRow, proposal, triple, table, observations, exact, bits},
  pyRow = pyRows[case["CaseID"]];
  proposal = pyRow["SelectedProposal"];
  If[!AssociationQ[proposal], Return[True]];
  triple = (proposal["SignalIndices"] + 1);
  table = proposal["TruthTable"];
  observations = case["Observations"];
  exact = AllTrue[observations, Function[observation,
    truthValue[table, signatureFor[domainByID[observation["ApplicationID"]], triple]] ===
      TrueQ[observation["Output"]]]];
  bits = proposal["DescriptionLengthBits"];
  exact && bits == wolframRow["BestExactDescriptionLengthBits"] &&
    costs[[table + 1]] == proposal["NANDCount"]
];

holdoutRows = Table[
  pyRow = pyRows[holdout["CaseID"]];
  proposal = pyRow["SelectedProposal"];
  If[!AssociationQ[proposal],
    <|"CaseID" -> holdout["CaseID"], "Evaluated" -> False, "Exact" -> False|>,
    triple = proposal["SignalIndices"] + 1;
    table = proposal["TruthTable"];
    exactCount = Count[holdout["Applications"], app_ /;
      truthValue[table, signatureFor[app, triple]] === TrueQ[app["Output"]]];
    <|"CaseID" -> holdout["CaseID"], "Evaluated" -> True,
      "ApplicationCount" -> Length[holdout["Applications"]],
      "ExactApplicationCount" -> exactCount,
      "Exact" -> (exactCount == Length[holdout["Applications"]])|>
  ],
  {holdout, holdouts}];

currentGrammarRows = currentGrammarAudit /@ caseData;

checks = <|
  "NANDMetaLanguageCoversAll256Functions" -> (Count[costs, _?NumberQ] == 256),
  "FiveStatusParity" -> AllTrue[rows, # ["Status"] === pyRows[# ["CaseID"]]["Status"] &],
  "ExactMetaProgramCountParity" -> AllTrue[rows,
    # ["ExactMetaProgramCount"] === pyRows[# ["CaseID"]]["ExactMetaProgramCount"] &],
  "SemanticClassCountParity" -> AllTrue[rows,
    # ["SemanticClassCount"] === pyRows[# ["CaseID"]]["SemanticClassCount"] &],
  "BestDescriptionLengthParity" -> AllTrue[rows,
    # ["BestExactDescriptionLengthBits"] === pyRows[# ["CaseID"]]["BestExactDescriptionLengthBits"] &],
  "AllCurrentGrammarCandidatesIndependentlyEliminated" -> AllTrue[currentGrammarRows,
    TrueQ[# ["CompleteElimination"]] &],
  "EveryPythonProposalExactAndMinimumMDL" -> And @@ MapThread[proposalExactAndMinimal, {caseData, rows}],
  "TwoHoldoutsExact" -> (Length[holdoutRows] == 2 && AllTrue[holdoutRows, TrueQ[# ["Exact"]] &]),
  "ExpectedStatusSequence" -> (Lookup[rows, "Status"] === {
    "EXACT_EXTENSION_PROPOSED", "EXACT_EXTENSION_PROPOSED",
    "MULTIPLE_EXTENSIONS_AMBIGUOUS", "NO_COMPRESSIVE_EXTENSION",
    "NO_COMPRESSIVE_EXTENSION"}),
  "PythonDevelopmentPassObserved" -> TrueQ[py["PythonDevelopmentPass"]]
|>;
pass = AllTrue[Values[checks], TrueQ];
result = <|"Stage" -> py["Stage"], "CaseRows" -> rows,
  "CurrentGrammarRows" -> currentGrammarRows, "HoldoutRows" -> holdoutRows, "Checks" -> checks,
  "WolframDevelopmentAuditPass" -> pass,
  "Conclusion" -> If[pass, "WOLFRAM_BOUNDED_LANGUAGE_EXTENSION_PARITY_PASS",
    "WOLFRAM_BOUNDED_LANGUAGE_EXTENSION_PARITY_FAIL"]|>;
Export[FileNameJoin[{root, "results", "wolfram_language_extension_audit.json"}], result, "RawJSON"];
Print[ExportString[<|"Pass" -> pass, "Statuses" -> Lookup[rows, "Status"],
  "MetaExact" -> Lookup[rows, "ExactMetaProgramCount"],
  "SemanticClasses" -> Lookup[rows, "SemanticClassCount"],
  "HoldoutExact" -> Lookup[holdoutRows, "Exact"]|>, "RawJSON"]];
If[pass, Exit[0], Exit[1]];
