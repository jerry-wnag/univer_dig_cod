import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S80_SOURCE = ROOT / "TCCT_S80_HierarchicalDiamondIn_BlindCompositionTest.wl"
WL_OUTPUT = ROOT / "TCCT_S81CF_PairedStructuralCounterfactualAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S81CF_PairedStructuralCounterfactualAudit.ipynb"
MARKER = "(* S81CF CELL *)"


s80 = S80_SOURCE.read_text(encoding="utf-8")
parts = s80.split("(* S80 CELL *)")
if len(parts) != 5:
    raise RuntimeError("S80 source no longer has exactly four code cells")

# Definitions only. No S80 case rows or score/result computations are copied.
frozen_architecture = parts[1].split("expectedMinimalKernelHash80=", 1)[0].rstrip()
neutral_topology = parts[2].split("blindDepths80=", 1)[0].rstrip()

cell1 = frozen_architecture + "\n\n" + neutral_topology + r'''

expectedMinimalKernelHash81=
"ec291466f20922dc4b2b879853cd3879c37151fb7e96c34eff45dcb185fe7f34";
expectedCanonicalizerHash81=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedFrozenArchitectureHash81=
"47c0f2de12d2b8d1d0311f7a0fecacba782ff9f0b391b3c86631fdb569a8a3b7";
expectedS80TopologyHash81=
"01af33358afe3fcfe876288b6de7c99a89af22599320fec75911661e240bc121";
expectedS80BlindResultHash81=
"c5a15629ed0631b8217b474b5be6f514bb1b9a8564c96ac4d964b63f376c992f";

frozenArchitectureHash81=Hash[
{
Normal[frozen75D],
minimalKernelHash79A,
canonicalizerImplementationHash79B
},
"SHA256",
"HexString"
];

freezePreflightPassed81=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelHash79A,
expectedMinimalKernelHash81
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash81
],
SameQ[
frozenArchitectureHash81,
expectedFrozenArchitectureHash81
],
SameQ[
topologyImplementationHash80,
expectedS80TopologyHash81
]
];

freezeCertificate81=<|
"Stage"->"S81-CF",
"Name"->"PairedStructuralCounterfactualAudit",
"ArchitectureFrozenBeforeCounterfactualProtocol"->True,
"FrozenModelHash"->modelHash79A,
"MinimalKernelHash"->minimalKernelHash79A,
"CanonicalizerImplementationHash"->
canonicalizerImplementationHash79B,
"FrozenArchitectureHash"->frozenArchitectureHash81,
"NeutralControlTopologyHash"->
topologyImplementationHash80,
"PriorS80BlindResultHash"->
expectedS80BlindResultHash81,
"HistoricalRegressionRerun"->False,
"S80BlindRerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"FreezePreflightPassed"->freezePreflightPassed81
|>;

If[
!TrueQ[freezePreflightPassed81],
Print[Dataset[{freezeCertificate81}]];
Print["S81-CF aborted: frozen S80 architecture or control topology hash mismatch."];
Abort[]
];

Dataset[{freezeCertificate81}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
EdgeSet81,
VertexSet81,
WithEdges81,
EdgePatch81,
ApplyEdgePatch81,
InverseEdgePatch81,
VertexDegreeProfile81,
OppositeAction81
];

EdgeSet81[c_List]:=c[[1,1]];

VertexSet81[c_List]:=Union@Flatten[
List@@@EdgeSet81[c]
];

WithEdges81[c_List,newEdges_List]:=Module[
{x=c[[1]],a=c[[2]]},
{{
Union[newEdges],
x[[2]],
x[[3]],
x[[4]],
x[[5]],
x[[6]]
},a}
];

EdgePatch81[from_List,to_List]:=<|
"Remove"->Complement[
EdgeSet81[from],
EdgeSet81[to]
],
"Add"->Complement[
EdgeSet81[to],
EdgeSet81[from]
]
|>;

ApplyEdgePatch81[c_List,patch_Association]:=Module[
{e,remove,add,valid},
e=EdgeSet81[c];
remove=patch["Remove"];
add=patch["Add"];
valid=And[
And@@Map[MemberQ[e,#]&,remove],
And@@Map[!MemberQ[e,#]&,add],
Intersection[remove,add]==={}
];
If[
!TrueQ[valid],
Return[$Failed]
];
WithEdges81[
c,
Join[Complement[e,remove],add]
]
];

InverseEdgePatch81[patch_Association]:=<|
"Remove"->patch["Add"],
"Add"->patch["Remove"]
|>;

VertexDegreeProfile81[c_List]:=Module[
{e=EdgeSet81[c],vertices},
vertices=VertexSet81[c];
AssociationThread[
vertices,
Map[
Function[node,
{
Count[e,DirectedEdge[_,node]],
Count[e,DirectedEdge[node,_]]
}
],
vertices
]
]
];

OppositeAction81[action_String]:=Switch[
action,
"Continue","Stop",
"Stop","Continue",
_,Missing["UnknownAction"]
];

counterfactualDepths81={31,63};
counterfactualAnswers81=Range[4];

protocol81=<|
"Stage"->"S81-CF",
"Name"->"PairedStructuralCounterfactualAudit",
"Depths"->counterfactualDepths81,
"Answers"->counterfactualAnswers81,
"ExpectedPairs"->8,
"ExpectedWorldsEvaluated"->16,
"FactualAction"->"Continue",
"CounterfactualAction"->"Stop",
"Intervention"->
"DegreePreservingGlobalSemanticEdgePermutation",
"ExpectedRemovedEdgesPerPair"->12,
"ExpectedAddedEdgesPerPair"->12,
"ExpectedEdgeEditDistancePerPair"->24,
"SameSeedWithinPair"->True,
"SameVerticesWithinPair"->True,
"SamePerVertexDegreeProfileWithinPair"->True,
"InverseInterventionMustRecoverFactual"->True,
"NeutralControl"->
"S80HierarchicalDiamondThenFrozenCanonicalization",
"NeutralControlMustRecoverEachWorld"->True,
"ArchitectureFrozenBeforeProtocol"->True,
"NoPairEvaluatedBeforeProtocolHash"->True,
"HistoricalRegressionRerun"->False,
"S80BlindRerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"S81IsBlindCounterfactualTest"->False
|>;

protocolHash81=Hash[
Normal[protocol81],
"SHA256",
"HexString"
];

modelHashBeforeAudit81=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];
coreHashBeforeAudit81=minimalKernelHash79A;
canonicalizerHashBeforeAudit81=
canonicalizerImplementationHash79B;
neutralTopologyHashBeforeAudit81=
topologyImplementationHash80;
protocolHashBeforeAudit81=protocolHash81;

Dataset[{<|
"Stage"->"S81-CF",
"ProtocolHash"->protocolHash81,
"Depths"->counterfactualDepths81,
"ExpectedPairs"->8,
"ExpectedWorldsEvaluated"->16,
"Intervention"->
"DegreePreservingGlobalSemanticEdgePermutation",
"ExpectedEdgeEditDistancePerPair"->24,
"NoPairEvaluatedBeforeProtocolHash"->True,
"S81IsBlindCounterfactualTest"->False
|>}]
'''.strip() + "\n"

cell3 = r'''
ClearAll[
PredictCodes81,
EvaluateArchitecture81,
PrepareCounterfactualPair81
];

PredictCodes81[codes_List]:=If[
AnyTrue[codes,MemberQ[frozen75D["Policy"],#]&],
"Continue",
"Stop"
];

EvaluateArchitecture81[
c_List,
depth_Integer,
answer_Integer,
worldName_String
]:=Module[
{
canonicalization,canonicalCase,traceSeconds,trace,
pairs,encoded,codes,prediction
},
canonicalization=CanonicalizePrivateDiamonds79B[c];
canonicalCase=canonicalization["Case"];
{traceSeconds,trace}=AbsoluteTiming[
RejectTrace78[canonicalCase]
];
pairs=DecisionStatePairsFromRejects78[
canonicalCase,
trace["Rejects"]
];
encoded=First@EncodeRows75[
{<|
"Grammar"->"S81CounterfactualWorld",
"Depth"->depth,
"Answer"->answer,
"Target"->"Unlabeled",
"StatePairs"->pairs
|>},
frozen75D["Params"],
frozen75D["K"]
];
codes=encoded["Codes"];
prediction=PredictCodes81[codes];
<|
"World"->worldName,
"CanonicalizationContractions"->
canonicalization["Contractions"],
"CanonicalCase"->canonicalCase,
"TraceSeconds"->traceSeconds,
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"StatePairCount"->Length[pairs],
"Codes"->codes,
"Prediction"->prediction
|>
];

PrepareCounterfactualPair81[
depth_Integer,
answer_Integer
]:=Module[
{
factualCase,counterfactualTemplate,patch,
counterfactualCase,inversePatch,recoveredFactual,
neutralFactual,neutralCounterfactual,
factualEvaluation,counterfactualEvaluation,
factualPrediction,counterfactualPrediction,
pairCorrect,flipCorrect
},
factualCase=Case59[depth,answer,"Continue"];
counterfactualTemplate=Case59[
depth,answer,"Stop"
];
patch=EdgePatch81[
factualCase,
counterfactualTemplate
];
counterfactualCase=ApplyEdgePatch81[
factualCase,
patch
];
inversePatch=InverseEdgePatch81[patch];
recoveredFactual=ApplyEdgePatch81[
counterfactualCase,
inversePatch
];
neutralFactual=CanonicalCase79B[
HierarchicalDiamondIn80[factualCase]
];
neutralCounterfactual=CanonicalCase79B[
HierarchicalDiamondIn80[counterfactualCase]
];
factualEvaluation=EvaluateArchitecture81[
factualCase,
depth,
answer,
"FactualContinue"
];
counterfactualEvaluation=EvaluateArchitecture81[
counterfactualCase,
depth,
answer,
"CounterfactualStop"
];
factualPrediction=factualEvaluation["Prediction"];
counterfactualPrediction=
counterfactualEvaluation["Prediction"];
pairCorrect=And[
SameQ[factualPrediction,"Continue"],
SameQ[counterfactualPrediction,"Stop"]
];
flipCorrect=And[
SameQ[factualPrediction,"Continue"],
SameQ[
counterfactualPrediction,
OppositeAction81[factualPrediction]
]
];
<|
"Depth"->depth,
"Answer"->answer,
"FactualTarget"->"Continue",
"CounterfactualTarget"->"Stop",
"RemovedEdges"->Length[patch["Remove"]],
"AddedEdges"->Length[patch["Add"]],
"EdgeEditDistance"->Total[
Length/@Lookup[patch,{"Remove","Add"}]
],
"CounterfactualCaseExactlyTemplate"->SameQ[
counterfactualCase,
counterfactualTemplate
],
"SameVertices"->SameQ[
VertexSet81[factualCase],
VertexSet81[counterfactualCase]
],
"SameEdgeCount"->SameQ[
Length[EdgeSet81[factualCase]],
Length[EdgeSet81[counterfactualCase]]
],
"SamePerVertexDegreeProfile"->SameQ[
VertexDegreeProfile81[factualCase],
VertexDegreeProfile81[counterfactualCase]
],
"InverseInterventionRecoversFactual"->SameQ[
recoveredFactual,
factualCase
],
"NeutralFactualRecoversExact"->SameQ[
neutralFactual,
factualCase
],
"NeutralCounterfactualRecoversExact"->SameQ[
neutralCounterfactual,
counterfactualCase
],
"FactualCodes"->factualEvaluation["Codes"],
"CounterfactualCodes"->
counterfactualEvaluation["Codes"],
"FactualPrediction"->factualPrediction,
"CounterfactualPrediction"->
counterfactualPrediction,
"FactualCorrect"->SameQ[
factualPrediction,
"Continue"
],
"CounterfactualCorrect"->SameQ[
counterfactualPrediction,
"Stop"
],
"PairCorrect"->pairCorrect,
"FlipDirectionCorrect"->flipCorrect,
"ReverseDirectionCorrect"->And[
SameQ[counterfactualPrediction,"Stop"],
SameQ[
factualPrediction,
OppositeAction81[counterfactualPrediction]
]
],
"FactualTerminatedNaturally"->
factualEvaluation["TerminatedNaturally"],
"CounterfactualTerminatedNaturally"->
counterfactualEvaluation["TerminatedNaturally"],
"FactualHitSafetyCap"->
factualEvaluation["HitSafetyCap"],
"CounterfactualHitSafetyCap"->
counterfactualEvaluation["HitSafetyCap"],
"FactualStatePairCount"->
factualEvaluation["StatePairCount"],
"CounterfactualStatePairCount"->
counterfactualEvaluation["StatePairCount"],
"TotalTraceSeconds"->Total[{
factualEvaluation["TraceSeconds"],
counterfactualEvaluation["TraceSeconds"]
}]
|>
];

counterfactualPairs81=Flatten[
Table[
PrepareCounterfactualPair81[depth,answer],
{depth,counterfactualDepths81},
{answer,counterfactualAnswers81}
],
1
];

counterfactualSummary81=<|
"Stage"->"S81-CF",
"Pairs"->Length[counterfactualPairs81],
"WorldsEvaluated"->2 Length[counterfactualPairs81],
"FactualCorrect"->Count[
counterfactualPairs81,
row_/;TrueQ[row["FactualCorrect"]]
],
"CounterfactualCorrect"->Count[
counterfactualPairs81,
row_/;TrueQ[row["CounterfactualCorrect"]]
],
"PairCorrect"->Count[
counterfactualPairs81,
row_/;TrueQ[row["PairCorrect"]]
],
"FlipDirectionCorrect"->Count[
counterfactualPairs81,
row_/;TrueQ[row["FlipDirectionCorrect"]]
],
"ReverseDirectionCorrect"->Count[
counterfactualPairs81,
row_/;TrueQ[row["ReverseDirectionCorrect"]]
],
"CounterfactualCaseExactlyTemplate"->Count[
counterfactualPairs81,
row_/;TrueQ[row["CounterfactualCaseExactlyTemplate"]]
],
"SameVertices"->Count[
counterfactualPairs81,
row_/;TrueQ[row["SameVertices"]]
],
"SameEdgeCount"->Count[
counterfactualPairs81,
row_/;TrueQ[row["SameEdgeCount"]]
],
"SamePerVertexDegreeProfile"->Count[
counterfactualPairs81,
row_/;TrueQ[row["SamePerVertexDegreeProfile"]]
],
"InverseInterventionRecovery"->Count[
counterfactualPairs81,
row_/;TrueQ[row["InverseInterventionRecoversFactual"]]
],
"NeutralFactualInvariance"->Count[
counterfactualPairs81,
row_/;TrueQ[row["NeutralFactualRecoversExact"]]
],
"NeutralCounterfactualInvariance"->Count[
counterfactualPairs81,
row_/;TrueQ[row["NeutralCounterfactualRecoversExact"]]
],
"RemovedEdgeCounts"->Counts@Lookup[
counterfactualPairs81,
"RemovedEdges"
],
"AddedEdgeCounts"->Counts@Lookup[
counterfactualPairs81,
"AddedEdges"
],
"EdgeEditDistances"->Counts@Lookup[
counterfactualPairs81,
"EdgeEditDistance"
],
"FactualCodeSet"->Union@@Lookup[
counterfactualPairs81,
"FactualCodes"
],
"CounterfactualCodeSet"->Union@@Lookup[
counterfactualPairs81,
"CounterfactualCodes"
],
"WorldsTerminatedNaturally"->Plus[
Count[
Lookup[counterfactualPairs81,"FactualTerminatedNaturally"],
True
],
Count[
Lookup[counterfactualPairs81,"CounterfactualTerminatedNaturally"],
True
]
],
"WorldsHitSafetyCap"->Plus[
Count[
Lookup[counterfactualPairs81,"FactualHitSafetyCap"],
True
],
Count[
Lookup[counterfactualPairs81,"CounterfactualHitSafetyCap"],
True
]
],
"TotalTraceSeconds"->Total@Lookup[
counterfactualPairs81,
"TotalTraceSeconds"
]
|>;

Dataset[{counterfactualSummary81}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfterAudit81=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];
coreHashAfterAudit81=Hash[
{
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
},
"SHA256",
"HexString"
];
canonicalizerHashAfterAudit81=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256",
"HexString"
];
neutralTopologyHashAfterAudit81=Hash[
{
DownValues[HierarchicalDiamondIn80],
DownValues[Case80]
},
"SHA256",
"HexString"
];
protocolHashAfterAudit81=Hash[
Normal[protocol81],
"SHA256",
"HexString"
];

modelUnchanged81=And[
SameQ[modelHashBeforeAudit81,modelHashAfterAudit81],
SameQ[modelHashAfterAudit81,expectedFrozenModelHash79A]
];
coreUnchanged81=And[
SameQ[coreHashBeforeAudit81,coreHashAfterAudit81],
SameQ[coreHashAfterAudit81,expectedMinimalKernelHash81]
];
canonicalizerUnchanged81=And[
SameQ[
canonicalizerHashBeforeAudit81,
canonicalizerHashAfterAudit81
],
SameQ[
canonicalizerHashAfterAudit81,
expectedCanonicalizerHash81
]
];
neutralTopologyUnchanged81=And[
SameQ[
neutralTopologyHashBeforeAudit81,
neutralTopologyHashAfterAudit81
],
SameQ[
neutralTopologyHashAfterAudit81,
expectedS80TopologyHash81
]
];
protocolUnchanged81=SameQ[
protocolHashBeforeAudit81,
protocolHashAfterAudit81
];

auditValidityPassed81=And[
TrueQ[freezePreflightPassed81],
TrueQ[modelUnchanged81],
TrueQ[coreUnchanged81],
TrueQ[canonicalizerUnchanged81],
TrueQ[neutralTopologyUnchanged81],
TrueQ[protocolUnchanged81],
SameQ[Length[counterfactualPairs81],8],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["CounterfactualCaseExactlyTemplate"]]
],
8
],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["SameVertices"]]
],
8
],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["SameEdgeCount"]]
],
8
],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["SamePerVertexDegreeProfile"]]
],
8
],
SameQ[Counts@Lookup[counterfactualPairs81,"RemovedEdges"],<|12->8|>],
SameQ[Counts@Lookup[counterfactualPairs81,"AddedEdges"],<|12->8|>],
SameQ[Counts@Lookup[counterfactualPairs81,"EdgeEditDistance"],<|24->8|>],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["InverseInterventionRecoversFactual"]]
],
8
],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["NeutralFactualRecoversExact"]]
],
8
],
SameQ[
Count[
counterfactualPairs81,
row_/;TrueQ[row["NeutralCounterfactualRecoversExact"]]
],
8
],
SameQ[
counterfactualSummary81["WorldsTerminatedNaturally"],
16
],
SameQ[counterfactualSummary81["WorldsHitSafetyCap"],0]
];

knownInterventionAuditPassed81=And[
TrueQ[auditValidityPassed81],
SameQ[counterfactualSummary81["FactualCorrect"],8],
SameQ[counterfactualSummary81["CounterfactualCorrect"],8],
SameQ[counterfactualSummary81["PairCorrect"],8],
SameQ[counterfactualSummary81["FlipDirectionCorrect"],8],
SameQ[counterfactualSummary81["ReverseDirectionCorrect"],8]
];

resultPayload81=<|
"Stage"->"S81-CF",
"Name"->"PairedStructuralCounterfactualAudit",
"FrozenArchitectureHash"->frozenArchitectureHash81,
"PriorS80BlindResultHash"->expectedS80BlindResultHash81,
"ProtocolHash"->protocolHashAfterAudit81,
"Pairs"->Length[counterfactualPairs81],
"WorldsEvaluated"->2 Length[counterfactualPairs81],
"FactualCorrect"->counterfactualSummary81["FactualCorrect"],
"CounterfactualCorrect"->
counterfactualSummary81["CounterfactualCorrect"],
"PairCorrect"->counterfactualSummary81["PairCorrect"],
"FlipDirectionCorrect"->
counterfactualSummary81["FlipDirectionCorrect"],
"ReverseDirectionCorrect"->
counterfactualSummary81["ReverseDirectionCorrect"],
"SameVertices"->counterfactualSummary81["SameVertices"],
"SameEdgeCount"->counterfactualSummary81["SameEdgeCount"],
"SamePerVertexDegreeProfile"->
counterfactualSummary81["SamePerVertexDegreeProfile"],
"InverseInterventionRecovery"->
counterfactualSummary81["InverseInterventionRecovery"],
"NeutralFactualInvariance"->
counterfactualSummary81["NeutralFactualInvariance"],
"NeutralCounterfactualInvariance"->
counterfactualSummary81["NeutralCounterfactualInvariance"],
"RemovedEdgeCounts"->
counterfactualSummary81["RemovedEdgeCounts"],
"AddedEdgeCounts"->counterfactualSummary81["AddedEdgeCounts"],
"EdgeEditDistances"->
counterfactualSummary81["EdgeEditDistances"],
"FactualCodeSet"->counterfactualSummary81["FactualCodeSet"],
"CounterfactualCodeSet"->
counterfactualSummary81["CounterfactualCodeSet"],
"ModelUnchanged"->modelUnchanged81,
"CoreUnchanged"->coreUnchanged81,
"CanonicalizerUnchanged"->canonicalizerUnchanged81,
"NeutralTopologyUnchanged"->neutralTopologyUnchanged81,
"ProtocolUnchanged"->protocolUnchanged81,
"AuditValidityPassed"->auditValidityPassed81,
"KnownInterventionAuditPassed"->
knownInterventionAuditPassed81
|>;

resultHash81=Hash[
Normal[resultPayload81],
"SHA256",
"HexString"
];

cert81=Join[
resultPayload81,
<|
"CounterfactualMethod"->
"ExternalGraphInterventionAndFrozenForwardSimulation",
"HistoricalRegressionRerun"->False,
"S80BlindRerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"OverallArchitectureChangedDuringS81"->False,
"S81IsBlindCounterfactualTest"->False,
"MayClaimCounterfactualProtocolOperational"->
knownInterventionAuditPassed81,
"MayClaimKnownInterventionPairedCounterfactualReasoning"->
knownInterventionAuditPassed81,
"MayClaimBlindCounterfactualGeneralization"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->
counterfactualSummary81["TotalTraceSeconds"],
"ResultHash"->resultHash81,
"Outcome"->Which[
!TrueQ[auditValidityPassed81],
"INVALID_COUNTERFACTUAL_AUDIT",
TrueQ[knownInterventionAuditPassed81],
"PAIRED_STRUCTURAL_COUNTERFACTUAL_AUDIT_PASS",
True,
"VALID_COUNTERFACTUAL_AUDIT_FAILURE"
],
"SuggestedNextStage"->If[
TrueQ[knownInterventionAuditPassed81],
"S82_BLIND_LOCAL_MEDIATOR_INTERVENTION_TEST",
"DIAGNOSE_S81_WITHOUT_RETUNING_FROZEN_ARCHITECTURE"
]
|>
];

Dataset[{KeyTake[
cert81,
{
"Stage",
"Name",
"Pairs",
"WorldsEvaluated",
"FactualCorrect",
"CounterfactualCorrect",
"PairCorrect",
"FlipDirectionCorrect",
"ReverseDirectionCorrect",
"SameVertices",
"SameEdgeCount",
"SamePerVertexDegreeProfile",
"InverseInterventionRecovery",
"NeutralFactualInvariance",
"NeutralCounterfactualInvariance",
"RemovedEdgeCounts",
"AddedEdgeCounts",
"EdgeEditDistances",
"FactualCodeSet",
"CounterfactualCodeSet",
"ModelUnchanged",
"CoreUnchanged",
"CanonicalizerUnchanged",
"NeutralTopologyUnchanged",
"ProtocolUnchanged",
"AuditValidityPassed",
"KnownInterventionAuditPassed",
"CounterfactualMethod",
"S81IsBlindCounterfactualTest",
"MayClaimCounterfactualProtocolOperational",
"MayClaimKnownInterventionPairedCounterfactualReasoning",
"MayClaimBlindCounterfactualGeneralization",
"MayClaimCausalDiscovery",
"TotalTraceSeconds",
"ResultHash",
"Outcome",
"SuggestedNextStage"
}
]}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindRows80=",
    "smallAuditRows79B=",
    "s79RepairRows79B=",
    "s79ReproductionRows79A=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Historical test leaked into S81-CF: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s81cf-intro",
            "metadata": {},
            "source": [
                "# TCCT S81-CF — Paired Structural Counterfactual Audit\n",
                "\n",
                "这是反事实协议审计，不是 blind counterfactual generalization test。第一格冻结 S80 架构；第二格在任何 pair 运行前锁定干预协议；第三格只评估 8 个孪生 pair（16 个世界）。\n",
                "\n",
                "每对世界拥有相同 seed、节点、边数和逐节点度数。显式边干预把事实 Continue 世界变成 Stop 世界；逆干预必须精确恢复事实世界。S80 层级菱形作为中性干预，规范化后必须精确恢复各自世界。模型输入中不包含事实或反事实标签。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s81cf-code-{index}",
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
