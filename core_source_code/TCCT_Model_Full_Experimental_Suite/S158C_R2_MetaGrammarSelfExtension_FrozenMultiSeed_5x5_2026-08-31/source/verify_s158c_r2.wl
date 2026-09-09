ClearAll["Global`*"];
stage = DirectoryName[DirectoryName[$InputFileName]];
data = Import[FileNameJoin[{stage, "results", "python_multiseed_result.json"}], "RawJSON"];
holdoutCohorts = Import[FileNameJoin[{stage, "oracle", "sealed_exact_holdout.json"}], "RawJSON"]["Cohorts"];
oracleCohorts = Import[FileNameJoin[{stage, "oracle", "sealed_query_oracles.json"}], "RawJSON"]["Cohorts"];

domain = Tuples[Range[0, 2], 2];
a = domain[[All, 1]]; b = domain[[All, 2]];
closure = DeleteDuplicates[{a, b}];
changed = True;
While[changed,
 old = closure;
 closure = DeleteDuplicates[Join[closure,
   Flatten[Table[MapThread[Min, {x, y}], {x, old}, {y, old}], 1],
   Flatten[Table[MapThread[Max, {x, y}], {x, old}, {y, old}], 1]]];
 changed = Length[closure] =!= Length[old]];
orderedG0 = First[holdoutCohorts]["OrderedG0Semantics"];
apply[sem_, swap_, perm_] := Module[{pair, sourcePair, position},
 Table[
  pair = domain[[domainIndex]];
  sourcePair = If[TrueQ[swap], Reverse[pair], pair];
  position = First@FirstPosition[domain, sourcePair];
  perm[[sem[[position]] + 1]],
  {domainIndex, Length[domain]}]];
rawRules = Flatten[Table[
  action = Flatten[Table[apply[orderedG0[[g0Index]], swapFlag, permutation],
    {g0Index, Length[orderedG0]}]];
  <|"Swap" -> swapFlag, "Perm" -> permutation, "Action" -> action|>,
  {swapFlag, {False, True}}, {permutation, Permutations[Range[0, 2]]}], 1];
expressiveQ[rule_] := ! And @@ Table[
  MemberQ[closure, apply[orderedG0[[g0Index]], rule["Swap"], rule["Perm"]]],
  {g0Index, Length[orderedG0]}];
rules = DeleteDuplicatesBy[Select[rawRules, expressiveQ], #["Action"] &];
qid[g0Index_, domainIndex_] := "Q" <> IntegerString[g0Index, 10, 2] <> "_" <>
  IntegerString[domainIndex, 10, 2];
strictlyDecreasingQ[sizes_] := And @@ Table[sizes[[k + 1]] < sizes[[k]],
  {k, Length[sizes] - 1}];

auditCohort[cohortData_] := Module[
 {cohortID, holdout, oracle, formation, reuse, ambiguous, unavailable,
  freshAction, historicalActions, freshRule, candidateOutput, replay,
  formationSizes, ambiguitySizes, unavailableActiveSizes, formationOracle,
  noExtensionOracle, fullCompatibleRules, fullCertificate, evalAst, reuseAst, checks},
 cohortID = cohortData["CohortID"];
 holdout = SelectFirst[holdoutCohorts, #["CohortID"] === cohortID &];
 oracle = SelectFirst[oracleCohorts, #["CohortID"] === cohortID &];
 formation = SelectFirst[cohortData["CaseRows"], StringEndsQ[#["CaseID"], "_FORM_RULE"] &];
 reuse = SelectFirst[cohortData["CaseRows"], StringEndsQ[#["CaseID"], "_REUSE_NESTED"] &];
 ambiguous = SelectFirst[cohortData["CaseRows"], StringEndsQ[#["CaseID"], "_AMBIGUOUS"] &];
 unavailable = SelectFirst[cohortData["CaseRows"], StringEndsQ[#["CaseID"], "_NO_EXTENSION"] &];
 freshAction = ToExpression /@ Characters[holdout["FreshTargetRuleActionSignature"]];
 historicalActions = (ToExpression /@ Characters[#]) & /@
   holdout["HistoricalTargetRuleActionSignatures"];
 freshRule = SelectFirst[rules, #["Action"] === freshAction &, Missing["NotFound"]];
 candidateOutput[rule_, observation_] := apply[
   orderedG0[[observation["SourceIndex"] + 1]], rule["Swap"], rule["Perm"]][[
   observation["InputIndex"] + 1]];
 replay[observations_] := Module[{vs = rules, sizes = {Length[rules]}},
   Do[
    vs = Select[vs, candidateOutput[#, observation] === observation["ObservedOutput"] &];
    AppendTo[sizes, Length[vs]],
    {observation, observations}];
   sizes];
 formationSizes = replay[formation["Observations"]];
 ambiguitySizes = replay[ambiguous["Observations"]];
 unavailableActiveSizes = replay[unavailable["Observations"]];
 formationOracle = SelectFirst[oracle["Cases"],
   StringEndsQ[#["CaseID"], "_FORM_RULE"] &]["QueryAnswers"];
 noExtensionOracle = SelectFirst[oracle["Cases"],
   StringEndsQ[#["CaseID"], "_NO_EXTENSION"] &]["QueryAnswers"];
 fullCertificate = And @@ Flatten[Table[
   formationOracle[qid[g0Index - 1, domainIndex - 1]] ===
     apply[orderedG0[[g0Index]], freshRule["Swap"], freshRule["Perm"]][[domainIndex]],
   {g0Index, Length[orderedG0]}, {domainIndex, Length[domain]}]];
 fullCompatibleRules = Select[rules, Function[rule, And @@ Flatten[Table[
    noExtensionOracle[qid[g0Index - 1, domainIndex - 1]] ===
      apply[orderedG0[[g0Index]], rule["Swap"], rule["Perm"]][[domainIndex]],
    {g0Index, Length[orderedG0]}, {domainIndex, Length[domain]}]]]];
 evalAst[ast_] := Which[
   ast[[1]] === "VAR", If[ast[[2]] === "A", a, b],
   ast[[1]] === "MIN", MapThread[Min, {evalAst[ast[[2]]], evalAst[ast[[3]]]}],
   ast[[1]] === "MAX", MapThread[Max, {evalAst[ast[[2]]], evalAst[ast[[3]]]}],
   ast[[1]] === "RULE", apply[evalAst[ast[[3]]], freshRule["Swap"], freshRule["Perm"]],
   True, $Failed];
 reuseAst = reuse["SelectedProgramAST"];
 checks = <|
   "NativeG0ClosureHasFourClasses" -> (Length[closure] === 4 && holdout["G0SemanticClassCount"] === 4),
   "OrderedG0IsNativeClosure" -> (Sort[orderedG0] === Sort[closure]),
   "CandidateRuleClassCountTen" -> (Length[rules] === holdout["CandidateRuleSemanticClassCount"] === 10),
   "FreshRuleExistsInSubstrate" -> ! MissingQ[freshRule],
   "FreshRuleNoHistoricalCollision" -> And @@
     Table[freshAction =!= historicalAction, {historicalAction, historicalActions}],
   "FormationTargetAbsentFromG0" -> ! MemberQ[closure, holdout["FormationTargetSemantics"]],
   "NestedTargetAbsentFromG0" -> ! MemberQ[closure, holdout["NestedReuseTargetSemantics"]],
   "FormationReplayUnique" -> (Last[formationSizes] === 1 && strictlyDecreasingQ[formationSizes]),
   "Full36CellFormationCertificate" -> TrueQ[fullCertificate],
   "FullActionMatchesHoldout" -> (Table[
     apply[orderedG0[[g0Index]], freshRule["Swap"], freshRule["Perm"]],
     {g0Index, Length[orderedG0]}] === holdout["FreshTargetRuleFullAction"]),
   "NestedReuseExactAndUsesRuleTwice" ->
     (evalAst[reuseAst] === holdout["NestedReuseTargetSemantics"] &&
      Count[reuseAst, "RULE", Infinity] >= 2 && reuse["RuleInventionCalls"] === 0),
   "AmbiguityAbstains" -> (Last[ambiguitySizes] > 1 &&
     ambiguous["Status"] === "META_GRAMMAR_RULE_AMBIGUOUS_ABSTAIN" &&
     ! TrueQ[ambiguous["FrozenRule"]]),
   "InsufficiencyFullCertificateEliminatesAll" ->
     (Length[fullCompatibleRules] === 0 && unavailable["FinalVersionSpaceSize"] === 0 &&
      unavailable["Status"] === "META_META_LANGUAGE_INSUFFICIENT_REJECT" &&
      ! TrueQ[unavailable["FrozenRule"]]),
   "PythonCohortChecksAllTrue" -> And @@ Values[cohortData["Checks"]],
   "PythonCohortPass" -> TrueQ[cohortData["CohortPass"]]
  |>;
 <|"CohortID" -> cohortID,
   "FormationVersionSpaceTrajectory" -> formationSizes,
   "AmbiguityVersionSpaceTrajectory" -> ambiguitySizes,
   "InsufficiencyActiveTrajectory" -> unavailableActiveSizes,
   "InsufficiencyFullCompatibleRuleCount" -> Length[fullCompatibleRules],
   "Checks" -> checks, "CohortAuditPass" -> And @@ Values[checks]|>
];

cohortAudits = auditCohort /@ data["Cohorts"];
freshActions = (ToExpression /@ Characters[#]) & /@
  (#["FreshTargetRuleActionSignature"] & /@ holdoutCohorts);
globalChecks = <|
 "FiveCohortsAudited" -> (Length[cohortAudits] === 5),
 "AllFiveCohortsPass" -> And @@ (#["CohortAuditPass"] & /@ cohortAudits),
 "FiveDistinctFreshRuleSemantics" -> (Length[DeleteDuplicates[freshActions]] === 5),
 "FreshFullWorldFingerprintsDistinctAndNonhistorical" ->
   (TrueQ[data["Checks"]["NoFullWorldSemanticCollisionWithS158C_R0"]] &&
    TrueQ[data["Checks"]["FiveDistinctFullWorldSemanticFingerprints"]]),
 "PythonGlobalChecksAllTrue" -> And @@ Values[data["Checks"]],
 "PythonMultiSeedPass" -> TrueQ[data["PythonMultiSeedPass"]]
|>;
out = <|
 "Stage" -> "S158-C-R2", "Engine" -> $Version,
 "AuditType" -> "NEW_SEEDS_FROZEN_MULTI_SEED_NATIVE_WOLFRAM_5x5_FULL_CERTIFICATE",
 "Recomputed" -> <|"G0SemanticClassCount" -> Length[closure],
   "RawRuleSchemaCount" -> Length[rawRules],
   "CandidateRuleSemanticClassCount" -> Length[rules]|>,
 "CohortAudits" -> cohortAudits, "Checks" -> globalChecks,
 "WolframIndependentPass" -> And @@ Values[globalChecks],
 "Conclusion" -> If[And @@ Values[globalChecks],
   "S158C_R2_WOLFRAM_NEW_SEEDS_FROZEN_MULTI_SEED_5X5_PASS",
   "S158C_R2_WOLFRAM_NEW_SEEDS_FROZEN_MULTI_SEED_5X5_FAIL"]|>;
Export[FileNameJoin[{stage, "results", "wolfram_multiseed_audit.json"}], out,
  "RawJSON", "Compact" -> False];
Print[ExportString[out, "RawJSON", "Compact" -> True]];
If[! TrueQ[out["WolframIndependentPass"]], Exit[1]];
