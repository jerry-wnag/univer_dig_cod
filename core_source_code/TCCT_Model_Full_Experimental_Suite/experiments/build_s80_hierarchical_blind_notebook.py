import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S79B_SOURCE = ROOT / "TCCT_S79B_PrivateDiamondCanonicalizationRepairAudit.wl"
WL_OUTPUT = ROOT / "TCCT_S80_HierarchicalDiamondIn_BlindCompositionTest.wl"
NB_OUTPUT = ROOT / "TCCT_S80_HierarchicalDiamondIn_BlindCompositionTest.ipynb"
MARKER = "(* S80 CELL *)"


s79b = S79B_SOURCE.read_text(encoding="utf-8")
parts = s79b.split("(* S79B CELL *)")
if len(parts) != 5:
    raise RuntimeError("S79B source no longer has exactly four code cells")

# Definitions only: no S79B test rows or result computations are copied.
core = parts[1].split("expectedMinimalKernelHash79B=", 1)[0].rstrip()
canonicalizer = parts[2].split("Dataset[{<|", 1)[0].rstrip()

cell1 = core + "\n\n" + canonicalizer + r'''

expectedMinimalKernelHash80=
"ec291466f20922dc4b2b879853cd3879c37151fb7e96c34eff45dcb185fe7f34";
expectedCanonicalizerHash80=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedS79BResultHash80=
"0f283d3aa52ec04478ada36f580a6832f09f2d41744bec6ffe3b60dd9e5169ff";

frozenArchitectureHash80=Hash[
{
Normal[frozen75D],
minimalKernelHash79A,
canonicalizerImplementationHash79B
},
"SHA256",
"HexString"
];

freezePreflightPassed80=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelHash79A,
expectedMinimalKernelHash80
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash80
]
];

freezeCertificate80=<|
"Stage"->"S80",
"Name"->"HierarchicalDiamondInBlindCompositionTest",
"ArchitectureFrozenBeforeTopologyDefinition"->True,
"FrozenModelHash"->modelHash79A,
"MinimalKernelHash"->minimalKernelHash79A,
"CanonicalizerImplementationHash"->
canonicalizerImplementationHash79B,
"PriorS79BResultHash"->expectedS79BResultHash80,
"FrozenArchitectureHash"->frozenArchitectureHash80,
"HistoricalRegressionRerun"->False,
"S79BRepairRerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"FreezePreflightPassed"->freezePreflightPassed80
|>;

If[
!TrueQ[freezePreflightPassed80],
Print[Dataset[{freezeCertificate80}]];
Print["S80 aborted before topology definition: frozen architecture hash mismatch."];
Abort[]
];

Dataset[{freezeCertificate80}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[HierarchicalDiamondIn80,Case80];

HierarchicalDiamondIn80[c_List]:=Module[
{
x=c[[1]],a=c[[2]],e,f,mx,next,new,m,incs,removed,
added,parent,s1,s2,g,l1,l2,lg,r1,r2,rg,i,j
},
e=x[[1]];
f=x[[6]];
mx=Max@Flatten[List@@@e];
next=mx+1;
new=e;
Do[
m=f[[i]];
incs=Cases[
new,
DirectedEdge[u_,v_]/;v===m:>{u,v}
];
removed=DirectedEdge@@@incs;
added={};
Do[
parent=incs[[j,1]];
s1=next;
s2=next+1;
g=next+2;
l1=next+3;
l2=next+4;
lg=next+5;
r1=next+6;
r2=next+7;
rg=next+8;
next=next+9;
added=Join[
added,
{
DirectedEdge[parent,l1],
DirectedEdge[parent,l2],
DirectedEdge[l1,lg],
DirectedEdge[l2,lg],
DirectedEdge[lg,s1],
DirectedEdge[parent,r1],
DirectedEdge[parent,r2],
DirectedEdge[r1,rg],
DirectedEdge[r2,rg],
DirectedEdge[rg,s2],
DirectedEdge[s1,g],
DirectedEdge[s2,g],
DirectedEdge[g,m]
}
],
{j,Length[incs]}
];
new=Join[
Complement[new,removed],
added
],
{i,Length[f]}
];
{{
Union[new],
x[[2]],
x[[3]],
x[[4]],
x[[5]],
x[[6]]
},a}
];

Case80[
depth_Integer,
answer_Integer,
target_String
]:=HierarchicalDiamondIn80[
Case59[depth,answer,target]
];

topologySpec80=<|
"Topology"->"HierarchicalDiamondIn",
"TransformationScope"->
"EveryIncomingEdgeOfEachDecisionNode",
"Motif"->
"OuterDiamondWhoseTwoUpperBranchesArePrivateDiamonds",
"CrossParentSharing"->False,
"PrivateDiamondsPerOriginalIncomingEdge"->3,
"HierarchyLevels"->2,
"ParentToDecisionPathLength"->5,
"NewNodesPerOriginalIncomingEdge"->9,
"ReplacementEdgesPerOriginalIncomingEdge"->13,
"EdgeDeltaPerOriginalIncomingEdge"->12,
"ExpectedCanonicalContractionsPerOriginalEdge"->3,
"ReachabilityPreserved"->True,
"OriginalDecisionNodesPreserved"->True,
"PrimitivePrivateDiamondSeenBeforeS80"->True,
"HierarchicalCompositionSeenBeforeS80"->False,
"TopologyUsedBeforeS80"->False
|>;

topologySpecHash80=Hash[
Normal[topologySpec80],
"SHA256",
"HexString"
];

topologyImplementationHash80=Hash[
{
DownValues[HierarchicalDiamondIn80],
DownValues[Case80]
},
"SHA256",
"HexString"
];

blindDepths80={63,127};
blindAnswers80=Range[4];
blindTargets80={"Continue","Stop"};

protocol80=<|
"Stage"->"S80",
"Topology"->"HierarchicalDiamondIn",
"Depths"->blindDepths80,
"Answers"->blindAnswers80,
"Targets"->blindTargets80,
"ExpectedCases"->16,
"SuccessCriterion"->"16/16",
"TopologyNovel"->True,
"DepthsNovel"->False,
"TopologyCompositionBlind"->True,
"PrimitiveRewriteBlind"->False,
"FrozenArchitectureHash"->frozenArchitectureHash80,
"CanonicalizerFrozenBeforeTopologyDefinition"->True,
"NoS80CaseEvaluatedBeforeProtocolHash"->True,
"S80LabelsUsedForSelection"->False,
"S80UsedForRetuning"->False,
"HistoricalRegressionRerun"->False
|>;

protocolHash80=Hash[
Normal[protocol80],
"SHA256",
"HexString"
];

topologyHashBeforeBlind80=topologyImplementationHash80;
protocolHashBeforeBlind80=protocolHash80;
modelHashBeforeBlind80=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];
coreHashBeforeBlind80=minimalKernelHash79A;
canonicalizerHashBeforeBlind80=
canonicalizerImplementationHash79B;

Dataset[{<|
"Stage"->"S80",
"Topology"->"HierarchicalDiamondIn",
"TopologySpecHash"->topologySpecHash80,
"TopologyImplementationHash"->
topologyImplementationHash80,
"ProtocolHash"->protocolHash80,
"Depths"->blindDepths80,
"ExpectedCases"->16,
"CanonicalizerFrozenBeforeTopologyDefinition"->True,
"NoS80CaseEvaluatedBeforeProtocolHash"->True
|>}]
'''.strip() + "\n"

cell3 = r'''
ClearAll[PredictCodes80,PrepareBlindRow80];

PredictCodes80[codes_List]:=If[
AnyTrue[codes,MemberQ[frozen75D["Policy"],#]&],
"Continue",
"Stop"
];

PrepareBlindRow80[
depth_Integer,
answer_Integer,
target_String
]:=Module[
{
originalCase,baseCase,canonicalization,canonicalCase,
expectedContractions,traceSeconds,trace,pairs,encoded,
codes,prediction
},
originalCase=Case80[depth,answer,target];
baseCase=Case59[depth,answer,target];
canonicalization=CanonicalizePrivateDiamonds79B[
originalCase
];
canonicalCase=canonicalization["Case"];
expectedContractions=
3 DecisionIncomingEdgeCount79B[baseCase];
{traceSeconds,trace}=AbsoluteTiming[
RejectTrace78[canonicalCase]
];
pairs=DecisionStatePairsFromRejects78[
canonicalCase,
trace["Rejects"]
];
encoded=First@EncodeRows75[
{<|
"Grammar"->"HierarchicalDiamondIn",
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"StatePairs"->pairs
|>},
frozen75D["Params"],
frozen75D["K"]
];
codes=encoded["Codes"];
prediction=PredictCodes80[codes];
<|
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[
canonicalization["Contractions"],
expectedContractions
],
"ProtectedNodesPreserved"->
canonicalization["ProtectedNodesPreserved"],
"CanonicalCaseExactlyBase"->SameQ[
canonicalCase,
baseCase
],
"OriginalEdgeCount"->Length[originalCase[[1,1]]],
"CanonicalEdgeCount"->Length[canonicalCase[[1,1]]],
"TraceSeconds"->traceSeconds,
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"StatePairCount"->Length[pairs],
"Codes"->codes,
"Prediction"->prediction,
"Correct"->SameQ[prediction,target]
|>
];

blindRows80=Flatten[
Table[
PrepareBlindRow80[depth,answer,target],
{depth,blindDepths80},
{answer,blindAnswers80},
{target,blindTargets80}
],
2
];

blindScore80=Count[
blindRows80,
row_/;TrueQ[row["Correct"]]
];

blindSummary80=<|
"Stage"->"S80",
"Topology"->"HierarchicalDiamondIn",
"Depths"->blindDepths80,
"Cases"->Length[blindRows80],
"Passed"->blindScore80,
"Accuracy"->N[blindScore80/Length[blindRows80]],
"CanonicalCaseExactlyBase"->Count[
blindRows80,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindRows80,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
blindRows80,
row_/;TrueQ[row["ProtectedNodesPreserved"]]
],
"ContractionCounts"->Counts@Lookup[
blindRows80,
"Contractions"
],
"ContinueCodes"->Union@@Lookup[
Select[
blindRows80,
SameQ[#["Target"],"Continue"]&
],
"Codes"
],
"StopCodes"->Union@@Lookup[
Select[
blindRows80,
SameQ[#["Target"],"Stop"]&
],
"Codes"
],
"NonEmptyStatePairs"->Count[
blindRows80,
row_/;row["StatePairCount"]>0
],
"TerminatedNaturally"->Count[
blindRows80,
row_/;TrueQ[row["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
blindRows80,
row_/;TrueQ[row["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[
blindRows80,
"TraceSeconds"
]
|>;

Dataset[{blindSummary80}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfterBlind80=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];
coreHashAfterBlind80=Hash[
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
canonicalizerHashAfterBlind80=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256",
"HexString"
];
topologyHashAfterBlind80=Hash[
{
DownValues[HierarchicalDiamondIn80],
DownValues[Case80]
},
"SHA256",
"HexString"
];
protocolHashAfterBlind80=Hash[
Normal[protocol80],
"SHA256",
"HexString"
];

modelUnchangedDuringBlind80=And[
SameQ[modelHashBeforeBlind80,modelHashAfterBlind80],
SameQ[modelHashAfterBlind80,expectedFrozenModelHash79A]
];

coreUnchangedDuringBlind80=And[
SameQ[coreHashBeforeBlind80,coreHashAfterBlind80],
SameQ[coreHashAfterBlind80,expectedMinimalKernelHash80]
];

canonicalizerUnchangedDuringBlind80=And[
SameQ[
canonicalizerHashBeforeBlind80,
canonicalizerHashAfterBlind80
],
SameQ[
canonicalizerHashAfterBlind80,
expectedCanonicalizerHash80
]
];

topologyUnchangedDuringBlind80=SameQ[
topologyHashBeforeBlind80,
topologyHashAfterBlind80
];

protocolUnchangedDuringBlind80=SameQ[
protocolHashBeforeBlind80,
protocolHashAfterBlind80
];

testValidityPassed80=And[
TrueQ[freezePreflightPassed80],
TrueQ[modelUnchangedDuringBlind80],
TrueQ[coreUnchangedDuringBlind80],
TrueQ[canonicalizerUnchangedDuringBlind80],
TrueQ[topologyUnchangedDuringBlind80],
TrueQ[protocolUnchangedDuringBlind80],
SameQ[Length[blindRows80],16],
SameQ[
Count[
blindRows80,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
16
],
SameQ[
Count[
blindRows80,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
16
],
SameQ[
Count[
blindRows80,
row_/;TrueQ[row["ProtectedNodesPreserved"]]
],
16
],
SameQ[
Count[
blindRows80,
row_/;row["StatePairCount"]>0
],
16
],
SameQ[
Count[
blindRows80,
row_/;TrueQ[row["TerminatedNaturally"]]
],
16
],
SameQ[
Count[
blindRows80,
row_/;TrueQ[row["HitSafetyCap"]]
],
0
]
];

blindPerfect80=And[
TrueQ[testValidityPassed80],
SameQ[blindScore80,16]
];

blindResultPayload80=<|
"Stage"->"S80",
"Name"->"HierarchicalDiamondInBlindCompositionTest",
"FrozenArchitectureHash"->frozenArchitectureHash80,
"PriorS79BResultHash"->expectedS79BResultHash80,
"TopologySpecHash"->topologySpecHash80,
"TopologyImplementationHash"->
topologyHashAfterBlind80,
"ProtocolHash"->protocolHashAfterBlind80,
"Depths"->blindDepths80,
"Cases"->Length[blindRows80],
"Passed"->blindScore80,
"CanonicalCaseExactlyBase"->Count[
blindRows80,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindRows80,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
"ContractionCounts"->Counts@Lookup[
blindRows80,
"Contractions"
],
"ContinueCodes"->blindSummary80["ContinueCodes"],
"StopCodes"->blindSummary80["StopCodes"],
"ModelUnchanged"->modelUnchangedDuringBlind80,
"CoreUnchanged"->coreUnchangedDuringBlind80,
"CanonicalizerUnchanged"->
canonicalizerUnchangedDuringBlind80,
"TopologyUnchanged"->topologyUnchangedDuringBlind80,
"ProtocolUnchanged"->protocolUnchangedDuringBlind80,
"TestValidityPassed"->testValidityPassed80,
"BlindPerfect"->blindPerfect80
|>;

blindResultHash80=Hash[
Normal[blindResultPayload80],
"SHA256",
"HexString"
];

cert80=Join[
blindResultPayload80,
<|
"HistoricalRegressionRerun"->False,
"S79BRepairRerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"InputCanonicalizerUsed"->True,
"OverallArchitectureChangedDuringS80"->False,
"TopologyNovel"->True,
"DepthsNovel"->False,
"PrimitivePrivateDiamondSeen"->True,
"HierarchicalCompositionSeen"->False,
"S80LabelsUsedForSelection"->False,
"S80UsedForRetuning"->False,
"S80IsBlindCompositionalTopologyTest"->True,
"MayClaimBlindPrimitiveCompositionGeneralization"->
blindPerfect80,
"MayClaimArbitraryTopologyGeneralization"->False,
"TotalTraceSeconds"->blindSummary80[
"TotalTraceSeconds"
],
"BlindResultHash"->blindResultHash80,
"Outcome"->Which[
!TrueQ[testValidityPassed80],
"INVALID_TEST",
TrueQ[blindPerfect80],
"BLIND_HIERARCHICAL_COMPOSITION_PASS",
True,
"VALID_BLIND_HIERARCHICAL_COMPOSITION_FAILURE"
],
"SuggestedNextStage"->If[
TrueQ[blindPerfect80],
"S81_ASYMMETRIC_NEUTRAL_REWRITE_BOUNDARY_TEST",
"AUDIT_S80_WITHOUT_RETUNING_FROZEN_ARCHITECTURE"
]
|>
];

Dataset[{KeyTake[
cert80,
{
"Stage",
"Name",
"Depths",
"Cases",
"Passed",
"CanonicalCaseExactlyBase",
"ContractionCountCorrect",
"ContractionCounts",
"ContinueCodes",
"StopCodes",
"ModelUnchanged",
"CoreUnchanged",
"CanonicalizerUnchanged",
"TopologyUnchanged",
"ProtocolUnchanged",
"TestValidityPassed",
"BlindPerfect",
"TopologyNovel",
"DepthsNovel",
"PrimitivePrivateDiamondSeen",
"HierarchicalCompositionSeen",
"S80LabelsUsedForSelection",
"S80UsedForRetuning",
"S80IsBlindCompositionalTopologyTest",
"MayClaimBlindPrimitiveCompositionGeneralization",
"MayClaimArbitraryTopologyGeneralization",
"TotalTraceSeconds",
"TopologySpecHash",
"TopologyImplementationHash",
"ProtocolHash",
"BlindResultHash",
"Outcome",
"SuggestedNextStage"
}
]}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "smallAuditRows79B=",
    "s79RepairRows79B=",
    "s79ReproductionRows79A=",
    "motifAuditRows79A=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Historical test leaked into S80: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s80-intro",
            "metadata": {},
            "source": [
                "# TCCT S80 — HierarchicalDiamondIn Blind Composition Test\n",
                "\n",
                "第一格先按 S79B 已存档哈希冻结模型、动态核心和私有菱形规范化器；第二格才定义新的层级组合 topology 和协议；第三格首次运行 16 个 S80 cases。\n",
                "\n",
                "这是一项 **blind topology-composition test**：局部 private-diamond primitive 已见，但“外层菱形的两条分支各自包含内层菱形”的层级组合未见。深度 63、127 并非新尺度，目的是单独检验组合泛化。它不重跑历史实验、不训练、不搜索、不调策略。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s80-code-{index}",
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
