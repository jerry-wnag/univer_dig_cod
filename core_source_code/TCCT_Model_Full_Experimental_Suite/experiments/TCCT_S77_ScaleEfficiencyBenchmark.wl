(* S77 CELL *)
ClearAll["Global`*77"];

expectedS76ProtocolHash77=
"f6b64054c51e1bc076a070c0068e2b5f2f1505a18ae71fd422bfc6a3ed1d7909";
expectedS76TopologySpecHash77=
"d3d0b7ba6135d648db64233ae3f9ba6a2ff91ddd3d591afb55b14a1c361802ea";
expectedS76TopologyImplementationHash77=
"4dd59ad9e8bad75c19c19d81d0ebca1a05c8de53f5330e367c258bb3e0b9e493";
expectedS76BlindResultHash77=
"7634f516b3344591f5e1fd1c146bc406b886a5f1984fe6953ad9de20a6cd9421";
expectedFrozenModelHash77=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";

expectedParams77={-1,0,-1,-1,-1,0,1,-1};
expectedK77=5;
expectedPolicy77={
{1,3},{2,2},{3,1},{3,2},{3,3},{4,3}
};

s76ResultLock77=And[
TrueQ[cert76["TestValidityPassed"]],
SameQ[cert76["Outcome"],"BLIND_PASS"],
SameQ[cert76["Cases"],32],
SameQ[cert76["Passed"],32],
SameQ[cert76["Accuracy"],1.],
SameQ[cert76["RootCause"],"BlindPerfect"],
SameQ[protocolHash76,expectedS76ProtocolHash77],
SameQ[topologySpecHash76,expectedS76TopologySpecHash77],
SameQ[
topologyImplementationHash76,
expectedS76TopologyImplementationHash77
],
SameQ[blindResultHash76,expectedS76BlindResultHash77],
SameQ[frozenModelHash75D,expectedFrozenModelHash77],
SameQ[frozen75D["Params"],expectedParams77],
SameQ[frozen75D["K"],expectedK77],
SameQ[frozen75D["Policy"],expectedPolicy77],
SameQ[cert76["CoreTCCTChanged"],False],
SameQ[cert76["EncoderParamsChanged"],False],
SameQ[cert76["KChanged"],False],
SameQ[cert76["PolicyChanged"],False],
SameQ[cert76["ModelChangedDuringTest"],False],
SameQ[cert76["S76UsedForSelection"],False],
SameQ[cert76["S76UsedForPolicyCompletion"],False]
];

benchmarkTopologies77={
"S59",
"ChainIn",
"SharedMerge",
"ParallelIn",
"ParallelOut",
"DiamondIn",
"SharedParallelIn",
"NestedBraidedIn"
};

benchmarkDepths77={31,63,127};
benchmarkAnswers77=Range[4];
benchmarkTargets77={"Continue","Stop"};
warmupDepth77=15;

environment77=<|
"WolframVersion"->$Version,
"SystemID"->$SystemID,
"ProcessorCount"->$ProcessorCount,
"KernelCount"->$KernelCount
|>;

protocol77=<|
"Stage"->"S77",
"Name"->"ScaleEfficiencyBenchmark",
"BenchmarkOnly"->True,
"ModelFrozen"->True,
"CoreTCCTChanged"->False,
"EncoderParamsChanged"->False,
"KChanged"->False,
"PolicyChanged"->False,
"NewCandidateSearch"->False,
"BenchmarkUsedForSelection"->False,
"BenchmarkUsedForPolicyCompletion"->False,
"Topologies"->benchmarkTopologies77,
"Depths"->benchmarkDepths77,
"Answers"->benchmarkAnswers77,
"Targets"->benchmarkTargets77,
"ExpectedBatches"->24,
"CasesPerBatch"->8,
"ExpectedCases"->192,
"WarmupDepth"->warmupDepth77,
"WarmupIncludedInBenchmark"->False,
"TimingMethod"->"AbsoluteTimingByEightCaseBatch",
"TimingStages"->{
"GraphGeneration","StateExtraction","Encoding","Decision"
},
"MemoryMeasurements"->{
"ByteCountOfCases","ByteCountOfStatePairs",
"ByteCountOfEncodedRows","KernelMemoryDelta"
},
"FrozenModelHash"->expectedFrozenModelHash77,
"S76ResultLockPassed"->s76ResultLock77
|>;

protocolHash77=Hash[
Normal[protocol77],
"SHA256",
"HexString"
];

preflightPass77=And[
TrueQ[s76ResultLock77],
SameQ[
Hash[Normal[frozen75D],"SHA256","HexString"],
expectedFrozenModelHash77
]
];

preflight77=Join[
protocol77,
<|
"Environment"->environment77,
"PreflightPassed"->preflightPass77,
"S76ProtocolHash"->protocolHash76,
"S76BlindResultHash"->blindResultHash76,
"S77ProtocolHash"->protocolHash77
|>
];

If[
!TrueQ[preflightPass77],
Print[Dataset[{preflight77}]];
Print["S77 aborted: S76 result lock or frozen model lock failed."];
Abort[]
];

Dataset[{preflight77}]

(* S77 CELL *)
ClearAll[
CaseByTopology77,
PredictEncodedRow77,
BenchmarkBatch77
];

CaseByTopology77[
topology_String,
depth_Integer,
answer_Integer,
target_String
]:=Switch[
topology,
"S59",
Case59[depth,answer,target],
"ChainIn",
Case63["ChainIn",depth,answer,target],
"SharedMerge",
Case63["SharedMerge",depth,answer,target],
"ParallelIn",
Case71[depth,answer,target],
"ParallelOut"|"DiamondIn"|"SharedParallelIn",
Case72[topology,depth,answer,target],
"NestedBraidedIn",
Case76[depth,answer,target],
_,
$Failed
];

PredictEncodedRow77[row_Association]:=If[
AnyTrue[
row["Codes"],
MemberQ[frozen75D["Policy"],#]&
],
"Continue",
"Stop"
];

BenchmarkBatch77[
topology_String,
depth_Integer
]:=Module[
{
memoryBefore,memoryAfter,generationSeconds,stateSeconds,
encodingSeconds,decisionSeconds,totalStageSeconds,
caseRecords,rows,encodedRows,predictions,caseResults,
cases,graphs,vertexCounts,edgeCounts,caseBytes,
statePairBytes,encodedBytes,passed
},
memoryBefore=MemoryInUse[];

{generationSeconds,caseRecords}=AbsoluteTiming[
Flatten[
Table[
<|
"Grammar"->topology,
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"Case"->CaseByTopology77[
topology,depth,answer,target
]
|>,
{answer,benchmarkAnswers77},
{target,benchmarkTargets77}
],
1
]
];

cases=Lookup[caseRecords,"Case"];

{stateSeconds,rows}=AbsoluteTiming[
Map[
Function[record,
<|
"Grammar"->record["Grammar"],
"Depth"->record["Depth"],
"Answer"->record["Answer"],
"Target"->record["Target"],
"StatePairs"->DecisionStatePairs75[record["Case"]]
|>
],
caseRecords
]
];

{encodingSeconds,encodedRows}=AbsoluteTiming[
EncodeRows75[
rows,
frozen75D["Params"],
frozen75D["K"]
]
];

{decisionSeconds,predictions}=AbsoluteTiming[
PredictEncodedRow77/@encodedRows
];

caseResults=MapThread[
Function[{row,encoded,prediction},
Join[
KeyTake[row,{"Grammar","Depth","Answer","Target"}],
<|
"Codes"->encoded["Codes"],
"Prediction"->prediction,
"Correct"->SameQ[prediction,row["Target"]]
|>
]
],
{rows,encodedRows,predictions}
];

passed=Count[
caseResults,
row_/;TrueQ[row["Correct"]]
];

graphs=Graph[#[[1,1]]]&/@cases;
vertexCounts=VertexCount/@graphs;
edgeCounts=EdgeCount/@graphs;
caseBytes=Total[ByteCount/@cases];
statePairBytes=ByteCount[Lookup[rows,"StatePairs"]];
encodedBytes=ByteCount[encodedRows];
memoryAfter=MemoryInUse[];
totalStageSeconds=Total[{
generationSeconds,stateSeconds,
encodingSeconds,decisionSeconds
}];

<|
"Summary"-><|
"Topology"->topology,
"Depth"->depth,
"Cases"->Length[caseResults],
"Passed"->passed,
"Accuracy"->N[passed/Length[caseResults]],
"GenerationSeconds"->generationSeconds,
"StateExtractionSeconds"->stateSeconds,
"EncodingSeconds"->encodingSeconds,
"DecisionSeconds"->decisionSeconds,
"TotalStageSeconds"->totalStageSeconds,
"SecondsPerCase"->N[
totalStageSeconds/Length[caseResults]
],
"CasesPerSecond"->If[
totalStageSeconds>0,
N[Length[caseResults]/totalStageSeconds],
Infinity
],
"MeanVertices"->N[Mean[vertexCounts]],
"MaxVertices"->Max[vertexCounts],
"MeanEdges"->N[Mean[edgeCounts]],
"MaxEdges"->Max[edgeCounts],
"CaseBytes"->caseBytes,
"StatePairBytes"->statePairBytes,
"EncodedBytes"->encodedBytes,
"KernelMemoryDeltaBytes"->(memoryAfter-memoryBefore),
"EmptyStatePairs"->Count[
Lookup[rows,"StatePairs"],
{}
]
|>,
"Cases"->caseResults
|>
];

warmupResults77=BenchmarkBatch77[
#,
warmupDepth77
]&/@benchmarkTopologies77;

warmupSummaries77=Lookup[warmupResults77,"Summary"];

warmupPass77=And[
SameQ[Length[warmupSummaries77],8],
And@@Map[
And[
SameQ[# ["Cases"],8],
SameQ[# ["Passed"],8],
SameQ[# ["EmptyStatePairs"],0]
]&,
warmupSummaries77
]
];

If[
!TrueQ[warmupPass77],
Print[Dataset[warmupSummaries77]];
Print["S77 aborted before benchmark: warm-up integrity failed."];
Abort[]
];

Dataset[warmupSummaries77]

(* S77 CELL *)
benchmark31Results77=BenchmarkBatch77[
#,
31
]&/@benchmarkTopologies77;

Dataset[Lookup[benchmark31Results77,"Summary"]]

(* S77 CELL *)
benchmark63Results77=BenchmarkBatch77[
#,
63
]&/@benchmarkTopologies77;

Dataset[Lookup[benchmark63Results77,"Summary"]]

(* S77 CELL *)
benchmark127Results77=BenchmarkBatch77[
#,
127
]&/@benchmarkTopologies77;

Dataset[Lookup[benchmark127Results77,"Summary"]]

(* S77 CELL *)
ClearAll[AggregateBatchScores77];

benchmarkResults77=Join[
benchmark31Results77,
benchmark63Results77,
benchmark127Results77
];

benchmarkBatchSummaries77=Lookup[
benchmarkResults77,
"Summary"
];

benchmarkCaseResults77=Flatten[
Lookup[benchmarkResults77,"Cases"],
1
];

benchmarkFailureRows77=Select[
benchmarkCaseResults77,
!TrueQ[# ["Correct"]]&
];

AggregateBatchScores77[
rows_List,
key_String
]:=Map[
Function[value,
Module[{selected,cases,passed,totalSeconds},
selected=Select[rows,SameQ[# [key],value]&];
cases=Total[Lookup[selected,"Cases"]];
passed=Total[Lookup[selected,"Passed"]];
totalSeconds=Total[Lookup[selected,"TotalStageSeconds"]];
<|
key->value,
"Batches"->Length[selected],
"Cases"->cases,
"Passed"->passed,
"Accuracy"->N[passed/cases],
"TotalStageSeconds"->totalSeconds,
"SecondsPerCase"->N[totalSeconds/cases],
"CasesPerSecond"->If[
totalSeconds>0,
N[cases/totalSeconds],
Infinity
],
"MaxVertices"->Max[Lookup[selected,"MaxVertices"]],
"MaxEdges"->Max[Lookup[selected,"MaxEdges"]],
"MaxCaseBytes"->Max[Lookup[selected,"CaseBytes"]],
"MaxStatePairBytes"->Max[
Lookup[selected,"StatePairBytes"]
],
"MaxEncodedBytes"->Max[Lookup[selected,"EncodedBytes"]]
|>
]
],
DeleteDuplicates[Lookup[rows,key]]
];

depthSummary77=AggregateBatchScores77[
benchmarkBatchSummaries77,
"Depth"
];

topologySummary77=AggregateBatchScores77[
benchmarkBatchSummaries77,
"Topology"
];

modelHashAfterBenchmark77=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];

totalBenchmarkSeconds77=Total[
Lookup[benchmarkBatchSummaries77,"TotalStageSeconds"]
];

benchmarkSummary77=<|
"Stage"->"S77",
"Name"->"ScaleEfficiencyBenchmark",
"ProtocolHash"->protocolHash77,
"Topologies"->Length[benchmarkTopologies77],
"Depths"->benchmarkDepths77,
"Batches"->Length[benchmarkBatchSummaries77],
"Cases"->Length[benchmarkCaseResults77],
"Passed"->Count[
benchmarkCaseResults77,
row_/;TrueQ[row["Correct"]]
],
"Accuracy"->N[
Count[
benchmarkCaseResults77,
row_/;TrueQ[row["Correct"]]
]/Length[benchmarkCaseResults77]
],
"FailedCases"->Length[benchmarkFailureRows77],
"TotalMeasuredStageSeconds"->totalBenchmarkSeconds77,
"OverallSecondsPerCase"->N[
totalBenchmarkSeconds77/Length[benchmarkCaseResults77]
],
"OverallCasesPerSecond"->If[
totalBenchmarkSeconds77>0,
N[
Length[benchmarkCaseResults77]/totalBenchmarkSeconds77
],
Infinity
],
"FrozenModelHashBefore"->expectedFrozenModelHash77,
"FrozenModelHashAfter"->modelHashAfterBenchmark77,
"ModelChangedDuringBenchmark"->Not@SameQ[
modelHashAfterBenchmark77,
expectedFrozenModelHash77
]
|>;

benchmarkValidityPassed77=And[
TrueQ[preflightPass77],
TrueQ[warmupPass77],
SameQ[Length[benchmarkBatchSummaries77],24],
SameQ[Length[benchmarkCaseResults77],192],
And@@Map[SameQ[# ["Cases"],8]&,
benchmarkBatchSummaries77],
And@@Map[SameQ[# ["EmptyStatePairs"],0]&,
benchmarkBatchSummaries77],
SameQ[
modelHashAfterBenchmark77,
expectedFrozenModelHash77
]
];

benchmarkResultPayload77=<|
"Stage"->"S77",
"ProtocolHash"->protocolHash77,
"FrozenModelHash"->expectedFrozenModelHash77,
"BenchmarkSummary"->benchmarkSummary77,
"DepthSummary"->depthSummary77,
"TopologySummary"->topologySummary77,
"FailureRows"->benchmarkFailureRows77,
"BenchmarkValidityPassed"->benchmarkValidityPassed77
|>;

benchmarkResultHash77=Hash[
Normal[benchmarkResultPayload77],
"SHA256",
"HexString"
];

cert77=Join[
benchmarkResultPayload77,
<|
"Name"->"ScaleEfficiencyBenchmark",
"Outcome"->If[
benchmarkValidityPassed77,
If[
SameQ[benchmarkSummary77["Passed"],192],
"VALID_SCALE_PASS",
"VALID_SCALE_LIMIT_FOUND"
],
"INVALID_BENCHMARK"
],
"CoreTCCTChanged"->False,
"EncoderParamsChanged"->False,
"KChanged"->False,
"PolicyChanged"->False,
"NewCandidateSearch"->False,
"BenchmarkUsedForSelection"->False,
"BenchmarkUsedForPolicyCompletion"->False,
"ModelChangedDuringBenchmark"->benchmarkSummary77[
"ModelChangedDuringBenchmark"
],
"TimingIncludesWarmup"->False,
"MemoryNumbersAreObjectSizeProxies"->True,
"BenchmarkResultHash"->benchmarkResultHash77,
"Environment"->environment77,
"BatchMetrics"->benchmarkBatchSummaries77
|>
];

Dataset[{benchmarkSummary77}]

Dataset[depthSummary77]

Dataset[topologySummary77]

Dataset[benchmarkFailureRows77]

Dataset[{cert77}]
