expectedCandidateHashForS83=
"1aeac2dc1aa0ec4f6e187e25ec054e3e8188c75ab1058b74f620500b826a587a";

If[
  !AssociationQ[frozenCandidate82C],
  Print["Export aborted: frozenCandidate82C is not present in this kernel."];
  Abort[]
];

candidateHashForS83=Hash[
  Normal[frozenCandidate82C],
  "SHA256",
  "HexString"
];

If[
  !SameQ[candidateHashForS83,expectedCandidateHashForS83],
  Print["Export aborted: the S82C frozen-candidate hash does not match."];
  Print[Dataset[{<|
    "ExpectedHash"->expectedCandidateHashForS83,
    "ActualHash"->candidateHashForS83
  |>}]];
  Abort[]
];

candidateSnapshotPathForS83=
  "E:/engine_wolf/TCCT_S82C_FrozenCandidate.wl";

Export[
  candidateSnapshotPathForS83,
  "frozenCandidate82C="<>
    ToString[InputForm[frozenCandidate82C]]<>";\n",
  "Text"
];

Dataset[{<|
  "Stage"->"S82C-to-S83",
  "CandidateExported"->FileExistsQ[candidateSnapshotPathForS83],
  "CandidateHash"->candidateHashForS83,
  "CandidateFile"->candidateSnapshotPathForS83,
  "OriginalFrozenModelChanged"->False,
  "CoreChanged"->False
|>}]
