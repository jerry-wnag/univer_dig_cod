ClearAll["Global`*"];

rootDirectory = DirectoryName[DirectoryName[$InputFileName]];
protocolPath = FileNameJoin[{rootDirectory, "protocol", "frozen_protocol.json"}];
publicPath = FileNameJoin[{rootDirectory, "input", "public_tasks.json"}];
resultPath = FileNameJoin[{rootDirectory, "results", "kernel_intervention_result.json"}];
oracleResponderPath = FileNameJoin[{rootDirectory, "source", "oracle_responder.py"}];
oracleResponsePath = FileNameJoin[{rootDirectory, "oracle", "runtime_response.json"}];
oracleRequestPath = FileNameJoin[{rootDirectory, "oracle", "runtime_request.json"}];
oracleLogPath = FileNameJoin[{rootDirectory, "oracle", "query_log.jsonl"}];
protocol = Import[protocolPath, "RawJSON"];
public = Import[publicPath, "RawJSON"];
protocolHash = IntegerString[FileHash[protocolPath, "SHA256"], 16, 64];
If[public["ProtocolSHA256"] =!= protocolHash,
  Print["FATAL: public tasks do not match frozen protocol"]; Exit[2]];
runnerHash = IntegerString[FileHash[$InputFileName, "SHA256"], 16, 64];
If[runnerHash =!= protocol["FrozenWolframRunnerSHA256"],
  Print["FATAL: Wolfram runner differs from frozen protocol"]; Exit[3]];
oracleResponderHash = IntegerString[FileHash[oracleResponderPath, "SHA256"], 16, 64];
If[oracleResponderHash =!= protocol["FrozenOracleResponderSHA256"],
  Print["FATAL: oracle responder differs from frozen protocol"]; Exit[4]];

historicalB6Path = FileNameJoin[Prepend[
  StringSplit[protocol["HistoricalB6RelativePath"], "/"], rootDirectory]];
If[IntegerString[FileHash[historicalB6Path, "SHA256"], 16, 64] =!=
    protocol["HistoricalB6SHA256"],
  Print["FATAL: historical B6 hash mismatch"]; Exit[5]];
b6Text = Import[historicalB6Path, "Text"];
b6Start = First@First@StringPosition[b6Text, "SemanticKeyB6[values_List]"];
b6End = First@First@StringPosition[b6Text,
  "SetAttributes[AddArithmeticB6, HoldFirst]"];
ToExpression[StringTake[b6Text, {b6Start, b6End - 1}], InputForm];

backgroundColor = protocol["BackgroundColor"];
coefficientValues = protocol["AffineCoefficientValues"];
constantValues = protocol["AffineConstantValues"];
maximumAffineTerms = protocol["MaximumAffineVariableTerms"];
minimumConceptSupport = protocol["MinimumDistinctTaskSupportForConcept"];
maximumActiveQueries = protocol["MaximumActiveQueriesPerTask"];
maximumGeneratedInterventions = protocol["KernelMaximumGeneratedInterventionsPerRound"];

ASTKey136[ast_] := ToString[ast, InputForm];

GridCells136[grid_List] := Flatten[Table[
  If[grid[[row, column]] === backgroundColor, Nothing,
    {row, column, grid[[row, column]]}],
  {row, Length[grid]}, {column, Length[First[grid]]}], 1];

RelationValue136[{"SameColor"}, left_List, right_List] := left[[3]] === right[[3]];
RelationValue136[{"EdgeAdjacent4"}, left_List, right_List] :=
  Abs[left[[1]] - right[[1]]] + Abs[left[[2]] - right[[2]]] === 1;
RelationValue136[{"DiagonalAdjacent"}, left_List, right_List] :=
  Abs[left[[1]] - right[[1]]] === 1 && Abs[left[[2]] - right[[2]]] === 1;
RelationValue136[{"And", left_, right_}, a_List, b_List] :=
  RelationValue136[left, a, b] && RelationValue136[right, a, b];
RelationValue136[{"Or", left_, right_}, a_List, b_List] :=
  RelationValue136[left, a, b] || RelationValue136[right, a, b];

RelationNodes136[ast_List] := If[MemberQ[{"And", "Or"}, First[ast]],
  1 + RelationNodes136[ast[[2]]] + RelationNodes136[ast[[3]]], 1];
RelationBits136[{"SameColor"}] := 3;
RelationBits136[{"EdgeAdjacent4"}] := 4;
RelationBits136[{"DiagonalAdjacent"}] := 4;
RelationBits136[{op : ("And" | "Or"), left_, right_}] :=
  3 + RelationBits136[left] + RelationBits136[right];

RelationSyntax136[] := {
  {"SameColor"},
  {"And", {"SameColor"}, {"EdgeAdjacent4"}},
  {"And", {"SameColor"}, {"DiagonalAdjacent"}},
  {"And", {"SameColor"},
    {"Or", {"EdgeAdjacent4"}, {"DiagonalAdjacent"}}}
};

PartitionCells136[grid_List, relationAST_List] := Module[
  {cells = GridCells136[grid], edges, graph, components},
  edges = Flatten@Table[
    If[RelationValue136[relationAST, cells[[i]], cells[[j]]],
      UndirectedEdge[i, j], Nothing],
    {i, Length[cells]}, {j, i + 1, Length[cells]}];
  graph = Graph[Range[Length[cells]], edges];
  components = ConnectedComponents[graph];
  Sort[Function[component,
    Sort[(cells[[#, {1, 2}]] &) /@ component]] /@ components]
];

VisibleInputGrids136[task_Association] := Join[
  (Lookup[#, "Input"] &) /@ task["InitialTrain"],
  (Lookup[#, "Input"] &) /@ task["Test"],
  (Lookup[#, "Input"] &) /@ task["QueryPool"]];

TrainCount136[task_Association] := Length[task["InitialTrain"]];
TestValueIndex136[task_Association] := TrainCount136[task] + 1;
QueryValueIndex136[task_Association, queryIndex_Integer] :=
  TrainCount136[task] + 1 + queryIndex;

RelationCandidates136[task_Association] := Module[
  {grids = VisibleInputGrids136[task], store = <||>, ast, signature,
   expression, key},
  Do[
    signature = PartitionCells136[#, ast] & /@ grids;
    key = SemanticKeyB6[signature];
    expression = <|"AST" -> ast, "Nodes" -> RelationNodes136[ast],
      "Bits" -> RelationBits136[ast], "Values" -> signature|>;
    If[!KeyExistsQ[store, key] ||
        {expression["Bits"], expression["Nodes"], ASTKey136[ast]} <
        {store[key]["Bits"], store[key]["Nodes"], ASTKey136[store[key]["AST"]]},
      AssociateTo[store, key -> expression]],
    {ast, RelationSyntax136[]}];
  SortBy[Values[store], {#["Bits"], #["Nodes"], ASTKey136[#["AST"]]} &]
];

MaterializeRecord136[grid_List, relationAST_List] := Module[
  {components = PartitionCells136[grid, relationAST], objects, colors, rows, cols},
  objects = MapIndexed[Function[{component, index},
    colors = DeleteDuplicates[(grid[[#[[1]], #[[2]]]] &) /@ component];
    If[Length[colors] =!= 1, Return[$Failed]];
    rows = component[[All, 1]]; cols = component[[All, 2]];
    <|"ObjectID" -> "object-" <> ToString[First[index]],
      "Color" -> First[colors], "Area" -> Length[component],
      "Cells" -> component,
      "BoundingBox" -> {Min[rows], Min[cols], Max[rows], Max[cols]}|>
  ], components];
  If[MemberQ[objects, $Failed], $Failed,
    <|"Grid" -> grid, "Objects" -> objects|>]
];

ObjectAttribute136[obj_Association, "Area"] := obj["Area"];
ObjectAttribute136[obj_Association, "Color"] := obj["Color"];
ObjectAttribute136[obj_Association, "RowMin"] := obj["BoundingBox"][[1]];
ObjectAttribute136[obj_Association, "ColMin"] := obj["BoundingBox"][[2]];

SelectObjectIndex136[record_Association, selector_List] := Module[
  {values, extreme, positions},
  values = ObjectAttribute136[#, selector[[3]]] & /@ record["Objects"];
  extreme = If[selector[[2]] === "Min", Min[values], Max[values]];
  positions = Flatten@Position[values, extreme];
  If[Length[positions] === 1, First[positions], 0]
];

SelectorSyntax136[] := Flatten[Table[
  {"ArgExtremum", direction, attribute},
  {direction, protocol["SelectorDirections"]},
  {attribute, protocol["SelectorAttributes"]}], 1];

AffineNodes136[ast_List] := 1 + Length[ast[[3]]];
AffineBits136[ast_List] := 6 + 5 Length[ast[[3]]];
EvalAffine136[ast_List, object_Association, cell_List] := Module[
  {bbox = object["BoundingBox"], values},
  values = <|"r" -> cell[[1]], "c" -> cell[[2]],
    "rmin" -> bbox[[1]], "cmin" -> bbox[[2]],
    "rmax" -> bbox[[3]], "cmax" -> bbox[[4]]|>;
  ast[[2]] + Total[(values[#[[1]]] #[[2]]) & /@ ast[[3]]]
];

BuildAffineExpressions136[] := Module[
  {variables = protocol["AffineVariables"], rows = {}, subset, signs, terms, ast},
  Do[
    Do[
      If[k === 0,
        AppendTo[rows, {"Affine", constant, {}}],
        Do[
          terms = MapThread[List, {subset, signs}];
          ast = {"Affine", constant, terms};
          AppendTo[rows, ast],
          {signs, Tuples[coefficientValues, k]}]],
      {subset, Subsets[variables, {k}]}],
    {constant, constantValues}, {k, 0, maximumAffineTerms}];
  SortBy[DeleteDuplicates[rows],
    {AffineBits136[#], AffineNodes136[#], ASTKey136[#]} &]
];

affineExpressions = BuildAffineExpressions136[];

ExpectedTargetCells136[inputGrid_List, outputGrid_List, record_Association,
  selectedIndex_Integer] := Module[
  {outsideObjects, outsideCells, selectedColor, expectedCells, outputCells},
  outsideObjects = Delete[record["Objects"], selectedIndex];
  outsideCells = If[Length[outsideObjects] === 0, {},
    DeleteDuplicates@Flatten[Lookup[outsideObjects, "Cells"], 1]];
  If[!And @@ ((outputGrid[[#[[1]], #[[2]]]] ===
          inputGrid[[#[[1]], #[[2]]]]) & /@ outsideCells), Return[$Failed]];
  selectedColor = record["Objects"][[selectedIndex]]["Color"];
  outputCells = GridCells136[outputGrid];
  expectedCells = Select[outputCells,
    !MemberQ[outsideCells, #[[{1, 2}]]] &];
  If[!And @@ (#[[3]] === selectedColor & /@ expectedCells), Return[$Failed]];
  Sort[expectedCells[[All, {1, 2}]]]
];

MarginalCompatible136[task_Association, records_List, selector_List,
  mode_String, ast_List, axis_Integer] := Module[
  {trainCount = Length[task["InitialTrain"]], index, object, sourceCells,
   expected, mappedValues, sourceValues, expectedValues},
  And @@ Table[
    index = SelectObjectIndex136[records[[i]], selector];
    If[index === 0, Return[False]];
    object = records[[i]]["Objects"][[index]];
    sourceCells = object["Cells"];
    expected = ExpectedTargetCells136[task["InitialTrain"][[i]]["Input"],
      task["InitialTrain"][[i]]["Output"], records[[i]], index];
    If[expected === $Failed, Return[False]];
    mappedValues = DeleteDuplicates[
      EvalAffine136[ast, object, #] & /@ sourceCells];
    sourceValues = DeleteDuplicates[sourceCells[[All, axis]]];
    expectedValues = DeleteDuplicates[expected[[All, axis]]];
    If[mode === "ReplaceSelected",
      Sort[mappedValues] === Sort[expectedValues],
      Sort[Union[sourceValues, mappedValues]] === Sort[expectedValues]],
    {i, trainCount}]
];

ApplyGeometry136[record_Association, selector_List, mode_String,
  rowAST_List, colAST_List] := Module[
  {index, object, sourceCells, mappedCells, grid, color, height, width},
  index = SelectObjectIndex136[record, selector];
  If[index === 0, Return[$Failed]];
  object = record["Objects"][[index]];
  sourceCells = object["Cells"];
  mappedCells = DeleteDuplicates@Map[
    {EvalAffine136[rowAST, object, #], EvalAffine136[colAST, object, #]} &,
    sourceCells];
  height = Length[record["Grid"]]; width = Length[First[record["Grid"]]];
  If[!VectorQ[mappedCells, MatchQ[#, {_Integer, _Integer}] &] ||
      !And @@ (1 <= #[[1]] <= height && 1 <= #[[2]] <= width & /@ mappedCells),
    Return[$Failed]];
  grid = record["Grid"];
  color = object["Color"];
  If[mode === "ReplaceSelected",
    Do[grid[[cell[[1]], cell[[2]]]] = backgroundColor, {cell, sourceCells}]];
  If[!And @@ (MemberQ[{backgroundColor, color},
        grid[[#[[1]], #[[2]]]]] & /@ mappedCells), Return[$Failed]];
  Do[grid[[cell[[1]], cell[[2]]]] = color, {cell, mappedCells}];
  grid
];

ProgramNodes136[ast_List] := 1 + RelationNodes136[ast[[2]]] + 1 +
  AffineNodes136[ast[[5]]] + AffineNodes136[ast[[6]]];
ProgramBits136[ast_List] := 17 + RelationBits136[ast[[2]]] +
  AffineBits136[ast[[5]]] + AffineBits136[ast[[6]]];

AddGeometryProgram136[store_, records_List, ast_List] := Module[
  {values, expression},
  values = ApplyGeometry136[#, ast[[3]], ast[[4]], ast[[5]], ast[[6]]] & /@ records;
  If[MemberQ[values, $Failed], Return[False]];
  expression = MakeExprB6[ast, ProgramNodes136[ast], ProgramBits136[ast],
    values, "OpenAffineSetProgram"];
  AddBestB6[store, expression]; True
];
SetAttributes[AddGeometryProgram136, HoldFirst];

BuildShadowExpression137[records_List, ast_List] := Module[{values},
  values = ApplyGeometry136[#, ast[[3]], ast[[4]], ast[[5]], ast[[6]]] & /@ records;
  If[MemberQ[values, $Failed], Return[$Failed]];
  MakeExprB6[ast, ProgramNodes136[ast], ProgramBits136[ast],
    values, "PreDedupExactShadowProgram"]
];

DedupShadowCandidates137[expressions_List] := Module[{store = <||>},
  Do[AddBestB6[store, expression], {expression, expressions}];
  SortBy[Values[store],
    {#["Bits"], #["Nodes"], ASTKey136[#["AST"]]} &]
];

ExactTraining136[task_Association, expression_Association] :=
  Take[expression["Values"], Length[task["InitialTrain"]]] ===
    Lookup[task["InitialTrain"], "Output"];

BuildOpenCandidates136[task_Association] := Module[
  {relations = RelationCandidates136[task], grids = VisibleInputGrids136[task],
   selectors = SelectorSyntax136[], store = <||>, records, selector, mode,
   rowExpressions, colExpressions, ast, rawPairs = 0, relationAudit = {},
   expression, shadowRows = {}, candidates, minimumBits, retainedShadows},
  Do[
    records = MaterializeRecord136[#, relationExpression["AST"]] & /@ grids;
    If[MemberQ[records, $Failed], Continue[]];
    Do[
      If[MemberQ[SelectObjectIndex136[#, selector] & /@ records, 0], Continue[]];
      Do[
        rowExpressions = Select[affineExpressions,
          MarginalCompatible136[task, records, selector, mode, #, 1] &];
        colExpressions = Select[affineExpressions,
          MarginalCompatible136[task, records, selector, mode, #, 2] &];
        Do[
          rawPairs++;
          ast = {"GeometryProgram", relationExpression["AST"], selector,
            mode, rowAST, colAST};
          AddGeometryProgram136[store, records, ast];
          expression = BuildShadowExpression137[records, ast];
          If[AssociationQ[expression] && ExactTraining136[task, expression],
            AppendTo[shadowRows, expression]],
          {rowAST, rowExpressions}, {colAST, colExpressions}];
        AppendTo[relationAudit, <|"RelationAST" -> relationExpression["AST"],
          "Selector" -> selector, "Mode" -> mode,
          "RowMarginalCount" -> Length[rowExpressions],
          "ColMarginalCount" -> Length[colExpressions]|>],
        {mode, protocol["SetCombinationModes"]}],
      {selector, selectors}],
    {relationExpression, relations}];
  candidates = SortBy[Select[Values[store], ExactTraining136[task, #] &],
    {#["Bits"], #["Nodes"], ASTKey136[#["AST"]]} &];
  shadowRows = DeleteDuplicatesBy[shadowRows, ASTKey136[#["AST"]] &];
  retainedShadows = If[Length[shadowRows] === 0, {},
    minimumBits = Min[Lookup[shadowRows, "Bits"]];
    Take[SortBy[Select[shadowRows,
        #["Bits"] <= minimumBits + protocol["ShadowMDLSlackBits"] &],
      {#["Bits"], #["Nodes"], ASTKey136[#["AST"]]} &],
      UpTo[protocol["ShadowMaximumExactPrograms"]]]];
  retainedShadows = DeleteDuplicatesBy[Join[candidates, retainedShadows],
    ASTKey136[#["AST"]] &];
  <|"Candidates" -> candidates, "ShadowCandidates" -> retainedShadows,
    "RawExactShadowProgramCount" -> Length[shadowRows],
    "RetainedShadowProgramCount" -> Length[retainedShadows],
    "ShadowMDLSlackBits" -> protocol["ShadowMDLSlackBits"],
    "RawExpressionCount" -> Length[affineExpressions],
    "RawProgramPairCount" -> rawPairs,
    "RelationCandidateCount" -> Length[relations],
    "MarginalAudit" -> relationAudit|>
];

BuildLibraryCandidates136[task_Association, library_List] := Module[
  {relations = RelationCandidates136[task], grids = VisibleInputGrids136[task],
   selectors = SelectorSyntax136[], store = <||>, records, ast, raw = 0},
  Do[
    records = MaterializeRecord136[#, relationExpression["AST"]] & /@ grids;
    If[MemberQ[records, $Failed], Continue[]];
    Do[
      If[MemberQ[SelectObjectIndex136[#, selector] & /@ records, 0], Continue[]];
      Do[
        raw++;
        ast = {"GeometryProgram", relationExpression["AST"], selector,
          concept["Skeleton"][[1]], concept["Skeleton"][[2]],
          concept["Skeleton"][[3]]};
        AddGeometryProgram136[store, records, ast],
        {concept, library}],
      {selector, selectors}],
    {relationExpression, relations}];
  <|"Candidates" -> SortBy[Select[Values[store], ExactTraining136[task, #] &],
      {#["Bits"], #["Nodes"], ASTKey136[#["AST"]]} &],
    "RawLibraryInstantiationCount" -> raw,
    "RelationCandidateCount" -> Length[relations]|>
];

PredictionGroups136[task_Association, candidates_List] := GatherBy[candidates,
  #["Values"][[TestValueIndex136[task]]] &];
Skeleton136[programAST_List] := programAST[[{4, 5, 6}]];
ConceptKey136[skeleton_List] := ASTKey136[skeleton];
ConceptID136[skeleton_List] := "concept-" <> StringTake[
  IntegerString[Hash[ConceptKey136[skeleton], "SHA256"], 16, 64], 12];

GridDigest137[grid_List] := IntegerString[
  Hash[StringRiffle[ToString /@ Flatten[grid], ","], "SHA256"], 16, 64];

NormalizeShape137[cells_List] := Module[{mins = Min /@ Transpose[cells]},
  Sort[(# - mins) & /@ cells]];

ExpandOneShape137[shape_List] := Module[{neighbors},
  neighbors = DeleteDuplicates@Flatten[
    Table[cell + delta, {cell, shape},
      {delta, {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}}], 1];
  DeleteDuplicates[
    NormalizeShape137[Append[shape, #]] & /@ Select[neighbors, !MemberQ[shape, #] &]]
];

ExpandShapes137[shapes_List] := DeleteDuplicates@Flatten[
  ExpandOneShape137 /@ shapes, 1];

BuildKernelShapes137[] := Module[{areas, shapes},
  areas = protocol["KernelSynthesizedObjectAreas"];
  DeleteDuplicates@Flatten[Table[
    shapes = Nest[ExpandShapes137, {{{0, 0}}}, area - 1];
    Take[SortBy[
      Select[shapes,
        1 + Max[#[[All, 1]]] <= protocol["KernelMaximumShapeSpan"] &&
        1 + Max[#[[All, 2]]] <= protocol["KernelMaximumShapeSpan"] &],
      ToString[#, InputForm] &],
      UpTo[protocol["KernelMaximumShapesPerArea"]]],
    {area, areas}], 1]
];

kernelShapes137 = BuildKernelShapes137[];

ShapeAxisSymmetric138FQ[intervention_Association, axis_String] := Module[
  {shape = intervention["Shape"], maximumRow, maximumColumn, reflected},
  maximumRow = Max[shape[[All, 1]]];
  maximumColumn = Max[shape[[All, 2]]];
  reflected = Which[
    axis === "LEFT_RIGHT", ({#[[1]], maximumColumn - #[[2]]} &) /@ shape,
    axis === "TOP_BOTTOM", ({maximumRow - #[[1]], #[[2]]} &) /@ shape,
    True, Return[False]
  ];
  Sort[shape] === Sort[reflected]
];

InferKernelScaffold137[task_Association, candidates_List] := Module[
  {grid, record, eligible, areas, index, object, scaffold},
  If[Length[candidates] === 0, Return[$Failed]];
  grid = task["InitialTrain"][[1]]["Input"];
  record = MaterializeRecord136[grid,
    {"And", {"SameColor"}, {"EdgeAdjacent4"}}];
  If[!AssociationQ[record], Return[$Failed]];
  eligible = Select[Range[Length[record["Objects"]]],
    !MemberQ[{6, 9}, record["Objects"][[#]]["Color"]] &];
  If[Length[eligible] === 0, Return[$Failed]];
  areas = record["Objects"][[#]]["Area"] & /@ eligible;
  index = eligible[[First@First@Position[areas, Max[areas]]]];
  object = record["Objects"][[index]];
  scaffold = grid;
  Do[scaffold[[cell[[1]], cell[[2]]]] = backgroundColor,
    {cell, object["Cells"]}];
  <|"Scaffold" -> scaffold, "Color" -> object["Color"],
    "InferredBy" -> "LARGEST_NON_MARKER_SAME_COLOR_EDGE_COMPONENT"|>
];

KernelInterventionUniverse137[task_Association, candidates_List,
    usedInputHashes_List] := Module[
  {inferred, scaffold, color, forbiddenHashes, rows, shape, height, width,
   grid, cells, digest, envelope, gridHeight, gridWidth, maximumTop,
   maximumLeft, supportTrapRows, supportTrapQuota},
  inferred = InferKernelScaffold137[task, candidates];
  If[inferred === $Failed, Return[{}]];
  scaffold = inferred["Scaffold"]; color = inferred["Color"];
  gridHeight = Length[scaffold];
  gridWidth = Length[First[scaffold]];
  forbiddenHashes = Join[usedInputHashes,
    GridDigest137 /@ Join[
      (#["Input"] &) /@ task["InitialTrain"],
      (#["Input"] &) /@ task["Test"]]];
  rows = Reap[
    Do[
      height = 1 + Max[shape[[All, 1]]];
      width = 1 + Max[shape[[All, 2]]];
      envelope = Max[height, width];
      maximumTop = gridHeight - envelope - protocol["ContextTranslationOffset"];
      maximumLeft = gridWidth - envelope - 1;
      Do[
        cells = (# + {top, left}) & /@ shape;
        If[And @@ (scaffold[[#[[1]], #[[2]]]] === backgroundColor & /@ cells),
          grid = scaffold;
          Do[grid[[cell[[1]], cell[[2]]]] = color, {cell, cells}];
          digest = GridDigest137[grid];
          If[!MemberQ[forbiddenHashes, digest], Sow[<|
            "Input" -> grid, "InputSHA256" -> digest,
            "Shape" -> shape, "TopLeft" -> {top, left},
            "Derivation" -> "PROOF_CONSTRUCTED_SYMMETRY_PRESERVING_SUPPORT_TRAP"|>]]],
        {top, 1, maximumTop}, {left, 1, maximumLeft}],
      {shape, kernelShapes137}]][[2]];
  rows = If[Length[rows] === 0, {}, First[rows]];
  supportTrapQuota = protocol["SupportTrapDoubleNeutralQuota"];
  supportTrapRows = Take[SortBy[Select[rows,
      ShapeAxisSymmetric138FQ[#, "LEFT_RIGHT"] &&
      ShapeAxisSymmetric138FQ[#, "TOP_BOTTOM"] &],
    #["InputSHA256"] &], UpTo[supportTrapQuota]];
  If[Length[supportTrapRows] =!= supportTrapQuota, Return[{}]];
  supportTrapRows
];

PredictKernelIntervention137[candidate_Association, grid_List] := Module[
  {ast = candidate["AST"], record, prediction},
  record = MaterializeRecord136[grid, ast[[2]]];
  If[!AssociationQ[record], Return[{"INVALID_PROGRAM_OUTPUT"}]];
  prediction = ApplyGeometry136[record, ast[[3]], ast[[4]], ast[[5]], ast[[6]]];
  If[prediction === $Failed, {"INVALID_PROGRAM_OUTPUT"}, prediction]
];

SemanticDecisionState138D[task_Association, candidates_List,
    universe_List] := Module[
  {testInput, rawMatrix, rawTestPredictions, signatures, groups,
   representatives, classMatrix, classTestPredictions},
  If[Length[candidates] === 0, Return[<|
    "RawCandidateCount" -> 0, "SemanticClassCount" -> 0,
    "DecisionClassCount" -> 0, "RawPredictionMatrix" -> {},
    "ClassPredictionMatrix" -> {}, "ClassTestPredictions" -> {}|>]];
  testInput = task["Test"][[1]]["Input"];
  rawMatrix = Table[
    PredictKernelIntervention137[candidate, intervention["Input"]],
    {candidate, candidates}, {intervention, universe}];
  rawTestPredictions =
    PredictKernelIntervention137[#, testInput] & /@ candidates;
  signatures = MapThread[
    ToString[{#1, #2}, InputForm] &, {rawMatrix, rawTestPredictions}];
  groups = GatherBy[Range[Length[candidates]], signatures[[#]] &];
  representatives = First /@ groups;
  classMatrix = rawMatrix[[representatives]];
  classTestPredictions = rawTestPredictions[[representatives]];
  <|"RawCandidateCount" -> Length[candidates],
    "SemanticClassCount" -> Length[groups],
    "DecisionClassCount" -> Length[DeleteDuplicates[
      ToString[#, InputForm] & /@ classTestPredictions]],
    "RawPredictionMatrix" -> rawMatrix,
    "ClassPredictionMatrix" -> classMatrix,
    "ClassTestPredictions" -> classTestPredictions|>
];

DecisionAwareScoreRows138D[state_Association, universe_List,
    usedInputHashes_List] := Module[
  {rows = {}, classPredictions, outputGroups, branchDecisionCounts,
   branchSemanticCounts, rawPredictions, intervention},
  Do[
    intervention = universe[[queryIndex]];
    If[MemberQ[usedInputHashes, intervention["InputSHA256"]], Continue[]];
    classPredictions = state["ClassPredictionMatrix"][[All, queryIndex]];
    outputGroups = GatherBy[Range[state["SemanticClassCount"]],
      ToString[classPredictions[[#]], InputForm] &];
    If[Length[outputGroups] <= 1, Continue[]];
    branchDecisionCounts = Length[DeleteDuplicates[
        ToString[state["ClassTestPredictions"][[#]], InputForm] & /@ #]] & /@
      outputGroups;
    branchSemanticCounts = Length /@ outputGroups;
    rawPredictions = state["RawPredictionMatrix"][[All, queryIndex]];
    AppendTo[rows, Join[intervention, <|
      "Predictions" -> rawPredictions,
      "WorstCaseRemainingDecisionClassCount" -> Max[branchDecisionCounts],
      "WorstCaseRemainingSemanticClassCount" -> Max[branchSemanticCounts],
      "OutputBranchCount" -> Length[outputGroups],
      "BranchDecisionClassCounts" -> Sort[branchDecisionCounts, Greater],
      "BranchSemanticClassCounts" -> Sort[branchSemanticCounts, Greater],
      "GeneratedInterventionUniverseCount" -> Length[universe]|>]],
    {queryIndex, Length[universe]}];
  SortBy[rows, {#["WorstCaseRemainingDecisionClassCount"],
      #["WorstCaseRemainingSemanticClassCount"], #["InputSHA256"]} &]
];

RunOracleCommand136[mode_String, taskID_String : "NONE", queryID_String : "NONE"] :=
  Module[{command},
    If[!StringQ[Environment["TCCT_PACKAGE_ROOT_B64"]] ||
        !StringQ[Environment["TCCT_PYTHON_ENGINE"]],
      Print["FATAL: ASCII oracle bridge environment is not configured"]; Exit[18]];
    command = "set TCCT_ORACLE_MODE=" <> mode <>
      "&&set TCCT_TASK=" <> taskID <>
      "&&set TCCT_QUERY=" <> queryID <>
      "&&" <> protocol["PowerShellEngine"] <>
      " -NoProfile -NonInteractive -EncodedCommand " <>
      protocol["OracleBridgeEncodedCommand"];
    Run[command]
  ];

CallOracle137[taskID_String, queryID_String, input_List] := Module[
  {exitCode, response, request, inputHash = GridDigest137[input]},
  If[!StringMatchQ[taskID, RegularExpression["[A-Z0-9_]+"]] ||
      !StringMatchQ[queryID, RegularExpression["KQ[0-9]+"]],
    Print["FATAL: unsafe oracle identifier"]; Exit[19]];
  request = <|"ProtocolSHA256" -> protocolHash, "TaskID" -> taskID,
    "QueryID" -> queryID, "Input" -> input, "InputSHA256" -> inputHash,
    "GeneratedByTCCTKernel" -> True,
    "TestOutputAccessed" -> False, "GeneratorFamilyAccessed" -> False|>;
  Export[oracleRequestPath, request, "RawJSON", "Compact" -> False];
  exitCode = RunOracleCommand136["query", taskID, queryID];
  If[exitCode =!= 0,
    Print["FATAL: oracle process failed for ", taskID, " ", queryID]; Exit[20]];
  response = Import[oracleResponsePath, "RawJSON"];
  If[response["ProtocolSHA256"] =!= protocolHash ||
      response["TaskID"] =!= taskID || response["QueryID"] =!= queryID ||
      response["InputSHA256"] =!= inputHash ||
      !TrueQ[response["GeneratedByTCCTKernel"]] ||
      TrueQ[response["TestOutputAccessed"]] ||
      TrueQ[response["GeneratorFamilyAccessed"]],
    Print["FATAL: invalid oracle response boundary"]; Exit[21]];
  response
];

EvaluateTask136[task_Association, searchMode_String, library_List] := Module[
  {build, initialCandidates, candidates, initialGroups, groups, status,
    committed, primary, groupRows, conceptID = Null, queryTrace = {},
    usedInputHashes = {}, scoreRows = {}, best, response, candidatesBefore,
    queryID, keepMask, initialShadowCandidates, shadowCandidates,
    unresolvedShadowDisagreement = False, initialCounterfactualOpportunity = False,
    testIndex = TestValueIndex136[task], runtime, timedValue, fullUniverse,
    state, initialState, decisionCertified = False, modelIdentified = False,
    stopReason = "NOT_STARTED", semanticBefore, decisionBefore,
    remainingInformativeQueryCount = 0},
  {runtime, timedValue} = AbsoluteTiming[
    build = If[searchMode === "TRANSFER_LIBRARY_ONLY",
      BuildLibraryCandidates136[task, library], BuildOpenCandidates136[task]];
    initialCandidates = build["Candidates"];
    candidates = initialCandidates;
    initialShadowCandidates = Lookup[build, "ShadowCandidates", initialCandidates];
    shadowCandidates = initialShadowCandidates;
    initialGroups = PredictionGroups136[task, candidates];
    groups = initialGroups;
    fullUniverse = If[Length[shadowCandidates] > 0,
      KernelInterventionUniverse137[task, shadowCandidates, {}], {}];
    state = SemanticDecisionState138D[task, shadowCandidates, fullUniverse];
    initialState = state;
    decisionCertified = state["DecisionClassCount"] === 1;
    modelIdentified = state["SemanticClassCount"] === 1;
    If[searchMode === "ACTIVE_OPEN_SEARCH" && !decisionCertified,
      scoreRows = DecisionAwareScoreRows138D[state, fullUniverse, usedInputHashes];
      initialCounterfactualOpportunity = Length[scoreRows] > 0];
    While[searchMode === "ACTIVE_OPEN_SEARCH" && Length[shadowCandidates] > 0 &&
        !decisionCertified && Length[usedInputHashes] < maximumActiveQueries &&
        Length[usedInputHashes] < Length[fullUniverse],
      scoreRows = DecisionAwareScoreRows138D[state, fullUniverse, usedInputHashes];
      If[Length[scoreRows] === 0, stopReason = "NO_INFORMATIVE_QUERY"; Break[]];
      best = First[scoreRows]; candidatesBefore = Length[shadowCandidates];
      semanticBefore = state["SemanticClassCount"];
      decisionBefore = state["DecisionClassCount"];
      queryID = "KQ" <> IntegerString[Length[usedInputHashes] + 1, 10, 2];
      response = CallOracle137[task["TaskID"], queryID, best["Input"]];
      keepMask = (# === response["Output"] &) /@ best["Predictions"];
      shadowCandidates = Pick[shadowCandidates, keepMask, True];
      candidates = DedupShadowCandidates137[shadowCandidates];
      AppendTo[usedInputHashes, best["InputSHA256"]];
      state = SemanticDecisionState138D[task, shadowCandidates, fullUniverse];
      decisionCertified = state["DecisionClassCount"] === 1;
      modelIdentified = state["SemanticClassCount"] === 1;
      AppendTo[queryTrace, <|
        "QueryNumber" -> Length[usedInputHashes],
        "QueryID" -> queryID,
        "GeneratedByTCCTKernel" -> True,
        "KernelGeneratedInput" -> best["Input"],
        "InputSHA256" -> best["InputSHA256"],
        "Shape" -> best["Shape"], "TopLeft" -> best["TopLeft"],
        "Derivation" -> best["Derivation"],
        "SelectedScore" -> KeyDrop[best,
          {"Input", "Predictions", "Shape", "TopLeft", "Derivation"}],
        "CandidateCountBefore" -> candidatesBefore,
        "SemanticClassCountBefore" -> semanticBefore,
        "DecisionClassCountBefore" -> decisionBefore,
        "OracleOutput" -> response["Output"],
        "OracleOutputSHA256" -> IntegerString[
          Hash[ToString[response["Output"], InputForm], "SHA256"], 16, 64],
        "CandidateCountAfter" -> Length[shadowCandidates],
        "SemanticClassCountAfter" -> state["SemanticClassCount"],
        "DecisionClassCountAfter" -> state["DecisionClassCount"],
        "DecisionCertifiedAfter" -> decisionCertified,
        "ModelIdentifiedAfter" -> modelIdentified,
        "TestOutputAccessed" -> False,
        "GeneratorFamilyAccessed" -> False|>];
      groups = PredictionGroups136[task, candidates]];
    unresolvedShadowDisagreement = state["SemanticClassCount"] > 1;
    stopReason = Which[
      Length[shadowCandidates] === 0, "NO_EXACT_MODEL_REMAINS",
      decisionCertified && modelIdentified, "MODEL_IDENTIFIED",
      decisionCertified, "DECISION_CERTIFIED_MODEL_UNRESOLVED",
      stopReason === "NO_INFORMATIVE_QUERY", stopReason,
      Length[usedInputHashes] >= Length[fullUniverse], "INTERVENTION_UNIVERSE_EXHAUSTED",
      Length[usedInputHashes] >= maximumActiveQueries, "RESOURCE_SAFETY_CAP_REACHED",
      True, "DECISION_AMBIGUOUS"];
    remainingInformativeQueryCount = If[
      stopReason === "NO_INFORMATIVE_QUERY", 0,
      Length[DecisionAwareScoreRows138D[state, fullUniverse, usedInputHashes]]
    ];
  ];
  committed = Length[shadowCandidates] > 0 && decisionCertified;
  status = Which[
    Length[initialCandidates] === 0, "NO_EXACT_INITIAL_TRAIN_MODEL",
    Length[candidates] === 0, "NO_EXACT_MODEL_AFTER_ACTIVE_QUERY",
    committed && modelIdentified, "MODEL_IDENTIFIED_DECISION_CERTIFIED",
    committed, "DECISION_CERTIFIED_MODEL_UNRESOLVED",
    stopReason === "NO_INFORMATIVE_QUERY", "DECISION_AMBIGUOUS_NO_INFORMATIVE_QUERY",
    True, "DECISION_AMBIGUOUS_RESOURCE_STOP"];
  primary = If[Length[candidates] > 0, First[candidates], Null];
  If[AssociationQ[primary] && modelIdentified,
    conceptID = Lookup[SelectFirst[library,
      ConceptKey136[#["Skeleton"]] === ConceptKey136[Skeleton136[primary["AST"]]] &,
      <||>], "ConceptID", Null]];
  groupRows = MapIndexed[Function[{group, index}, <|
    "PredictionIndex" -> First[index],
    "Prediction" -> First[group]["Values"][[testIndex]],
    "SupportingExactModelCount" -> Length[group],
    "RepresentativeAST" -> First[group]["AST"]|>], groups];
  <|"TaskID" -> task["TaskID"], "SearchMode" -> searchMode,
    "RuntimeSeconds" -> runtime,
    "CandidateAudit" -> KeyDrop[build, {"Candidates", "ShadowCandidates"}],
    "InitialVersionSpaceASTs" -> ((#["AST"] &) /@ initialCandidates),
    "InitialShadowHypothesisASTs" -> ((#["AST"] &) /@ initialShadowCandidates),
    "FinalVersionSpaceASTs" -> ((#["AST"] &) /@ candidates),
    "FinalShadowHypothesisASTs" -> ((#["AST"] &) /@ shadowCandidates),
    "InitialShadowHypothesisCount" -> Length[initialShadowCandidates],
    "FinalShadowHypothesisCount" -> Length[shadowCandidates],
    "UnresolvedShadowDisagreement" -> unresolvedShadowDisagreement,
    "InitialSemanticClassCount" -> initialState["SemanticClassCount"],
    "InitialDecisionClassCount" -> initialState["DecisionClassCount"],
    "FinalSemanticClassCount" -> state["SemanticClassCount"],
    "FinalDecisionClassCount" -> state["DecisionClassCount"],
    "DecisionCertified" -> decisionCertified,
    "ModelIdentified" -> modelIdentified,
    "AdaptiveStopReason" -> stopReason,
    "FrozenInterventionUniverseCount" -> Length[fullUniverse],
    "RemainingUnusedInterventionCount" ->
      Length[fullUniverse] - Length[usedInputHashes],
    "RemainingInformativeInterventionCount" -> remainingInformativeQueryCount,
    "EverySelectedQueryStrictlyReducedDecisionClasses" -> And @@ (
      #1["DecisionClassCountAfter"] < #1["DecisionClassCountBefore"] & /@
        queryTrace),
    "EverySelectedQueryHadStrictWorstCaseDecisionGain" -> And @@ (
      #1["SelectedScore"]["WorstCaseRemainingDecisionClassCount"] <
        #1["DecisionClassCountBefore"] & /@ queryTrace),
    "InitialCounterfactualOpportunity" -> initialCounterfactualOpportunity,
    "OpportunityResolved" -> (initialCounterfactualOpportunity &&
      Length[queryTrace] > 0 && committed),
    "UnnecessaryQuery" -> (!initialCounterfactualOpportunity &&
      Length[queryTrace] > 0),
    "InitialExactTrainModelCount" -> Length[initialCandidates],
    "InitialDistinctTestPredictionCount" -> Length[initialGroups],
    "ExactTrainModelCount" -> Length[candidates],
    "DistinctTestPredictionCount" -> state["DecisionClassCount"],
    "Status" -> status, "TestPredictionCommitted" -> committed,
    "CommittedPrediction" -> If[committed,
      First[shadowCandidates]["Values"][[testIndex]], Null],
    "PrimaryAST" -> If[AssociationQ[primary], primary["AST"], Null],
    "PrimaryBits" -> If[AssociationQ[primary], primary["Bits"], Null],
    "PrimaryNodes" -> If[AssociationQ[primary], primary["Nodes"], Null],
    "PrimaryConceptID" -> conceptID,
    "VersionSpacePredictions" -> groupRows,
    "PublicQueryPoolSize" -> Length[task["QueryPool"]],
    "KernelShapeGrammarSize" -> Length[kernelShapes137],
    "ActiveQueryCount" -> Length[queryTrace],
    "ActiveQueryTrace" -> queryTrace,
    "ActiveSelectionRule" -> protocol["KernelInterventionSelectionRule"],
    "OracleAccessed" -> Length[queryTrace] > 0,
    "TestOutputAccessed" -> False,
    "GeneratorFamilyAccessed" -> False,
    "DifficultyAxisAccessed" -> False,
    "NamedTransformationPrimitiveAccessed" -> False|>
];

Print[protocol["Stage"]];
Print["Initial named geometry transformations=0; only affine +/- and set modes"];
Print["Kernel intervention rule=", protocol["KernelInterventionSelectionRule"],
  " resource safety cap=", maximumActiveQueries,
  "; actual query count is adaptive"];
resetExitCode = RunOracleCommand136["reset"];
If[resetExitCode =!= 0,
  Print["FATAL: oracle reset failed"]; Exit[22]];

conceptSupport = <||>; conceptLibrary = <||>; taskRows = {};
{totalRuntime, runValue} = AbsoluteTiming[
  Do[
    taskID = task["TaskID"];
    searchMode = Which[
      MemberQ[protocol["TransferTaskIDs"], taskID], "TRANSFER_LIBRARY_ONLY",
      True, "ACTIVE_OPEN_SEARCH"];
    conceptsBefore = Values[conceptLibrary];
    row = EvaluateTask136[task, searchMode, conceptsBefore];
    AssociateTo[row, "ConceptCountBefore" -> Length[conceptsBefore]];
    If[MemberQ[protocol["DiscoveryTaskIDs"], taskID] &&
        TrueQ[row["TestPredictionCommitted"]] &&
        TrueQ[row["ModelIdentified"]] && ListQ[row["PrimaryAST"]],
      skeleton = Skeleton136[row["PrimaryAST"]]; key = ConceptKey136[skeleton];
      supportRow = Lookup[conceptSupport, key,
        <|"Skeleton" -> skeleton, "SupportingTaskIDs" -> {}|>];
      AssociateTo[supportRow, "SupportingTaskIDs" ->
        DeleteDuplicates@Append[supportRow["SupportingTaskIDs"], taskID]];
      AssociateTo[conceptSupport, key -> supportRow];
      If[Length[supportRow["SupportingTaskIDs"]] >= minimumConceptSupport &&
          !KeyExistsQ[conceptLibrary, key],
        AssociateTo[conceptLibrary, key -> <|
          "ConceptID" -> ConceptID136[skeleton],
          "Skeleton" -> skeleton,
          "InventedFromTaskIDs" -> supportRow["SupportingTaskIDs"],
          "InitialNamedPrimitive" -> False|>]]];
    AssociateTo[row, "ConceptCountAfter" -> Length[conceptLibrary]];
    AssociateTo[row, "AvailableConceptIDsAfter" ->
      (#1["ConceptID"] &) /@ Values[conceptLibrary]];
    AppendTo[taskRows, row];
    Print[taskID, " mode=", searchMode, " status=", row["Status"],
      " initial=", row["InitialExactTrainModelCount"],
      " final=", row["ExactTrainModelCount"],
      " queries=", row["ActiveQueryCount"], " concepts=", Length[conceptLibrary],
      " runtime=", row["RuntimeSeconds"]],
    {task, public["Tasks"]}]
];

rowByID = AssociationThread[Lookup[taskRows, "TaskID"] -> taskRows];
fixedDiscoveryCohortPass =
  Length[protocol["DiscoveryTaskIDs"]] === protocol["FixedDiscoveryCohortSize"] &&
  Length[taskRows] === Length[protocol["TaskOrder"]] &&
  Sort[Lookup[taskRows, "TaskID"]] === Sort[protocol["TaskOrder"]] &&
  And @@ (KeyExistsQ[rowByID, #] & /@ protocol["DiscoveryTaskIDs"]);
discoveryPass = And @@ (TrueQ[rowByID[#]["TestPredictionCommitted"]] & /@
  protocol["DiscoveryTaskIDs"]);
transferPass = And @@ (TrueQ[rowByID[#]["TestPredictionCommitted"]] &&
    rowByID[#]["SearchMode"] === "TRANSFER_LIBRARY_ONLY" &&
    StringQ[rowByID[#]["PrimaryConceptID"]] & /@ protocol["TransferTaskIDs"]);
controlsPass = And @@ (!TrueQ[rowByID[#]["TestPredictionCommitted"]] &&
    MemberQ[{"NO_EXACT_INITIAL_TRAIN_MODEL", "NO_EXACT_MODEL_AFTER_ACTIVE_QUERY",
      "DECISION_AMBIGUOUS_NO_INFORMATIVE_QUERY",
      "AMBIGUOUS_AFTER_ACTIVE_QUERY_LIMIT",
      "SHADOW_ALIAS_AMBIGUOUS_AFTER_ACTIVE_QUERY_LIMIT"},
      rowByID[#]["Status"]] & /@
    protocol["ControlTaskIDs"]);
libraryRows = Values[conceptLibrary];
libraryPass = Length[libraryRows] === protocol["ExpectedInventedConceptCount"] &&
  And @@ (Length[#["InventedFromTaskIDs"]] >= minimumConceptSupport & /@ libraryRows);
boundaryPass = public["LearnerVisibleNamedTransformationPrimitiveCount"] === 0 &&
  public["LearnerVisibleTestOutputCount"] === 0 &&
  public["LearnerVisibleGeneratorFamilyCount"] === 0 &&
  !MemberQ[Lookup[taskRows, "TestOutputAccessed"], True] &&
  !MemberQ[Lookup[taskRows, "GeneratorFamilyAccessed"], True] &&
  !MemberQ[Lookup[taskRows, "DifficultyAxisAccessed"], True] &&
  And @@ (!KeyExistsQ[#, "DifficultyConstructionAxis"] & /@ public["Tasks"]) &&
  !MemberQ[Lookup[taskRows, "NamedTransformationPrimitiveAccessed"], True];
kernelInterventionBoundaryPass =
  And @@ (Length[#["QueryPool"]] === 0 & /@ public["Tasks"]) &&
  And @@ Flatten[(Lookup[#["ActiveQueryTrace"],
      "GeneratedByTCCTKernel", {}] &) /@ taskRows] &&
  And @@ (# === "PROOF_CONSTRUCTED_SYMMETRY_PRESERVING_SUPPORT_TRAP" & /@
    Flatten[(Lookup[#["ActiveQueryTrace"], "Derivation", {}] &) /@ taskRows]);
oracleLogLineCount = Length@Select[
  StringSplit[Import[oracleLogPath, "Text"], "\n"], StringLength[#] > 0 &];
queryBoundaryPass = And @@ (rowByID[#]["ActiveQueryCount"] <= maximumActiveQueries & /@
    protocol["ActiveTaskIDs"]) &&
  And @@ (rowByID[#]["ActiveQueryCount"] === 0 & /@ protocol["TransferTaskIDs"]) &&
  oracleLogLineCount === Total[Lookup[taskRows, "ActiveQueryCount"]] &&
  !MemberQ[Flatten[(Lookup[#["ActiveQueryTrace"],
    "TestOutputAccessed", {}] &) /@ taskRows], True] &&
  !MemberQ[Flatten[(Lookup[#["ActiveQueryTrace"],
    "GeneratorFamilyAccessed", {}] &) /@ taskRows], True];
opportunityCount = Count[(rowByID[#] &) /@ protocol["DiscoveryTaskIDs"],
  row_ /; TrueQ[row["InitialCounterfactualOpportunity"]]];
activeResolutionCount = Count[(rowByID[#] &) /@ protocol["DiscoveryTaskIDs"],
  row_ /; TrueQ[row["OpportunityResolved"]]];
unnecessaryQueryCount = Count[(rowByID[#] &) /@ protocol["DiscoveryTaskIDs"],
  row_ /; TrueQ[row["UnnecessaryQuery"]]];
opportunityChallengePass = opportunityCount >=
  protocol["MinimumDiscoveryInterventionOpportunityCount"];
activeResolutionPass = activeResolutionCount === opportunityCount &&
  unnecessaryQueryCount === 0 &&
  And @@ (TrueQ[rowByID[#]["DecisionCertified"]] & /@
    protocol["DiscoveryTaskIDs"]);
adaptiveQueryPolicyPass = And @@ (
    rowByID[#]["ActiveQueryCount"] <= maximumActiveQueries &&
    rowByID[#]["ActiveQueryCount"] <= rowByID[#]["FrozenInterventionUniverseCount"] &&
    If[rowByID[#]["InitialDecisionClassCount"] > 1,
      rowByID[#]["ActiveQueryCount"] >= 1,
      rowByID[#]["ActiveQueryCount"] === 0] &&
    TrueQ[rowByID[#]["DecisionCertified"]] &&
    If[rowByID[#]["ActiveQueryCount"] > 0,
      TrueQ[Last[rowByID[#]["ActiveQueryTrace"]]["DecisionCertifiedAfter"]],
      True] & /@ protocol["DiscoveryTaskIDs"]);
capabilityPreScorePass = fixedDiscoveryCohortPass && discoveryPass && transferPass && controlsPass &&
  boundaryPass && kernelInterventionBoundaryPass && queryBoundaryPass &&
  activeResolutionPass && adaptiveQueryPolicyPass;
preScorePass = capabilityPreScorePass && opportunityChallengePass;

result = <|"Stage" -> protocol["Stage"],
  "EvidenceStatus" -> protocol["EvidenceStatus"],
  "NativeWolframExecution" -> True, "WolframVersion" -> $Version,
  "RuntimeSeconds" -> totalRuntime, "ProtocolSHA256" -> protocolHash,
  "WolframRunnerSHA256" -> runnerHash,
  "OracleResponderSHA256" -> oracleResponderHash,
  "OracleQueryLogSHA256" -> IntegerString[FileHash[oracleLogPath, "SHA256"], 16, 64],
  "HistoricalB6LoadedVerbatim" -> True,
  "InitialNamedTransformationPrimitiveCount" -> 0,
  "AffineExpressionCount" -> Length[affineExpressions],
  "InventedConceptLibrary" -> libraryRows,
  "ConceptSupportAudit" -> Values[conceptSupport],
  "KernelInterventionSelectionRule" -> protocol["KernelInterventionSelectionRule"],
  "KernelInterventionGrammar" -> protocol["KernelInterventionGrammar"],
  "KernelShapeGrammarSize" -> Length[kernelShapes137],
  "ResourceSafetyCapPerTask" -> maximumActiveQueries,
  "QueryCountPredeclaredAsCapabilityConstant" -> False,
  "ObservedActiveQueryCounts" ->
    (rowByID[#]["ActiveQueryCount"] & /@ protocol["TaskOrder"]),
  "OracleQueryLogLineCount" -> oracleLogLineCount,
  "ActivelyResolvedTaskCount" -> activeResolutionCount,
  "ActiveResolutionPreScorePass" -> activeResolutionPass,
  "AdaptiveQueryPolicyPreScorePass" -> adaptiveQueryPolicyPass,
  "InitialCounterfactualOpportunityCount" -> opportunityCount,
  "MinimumRequiredCounterfactualOpportunityCount" ->
    protocol["MinimumDiscoveryInterventionOpportunityCount"],
  "OpportunityChallengePreScorePass" -> opportunityChallengePass,
  "OpportunityResolutionRate" -> If[opportunityCount === 0, Null,
    N[activeResolutionCount/opportunityCount]],
  "UnnecessaryQueryCount" -> unnecessaryQueryCount,
  "CapabilityPreScorePass" -> capabilityPreScorePass,
  "FixedDiscoveryCohortSize" -> protocol["FixedDiscoveryCohortSize"],
  "AllFixedCohortWorldsEvaluated" -> fixedDiscoveryCohortPass,
  "TaskResults" -> taskRows,
  "DiscoveryPreScorePass" -> discoveryPass,
  "TransferLibraryOnlyPreScorePass" -> transferPass,
  "ControlsPreScorePass" -> controlsPass,
  "ConceptLibraryPreScorePass" -> libraryPass,
  "BoundaryPass" -> boundaryPass,
  "KernelInterventionBoundaryPass" -> kernelInterventionBoundaryPass,
  "ActiveQueryBoundaryPass" -> queryBoundaryPass,
  "NativePreScorePass" -> preScorePass,
  "CanonicalTCCTModified" -> False,
  "S135BModified" -> False,
  "S136AModified" -> False,
  "OfficialARCDataTouched" -> False,
  "ThirdPartyExternalSeal" -> False,
  "Conclusion" -> If[preScorePass,
    "KERNEL_INTERVENTION_SYNTHESIS_COMPLETE_AWAITING_SEALED_SCORING",
    If[capabilityPreScorePass && !opportunityChallengePass,
      "KERNEL_INTERVENTION_SYNTHESIS_INSUFFICIENT_CHALLENGE",
      "KERNEL_INTERVENTION_SYNTHESIS_MODEL_FAILURE"]]|>;
Export[resultPath, result, "RawJSON", "Compact" -> False];
Print[protocol["Stage"], " pre-score pass=", preScorePass,
  " concepts=", Length[libraryRows], " runtime=", totalRuntime];
Exit[0];
