(* S76 CELL *)
ClearAll["Global`*76"];

expectedS75DProtocolHash76=
"6dc63ed23ac9662155d1b09a4a2fd7d26bfd79fe87576e23caecbf76900e409f";
expectedFrozenModelHash76=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedS75DCheckpointHash76=
"1eff8e0db4c1af364e443ec194068d04b830d3ee02f941aaaa05b80bb2001222";

expectedParams76={-1,0,-1,-1,-1,0,1,-1};
expectedK76=5;
expectedPolicy76={
{1,3},{2,2},{3,1},{3,2},{3,3},{4,3}
};

s75DResultLock76=And[
TrueQ[preflightPass75D],
TrueQ[resultLock75D],
TrueQ[cert75D["ResultLockPassed"]],
SameQ[checkpoint75D["Status"],"FROZEN"],
SameQ[protocolHash75D,expectedS75DProtocolHash76],
SameQ[frozenModelHash75D,expectedFrozenModelHash76],
SameQ[checkpointHash75D,expectedS75DCheckpointHash76],
SameQ[frozen75D["Params"],expectedParams76],
SameQ[frozen75D["K"],expectedK76],
SameQ[frozen75D["Policy"],expectedPolicy76],
SameQ[checkpoint75D["CompletedPolicyAllSeenScore"],224],
SameQ[checkpoint75D["AllSeenCases"],224],
SameQ[checkpoint75D["GlobalSharedTokens"],0],
SameQ[checkpoint75D["MissedContinueCases"],0],
SameQ[checkpoint75D["TriggeredStopCases"],0],
TrueQ[checkpoint75D["AllSevenGrammarsPerfect"]],
TrueQ[checkpoint75D["FrozenBeforeS76"]],
SameQ[checkpoint75D["S76BlindTestRun"],False]
];

ClearAll[NestedBraidedIn76,Case76];

NestedBraidedIn76[c_List]:=Module[
{
x=c[[1]],a=c[[2]],e,f,mx,next,new,m,parents,removed,
lane1,lane2,bridge,private1,private2,added,i,j
},
e=x[[1]];
f=x[[6]];
mx=Max@Flatten[List@@@e];
next=mx+1;
new=e;
Do[
m=f[[i]];
parents=Cases[
new,
DirectedEdge[u_,v_]/;v===m:>u
];
removed=(DirectedEdge[#,m]&)/@parents;
lane1=next;
lane2=next+1;
bridge=next+2;
next=next+3;
added={};
Do[
private1=next;
private2=next+1;
next=next+2;
added=Join[
added,
{
DirectedEdge[parents[[j]],private1],
DirectedEdge[parents[[j]],private2],
DirectedEdge[private1,lane1],
DirectedEdge[private2,lane2]
}
],
{j,Length[parents]}
];
added=Join[
added,
{
DirectedEdge[lane1,bridge],
DirectedEdge[lane2,bridge],
DirectedEdge[bridge,m]
}
];
new=Join[
Complement[new,removed],
added
],
{i,Length[f]}
];
{{
Union[new],
x[[2]],x[[3]],x[[4]],x[[5]],x[[6]]
},a}
];

Case76[
d_Integer,
a_Integer,
t_String
]:=NestedBraidedIn76[
Case59[d,a,t]
];

topologySpec76=<|
"Topology"->"NestedBraidedIn",
"TransformationScope"->"EveryIncomingEdgeOfEachDecisionNode",
"ParentMotif"->"PrivateTwoWaySplit",
"CrossParentMotif"->"TwoSharedLanes",
"FinalMotif"->"LaneMergeThroughSingleBridge",
"ParentToDecisionPathLength"->4,
"NewNodesPerDecision"->
"ThreeSharedPlusTwoPerOriginalParent",
"ReachabilityPreserved"->True,
"OriginalDecisionNodesPreserved"->True,
"TopologyUsedInS59ThroughS75D"->False
|>;

topologySpecHash76=Hash[
Normal[topologySpec76],
"SHA256",
"HexString"
];

topologyImplementationHash76=Hash[
{
DownValues[NestedBraidedIn76],
DownValues[Case76]
},
"SHA256",
"HexString"
];

blindDepths76={2,5,9,15};
blindAnswers76=Range[4];
blindTargets76={"Continue","Stop"};

protocol76=<|
"Stage"->"S76",
"Name"->"NestedBraidedInBlindTest",
"TestType"->"OneShotFrozenModelBlindTopologyTest",
"Topology"->"NestedBraidedIn",
"TopologySpecHash"->topologySpecHash76,
"TopologyImplementationHash"->topologyImplementationHash76,
"Depths"->blindDepths76,
"Answers"->blindAnswers76,
"Targets"->blindTargets76,
"ExpectedCases"->32,
"FrozenModelHash"->expectedFrozenModelHash76,
"CoreTCCTChanged"->False,
"EncoderParamsChanged"->False,
"KChanged"->False,
"PolicyChanged"->False,
"NewCandidateSearch"->False,
"S76UsedForSelection"->False,
"S76UsedForPolicyCompletion"->False,
"BlindScoreUnknownAtProtocolFreeze"->True,
"NoTuningAfterReveal"->True,
"S75DResultLockPassed"->s75DResultLock76
|>;

protocolHash76=Hash[
Normal[protocol76],
"SHA256",
"HexString"
];

preflightPass76=And[
TrueQ[s75DResultLock76],
SameQ[
Hash[Normal[frozen75D],"SHA256","HexString"],
expectedFrozenModelHash76
]
];

preflight76=Join[
protocol76,
<|
"PreflightPassed"->preflightPass76,
"S75DProtocolHash"->protocolHash75D,
"S75DCheckpointHash"->checkpointHash75D,
"S76ProtocolHash"->protocolHash76
|>
];

If[
!TrueQ[preflightPass76],
Print[Dataset[{preflight76}]];
Print["S76 aborted before case generation: S75D lock failed."];
Abort[]
];

Dataset[{preflight76}]

(* S76 CELL *)
baseSample76=Case59[2,1,"Continue"];
changedSample76=Case76[2,1,"Continue"];

baseEdges76=baseSample76[[1,1]];
changedEdges76=changedSample76[[1,1]];
decisionNodes76=baseSample76[[1,6]];
baseGraph76=Graph[baseEdges76];
changedGraph76=Graph[changedEdges76];

baseParentsByDecision76=AssociationMap[
Function[m,
Cases[
baseEdges76,
DirectedEdge[u_,v_]/;v===m:>u
]
],
decisionNodes76
];

originalParentCount76=Total[
Length/@Values[baseParentsByDecision76]
];

parentDecisionDistances76=Flatten@KeyValueMap[
Function[{m,parents},
Map[GraphDistance[changedGraph76,#,m]&,parents]
],
baseParentsByDecision76
];

bridgeNodes76=Cases[
changedEdges76,
DirectedEdge[u_,v_]/;MemberQ[decisionNodes76,v]:>u
];

laneNodes76=Union@Cases[
changedEdges76,
DirectedEdge[u_,v_]/;MemberQ[bridgeNodes76,v]:>u
];

seenSampleCases76=<|
"S59"->Case59[2,1,"Continue"],
"ChainIn"->Case63["ChainIn",2,1,"Continue"],
"SharedMerge"->Case63["SharedMerge",2,1,"Continue"],
"ParallelIn"->Case71[2,1,"Continue"],
"ParallelOut"->Case72["ParallelOut",2,1,"Continue"],
"DiamondIn"->Case72["DiamondIn",2,1,"Continue"],
"SharedParallelIn"->Case72[
"SharedParallelIn",2,1,"Continue"
]
|>;

distinctFromSeen76=Association@KeyValueMap[
Function[{name,case},
name->Not@TrueQ[
IsomorphicGraphQ[
changedGraph76,
Graph[case[[1,1]]]
]
]
],
seenSampleCases76
];

expectedAddedVertices76=
3 Length[decisionNodes76]+2 originalParentCount76;

expectedEdgeDelta76=
3 originalParentCount76+3 Length[decisionNodes76];

topologyAudit76=<|
"BaseVertices"->VertexCount[baseGraph76],
"ChangedVertices"->VertexCount[changedGraph76],
"AddedVertices"->(
VertexCount[changedGraph76]-VertexCount[baseGraph76]
),
"ExpectedAddedVertices"->expectedAddedVertices76,
"BaseEdges"->EdgeCount[baseGraph76],
"ChangedEdges"->EdgeCount[changedGraph76],
"EdgeDelta"->(
EdgeCount[changedGraph76]-EdgeCount[baseGraph76]
),
"ExpectedEdgeDelta"->expectedEdgeDelta76,
"OriginalParentDecisionEdgesRemoved"->SameQ[
Intersection[
changedEdges76,
Flatten@KeyValueMap[
Function[{m,parents},DirectedEdge[#,m]&/@parents],
baseParentsByDecision76
]
],
{}
],
"ParentDecisionDistances"->Counts[
parentDecisionDistances76
],
"AllParentDecisionDistancesFour"->And@@(
SameQ[#,4]&/@parentDecisionDistances76
),
"DecisionInDegrees"->(
VertexInDegree[changedGraph76,#]&/@decisionNodes76
),
"BridgeInDegrees"->(
VertexInDegree[changedGraph76,#]&/@bridgeNodes76
),
"LaneInDegrees"->(
VertexInDegree[changedGraph76,#]&/@laneNodes76
),
"MetadataAndAnswerPreserved"->And[
SameQ[
changedSample76[[1,2;;6]],
baseSample76[[1,2;;6]]
],
SameQ[changedSample76[[2]],baseSample76[[2]]]
],
"DistinctFromSeenTopologies"->distinctFromSeen76
|>;

structuralAuditPass76=And[
SameQ[
topologyAudit76["AddedVertices"],
topologyAudit76["ExpectedAddedVertices"]
],
SameQ[
topologyAudit76["EdgeDelta"],
topologyAudit76["ExpectedEdgeDelta"]
],
TrueQ[
topologyAudit76[
"OriginalParentDecisionEdgesRemoved"
]
],
TrueQ[
topologyAudit76[
"AllParentDecisionDistancesFour"
]
],
And@@(SameQ[#,1]&/@topologyAudit76[
"DecisionInDegrees"
]),
And@@(SameQ[#,2]&/@topologyAudit76[
"BridgeInDegrees"
]),
And@@(#>=2&/@topologyAudit76["LaneInDegrees"]),
TrueQ[topologyAudit76["MetadataAndAnswerPreserved"]],
And@@Values[distinctFromSeen76]
];

blindRows76=Flatten[
Table[
<|
"Grammar"->"NestedBraidedIn",
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"StatePairs"->DecisionStatePairs75[
Case76[depth,answer,target]
]
|>,
{depth,blindDepths76},
{answer,blindAnswers76},
{target,blindTargets76}
],
2
];

blindDataCert76=<|
"Cases"->Length[blindRows76],
"DepthCounts"->Counts[Lookup[blindRows76,"Depth"]],
"AnswerCounts"->Counts[Lookup[blindRows76,"Answer"]],
"TargetCounts"->Counts[Lookup[blindRows76,"Target"]],
"EmptyStatePairs"->Count[
Lookup[blindRows76,"StatePairs"],
{}
],
"StructuralAuditPassed"->structuralAuditPass76,
"TopologySpecHash"->topologySpecHash76,
"TopologyImplementationHash"->topologyImplementationHash76,
"ProtocolHash"->protocolHash76
|>;

blindDataLock76=And[
TrueQ[preflightPass76],
TrueQ[structuralAuditPass76],
SameQ[blindDataCert76["Cases"],32],
SameQ[
blindDataCert76["DepthCounts"],
AssociationThread[blindDepths76,ConstantArray[8,4]]
],
SameQ[
blindDataCert76["AnswerCounts"],
AssociationThread[blindAnswers76,ConstantArray[8,4]]
],
SameQ[
blindDataCert76["TargetCounts"],
<|"Continue"->16,"Stop"->16|>
],
SameQ[blindDataCert76["EmptyStatePairs"],0]
];

If[
!TrueQ[blindDataLock76],
Print[Dataset[{topologyAudit76}]];
Print[Dataset[{blindDataCert76}]];
Print["S76 aborted before scoring: topology or data lock failed."];
Abort[]
];

Dataset[{topologyAudit76}]

Dataset[{blindDataCert76}]

(* S76 CELL *)
ClearAll[SliceScores76];

modelHashBeforeBlind76=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];

blindEncoded76=EncodeRows75[
blindRows76,
frozen75D["Params"],
frozen75D["K"]
];

blindCaseResults76=MapThread[
Function[{row,encoded},
Module[{prediction},
prediction=If[
AnyTrue[
encoded["Codes"],
MemberQ[frozen75D["Policy"],#]&
],
"Continue",
"Stop"
];
Join[
KeyTake[row,{"Grammar","Depth","Answer","Target"}],
<|
"Codes"->encoded["Codes"],
"Prediction"->prediction,
"Correct"->SameQ[prediction,row["Target"]]
|>
]
]
],
{blindRows76,blindEncoded76}
];

blindScore76=Count[
blindCaseResults76,
row_/;TrueQ[row["Correct"]]
];

blindAccuracy76=N[
blindScore76/Length[blindCaseResults76]
];

blindFailureRows76=Select[
blindCaseResults76,
!TrueQ[# ["Correct"]]&
];

SliceScores76[key_String]:=Map[
Function[value,
Module[{rows},
rows=Select[
blindCaseResults76,
SameQ[# [key],value]&
];
<|
key->value,
"Cases"->Length[rows],
"Passed"->Count[rows,x_/;TrueQ[x["Correct"]]],
"Accuracy"->N[
Count[rows,x_/;TrueQ[x["Correct"]]]/Length[rows]
]
|>
]
],
DeleteDuplicates[Lookup[blindCaseResults76,key]]
];

depthScores76=SliceScores76["Depth"];
answerScores76=SliceScores76["Answer"];
targetScores76=SliceScores76["Target"];

modelHashAfterBlind76=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];

blindExecutionValid76=And[
TrueQ[blindDataLock76],
SameQ[
modelHashBeforeBlind76,
expectedFrozenModelHash76
],
SameQ[
modelHashAfterBlind76,
modelHashBeforeBlind76
],
SameQ[Length[blindCaseResults76],32]
];

blindSummary76=<|
"Stage"->"S76",
"Topology"->"NestedBraidedIn",
"ProtocolHash"->protocolHash76,
"FrozenModelHash"->modelHashBeforeBlind76,
"Cases"->Length[blindCaseResults76],
"Passed"->blindScore76,
"Accuracy"->blindAccuracy76,
"FailedCases"->Length[blindFailureRows76],
"BlindPerfect"->SameQ[blindScore76,32],
"ExecutionValid"->blindExecutionValid76,
"ModelChangedDuringTest"->Not@SameQ[
modelHashBeforeBlind76,
modelHashAfterBlind76
]
|>;

Dataset[{blindSummary76}]

Dataset[depthScores76]

Dataset[answerScores76]

Dataset[targetScores76]

Dataset[blindFailureRows76]

(* S76 CELL *)
seenTokenSets76=TokenSets75B[allSeenEncoded75D];
blindTokenSets76=TokenSets75B[blindEncoded76];
combinedEncoded76=Join[
allSeenEncoded75D,
blindEncoded76
];

combinedSemanticFeasibility76=SemanticFeasibility75B[
combinedEncoded76
];

rawCombinedSemanticFeasibility76=SemanticFeasibility75B[
RawEncodedRows75B[
Join[allSeenRows75B,blindRows76]
]
];

blindPolicyErrors76=PolicyErrorCounts75B[
blindEncoded76,
frozen75D["Policy"]
];

newBlindTokens76=Complement[
blindTokenSets76["All"],
seenTokenSets76["All"]
];

tokenMeaningAudit76=Map[
Function[token,
<|
"Token"->token,
"SeenMeaning"->TokenMeaning75B[token,seenTokenSets76],
"S76Meaning"->TokenMeaning75B[token,blindTokenSets76],
"CombinedMeaning"->TokenMeaning75B[
token,
TokenSets75B[combinedEncoded76]
],
"SelectedByFrozenPolicy"->MemberQ[
frozen75D["Policy"],
token
],
"NewAtS76"->MemberQ[newBlindTokens76,token]
|>
],
Union[
seenTokenSets76["All"],
blindTokenSets76["All"]
]
];

blindRootCause76=Which[
SameQ[blindScore76,32],
"BlindPerfect",
Not@TrueQ[
rawCombinedSemanticFeasibility76[
"PerfectPurePolicyFeasible"
]
],
"RawCrossTopologyObservationConflict",
combinedSemanticFeasibility76["SharedTokens"]>0,
"LatentCrossTopologySemanticConflict",
And[
blindPolicyErrors76["MissedContinueCases"]>0,
SameQ[blindPolicyErrors76["TriggeredStopCases"],0]
],
"FrozenPolicyCoverageGap",
blindPolicyErrors76["TriggeredStopCases"]>0,
"FrozenPolicyStopCollisionOrOvergeneralization",
True,
"MixedResidualFailure"
];

blindDiagnostic76=<|
"DiagnosticOnlyAfterBlindReveal"->True,
"FrozenModelChanged"->False,
"RawCombinedPerfectPolicyFeasible"->
rawCombinedSemanticFeasibility76[
"PerfectPurePolicyFeasible"
],
"LatentCombinedPerfectPolicyFeasible"->
combinedSemanticFeasibility76[
"PerfectPurePolicyFeasible"
],
"CombinedSharedTokens"->
combinedSemanticFeasibility76["SharedTokens"],
"S76DistinctTokens"->Length[blindTokenSets76["All"]],
"S76NewTokens"->newBlindTokens76,
"S76NewTokenCount"->Length[newBlindTokens76],
"MissedContinueCases"->
blindPolicyErrors76["MissedContinueCases"],
"TriggeredStopCases"->
blindPolicyErrors76["TriggeredStopCases"],
"RootCause"->blindRootCause76
|>;

Dataset[{blindDiagnostic76}]

Dataset[Select[tokenMeaningAudit76,TrueQ[# ["NewAtS76"]]&]]

(* S76 CELL *)
testValidityPassed76=And[
TrueQ[preflightPass76],
TrueQ[blindDataLock76],
TrueQ[blindExecutionValid76],
SameQ[modelHashAfterBlind76,expectedFrozenModelHash76],
SameQ[protocol76["PolicyChanged"],False],
SameQ[protocol76["NewCandidateSearch"],False],
SameQ[protocol76["S76UsedForSelection"],False],
SameQ[protocol76["S76UsedForPolicyCompletion"],False]
];

blindResultPayload76=<|
"Stage"->"S76",
"Topology"->"NestedBraidedIn",
"ProtocolHash"->protocolHash76,
"TopologySpecHash"->topologySpecHash76,
"TopologyImplementationHash"->topologyImplementationHash76,
"FrozenModelHash"->modelHashBeforeBlind76,
"Cases"->32,
"Passed"->blindScore76,
"Accuracy"->blindAccuracy76,
"FailedCases"->Length[blindFailureRows76],
"DepthScores"->depthScores76,
"AnswerScores"->answerScores76,
"TargetScores"->targetScores76,
"RootCause"->blindRootCause76,
"TestValidityPassed"->testValidityPassed76
|>;

blindResultHash76=Hash[
Normal[blindResultPayload76],
"SHA256",
"HexString"
];

cert76=Join[
blindResultPayload76,
<|
"Name"->"NestedBraidedInBlindTest",
"Outcome"->If[
SameQ[blindScore76,32],
"BLIND_PASS",
"BLIND_FAIL_ACCEPTED"
],
"CoreTCCTChanged"->False,
"EncoderParamsChanged"->False,
"KChanged"->False,
"PolicyChanged"->False,
"ModelChangedDuringTest"->False,
"S76UsedForSelection"->False,
"S76UsedForPolicyCompletion"->False,
"ResultAcceptedWithoutRetuning"->True,
"DiagnosticOnlyAfterReveal"->True,
"BlindResultHash"->blindResultHash76,
"TopologyAudit"->topologyAudit76,
"DataCertificate"->blindDataCert76,
"Diagnostic"->blindDiagnostic76
|>
];

Dataset[{cert76}]
