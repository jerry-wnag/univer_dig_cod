(* TCCT S87D frozen world-multiset decoder runtime.
   This file defines only the fixed 27-dimensional feature extractor and
   loader/predictor helpers. It performs no training and reads no blind data. *)

ClearAll[
  TCCTCodeStatsS87D,
  TCCTPairwiseStatsS87D,
  TCCTWorldVectorS87D,
  TCCTFeatureNamesS87D,
  TCCTFrozenFeatureDefinitionBundleS87D,
  TCCTLoadFrozenDecoderS87D,
  TCCTPredictWorldS87D
];

TCCTCodeStatsS87D[observations_List] := Module[
  {codes, a, b, delta, sum, product},
  codes = Lookup[observations, "Code", {}];
  If[Length[codes] === 0, Return[ConstantArray[0, 17]]];
  If[
    !And @@ Map[
      Function[code,
        VectorQ[code, IntegerQ] &&
        Length[code] === 2 &&
        And @@ (Between[#, {1, 33}] & /@ code)
      ],
      codes
    ],
    Return[$Failed]
  ];
  a = codes[[All, 1]];
  b = codes[[All, 2]];
  delta = Mod[a - b, 33];
  sum = Mod[a + b - 2, 33];
  product = Mod[(a - 1) (b - 1), 33];
  {
    Length[codes],
    Length[DeleteDuplicates[codes]],
    Total[a], Total[b],
    Total[a^2], Total[b^2],
    Min[a], Max[a], Min[b], Max[b],
    Total[delta], Total[sum], Total[product],
    Count[MapThread[SameQ, {a, b}], True],
    Count[MapThread[Less, {a, b}], True],
    Count[MapThread[Greater, {a, b}], True],
    Total[Abs[a - b]]
  }
];

TCCTPairwiseStatsS87D[observations_List] := Module[
  {codes, pairs, firstDistance, secondDistance, crossDistance},
  codes = Lookup[observations, "Code", {}];
  If[Length[codes] === 0, Return[ConstantArray[0, 10]]];
  If[
    !And @@ Map[
      Function[code,
        VectorQ[code, IntegerQ] &&
        Length[code] === 2 &&
        And @@ (Between[#, {1, 33}] & /@ code)
      ],
      codes
    ],
    Return[$Failed]
  ];
  pairs = Subsets[codes, {2}];
  If[Length[pairs] === 0, Return[ConstantArray[0, 10]]];
  firstDistance = Abs[pairs[[All, 1, 1]] - pairs[[All, 2, 1]]];
  secondDistance = Abs[pairs[[All, 1, 2]] - pairs[[All, 2, 2]]];
  crossDistance = Abs[
    (pairs[[All, 1, 1]] - pairs[[All, 1, 2]]) -
    (pairs[[All, 2, 1]] - pairs[[All, 2, 2]])
  ];
  {
    Length[pairs],
    Total[firstDistance], Total[secondDistance], Total[crossDistance],
    Min[firstDistance], Max[firstDistance],
    Min[secondDistance], Max[secondDistance],
    Count[firstDistance, 0], Count[secondDistance, 0]
  }
];

TCCTWorldVectorS87D[world_Association] := Module[
  {observations, queriedObservations, codeStats, pairwiseStats, vector},
  observations = Lookup[world, "Observations", $Failed];
  If[
    !ListQ[observations] ||
    !And @@ (AssociationQ /@ observations),
    Return[$Failed]
  ];
  queriedObservations = Select[
    observations,
    TrueQ[Lookup[#, "QueryBranchRelated", False]] &
  ];
  codeStats = TCCTCodeStatsS87D[queriedObservations];
  pairwiseStats = TCCTPairwiseStatsS87D[queriedObservations];
  If[SameQ[codeStats, $Failed] || SameQ[pairwiseStats, $Failed], Return[$Failed]];
  vector = Join[codeStats, pairwiseStats];
  If[Length[vector] === 27, vector, $Failed]
];

TCCTFeatureNamesS87D[] := {
  "ObservationCount", "DistinctCodeCount",
  "FirstCoordinateTotal", "SecondCoordinateTotal",
  "FirstCoordinateSquareTotal", "SecondCoordinateSquareTotal",
  "FirstCoordinateMinimum", "FirstCoordinateMaximum",
  "SecondCoordinateMinimum", "SecondCoordinateMaximum",
  "DeltaMod33Total", "SumMod33Total", "ProductMod33Total",
  "EqualCoordinateCount", "FirstLessCount", "FirstGreaterCount",
  "CoordinateDistanceTotal",
  "PairCount", "PairFirstDistanceTotal", "PairSecondDistanceTotal",
  "PairCrossDistanceTotal", "PairFirstDistanceMinimum",
  "PairFirstDistanceMaximum", "PairSecondDistanceMinimum",
  "PairSecondDistanceMaximum", "PairFirstEqualCount",
  "PairSecondEqualCount"
};

TCCTFrozenFeatureDefinitionBundleS87D[] := {
  DownValues[TCCTCodeStatsS87D],
  DownValues[TCCTPairwiseStatsS87D],
  DownValues[TCCTWorldVectorS87D],
  DownValues[TCCTFeatureNamesS87D],
  DownValues[TCCTLoadFrozenDecoderS87D],
  DownValues[TCCTPredictWorldS87D]
};

TCCTLoadFrozenDecoderS87D[path_String] := Module[
  {candidate, payload, payloadHash, classifierBytesHash, classifier},
  If[!FileExistsQ[path], Return[$Failed]];
  candidate = Quiet@Check[Import[path, "WXF"], $Failed];
  If[!AssociationQ[candidate], Return[$Failed]];
  If[
    !And @@ (KeyExistsQ[candidate, #] & /@ {
      "CandidateHash", "ClassifierBinary", "ClassifierBinaryHash",
      "FeatureFamily", "FeatureDimension"
    }),
    Return[$Failed]
  ];
  payload = KeyDrop[candidate, {"CandidateHash"}];
  payloadHash = Hash[Normal[payload], "SHA256", "HexString"];
  classifierBytesHash = Hash[
    candidate["ClassifierBinary"], "SHA256", "HexString"
  ];
  If[
    !SameQ[payloadHash, candidate["CandidateHash"]] ||
    !SameQ[classifierBytesHash, candidate["ClassifierBinaryHash"]] ||
    !SameQ[candidate["FeatureFamily"], "QueriedGlobalMoments"] ||
    !SameQ[candidate["FeatureDimension"], 27],
    Return[$Failed]
  ];
  classifier = Quiet@Check[
    BinaryDeserialize[candidate["ClassifierBinary"]],
    $Failed
  ];
  If[Head[classifier] =!= ClassifierFunction, Return[$Failed]];
  Append[candidate, "Classifier" -> classifier]
];

TCCTPredictWorldS87D[world_Association, decoder_Association] := Module[
  {vector, classifier},
  vector = TCCTWorldVectorS87D[world];
  classifier = Lookup[decoder, "Classifier", $Failed];
  If[
    SameQ[vector, $Failed] || Head[classifier] =!= ClassifierFunction,
    Return[$Failed]
  ];
  Quiet@Check[classifier[vector], $Failed]
];

