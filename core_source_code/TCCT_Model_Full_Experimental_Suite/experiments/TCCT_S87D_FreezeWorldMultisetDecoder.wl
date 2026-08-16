(* TCCT S87D CELL
   Freeze the already-selected S87C world-multiset decoder before S88 exists.
   Run this cell only in the current, completed S87C kernel. *)

s87DStateAvailable = And[
  ValueQ[allWorlds87A],
  ValueQ[cert87A],
  ValueQ[cert87B],
  ValueQ[cert87C],
  ValueQ[bestResult87C],
  ListQ[allWorlds87A],
  SameQ[Length[allWorlds87A], 392],
  TrueQ[cert87A["AuditValidityPassed"]],
  TrueQ[cert87B["ResearchValidityPassed"]],
  TrueQ[cert87C["ResearchValidityPassed"]],
  TrueQ[cert87C["WorldMultisetDecoderCandidateFound"]],
  SameQ[cert87C["Outcome"],
    "S87C_WORLD_MULTISET_DECODER_CANDIDATE_FOUND_NOT_FROZEN"],
  SameQ[bestResult87C["Family"], "QueriedGlobalMoments"],
  SameQ[bestResult87C["FeatureDimension"], 27],
  SameQ[bestResult87C["PerfectFolds"], 11],
  SameQ[bestResult87C["FullScore"], 392],
  Head[bestResult87C["FullClassifier"]] === ClassifierFunction
];

If[
  !TrueQ[s87DStateAvailable],
  Print["S87D aborted: the completed and valid S87C runtime state is missing."];
  Print["Return to TCCT_S87A_SevenBranchFailureAudit.ipynb and run S87A-S87C first."];
  Abort[]
];

expectedFrozenModelHash87D =
  "d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash87D =
  "2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";

s87DRuntimePath =
  "E:\\engine_wolf\\TCCT_S87D_FrozenDecoderRuntime.wl";
s87DCandidatePath =
  "E:\\engine_wolf\\TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
s87DMetadataPath =
  "E:\\engine_wolf\\TCCT_S87D_FrozenWorldMultisetDecoder_Metadata.wl";
s87DCertificatePath =
  "E:\\engine_wolf\\TCCT_S87D_FreezeCertificate.json";

If[
  !FileExistsQ[s87DRuntimePath],
  Print["S87D aborted: frozen feature runtime file is missing: ", s87DRuntimePath];
  Abort[]
];

modelHashBefore87D = Hash[Normal[frozen75D], "SHA256", "HexString"];
candidateHashBefore87D =
  Hash[Normal[frozenCandidate86E], "SHA256", "HexString"];
coreHashBefore87D = Hash[CoreDefinitionBundle87[], "SHA256", "HexString"];
canonicalizerHashBefore87D = Hash[
  {
    DownValues[FindPrivateDiamond79B],
    DownValues[CanonicalizePrivateDiamonds79B],
    DownValues[CanonicalCase79B]
  },
  "SHA256", "HexString"
];
interventionHashBefore87D = Hash[
  {
    DownValues[LocalMediatorSources82],
    DownValues[FullSemanticPatch82],
    DownValues[LocalMediatorPatch82],
    DownValues[ReferenceAction82]
  },
  "SHA256", "HexString"
];
topologyHashBefore87D = Hash[
  {DownValues[DoubleDiamondIn79], DownValues[HierarchicalDiamondIn80]},
  "SHA256", "HexString"
];
s87DefinitionHashBefore87D = Hash[
  S87TestDefinitionBundle[], "SHA256", "HexString"
];
s87CDefinitionHashBefore87D = Hash[
  S87CDefinitionBundle[], "SHA256", "HexString"
];
s87CInputDataHashBefore87D = Hash[
  Normal[auditDataPayload87B], "SHA256", "HexString"
];
k33CandidateFileHashBefore87D = FileHash[k33CandidatePath87, "SHA256"];
s87DRuntimeFileHashBefore = FileHash[s87DRuntimePath, "SHA256"];

Get[s87DRuntimePath];

s87DFeatureDefinitionHashBefore = Hash[
  TCCTFrozenFeatureDefinitionBundleS87D[], "SHA256", "HexString"
];

s87CVectorsForFreeze =
  (WorldVector87C[#, "QueriedGlobalMoments"] &) /@ allWorlds87A;
s87DVectorsForFreeze = TCCTWorldVectorS87D /@ allWorlds87A;
s87DFeatureParityPassed = SameQ[s87CVectorsForFreeze, s87DVectorsForFreeze];
s87DFeatureDimensionsPassed = And @@ (
  Function[vector, VectorQ[vector, IntegerQ] && Length[vector] === 27] /@
    s87DVectorsForFreeze
);

s87DClassifier = bestResult87C["FullClassifier"];
s87DTargets = Lookup[allWorlds87A, "Target"];
s87DPredictionsBeforeExport = Quiet@Check[
  s87DClassifier /@ s87DVectorsForFreeze,
  $Failed
];
s87DScoreBeforeExport = If[
  ListQ[s87DPredictionsBeforeExport],
  ScorePredictions87C[allWorlds87A, s87DPredictionsBeforeExport],
  $Failed
];

If[
  !TrueQ[s87DFeatureParityPassed] ||
  !TrueQ[s87DFeatureDimensionsPassed] ||
  !AssociationQ[s87DScoreBeforeExport] ||
  !SameQ[s87DScoreBeforeExport["Score"], 392] ||
  !SameQ[s87DScoreBeforeExport["ContinueCorrect"],
    s87DScoreBeforeExport["ContinueCases"]] ||
  !SameQ[s87DScoreBeforeExport["StopCorrect"],
    s87DScoreBeforeExport["StopCases"]],
  Print["S87D aborted: feature parity or pre-export prediction lock failed."];
  Abort[]
];

s87DClassifierBinary = BinarySerialize[s87DClassifier];
s87DClassifierBinaryHash = Hash[
  s87DClassifierBinary, "SHA256", "HexString"
];

s87DProtocol = <|
  "Stage" -> "S87D",
  "Name" -> "FreezeWorldMultisetDecoder",
  "Purpose" -> "FreezeSelectedS87CDecoderBeforeS88",
  "ResearchSourceStage" -> "S87C",
  "UsesRevealedS87Labels" -> True,
  "BlindTest" -> False,
  "S88DesignedBeforeFreeze" -> False,
  "S88DataAvailableToFreeze" -> False,
  "S88BlindTestRun" -> False,
  "FeatureFamily" -> "QueriedGlobalMoments",
  "FeatureDimension" -> 27,
  "FeatureInputs" -> {"QueryBranchRelated", "Code"},
  "ForbiddenFeatureInputs" -> {
    "Topology", "Depth", "InterventionPair", "Answer",
    "GraphCondition", "Target"
  },
  "Classifier" -> "FrozenBalancedDecisionTree",
  "OriginalTrainingSeed" -> 870399,
  "TrainingBalance" -> "StopRowsRepeatedToMatchContinueRows",
  "CoreEditApplied" -> False,
  "OriginalFrozenPolicyEditApplied" -> False,
  "OuterDecoderAdded" -> True,
  "CandidateSearchRun" -> False,
  "DecoderRetrainedInS87D" -> False
|>;
s87DProtocolHash = Hash[
  Normal[s87DProtocol], "SHA256", "HexString"
];

s87DCandidatePayload = <|
  "Stage" -> "S87D",
  "Name" -> "FrozenWorldMultisetDecoder",
  "FrozenBeforeS88" -> True,
  "ResearchSourceStage" -> "S87C",
  "FeatureFamily" -> "QueriedGlobalMoments",
  "FeatureDimension" -> 27,
  "FeatureNames" -> TCCTFeatureNamesS87D[],
  "FeatureInputs" -> {"QueryBranchRelated", "Code"},
  "K" -> 33,
  "BaseFrozenModelHash" -> modelHashBefore87D,
  "BaseK33CandidateHash" -> candidateHashBefore87D,
  "S87CInputDataHash" -> s87CInputDataHashBefore87D,
  "S87CDefinitionHash" -> s87CDefinitionHashBefore87D,
  "FeatureRuntimeFileName" -> FileNameTake[s87DRuntimePath],
  "FeatureRuntimeFileHash" -> s87DRuntimeFileHashBefore,
  "FeatureDefinitionHash" -> s87DFeatureDefinitionHashBefore,
  "ClassifierMethod" -> "DecisionTree",
  "ClassifierSeed" -> 870399,
  "ClassifierBinary" -> s87DClassifierBinary,
  "ClassifierBinaryHash" -> s87DClassifierBinaryHash,
  "DevelopmentWorlds" -> 392,
  "DevelopmentScore" -> s87DScoreBeforeExport["Score"],
  "DevelopmentContinueCorrect" ->
    s87DScoreBeforeExport["ContinueCorrect"],
  "DevelopmentContinueCases" ->
    s87DScoreBeforeExport["ContinueCases"],
  "DevelopmentStopCorrect" -> s87DScoreBeforeExport["StopCorrect"],
  "DevelopmentStopCases" -> s87DScoreBeforeExport["StopCases"],
  "GroupedHoldoutFolds" -> 11,
  "GroupedHoldoutPerfectFolds" -> 11,
  "UsesRevealedS87Labels" -> True,
  "MayClaimBlindGeneralization" -> False,
  "S88DataReadBeforeFreeze" -> False,
  "ProtocolHash" -> s87DProtocolHash,
  "WolframVersion" -> $Version,
  "SystemID" -> $SystemID
|>;
s87DCandidateHash = Hash[
  Normal[s87DCandidatePayload], "SHA256", "HexString"
];
frozenDecoder87D = Append[
  s87DCandidatePayload,
  "CandidateHash" -> s87DCandidateHash
];

s87DExistingCandidateCompatible = False;
s87DCandidateCreatedThisRun = !FileExistsQ[s87DCandidatePath];
If[
  FileExistsQ[s87DCandidatePath],
  s87DExistingCandidate = Quiet@Check[
    Import[s87DCandidatePath, "WXF"], $Failed
  ];
  s87DExistingCandidateCompatible = And[
    AssociationQ[s87DExistingCandidate],
    SameQ[
      Lookup[s87DExistingCandidate, "CandidateHash", $Failed],
      s87DCandidateHash
    ]
  ];
  If[
    !TrueQ[s87DExistingCandidateCompatible],
    Print["S87D aborted: an incompatible candidate file already exists."];
    Print[s87DCandidatePath];
    Abort[]
  ],
  s87DExportResult = Quiet@Check[
    Export[s87DCandidatePath, frozenDecoder87D, "WXF"],
    $Failed
  ];
  If[SameQ[s87DExportResult, $Failed],
    Print["S87D aborted: candidate export failed."];
    Abort[]
  ]
];

s87DLoadedDecoder = TCCTLoadFrozenDecoderS87D[s87DCandidatePath];
s87DPredictionsAfterImport = If[
  AssociationQ[s87DLoadedDecoder],
  (TCCTPredictWorldS87D[#, s87DLoadedDecoder] &) /@ allWorlds87A,
  $Failed
];
s87DScoreAfterImport = If[
  ListQ[s87DPredictionsAfterImport],
  ScorePredictions87C[allWorlds87A, s87DPredictionsAfterImport],
  $Failed
];

s87DRoundTripPredictionParityPassed = SameQ[
  s87DPredictionsBeforeExport,
  s87DPredictionsAfterImport
];
s87DRoundTripScorePassed = And[
  AssociationQ[s87DScoreAfterImport],
  SameQ[s87DScoreAfterImport["Score"], 392],
  SameQ[s87DScoreAfterImport["ContinueCorrect"],
    s87DScoreAfterImport["ContinueCases"]],
  SameQ[s87DScoreAfterImport["StopCorrect"],
    s87DScoreAfterImport["StopCases"]]
];

If[
  !TrueQ[s87DRoundTripPredictionParityPassed] ||
  !TrueQ[s87DRoundTripScorePassed] ||
  !AssociationQ[s87DLoadedDecoder],
  If[
    TrueQ[s87DCandidateCreatedThisRun] && FileExistsQ[s87DCandidatePath],
    DeleteFile[s87DCandidatePath]
  ];
  Print["S87D aborted: exported decoder failed round-trip verification."];
  Abort[]
];

modelHashAfter87D = Hash[Normal[frozen75D], "SHA256", "HexString"];
candidateHashAfter87D =
  Hash[Normal[frozenCandidate86E], "SHA256", "HexString"];
coreHashAfter87D = Hash[CoreDefinitionBundle87[], "SHA256", "HexString"];
canonicalizerHashAfter87D = Hash[
  {
    DownValues[FindPrivateDiamond79B],
    DownValues[CanonicalizePrivateDiamonds79B],
    DownValues[CanonicalCase79B]
  },
  "SHA256", "HexString"
];
interventionHashAfter87D = Hash[
  {
    DownValues[LocalMediatorSources82],
    DownValues[FullSemanticPatch82],
    DownValues[LocalMediatorPatch82],
    DownValues[ReferenceAction82]
  },
  "SHA256", "HexString"
];
topologyHashAfter87D = Hash[
  {DownValues[DoubleDiamondIn79], DownValues[HierarchicalDiamondIn80]},
  "SHA256", "HexString"
];
s87DefinitionHashAfter87D = Hash[
  S87TestDefinitionBundle[], "SHA256", "HexString"
];
s87CDefinitionHashAfter87D = Hash[
  S87CDefinitionBundle[], "SHA256", "HexString"
];
s87CInputDataHashAfter87D = Hash[
  Normal[auditDataPayload87B], "SHA256", "HexString"
];
k33CandidateFileHashAfter87D = FileHash[k33CandidatePath87, "SHA256"];
s87DRuntimeFileHashAfter = FileHash[s87DRuntimePath, "SHA256"];
s87DFeatureDefinitionHashAfter = Hash[
  TCCTFrozenFeatureDefinitionBundleS87D[], "SHA256", "HexString"
];
s87DCandidateFileHash = FileHash[s87DCandidatePath, "SHA256"];
deduplicationMechanismUnchanged87D = And[
  SameQ[
    protocol87["TokenDeduplication"],
    "DeleteDuplicatesAfterExactRoleCodePairing"
  ],
  SameQ[coreHashBefore87D, coreHashAfter87D]
];

s87DIntegrityPassed = And[
  SameQ[modelHashBefore87D, expectedFrozenModelHash87D],
  SameQ[candidateHashBefore87D, expectedK33CandidateHash87D],
  SameQ[modelHashBefore87D, modelHashAfter87D],
  SameQ[candidateHashBefore87D, candidateHashAfter87D],
  SameQ[coreHashBefore87D, coreHashAfter87D],
  SameQ[canonicalizerHashBefore87D, canonicalizerHashAfter87D],
  SameQ[interventionHashBefore87D, interventionHashAfter87D],
  SameQ[topologyHashBefore87D, topologyHashAfter87D],
  SameQ[s87DefinitionHashBefore87D, s87DefinitionHashAfter87D],
  SameQ[s87CDefinitionHashBefore87D, s87CDefinitionHashAfter87D],
  SameQ[s87CInputDataHashBefore87D, s87CInputDataHashAfter87D],
  SameQ[k33CandidateFileHashBefore87D, k33CandidateFileHashAfter87D],
  SameQ[s87DRuntimeFileHashBefore, s87DRuntimeFileHashAfter],
  SameQ[
    s87DFeatureDefinitionHashBefore,
    s87DFeatureDefinitionHashAfter
  ],
  TrueQ[deduplicationMechanismUnchanged87D],
  TrueQ[s87DFeatureParityPassed],
  TrueQ[s87DFeatureDimensionsPassed],
  TrueQ[s87DRoundTripPredictionParityPassed],
  TrueQ[s87DRoundTripScorePassed],
  AssociationQ[s87DLoadedDecoder]
];

s87DMetadata = KeyDrop[frozenDecoder87D, {"ClassifierBinary"}];
Put[s87DMetadata, s87DMetadataPath];

cert87D = <|
  "Stage" -> "S87D",
  "Name" -> "FreezeWorldMultisetDecoder",
  "FreezeValidityPassed" -> s87DIntegrityPassed,
  "FeatureFamily" -> "QueriedGlobalMoments",
  "FeatureDimension" -> 27,
  "DevelopmentWorlds" -> 392,
  "DevelopmentScoreBeforeExport" -> s87DScoreBeforeExport["Score"],
  "DevelopmentScoreAfterImport" -> s87DScoreAfterImport["Score"],
  "GroupedHoldoutPerfectFolds" -> 11,
  "GroupedHoldoutFolds" -> 11,
  "FeatureParityPassed" -> s87DFeatureParityPassed,
  "RoundTripPredictionParityPassed" ->
    s87DRoundTripPredictionParityPassed,
  "RoundTripScorePassed" -> s87DRoundTripScorePassed,
  "CandidateExported" -> FileExistsQ[s87DCandidatePath],
  "CandidateHash" -> s87DCandidateHash,
  "CandidateFileHash" -> s87DCandidateFileHash,
  "ClassifierBinaryHash" -> s87DClassifierBinaryHash,
  "FeatureRuntimeFileHash" -> s87DRuntimeFileHashAfter,
  "ProtocolHash" -> s87DProtocolHash,
  "OriginalFrozenModelChanged" ->
    !SameQ[modelHashBefore87D, modelHashAfter87D],
  "OriginalK33CandidateChanged" ->
    !SameQ[candidateHashBefore87D, candidateHashAfter87D],
  "OriginalFrozenPolicyChanged" ->
    !SameQ[candidateHashBefore87D, candidateHashAfter87D],
  "CoreChanged" -> !SameQ[coreHashBefore87D, coreHashAfter87D],
  "CanonicalizerChanged" ->
    !SameQ[canonicalizerHashBefore87D, canonicalizerHashAfter87D],
  "InterventionChanged" ->
    !SameQ[interventionHashBefore87D, interventionHashAfter87D],
  "TopologyImplementationsChanged" ->
    !SameQ[topologyHashBefore87D, topologyHashAfter87D],
  "DeduplicationMechanismChanged" ->
    !TrueQ[deduplicationMechanismUnchanged87D],
  "OuterDecoderAdded" -> True,
  "UsesRevealedS87Labels" -> True,
  "MayClaimBlindGeneralization" -> False,
  "S88DataReadBeforeFreeze" -> False,
  "S88BlindTestRun" -> False,
  "ReadyForS88" -> s87DIntegrityPassed,
  "Outcome" -> If[
    TrueQ[s87DIntegrityPassed],
    "S87D_DECODER_FROZEN_AND_LOCKED_READY_FOR_S88",
    "S87D_FREEZE_INVALID"
  ]
|>;

Export[s87DCertificatePath, cert87D, "RawJSON"];
Dataset[{cert87D}]
