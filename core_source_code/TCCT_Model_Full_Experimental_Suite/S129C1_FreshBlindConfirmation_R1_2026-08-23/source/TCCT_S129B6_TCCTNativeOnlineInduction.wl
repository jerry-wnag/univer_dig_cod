(* ::Package:: *)

(* S129-B6: fresh-world TCCT-managed online symbolic induction. *)

ClearAll["Global`*"];

sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
publicPath = FileNameJoin[{rootDirectory, "input", "S129B6_public_input.json"}];
oraclePath = FileNameJoin[{rootDirectory, "oracle", "S129B6_oracle_tables.json"}];
manifestPath = FileNameJoin[{rootDirectory, "protocol", "S129B6_preregistered_manifest.json"}];
resultDirectory = FileNameJoin[{rootDirectory, "results"}];
controlDirectory = FileNameJoin[{rootDirectory, "negative_controls"}];
resultPath = FileNameJoin[{resultDirectory, "S129B6_result.json"}];
If[!DirectoryQ[resultDirectory], CreateDirectory[resultDirectory]];
If[!DirectoryQ[controlDirectory], CreateDirectory[controlDirectory]];

If[!And @@ (FileExistsQ /@ {publicPath, oraclePath, manifestPath}),
  Print["FATAL: S129-B6 input boundary incomplete"]; Exit[2]];

public = Import[publicPath, "RawJSON"];
oracle = Import[oraclePath, "RawJSON"];
manifest = Import[manifestPath, "RawJSON"];
publicWorlds = public["Worlds"];
oracleByID = AssociationThread[Lookup[oracle["Worlds"], "WorldID"] -> oracle["Worlds"]];

basisRounds = manifest["BlindArithmeticExpansionRounds"];
roundSemanticCap = manifest["BlindRoundSemanticCap"];
candidateCap = manifest["CandidateSemanticCapPerTarget"];
predicateSearchCap = manifest["PredicateSearchCap"];
membershipBudget = manifest["MembershipQueryBudget"];
equivalenceBudget = manifest["EquivalenceCounterexampleBudget"];

SemanticKeyB6[values_List] := ToString[values, InputForm];
ASTKeyB6[ast_] := ToString[ast, InputForm];
ConstantBitsB6[value_Integer] := 3 + 2 Ceiling[Log[2, Abs[value] + 2]];
MakeExprB6[ast_, nodes_Integer, bits_Integer, values_List, kind_String] :=
  <|"AST" -> ast, "Nodes" -> nodes, "Bits" -> bits,
    "Values" -> values, "Kind" -> kind|>;

SetAttributes[AddBestB6, HoldFirst];
AddBestB6[store_, expr_Association] := Module[{key, old, candidateRank, oldRank},
  key = SemanticKeyB6[expr["Values"]];
  old = Lookup[store, key, Null];
  candidateRank = {expr["Bits"], expr["Nodes"], ASTKeyB6[expr["AST"]]};
  oldRank = If[AssociationQ[old],
    {old["Bits"], old["Nodes"], ASTKeyB6[old["AST"]]}, Null];
  If[!AssociationQ[old] || OrderedQ[{candidateRank, oldRank}] && candidateRank =!= oldRank,
    AssociateTo[store, key -> expr]];
];

SetAttributes[AddArithmeticB6, HoldFirst];
AddArithmeticB6[store_, op_String, left_Association, right_Association,
  values_List, valueCap_Integer] := Module[{bits},
  If[Length[values] === 0 || Max[Abs[values]] > valueCap, Return[]];
  bits = 4 + left["Bits"] + right["Bits"];
  AddBestB6[store, MakeExprB6[{op, left["AST"], right["AST"]},
    1 + left["Nodes"] + right["Nodes"], bits, values, "Int"]];
];

BuildBlindBasisB6[examples_List, dimensions_List] := Module[
  {started = AbsoluteTime[], count, dimensionCount, constants, divisors,
   terminalStore = <||>, allStore = <||>, frontier, atoms, newStore,
   newRules, limited, values, valueCap, expr, atom, divisor, round,
   commutativeOrder, sorted},
  count = Length[examples]; dimensionCount = Length[dimensions];
  constants = Range[0, Max[dimensions]];
  divisors = DeleteDuplicates@Join[Range[2, Max[dimensions]], dimensions];
  valueCap = Max[256, 6 Max[dimensions]^2];
  Do[AddBestB6[terminalStore, MakeExprB6[{"Var", index}, 1,
      4 + Ceiling[Log[2, dimensionCount + 1]], examples[[All, index]], "Int"]],
    {index, dimensionCount}];
  Do[AddBestB6[terminalStore, MakeExprB6[{"Const", constant}, 1,
      ConstantBitsB6[constant], ConstantArray[constant, count], "Int"]],
    {constant, constants}];
  allStore = Association[Normal[terminalStore]];
  atoms = SortBy[Values[terminalStore], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}];
  frontier = atoms;
  Do[
    newStore = <||>;
    limited = Take[SortBy[frontier, {#Bits &, #Nodes &, ASTKeyB6[#AST] &}],
      UpTo[roundSemanticCap]];
    Do[
      Do[
        commutativeOrder = OrderedQ[{{expr["Bits"], ASTKeyB6[expr["AST"]]},
          {atom["Bits"], ASTKeyB6[atom["AST"]]}}];
        If[commutativeOrder,
          AddArithmeticB6[newStore, "Add", expr, atom,
            expr["Values"] + atom["Values"], valueCap];
          AddArithmeticB6[newStore, "Mul", expr, atom,
            expr["Values"] atom["Values"], valueCap];
          If[Min[expr["Values"]] >= 0 && Min[atom["Values"]] >= 0,
            AddArithmeticB6[newStore, "BitXor", expr, atom,
              MapThread[BitXor, {expr["Values"], atom["Values"]}], valueCap]]];
        AddArithmeticB6[newStore, "Sub", expr, atom,
          expr["Values"] - atom["Values"], valueCap];
        AddArithmeticB6[newStore, "Sub", atom, expr,
          atom["Values"] - expr["Values"], valueCap],
        {atom, atoms}];
      Do[
        values = Mod[expr["Values"], divisor];
        AddBestB6[newStore, MakeExprB6[
          {"Mod", expr["AST"], {"Const", divisor}},
          2 + expr["Nodes"], 4 + expr["Bits"] + ConstantBitsB6[divisor],
          values, "Int"]],
        {divisor, divisors}],
      {expr, limited}];
    newRules = Select[Normal[newStore], !KeyExistsQ[allStore, First[#]] &];
    frontier = If[Length[newRules] === 0, {},
      Take[SortBy[Values[Association[newRules]],
        {#Bits &, #Nodes &, ASTKeyB6[#AST] &}], UpTo[roundSemanticCap]]];
    Do[AddBestB6[allStore, item], {item, frontier}],
    {round, basisRounds}];
  sorted = SortBy[Values[allStore], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}];
  <|"Ints" -> sorted,
    "Statistics" -> <|"IntegerSemanticCount" -> Length[sorted],
      "ExpansionRounds" -> basisRounds,
      "BuildSeconds" -> N[AbsoluteTime[] - started]|>|>
];

BuildPredicatesB6[examples_List, dimensions_List] := Module[
  {store = <||>, count = Length[examples], left, right, values, expr,
   terminals = {}, dimensionCount = Length[dimensions]},
  Do[AppendTo[terminals, MakeExprB6[{"Var", index}, 1, 5,
      examples[[All, index]], "Int"]], {index, dimensionCount}];
  Do[AppendTo[terminals, MakeExprB6[{"Const", constant}, 1,
      ConstantBitsB6[constant], ConstantArray[constant, count], "Int"]],
    {constant, 0, Max[dimensions]}];
  Do[
    values = MapThread[SameQ, {left["Values"], right["Values"]}];
    If[Length[DeleteDuplicates[values]] > 1,
      AddBestB6[store, MakeExprB6[{"Eq", left["AST"], right["AST"]},
        1 + left["Nodes"] + right["Nodes"], 4 + left["Bits"] + right["Bits"],
        values, "Bool"]]];
    values = MapThread[Less, {left["Values"], right["Values"]}];
    If[Length[DeleteDuplicates[values]] > 1,
      AddBestB6[store, MakeExprB6[{"Lt", left["AST"], right["AST"]},
        1 + left["Nodes"] + right["Nodes"], 4 + left["Bits"] + right["Bits"],
        values, "Bool"]]],
    {left, terminals}, {right, terminals}];
  SortBy[Values[store], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}]
];

ValidTargetExprsB6[ints_List, dimension_Integer] := Select[ints,
  Min[#Values] >= 0 && Max[#Values] < dimension &];

CandidatesForTargetB6[validInts_List, predicates_List, observations_List,
  action_Integer, component_Integer] := Module[
  {records, states, labels, store = <||>, direct, selectedPredicates,
   predicate, yesPositions, noPositions, yesLeaves, noLeaves, yes, no,
   candidate, ranked},
  records = Select[observations, #Action === action &];
  states = Lookup[records, "State", {}];
  labels = If[Length[records] === 0, {}, Lookup[records, "TargetCoordinate"][[All, component]]];
  direct = Select[validInts,
    Length[states] === 0 || #["Values"][[states]] === labels &];
  Do[AddBestB6[store, item], {item, Take[direct, UpTo[candidateCap]]}];
  If[Length[states] >= 2,
    selectedPredicates = Take[predicates, UpTo[predicateSearchCap]];
    Do[
      yesPositions = Select[Range[Length[states]],
        TrueQ[predicate["Values"][[states[[#]]]]] &];
      noPositions = Complement[Range[Length[states]], yesPositions];
      If[Length[yesPositions] === 0 || Length[noPositions] === 0, Continue[]];
      yesLeaves = Take[Select[validInts,
        #["Values"][[states[[yesPositions]]]] === labels[[yesPositions]] &], UpTo[2]];
      noLeaves = Take[Select[validInts,
        #["Values"][[states[[noPositions]]]] === labels[[noPositions]] &], UpTo[2]];
      Do[
        candidate = MakeExprB6[
          {"If", predicate["AST"], yes["AST"], no["AST"]},
          1 + predicate["Nodes"] + yes["Nodes"] + no["Nodes"],
          5 + predicate["Bits"] + yes["Bits"] + no["Bits"],
          MapThread[If, {predicate["Values"], yes["Values"], no["Values"]}], "Int"];
        AddBestB6[store, candidate],
        {yes, yesLeaves}, {no, noLeaves}],
      {predicate, selectedPredicates}]];
  ranked = SortBy[Values[store], {#Bits &, #Nodes &, ASTKeyB6[#AST] &}];
  Take[ranked, UpTo[candidateCap]]
];

BuildCandidateMatrixB6[world_Association, basis_Association, predicates_List,
  observations_List] := Module[{validByComponent},
  validByComponent = Table[ValidTargetExprsB6[basis["Ints"], dimension],
    {dimension, world["CoordinateDimensions"]}];
  Table[CandidatesForTargetB6[validByComponent[[component]], predicates,
      observations, action, component],
    {action, world["ActionCount"]},
    {component, Length[world["CoordinateDimensions"]]}]
];

FilterFixedMatrixB6[matrix_List, observations_List] := Table[
  Select[matrix[[action, component]], Function[candidate,
    And @@ Table[candidate["Values"][[record["State"]]] ===
      record["TargetCoordinate"][[component]],
      {record, Select[observations, #Action === action &]}]]],
  {action, Length[matrix]}, {component, Length[matrix[[action]]]}];

MatrixNonemptyB6[matrix_List] := And @@ Flatten[Map[Length[#] > 0 &, matrix, {2}]];
EntropyB6[values_List] := Module[{p},
  If[Length[values] <= 1, Return[0.]];
  p = N[Values[Counts[values]]/Length[values]];
  -Total[p Log2[p]]
];
DisagreementScoreB6[matrix_List, state_Integer, action_Integer] :=
  Total[EntropyB6[Lookup[#, "Values"][[All, state]]] & /@ matrix[[action]]];

WinnerProgramsB6[matrix_List] := Table[
  (First@SortBy[matrix[[action, component]],
    {#Bits &, #Nodes &, ASTKeyB6[#AST] &}])["AST"],
  {action, Length[matrix]}, {component, Length[matrix[[action]]]}];
WinnerProgramBitsB6[matrix_List] := 16 + 8 Length[matrix] +
  Total@Flatten@Table[
    (First@SortBy[matrix[[action, component]],
      {#Bits &, #Nodes &, ASTKeyB6[#AST] &}])["Bits"],
    {action, Length[matrix]}, {component, Length[matrix[[action]]]}];

EvalASTB6[ast_List, coordinate_List] := Switch[First[ast],
  "Var", coordinate[[ast[[2]]]],
  "Const", ast[[2]],
  "Add", EvalASTB6[ast[[2]], coordinate] + EvalASTB6[ast[[3]], coordinate],
  "Sub", EvalASTB6[ast[[2]], coordinate] - EvalASTB6[ast[[3]], coordinate],
  "Mul", EvalASTB6[ast[[2]], coordinate] EvalASTB6[ast[[3]], coordinate],
  "Mod", Mod[EvalASTB6[ast[[2]], coordinate], EvalASTB6[ast[[3]], coordinate]],
  "BitXor", BitXor[EvalASTB6[ast[[2]], coordinate], EvalASTB6[ast[[3]], coordinate]],
  "Eq", EvalASTB6[ast[[2]], coordinate] === EvalASTB6[ast[[3]], coordinate],
  "Lt", EvalASTB6[ast[[2]], coordinate] < EvalASTB6[ast[[3]], coordinate],
  "If", If[TrueQ[EvalASTB6[ast[[2]], coordinate]],
    EvalASTB6[ast[[3]], coordinate], EvalASTB6[ast[[4]], coordinate]],
  _, $Failed];

OracleTargetB6[world_Association, table_List, state_Integer, action_Integer] :=
  world["Phi"][[table[[state, action]]]];
ProgramErrorsB6[world_Association, table_List, programs_List] := Module[
  {errors = {}, predicted, target},
  Do[
    predicted = EvalASTB6[#, world["Phi"][[state]]] & /@ programs[[action]];
    target = OracleTargetB6[world, table, state, action];
    If[predicted =!= target, AppendTo[errors,
      <|"State" -> state, "Action" -> action,
        "Predicted" -> predicted, "TargetCoordinate" -> target|>]],
    {state, world["StateCount"]}, {action, world["ActionCount"]}];
  errors
];

AddObservationB6[observations_List, world_Association, table_List,
  state_Integer, action_Integer, source_String] := Module[{existing},
  existing = SelectFirst[observations, #State === state && #Action === action &, Null];
  If[AssociationQ[existing], observations,
    Append[observations, <|"State" -> state, "Action" -> action,
      "TargetCoordinate" -> OracleTargetB6[world, table, state, action],
      "Source" -> source|>]]
];

RunOnlineLearnerB6[world_Association, table_List, basis_Association,
  predicates_List, mode_String] := Module[
  {started = AbsoluteTime[], observations = {}, trace = {}, matrix, fixedMatrix = Null,
   previousSignature = Null, signature, rewriteCount = 0, query, candidates,
   unqueried, ranked, maxScore, programs = Null, errors, counterexample,
   outcome = "BUDGET_EXHAUSTED_FALLBACK", exact = False, equivalenceCalls = 0,
   equivalenceCounterexamples = 0, initialQueries = 0, programBits = Null,
   tableBits, phiBits, totalBits, ratio, state, action},
  Do[
    observations = AddObservationB6[observations, world, table,
      world["StartState"], action, "INITIAL_SEED"];
    initialQueries++, {action, world["ActionCount"]}];
  If[mode === "REWRITE_DISABLED_ABLATION",
    fixedMatrix = BuildCandidateMatrixB6[world, basis, predicates, observations]];
  While[Length[observations] <= membershipBudget && equivalenceCalls <= equivalenceBudget,
    matrix = If[mode === "REWRITE_DISABLED_ABLATION",
      FilterFixedMatrixB6[fixedMatrix, observations],
      BuildCandidateMatrixB6[world, basis, predicates, observations]];
    signature = Map[Length, matrix, {2}];
    If[previousSignature =!= Null && signature =!= previousSignature, rewriteCount++];
    previousSignature = signature;
    If[!MatrixNonemptyB6[matrix],
      outcome = "NO_SURVIVING_PROGRAM_FALLBACK"; Break[]];
    unqueried = Select[Flatten[Table[{state, action},
        {state, world["StateCount"]}, {action, world["ActionCount"]}], 1],
      Function[pair, !AnyTrue[observations,
        Function[record, record["State"] === pair[[1]] &&
          record["Action"] === pair[[2]]]]]];
    ranked = If[Length[unqueried] === 0, {},
      SortBy[Table[{DisagreementScoreB6[matrix, pair[[1]], pair[[2]]],
          pair[[1]], pair[[2]]}, {pair, unqueried}],
        Function[row, {-row[[1]], row[[2]], row[[3]]}]]];
    maxScore = If[Length[ranked] === 0, 0., ranked[[1, 1]]];
    If[Length[unqueried] > 0 && (mode === "PASSIVE_FIXED_ORDER" || maxScore > 0),
      query = If[mode === "PASSIVE_FIXED_ORDER", First[unqueried], ranked[[1, {2, 3}]]];
      observations = AddObservationB6[observations, world, table,
        query[[1]], query[[2]], If[mode === "PASSIVE_FIXED_ORDER",
          "PASSIVE_QUERY", "MAX_DISAGREEMENT_QUERY"]];
      AppendTo[trace, <|"Round" -> Length[trace] + 1,
        "Event" -> Last[observations]["Source"], "State" -> query[[1]],
        "Action" -> query[[2]], "DisagreementBits" -> N[maxScore],
        "CandidateCounts" -> signature|>];
      Continue[]];
    programs = WinnerProgramsB6[matrix]; programBits = WinnerProgramBitsB6[matrix];
    equivalenceCalls++;
    errors = ProgramErrorsB6[world, table, programs];
    If[Length[errors] === 0,
      exact = True; outcome = "EXACT_PROGRAM_FROZEN";
      AppendTo[trace, <|"Round" -> Length[trace] + 1,
        "Event" -> "EQUIVALENCE_CERTIFICATE", "MismatchCount" -> 0|>]; Break[]];
    counterexample = First[errors]; equivalenceCounterexamples++;
    If[AnyTrue[observations, #State === counterexample["State"] &&
        #Action === counterexample["Action"] &],
      outcome = "REPEATED_COUNTEREXAMPLE_FALLBACK"; Break[]];
    observations = Append[observations, Join[counterexample,
      <|"Source" -> "EQUIVALENCE_COUNTEREXAMPLE"|>]];
    AppendTo[trace, <|"Round" -> Length[trace] + 1,
      "Event" -> "EQUIVALENCE_COUNTEREXAMPLE",
      "State" -> counterexample["State"], "Action" -> counterexample["Action"],
      "CandidateCounts" -> signature|>];
  ];
  tableBits = world["StateCount"] world["ActionCount"]
    Ceiling[Log[2, world["StateCount"]]];
  phiBits = Ceiling[Log[2, Factorial[world["StateCount"]]]];
  totalBits = If[exact, phiBits + programBits, Null];
  ratio = If[exact, N[totalBits/tableBits], Null];
  <|"Mode" -> mode, "Outcome" -> outcome, "ExactCertified" -> exact,
    "MembershipQueryCount" -> Length[observations],
    "InitialSeedQueryCount" -> initialQueries,
    "EquivalenceOracleCalls" -> equivalenceCalls,
    "EquivalenceCounterexampleCount" -> equivalenceCounterexamples,
    "RewriteCount" -> rewriteCount,
    "Programs" -> If[exact, programs, Null],
    "ProgramBits" -> If[exact, programBits, Null],
    "TransitionTableBits" -> tableBits, "PhiBits" -> phiBits,
    "PhiProgramBits" -> totalBits, "CompressionRatio" -> ratio,
    "CompressionReduction" -> If[exact, N[1 - ratio], Null],
    "Observations" -> observations, "Trace" -> trace,
    "RuntimeSeconds" -> N[AbsoluteTime[] - started],
    "AutomatonFallbackRetained" -> True|>
];

ReachableCountB6[table_List, start_Integer] := Module[
  {queue = {start}, seen = <|start -> True|>, state, target,
   k = Length[First[table]]},
  While[Length[queue] > 0,
    state = First[queue]; queue = Rest[queue];
    Do[target = table[[state, action]];
      If[!KeyExistsQ[seen, target], AssociateTo[seen, target -> True];
        AppendTo[queue, target]], {action, k}]];
  Length[seen]
];
RandomReachableTableB6[n_Integer, k_Integer, start_Integer, seed_Integer] := Module[
  {table, attempt = 0}, SeedRandom[seed, Method -> "MersenneTwister"];
  While[attempt < 300, attempt++; table = Transpose@Table[RandomSample[Range[n]], {k}];
    If[ReachableCountB6[table, start] === n, Return[table]]]; $Failed];

RelabelWorldB6[world_Association, table_List, seed_Integer] := Module[
  {n = world["StateCount"], oldToNew, newToOld, result, newTable},
  SeedRandom[seed, Method -> "MersenneTwister"]; oldToNew = RandomSample[Range[n]];
  newToOld = Ordering[oldToNew]; result = Association[world];
  result["StartState"] = oldToNew[[world["StartState"]]];
  result["Phi"] = world["Phi"][[newToOld]];
  newTable = Table[oldToNew[[table[[newToOld[[state]], action]]]],
    {state, n}, {action, world["ActionCount"]}];
  <|"World" -> result, "Table" -> newTable|>
];

CoordinateDatasetHashB6[world_Association, table_List] := Hash[
  ExportString[Sort@Table[{world["Phi"][[state]],
      Table[OracleTargetB6[world, table, state, action],
        {action, world["ActionCount"]}]}, {state, world["StateCount"]}],
    "RawJSON", "Compact" -> True], "SHA256", "HexString"];

Print["S129-B6 TCCT-native online induction R1"];
Print["Prior best programs=False; generator truth visible=False; canonical core modified=False"];

$BasisCacheB6 = <||>;
GetBasisB6[world_Association] := Module[{key, cached, built},
  key = SemanticKeyB6[{world["Phi"], world["CoordinateDimensions"]}];
  cached = Lookup[$BasisCacheB6, key, Null]; If[AssociationQ[cached], Return[cached]];
  built = <|"Basis" -> BuildBlindBasisB6[world["Phi"], world["CoordinateDimensions"]],
    "Predicates" -> BuildPredicatesB6[world["Phi"], world["CoordinateDimensions"]]|>;
  AssociateTo[$BasisCacheB6, key -> built]; built];

formalResults = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  Print["FRESH WORLD START ", world["WorldID"], " n=", world["StateCount"]];
  built = GetBasisB6[world];
  active = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "ACTIVE_TCCT_REWRITE_DISAGREEMENT"];
  passive = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "PASSIVE_FIXED_ORDER"];
  ablation = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
    "REWRITE_DISABLED_ABLATION"];
  Print["FRESH WORLD END ", world["WorldID"], " active=", active["Outcome"],
    " q=", active["MembershipQueryCount"], " passiveQ=", passive["MembershipQueryCount"],
    " noRewrite=", ablation["Outcome"]];
  <|"WorldID" -> world["WorldID"], "StateCount" -> world["StateCount"],
    "CoordinateDimensions" -> world["CoordinateDimensions"],
    "BasisStatistics" -> built["Basis"]["Statistics"],
    "PredicateSemanticCount" -> Length[built["Predicates"]],
    "Active" -> active, "Passive" -> passive, "RewriteDisabled" -> ablation|>,
  {index, Length[publicWorlds]}];

randomResults = Table[
  world = publicWorlds[[index]]; table = RandomReachableTableB6[world["StateCount"],
    world["ActionCount"], world["StartState"], 1298700 + index];
  built = GetBasisB6[world];
  If[table === $Failed,
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> True,
      "FalseCertification" -> False|>,
    randomRun = RunOnlineLearnerB6[world, table, built["Basis"], built["Predicates"],
      "ACTIVE_TCCT_REWRITE_DISAGREEMENT"];
    <|"WorldID" -> world["WorldID"], "GenerationFailed" -> False,
      "Outcome" -> randomRun["Outcome"], "ExactCertified" -> randomRun["ExactCertified"],
      "MembershipQueryCount" -> randomRun["MembershipQueryCount"],
      "CompressionRatio" -> randomRun["CompressionRatio"],
      "FalseCertification" -> False|>],
  {index, Length[publicWorlds]}];

nearLawResults = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  active = formalResults[[index, "Active"]];
  mutated = Map[Identity, table]; oldTarget = mutated[[1, 1]];
  mutated[[1, 1]] = Mod[oldTarget, world["StateCount"]] + 1;
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[world, mutated, active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"], "Applicable" -> TrueQ[active["ExactCertified"]],
    "MutatedState" -> 1, "MutatedAction" -> 1, "OldTarget" -> oldTarget,
    "NewTarget" -> mutated[[1, 1]], "BaseProgramMismatchCount" -> Length[errors],
    "MutationDetected" -> (!TrueQ[active["ExactCertified"]] || Length[errors] >= 1)|>,
  {index, Length[publicWorlds]}];

relabelResults = Table[
  world = publicWorlds[[index]]; table = oracleByID[world["WorldID"]]["TransitionTable"];
  relabeled = RelabelWorldB6[world, table, 1298800 + index];
  active = formalResults[[index, "Active"]];
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[relabeled["World"], relabeled["Table"], active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"],
    "CoordinateDatasetHashInvariant" ->
      (CoordinateDatasetHashB6[world, table] ===
        CoordinateDatasetHashB6[relabeled["World"], relabeled["Table"]]),
    "FrozenProgramStillExact" -> (!TrueQ[active["ExactCertified"]] || Length[errors] === 0)|>,
  {index, Length[publicWorlds]}];

exactCount = Count[Lookup[Lookup[formalResults, "Active"], "ExactCertified"], True];
passiveExactCount = Count[Lookup[Lookup[formalResults, "Passive"], "ExactCertified"], True];
rewriteDisabledExactCount = Count[
  Lookup[Lookup[formalResults, "RewriteDisabled"], "ExactCertified"], True];
activeBeatsPassiveCount = Count[Table[
  TrueQ[formalResults[[index, "Active", "ExactCertified"]]] &&
    TrueQ[formalResults[[index, "Passive", "ExactCertified"]]] &&
    formalResults[[index, "Active", "MembershipQueryCount"]] <
      formalResults[[index, "Passive", "MembershipQueryCount"]],
  {index, Length[formalResults]}], True];
randomExactCount = Count[Lookup[randomResults, "ExactCertified", False], True];
nearLawPass = And @@ Lookup[nearLawResults, "MutationDetected"];
relabelPass = And @@ Flatten[{Lookup[relabelResults, "CoordinateDatasetHashInvariant"],
  Lookup[relabelResults, "FrozenProgramStillExact"]}];

result = <|
  "Stage" -> "S129-B6 TCCT-native online induction R1",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "WolframVersion" -> $Version, "NativeWolframExecution" -> True,
  "CanonicalTCCTModified" -> False, "S128BModified" -> False,
  "PriorBestProgramsLoaded" -> False, "GeneratorProgramsVisibleToLearner" -> False,
  "CandidateGenerationTargetIndependentUntilQueriedEvidence" -> True,
  "CompleteTargetVectorVisibleOnlyToEquivalenceOracle" -> True,
  "TCCTControlRole" -> "counterexample-triggered rewrite -> semantic dedup -> maximum-disagreement query -> exact freeze/fallback",
  "FreshWorldCount" -> Length[formalResults], "ActiveExactCount" -> exactCount,
  "PassiveExactCount" -> passiveExactCount,
  "RewriteDisabledExactCount" -> rewriteDisabledExactCount,
  "ActiveBeatsPassiveCount" -> activeBeatsPassiveCount,
  "RandomControlExactCount" -> randomExactCount,
  "NearLawMutationDetectionPass" -> nearLawPass,
  "StateRelabelingPass" -> relabelPass,
  "NoFixedCompressionThreshold" -> True,
  "AutomatonFallbackRetained" -> True,
  "FormalResults" -> formalResults,
  "RandomControls" -> randomResults,
  "NearLawControls" -> nearLawResults,
  "StateRelabelingControls" -> relabelResults|>;

Export[resultPath, result, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{resultDirectory, "S129B6_per_world.csv"}], Table[
  {row["WorldID"], row["StateCount"], row["Active"]["Outcome"],
    row["Active"]["MembershipQueryCount"], row["Passive"]["Outcome"],
    row["Passive"]["MembershipQueryCount"], row["RewriteDisabled"]["Outcome"],
    row["Active"]["CompressionRatio"]}, {row, formalResults}], "CSV",
  "TableHeadings" -> {{}, {"WorldID", "StateCount", "ActiveOutcome", "ActiveQueries",
    "PassiveOutcome", "PassiveQueries", "RewriteDisabledOutcome", "CompressionRatio"}}];
Export[FileNameJoin[{controlDirectory, "S129B6_random_controls.json"}],
  randomResults, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B6_near_law_controls.json"}],
  nearLawResults, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129B6_state_relabeling_controls.json"}],
  relabelResults, "RawJSON", "Compact" -> False];
Print["S129-B6 COMPLETE activeExact=", exactCount, "/", Length[formalResults],
  " passiveExact=", passiveExactCount, " noRewriteExact=", rewriteDisabledExactCount,
  " randomExact=", randomExactCount];
