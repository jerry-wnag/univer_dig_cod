import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S83_SOURCE = ROOT / "TCCT_S83_BlindQuerySwitchTopologyComposition.wl"
WL_OUTPUT = ROOT / "TCCT_S84_BlindDoubleInterventionQueryGrid.wl"
NB_OUTPUT = ROOT / "TCCT_S84_BlindDoubleInterventionQueryGrid_AutoRun.ipynb"
MARKER = "(* S84 CELL *)"


s83 = S83_SOURCE.read_text(encoding="utf-8")
s83_parts = s83.split("(* S83 CELL *)")
if len(s83_parts) != 5:
    raise RuntimeError("S83 source no longer has exactly four code cells")

# Reuse only the architecture/core constructors that were already locked before
# S83. No S83 cases, labels, predictions, or S83B development rows enter S84.
base_definitions = s83_parts[1].split(
    "expectedMinimalKernelDefinitionTextHash83=", 1
)[0].rstrip()

cell1 = base_definitions + r'''

expectedMinimalKernelDefinitionTextHash84=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash84=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedStableFrozenArchitectureHash84=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedInterventionHash84=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedCandidateHash84=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";

candidateSnapshotPath84=
"E:/engine_wolf/TCCT_S83B_FrozenCandidate.wl";

If[
!FileExistsQ[candidateSnapshotPath84],
Print["S84 aborted: frozen S83B candidate file is missing."];
Abort[]
];

Get[candidateSnapshotPath84];

ClearAll[CoreDefinitionBundle84];
CoreDefinitionBundle84[]:={
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
};

minimalKernelDefinitionTextHash84=Hash[
ToString[InputForm[CoreDefinitionBundle84[]]],
"SHA256","HexString"
];

stableFrozenArchitectureHash84=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash84,
canonicalizerImplementationHash79B
},
"SHA256","HexString"
];

candidateHashLoaded84=If[
AssociationQ[frozenCandidate83B],
Hash[Normal[frozenCandidate83B],"SHA256","HexString"],
Missing["CandidateNotLoaded"]
];

preflightPassed84=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash84,
expectedMinimalKernelDefinitionTextHash84
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash84
],
SameQ[
stableFrozenArchitectureHash84,
expectedStableFrozenArchitectureHash84
],
SameQ[interventionImplementationHash82,expectedInterventionHash84],
AssociationQ[frozenCandidate83B],
SameQ[candidateHashLoaded84,expectedCandidateHash84],
SameQ[frozenCandidate83B["BaseFrozenModelHash"],expectedFrozenModelHash79A],
SameQ[frozenCandidate83B["EncoderParams"],frozen75D["Params"]],
SameQ[frozenCandidate83B["Representation"],"KExactRole"],
SameQ[frozenCandidate83B["K"],19],
SameQ[Length[frozenCandidate83B["Policy"]],26],
SameQ[frozenCandidate83B["DevelopmentScore"],264],
TrueQ[frozenCandidate83B["ExactNodeRoleUsed"]],
TrueQ[frozenCandidate83B["FrozenBeforeS84"]]
];

preflight84=<|
"Stage"->"S84",
"Name"->"BlindDoubleInterventionQueryGrid",
"CandidateFileLoaded"->FileExistsQ[candidateSnapshotPath84],
"CandidateHash"->candidateHashLoaded84,
"ExpectedCandidateHash"->expectedCandidateHash84,
"CandidateK"->If[AssociationQ[frozenCandidate83B],frozenCandidate83B["K"],Missing[]],
"CandidatePolicyLength"->If[
AssociationQ[frozenCandidate83B],Length[frozenCandidate83B["Policy"]],Missing[]
],
"OriginalFrozenModelChanged"->False,
"FrozenCandidateChanged"->False,
"CoreChanged"->False,
"PreflightPassed"->preflightPassed84
|>;

If[
!TrueQ[preflightPassed84],
Print[Dataset[{preflight84}]];
Print["S84 aborted: frozen architecture or S83B candidate mismatch."];
Abort[]
];

Dataset[{preflight84}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
NodeRole84,
EncodePair84,
PredictTokens84,
SetAnswer84,
TopologyTransform84,
ExpectedContractions84,
BranchStopPatch84,
DoubleBranchPatch84,
PrepareWorld84,
PrepareScenario84,
S84TestDefinitionBundle
];

NodeRole84[originalNode_,case_List,answer_Integer]:=Module[
{x,m,correct,wrong,dummy,querySources,queryBranch,role},
x=case[[1]];
m=x[[6,answer]];
correct=x[[5,answer]];
wrong=x[[5,1+Mod[answer,4]]];
dummy=m+3;
querySources={m,m+1,m+2};
queryBranch=Union[querySources,{correct,wrong,dummy}];
role=Which[
SameQ[originalNode,m],"QueriedDecision",
MemberQ[querySources,originalNode],"QueriedMediatorSource",
SameQ[originalNode,correct],"QueriedCorrectDestination",
SameQ[originalNode,wrong],"QueriedWrongDestination",
SameQ[originalNode,dummy],"QueriedDummyDestination",
MemberQ[x[[6]],originalNode],"OtherDecision",
MemberQ[x[[5]],originalNode],"OtherAnswerDestination",
True,"OtherReject"
];
<|
"Role"->role,
"QueryBranchRelated"->MemberQ[queryBranch,originalNode]
|>
];

EncodePair84[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[
{<|
"Grammar"->"S84BlindObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozenCandidate83B["EncoderParams"],
frozenCandidate83B["K"]
];
First[encoded["Codes"]]
];

PredictTokens84[tokens_List]:=If[
AnyTrue[tokens,MemberQ[frozenCandidate83B["Policy"],#]&],
"Continue",
"Stop"
];

SetAnswer84[c_List,answer_Integer]:={c[[1]],answer};

TopologyTransform84[topology_String,c_List]:=Switch[
topology,
"DoubleDiamondIn",DoubleDiamondIn79[c],
"HierarchicalDiamondIn",HierarchicalDiamondIn80[c],
_,$Failed
];

ExpectedContractions84[topology_String,baseCase_List]:=Switch[
topology,
"DoubleDiamondIn",2 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];

BranchStopPatch84[c_List,branch_Integer]:=Module[
{x,e,m,safe,u,dummy,correct,wrong,remove,add},
x=c[[1]];
e=x[[1]];
m=x[[6,branch]];
safe=m+1;
u=m+2;
dummy=m+3;
correct=x[[5,branch]];
wrong=x[[5,1+Mod[branch,4]]];
remove={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};
add={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};
<|
"Remove"->remove,
"Add"->add,
"ValidOnInput"->And[
And@@Map[MemberQ[e,#]&,remove],
And@@Map[!MemberQ[e,#]&,add],
Intersection[remove,add]==={}
]
|>
];

DoubleBranchPatch84[c_List,branches_List]:=Module[
{parts,remove,add},
parts=BranchStopPatch84[c,#]&/@branches;
remove=DeleteDuplicates@Flatten[Lookup[parts,"Remove"],1];
add=DeleteDuplicates@Flatten[Lookup[parts,"Add"],1];
<|
"Remove"->remove,
"Add"->add,
"Branches"->branches,
"ComponentPatchesValid"->And@@Lookup[parts,"ValidOnInput"],
"NoCrossBranchConflict"->Intersection[remove,add]==={},
"ExpectedEditCount"->And[Length[remove]===6,Length[add]===6]
|>
];

PrepareWorld84[
topology_String,
depth_Integer,
patchedBranches_List,
graphCondition_String,
answer_Integer,
target_String,
baseCase_List
]:=Module[
{
topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,
observations,originalNode,pair,roleInfo,rawTokens,tokens,prediction
},
topologyCase=TopologyTransform84[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions84[topology,baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];
pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[
Length[trace["Rejects"]]===0,
{},
DeleteDuplicates[trace["Rejects"][[All,2]]]
];
observations=Map[
Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole84[originalNode,canonicalCase,answer];
<|
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair84[pair]
|>
],
packedNodes
];
rawTokens=({#1["Role"],#1["Code"]}&)/@observations;
tokens=DeleteDuplicates[rawTokens];
prediction=PredictTokens84[tokens];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranches"->patchedBranches,
"GraphCondition"->graphCondition,
"Answer"->answer,
"Target"->target,
"ReferenceAction"->ReferenceAction82[canonicalCase],
"Prediction"->prediction,
"Correct"->SameQ[prediction,target],
"TopologyGraphHash"->Hash[topologyCase[[1,1]],"SHA256","HexString"],
"CanonicalGraphHash"->Hash[canonicalCase[[1,1]],"SHA256","HexString"],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[
canonicalization["Contractions"],expectedContractions
],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"StateObservationCount"->Length[observations],
"RawTokenCount"->Length[rawTokens],
"TokenCount"->Length[tokens],
"DuplicateTokensRemoved"->Length[rawTokens]-Length[tokens],
"PolicyHitTokens"->Intersection[tokens,frozenCandidate83B["Policy"]],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds
|>
];

PrepareScenario84[
topology_String,depth_Integer,patchedBranches_List
]:=Module[
{
seedCase,patch,hybridSeed,baseWorlds,hybridWorlds,
worldPairs,baseGraphHashes,hybridGraphHashes
},
seedCase=Case59[depth,1,"Continue"];
patch=DoubleBranchPatch84[seedCase,patchedBranches];
hybridSeed=ApplyEdgePatch81[seedCase,patch];
If[SameQ[hybridSeed,$Failed],Return[$Failed]];
baseWorlds=Table[
PrepareWorld84[
topology,depth,patchedBranches,"Baseline",answer,"Continue",
SetAnswer84[seedCase,answer]
],
{answer,Range[4]}
];
hybridWorlds=Table[
PrepareWorld84[
topology,depth,patchedBranches,"DoubleIntervention",answer,
If[MemberQ[patchedBranches,answer],"Stop","Continue"],
SetAnswer84[hybridSeed,answer]
],
{answer,Range[4]}
];
worldPairs=MapThread[
Function[{base,hybrid},
<|
"Answer"->base["Answer"],
"PatchedQuery"->MemberQ[patchedBranches,base["Answer"]],
"SameQuery"->SameQ[base["Answer"],hybrid["Answer"]],
"ReferenceRelationCorrect"->If[
MemberQ[patchedBranches,base["Answer"]],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Stop"]
],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Continue"]
]
],
"PredictionRelationCorrect"->If[
MemberQ[patchedBranches,base["Answer"]],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Stop"]
],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Continue"]
]
],
"PairCorrect"->And[TrueQ[base["Correct"]],TrueQ[hybrid["Correct"]]],
"BaselineWorld"->base,
"InterventionWorld"->hybrid
|>
],
{baseWorlds,hybridWorlds}
];
baseGraphHashes=Lookup[baseWorlds,"TopologyGraphHash"];
hybridGraphHashes=Lookup[hybridWorlds,"TopologyGraphHash"];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranches"->patchedBranches,
"PatchComponentValidity"->patch["ComponentPatchesValid"],
"PatchNoConflict"->patch["NoCrossBranchConflict"],
"PatchEditCountCorrect"->patch["ExpectedEditCount"],
"BaselineSameGraphAcrossQueries"->SameQ@@baseGraphHashes,
"InterventionSameGraphAcrossQueries"->SameQ@@hybridGraphHashes,
"PatchChangesGraph"->UnsameQ[First[baseGraphHashes],First[hybridGraphHashes]],
"ReferenceRelationsCorrect"->And@@Lookup[worldPairs,"ReferenceRelationCorrect"],
"PredictionRelationsCorrect"->And@@Lookup[worldPairs,"PredictionRelationCorrect"],
"AllEightWorldsCorrect"->And@@Join[
Lookup[baseWorlds,"Correct"],Lookup[hybridWorlds,"Correct"]
],
"WorldPairs"->worldPairs,
"BaselineWorlds"->baseWorlds,
"InterventionWorlds"->hybridWorlds
|>
];

S84TestDefinitionBundle[]:={
DownValues[NodeRole84],DownValues[EncodePair84],DownValues[PredictTokens84],
DownValues[SetAnswer84],DownValues[TopologyTransform84],
DownValues[ExpectedContractions84],DownValues[BranchStopPatch84],
DownValues[DoubleBranchPatch84],DownValues[PrepareWorld84],
DownValues[PrepareScenario84]
};

blindDepths84={29,53};
blindTopologies84={"DoubleDiamondIn","HierarchicalDiamondIn"};
blindPatchedBranchPairs84=Subsets[Range[4],{2}];

protocol84=<|
"Stage"->"S84",
"Name"->"BlindDoubleInterventionQueryGrid",
"Candidate"->"S83B-K19ExactRole",
"CandidateHash"->candidateHashLoaded84,
"Depths"->blindDepths84,
"Topologies"->blindTopologies84,
"PatchedBranchPairs"->blindPatchedBranchPairs84,
"ExpectedScenarios"->24,
"ExpectedWorldPairs"->96,
"ExpectedWorlds"->192,
"Intervention"->"TwoSimultaneousBranchStopPatches",
"QueryGrid"->"AllFourQueriesBeforeAndAfterIntervention",
"ExpectedPatchedQueryPairs"->48,
"ExpectedUnpatchedQueryPairs"->48,
"TokenDeduplication"->"DeleteDuplicatesAfterExactRoleCodePairing",
"CandidateFrozenBeforeProtocol"->True,
"CandidateSearchRun"->False,
"TrainingRun"->False,
"HistoricalRegressionRerun"->False,
"S83BlindRerun"->False,
"S83BDevelopmentRowsRerun"->False,
"S84LabelsUsedForSelection"->False,
"NoCaseEvaluatedBeforeProtocolHash"->True
|>;

protocolHash84=Hash[Normal[protocol84],"SHA256","HexString"];
modelHashBefore84=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore84=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashBefore84=Hash[CoreDefinitionBundle84[],"SHA256","HexString"];
canonicalizerHashBefore84=canonicalizerImplementationHash79B;
interventionHashBefore84=interventionImplementationHash82;
topologyHashBefore84=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
testDefinitionHashBefore84=Hash[
S84TestDefinitionBundle[],"SHA256","HexString"
];

Dataset[{Join[protocol84,<|"ProtocolHash"->protocolHash84|>]}]
'''.strip() + "\n"

cell3 = r'''
blindScenarios84=Flatten[
Table[
PrepareScenario84[topology,depth,patchedBranches],
{topology,blindTopologies84},
{depth,blindDepths84},
{patchedBranches,blindPatchedBranchPairs84}
],
2
];

blindWorldPairs84=Flatten[Lookup[blindScenarios84,"WorldPairs"],1];
baselineWorlds84=Flatten[Lookup[blindScenarios84,"BaselineWorlds"],1];
interventionWorlds84=Flatten[
Lookup[blindScenarios84,"InterventionWorlds"],1
];
blindWorlds84=Join[baselineWorlds84,interventionWorlds84];

summary84=<|
"Scenarios"->Length[blindScenarios84],
"WorldPairs"->Length[blindWorldPairs84],
"Worlds"->Length[blindWorlds84],
"PatchedQueryPairs"->Count[
blindWorldPairs84,p_/;TrueQ[p["PatchedQuery"]]
],
"UnpatchedQueryPairs"->Count[
blindWorldPairs84,p_/;!TrueQ[p["PatchedQuery"]]
],
"PatchComponentValidity"->Count[
blindScenarios84,s_/;TrueQ[s["PatchComponentValidity"]]
],
"PatchNoConflict"->Count[
blindScenarios84,s_/;TrueQ[s["PatchNoConflict"]]
],
"PatchEditCountCorrect"->Count[
blindScenarios84,s_/;TrueQ[s["PatchEditCountCorrect"]]
],
"BaselineSameGraphAcrossQueries"->Count[
blindScenarios84,s_/;TrueQ[s["BaselineSameGraphAcrossQueries"]]
],
"InterventionSameGraphAcrossQueries"->Count[
blindScenarios84,s_/;TrueQ[s["InterventionSameGraphAcrossQueries"]]
],
"PatchChangesGraph"->Count[
blindScenarios84,s_/;TrueQ[s["PatchChangesGraph"]]
],
"ReferenceRelationsCorrect"->Count[
blindWorldPairs84,p_/;TrueQ[p["ReferenceRelationCorrect"]]
],
"PredictionRelationsCorrect"->Count[
blindWorldPairs84,p_/;TrueQ[p["PredictionRelationCorrect"]]
],
"PairCorrect"->Count[
blindWorldPairs84,p_/;TrueQ[p["PairCorrect"]]
],
"ScenarioPerfect"->Count[
blindScenarios84,s_/;TrueQ[s["AllEightWorldsCorrect"]]
],
"BaselineCorrect"->Count[baselineWorlds84,w_/;TrueQ[w["Correct"]]],
"InterventionContinueCorrect"->Count[
interventionWorlds84,
w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"InterventionStopCorrect"->Count[
interventionWorlds84,
w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"WorldCorrect"->Count[blindWorlds84,w_/;TrueQ[w["Correct"]]],
"CanonicalCaseExactlyBase"->Count[
blindWorlds84,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindWorlds84,w_/;TrueQ[w["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
blindWorlds84,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"ReferenceActionsCorrect"->Count[
blindWorlds84,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"NonEmptyTokens"->Count[blindWorlds84,w_/;w["TokenCount"]>0],
"TerminatedNaturally"->Count[
blindWorlds84,w_/;TrueQ[w["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
blindWorlds84,w_/;TrueQ[w["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[blindWorlds84,"TraceSeconds"]
|>;

byTopology84=Map[
Function[topology,
Module[{scenarios,pairs,base,intervention,worlds},
scenarios=Select[blindScenarios84,SameQ[#["Topology"],topology]&];
pairs=Flatten[Lookup[scenarios,"WorldPairs"],1];
base=Flatten[Lookup[scenarios,"BaselineWorlds"],1];
intervention=Flatten[Lookup[scenarios,"InterventionWorlds"],1];
worlds=Join[base,intervention];
<|
"Topology"->topology,
"Scenarios"->Length[scenarios],
"Worlds"->Length[worlds],
"BaselineCorrect"->Count[base,w_/;TrueQ[w["Correct"]]],
"InterventionContinueCorrect"->Count[
intervention,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"InterventionStopCorrect"->Count[
intervention,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
"ScenarioPerfect"->Count[
scenarios,s_/;TrueQ[s["AllEightWorldsCorrect"]]
],
"CanonicalExact"->Count[
worlds,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"TerminatedNaturally"->Count[
worlds,w_/;TrueQ[w["TerminatedNaturally"]]
],
"TraceSeconds"->Total@Lookup[worlds,"TraceSeconds"]
|>
]
],
blindTopologies84
];

Column[{
Dataset[Map[
KeyTake[#,{"Topology","Depth","PatchedBranches",
"PatchComponentValidity","PatchNoConflict","PatchEditCountCorrect",
"BaselineSameGraphAcrossQueries","InterventionSameGraphAcrossQueries",
"ReferenceRelationsCorrect","PredictionRelationsCorrect",
"AllEightWorldsCorrect"}]&,
blindScenarios84
]],
Dataset[byTopology84],
Dataset[{summary84}]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfter84=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter84=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashAfter84=Hash[CoreDefinitionBundle84[],"SHA256","HexString"];
canonicalizerHashAfter84=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter84=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashAfter84=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
testDefinitionHashAfter84=Hash[
S84TestDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter84=Hash[Normal[protocol84],"SHA256","HexString"];

originalFrozenModelUnchanged84=And[
SameQ[modelHashBefore84,modelHashAfter84],
SameQ[modelHashAfter84,expectedFrozenModelHash79A]
];
frozenCandidateUnchanged84=And[
SameQ[candidateHashBefore84,candidateHashAfter84],
SameQ[candidateHashAfter84,expectedCandidateHash84]
];
coreUnchanged84=SameQ[coreHashBefore84,coreHashAfter84];
canonicalizerUnchanged84=And[
SameQ[canonicalizerHashBefore84,canonicalizerHashAfter84],
SameQ[canonicalizerHashAfter84,expectedCanonicalizerHash84]
];
interventionUnchanged84=And[
SameQ[interventionHashBefore84,interventionHashAfter84],
SameQ[interventionHashAfter84,expectedInterventionHash84]
];
topologiesUnchanged84=SameQ[topologyHashBefore84,topologyHashAfter84];
testDefinitionUnchanged84=SameQ[
testDefinitionHashBefore84,testDefinitionHashAfter84
];
protocolUnchanged84=SameQ[protocolHash84,protocolHashAfter84];
deduplicationMechanismUnchanged84=And[
TrueQ[coreUnchanged84],
TrueQ[testDefinitionUnchanged84],
SameQ[protocol84["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleCodePairing"]
];

testValidityPassed84=And[
TrueQ[preflightPassed84],
TrueQ[originalFrozenModelUnchanged84],
TrueQ[frozenCandidateUnchanged84],
TrueQ[coreUnchanged84],
TrueQ[canonicalizerUnchanged84],
TrueQ[interventionUnchanged84],
TrueQ[topologiesUnchanged84],
TrueQ[testDefinitionUnchanged84],
TrueQ[protocolUnchanged84],
TrueQ[deduplicationMechanismUnchanged84],
SameQ[summary84["Scenarios"],24],
SameQ[summary84["WorldPairs"],96],
SameQ[summary84["Worlds"],192],
SameQ[summary84["PatchedQueryPairs"],48],
SameQ[summary84["UnpatchedQueryPairs"],48],
SameQ[summary84["PatchComponentValidity"],24],
SameQ[summary84["PatchNoConflict"],24],
SameQ[summary84["PatchEditCountCorrect"],24],
SameQ[summary84["BaselineSameGraphAcrossQueries"],24],
SameQ[summary84["InterventionSameGraphAcrossQueries"],24],
SameQ[summary84["PatchChangesGraph"],24],
SameQ[summary84["ReferenceRelationsCorrect"],96],
SameQ[summary84["CanonicalCaseExactlyBase"],192],
SameQ[summary84["ContractionCountCorrect"],192],
SameQ[summary84["ProtectedNodesPreserved"],192],
SameQ[summary84["ReferenceActionsCorrect"],192],
SameQ[summary84["NonEmptyTokens"],192],
SameQ[summary84["TerminatedNaturally"],192],
SameQ[summary84["HitSafetyCap"],0]
];

blindPerfect84=And[
TrueQ[testValidityPassed84],
SameQ[summary84["BaselineCorrect"],96],
SameQ[summary84["InterventionContinueCorrect"],48],
SameQ[summary84["InterventionStopCorrect"],48],
SameQ[summary84["WorldCorrect"],192],
SameQ[summary84["PairCorrect"],96],
SameQ[summary84["PredictionRelationsCorrect"],96],
SameQ[summary84["ScenarioPerfect"],24]
];

resultPayload84=<|
"Stage"->"S84",
"Name"->"BlindDoubleInterventionQueryGrid",
"CandidateHash"->candidateHashAfter84,
"ProtocolHash"->protocolHashAfter84,
"Depths"->blindDepths84,
"Topologies"->blindTopologies84,
"Scenarios"->summary84["Scenarios"],
"WorldPairs"->summary84["WorldPairs"],
"Worlds"->summary84["Worlds"],
"BaselineCorrect"->summary84["BaselineCorrect"],
"InterventionContinueCorrect"->summary84["InterventionContinueCorrect"],
"InterventionStopCorrect"->summary84["InterventionStopCorrect"],
"WorldCorrect"->summary84["WorldCorrect"],
"PairCorrect"->summary84["PairCorrect"],
"PredictionRelationsCorrect"->summary84["PredictionRelationsCorrect"],
"ScenarioPerfect"->summary84["ScenarioPerfect"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged84],
"FrozenCandidateChanged"->!TrueQ[frozenCandidateUnchanged84],
"CoreChanged"->!TrueQ[coreUnchanged84],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged84],
"InterventionChanged"->!TrueQ[interventionUnchanged84],
"TopologyImplementationsChanged"->!TrueQ[topologiesUnchanged84],
"DeduplicationMechanismChanged"->!TrueQ[deduplicationMechanismUnchanged84],
"TestValidityPassed"->testValidityPassed84,
"BlindPerfect"->blindPerfect84
|>;

blindResultHash84=Hash[
Normal[resultPayload84],"SHA256","HexString"
];

cert84=Join[
resultPayload84,
<|
"CandidateFrozenBeforeS84"->True,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"HistoricalRegressionRerun"->False,
"S83BlindRerun"->False,
"S83BDevelopmentRowsRerun"->False,
"S84LabelsUsedForSelection"->False,
"DoubleInterventionNovel"->True,
"AllQueryRolesTestedPerGraph"->True,
"SameQueryBeforeAfterIntervention"->True,
"S84IsBlindCounterfactualCompositionTest"->True,
"MayClaimBlindMultiInterventionCounterfactualComposition"->blindPerfect84,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary84["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash84,
"Outcome"->Which[
!TrueQ[testValidityPassed84],
"INVALID_S84_BLIND_TEST",
TrueQ[blindPerfect84],
"BLIND_DOUBLE_INTERVENTION_QUERY_GRID_PASS",
True,
"VALID_BLIND_DOUBLE_INTERVENTION_QUERY_GRID_FAILURE"
],
"SuggestedNextStage"->If[
TrueQ[blindPerfect84],
"S85_INDEPENDENT_INTERVENTION_OPERATOR_BLIND_TEST",
"S84A_FAILURE_AUDIT_WITHOUT_RETUNING"
]
|>
];

Dataset[{cert84}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindPairs83=",
    "blindWorlds83=",
    "pairSummary83=",
    "cert83=",
    "cert83BScan=",
    "selectedRepresentation83B=",
    "semanticDevelopmentRows83B=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Prior blind/development material leaked into S84: {forbidden}")

if wl_source.index("protocolHash84=") > wl_source.index("blindScenarios84="):
    raise RuntimeError("S84 cases would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S84 — Blind Double-Intervention Query Grid\n",
                "\n",
                "The frozen S83B K=19 exact-role candidate is tested without tuning. "
                "Each scenario compares all four queries before and after two simultaneous "
                "branch interventions, under two locked topology transforms and unseen depths.\n",
                "\n",
                "Core propagation, canonicalization, intervention primitives, topology "
                "implementations, and DeleteDuplicates behavior are hash-locked.\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell.splitlines(keepends=True),
            }
            for cell in cells
        ],
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Wolfram Language 15",
            "language": "Wolfram Language",
            "name": "wolframlanguage15",
        },
        "language_info": {
            "codemirror_mode": "mathematica",
            "file_extension": ".m",
            "mimetype": "application/vnd.wolfram.m",
            "name": "Wolfram Language",
            "pygments_lexer": "mathematica",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_OUTPUT.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
