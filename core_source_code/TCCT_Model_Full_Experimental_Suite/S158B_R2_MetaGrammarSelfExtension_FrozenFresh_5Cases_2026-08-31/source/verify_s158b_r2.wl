ClearAll["Global`*"];
stage = DirectoryName[DirectoryName[$InputFileName]];
data = Import[FileNameJoin[{stage, "results", "python_fresh_result.json"}], "RawJSON"];
holdout = Import[FileNameJoin[{stage, "oracle", "sealed_exact_holdout.json"}], "RawJSON"];
oracleRows = Import[FileNameJoin[{stage, "oracle", "sealed_query_oracles.json"}], "RawJSON"]["Cases"];

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

orderedG0 = holdout["OrderedG0Semantics"];
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
expressiveRules = Select[rawRules, expressiveQ];
rules = DeleteDuplicatesBy[expressiveRules, #["Action"] &];

freshAction = ToExpression /@ Characters[holdout["FreshTargetRuleActionSignature"]];
historicalActions = (ToExpression /@ Characters[#]) & /@
  holdout["HistoricalTargetRuleActionSignatures"];
freshRule = SelectFirst[rules, #["Action"] === freshAction &, Missing["NotFound"]];
caseRows = Association@Table[row["CaseID"] -> row, {row, data["CaseRows"]}];
formation = caseRows["S158B_R2_FORM_RULE"];
reuse = caseRows["S158B_R2_REUSE_NESTED"];
ambiguous = caseRows["S158B_R2_AMBIGUOUS"];
unavailable = caseRows["S158B_R2_NO_EXTENSION"];

candidateOutput[rule_, observation_] := apply[
  orderedG0[[observation["SourceIndex"] + 1]], rule["Swap"], rule["Perm"]][[
  observation["InputIndex"] + 1]];
replaySizes[observations_] := Module[{vs = rules, sizes = {Length[rules]}},
 Do[
  vs = Select[vs, candidateOutput[#, observation] === observation["ObservedOutput"] &];
  AppendTo[sizes, Length[vs]],
  {observation, observations}];
 sizes];
formationSizes = replaySizes[formation["Observations"]];
ambiguitySizes = replaySizes[ambiguous["Observations"]];
unavailableSizes = replaySizes[unavailable["Observations"]];
strictlyDecreasingQ[sizes_] := And @@ Table[sizes[[k + 1]] < sizes[[k]],
  {k, Length[sizes] - 1}];

formationOracle = SelectFirst[oracleRows,
  #["CaseID"] === "S158B_R2_FORM_RULE" &]["QueryAnswers"];
qid[g0Index_, domainIndex_] := "Q" <> IntegerString[g0Index, 10, 2] <> "_" <>
  IntegerString[domainIndex, 10, 2];
fullRuleCertificate = And @@ Flatten[Table[
  formationOracle[qid[g0Index - 1, domainIndex - 1]] ===
    apply[orderedG0[[g0Index]], freshRule["Swap"], freshRule["Perm"]][[domainIndex]],
  {g0Index, Length[orderedG0]}, {domainIndex, Length[domain]}]];

evalAst[ast_] := Which[
 ast[[1]] === "VAR", If[ast[[2]] === "A", a, b],
 ast[[1]] === "MIN", MapThread[Min, {evalAst[ast[[2]]], evalAst[ast[[3]]]}],
 ast[[1]] === "MAX", MapThread[Max, {evalAst[ast[[2]]], evalAst[ast[[3]]]}],
 ast[[1]] === "RULE", apply[evalAst[ast[[3]]], freshRule["Swap"], freshRule["Perm"]],
 True, $Failed];
reuseAst = reuse["SelectedProgramAST"];

checks = <|
 "NativeG0ClosureHasFourClasses" -> (Length[closure] === 4 && holdout["G0SemanticClassCount"] === 4),
 "OrderedG0IsExactlyNativeClosure" -> (Sort[orderedG0] === Sort[closure]),
 "IndependentCandidateRuleClassCount" -> (Length[rules] === holdout["CandidateRuleSemanticClassCount"] === 10),
 "FreshRuleExistsInFixedSubstrate" -> ! MissingQ[freshRule],
 "FreshRuleHasNoHistoricalSemanticCollision" -> And @@
   Table[freshAction =!= historicalAction, {historicalAction, historicalActions}],
 "FormationTargetAbsentFromG0" -> ! MemberQ[closure, holdout["FormationTargetSemantics"]],
 "NestedTargetAbsentFromG0" -> ! MemberQ[closure, holdout["NestedReuseTargetSemantics"]],
 "ActiveFormationReplayUnique" -> (Last[formationSizes] === 1 && strictlyDecreasingQ[formationSizes]),
 "Full36CellRuleActionCertificate" -> TrueQ[fullRuleCertificate],
 "FreshFullActionMatchesHoldout" -> (Table[
   apply[orderedG0[[g0Index]], freshRule["Swap"], freshRule["Perm"]],
   {g0Index, Length[orderedG0]}] === holdout["FreshTargetRuleFullAction"]),
 "NestedReuseASTExact" -> (evalAst[reuseAst] === holdout["NestedReuseTargetSemantics"] &&
   Count[reuseAst, "RULE", Infinity] >= 2 && reuse["RuleInventionCalls"] === 0),
 "AmbiguityReplayRemainsNonUnique" -> (Last[ambiguitySizes] > 1 &&
   ambiguous["Status"] === "META_GRAMMAR_RULE_AMBIGUOUS_ABSTAIN" && ! TrueQ[ambiguous["FrozenRule"]]),
 "InsufficiencyReplayEliminatesAll" -> (Last[unavailableSizes] === 0 &&
   unavailable["Status"] === "META_META_LANGUAGE_INSUFFICIENT_REJECT" && ! TrueQ[unavailable["FrozenRule"]]),
 "PythonChecksAllTrue" -> And @@ Values[data["Checks"]],
 "PythonFreshPass" -> TrueQ[data["PythonFreshPass"]]
|>;

out = <|
 "Stage" -> "S158-B-R2",
 "Engine" -> $Version,
 "AuditType" -> "NEW_SEED_FROZEN_PRE_MATERIALIZATION_INDEPENDENT_NATIVE_WOLFRAM",
 "Recomputed" -> <|
   "G0SemanticClassCount" -> Length[closure],
   "RawRuleSchemaCount" -> Length[rawRules],
   "ExpressiveRuleSchemaCount" -> Length[expressiveRules],
   "CandidateRuleSemanticClassCount" -> Length[rules],
   "FormationVersionSpaceTrajectory" -> formationSizes,
   "AmbiguityVersionSpaceTrajectory" -> ambiguitySizes,
   "InsufficiencyVersionSpaceTrajectory" -> unavailableSizes|>,
 "Checks" -> checks,
 "WolframIndependentPass" -> And @@ Values[checks],
 "Conclusion" -> If[And @@ Values[checks],
   "S158B_R2_WOLFRAM_NEW_SEED_FROZEN_FRESH_AUDIT_PASS",
   "S158B_R2_WOLFRAM_NEW_SEED_FROZEN_FRESH_AUDIT_FAIL"]|>;
Export[FileNameJoin[{stage, "results", "wolfram_fresh_audit.json"}], out,
  "RawJSON", "Compact" -> False];
Print[ExportString[out, "RawJSON", "Compact" -> True]];
If[! TrueQ[out["WolframIndependentPass"]], Exit[1]];
