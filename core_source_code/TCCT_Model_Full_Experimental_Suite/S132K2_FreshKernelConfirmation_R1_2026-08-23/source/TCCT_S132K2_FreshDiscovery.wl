(* ::Package:: *)

(* S132-K2: fresh-world discovery using unchanged frozen S129-B8A. *)

ClearAll["Global`*"];
sourceDirectory = DirectoryName[$InputFileName];
rootDirectory = DirectoryName[sourceDirectory];
b8Path = FileNameJoin[{sourceDirectory,
  "TCCT_S129B8A_IncrementalCompleteSearch.wl"}];
b8Text = Import[b8Path, "Text"];
b8Marker = "Print[\"S129-B8A incremental bounded-complete search R1\"]";
b8Position = First@First@StringPosition[b8Text, b8Marker];
ToExpression[StringTake[b8Text, b8Position - 1], InputForm];

manifest = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K2_pre_world_manifest.json"}], "RawJSON"];
receipt = Import[FileNameJoin[{rootDirectory, "protocol",
  "S132K2_freeze_receipt.json"}], "RawJSON"];
public = Import[FileNameJoin[{rootDirectory, "input",
  "S132K2_public_input.json"}], "RawJSON"];
oracle = Import[FileNameJoin[{rootDirectory, "oracle",
  "S132K2_oracle_tables.json"}], "RawJSON"];

If[!TrueQ[receipt["WorldsMaterialized"]] ||
    TrueQ[receipt["CertifiedAutomataMaterialized"]],
  Print["FATAL: S132-K2 discovery phase order invalid"]; Exit[2]];

publicWorlds = public["Worlds"];
oracleByID = AssociationThread[Lookup[oracle["Worlds"], "WorldID"] ->
  oracle["Worlds"]];
$BasisCacheB7 = <||>;

Print["S132-K2 FRESH-WORLD TCCT DISCOVERY"];
Print["Generator truth=False; prior programs=False; B8A modified=False"];

formalResults = Table[Module[{world, table, built, active},
    world = publicWorlds[[index]];
    table = oracleByID[world["WorldID"]]["TransitionTable"];
    Print["FRESH DISCOVERY START ", world["WorldID"],
      " states=", world["StateCount"]];
    built = GetBasisB7[world];
    active = RunIncrementalLearnerB8[world, table, built["Basis"],
      built["Predicates"], "ACTIVE_INCREMENTAL"];
    Print["FRESH DISCOVERY END ", world["WorldID"],
      " outcome=", active["Outcome"],
      " q=", active["MembershipQueryCount"]];
    <|"WorldID" -> world["WorldID"],
      "StateCount" -> world["StateCount"],
      "ActionCount" -> world["ActionCount"],
      "CoordinateDimensions" -> world["CoordinateDimensions"],
      "BasisStatistics" -> built["Basis"]["Statistics"],
      "Active" -> active|>
  ], {index, Length[publicWorlds]}];

exactCount = Count[Lookup[Lookup[formalResults, "Active"],
  "ExactCertified"], True];
result = <|
  "Stage" -> "S132-K2 fresh-world TCCT discovery",
  "EvidenceStatus" -> manifest["EvidenceStatus"],
  "NativeWolframExecution" -> True,
  "WolframVersion" -> $Version,
  "FreshWorldsMaterializedAfterProtocolFreeze" -> True,
  "GeneratorTruthRead" -> False,
  "PriorProgramsLoaded" -> False,
  "CanonicalTCCTModified" -> False,
  "B8AAlgorithmModified" -> False,
  "DiscoveryExactCount" -> exactCount,
  "DiscoveryWorldCount" -> Length[formalResults],
  "FormalResults" -> formalResults|>;

Export[FileNameJoin[{rootDirectory, "discovery",
  "S132K2_discovery_result.json"}], result, "RawJSON", "Compact" -> False];
Print["S132-K2 DISCOVERY COMPLETE exact=", exactCount, "/",
  Length[formalResults]];
Exit[If[exactCount === Length[formalResults], 0, 1]];
