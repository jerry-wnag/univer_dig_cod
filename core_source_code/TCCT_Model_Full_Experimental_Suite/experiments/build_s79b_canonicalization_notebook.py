import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S79A_SOURCE = ROOT / "TCCT_S79A_MinimalBlindFailureMechanismAudit.wl"
WL_OUTPUT = ROOT / "TCCT_S79B_PrivateDiamondCanonicalizationRepairAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S79B_PrivateDiamondCanonicalizationRepairAudit.ipynb"
MARKER = "(* S79B CELL *)"


s79a = S79A_SOURCE.read_text(encoding="utf-8")
s79a_parts = s79a.split("(* S79A CELL *)")
if len(s79a_parts) != 5:
    raise RuntimeError("S79A source no longer has exactly four code cells")

# Reuse definitions only. Nothing after preflightPass79A is copied, so none of
# the S79A reproduction or motif tests can execute in S79B.
core = s79a_parts[1].split("preflightPass79A=", 1)[0].rstrip()

cell1 = core + r'''

expectedMinimalKernelHash79B=
"ec291466f20922dc4b2b879853cd3879c37151fb7e96c34eff45dcb185fe7f34";

minimalKernelHash79B=minimalKernelHash79A;

preflightPass79B=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[topologySpecHash79,expectedTopologySpecHash79A],
SameQ[
topologyImplementationHash79,
expectedTopologyImplementationHash79A
],
SameQ[
minimalKernelHash79B,
expectedMinimalKernelHash79B
]
];

preflight79B=<|
"Stage"->"S79B",
"Name"->"PrivateDiamondCanonicalizationRepairAudit",
"StandaloneMinimalKernel"->True,
"HistoricalRegressionRerun"->False,
"UncanonicalizedS79Rerun"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"DesignedAfterS79Exposure"->True,
"S79BIsBlindTest"->False,
"ExpectedS79BlindResultHash"->
expectedS79BlindResultHash79A,
"FrozenModelHash"->modelHash79A,
"TopologySpecHash"->topologySpecHash79,
"TopologyImplementationHash"->
topologyImplementationHash79,
"MinimalKernelHash"->minimalKernelHash79B,
"PreflightPassed"->preflightPass79B
|>;

If[
!TrueQ[preflightPass79B],
Print[Dataset[{preflight79B}]];
Print["S79B aborted: frozen minimal core does not match S79A."];
Abort[]
];

Dataset[{preflight79B}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
FindPrivateDiamond79B,
CanonicalizePrivateDiamonds79B,
CanonicalCase79B,
CaseByTopology79B,
DecisionIncomingEdgeCount79B,
ExpectedContractions79B
];

FindPrivateDiamond79B[e_List,protected_List]:=Module[
{
vertices,parents,children,harvest,ins,outs,s1,s2,
p1,p2,g
},
vertices=Union@Flatten[List@@@e];
parents=GroupBy[
Cases[e,DirectedEdge[u_,v_]:>{v,u}],
First->Last
];
children=GroupBy[
Cases[e,DirectedEdge[u_,v_]:>{u,v}],
First->Last
];
harvest=Reap[
Do[
If[
!MemberQ[protected,g],
ins=Sort@Lookup[parents,g,{}];
outs=Sort@Lookup[children,g,{}];
If[
Length[ins]===2&&Length[outs]===1,
{s1,s2}=ins;
p1=Sort@Lookup[parents,s1,{}];
p2=Sort@Lookup[parents,s2,{}];
If[
And[
Intersection[protected,{s1,s2,g}]==={},
Length[p1]===1,
SameQ[p1,p2],
SameQ[Sort@Lookup[children,s1,{}],{g}],
SameQ[Sort@Lookup[children,s2,{}],{g}],
DuplicateFreeQ[{First[p1],s1,s2,g,First[outs]}]
],
Sow[{First[p1],s1,s2,g,First[outs]}]
]
]
],
{g,vertices}
]
][[2]];
If[
harvest==={},
Missing["NotFound"],
First@Sort@First[harvest]
]
];

CanonicalizePrivateDiamonds79B[c_List]:=Module[
{
x=c[[1]],a=c[[2]],e,protected,candidate,
parent,s1,s2,g,target,removed,count=0,log={}
},
e=Union[x[[1]]];
protected=Union[
x[[2]],
{x[[3]]},
x[[4]],
x[[5]],
x[[6]]
];
While[
True,
candidate=FindPrivateDiamond79B[e,protected];
If[MissingQ[candidate],Break[]];
{parent,s1,s2,g,target}=candidate;
removed={s1,s2,g};
e=Union[
Select[
e,
Function[edge,
And[
!MemberQ[removed,edge[[1]]],
!MemberQ[removed,edge[[2]]]
]
]
],
{DirectedEdge[parent,target]}
];
count++;
AppendTo[log,candidate]
];
<|
"Case"->{{
e,
x[[2]],
x[[3]],
x[[4]],
x[[5]],
x[[6]]
},a},
"Contractions"->count,
"ContractionLog"->log,
"ProtectedNodesPreserved"->And@@Map[
MemberQ[Union@Flatten[List@@@e],#]&,
protected
]
|>
];

CanonicalCase79B[c_List]:=
CanonicalizePrivateDiamonds79B[c]["Case"];

CaseByTopology79B[
topology_String,
depth_Integer,
answer_Integer,
target_String
]:=Switch[
topology,
"Base",
Case59[depth,answer,target],
"DiamondIn",
DiamondIn72[Case59[depth,answer,target]],
"DoubleDiamondIn",
DoubleDiamondIn79[Case59[depth,answer,target]],
_,
$Failed
];

DecisionIncomingEdgeCount79B[c_List]:=Module[
{e=c[[1,1]],f=c[[1,6]]},
Total[Count[e,DirectedEdge[_,#]]&/@f]
];

ExpectedContractions79B[
topology_String,
baseCase_List
]:=Switch[
topology,
"Base",
0,
"DiamondIn",
DecisionIncomingEdgeCount79B[baseCase],
"DoubleDiamondIn",
2 DecisionIncomingEdgeCount79B[baseCase],
_,
Missing["UnknownTopology"]
];

canonicalizerImplementationHash79B=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256",
"HexString"
];

Dataset[{<|
"Stage"->"S79B",
"Canonicalizer"->"ProtectedPrivateDiamondQuotient",
"CanonicalizerImplementationHash"->
canonicalizerImplementationHash79B,
"FrozenCoreChanged"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False
|>}]
'''.strip() + "\n"

cell3 = r'''
ClearAll[
PredictCodes79B,
PrepareCanonicalAuditRow79B,
CanonicalSummary79B
];

PredictCodes79B[codes_List]:=If[
AnyTrue[codes,MemberQ[frozen75D["Policy"],#]&],
"Continue",
"Stop"
];

PrepareCanonicalAuditRow79B[
topology_String,
depth_Integer,
answer_Integer,
target_String
]:=Module[
{
originalCase,baseCase,canonicalization,canonicalCase,
expectedContractions,traceSeconds,trace,pairs,encoded,
codes,prediction
},
originalCase=CaseByTopology79B[
topology,depth,answer,target
];
baseCase=Case59[depth,answer,target];
canonicalization=CanonicalizePrivateDiamonds79B[
originalCase
];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions79B[
topology,
baseCase
];
{traceSeconds,trace}=AbsoluteTiming[
RejectTrace78[canonicalCase]
];
pairs=DecisionStatePairsFromRejects78[
canonicalCase,
trace["Rejects"]
];
encoded=First@EncodeRows75[
{<|
"Grammar"->topology,
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"StatePairs"->pairs
|>},
frozen75D["Params"],
frozen75D["K"]
];
codes=encoded["Codes"];
prediction=PredictCodes79B[codes];
<|
"Topology"->topology,
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

smallAuditRows79B=Flatten[
Table[
PrepareCanonicalAuditRow79B[
topology,
depth,
answer,
target
],
{topology,{"Base","DiamondIn","DoubleDiamondIn"}},
{depth,{5,31}},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
3
];

s79RepairRows79B=Flatten[
Table[
PrepareCanonicalAuditRow79B[
"DoubleDiamondIn",
depth,
answer,
target
],
{depth,{191,255}},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
2
];

CanonicalSummary79B[
rows_List,
topology_String,
depth_Integer
]:=Module[
{selected,continueRows,stopRows,passed},
selected=Select[
rows,
And[
SameQ[#["Topology"],topology],
SameQ[#["Depth"],depth]
]&
];
continueRows=Select[
selected,
SameQ[#["Target"],"Continue"]&
];
stopRows=Select[
selected,
SameQ[#["Target"],"Stop"]&
];
passed=Count[selected,row_/;TrueQ[row["Correct"]]];
<|
"Topology"->topology,
"Depth"->depth,
"Cases"->Length[selected],
"CanonicalCaseExactlyBase"->Count[
selected,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
selected,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
selected,
row_/;TrueQ[row["ProtectedNodesPreserved"]]
],
"ContractionCounts"->Counts@Lookup[
selected,
"Contractions"
],
"ContinueCodes"->Union@@Lookup[
continueRows,
"Codes"
],
"StopCodes"->Union@@Lookup[
stopRows,
"Codes"
],
"Passed"->passed,
"Accuracy"->N[passed/Length[selected]],
"TerminatedNaturally"->Count[
selected,
row_/;TrueQ[row["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
selected,
row_/;TrueQ[row["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[
selected,
"TraceSeconds"
]
|>
];

smallSummary79B=Flatten[
Table[
CanonicalSummary79B[
smallAuditRows79B,
topology,
depth
],
{topology,{"Base","DiamondIn","DoubleDiamondIn"}},
{depth,{5,31}}
],
1
];

s79RepairSummary79B=Map[
CanonicalSummary79B[
s79RepairRows79B,
"DoubleDiamondIn",
#
]&,
{191,255}
];

Dataset[Join[smallSummary79B,s79RepairSummary79B]]
'''.strip() + "\n"

cell4 = r'''
smallAuditPassed79B=And[
SameQ[Length[smallAuditRows79B],48],
SameQ[
Count[
smallAuditRows79B,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
48
],
SameQ[
Count[
smallAuditRows79B,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
48
],
SameQ[
Count[
smallAuditRows79B,
row_/;TrueQ[row["Correct"]]
],
48
],
SameQ[
Count[
smallAuditRows79B,
row_/;TrueQ[row["TerminatedNaturally"]]
],
48
],
SameQ[
Count[
smallAuditRows79B,
row_/;TrueQ[row["HitSafetyCap"]]
],
0
]
];

s79RepairPassed79B=And[
SameQ[Length[s79RepairRows79B],16],
SameQ[
Count[
s79RepairRows79B,
row_/;TrueQ[row["CanonicalCaseExactlyBase"]]
],
16
],
SameQ[
Count[
s79RepairRows79B,
row_/;TrueQ[row["ContractionCountCorrect"]]
],
16
],
SameQ[
Count[
s79RepairRows79B,
row_/;TrueQ[row["Correct"]]
],
16
],
SameQ[
Count[
s79RepairRows79B,
row_/;TrueQ[row["TerminatedNaturally"]]
],
16
],
SameQ[
Count[
s79RepairRows79B,
row_/;TrueQ[row["HitSafetyCap"]]
],
0
]
];

modelHashAfter79B=Hash[
Normal[frozen75D],
"SHA256",
"HexString"
];

modelUnchanged79B=SameQ[
modelHashAfter79B,
expectedFrozenModelHash79A
];

auditValidityPassed79B=And[
TrueQ[preflightPass79B],
TrueQ[smallAuditPassed79B],
TrueQ[modelUnchanged79B]
];

repairMechanismPassed79B=And[
TrueQ[auditValidityPassed79B],
TrueQ[s79RepairPassed79B]
];

resultPayload79B=<|
"Stage"->"S79B",
"Name"->"PrivateDiamondCanonicalizationRepairAudit",
"PriorS79BlindResultHash"->
expectedS79BlindResultHash79A,
"PriorS79FailureRerun"->False,
"HistoricalRegressionRerun"->False,
"SmallAuditCases"->Length[smallAuditRows79B],
"SmallAuditPassed"->Count[
smallAuditRows79B,
row_/;TrueQ[row["Correct"]]
],
"S79RepairCases"->Length[s79RepairRows79B],
"S79RepairPassed"->Count[
s79RepairRows79B,
row_/;TrueQ[row["Correct"]]
],
"AllCanonicalCasesExactlyBase"->And[
And@@Lookup[
smallAuditRows79B,
"CanonicalCaseExactlyBase"
],
And@@Lookup[
s79RepairRows79B,
"CanonicalCaseExactlyBase"
]
],
"AllContractionCountsCorrect"->And[
And@@Lookup[
smallAuditRows79B,
"ContractionCountCorrect"
],
And@@Lookup[
s79RepairRows79B,
"ContractionCountCorrect"
]
],
"CanonicalizerImplementationHash"->
canonicalizerImplementationHash79B,
"FrozenModelHash"->modelHashAfter79B,
"FrozenModelChanged"->!TrueQ[modelUnchanged79B],
"FrozenCoreChanged"->False,
"PolicyEditApplied"->False,
"RetuningApplied"->False,
"CandidateSearchRun"->False,
"InputCanonicalizerAdded"->True,
"OverallArchitectureChanged"->True,
"DesignedAfterS79Exposure"->True,
"S79LabelsUsedByCanonicalizer"->False,
"S79LabelsUsedForPolicyOrParameterSelection"->False,
"S79BIsBlindTest"->False,
"MayClaimRepairMechanism"->
repairMechanismPassed79B,
"MayClaimNewBlindGeneralization"->False,
"AuditValidityPassed"->auditValidityPassed79B,
"RepairMechanismPassed"->repairMechanismPassed79B,
"MechanismConclusion"->If[
TrueQ[repairMechanismPassed79B],
"PRIVATE_DIAMOND_QUOTIENT_RESTORES_CANONICAL_ACTION_SEMANTICS",
"CANONICALIZATION_REPAIR_NOT_ESTABLISHED"
]
|>;

resultHash79B=Hash[
Normal[resultPayload79B],
"SHA256",
"HexString"
];

cert79B=Join[
resultPayload79B,
<|
"AuditOnly"->True,
"ResultHash"->resultHash79B,
"ScientificStatus"->If[
TrueQ[repairMechanismPassed79B],
"POST_HOC_REPAIR_PASS_NOT_BLIND_EVIDENCE",
"REPAIR_AUDIT_FAILED"
],
"SuggestedNextStage"->If[
TrueQ[repairMechanismPassed79B],
"FREEZE_CANONICALIZER_THEN_S80_NEW_BLIND_NEUTRAL_REWRITE",
"DIAGNOSE_S79B_WITHOUT_EDITING_FROZEN_POLICY"
]
|>
];

Dataset[{KeyTake[
cert79B,
{
"Stage",
"Name",
"PriorS79FailureRerun",
"HistoricalRegressionRerun",
"SmallAuditCases",
"SmallAuditPassed",
"S79RepairCases",
"S79RepairPassed",
"AllCanonicalCasesExactlyBase",
"AllContractionCountsCorrect",
"FrozenModelChanged",
"FrozenCoreChanged",
"PolicyEditApplied",
"RetuningApplied",
"InputCanonicalizerAdded",
"OverallArchitectureChanged",
"DesignedAfterS79Exposure",
"S79BIsBlindTest",
"MayClaimRepairMechanism",
"MayClaimNewBlindGeneralization",
"AuditValidityPassed",
"RepairMechanismPassed",
"MechanismConclusion",
"CanonicalizerImplementationHash",
"ResultHash",
"ScientificStatus",
"SuggestedNextStage"
}
]}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "s79ReproductionRows79A=",
    "motifAuditRows79A=",
    "s79FailureReproduced79A=",
):
    if forbidden in wl_source:
        raise RuntimeError(f"Historical S79A test leaked into S79B: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s79b-intro",
            "metadata": {},
            "source": [
                "# TCCT S79B — Private-Diamond Canonicalization Repair Audit\n",
                "\n",
                "这是 **S79 暴露后的候选修复审计**，不是新的 blind test。它不重跑历史回归、不重跑未规范化的 S79、不训练、不搜索、不改冻结参数或策略。\n",
                "\n",
                "新增内容只有一个可审计的输入规范化器：反复收缩不包含受保护语义节点的私有菱形。测试包括 48 个小型结构/语义对照，以及规范化后的 16 个 S79 cases。最后一格会明确区分“修复机制成立”和“新盲测泛化证据”。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s79b-code-{index}",
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
