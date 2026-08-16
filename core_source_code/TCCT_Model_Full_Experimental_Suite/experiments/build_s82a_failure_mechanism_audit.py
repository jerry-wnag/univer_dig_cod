import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82_SOURCE = ROOT / "TCCT_S82_BlindLocalMediatorCounterfactualTest.wl"
WL_OUTPUT = ROOT / "TCCT_S82A_BlindCounterfactualFailureMechanismAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S82A_BlindCounterfactualFailureMechanismAudit.ipynb"
MARKER = "(* S82A CELL *)"


s82 = S82_SOURCE.read_text(encoding="utf-8")
parts = s82.split("(* S82 CELL *)")
if len(parts) != 5:
    raise RuntimeError("S82 source no longer has exactly four code cells")

# Definitions only. No S82 blind rows or score/result computation is copied.
frozen_architecture = parts[1].split("expectedMinimalKernelHash82=", 1)[0].rstrip()
intervention_definitions = parts[2].split("blindDepths82=", 1)[0].rstrip()

cell1 = frozen_architecture + "\n\n" + intervention_definitions + r'''

expectedMinimalKernelHash82A=
"ec291466f20922dc4b2b879853cd3879c37151fb7e96c34eff45dcb185fe7f34";
expectedMinimalKernelDefinitionTextHash82A=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash82A=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedFrozenArchitectureHash82A=
"47c0f2de12d2b8d1d0311f7a0fecacba782ff9f0b391b3c86631fdb569a8a3b7";
expectedStableFrozenArchitectureHash82A=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedNeutralTopologyHash82A=
"01af33358afe3fcfe876288b6de7c99a89af22599320fec75911661e240bc121";
expectedInterventionHash82A=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedS82ProtocolHash82A=
"7695bea7ea07f903615ce01ad6b6a8481d2741ef1ce08fafb0e2d279e39f09bd";
expectedS82BlindResultHash82A=
"64be56fb8ef29638666efaf92cdcd03994a43e3328236fd0f7bd73a4808aa58f";

ClearAll[CoreDefinitionBundle82A];
CoreDefinitionBundle82A[]:={
DownValues[P59],
DownValues[A59],
DownValues[T59],
DownValues[Case59],
OwnValues[rw60],
DownValues[Pack60],
DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],
DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],
DownValues[EncodeRows75],
DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],
DownValues[Case79]
};

minimalKernelDefinitionTextHash82A=Hash[
ToString[InputForm[CoreDefinitionBundle82A[]]],
"SHA256",
"HexString"
];

frozenArchitectureHash82A=Hash[
{
Normal[frozen75D],
minimalKernelHash79A,
canonicalizerImplementationHash79B
},
"SHA256",
"HexString"
];

stableFrozenArchitectureHash82A=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash82A,
canonicalizerImplementationHash79B
},
"SHA256",
"HexString"
];

preflightPassed82A=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash82A,
expectedMinimalKernelDefinitionTextHash82A
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash82A
],
SameQ[
stableFrozenArchitectureHash82A,
expectedStableFrozenArchitectureHash82A
],
SameQ[
topologyImplementationHash80,
expectedNeutralTopologyHash82A
],
SameQ[
interventionImplementationHash82,
expectedInterventionHash82A
]
];

preflight82A=<|
"Stage"->"S82A",
"Name"->"BlindCounterfactualFailureMechanismAudit",
"AuditOnly"->True,
"PriorS82ProtocolHash"->expectedS82ProtocolHash82A,
"PriorS82BlindResultHash"->expectedS82BlindResultHash82A,
"RuntimeMinimalKernelHash"->minimalKernelHash79A,
"LegacyCheckpointMinimalKernelHash"->
expectedMinimalKernelHash82A,
"MinimalKernelDefinitionTextHash"->
minimalKernelDefinitionTextHash82A,
"RuntimeFrozenArchitectureHash"->
frozenArchitectureHash82A,
"LegacyCheckpointFrozenArchitectureHash"->
expectedFrozenArchitectureHash82A,
"StableFrozenArchitectureHash"->
stableFrozenArchitectureHash82A,
"InterventionImplementationHash"->
interventionImplementationHash82,
"HistoricalRegressionRerun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"CandidateSearchRun"->False,
"NewModelSelected"->False,
"PreflightPassed"->preflightPassed82A
|>;

If[
!TrueQ[preflightPassed82A],
Print[Dataset[{preflight82A}]];
Print["S82A aborted: S82 frozen architecture or intervention mismatch."];
Abort[]
];

Dataset[{preflight82A}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
WorldCase82A,
EncodeStatePair82A,
PrepareMechanismWorld82A,
SemanticConflictCount82A,
CaseSignatureConflictCount82A,
WorldSummary82A
];

auditDepths82A={31,63};
auditAnswers82A=Range[4];
auditWorlds82A={
"FactualContinue",
"GlobalStop",
"LocalStopHybrid"
};

WorldCase82A[
world_String,
depth_Integer,
answer_Integer
]:=Switch[
world,
"FactualContinue",
Case59[depth,answer,"Continue"],
"GlobalStop",
Case59[depth,answer,"Stop"],
"LocalStopHybrid",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
],
_,
$Failed
];

EncodeStatePair82A[pair_List]:=Module[
{encoded},
encoded=First@EncodeRows75[
{<|
"Grammar"->"S82AMechanismObservation",
"Depth"->0,
"Answer"->0,
"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozen75D["Params"],
frozen75D["K"]
];
First[encoded["Codes"]]
];

auditProtocol82A=<|
"Stage"->"S82A",
"Name"->"BlindCounterfactualFailureMechanismAudit",
"Depths"->auditDepths82A,
"Answers"->auditAnswers82A,
"Worlds"->auditWorlds82A,
"ExpectedCases"->24,
"Purpose"->
"RawRadiusAndNodeLevelEncoderPolicyAttribution",
"PriorS82ResultChanged"->False,
"S82UsedForRetuning"->False,
"PolicyEditApplied"->False,
"CandidateSearchRun"->False,
"NewModelSelected"->False
|>;

auditProtocolHash82A=Hash[
Normal[auditProtocol82A],
"SHA256",
"HexString"
];

modelHashBeforeAudit82A=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];
coreHashBeforeAudit82A=minimalKernelHash79A;
coreDefinitionTextHashBeforeAudit82A=
minimalKernelDefinitionTextHash82A;
canonicalizerHashBeforeAudit82A=
canonicalizerImplementationHash79B;
neutralTopologyHashBeforeAudit82A=
topologyImplementationHash80;
interventionHashBeforeAudit82A=
interventionImplementationHash82;
auditProtocolHashBefore82A=auditProtocolHash82A;

Dataset[{<|
"Stage"->"S82A",
"AuditProtocolHash"->auditProtocolHash82A,
"ExpectedCases"->24,
"HistoricalRegressionRerun"->False,
"S82BlindScoreChanged"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False
|>}]
'''.strip() + "\n"

cell3 = r'''
PrepareMechanismWorld82A[
world_String,
depth_Integer,
answer_Integer
]:=Module[
{
case,reference,canonicalization,canonicalCase,
traceSeconds,trace,levels,pack,vertexList,nodes,
queriedDecision,queriedSources,correct,wrong,dummy,
observations,codes,policyHits,prediction
},
case=WorldCase82A[world,depth,answer];
reference=ReferenceAction82[case];
canonicalization=CanonicalizePrivateDiamonds79B[case];
canonicalCase=canonicalization["Case"];
{traceSeconds,trace}=AbsoluteTiming[
RejectTrace78[canonicalCase]
];
levels=SigLevels61[canonicalCase,3];
pack=Pack60[canonicalCase];
vertexList=pack[[12]];
nodes=If[
Length[trace["Rejects"]]===0,
{},
DeleteDuplicates[trace["Rejects"][[All,2]]]
];
queriedDecision=canonicalCase[[1,6,answer]];
queriedSources={
queriedDecision,
queriedDecision+1,
queriedDecision+2
};
correct=canonicalCase[[1,5,answer]];
wrong=canonicalCase[[1,5,1+Mod[answer,4]]];
dummy=queriedDecision+3;
observations=Map[
Function[node,
Module[{pair,code,originalNode,role,queryBranchRelated},
pair={
Lookup[levels[[3]],node],
Lookup[levels[[4]],node]
};
code=EncodeStatePair82A[pair];
originalNode=vertexList[[node]];
role=Which[
SameQ[originalNode,queriedDecision],
"QueriedDecision",
MemberQ[queriedSources,originalNode],
"QueriedMediatorSource",
SameQ[originalNode,correct],
"QueriedCorrectDestination",
SameQ[originalNode,wrong],
"QueriedWrongDestination",
SameQ[originalNode,dummy],
"QueriedDummyDestination",
MemberQ[canonicalCase[[1,6]],originalNode],
"OtherDecision",
MemberQ[canonicalCase[[1,5]],originalNode],
"OtherAnswerDestination",
True,
"OtherReject"
];
queryBranchRelated=MemberQ[
Union[queriedSources,{correct,wrong,dummy}],
originalNode
];
<|
"World"->world,
"Depth"->depth,
"Answer"->answer,
"ReferenceAction"->reference,
"PackedNode"->node,
"OriginalNode"->originalNode,
"NodeRole"->role,
"QueryBranchRelated"->queryBranchRelated,
"RawPairHash"->Hash[pair,"SHA256","HexString"],
"Radius2Hash"->Hash[pair[[1]],"SHA256","HexString"],
"Radius3Hash"->Hash[pair[[2]],"SHA256","HexString"],
"Code"->code,
"CodeHash"->Hash[code,"SHA256","HexString"],
"PolicyHit"->MemberQ[frozen75D["Policy"],code]
|>
]
],
nodes
];
codes=DeleteDuplicates@Lookup[observations,"Code"];
policyHits=Intersection[codes,frozen75D["Policy"]];
prediction=If[
Length[policyHits]>0,
"Continue",
"Stop"
];
<|
"World"->world,
"Depth"->depth,
"Answer"->answer,
"ReferenceAction"->reference,
"TraceSeconds"->traceSeconds,
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"RejectNodeCount"->Length[nodes],
"QueriedDecisionRejectPresent"->AnyTrue[
observations,
SameQ[#["NodeRole"],"QueriedDecision"]&
],
"Codes"->codes,
"PolicyHits"->policyHits,
"PolicyHitFraction"->If[
Length[codes]===0,
0.,
N[Length[policyHits]/Length[codes]]
],
"AllCodesPolicyTriggered"->And[
Length[codes]>0,
SameQ[Length[policyHits],Length[codes]]
],
"QueriedDecisionPolicyHit"->AnyTrue[
observations,
And[
SameQ[#["NodeRole"],"QueriedDecision"],
TrueQ[#["PolicyHit"]]
]&
],
"NonQueriedPolicyHit"->AnyTrue[
observations,
And[
!SameQ[#["NodeRole"],"QueriedDecision"],
TrueQ[#["PolicyHit"]]
]&
],
"QueriedBranchPolicyHit"->AnyTrue[
observations,
And[
TrueQ[#["QueryBranchRelated"]],
TrueQ[#["PolicyHit"]]
]&
],
"OutsideQueriedBranchPolicyHit"->AnyTrue[
observations,
And[
!TrueQ[#["QueryBranchRelated"]],
TrueQ[#["PolicyHit"]]
]&
],
"RawPairHashes"->DeleteDuplicates@Lookup[
observations,
"RawPairHash"
],
"Radius2Hashes"->DeleteDuplicates@Lookup[
observations,
"Radius2Hash"
],
"Radius3Hashes"->DeleteDuplicates@Lookup[
observations,
"Radius3Hash"
],
"CodeHashes"->DeleteDuplicates@Lookup[
observations,
"CodeHash"
],
"Prediction"->prediction,
"Correct"->SameQ[prediction,reference],
"Observations"->observations
|>
];

mechanismRows82A=Flatten[
Table[
PrepareMechanismWorld82A[world,depth,answer],
{world,auditWorlds82A},
{depth,auditDepths82A},
{answer,auditAnswers82A}
],
2
];

mechanismObservations82A=Flatten[
Lookup[mechanismRows82A,"Observations"],
1
];

SemanticConflictCount82A[
observations_List,
key_String
]:=Module[{groups},
groups=Values@GroupBy[
observations,
Lookup[#,key]&
];
Count[
groups,
group_/;Length[
DeleteDuplicates@Lookup[group,"ReferenceAction"]
]>1
]
];

CaseSignatureConflictCount82A[
rows_List,
key_String
]:=Module[{groups},
groups=Values@GroupBy[
rows,
Hash[Sort@Lookup[#,key],"SHA256","HexString"]&
];
Count[
groups,
group_/;Length[
DeleteDuplicates@Lookup[group,"ReferenceAction"]
]>1
]
];

WorldSummary82A[world_String]:=Module[
{rows,observations},
rows=Select[
mechanismRows82A,
SameQ[#["World"],world]&
];
observations=Flatten[Lookup[rows,"Observations"],1];
<|
"World"->world,
"Cases"->Length[rows],
"ReferenceActions"->Counts@Lookup[rows,"ReferenceAction"],
"Predictions"->Counts@Lookup[rows,"Prediction"],
"Correct"->Count[rows,row_/;TrueQ[row["Correct"]]],
"Codes"->Union@@Lookup[rows,"Codes"],
"PolicyCollisionCodes"->Intersection[
Union@@Lookup[rows,"Codes"],
frozen75D["Policy"]
],
"RowsWithAnyPolicyHit"->Count[
rows,
row_/;Length[row["PolicyHits"]]>0
],
"RowsWithAllCodesPolicyTriggered"->Count[
rows,
row_/;TrueQ[row["AllCodesPolicyTriggered"]]
],
"QueriedDecisionRejectPresent"->Count[
rows,
row_/;TrueQ[row["QueriedDecisionRejectPresent"]]
],
"QueriedDecisionPolicyHit"->Count[
rows,
row_/;TrueQ[row["QueriedDecisionPolicyHit"]]
],
"NonQueriedPolicyHit"->Count[
rows,
row_/;TrueQ[row["NonQueriedPolicyHit"]]
],
"QueriedBranchPolicyHit"->Count[
rows,
row_/;TrueQ[row["QueriedBranchPolicyHit"]]
],
"OutsideQueriedBranchPolicyHit"->Count[
rows,
row_/;TrueQ[row["OutsideQueriedBranchPolicyHit"]]
],
"ObservationCount"->Length[observations],
"TerminatedNaturally"->Count[
rows,
row_/;TrueQ[row["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
rows,
row_/;TrueQ[row["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[rows,"TraceSeconds"]
|>
];

worldSummary82A=WorldSummary82A/@auditWorlds82A;

factualRows82A=Select[
mechanismRows82A,
SameQ[#["World"],"FactualContinue"]&
];
globalStopRows82A=Select[
mechanismRows82A,
SameQ[#["World"],"GlobalStop"]&
];
localStopRows82A=Select[
mechanismRows82A,
SameQ[#["World"],"LocalStopHybrid"]&
];

factualQueriedObservations82A=Select[
mechanismObservations82A,
And[
SameQ[#["World"],"FactualContinue"],
SameQ[#["NodeRole"],"QueriedDecision"]
]&
];
globalStopQueriedObservations82A=Select[
mechanismObservations82A,
And[
SameQ[#["World"],"GlobalStop"],
SameQ[#["NodeRole"],"QueriedDecision"]
]&
];
localStopQueriedObservations82A=Select[
mechanismObservations82A,
And[
SameQ[#["World"],"LocalStopHybrid"],
SameQ[#["NodeRole"],"QueriedDecision"]
]&
];

factualQueriedRawHashes82A=DeleteDuplicates@Lookup[
factualQueriedObservations82A,
"RawPairHash"
];
factualQueriedCodes82A=DeleteDuplicates@Lookup[
factualQueriedObservations82A,
"Code"
];

mechanismSummary82A=<|
"NodeRawPairCrossWorldLabelConflictCount"->
SemanticConflictCount82A[
mechanismObservations82A,
"RawPairHash"
],
"NodeRadius2CrossWorldLabelConflictCount"->
SemanticConflictCount82A[
mechanismObservations82A,
"Radius2Hash"
],
"NodeRadius3CrossWorldLabelConflictCount"->
SemanticConflictCount82A[
mechanismObservations82A,
"Radius3Hash"
],
"NodeEncodedCodeCrossWorldLabelConflictCount"->
SemanticConflictCount82A[
mechanismObservations82A,
"CodeHash"
],
"QueriedRawPairSemanticConflictCount"->
SemanticConflictCount82A[
Join[
factualQueriedObservations82A,
globalStopQueriedObservations82A,
localStopQueriedObservations82A
],
"RawPairHash"
],
"QueriedEncodedCodeSemanticConflictCount"->
SemanticConflictCount82A[
Join[
factualQueriedObservations82A,
globalStopQueriedObservations82A,
localStopQueriedObservations82A
],
"CodeHash"
],
"CaseRawPairSetSemanticConflictCount"->
CaseSignatureConflictCount82A[
mechanismRows82A,
"RawPairHashes"
],
"CaseRadius2SetSemanticConflictCount"->
CaseSignatureConflictCount82A[
mechanismRows82A,
"Radius2Hashes"
],
"CaseRadius3SetSemanticConflictCount"->
CaseSignatureConflictCount82A[
mechanismRows82A,
"Radius3Hashes"
],
"CaseEncodedCodeSetSemanticConflictCount"->
CaseSignatureConflictCount82A[
mechanismRows82A,
"CodeHashes"
],
"LocalFactualRawPairOverlapCount"->Length@Intersection[
Union@@Lookup[localStopRows82A,"RawPairHashes"],
Union@@Lookup[factualRows82A,"RawPairHashes"]
],
"LocalGlobalStopRawPairOverlapCount"->Length@Intersection[
Union@@Lookup[localStopRows82A,"RawPairHashes"],
Union@@Lookup[globalStopRows82A,"RawPairHashes"]
],
"LocalStopPolicyCollisionCodes"->Intersection[
Union@@Lookup[localStopRows82A,"Codes"],
frozen75D["Policy"]
],
"LocalStopQueriedRawOverlapWithFactualRows"->Count[
localStopQueriedObservations82A,
observation_/;MemberQ[
factualQueriedRawHashes82A,
observation["RawPairHash"]
]
],
"LocalStopQueriedCodeOverlapWithFactualRows"->Count[
localStopQueriedObservations82A,
observation_/;MemberQ[
factualQueriedCodes82A,
observation["Code"]
]
],
"LocalStopRowsPredictedContinue"->Count[
localStopRows82A,
row_/;SameQ[row["Prediction"],"Continue"]
],
"LocalStopRowsAllCodesPolicyTriggered"->Count[
localStopRows82A,
row_/;TrueQ[row["AllCodesPolicyTriggered"]]
],
"LocalStopQueriedDecisionPolicyHit"->Count[
localStopRows82A,
row_/;TrueQ[row["QueriedDecisionPolicyHit"]]
],
"LocalStopNonQueriedPolicyHit"->Count[
localStopRows82A,
row_/;TrueQ[row["NonQueriedPolicyHit"]]
],
"LocalStopQueriedBranchPolicyHit"->Count[
localStopRows82A,
row_/;TrueQ[row["QueriedBranchPolicyHit"]]
],
"LocalStopOutsideQueriedBranchPolicyHit"->Count[
localStopRows82A,
row_/;TrueQ[row["OutsideQueriedBranchPolicyHit"]]
],
"AllPolicyAggregationWouldContinueRows"->Count[
localStopRows82A,
row_/;TrueQ[row["AllCodesPolicyTriggered"]]
],
"QueryOnlyAggregationWouldContinueRows"->Count[
localStopRows82A,
row_/;TrueQ[row["QueriedDecisionPolicyHit"]]
],
"AnyToAllAggregationFixedRows"->Count[
localStopRows82A,
row_/;!TrueQ[row["AllCodesPolicyTriggered"]]
],
"AnyToQueryOnlyAggregationFixedRows"->Count[
localStopRows82A,
row_/;!TrueQ[row["QueriedDecisionPolicyHit"]]
]
|>;

Column[{
Dataset[worldSummary82A],
Dataset[{mechanismSummary82A}]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfterAudit82A=Hash[
Normal[frozen75D],"SHA256","HexString"
];
coreHashAfterAudit82A=Hash[
{
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
},"SHA256","HexString"
];
coreDefinitionTextHashAfterAudit82A=Hash[
ToString[InputForm[CoreDefinitionBundle82A[]]],
"SHA256",
"HexString"
];
canonicalizerHashAfterAudit82A=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},"SHA256","HexString"
];
stableFrozenArchitectureHashAfterAudit82A=Hash[
{
Normal[frozen75D],
coreDefinitionTextHashAfterAudit82A,
canonicalizerHashAfterAudit82A
},
"SHA256",
"HexString"
];
neutralTopologyHashAfterAudit82A=Hash[
{
DownValues[HierarchicalDiamondIn80],
DownValues[Case80]
},"SHA256","HexString"
];
interventionHashAfterAudit82A=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},"SHA256","HexString"
];
auditProtocolHashAfter82A=Hash[
Normal[auditProtocol82A],"SHA256","HexString"
];

integrityPassed82A=And[
SameQ[modelHashBeforeAudit82A,modelHashAfterAudit82A],
SameQ[modelHashAfterAudit82A,expectedFrozenModelHash79A],
SameQ[coreHashBeforeAudit82A,coreHashAfterAudit82A],
SameQ[
coreDefinitionTextHashBeforeAudit82A,
coreDefinitionTextHashAfterAudit82A
],
SameQ[
coreDefinitionTextHashAfterAudit82A,
expectedMinimalKernelDefinitionTextHash82A
],
SameQ[
canonicalizerHashBeforeAudit82A,
canonicalizerHashAfterAudit82A
],
SameQ[
canonicalizerHashAfterAudit82A,
expectedCanonicalizerHash82A
],
SameQ[
stableFrozenArchitectureHashAfterAudit82A,
expectedStableFrozenArchitectureHash82A
],
SameQ[
neutralTopologyHashBeforeAudit82A,
neutralTopologyHashAfterAudit82A
],
SameQ[
neutralTopologyHashAfterAudit82A,
expectedNeutralTopologyHash82A
],
SameQ[
interventionHashBeforeAudit82A,
interventionHashAfterAudit82A
],
SameQ[
interventionHashAfterAudit82A,
expectedInterventionHash82A
],
SameQ[
auditProtocolHashBefore82A,
auditProtocolHashAfter82A
]
];

auditValidityPassed82A=And[
TrueQ[preflightPassed82A],
TrueQ[integrityPassed82A],
SameQ[Length[mechanismRows82A],24],
SameQ[
Count[
mechanismRows82A,
row_/;TrueQ[row["TerminatedNaturally"]]
],
24
],
SameQ[
Count[
mechanismRows82A,
row_/;TrueQ[row["HitSafetyCap"]]
],
0
],
SameQ[Counts@Lookup[factualRows82A,"ReferenceAction"],<|"Continue"->8|>],
SameQ[Counts@Lookup[globalStopRows82A,"ReferenceAction"],<|"Stop"->8|>],
SameQ[Counts@Lookup[localStopRows82A,"ReferenceAction"],<|"Stop"->8|>]
];

s82FailureFingerprintReproduced82A=And[
SameQ[
Count[factualRows82A,row_/;TrueQ[row["Correct"]]],
8
],
SameQ[
mechanismSummary82A["LocalStopRowsPredictedContinue"],
8
],
SameQ[
Union@@Lookup[factualRows82A,"Codes"],
{{3,3},{4,3}}
],
SameQ[
Union@@Lookup[localStopRows82A,"Codes"],
{{2,2},{3,2}}
]
];

rootCause82A=Which[
!TrueQ[auditValidityPassed82A],
"INVALID_AUDIT",
!TrueQ[s82FailureFingerprintReproduced82A],
"S82_FAILURE_FINGERPRINT_NOT_REPRODUCED",
mechanismSummary82A[
"CaseRawPairSetSemanticConflictCount"
]>0,
"CASE_LEVEL_RAW_STATE_SET_ALIASING",
mechanismSummary82A[
"LocalStopQueriedRawOverlapWithFactualRows"
]===8&&
mechanismSummary82A[
"LocalStopQueriedDecisionPolicyHit"
]===8,
"QUERY_LOCAL_RAW_STATE_ALIASING",
mechanismSummary82A[
"LocalStopQueriedCodeOverlapWithFactualRows"
]===8&&
mechanismSummary82A[
"LocalStopQueriedDecisionPolicyHit"
]===8,
"QUERY_LOCAL_ENCODER_ALIASING",
mechanismSummary82A[
"LocalStopQueriedDecisionPolicyHit"
]===8,
"QUERY_LOCAL_FROZEN_POLICY_COLLISION_AFTER_ENCODING",
mechanismSummary82A[
"LocalStopQueriedBranchPolicyHit"
]>0,
"QUERY_BRANCH_FOOTPRINT_POLICY_COLLISION",
mechanismSummary82A[
"LocalStopOutsideQueriedBranchPolicyHit"
]>0,
"OFF_QUERY_REJECT_TOKEN_LEAK_THROUGH_ANYTRUE",
mechanismSummary82A["LocalStopRowsAllCodesPolicyTriggered"]===8,
"EXHAUSTIVE_FROZEN_POLICY_TOKEN_ALIASING",
True,
"UNRESOLVED_LOCAL_COUNTERFACTUAL_REPRESENTATION_FAILURE"
];

auditPayload82A=<|
"Stage"->"S82A",
"Name"->"BlindCounterfactualFailureMechanismAudit",
"PriorS82BlindResultHash"->expectedS82BlindResultHash82A,
"S82FailureFingerprintReproduced"->
s82FailureFingerprintReproduced82A,
"CasesAudited"->Length[mechanismRows82A],
"RuntimeMinimalKernelHash"->coreHashAfterAudit82A,
"LegacyCheckpointMinimalKernelHash"->
expectedMinimalKernelHash82A,
"MinimalKernelDefinitionTextHash"->
coreDefinitionTextHashAfterAudit82A,
"StableFrozenArchitectureHash"->
stableFrozenArchitectureHashAfterAudit82A,
"NodeRawPairCrossWorldLabelConflictCount"->
mechanismSummary82A[
"NodeRawPairCrossWorldLabelConflictCount"
],
"QueriedRawPairSemanticConflictCount"->
mechanismSummary82A[
"QueriedRawPairSemanticConflictCount"
],
"QueriedEncodedCodeSemanticConflictCount"->
mechanismSummary82A[
"QueriedEncodedCodeSemanticConflictCount"
],
"CaseRawPairSetSemanticConflictCount"->
mechanismSummary82A[
"CaseRawPairSetSemanticConflictCount"
],
"CaseEncodedCodeSetSemanticConflictCount"->
mechanismSummary82A[
"CaseEncodedCodeSetSemanticConflictCount"
],
"LocalFactualRawPairOverlapCount"->
mechanismSummary82A["LocalFactualRawPairOverlapCount"],
"LocalGlobalStopRawPairOverlapCount"->
mechanismSummary82A["LocalGlobalStopRawPairOverlapCount"],
"LocalStopPolicyCollisionCodes"->
mechanismSummary82A["LocalStopPolicyCollisionCodes"],
"LocalStopQueriedRawOverlapWithFactualRows"->
mechanismSummary82A[
"LocalStopQueriedRawOverlapWithFactualRows"
],
"LocalStopQueriedCodeOverlapWithFactualRows"->
mechanismSummary82A[
"LocalStopQueriedCodeOverlapWithFactualRows"
],
"LocalStopRowsPredictedContinue"->
mechanismSummary82A["LocalStopRowsPredictedContinue"],
"LocalStopRowsAllCodesPolicyTriggered"->
mechanismSummary82A["LocalStopRowsAllCodesPolicyTriggered"],
"LocalStopQueriedDecisionPolicyHit"->
mechanismSummary82A["LocalStopQueriedDecisionPolicyHit"],
"LocalStopNonQueriedPolicyHit"->
mechanismSummary82A["LocalStopNonQueriedPolicyHit"],
"LocalStopQueriedBranchPolicyHit"->
mechanismSummary82A[
"LocalStopQueriedBranchPolicyHit"
],
"LocalStopOutsideQueriedBranchPolicyHit"->
mechanismSummary82A[
"LocalStopOutsideQueriedBranchPolicyHit"
],
"AllPolicyAggregationWouldContinueRows"->
mechanismSummary82A[
"AllPolicyAggregationWouldContinueRows"
],
"QueryOnlyAggregationWouldContinueRows"->
mechanismSummary82A[
"QueryOnlyAggregationWouldContinueRows"
],
"AnyToAllAggregationFixedRows"->
mechanismSummary82A["AnyToAllAggregationFixedRows"],
"AnyToQueryOnlyAggregationFixedRows"->
mechanismSummary82A[
"AnyToQueryOnlyAggregationFixedRows"
],
"ModelChanged"->!SameQ[
modelHashBeforeAudit82A,
modelHashAfterAudit82A
],
"CoreChanged"->!SameQ[
coreHashBeforeAudit82A,
coreHashAfterAudit82A
],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBeforeAudit82A,
canonicalizerHashAfterAudit82A
],
"NeutralTopologyChanged"->!SameQ[
neutralTopologyHashBeforeAudit82A,
neutralTopologyHashAfterAudit82A
],
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"CandidateSearchRun"->False,
"AuditValidityPassed"->auditValidityPassed82A,
"RootCause"->rootCause82A
|>;

auditResultHash82A=Hash[
Normal[auditPayload82A],"SHA256","HexString"
];

cert82A=Join[
auditPayload82A,
<|
"AuditOnly"->True,
"S82BlindResultChanged"->False,
"AuditResultHash"->auditResultHash82A,
"SuggestedNextStage"->If[
TrueQ[auditValidityPassed82A],
"S82B_QUERY_ANCHORED_SEMANTIC_REPRESENTATION_DESIGN_NO_BLIND_RETUNING",
"REPAIR_S82A_AUDIT_WITHOUT_CHANGING_FROZEN_MODEL"
]
|>
];

Dataset[{cert82A}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindCounterfactualPairs82=",
    "counterfactualPairs81=",
    "blindRows80=",
    "smallAuditRows79B=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Historical test leaked into S82A: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s82a-intro",
            "metadata": {},
            "source": [
                "# TCCT S82A — Blind-Counterfactual Failure Mechanism Audit\n",
                "\n",
                "这是只读机制审计：锁定 S82 的有效盲测失败，不修改模型、策略、规范化器或干预。仅比较 8 个事实 Continue、8 个全局 Stop、8 个局部混合 Stop。\n",
                "\n",
                "审计逐拒绝节点记录 raw radius-2/radius-3 hash、编码 token、节点角色和 frozen-policy hit，用于区分原始状态歧义、查询局部编码别名、非查询 token 泄漏和最终 OR 聚合问题。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s82a-code-{index}",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": cell.splitlines(keepends=True),
            }
            for index, cell in enumerate(cells, start=1)
        ],
    ],
    "metadata": {
        "kernelspec": {
            "display_name": "Wolfram Language 15",
            "language": "Wolfram Language",
            "name": "wolframlanguage15",
        },
        "language_info": {
            "file_extension": ".wl",
            "mimetype": "application/vnd.wolfram.mathematica",
            "name": "Wolfram Language",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_OUTPUT.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
