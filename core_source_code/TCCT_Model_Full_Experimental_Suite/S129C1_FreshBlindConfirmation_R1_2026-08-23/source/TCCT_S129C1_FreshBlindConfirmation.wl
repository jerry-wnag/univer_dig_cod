(* ::Package:: *)

(* S129-C1 fresh blind confirmation over the frozen B8A learner. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
b8RunnerPath = FileNameJoin[{sourceDirectory,
  "TCCT_S129B8A_IncrementalCompleteSearch.wl"}];
b8Text = Import[b8RunnerPath, "Text"];
b8Marker = "Print[\"S129-B8A incremental bounded-complete search R1\"]";
b8MarkerPosition = First@First@StringPosition[b8Text, b8Marker];
ToExpression[StringTake[b8Text, b8MarkerPosition - 1], InputForm];

(* Override the inherited B6 development inputs with the frozen C1 boundary. *)
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S129C1_pre_world_manifest.json"}], "RawJSON"];
receipt = Import[FileNameJoin[{rootDirectory, "protocol",
  "S129C1_freeze_receipt.json"}], "RawJSON"];
public = Import[FileNameJoin[{rootDirectory, "input",
  "S129C1_public_input.json"}], "RawJSON"];
oracle = Import[FileNameJoin[{rootDirectory, "oracle",
  "S129C1_oracle_tables.json"}], "RawJSON"];
If[!TrueQ[receipt["WorldMaterialized"]],
  Print["FATAL: worlds were not materialized after protocol freeze"]; Exit[2]];

publicWorlds = public["Worlds"];
oracleByID = AssociationThread[Lookup[oracle["Worlds"], "WorldID"] ->
  oracle["Worlds"]];
inBoundIDs = Lookup[manifest["InBoundWorldSpecifications"], "WorldID"];
challengeIDs = Lookup[manifest["ChallengeWorldSpecifications"], "WorldID"];
inBoundWorlds = Select[publicWorlds, MemberQ[inBoundIDs, #["WorldID"]] &];
challengeWorlds = Select[publicWorlds, MemberQ[challengeIDs, #["WorldID"]] &];
randomSeeds = manifest["RandomControlSeeds"];
$BasisCacheB7 = <||>;

resultDirectory = FileNameJoin[{rootDirectory, "results"}];
controlDirectory = FileNameJoin[{rootDirectory, "negative_controls"}];
If[!DirectoryQ[resultDirectory], CreateDirectory[resultDirectory]];
If[!DirectoryQ[controlDirectory], CreateDirectory[controlDirectory]];

Print["S129-C1 FRESH BLIND CONFIRMATION R1"];
Print["Frozen B8A; no truth programs; no solver-based resampling"];

formalResultsC1 = Table[
  world = inBoundWorlds[[index]];
  table = oracleByID[world["WorldID"]]["TransitionTable"];
  Print["C1 IN-BOUND START ", world["WorldID"], " states=", world["StateCount"],
    " actions=", world["ActionCount"]];
  built = GetBasisB7[world];
  active = RunIncrementalLearnerB8[world, table, built["Basis"],
    built["Predicates"], "ACTIVE_INCREMENTAL"];
  passive = RunIncrementalLearnerB8[world, table, built["Basis"],
    built["Predicates"], "PASSIVE_INCREMENTAL"];
  Print["C1 IN-BOUND END ", world["WorldID"], " active=", active["Outcome"],
    " q=", active["MembershipQueryCount"], " passiveQ=",
    passive["MembershipQueryCount"], " sec=", active["RuntimeSeconds"]];
  <|"WorldID" -> world["WorldID"], "StateCount" -> world["StateCount"],
    "ActionCount" -> world["ActionCount"],
    "CoordinateDimensions" -> world["CoordinateDimensions"],
    "BasisStatistics" -> built["Basis"]["Statistics"],
    "Active" -> active, "Passive" -> passive|>,
  {index, Length[inBoundWorlds]}];

challengeResultsC1 = Table[
  world = challengeWorlds[[index]];
  table = oracleByID[world["WorldID"]]["TransitionTable"];
  boundary = SelectFirst[manifest["ChallengeWorldSpecifications"],
    #["WorldID"] === world["WorldID"] &]["Boundary"];
  Print["C1 CHALLENGE START ", world["WorldID"], " boundary=", boundary];
  built = GetBasisB7[world];
  active = RunIncrementalLearnerB8[world, table, built["Basis"],
    built["Predicates"], "ACTIVE_INCREMENTAL"];
  Print["C1 CHALLENGE END ", world["WorldID"], " outcome=", active["Outcome"],
    " q=", active["MembershipQueryCount"], " sec=", active["RuntimeSeconds"]];
  <|"WorldID" -> world["WorldID"], "Boundary" -> boundary,
    "StateCount" -> world["StateCount"], "ActionCount" -> world["ActionCount"],
    "CoordinateDimensions" -> world["CoordinateDimensions"],
    "BasisStatistics" -> built["Basis"]["Statistics"], "Active" -> active|>,
  {index, Length[challengeWorlds]}];

randomResultsC1 = Table[
  world = inBoundWorlds[[index]];
  table = RandomReachableTableB6[world["StateCount"], world["ActionCount"],
    world["StartState"], randomSeeds[[index]]];
  built = GetBasisB7[world];
  If[table === $Failed,
    <|"WorldID" -> world["WorldID"], "Seed" -> randomSeeds[[index]],
      "GenerationFailed" -> True, "ExactCertified" -> False|>,
    randomRun = RunIncrementalLearnerB8[world, table, built["Basis"],
      built["Predicates"], "ACTIVE_INCREMENTAL"];
    <|"WorldID" -> world["WorldID"], "Seed" -> randomSeeds[[index]],
      "GenerationFailed" -> False, "TransitionTable" -> table,
      "Outcome" -> randomRun["Outcome"],
      "ExactCertified" -> randomRun["ExactCertified"],
      "MembershipQueryCount" -> randomRun["MembershipQueryCount"],
      "Programs" -> randomRun["Programs"],
      "Observations" -> randomRun["Observations"],
      "RuntimeSeconds" -> randomRun["RuntimeSeconds"]|>],
  {index, Length[inBoundWorlds]}];

nearLawResultsC1 = Table[
  world = inBoundWorlds[[index]];
  table = oracleByID[world["WorldID"]]["TransitionTable"];
  active = formalResultsC1[[index, "Active"]];
  mutated = Map[Identity, table]; oldTarget = mutated[[1, 1]];
  mutated[[1, 1]] = Mod[oldTarget, world["StateCount"]] + 1;
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[world, mutated, active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"],
    "Applicable" -> TrueQ[active["ExactCertified"]],
    "MutatedState" -> 1, "MutatedAction" -> 1,
    "OriginalTarget" -> oldTarget, "MutatedTarget" -> mutated[[1, 1]],
    "BaseProgramMismatchCount" -> Length[errors],
    "MutationDetected" -> (!TrueQ[active["ExactCertified"]] || Length[errors] >= 1)|>,
  {index, Length[inBoundWorlds]}];

relabelResultsC1 = Table[
  world = inBoundWorlds[[index]];
  table = oracleByID[world["WorldID"]]["TransitionTable"];
  relabeled = RelabelWorldB6[world, table, 1299500 + index];
  active = formalResultsC1[[index, "Active"]];
  errors = If[TrueQ[active["ExactCertified"]],
    ProgramErrorsB6[relabeled["World"], relabeled["Table"], active["Programs"]], {}];
  <|"WorldID" -> world["WorldID"],
    "CoordinateDatasetHashInvariant" ->
      (CoordinateDatasetHashB6[world, table] ===
        CoordinateDatasetHashB6[relabeled["World"], relabeled["Table"]]),
    "FrozenProgramStillExact" ->
      (!TrueQ[active["ExactCertified"]] || Length[errors] === 0)|>,
  {index, Length[inBoundWorlds]}];

inBoundExactCountC1 = Count[Lookup[Lookup[formalResultsC1, "Active"],
  "ExactCertified"], True];
passiveExactCountC1 = Count[Lookup[Lookup[formalResultsC1, "Passive"],
  "ExactCertified"], True];
challengeExactCountC1 = Count[Lookup[Lookup[challengeResultsC1, "Active"],
  "ExactCertified"], True];
randomExactCountC1 = Count[Lookup[randomResultsC1, "ExactCertified"], True];
randomGenerationPassC1 = !MemberQ[Lookup[randomResultsC1,
  "GenerationFailed"], True];
nearPassC1 = And @@ Lookup[nearLawResultsC1, "MutationDetected"];
relabelPassC1 = And @@ Flatten[{Lookup[relabelResultsC1,
  "CoordinateDatasetHashInvariant"], Lookup[relabelResultsC1,
  "FrozenProgramStillExact"]}];
primaryPassC1 = inBoundExactCountC1 === Length[inBoundWorlds] &&
  randomGenerationPassC1 && randomExactCountC1 === 0 && nearPassC1 &&
  relabelPassC1;

resultC1 = <|
  "Stage" -> manifest["Stage"], "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True, "WolframVersion" -> $Version,
  "PreWorldManifestSHA256" -> receipt["PreWorldManifestSHA256"],
  "GeneratorTruthRead" -> False, "PriorProgramsLoaded" -> False,
  "PerWorldTemplatesAdded" -> False, "SolverBasedResampling" -> False,
  "CanonicalTCCTModified" -> False, "S128BModified" -> False,
  "B8AAlgorithmModified" -> False,
  "InBoundExactCount" -> inBoundExactCountC1,
  "PassiveExactCount" -> passiveExactCountC1,
  "ChallengeExactCount" -> challengeExactCountC1,
  "RandomControlExactCount" -> randomExactCountC1,
  "RandomControlsGenerated" -> randomGenerationPassC1,
  "NearLawPass" -> nearPassC1, "StateRelabelingPass" -> relabelPassC1,
  "PrimaryConfirmatoryPassBeforeIndependentVerification" -> primaryPassC1,
  "ChallengeOutcomesAreDescriptive" -> True,
  "NoPostResultDSLChange" -> True, "AutomatonFallbackRetained" -> True,
  "FormalResults" -> formalResultsC1,
  "ChallengeResults" -> challengeResultsC1,
  "RandomControls" -> randomResultsC1,
  "NearLawControls" -> nearLawResultsC1,
  "StateRelabelingControls" -> relabelResultsC1|>;

Export[FileNameJoin[{resultDirectory, "S129C1_result.json"}], resultC1,
  "RawJSON", "Compact" -> False];
Export[FileNameJoin[{resultDirectory, "S129C1_per_world.csv"}], Table[
  {row["WorldID"], row["StateCount"], row["ActionCount"],
    row["Active"]["Outcome"], row["Active"]["MembershipQueryCount"],
    row["Passive"]["MembershipQueryCount"], row["Active"]["RuntimeSeconds"],
    row["Active"]["CompressionRatio"]}, {row, formalResultsC1}], "CSV",
  "TableHeadings" -> {{}, {"WorldID", "States", "Actions", "ActiveOutcome",
    "ActiveQueries", "PassiveQueries", "ActiveSeconds", "CompressionRatio"}}];
Export[FileNameJoin[{controlDirectory, "S129C1_random_controls.json"}],
  randomResultsC1, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129C1_near_law_controls.json"}],
  nearLawResultsC1, "RawJSON", "Compact" -> False];
Export[FileNameJoin[{controlDirectory, "S129C1_state_relabeling_controls.json"}],
  relabelResultsC1, "RawJSON", "Compact" -> False];
Print["S129-C1 COMPLETE inBoundExact=", inBoundExactCountC1, "/",
  Length[inBoundWorlds], " challengeExact=", challengeExactCountC1, "/",
  Length[challengeWorlds], " randomExact=", randomExactCountC1,
  " primaryPass=", primaryPassC1];
