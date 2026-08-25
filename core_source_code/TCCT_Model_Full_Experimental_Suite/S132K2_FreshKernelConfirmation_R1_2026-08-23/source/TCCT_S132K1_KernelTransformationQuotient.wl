(* ::Package:: *)

(* S132-K1: TCCT-native second-order transformation quotient diagnostic. *)

ClearAll["Global`*"];

sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
inputPath = FileNameJoin[{rootDirectory, "input", "certified_automata.json"}];
manifestPath = FileNameJoin[{rootDirectory, "protocol", "S132K1_frozen_manifest.json"}];
resultPath = FileNameJoin[{rootDirectory, "results", "S132K1_result.json"}];
controlPath = FileNameJoin[{rootDirectory, "negative_controls", "S132K1_random_automata.json"}];

If[!And @@ (FileExistsQ /@ {inputPath, manifestPath}),
  Print["FATAL: frozen S132-K1 boundary incomplete"]; Exit[2]];

input = Import[inputPath, "RawJSON"];
manifest = Import[manifestPath, "RawJSON"];
automata = input["Automata"];
maximumWordLength = manifest["MaximumWordLength"];
heldoutProgramCount = manifest["HeldoutProgramCountPerWorld"];
heldoutProgramLength = manifest["HeldoutProgramLength"];
heldoutSeeds = manifest["HeldoutSeeds"];
randomControlSeeds = manifest["RandomControlSeeds"];
relabelSeeds = manifest["StateRelabelSeeds"];

WordKeyK1[word_List] := ToString[word, InputForm];
TransformKeyK1[transform_List] := ToString[transform, InputForm];

WordTransformK1[table_List, word_List] := Fold[
  Function[{mapping, action}, table[[mapping, action]]],
  Range[Length[table]], word];

ShortestRepresentativeK1[words_List] := First@SortBy[words,
  Function[word, {Length[word], WordKeyK1[word]}]];

BuildTransformationQuotientK1[table_List, maxLength_Integer] := Module[
  {actionCount = Length[First[table]], words, groups, classRecords,
   rules, exactRuleCount, badRules},
  words = Join[{{}}, Flatten[Table[Tuples[Range[actionCount], length],
    {length, 1, maxLength}], 1]];
  groups = GroupBy[words, TransformKeyK1[WordTransformK1[table, #]] &];
  classRecords = KeyValueMap[Function[{semanticKey, members}, Module[
      {representative = ShortestRepresentativeK1[members], longer},
      longer = Select[members, Length[#] > Length[representative] &];
      <|"SemanticKey" -> semanticKey,
        "RealizationCount" -> Length[members],
        "DistinctLengths" -> Sort@DeleteDuplicates[Length /@ members],
        "Representative" -> representative,
        "RewriteCount" -> Length[longer],
        "LongerWords" -> longer|>]], groups];
  rules = Association@Flatten[Table[
      Rule[WordKeyK1[word], record["Representative"]],
      {record, classRecords}, {word, record["LongerWords"]}], 1];
  badRules = Select[Normal[rules],
    WordTransformK1[table, ToExpression[First[#], InputForm]] =!=
      WordTransformK1[table, Last[#]] &];
  exactRuleCount = Length[rules] - Length[badRules];
  <|"EnumeratedWordCount" -> Length[words],
    "SemanticClassCount" -> Length[groups],
    "MultiRealizationClassCount" -> Count[classRecords,
      record_ /; record["RealizationCount"] > 1],
    "ShorteningConceptCount" -> Count[classRecords,
      record_ /; record["RewriteCount"] > 0],
    "RewriteRuleCount" -> Length[rules],
    "ExactRewriteRuleCount" -> exactRuleCount,
    "FalseEquivalenceCount" -> Length[badRules],
    "Rules" -> rules|>
];

RewriteProgramK1[program_List, rules_Association, maxLength_Integer] := Module[
  {current = program, changed = True, position, length, replacement},
  While[TrueQ[changed],
    changed = False;
    For[position = 1, position <= Length[current] && !TrueQ[changed], position++,
      For[length = Min[maxLength, Length[current] - position + 1],
          length >= 1, length--,
        replacement = Lookup[rules,
          WordKeyK1[Take[current, {position, position + length - 1}]],
          Missing["NoRule"]];
        If[ListQ[replacement] && Length[replacement] < length,
          current = Join[Take[current, position - 1], replacement,
            Drop[current, position + length - 1]];
          changed = True;
          Break[]]
      ]
    ]
  ];
  current
];

EvaluateHeldoutK1[table_List, quotient_Association, seed_Integer] := Module[
  {actionCount = Length[First[table]], programs, rewritten, exactFlags,
   rawTokens, rewrittenTokens},
  programs = BlockRandom[SeedRandom[seed, Method -> "MersenneTwister"];
    Table[RandomChoice[Range[actionCount], heldoutProgramLength],
      {heldoutProgramCount}]];
  rewritten = RewriteProgramK1[#, quotient["Rules"], maximumWordLength] & /@ programs;
  exactFlags = MapThread[
    WordTransformK1[table, #1] === WordTransformK1[table, #2] &,
    {programs, rewritten}];
  rawTokens = Total[Length /@ programs];
  rewrittenTokens = Total[Length /@ rewritten];
  <|"ProgramCount" -> Length[programs],
    "RawActionTokens" -> rawTokens,
    "RewrittenActionTokens" -> rewrittenTokens,
    "ActionTokenReduction" -> rawTokens - rewrittenTokens,
    "ActionTokenReductionFraction" -> N[(rawTokens - rewrittenTokens)/rawTokens],
    "ExactProgramCount" -> Count[exactFlags, True],
    "AllProgramsExactlyEquivalent" -> And @@ exactFlags,
    "RewriteDisabledAblationTokens" -> rawTokens,
    "RewriteDisabledAblationReduction" -> 0|>
];

ActionImageRanksK1[table_List] := Table[
  Length@DeleteDuplicates[table[[All, action]]],
  {action, Length[First[table]]}];

MakeRankMatchedFunctionK1[stateCount_Integer, rank_Integer] := Module[
  {image, values},
  image = RandomSample[Range[stateCount], rank];
  values = Join[image, If[stateCount > rank,
    RandomChoice[image, stateCount - rank], {}]];
  RandomSample[values]
];

MakeRankMatchedAutomatonK1[table_List, seed_Integer] := Module[
  {stateCount = Length[table], ranks, columns},
  ranks = ActionImageRanksK1[table];
  columns = BlockRandom[SeedRandom[seed, Method -> "MersenneTwister"];
    MakeRankMatchedFunctionK1[stateCount, #] & /@ ranks];
  Transpose[columns]
];

RelabelAutomatonK1[table_List, seed_Integer] := Module[
  {stateCount = Length[table], actionCount = Length[First[table]],
   oldToNew, newToOld},
  oldToNew = BlockRandom[SeedRandom[seed, Method -> "MersenneTwister"];
    RandomSample[Range[stateCount]]];
  newToOld = Ordering[oldToNew];
  Table[oldToNew[[table[[newToOld[[state]], action]]]],
    {state, stateCount}, {action, actionCount}]
];

SummarizeQuotientK1[quotient_Association] := KeyDrop[quotient, {"Rules"}];

Print["S132-K1 TCCT-NATIVE TRANSFORMATION QUOTIENT"];
Print["AST input=False; generator truth=False; canonical core modified=False"];

structuredResults = Table[Module[
    {world = automata[[index]], table, quotient, heldout, relabeledTable,
     relabeledQuotient, invariant},
    table = world["TransitionTable"];
    quotient = BuildTransformationQuotientK1[table, maximumWordLength];
    heldout = EvaluateHeldoutK1[table, quotient, heldoutSeeds[[index]]];
    relabeledTable = RelabelAutomatonK1[table, relabelSeeds[[index]]];
    relabeledQuotient = BuildTransformationQuotientK1[relabeledTable, maximumWordLength];
    invariant = And @@ Table[
      quotient[key] === relabeledQuotient[key],
      {key, {"EnumeratedWordCount", "SemanticClassCount",
        "MultiRealizationClassCount", "ShorteningConceptCount",
        "RewriteRuleCount", "FalseEquivalenceCount"}}];
    Print[world["WorldID"], " classes=", quotient["SemanticClassCount"],
      " concepts=", quotient["ShorteningConceptCount"],
      " saved=", heldout["ActionTokenReduction"]];
    <|"WorldID" -> world["WorldID"],
      "StateCount" -> world["StateCount"],
      "ActionCount" -> world["ActionCount"],
      "ActionImageRanks" -> ActionImageRanksK1[table],
      "Quotient" -> SummarizeQuotientK1[quotient],
      "Heldout" -> heldout,
      "StateRelabelInvariant" -> invariant|>
  ], {index, Length[automata]}];

randomControlRecords = Flatten[Table[Module[
    {world = automata[[index]], table, controlTable, quotient, heldout,
     controlSeed, programSeed},
    table = world["TransitionTable"];
    controlSeed = randomControlSeeds[[replicate, index]];
    programSeed = controlSeed + 500000;
    controlTable = MakeRankMatchedAutomatonK1[table, controlSeed];
    quotient = BuildTransformationQuotientK1[controlTable, maximumWordLength];
    heldout = EvaluateHeldoutK1[controlTable, quotient, programSeed];
    <|"Replicate" -> replicate, "WorldID" -> world["WorldID"],
      "Seed" -> controlSeed, "ProgramSeed" -> programSeed,
      "StateCount" -> world["StateCount"],
      "ActionCount" -> world["ActionCount"],
      "TargetActionImageRanks" -> ActionImageRanksK1[table],
      "ControlActionImageRanks" -> ActionImageRanksK1[controlTable],
      "TransitionTable" -> controlTable,
      "Quotient" -> SummarizeQuotientK1[quotient],
      "Heldout" -> heldout|>
  ], {replicate, Length[randomControlSeeds]}, {index, Length[automata]}], 1];

Export[controlPath, <|"Stage" -> "S132-K1 rank-matched random automata",
  "Controls" -> randomControlRecords|>, "RawJSON", "Compact" -> False];

structuredConcepts = Total[Lookup[Lookup[structuredResults, "Quotient"],
  "ShorteningConceptCount"]];
structuredRules = Total[Lookup[Lookup[structuredResults, "Quotient"],
  "RewriteRuleCount"]];
structuredSavings = Total[Lookup[Lookup[structuredResults, "Heldout"],
  "ActionTokenReduction"]];
structuredExact = And @@ Lookup[Lookup[structuredResults, "Heldout"],
  "AllProgramsExactlyEquivalent"];
structuredRuleExact = Total[Lookup[Lookup[structuredResults, "Quotient"],
  "FalseEquivalenceCount"]] === 0;
relabelPass = And @@ Lookup[structuredResults, "StateRelabelInvariant"];
controlExact = And @@ Lookup[Lookup[randomControlRecords, "Heldout"],
  "AllProgramsExactlyEquivalent"];
controlRuleExact = Total[Lookup[Lookup[randomControlRecords, "Quotient"],
  "FalseEquivalenceCount"]] === 0;
ablationReduction = Total[Lookup[Lookup[structuredResults, "Heldout"],
  "RewriteDisabledAblationReduction"]];

kernelGatePass = structuredConcepts > 0 && structuredRules > 0 &&
  structuredSavings > 0 && structuredExact && structuredRuleExact &&
  relabelPass && controlExact && controlRuleExact && ablationReduction === 0;

result = <|
  "Stage" -> "S132-K1 TCCT-native second-order transformation quotient",
  "EvidenceStatus" -> "RETROSPECTIVE_KERNEL_MECHANISM_DIAGNOSTIC_NOT_FRESH_WORLD_EVIDENCE",
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "GeneratorTruthRead" -> False,
  "ProgramASTReadByConceptLearner" -> False,
  "CanonicalTCCTModified" -> False,
  "CertifiedAutomataModified" -> False,
  "ConceptSource" -> "exact action-word transformation signatures over TCCT certified latent automata",
  "TCCTMechanism" -> "semantic rewrite -> transformation-signature dedup -> shortest representative freeze -> exact fallback",
  "MaximumWordLength" -> maximumWordLength,
  "StructuredWorldCount" -> Length[structuredResults],
  "StructuredShorteningConceptCount" -> structuredConcepts,
  "StructuredRewriteRuleCount" -> structuredRules,
  "StructuredHeldoutActionTokenReduction" -> structuredSavings,
  "StructuredAllRewritesExact" -> structuredExact && structuredRuleExact,
  "RewriteDisabledAblationReduction" -> ablationReduction,
  "StateRelabelingPass" -> relabelPass,
  "RandomControlCount" -> Length[randomControlRecords],
  "RandomControlsAllRewritesExact" -> controlExact && controlRuleExact,
  "KernelCausalGatePass" -> kernelGatePass,
  "OpenEndedPrimitiveInventionProven" -> False,
  "ClaimBoundary" -> "proves only kernel-native exact transformation-quotient concept formation, not open-ended language invention",
  "StructuredResults" -> structuredResults,
  "Conclusion" -> If[kernelGatePass,
    "KERNEL_TRANSFORMATION_QUOTIENT_GATE_PASS",
    "KERNEL_TRANSFORMATION_QUOTIENT_GATE_NOT_PASSED"]|>;

Export[resultPath, result, "RawJSON", "Compact" -> False];
Print["S132-K1 COMPLETE gate=", kernelGatePass,
  " concepts=", structuredConcepts, " rules=", structuredRules,
  " saved=", structuredSavings];
Exit[If[kernelGatePass, 0, 1]];
