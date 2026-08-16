(* TCCT S92B frozen paired-contrast decoder runtime.
   This adapter compares two already-computed S87D 27-dimensional vectors.
   It does not alter TCCT propagation, canonicalization, freezing, or deduplication. *)

ClearAll[
  TCCTPairContrastVectorS92B,
  TCCTLoadFrozenPairDecoderS92B,
  TCCTPredictOrderedPairVectorsS92B,
  TCCTPredictOrderedPairWorldsS92B
];

TCCTPairContrastVectorS92B[
  firstVector_List, secondVector_List, position_Integer, modulus_Integer
] := Module[{valid},
  valid = And[
    VectorQ[firstVector, IntegerQ], Length[firstVector] === 27,
    VectorQ[secondVector, IntegerQ], Length[secondVector] === 27,
    Between[position, {3, 17}], modulus > 1
  ];
  If[!TrueQ[valid], Return[$Failed]];
  {Mod[firstVector[[position]] - secondVector[[position]], modulus]}
];

TCCTLoadFrozenPairDecoderS92B[path_String] := Module[
  {candidate, payload, payloadHash, rules, policy},
  If[!FileExistsQ[path], Return[$Failed]];
  candidate = Quiet@Check[Import[path, "WXF"], $Failed];
  If[!AssociationQ[candidate], Return[$Failed]];
  If[!And @@ (KeyExistsQ[candidate, #] & /@ {
    "CandidateHash", "ContrastPosition", "Modulus", "PolicyRules",
    "BaseFeatureDimension", "BaseFrozenCandidateHash"
  }), Return[$Failed]];
  payload = KeyDrop[candidate, {"CandidateHash"}];
  payloadHash = Hash[Normal[payload], "SHA256", "HexString"];
  rules = candidate["PolicyRules"];
  If[
    !SameQ[payloadHash, candidate["CandidateHash"]] ||
    !SameQ[candidate["BaseFeatureDimension"], 27] ||
    !Between[candidate["ContrastPosition"], {3, 17}] ||
    !IntegerQ[candidate["Modulus"]] || candidate["Modulus"] <= 1 ||
    !ListQ[rules] || Length[rules] < 2 ||
    !And @@ Map[Function[row, And[
      AssociationQ[row], IntegerQ[Lookup[row, "Delta", Missing[]]],
      Between[Lookup[row, "Delta", -1], {0, candidate["Modulus"] - 1}],
      MemberQ[{"FirstContinue", "FirstStop"},
        Lookup[row, "Prediction", Missing[]]]
    ]], rules],
    Return[$Failed]
  ];
  policy = Association[
    (Lookup[#, "Delta"] -> Lookup[#, "Prediction"]) & /@ rules
  ];
  Append[candidate, "Policy" -> policy]
];

TCCTPredictOrderedPairVectorsS92B[
  firstVector_List, secondVector_List, decoder_Association
] := Module[{pairVector, policy},
  policy = Lookup[decoder, "Policy", $Failed];
  If[!AssociationQ[policy], Return[$Failed]];
  pairVector = TCCTPairContrastVectorS92B[
    firstVector, secondVector, decoder["ContrastPosition"], decoder["Modulus"]
  ];
  If[SameQ[pairVector, $Failed], Return[$Failed]];
  Lookup[policy, First[pairVector], "Unknown"]
];

TCCTPredictOrderedPairWorldsS92B[
  firstWorld_Association, secondWorld_Association, decoder_Association
] := Module[{firstVector, secondVector},
  If[!ValueQ[TCCTWorldVectorS87D], Return[$Failed]];
  firstVector = TCCTWorldVectorS87D[firstWorld];
  secondVector = TCCTWorldVectorS87D[secondWorld];
  If[SameQ[firstVector, $Failed] || SameQ[secondVector, $Failed],
    Return[$Failed]
  ];
  TCCTPredictOrderedPairVectorsS92B[firstVector, secondVector, decoder]
];
