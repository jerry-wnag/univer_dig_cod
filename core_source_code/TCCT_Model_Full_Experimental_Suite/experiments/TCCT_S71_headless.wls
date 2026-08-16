SetDirectory[DirectoryName[$InputFileName]];

Print["TCCT S71 headless run started..."];
loadTiming71 = AbsoluteTiming[
  Get[FileNameJoin[{Directory[], "TCCT_S71_recovered_full.wl"}]]
][[1]];

resultDirectory = FileNameJoin[{Directory[], "results"}];
If[!DirectoryQ[resultDirectory],
  CreateDirectory[resultDirectory, CreateIntermediateDirectories -> True]
];

headlessReport71 = <|
  "Stage" -> "S71",
  "WolframVersion" -> $Version,
  "ElapsedSeconds" -> loadTiming71,
  "FrozenK" -> 5,
  "FrozenParams" -> {0, -1, 1, -1, -1, 0},
  "FrozenPolicy" -> {1, 4},
  "ParallelInPassed" -> score71,
  "ParallelInCases" -> 32,
  "CandidateScores" -> candidateScores71
|>;

Export[
  FileNameJoin[{resultDirectory, "TCCT_S71_result.json"}],
  Normal[headlessReport71],
  "RawJSON"
];

Print[Dataset[{headlessReport71}]];
Print["Saved results to: " <> resultDirectory];
