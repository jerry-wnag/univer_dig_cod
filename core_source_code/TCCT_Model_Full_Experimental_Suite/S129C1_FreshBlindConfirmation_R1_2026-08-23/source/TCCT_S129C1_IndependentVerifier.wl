(* Independent verifier for S129-C1. This is the only stage that reads sealed truth. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S129C1_pre_world_manifest.json"}], "RawJSON"];
receipt = Import[FileNameJoin[{rootDirectory, "protocol",
  "S129C1_freeze_receipt.json"}], "RawJSON"];
public = Import[FileNameJoin[{rootDirectory, "input",
  "S129C1_public_input.json"}], "RawJSON"];
oracle = Import[FileNameJoin[{rootDirectory, "oracle",
  "S129C1_oracle_tables.json"}], "RawJSON"];
truth = Import[FileNameJoin[{rootDirectory, "sealed",
  "S129C1_generator_truth.json"}], "RawJSON"];
result = Import[FileNameJoin[{rootDirectory, "results",
  "S129C1_result.json"}], "RawJSON"];

verificationDirectory = FileNameJoin[{rootDirectory, "verification"}];
If[!DirectoryQ[verificationDirectory], CreateDirectory[verificationDirectory]];
publicByID = AssociationThread[Lookup[public["Worlds"], "WorldID"] ->
  public["Worlds"]];
oracleByID = AssociationThread[Lookup[oracle["Worlds"], "WorldID"] ->
  oracle["Worlds"]];
truthByID = AssociationThread[Lookup[truth["Worlds"], "WorldID"] ->
  truth["Worlds"]];

HexSHA256C1[path_String] := IntegerString[FileHash[path, "SHA256"], 16, 64];

EvalIndependentC1[ast_List, coordinate_List] := Switch[First[ast],
  "Var", coordinate[[ast[[2]]]], "Const", ast[[2]],
  "Add", EvalIndependentC1[ast[[2]], coordinate] +
    EvalIndependentC1[ast[[3]], coordinate],
  "Sub", EvalIndependentC1[ast[[2]], coordinate] -
    EvalIndependentC1[ast[[3]], coordinate],
  "Mul", EvalIndependentC1[ast[[2]], coordinate]
    EvalIndependentC1[ast[[3]], coordinate],
  "Mod", Mod[EvalIndependentC1[ast[[2]], coordinate],
    EvalIndependentC1[ast[[3]], coordinate]],
  "BitXor", BitXor[EvalIndependentC1[ast[[2]], coordinate],
    EvalIndependentC1[ast[[3]], coordinate]],
  "Eq", EvalIndependentC1[ast[[2]], coordinate] ===
    EvalIndependentC1[ast[[3]], coordinate],
  "Lt", EvalIndependentC1[ast[[2]], coordinate] <
    EvalIndependentC1[ast[[3]], coordinate],
  "If", If[TrueQ[EvalIndependentC1[ast[[2]], coordinate]],
    EvalIndependentC1[ast[[3]], coordinate],
    EvalIndependentC1[ast[[4]], coordinate]],
  _, $Failed];

ProgramMismatchCountC1[world_Association, table_List, programs_] := Module[
  {count = 0, predicted, target}, If[programs === Null, Return[Null]];
  Do[
    predicted = EvalIndependentC1[#, world["Phi"][[state]]] & /@
      programs[[action]];
    target = world["Phi"][[table[[state, action]]]];
    If[predicted =!= target, count++],
    {state, world["StateCount"]}, {action, world["ActionCount"]}];
  count];

GeneratorTableMismatchCountC1[world_Association, table_List,
  programs_List] := Module[{count = 0, coordinate, target, targetState},
  Do[
    coordinate = world["Phi"][[state]];
    target = EvalIndependentC1[#, coordinate] & /@ programs[[action]];
    targetState = FirstPosition[world["Phi"], target, Missing["NotFound"]];
    If[MissingQ[targetState] || First[targetState] =!= table[[state, action]], count++],
    {state, world["StateCount"]}, {action, world["ActionCount"]}];
  count];

ObservationAuditC1[world_Association, table_List, run_Association] := Module[
  {observations = run["Observations"], keys, truthPass},
  keys = ({#["State"], #["Action"]} &) /@ observations;
  truthPass = And @@ Table[
    record["TargetCoordinate"] ===
      world["Phi"][[table[[record["State"], record["Action"]]]]],
    {record, observations}];
  <|"NoDuplicateQueries" ->
      (Length[keys] === Length[DeleteDuplicates[keys]]),
    "OracleAnswersExact" -> truthPass,
    "QueryCountExact" ->
      (Length[observations] === run["MembershipQueryCount"])|>];

RunClaimAuditC1[world_Association, table_List, run_Association] := Module[
  {mismatches = ProgramMismatchCountC1[world, table, run["Programs"]]},
  <|"MismatchCount" -> mismatches,
    "ClaimConsistent" -> If[TrueQ[run["ExactCertified"]],
      mismatches === 0, run["Programs"] === Null],
    "ObservationAudit" -> ObservationAuditC1[world, table, run]|>];

formalAudits = Table[
  world = publicByID[row["WorldID"]];
  table = oracleByID[row["WorldID"]]["TransitionTable"];
  <|"WorldID" -> row["WorldID"],
    "Active" -> RunClaimAuditC1[world, table, row["Active"]],
    "Passive" -> RunClaimAuditC1[world, table, row["Passive"]],
    "GeneratorTableMismatchCount" -> GeneratorTableMismatchCountC1[
      world, table, truthByID[row["WorldID"]]["GeneratorPrograms"]]|>,
  {row, result["FormalResults"]}];

challengeAudits = Table[
  world = publicByID[row["WorldID"]];
  table = oracleByID[row["WorldID"]]["TransitionTable"];
  <|"WorldID" -> row["WorldID"],
    "Active" -> RunClaimAuditC1[world, table, row["Active"]],
    "GeneratorTableMismatchCount" -> GeneratorTableMismatchCountC1[
      world, table, truthByID[row["WorldID"]]["GeneratorPrograms"]]|>,
  {row, result["ChallengeResults"]}];

randomAudits = Table[
  world = publicByID[row["WorldID"]];
  If[TrueQ[row["GenerationFailed"]],
    <|"WorldID" -> row["WorldID"], "GenerationFailed" -> True,
      "ClaimConsistent" -> False|>,
    mismatches = ProgramMismatchCountC1[world, row["TransitionTable"],
      row["Programs"]];
    observations = row["Observations"];
    observationPass = And @@ Table[
      record["TargetCoordinate"] === world["Phi"][[
        row["TransitionTable"][[record["State"], record["Action"]]]]],
      {record, observations}];
    <|"WorldID" -> row["WorldID"], "GenerationFailed" -> False,
      "MismatchCount" -> mismatches,
      "ClaimConsistent" -> If[TrueQ[row["ExactCertified"]],
        mismatches === 0, row["Programs"] === Null],
      "ObservationAnswersExact" -> observationPass|>],
  {row, result["RandomControls"]}];

formalClaimsPass = And @@ Flatten@Table[
  formalAudits[[index, mode, "ClaimConsistent"]],
  {index, Length[formalAudits]}, {mode, {"Active", "Passive"}}];
formalLogsPass = And @@ Flatten@Table[
  And @@ Values[formalAudits[[index, mode, "ObservationAudit"]]],
  {index, Length[formalAudits]}, {mode, {"Active", "Passive"}}];
challengeClaimsPass = And @@ Lookup[Lookup[challengeAudits, "Active"],
  "ClaimConsistent"];
challengeLogsPass = And @@ Table[
  And @@ Values[challengeAudits[[index, "Active", "ObservationAudit"]]],
  {index, Length[challengeAudits]}];
generatorTablesPass = Lookup[formalAudits,
    "GeneratorTableMismatchCount"] === ConstantArray[0, Length[formalAudits]] &&
  Lookup[challengeAudits, "GeneratorTableMismatchCount"] ===
    ConstantArray[0, Length[challengeAudits]];
randomGenerationPass = !MemberQ[Lookup[result["RandomControls"],
  "GenerationFailed"], True];
randomClaimsPass = And @@ Lookup[randomAudits, "ClaimConsistent"] &&
  And @@ Lookup[randomAudits, "ObservationAnswersExact", False];
nearPass = result["NearLawPass"] ===
  And @@ Lookup[result["NearLawControls"], "MutationDetected"];
relabelPass = result["StateRelabelingPass"] === And @@ Flatten[{
  Lookup[result["StateRelabelingControls"], "CoordinateDatasetHashInvariant"],
  Lookup[result["StateRelabelingControls"], "FrozenProgramStillExact"]}];

publicForbidden = {"TransitionTable", "GeneratorPrograms", "WorldType",
  "Modulus", "Offset", "Seed"};
publicBoundaryPass = And @@ Table[
  Intersection[Keys[world], publicForbidden] === {}, {world, public["Worlds"]}];
freezeHashPass = And @@ {
  HexSHA256C1[FileNameJoin[{rootDirectory, "protocol",
      "S129C1_pre_world_manifest.json"}]] === receipt["PreWorldManifestSHA256"],
  HexSHA256C1[FileNameJoin[{sourceDirectory,
      "TCCT_S129C1_FreshBlindConfirmationBuilder.py"}]] === manifest["BuilderSHA256"],
  HexSHA256C1[FileNameJoin[{sourceDirectory,
      "TCCT_S129C1_FreshBlindConfirmation.wl"}]] === manifest["RunnerSHA256"],
  HexSHA256C1[$InputFileName] === manifest["VerifierSHA256"],
  HexSHA256C1[FileNameJoin[{sourceDirectory,
      "TCCT_S129B8A_IncrementalCompleteSearch.wl"}]] ===
    manifest["FrozenB8ASourceSHA256"],
  HexSHA256C1[FileNameJoin[{rootDirectory, "input",
      "S129C1_public_input.json"}]] === receipt["PublicInputSHA256"],
  HexSHA256C1[FileNameJoin[{rootDirectory, "oracle",
      "S129C1_oracle_tables.json"}]] === receipt["OracleTablesSHA256"],
  HexSHA256C1[FileNameJoin[{rootDirectory, "sealed",
      "S129C1_generator_truth.json"}]] === receipt["SealedTruthSHA256"]};

inBoundDecisionPass = result["InBoundExactCount"] ===
  Length[manifest["InBoundWorldSpecifications"]];
randomDecisionPass = result["RandomControlExactCount"] === 0 &&
  randomGenerationPass;
primaryPass = freezeHashPass && publicBoundaryPass && generatorTablesPass &&
  formalClaimsPass && formalLogsPass && challengeClaimsPass &&
  challengeLogsPass && randomClaimsPass && inBoundDecisionPass &&
  randomDecisionPass && nearPass && relabelPass &&
  !TrueQ[result["GeneratorTruthRead"]] &&
  !TrueQ[result["PriorProgramsLoaded"]] &&
  !TrueQ[result["PerWorldTemplatesAdded"]] &&
  !TrueQ[result["SolverBasedResampling"]] &&
  !TrueQ[result["B8AAlgorithmModified"]];

verification = <|
  "Stage" -> "S129-C1 independent verification",
  "FreezeHashPass" -> freezeHashPass,
  "PublicLearnerBoundaryPass" -> publicBoundaryPass,
  "GeneratorTablesRecomputedExactly" -> generatorTablesPass,
  "FormalExactClaimsRecomputed" -> formalClaimsPass,
  "FormalObservationLogsValid" -> formalLogsPass,
  "ChallengeClaimsSafe" -> challengeClaimsPass,
  "ChallengeObservationLogsValid" -> challengeLogsPass,
  "RandomControlsGenerated" -> randomGenerationPass,
  "RandomClaimsConsistent" -> randomClaimsPass,
  "InBoundDecisionPass" -> inBoundDecisionPass,
  "RandomFalseExactDecisionPass" -> randomDecisionPass,
  "NearLawControlPass" -> nearPass,
  "StateRelabelingControlPass" -> relabelPass,
  "FormalAudits" -> formalAudits,
  "ChallengeAudits" -> challengeAudits,
  "RandomAudits" -> randomAudits,
  "IndependentVerificationPass" -> primaryPass|>;
Export[FileNameJoin[{verificationDirectory,
  "S129C1_independent_verification.json"}], verification,
  "RawJSON", "Compact" -> False];
Print["S129-C1 INDEPENDENT VERIFICATION PASS=", primaryPass];
Exit[If[primaryPass, 0, 1]];
