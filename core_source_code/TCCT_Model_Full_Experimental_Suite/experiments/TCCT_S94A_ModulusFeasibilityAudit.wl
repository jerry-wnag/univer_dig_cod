(* TCCT S94A - post-hoc modulus feasibility audit.
   Run only in the still-live S94 kernel. This file does not rerun graph traces,
   select a new model, change the frozen decoder, or make a blind-test claim. *)

ClearAll[JSONCountRows94A];
JSONCountRows94A[values_List] := KeyValueMap[
  <|"Value" -> #1, "Count" -> #2|> &,
  Counts[values]
];

requiredStateAvailable94A = And[
  ValueQ[blindPairs94],
  ValueQ[blindWorlds94],
  ValueQ[summary94],
  ValueQ[cert94],
  ValueQ[pairDecoderLoaded94],
  ValueQ[modelHashBefore94],
  ValueQ[coreHashBefore94],
  ValueQ[canonicalizerHashBefore94],
  ValueQ[interventionHashBefore94],
  ValueQ[topologyPrimitiveHashBefore94],
  ValueQ[baseRuntimeDefinitionHashBefore94],
  ValueQ[pairRuntimeDefinitionHashBefore94]
];

If[!TrueQ[requiredStateAvailable94A],
  Print["S94A aborted: the live S94 variables are unavailable."];
  Print["Return to the completed S94 notebook without restarting its kernel, then run this file."];
  Abort[]
];

expectedProtocolHash94A =
  "4e0e41ef24649fde483e2e362e6bf83ffdc589da8ee3ae72f5e4caa6b5b91fd1";
expectedCandidateHash94A =
  "540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c";
expectedBlindResultHash94A =
  "157b0ed8c3b106fc6f7aa31fae21382b0f238dccaeb48e1b3f2b2f381732925e";
auditCertificatePath94A =
  "E:/engine_wolf/TCCT_S94A_ModulusFeasibilityAudit.json";

If[FileExistsQ[auditCertificatePath94A] &&
    FileByteCount[auditCertificatePath94A] > 0,
  Print["S94A aborted: an audit certificate already exists; preserve it."];
  Abort[]
];

stateLockPassed94A = And[
  SameQ[Length[blindPairs94], 52],
  SameQ[Length[blindWorlds94], 104],
  SameQ[cert94["ProtocolHash"], expectedProtocolHash94A],
  SameQ[cert94["CandidateHash"], expectedCandidateHash94A],
  SameQ[cert94["BlindResultHash"], expectedBlindResultHash94A],
  SameQ[cert94["Outcome"], "S94_INVALID_BLIND_TEST_DO_NOT_INTERPRET"],
  SameQ[summary94["CardinalityPairsMatched"], 26],
  SameQ[summary94["UnknownPredictions"], 104],
  SameQ[pairDecoderLoaded94["ContrastPosition"], 3],
  SameQ[pairDecoderLoaded94["Modulus"], 33],
  SameQ[Sort[Keys[pairDecoderLoaded94["Policy"]]], {6, 27}]
];

If[!TrueQ[stateLockPassed94A],
  Print["S94A aborted: the live state does not match the locked invalid S94 run."];
  Abort[]
];

modelHashAuditBefore94A = Hash[Normal[frozen75D], "SHA256", "HexString"];
coreHashAuditBefore94A = Hash[CoreDefinitionBundle94[], "SHA256", "HexString"];
canonicalizerHashAuditBefore94A = Hash[{
  DownValues[FindPrivateDiamond79B],
  DownValues[CanonicalizePrivateDiamonds79B],
  DownValues[CanonicalCase79B]
}, "SHA256", "HexString"];
interventionHashAuditBefore94A = Hash[{
  DownValues[LocalMediatorSources82],
  DownValues[FullSemanticPatch82],
  DownValues[LocalMediatorPatch82],
  DownValues[ReferenceAction82]
}, "SHA256", "HexString"];
topologyHashAuditBefore94A = Hash[{
  DownValues[DiamondIn72],
  DownValues[DoubleDiamondIn79],
  DownValues[HierarchicalDiamondIn80]
}, "SHA256", "HexString"];
baseRuntimeHashAuditBefore94A = Hash[TCCTFrozenFeatureDefinitionBundleS87D[],
  "SHA256", "HexString"];
pairRuntimeHashAuditBefore94A = Hash[PairRuntimeDefinitionBundle94[],
  "SHA256", "HexString"];

rawForwardDifferences94A = Table[
  Map[
    Function[pair,
      pair["ContinueWorld"]["FeatureVector"][[position]] -
        pair["StopWorld"]["FeatureVector"][[position]]
    ],
    blindPairs94
  ],
  {position, 27}
];

rawPositionRows94A = Table[
  Module[{forward, reverse},
    forward = rawForwardDifferences94A[[position]];
    reverse = -forward;
    <|
      "Position" -> position,
      "RawZeroCount" -> Count[forward, 0],
      "RawForwardUniqueCount" -> Length[DeleteDuplicates[forward]],
      "RawReverseUniqueCount" -> Length[DeleteDuplicates[reverse]],
      "RawOrientationIntersectionCount" ->
        Length[Intersection[DeleteDuplicates[forward], DeleteDuplicates[reverse]]],
      "RawOrientationDisjoint" ->
        SameQ[Intersection[DeleteDuplicates[forward], DeleteDuplicates[reverse]], {}]
    |>
  ],
  {position, 27}
];

modulusRows94A = Flatten[
  Table[
    Module[{forward, reverse},
      forward = Mod[rawForwardDifferences94A[[position]], modulus];
      reverse = Mod[-rawForwardDifferences94A[[position]], modulus];
      <|
        "Position" -> position,
        "Modulus" -> modulus,
        "OrientationDisjoint" ->
          SameQ[Intersection[DeleteDuplicates[forward], DeleteDuplicates[reverse]], {}],
        "ForwardUniqueCount" -> Length[DeleteDuplicates[forward]],
        "ReverseUniqueCount" -> Length[DeleteDuplicates[reverse]]
      |>
    ],
    {position, 27}, {modulus, 2, 4096}
  ],
  1
];

perfectModulusRows94A = Select[
  modulusRows94A,
  TrueQ[Lookup[#, "OrientationDisjoint", False]] &
];
positionsWithPerfectModulus94A = Sort[DeleteDuplicates[
  Lookup[perfectModulusRows94A, "Position", {}]
]];
minimumPerfectModulusRows94A = Map[
  First[SortBy[#, Lookup[#, "Modulus"] &]] &,
  GatherBy[perfectModulusRows94A, Lookup[#, "Position"] &]
];

position3ForwardRaw94A = rawForwardDifferences94A[[3]];
position3ZeroPairIndices94A = Flatten[Position[position3ForwardRaw94A, 0]];
position3ZeroPairRows94A = Map[
  Function[index,
    With[{pair = blindPairs94[[index]]},
      <|
        "PairIndex" -> index,
        "Topology" -> pair["ContinueWorld"]["Topology"],
        "Depth" -> pair["ContinueWorld"]["Depth"],
        "Answer" -> pair["Answer"]
      |>
    ]
  ],
  position3ZeroPairIndices94A
];
position3PerfectModuli94A = Lookup[
  Select[perfectModulusRows94A, SameQ[Lookup[#, "Position"], 3] &],
  "Modulus",
  {}
];

forwardDeltaMod33Rows94A = JSONCountRows94A[
  Mod[position3ForwardRaw94A, 33]
];
reverseDeltaMod33Rows94A = JSONCountRows94A[
  Mod[-position3ForwardRaw94A, 33]
];
frozenSupportedDeltas94A = Sort[Keys[pairDecoderLoaded94["Policy"]]];
supportedForwardCases94A = Count[
  Mod[position3ForwardRaw94A, 33],
  Alternatives @@ frozenSupportedDeltas94A
];

worldRows94A = Join[
  Map[<|"Target" -> "Continue", "Vector" ->
      #["ContinueWorld"]["FeatureVector"]|> &, blindPairs94],
  Map[<|"Target" -> "Stop", "Vector" ->
      #["StopWorld"]["FeatureVector"]|> &, blindPairs94]
];
fullVectorGroups94A = GatherBy[worldRows94A, Lookup[#, "Vector"] &];
crossLabelAliasGroups94A = Select[
  fullVectorGroups94A,
  Length[DeleteDuplicates[Lookup[#, "Target"]]] > 1 &
];

modelHashAuditAfter94A = Hash[Normal[frozen75D], "SHA256", "HexString"];
coreHashAuditAfter94A = Hash[CoreDefinitionBundle94[], "SHA256", "HexString"];
canonicalizerHashAuditAfter94A = Hash[{
  DownValues[FindPrivateDiamond79B],
  DownValues[CanonicalizePrivateDiamonds79B],
  DownValues[CanonicalCase79B]
}, "SHA256", "HexString"];
interventionHashAuditAfter94A = Hash[{
  DownValues[LocalMediatorSources82],
  DownValues[FullSemanticPatch82],
  DownValues[LocalMediatorPatch82],
  DownValues[ReferenceAction82]
}, "SHA256", "HexString"];
topologyHashAuditAfter94A = Hash[{
  DownValues[DiamondIn72],
  DownValues[DoubleDiamondIn79],
  DownValues[HierarchicalDiamondIn80]
}, "SHA256", "HexString"];
baseRuntimeHashAuditAfter94A = Hash[TCCTFrozenFeatureDefinitionBundleS87D[],
  "SHA256", "HexString"];
pairRuntimeHashAuditAfter94A = Hash[PairRuntimeDefinitionBundle94[],
  "SHA256", "HexString"];

integrityPassed94A = And[
  SameQ[modelHashAuditBefore94A, modelHashAuditAfter94A, modelHashBefore94],
  SameQ[coreHashAuditBefore94A, coreHashAuditAfter94A, coreHashBefore94],
  SameQ[canonicalizerHashAuditBefore94A,
    canonicalizerHashAuditAfter94A, canonicalizerHashBefore94],
  SameQ[interventionHashAuditBefore94A,
    interventionHashAuditAfter94A, interventionHashBefore94],
  SameQ[topologyHashAuditBefore94A,
    topologyHashAuditAfter94A, topologyPrimitiveHashBefore94],
  SameQ[baseRuntimeHashAuditBefore94A,
    baseRuntimeHashAuditAfter94A, baseRuntimeDefinitionHashBefore94],
  SameQ[pairRuntimeHashAuditBefore94A,
    pairRuntimeHashAuditAfter94A, pairRuntimeDefinitionHashBefore94]
];

auditValidityPassed94A = And[
  TrueQ[stateLockPassed94A],
  TrueQ[integrityPassed94A],
  SameQ[Count[position3ForwardRaw94A, 0], 4],
  SameQ[position3PerfectModuli94A, {}],
  SameQ[positionsWithPerfectModulus94A, {6}],
  SameQ[Lookup[minimumPerfectModulusRows94A, "Modulus"], {78}],
  SameQ[supportedForwardCases94A, 0],
  SameQ[Length[crossLabelAliasGroups94A], 0]
];

auditPayload94A = <|
  "Stage" -> "S94A",
  "Name" -> "PostHocModulusFeasibilityAudit",
  "AuditOnly" -> True,
  "UsesRevealedS94Labels" -> True,
  "MayClaimBlindResult" -> False,
  "SourceS94Outcome" -> cert94["Outcome"],
  "SourceS94BlindResultHash" -> cert94["BlindResultHash"],
  "CandidateHash" -> pairDecoderLoaded94["CandidateHash"],
  "FrozenContrastPosition" -> pairDecoderLoaded94["ContrastPosition"],
  "FrozenModulus" -> pairDecoderLoaded94["Modulus"],
  "FrozenSupportedDeltas" -> frozenSupportedDeltas94A,
  "PairsAudited" -> Length[blindPairs94],
  "Position3RawZeroCount" -> Count[position3ForwardRaw94A, 0],
  "Position3ZeroPairs" -> position3ZeroPairRows94A,
  "Position3PerfectModuli2Through4096" -> position3PerfectModuli94A,
  "Position3CanBeRepairedByModulusAlone" -> False,
  "ForwardDeltaMod33Distribution" -> forwardDeltaMod33Rows94A,
  "ReverseDeltaMod33Distribution" -> reverseDeltaMod33Rows94A,
  "FrozenSupportedForwardCases" -> supportedForwardCases94A,
  "PositionsWithAnyPerfectModulus2Through4096" ->
    positionsWithPerfectModulus94A,
  "MinimumPerfectModulusByPosition" -> minimumPerfectModulusRows94A,
  "ExactFullVectorCrossLabelAliasGroups" -> Length[crossLabelAliasGroups94A],
  "FullVectorRetainsDistinguishingInformation" ->
    SameQ[Length[crossLabelAliasGroups94A], 0],
  "DynamicModulusSelected" -> False,
  "FeaturePositionChanged" -> False,
  "DecoderPolicyChanged" -> False,
  "TrainingRun" -> False,
  "CandidateSearchRun" -> False,
  "OriginalFrozenModelChanged" ->
    !SameQ[modelHashAuditBefore94A, modelHashAuditAfter94A],
  "CoreChanged" -> !SameQ[coreHashAuditBefore94A, coreHashAuditAfter94A],
  "CanonicalizerChanged" ->
    !SameQ[canonicalizerHashAuditBefore94A, canonicalizerHashAuditAfter94A],
  "InterventionCoreChanged" ->
    !SameQ[interventionHashAuditBefore94A, interventionHashAuditAfter94A],
  "TopologyPrimitivesChanged" ->
    !SameQ[topologyHashAuditBefore94A, topologyHashAuditAfter94A],
  "BaseFeatureRuntimeChanged" ->
    !SameQ[baseRuntimeHashAuditBefore94A, baseRuntimeHashAuditAfter94A],
  "PairRuntimeChanged" ->
    !SameQ[pairRuntimeHashAuditBefore94A, pairRuntimeHashAuditAfter94A],
  "AuditValidityPassed" -> auditValidityPassed94A,
  "Diagnosis" ->
    "POSITION3_HAS_ZERO_AND_CONTEXT_DEPENDENT_DIFFERENCES_MODULUS_ALONE_INSUFFICIENT",
  "Interpretation" ->
    "FULL_VECTOR_RETAINS_SIGNAL_BUT_FROZEN_POSITION3_MOD33_READOUT_IS_NOT_CONTEXT_INVARIANT",
  "Outcome" -> If[
    TrueQ[auditValidityPassed94A],
    "S94A_AUDIT_PASS_MODULUS_ALONE_INSUFFICIENT",
    "S94A_AUDIT_INVALID"
  ],
  "SuggestedNextStage" ->
    "S94B_DEVELOPMENT_ONLY_LABEL_FREE_ADAPTIVE_READOUT_DESIGN"
|>;

auditResultHash94A = Hash[Normal[auditPayload94A], "SHA256", "HexString"];
auditCertificate94A = Append[auditPayload94A,
  "AuditResultHash" -> auditResultHash94A
];

auditExportResult94A = Quiet@Check[
  Export[auditCertificatePath94A, auditCertificate94A, "RawJSON"],
  $Failed
];
auditCertificateExported94A = StringQ[auditExportResult94A] &&
  FileExistsQ[auditCertificatePath94A] &&
  FileByteCount[auditCertificatePath94A] > 0;

Column[{
  Dataset[{auditCertificate94A}],
  Dataset[rawPositionRows94A],
  Dataset[{<|
    "AuditCertificateExported" -> auditCertificateExported94A,
    "AuditCertificatePath" -> auditCertificatePath94A,
    "AuditCertificateBytes" -> If[
      FileExistsQ[auditCertificatePath94A],
      FileByteCount[auditCertificatePath94A],
      0
    ]
  |> }]
}]
