(* ::Package:: *)

(* S132-K2: fresh confirmatory run of the unchanged K1 kernel quotient. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];

manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K2_pre_world_manifest.json"}], "RawJSON"];
receipt = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K2_freeze_receipt.json"}], "RawJSON"];
input = Import[FileNameJoin[{rootDirectory, "input",
  "certified_automata.json"}], "RawJSON"];

If[!TrueQ[receipt["CertifiedAutomataMaterialized"]] ||
    TrueQ[receipt["ConceptRunComplete"]],
  Print["FATAL: S132-K2 concept phase order invalid"]; Exit[2]];

automata = input["Automata"];
maximumWordLength = manifest["MaximumWordLength"];
heldoutProgramCount = manifest["HeldoutProgramCountPerWorld"];
heldoutProgramLength = manifest["HeldoutProgramLength"];
heldoutSeeds = manifest["HeldoutSeeds"];
randomControlSeeds = manifest["RandomControlSeeds"];
relabelSeeds = manifest["StateRelabelSeeds"];

(* Load only the frozen K1 mechanism definitions, not its setup or run. *)
k1Path = FileNameJoin[{sourceDirectory,
  "TCCT_S132K1_KernelTransformationQuotient.wl"}];
k1Text = Import[k1Path, "Text"];
k1StartMarker = "WordKeyK1[word_List]";
k1EndMarker = "Print[\"S132-K1 TCCT-NATIVE TRANSFORMATION QUOTIENT\"]";
k1Start = First@First@StringPosition[k1Text, k1StartMarker];
k1End = First@First@StringPosition[k1Text, k1EndMarker];
ToExpression[StringTake[k1Text, {k1Start, k1End - 1}], InputForm];

Print["S132-K2 FRESH KERNEL TRANSFORMATION QUOTIENT"];
Print["K1 mechanism changed=False; AST input=False; generator truth=False"];

structuredResults = Table[Module[
    {world = automata[[index]], table, quotient, heldout, relabeledTable,
     relabeledQuotient, invariant},
    table = world["TransitionTable"];
    quotient = BuildTransformationQuotientK1[table, maximumWordLength];
    heldout = EvaluateHeldoutK1[table, quotient, heldoutSeeds[[index]]];
    relabeledTable = RelabelAutomatonK1[table, relabelSeeds[[index]]];
    relabeledQuotient = BuildTransformationQuotientK1[relabeledTable,
      maximumWordLength];
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
  ], {replicate, Length[randomControlSeeds]},
  {index, Length[automata]}], 1];

Export[FileNameJoin[{rootDirectory, "negative_controls",
  "S132K2_random_automata.json"}],
  <|"Stage" -> "S132-K2 fresh rank-matched random automata",
    "Controls" -> randomControlRecords|>, "RawJSON", "Compact" -> False];

conceptWorldPasses = Table[
  structuredResults[[index, "Quotient", "ShorteningConceptCount"]] > 0,
  {index, Length[structuredResults]}];
reductionWorldPasses = Table[
  structuredResults[[index, "Heldout", "ActionTokenReduction"]] > 0,
  {index, Length[structuredResults]}];
pairedControlMeans = Table[Mean[Lookup[Lookup[Select[randomControlRecords,
    #WorldID === structuredResults[[index, "WorldID"]] &], "Heldout"],
    "ActionTokenReduction"]], {index, Length[structuredResults]}];
pairedAdvantagePasses = Table[
  structuredResults[[index, "Heldout", "ActionTokenReduction"]] >
    pairedControlMeans[[index]], {index, Length[structuredResults]}];

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

freshGatePass = input["DiscoveryExactCount"] === Length[automata] &&
  And @@ conceptWorldPasses && And @@ reductionWorldPasses &&
  structuredExact && structuredRuleExact && relabelPass &&
  controlExact && controlRuleExact && ablationReduction === 0 &&
  And @@ pairedAdvantagePasses;

result = <|
  "Stage" -> "S132-K2 fresh-world kernel transformation quotient confirmation",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "K1MechanismModified" -> False,
  "GeneratorTruthRead" -> False,
  "ProgramASTReadByConceptLearner" -> False,
  "CanonicalTCCTModified" -> False,
  "DiscoveryExactCount" -> input["DiscoveryExactCount"],
  "FreshWorldCount" -> Length[automata],
  "ConceptPositiveWorldCount" -> Count[conceptWorldPasses, True],
  "ReductionPositiveWorldCount" -> Count[reductionWorldPasses, True],
  "StructuredShorteningConceptCount" -> structuredConcepts,
  "StructuredRewriteRuleCount" -> structuredRules,
  "StructuredHeldoutActionTokenReduction" -> structuredSavings,
  "StructuredAllRewritesExact" -> structuredExact && structuredRuleExact,
  "RewriteDisabledAblationReduction" -> ablationReduction,
  "StateRelabelingPass" -> relabelPass,
  "RandomControlCount" -> Length[randomControlRecords],
  "RandomControlsAllRewritesExact" -> controlExact && controlRuleExact,
  "PairedControlMeanReductions" -> pairedControlMeans,
  "StructuredBeatsFiveControlMeanWorldCount" -> Count[pairedAdvantagePasses, True],
  "FreshKernelConfirmationPass" -> freshGatePass,
  "OpenEndedPrimitiveInventionProven" -> False,
  "ClaimBoundary" -> "fresh confirmation of exact kernel transformation quotients only",
  "StructuredResults" -> structuredResults,
  "Conclusion" -> If[freshGatePass,
    "FRESH_KERNEL_TRANSFORMATION_QUOTIENT_CONFIRMED",
    "FRESH_KERNEL_TRANSFORMATION_QUOTIENT_NOT_CONFIRMED"]|>;

Export[FileNameJoin[{rootDirectory, "results", "S132K2_result.json"}],
  result, "RawJSON", "Compact" -> False];
Print["S132-K2 COMPLETE pass=", freshGatePass,
  " concepts=", structuredConcepts,
  " rules=", structuredRules, " saved=", structuredSavings,
  " paired=", Count[pairedAdvantagePasses, True], "/", Length[automata]];
Exit[If[freshGatePass, 0, 1]];
