import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82C_SOURCE = ROOT / "TCCT_S82C_RepresentationCapacityDiagnosis.wl"
WL_OUTPUT = ROOT / "TCCT_S83_BlindQuerySwitchTopologyComposition.wl"
NB_OUTPUT = ROOT / "TCCT_S83_BlindQuerySwitchTopologyComposition.ipynb"
MARKER = "(* S83 CELL *)"


s82c = S82C_SOURCE.read_text(encoding="utf-8")
s82c_parts = s82c.split("(* S82C CELL *)")
if len(s82c_parts) != 5:
    raise RuntimeError("S82C source no longer has exactly four code cells")

# Copy only the frozen S75D architecture and the already locked S59-S82
# constructors/core helpers. S82C development rows, labels, scans, scores, and
# candidate selection are deliberately excluded.
base_definitions = s82c_parts[1].split(
    "expectedMinimalKernelDefinitionTextHash82C=", 1
)[0].rstrip()

cell1 = base_definitions + r'''

expectedMinimalKernelDefinitionTextHash83=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash83=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedStableFrozenArchitectureHash83=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedInterventionHash83=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedCandidateHash83=
"1aeac2dc1aa0ec4f6e187e25ec054e3e8188c75ab1058b74f620500b826a587a";

candidateSnapshotPath83=
"E:/engine_wolf/TCCT_S82C_FrozenCandidate.wl";

If[
!FileExistsQ[candidateSnapshotPath83],
Print["S83 aborted: frozen S82C candidate file is missing."];
Print["Run TCCT_S82C_FrozenCandidateRecovery.ipynb first."];
Abort[]
];

Get[candidateSnapshotPath83];

ClearAll[CoreDefinitionBundle83];
CoreDefinitionBundle83[]:={
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
};

minimalKernelDefinitionTextHash83=Hash[
ToString[InputForm[CoreDefinitionBundle83[]]],
"SHA256","HexString"
];

stableFrozenArchitectureHash83=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash83,
canonicalizerImplementationHash79B
},
"SHA256","HexString"
];

candidateHashLoaded83=If[
AssociationQ[frozenCandidate82C],
Hash[Normal[frozenCandidate82C],"SHA256","HexString"],
Missing["CandidateNotLoaded"]
];

preflightPassed83=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash83,
expectedMinimalKernelDefinitionTextHash83
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash83
],
SameQ[
stableFrozenArchitectureHash83,
expectedStableFrozenArchitectureHash83
],
SameQ[interventionImplementationHash82,expectedInterventionHash83],
AssociationQ[frozenCandidate82C],
SameQ[candidateHashLoaded83,expectedCandidateHash83],
SameQ[frozenCandidate82C["BaseFrozenModelHash"],expectedFrozenModelHash79A],
SameQ[frozenCandidate82C["EncoderParams"],frozen75D["Params"]],
SameQ[frozenCandidate82C["Representation"],"KExactRole"],
SameQ[frozenCandidate82C["K"],10],
SameQ[Length[frozenCandidate82C["Policy"]],8],
TrueQ[frozenCandidate82C["ExactNodeRoleUsed"]],
TrueQ[frozenCandidate82C["FrozenBeforeS83"]]
];

preflight83=<|
"Stage"->"S83",
"Name"->"BlindQuerySwitchTopologyComposition",
"CandidateFileLoaded"->FileExistsQ[candidateSnapshotPath83],
"CandidateHash"->candidateHashLoaded83,
"ExpectedCandidateHash"->expectedCandidateHash83,
"CandidateK"->If[AssociationQ[frozenCandidate82C],frozenCandidate82C["K"],Missing[]],
"CandidatePolicyLength"->If[
AssociationQ[frozenCandidate82C],Length[frozenCandidate82C["Policy"]],Missing[]
],
"OriginalFrozenModelChanged"->False,
"FrozenCandidateChanged"->False,
"CoreChanged"->False,
"PreflightPassed"->preflightPassed83
|>;

If[
!TrueQ[preflightPassed83],
Print[Dataset[{preflight83}]];
Print["S83 aborted: frozen architecture or S82C candidate mismatch."];
Abort[]
];

Dataset[{preflight83}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
NodeRole83,
EncodePair83,
PredictTokens83,
SetAnswer83,
TopologyTransform83,
ExpectedContractions83,
PrepareWorld83,
PreparePair83,
S83TestDefinitionBundle
];

NodeRole83[originalNode_,case_List,answer_Integer]:=Module[
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

EncodePair83[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[
{<|
"Grammar"->"S83BlindObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozenCandidate82C["EncoderParams"],
frozenCandidate82C["K"]
];
First[encoded["Codes"]]
];

PredictTokens83[tokens_List]:=If[
AnyTrue[tokens,MemberQ[frozenCandidate82C["Policy"],#]&],
"Continue",
"Stop"
];

SetAnswer83[c_List,answer_Integer]:={c[[1]],answer};

TopologyTransform83[topology_String,c_List]:=Switch[
topology,
"DoubleDiamondIn",DoubleDiamondIn79[c],
"HierarchicalDiamondIn",HierarchicalDiamondIn80[c],
_,$Failed
];

ExpectedContractions83[topology_String,baseCase_List]:=Switch[
topology,
"DoubleDiamondIn",2 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];

PrepareWorld83[
topology_String,
depth_Integer,
patchedBranch_Integer,
answer_Integer,
target_String,
baseCase_List
]:=Module[
{
topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,
observations,originalNode,pair,roleInfo,rawTokens,tokens,prediction
},
topologyCase=TopologyTransform83[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions83[topology,baseCase];
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
roleInfo=NodeRole83[originalNode,canonicalCase,answer];
<|
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair83[pair]
|>
],
packedNodes
];
rawTokens=({#1["Role"],#1["Code"]}&)/@observations;
tokens=DeleteDuplicates[rawTokens];
prediction=PredictTokens83[tokens];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranch"->patchedBranch,
"Answer"->answer,
"Target"->target,
"ReferenceAction"->ReferenceAction82[canonicalCase],
"Prediction"->prediction,
"Correct"->SameQ[prediction,target],
"BaseGraphHash"->Hash[baseCase[[1,1]],"SHA256","HexString"],
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
"PolicyHitTokens"->Intersection[tokens,frozenCandidate82C["Policy"]],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds
|>
];

PreparePair83[
topology_String,depth_Integer,patchedBranch_Integer
]:=Module[
{
seedCase,patch,hybridCase,factualAnswer,counterfactualAnswer,
factualBase,counterfactualBase,factualWorld,counterfactualWorld
},
seedCase=Case59[depth,patchedBranch,"Continue"];
patch=LocalMediatorPatch82[depth,patchedBranch];
hybridCase=ApplyEdgePatch81[seedCase,patch];
factualAnswer=1+Mod[patchedBranch,4];
counterfactualAnswer=patchedBranch;
factualBase=SetAnswer83[hybridCase,factualAnswer];
counterfactualBase=SetAnswer83[hybridCase,counterfactualAnswer];
factualWorld=PrepareWorld83[
topology,depth,patchedBranch,factualAnswer,"Continue",factualBase
];
counterfactualWorld=PrepareWorld83[
topology,depth,patchedBranch,counterfactualAnswer,"Stop",counterfactualBase
];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranch"->patchedBranch,
"FactualAnswer"->factualAnswer,
"CounterfactualAnswer"->counterfactualAnswer,
"SameBaseGraph"->SameQ[factualBase[[1]],counterfactualBase[[1]]],
"SameTopologyGraph"->SameQ[
factualWorld["TopologyGraphHash"],counterfactualWorld["TopologyGraphHash"]
],
"OnlyQueryChanged"->And[
SameQ[factualBase[[1]],counterfactualBase[[1]]],
UnsameQ[factualBase[[2]],counterfactualBase[[2]]]
],
"ReferenceFlipCorrect"->And[
SameQ[factualWorld["ReferenceAction"],"Continue"],
SameQ[counterfactualWorld["ReferenceAction"],"Stop"]
],
"FactualPrediction"->factualWorld["Prediction"],
"CounterfactualPrediction"->counterfactualWorld["Prediction"],
"PredictionFlipCorrect"->And[
SameQ[factualWorld["Prediction"],"Continue"],
SameQ[counterfactualWorld["Prediction"],"Stop"]
],
"PairCorrect"->And[
TrueQ[factualWorld["Correct"]],
TrueQ[counterfactualWorld["Correct"]]
],
"FactualWorld"->factualWorld,
"CounterfactualWorld"->counterfactualWorld
|>
];

S83TestDefinitionBundle[]:={
DownValues[NodeRole83],DownValues[EncodePair83],DownValues[PredictTokens83],
DownValues[SetAnswer83],DownValues[TopologyTransform83],
DownValues[ExpectedContractions83],DownValues[PrepareWorld83],
DownValues[PreparePair83]
};

blindDepths83={23,47};
blindTopologies83={"DoubleDiamondIn","HierarchicalDiamondIn"};
blindPatchedBranches83=Range[4];

protocol83=<|
"Stage"->"S83",
"Name"->"BlindQuerySwitchTopologyComposition",
"Candidate"->"S82C-K10ExactRole",
"CandidateHash"->candidateHashLoaded83,
"Depths"->blindDepths83,
"Topologies"->blindTopologies83,
"PatchedBranches"->blindPatchedBranches83,
"ExpectedPairs"->16,
"ExpectedWorlds"->32,
"Intervention"->"SameGraphQuerySwitchFromUnpatchedToPatchedBranch",
"FactualTarget"->"Continue",
"CounterfactualTarget"->"Stop",
"GraphChangesWithinPair"->0,
"TokenDeduplication"->"DeleteDuplicatesAfterExactRoleCodePairing",
"CandidateFrozenBeforeProtocol"->True,
"CandidateSearchRun"->False,
"TrainingRun"->False,
"HistoricalRegressionRerun"->False,
"S82BlindRerun"->False,
"S82CDevelopmentRowsRerun"->False,
"S83LabelsUsedForSelection"->False,
"NoCaseEvaluatedBeforeProtocolHash"->True
|>;

protocolHash83=Hash[Normal[protocol83],"SHA256","HexString"];
modelHashBefore83=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore83=Hash[Normal[frozenCandidate82C],"SHA256","HexString"];
coreHashBefore83=Hash[CoreDefinitionBundle83[],"SHA256","HexString"];
canonicalizerHashBefore83=canonicalizerImplementationHash79B;
interventionHashBefore83=interventionImplementationHash82;
topologyHashBefore83=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
testDefinitionHashBefore83=Hash[
S83TestDefinitionBundle[],"SHA256","HexString"
];

Dataset[{Join[
protocol83,
<|"ProtocolHash"->protocolHash83|>
]}]
'''.strip() + "\n"

cell3 = r'''
blindPairs83=Flatten[
Table[
PreparePair83[topology,depth,patchedBranch],
{topology,blindTopologies83},
{depth,blindDepths83},
{patchedBranch,blindPatchedBranches83}
],
2
];

blindWorlds83=Flatten[
Map[
{#["FactualWorld"],#["CounterfactualWorld"]}&,
blindPairs83
],
1
];

pairSummary83=<|
"Pairs"->Length[blindPairs83],
"Worlds"->Length[blindWorlds83],
"SameBaseGraph"->Count[
blindPairs83,pair_/;TrueQ[pair["SameBaseGraph"]]
],
"SameTopologyGraph"->Count[
blindPairs83,pair_/;TrueQ[pair["SameTopologyGraph"]]
],
"OnlyQueryChanged"->Count[
blindPairs83,pair_/;TrueQ[pair["OnlyQueryChanged"]]
],
"ReferenceFlipCorrect"->Count[
blindPairs83,pair_/;TrueQ[pair["ReferenceFlipCorrect"]]
],
"FactualCorrect"->Count[
blindWorlds83,
world_/;SameQ[world["Target"],"Continue"]&&TrueQ[world["Correct"]]
],
"CounterfactualCorrect"->Count[
blindWorlds83,
world_/;SameQ[world["Target"],"Stop"]&&TrueQ[world["Correct"]]
],
"PairCorrect"->Count[
blindPairs83,pair_/;TrueQ[pair["PairCorrect"]]
],
"PredictionFlipCorrect"->Count[
blindPairs83,pair_/;TrueQ[pair["PredictionFlipCorrect"]]
],
"CanonicalCaseExactlyBase"->Count[
blindWorlds83,world_/;TrueQ[world["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindWorlds83,world_/;TrueQ[world["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
blindWorlds83,world_/;TrueQ[world["ProtectedNodesPreserved"]]
],
"ReferenceActionsCorrect"->Count[
blindWorlds83,world_/;SameQ[world["ReferenceAction"],world["Target"]]
],
"NonEmptyTokens"->Count[
blindWorlds83,world_/;world["TokenCount"]>0
],
"TerminatedNaturally"->Count[
blindWorlds83,world_/;TrueQ[world["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
blindWorlds83,world_/;TrueQ[world["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[blindWorlds83,"TraceSeconds"]
|>;

byTopology83=Map[
Function[topology,
Module[{pairs,worlds},
pairs=Select[blindPairs83,SameQ[#["Topology"],topology]&];
worlds=Flatten[
Map[{#["FactualWorld"],#["CounterfactualWorld"]}&,pairs],1
];
<|
"Topology"->topology,
"Pairs"->Length[pairs],
"FactualCorrect"->Count[
worlds,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"CounterfactualCorrect"->Count[
worlds,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
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
blindTopologies83
];

Column[{
Dataset[Map[
KeyTake[#,{"Topology","Depth","PatchedBranch","FactualAnswer",
"CounterfactualAnswer","SameBaseGraph","OnlyQueryChanged",
"ReferenceFlipCorrect","FactualPrediction","CounterfactualPrediction",
"PredictionFlipCorrect","PairCorrect"}]&,
blindPairs83
]],
Dataset[byTopology83],
Dataset[{pairSummary83}]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfter83=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter83=Hash[
Normal[frozenCandidate82C],"SHA256","HexString"
];
coreHashAfter83=Hash[CoreDefinitionBundle83[],"SHA256","HexString"];
canonicalizerHashAfter83=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter83=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashAfter83=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
testDefinitionHashAfter83=Hash[
S83TestDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter83=Hash[Normal[protocol83],"SHA256","HexString"];

originalFrozenModelUnchanged83=And[
SameQ[modelHashBefore83,modelHashAfter83],
SameQ[modelHashAfter83,expectedFrozenModelHash79A]
];
frozenCandidateUnchanged83=And[
SameQ[candidateHashBefore83,candidateHashAfter83],
SameQ[candidateHashAfter83,expectedCandidateHash83]
];
coreUnchanged83=SameQ[coreHashBefore83,coreHashAfter83];
canonicalizerUnchanged83=And[
SameQ[canonicalizerHashBefore83,canonicalizerHashAfter83],
SameQ[canonicalizerHashAfter83,expectedCanonicalizerHash83]
];
interventionUnchanged83=And[
SameQ[interventionHashBefore83,interventionHashAfter83],
SameQ[interventionHashAfter83,expectedInterventionHash83]
];
topologiesUnchanged83=SameQ[topologyHashBefore83,topologyHashAfter83];
testDefinitionUnchanged83=SameQ[
testDefinitionHashBefore83,testDefinitionHashAfter83
];
protocolUnchanged83=SameQ[protocolHash83,protocolHashAfter83];
deduplicationMechanismUnchanged83=And[
TrueQ[coreUnchanged83],
TrueQ[testDefinitionUnchanged83],
SameQ[protocol83["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleCodePairing"]
];

testValidityPassed83=And[
TrueQ[preflightPassed83],
TrueQ[originalFrozenModelUnchanged83],
TrueQ[frozenCandidateUnchanged83],
TrueQ[coreUnchanged83],
TrueQ[canonicalizerUnchanged83],
TrueQ[interventionUnchanged83],
TrueQ[topologiesUnchanged83],
TrueQ[testDefinitionUnchanged83],
TrueQ[protocolUnchanged83],
TrueQ[deduplicationMechanismUnchanged83],
SameQ[pairSummary83["Pairs"],16],
SameQ[pairSummary83["Worlds"],32],
SameQ[pairSummary83["SameBaseGraph"],16],
SameQ[pairSummary83["SameTopologyGraph"],16],
SameQ[pairSummary83["OnlyQueryChanged"],16],
SameQ[pairSummary83["ReferenceFlipCorrect"],16],
SameQ[pairSummary83["CanonicalCaseExactlyBase"],32],
SameQ[pairSummary83["ContractionCountCorrect"],32],
SameQ[pairSummary83["ProtectedNodesPreserved"],32],
SameQ[pairSummary83["ReferenceActionsCorrect"],32],
SameQ[pairSummary83["NonEmptyTokens"],32],
SameQ[pairSummary83["TerminatedNaturally"],32],
SameQ[pairSummary83["HitSafetyCap"],0]
];

blindPerfect83=And[
TrueQ[testValidityPassed83],
SameQ[pairSummary83["FactualCorrect"],16],
SameQ[pairSummary83["CounterfactualCorrect"],16],
SameQ[pairSummary83["PairCorrect"],16],
SameQ[pairSummary83["PredictionFlipCorrect"],16]
];

resultPayload83=<|
"Stage"->"S83",
"Name"->"BlindQuerySwitchTopologyComposition",
"CandidateHash"->candidateHashAfter83,
"ProtocolHash"->protocolHashAfter83,
"Depths"->blindDepths83,
"Topologies"->blindTopologies83,
"Pairs"->pairSummary83["Pairs"],
"Worlds"->pairSummary83["Worlds"],
"FactualCorrect"->pairSummary83["FactualCorrect"],
"CounterfactualCorrect"->pairSummary83["CounterfactualCorrect"],
"PairCorrect"->pairSummary83["PairCorrect"],
"PredictionFlipCorrect"->pairSummary83["PredictionFlipCorrect"],
"SameGraphPairs"->pairSummary83["SameBaseGraph"],
"OnlyQueryChangedPairs"->pairSummary83["OnlyQueryChanged"],
"ReferenceFlipCorrectPairs"->pairSummary83["ReferenceFlipCorrect"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged83],
"FrozenCandidateChanged"->!TrueQ[frozenCandidateUnchanged83],
"CoreChanged"->!TrueQ[coreUnchanged83],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged83],
"InterventionChanged"->!TrueQ[interventionUnchanged83],
"TopologyImplementationsChanged"->!TrueQ[topologiesUnchanged83],
"DeduplicationMechanismChanged"->!TrueQ[deduplicationMechanismUnchanged83],
"TestValidityPassed"->testValidityPassed83,
"BlindPerfect"->blindPerfect83
|>;

blindResultHash83=Hash[
Normal[resultPayload83],"SHA256","HexString"
];

cert83=Join[
resultPayload83,
<|
"CandidateFrozenBeforeS83"->True,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"HistoricalRegressionRerun"->False,
"S82BlindRerun"->False,
"S82CDevelopmentRowsRerun"->False,
"S83LabelsUsedForSelection"->False,
"SameGraphCounterfactual"->True,
"QueryInterventionNovel"->True,
"TopologyInterventionCompositionNovel"->True,
"S83IsBlindCounterfactualCompositionTest"->True,
"MayClaimBlindQueryRelativeCounterfactualComposition"->blindPerfect83,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->pairSummary83["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash83,
"Outcome"->Which[
!TrueQ[testValidityPassed83],
"INVALID_S83_BLIND_TEST",
TrueQ[blindPerfect83],
"BLIND_QUERY_SWITCH_COMPOSITION_PASS",
True,
"VALID_BLIND_QUERY_SWITCH_COMPOSITION_FAILURE"
],
"SuggestedNextStage"->If[
TrueQ[blindPerfect83],
"S84_INDEPENDENT_INTERVENTION_FAMILY_BLIND_TEST",
"S83A_FAILURE_AUDIT_WITHOUT_RETUNING"
]
|>
];

Dataset[{cert83}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "legacyRows82C=",
    "stressFitRows82C=",
    "stressValidationRows82C=",
    "capacityResults82C=",
    "selectedCapacityCandidate82C=",
    "blindCounterfactualPairs82=",
    "blindDepths82=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Prior development/blind material leaked into S83: {forbidden}")

if wl_source.index("protocolHash83=") > wl_source.index("blindPairs83="):
    raise RuntimeError("S83 cases would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S83 — Blind Query-Switch Topology Composition\n",
                "\n",
                "冻结的 S82C `K10ExactRole` 候选在 16 对、32 个世界上接受盲测。每对世界的图完全相同，只切换查询分支；测试同时叠加 DoubleDiamondIn 与 HierarchicalDiamondIn。\n",
                "\n",
                "本文件不重跑 S82C 开发集、不搜索候选、不修改策略。若第一格提示候选文件缺失，请先运行独立的 S82C Frozen Candidate Recovery notebook。\n",
                "\n",
                "候选快照固定保存为 `E:/engine_wolf/TCCT_S82C_FrozenCandidate.wl`，避免中文 Windows 用户路径编码问题。\n",
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
