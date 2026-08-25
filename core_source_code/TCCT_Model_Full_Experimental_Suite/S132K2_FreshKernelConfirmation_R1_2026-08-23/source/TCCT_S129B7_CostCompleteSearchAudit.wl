(* ::Package:: *)

(* S129-B7 retrospective bounded cost-complete search audit. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
b6RunnerPath = FileNameJoin[{sourceDirectory,
  "TCCT_S129B6_TCCTNativeOnlineInduction.wl"}];
b6Text = Import[b6RunnerPath, "Text"];
marker = "Print[\"S129-B6 TCCT-native online induction R1\"]";
markerPosition = First@First@StringPosition[b6Text, marker];
ToExpression[StringTake[b6Text, markerPosition - 1], InputForm];

b7Manifest = Import[FileNameJoin[{rootDirectory, "protocol", "S129B7_manifest.json"}],
  "RawJSON"];
b6Result = Import[FileNameJoin[{rootDirectory, "input", "frozen_S129B6_result.json"}],
  "RawJSON"];
b6ByID = AssociationThread[Lookup[b6Result["FormalResults"], "WorldID"] ->
  b6Result["FormalResults"]];
maximumNodeCostB7 = b7Manifest["MaximumASTNodeCost"];
valueBoundB7 = b7Manifest["IntermediateAbsoluteValueBound"];
resultDirectory = FileNameJoin[{rootDirectory, "results"}];
controlDirectory = FileNameJoin[{rootDirectory, "negative_controls"}];
If[!DirectoryQ[resultDirectory], CreateDirectory[resultDirectory]];
If[!DirectoryQ[controlDirectory], CreateDirectory[controlDirectory]];

SetAttributes[AddCompleteArithmeticB7, HoldFirst];
AddCompleteArithmeticB7[store_, op_String, left_Association,
  right_Association, values_List] := Module[{expr},
  If[Length[values] === 0 || Max[Abs[values]] > valueBoundB7, Return[False]];
  expr = MakeExprB6[{op, left["AST"], right["AST"]},
    1 + left["Nodes"] + right["Nodes"],
    4 + left["Bits"] + right["Bits"], values, "Int"];
  AddBestB6[store, expr]; True
];

BuildCostCompleteBasisB7[examples_List, dimensions_List] := Module[
  {started = AbsoluteTime[], count = Length[examples],
   dimensionCount = Length[dimensions], constants, byCost, allStore = <||>,
   terminals = <||>, newStore, newRules, leftCost, rightCost, lefts, rights,
   left, right, values, divisor, ordered, cost, expansionAttempts = 0,
   countsByCost, sorted},
  constants = Range[0, Max[dimensions]];
  byCost = Table[<||>, {maximumNodeCostB7}];
  Do[AddBestB6[terminals, MakeExprB6[{"Var", index}, 1,
      4 + Ceiling[Log[2, dimensionCount + 1]], examples[[All, index]], "Int"]],
    {index, dimensionCount}];
  Do[AddBestB6[terminals, MakeExprB6[{"Const", constant}, 1,
      ConstantBitsB6[constant], ConstantArray[constant, count], "Int"]],
    {constant, constants}];
  byCost[[1]] = terminals; allStore = Association[Normal[terminals]];
  Do[
    newStore = <||>;
    Do[
      rightCost = cost - 1 - leftCost;
      If[rightCost < 1, Continue[]];
      lefts = Values[byCost[[leftCost]]]; rights = Values[byCost[[rightCost]]];
      If[Length[lefts] === 0 || Length[rights] === 0, Continue[]];
      Do[
        ordered = OrderedQ[{{left["Bits"], ASTKeyB6[left["AST"]]},
          {right["Bits"], ASTKeyB6[right["AST"]]}}];
        If[ordered,
          expansionAttempts++;
          AddCompleteArithmeticB7[newStore, "Add", left, right,
            left["Values"] + right["Values"]];
          expansionAttempts++;
          AddCompleteArithmeticB7[newStore, "Mul", left, right,
            left["Values"] right["Values"]];
          If[Min[left["Values"]] >= 0 && Min[right["Values"]] >= 0,
            expansionAttempts++;
            AddCompleteArithmeticB7[newStore, "BitXor", left, right,
              MapThread[BitXor, {left["Values"], right["Values"]}]]]];
        expansionAttempts++;
        AddCompleteArithmeticB7[newStore, "Sub", left, right,
          left["Values"] - right["Values"]];
        If[Length[DeleteDuplicates[right["Values"]]] === 1 &&
            First[right["Values"]] > 0,
          divisor = First[right["Values"]]; expansionAttempts++;
          AddCompleteArithmeticB7[newStore, "Mod", left, right,
            Mod[left["Values"], divisor]]],
        {left, lefts}, {right, rights}],
      {leftCost, 1, cost - 2}];
    newRules = Select[Normal[newStore], !KeyExistsQ[allStore, First[#]] &];
    byCost[[cost]] = If[Length[newRules] === 0, <||>, Association[newRules]];
    Do[AddBestB6[allStore, item], {item, Values[byCost[[cost]]]}],
    {cost, 2, maximumNodeCostB7}];
  countsByCost = Table[Length[byCost[[cost]]], {cost, maximumNodeCostB7}];
  sorted = SortBy[Values[allStore], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}];
  <|"Ints" -> sorted,
    "Statistics" -> <|"IntegerSemanticCount" -> Length[sorted],
      "SemanticCountsByExactNodeCost" -> countsByCost,
      "MaximumNodeCost" -> maximumNodeCostB7,
      "IntermediateAbsoluteValueBound" -> valueBoundB7,
      "ExpansionAttempts" -> expansionAttempts,
      "BuildSeconds" -> N[AbsoluteTime[] - started],
      "SemanticCompleteWithinFrozenBound" -> True|>|>
];

$BasisCacheB7 = <||>;
GetBasisB7[world_Association] := Module[{key, cached, built},
  key = SemanticKeyB6[{world["Phi"], world["CoordinateDimensions"]}];
  cached = Lookup[$BasisCacheB7, key, Null]; If[AssociationQ[cached], Return[cached]];
  built = <|"Basis" -> BuildCostCompleteBasisB7[world["Phi"],
      world["CoordinateDimensions"]],
    "Predicates" -> BuildPredicatesB6[world["Phi"],
      world["CoordinateDimensions"]]|>;
  AssociateTo[$BasisCacheB7, key -> built]; built
];

Print["S129-B7 bounded cost-complete search audit R1"];
Print["Retrospective=True; F02 templates=False; worlds/DSL/TCCT loop changed=False"];

formalResultsB7 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  Print["B7 WORLD START ", world["WorldID"], " n=", world["StateCount"]];
  built = GetBasisB7[world];
  active = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "ACTIVE_TCCT_REWRITE_DISAGREEMENT"];
  passive = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "PASSIVE_FIXED_ORDER"];
  ablation = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "REWRITE_DISABLED_ABLATION"];
  old = b6ByID[world["WorldID"]];
  Print["B7 WORLD END ", world["WorldID"], " active=", active["Outcome"],
    " q=", active["MembershipQueryCount"], " passiveQ=", passive["MembershipQueryCount"],
    " noRewrite=", ablation["Outcome"]];
  <|"WorldID" -> world["WorldID"], "StateCount" -> world["StateCount"],
    "CoordinateDimensions" -> world["CoordinateDimensions"],
    "BasisStatistics" -> built["Basis"]["Statistics"],
    "B6ActiveOutcome" -> old["Active"]["Outcome"],
    "B6ActiveExact" -> old["Active"]["ExactCertified"],
    "Active" -> active, "Passive" -> passive, "RewriteDisabled" -> ablation|>,
  {index, Length[publicWorlds]}];

randomResultsB7 = Table[
  world = publicWorlds[[index]];
  table = RandomReachableTableB6[world["StateCount"], world["ActionCount"],
    world["StartState"], 1298900 + index];
  built = GetBasisB7[world];
  If[table === $Failed,
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> True,
      "ExactCertified" -> False|>,
    randomRun = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
      "ACTIVE_TCCT_REWRITE_DISAGREEMENT"];
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> False,
      "Outcome" -> randomRun["Outcome"], "ExactCertified" -> randomRun["ExactCertified"],
      "MembershipQueryCount" -> randomRun["MembershipQueryCount"],
      "Programs" -> randomRun["Programs"],
      "CompressionRatio" -> randomRun["CompressionRatio"]|>],
  {index, Length[publicWorlds]}];

nearLawResultsB7 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  active = formalResultsB7[[index, "Active"]];
  mutated = Map[Identity, table]; oldTarget = mutated[[1, 1]];
  mutated[[1, 1]] = Mod[oldTarget, world["StateCount"]] + 1;
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[world, mutated, active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"], "Applicable" -> TrueQ[active["ExactCertified"]],
    "BaseProgramMismatchCount" -> Length[errors],
    "MutationDetected" -> (!TrueQ[active["ExactCertified"]] || Length[errors] >= 1)|>,
  {index, Length[publicWorlds]}];

relabelResultsB7 = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  relabeled = RelabelWorldB6[world, table, 1299000 + index];
  active = formalResultsB7[[index, "Active"]];
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[relabeled["World"], relabeled["Table"], active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"],
    "CoordinateDatasetHashInvariant" ->
      (CoordinateDatasetHashB6[world, table] ===
        CoordinateDatasetHashB6[relabeled["World"], relabeled["Table"]]),
    "FrozenProgramStillExact" -> (!TrueQ[active["ExactCertified"]] || Length[errors] === 0)|>,
  {index, Length[publicWorlds]}];

activeExactCountB7 = Count[Lookup[Lookup[formalResultsB7, "Active"],
  "ExactCertified"], True];
passiveExactCountB7 = Count[Lookup[Lookup[formalResultsB7, "Passive"],
  "ExactCertified"], True];
noRewriteExactCountB7 = Count[Lookup[Lookup[formalResultsB7, "RewriteDisabled"],
  "ExactCertified"], True];
randomExactCountB7 = Count[Lookup[randomResultsB7, "ExactCertified"], True];
f02ResultB7 = SelectFirst[formalResultsB7, #WorldID === "F02" &];
f02CausalSupport = !TrueQ[f02ResultB7["B6ActiveExact"]] &&
  TrueQ[f02ResultB7["Active"]["ExactCertified"]];
nearLawPassB7 = And @@ Lookup[nearLawResultsB7, "MutationDetected"];
relabelPassB7 = And @@ Flatten[{Lookup[relabelResultsB7,
  "CoordinateDatasetHashInvariant"], Lookup[relabelResultsB7,
  "FrozenProgramStillExact"]}];

resultB7 = <|
  "Stage" -> b7Manifest["Stage"],
  "EvidenceStatus" -> b7Manifest["EvidenceStatus"],
  "WolframVersion" -> $Version, "NativeWolframExecution" -> True,
  "CanonicalTCCTModified" -> False, "S128BModified" -> False,
  "WorldsChangedFromB6" -> False, "DSLChangedFromB6" -> False,
  "TCCTControlLoopChangedFromB6" -> False,
  "PriorBestProgramsLoaded" -> False, "GeneratorTruthRead" -> False,
  "F02SpecificTemplatesAdded" -> False,
  "SearchBoundary" -> b7Manifest["CompletenessClaim"],
  "ActiveExactCount" -> activeExactCountB7,
  "PassiveExactCount" -> passiveExactCountB7,
  "RewriteDisabledExactCount" -> noRewriteExactCountB7,
  "RandomControlExactCount" -> randomExactCountB7,
  "F02SearchCoverageCausalHypothesisSupported" -> f02CausalSupport,
  "NearLawPass" -> nearLawPassB7, "StateRelabelingPass" -> relabelPassB7,
  "AutomatonFallbackRetained" -> True,
  "FormalResults" -> formalResultsB7,
  "RandomControls" -> randomResultsB7,
  "NearLawControls" -> nearLawResultsB7,
  "StateRelabelingControls" -> relabelResultsB7|>;

Export[FileNameJoin[{resultDirectory, "S129B7_result.json"}], resultB7,
  "RawJSON", "Compact" -> False];
Export[FileNameJoin[{resultDirectory, "S129B7_per_world.csv"}], Table[
  {row["WorldID"], row["B6ActiveOutcome"], row["Active"]["Outcome"],
    row["Active"]["MembershipQueryCount"], row["Passive"]["MembershipQueryCount"],
    row["RewriteDisabled"]["Outcome"], row["BasisStatistics"]["IntegerSemanticCount"],
    row["BasisStatistics"]["BuildSeconds"]}, {row, formalResultsB7}], "CSV",
  "TableHeadings" -> {{}, {"WorldID", "B6Outcome", "B7Outcome", "ActiveQueries",
    "PassiveQueries", "RewriteDisabledOutcome", "BasisSemantics", "BasisBuildSeconds"}}];
Export[FileNameJoin[{controlDirectory, "S129B7_random_controls.json"}],
  randomResultsB7, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B7_near_law_controls.json"}],
  nearLawResultsB7, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B7_state_relabeling_controls.json"}],
  relabelResultsB7, "RawJSON", "Compact" -> False];
Print["S129-B7 COMPLETE exact=", activeExactCountB7, "/", Length[formalResultsB7],
  " F02CausalSupport=", f02CausalSupport, " randomExact=", randomExactCountB7];
