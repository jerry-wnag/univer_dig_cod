import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82C_SOURCE = ROOT / "TCCT_S82C_RepresentationCapacityDiagnosis.wl"
S83_SOURCE = ROOT / "TCCT_S83_BlindQuerySwitchTopologyComposition.wl"
WL_OUTPUT = ROOT / "TCCT_S83A_QuerySwitchFailureAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S83A_QuerySwitchFailureAudit_AutoRun.ipynb"
MARKER = "(* S83A CELL *)"


s82c = S82C_SOURCE.read_text(encoding="utf-8")
s82c_parts = s82c.split("(* S82C CELL *)")
if len(s82c_parts) != 5:
    raise RuntimeError("S82C source no longer has exactly four code cells")

s83 = S83_SOURCE.read_text(encoding="utf-8")
s83_parts = s83.split("(* S83 CELL *)")
if len(s83_parts) != 5:
    raise RuntimeError("S83 source no longer has exactly four code cells")

base_cell = s83_parts[1].rstrip()
capacity_functions = s82c_parts[3].split("legacyRows82C=", 1)[0].rstrip()

cell1 = base_cell + ";\n\n" + r'''

expectedS83BlindResultHash83A=
"11382b49d339e39a3e08afe33f65ac592c6e859b08fef56cd0e22376ee97c199";

auditPreflight83A=<|
"Stage"->"S83A",
"Name"->"QuerySwitchFailureAudit",
"PriorS83ResultHash"->expectedS83BlindResultHash83A,
"PriorS83Outcome"->"VALID_BLIND_QUERY_SWITCH_COMPOSITION_FAILURE",
"OriginalFrozenModelChanged"->False,
"FrozenCandidateChanged"->False,
"CoreChanged"->False,
"AuditOnly"->True,
"RetuningApplied"->False,
"PreflightPassed"->preflightPassed83
|>;

If[
!TrueQ[preflightPassed83],
Print[Dataset[{auditPreflight83A}]];
Print["S83A aborted: frozen S82C candidate preflight failed."];
Abort[]
];

Dataset[{auditPreflight83A}]
'''.strip() + "\n"

cell2 = capacity_functions + r'''

ClearAll[
TopologyTransform83A,
SetAnswer83A,
PrepareAuditRow83A,
BuildHybridRows83A,
ScopedObservations83A,
ScopedTokenRows83A,
EvaluateScope83A,
AuditDefinitionBundle83A
];

TopologyTransform83A[topology_String,c_List]:=Switch[
topology,
"DoubleDiamondIn",DoubleDiamondIn79[c],
"HierarchicalDiamondIn",HierarchicalDiamondIn80[c],
_,$Failed
];

SetAnswer83A[c_List,answer_Integer]:={c[[1]],answer};

PrepareAuditRow83A[
topology_String,
depth_Integer,
patchedBranch_Integer,
answer_Integer,
target_String,
worldType_String,
baseCase_List
]:=Join[
PrepareCapacityRow82C[
"S83A-"<>worldType,
depth,
answer,
target,
TopologyTransform83A[topology,baseCase]
],
<|
"Topology"->topology,
"PatchedBranch"->patchedBranch,
"WorldType"->worldType
|>
];

BuildHybridRows83A[
topology_String,depth_Integer,patchedBranch_Integer
]:=Module[
{seedCase,hybridCase,factualAnswer,factualBase,counterfactualBase},
seedCase=Case59[depth,patchedBranch,"Continue"];
hybridCase=ApplyEdgePatch81[
seedCase,LocalMediatorPatch82[depth,patchedBranch]
];
factualAnswer=1+Mod[patchedBranch,4];
factualBase=SetAnswer83A[hybridCase,factualAnswer];
counterfactualBase=SetAnswer83A[hybridCase,patchedBranch];
{
PrepareAuditRow83A[
topology,depth,patchedBranch,factualAnswer,"Continue",
"HybridFactual",factualBase
],
PrepareAuditRow83A[
topology,depth,patchedBranch,patchedBranch,"Stop",
"HybridCounterfactual",counterfactualBase
]
}
];

ScopedObservations83A[row_Association,scope_Association]:=Switch[
scope["Type"],
"All",row["Observations"],
"QueryRelated",Select[
row["Observations"],TrueQ[#1["QueryBranchRelated"]]&
],
"RoleSubset",Select[
row["Observations"],MemberQ[scope["Roles"],#1["Role"]]&
],
_,{}
];

ScopedTokenRows83A[rows_List,scope_Association]:=Map[
Function[row,
Join[
KeyTake[row,{"Grammar","Depth","Answer","Target","Topology",
"PatchedBranch","WorldType"}],
<|
"Tokens"->DeleteDuplicates[
({#1["Role"],EncodePairWithK82C[#1["RawPair"],10]}&)/@
ScopedObservations83A[row,scope]
]
|>
]
],
rows
];

EvaluateScope83A[scope_Association]:=Module[
{legacyTokens,stressTokens,hybridTokens,allTokens,policy},
legacyTokens=ScopedTokenRows83A[legacyRows83A,scope];
stressTokens=ScopedTokenRows83A[stressRows83A,scope];
hybridTokens=ScopedTokenRows83A[hybridRows83A,scope];
allTokens=Join[legacyTokens,stressTokens,hybridTokens];
policy=SafePolicy82C[allTokens];
Join[
scope,
<|
"Policy"->policy,
"PolicyLength"->Length[policy],
"LegacyScore"->ScoreRows82C[legacyTokens,policy],
"LegacyCases"->Length[legacyTokens],
"StressScore"->ScoreRows82C[stressTokens,policy],
"StressCases"->Length[stressTokens],
"HybridFactualScore"->ScoreRows82C[
Select[hybridTokens,SameQ[#1["Target"],"Continue"]&],policy
],
"HybridFactualCases"->Count[
hybridTokens,row_/;SameQ[row["Target"],"Continue"]
],
"HybridCounterfactualScore"->ScoreRows82C[
Select[hybridTokens,SameQ[#1["Target"],"Stop"]&],policy
],
"HybridCounterfactualCases"->Count[
hybridTokens,row_/;SameQ[row["Target"],"Stop"]
],
"AllDevelopmentScore"->ScoreRows82C[allTokens,policy],
"AllDevelopmentCases"->Length[allTokens],
"AddedTokensVsFrozen"->Length[Complement[
policy,frozenCandidate82C["Policy"]
]],
"RemovedTokensVsFrozen"->Length[Complement[
frozenCandidate82C["Policy"],policy
]],
"Perfect"->SameQ[ScoreRows82C[allTokens,policy],Length[allTokens]]
|>
]
];

AuditDefinitionBundle83A[]:={
DownValues[TopologyTransform83A],DownValues[SetAnswer83A],
DownValues[PrepareAuditRow83A],DownValues[BuildHybridRows83A],
DownValues[ScopedObservations83A],DownValues[ScopedTokenRows83A],
DownValues[EvaluateScope83A]
};

legacyGrammars83A={
"S59","ChainIn","SharedMerge","ParallelIn",
"ParallelOut","DiamondIn","SharedParallelIn"
};
legacyDepths83A={2,5,9,15};
stressDepths83A={2,5};
auditDepths83A={23,47};
auditTopologies83A={"DoubleDiamondIn","HierarchicalDiamondIn"};
auditBranches83A=Range[4];

queryRoles83A={
"QueriedDecision","QueriedMediatorSource",
"QueriedCorrectDestination","QueriedWrongDestination",
"QueriedDummyDestination"
};

scopeCandidates83A=Join[
{
<|"Name"->"AllTokens","Type"->"All","Roles"->All,"Priority"->0|>,
<|"Name"->"QueryRelatedOnly","Type"->"QueryRelated",
"Roles"->queryRoles83A,"Priority"->1|>
},
MapIndexed[
Function[{roles,index},<|
"Name"->("RoleSubset"<>ToString[First[index]]),
"Type"->"RoleSubset",
"Roles"->roles,
"Priority"->10+Length[roles]
|>],
Rest@Subsets[queryRoles83A]
]
];

protocol83A=<|
"Stage"->"S83A",
"Name"->"QuerySwitchFailureAudit",
"PriorS83ResultHash"->expectedS83BlindResultHash83A,
"LegacyGrammars"->legacyGrammars83A,
"LegacyDepths"->legacyDepths83A,
"StressDepths"->stressDepths83A,
"AuditDepths"->auditDepths83A,
"AuditTopologies"->auditTopologies83A,
"AuditBranches"->auditBranches83A,
"ScopeCandidateCount"->Length[scopeCandidates83A],
"UsesS83LabelsForPostFailureDiagnosis"->True,
"S83AIsBlindTest"->False,
"CandidateSearchAppliedToFrozenModel"->False,
"RetuningApplied"->False,
"CoreMayChange"->False,
"NoRowEvaluatedBeforeProtocolHash"->True
|>;

protocolHash83A=Hash[Normal[protocol83A],"SHA256","HexString"];
modelHashBefore83A=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore83A=Hash[
Normal[frozenCandidate82C],"SHA256","HexString"
];
coreHashBefore83A=Hash[CoreDefinitionBundle83[],"SHA256","HexString"];
canonicalizerHashBefore83A=canonicalizerImplementationHash79B;
interventionHashBefore83A=interventionImplementationHash82;
auditDefinitionHashBefore83A=Hash[
AuditDefinitionBundle83A[],"SHA256","HexString"
];

Dataset[{Join[protocol83A,<|"ProtocolHash"->protocolHash83A|>]}]
'''.strip() + "\n"

cell3 = r'''
legacyRows83A=Flatten[
Table[
PrepareCapacityRow82C[
grammar,depth,answer,target,
CaseByGrammar82C[grammar,depth,answer,target]
],
{grammar,legacyGrammars83A},
{depth,legacyDepths83A},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
3
];

stressRows83A=Flatten[
Table[
PrepareCapacityRow82C[
"LocalMediatorDevelopment",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,stressDepths83A},
{answer,Range[4]}
],
1
];

hybridRows83A=Flatten[
Table[
BuildHybridRows83A[topology,depth,patchedBranch],
{topology,auditTopologies83A},
{depth,auditDepths83A},
{patchedBranch,auditBranches83A}
],
3
];

allScopeResults83A=EvaluateScope83A/@scopeCandidates83A;
perfectScopes83A=Select[allScopeResults83A,TrueQ[#1["Perfect"]]&];

allScope83A=First@Select[
allScopeResults83A,SameQ[#1["Name"],"AllTokens"]&
];
queryRelatedScope83A=First@Select[
allScopeResults83A,SameQ[#1["Name"],"QueryRelatedOnly"]&
];

frozenAllTokens83A=ScopedTokenRows83A[
Join[legacyRows83A,stressRows83A,hybridRows83A],
First[scopeCandidates83A]
];
frozenPolicyScore83A=ScoreRows82C[
frozenAllTokens83A,frozenCandidate82C["Policy"]
];

selectedFeasibleScope83A=If[
Length[perfectScopes83A]>0,
First@SortBy[
perfectScopes83A,
{#1["Priority"],Length[#1["Roles"]/.All->{}],#1["PolicyLength"],#1["Name"]}&
],
Missing["NoPerfectScope"]
];

failureDiagnosis83A=Which[
TrueQ[allScope83A["Perfect"]],
"OUTER_POLICY_COVERAGE_FAILURE_TOKENS_ARE_SEPARABLE",
TrueQ[queryRelatedScope83A["Perfect"]],
"GLOBAL_POOLING_CONTAMINATION_QUERY_SCOPE_SUFFICIENT",
Length[perfectScopes83A]>0,
"ROLE_SCOPE_SELECTION_REQUIRED",
True,
"K10_EXACT_ROLE_TOKEN_REPRESENTATION_NOT_SEPARABLE"
];

dataSummary83A=<|
"LegacyRows"->Length[legacyRows83A],
"StressRows"->Length[stressRows83A],
"HybridRows"->Length[hybridRows83A],
"AllRowsTerminatedNaturally"->And@@Lookup[
Join[legacyRows83A,stressRows83A,hybridRows83A],
"TerminatedNaturally"
],
"RowsHitSafetyCap"->Count[
Join[legacyRows83A,stressRows83A,hybridRows83A],
row_/;TrueQ[row["HitSafetyCap"]]
],
"FrozenPolicyScore"->frozenPolicyScore83A,
"FrozenPolicyCases"->Length[frozenAllTokens83A],
"PerfectScopeCount"->Length[perfectScopes83A],
"FailureDiagnosis"->failureDiagnosis83A
|>;

Column[{
Dataset[{dataSummary83A}],
Dataset[Map[
KeyDrop[#1,"Policy"]&,
Take[SortBy[allScopeResults83A,{-#1["AllDevelopmentScore"],#1["Priority"]}&],
UpTo[12]]
]],
Dataset[{If[
AssociationQ[selectedFeasibleScope83A],
KeyDrop[selectedFeasibleScope83A,"Policy"],
<|"SelectedScope"->selectedFeasibleScope83A|>
]}]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfter83A=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter83A=Hash[
Normal[frozenCandidate82C],"SHA256","HexString"
];
coreHashAfter83A=Hash[CoreDefinitionBundle83[],"SHA256","HexString"];
canonicalizerHashAfter83A=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},"SHA256","HexString"
];
interventionHashAfter83A=Hash[
{
DownValues[LocalMediatorSources82],DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],DownValues[ReferenceAction82]
},"SHA256","HexString"
];
auditDefinitionHashAfter83A=Hash[
AuditDefinitionBundle83A[],"SHA256","HexString"
];
protocolHashAfter83A=Hash[Normal[protocol83A],"SHA256","HexString"];

auditValidityPassed83A=And[
TrueQ[preflightPassed83],
SameQ[modelHashBefore83A,modelHashAfter83A],
SameQ[candidateHashBefore83A,candidateHashAfter83A],
SameQ[candidateHashAfter83A,expectedCandidateHash83],
SameQ[coreHashBefore83A,coreHashAfter83A],
SameQ[canonicalizerHashBefore83A,canonicalizerHashAfter83A],
SameQ[canonicalizerHashAfter83A,expectedCanonicalizerHash83],
SameQ[interventionHashBefore83A,interventionHashAfter83A],
SameQ[interventionHashAfter83A,expectedInterventionHash83],
SameQ[auditDefinitionHashBefore83A,auditDefinitionHashAfter83A],
SameQ[protocolHash83A,protocolHashAfter83A],
SameQ[Length[legacyRows83A],224],
SameQ[Length[stressRows83A],8],
SameQ[Length[hybridRows83A],32],
TrueQ[dataSummary83A["AllRowsTerminatedNaturally"]],
SameQ[dataSummary83A["RowsHitSafetyCap"],0]
];

cert83A=<|
"Stage"->"S83A",
"Name"->"QuerySwitchFailureAudit",
"Meaning"->"PostS83DevelopmentAuditNotBlindTest",
"PriorS83ResultHash"->expectedS83BlindResultHash83A,
"RowsAudited"->Length[Join[legacyRows83A,stressRows83A,hybridRows83A]],
"ScopeCandidatesAudited"->Length[allScopeResults83A],
"FrozenPolicyScore"->frozenPolicyScore83A,
"FrozenPolicyCases"->Length[frozenAllTokens83A],
"AllTokensRetrainedPerfect"->allScope83A["Perfect"],
"AllTokensRetrainedPolicyLength"->allScope83A["PolicyLength"],
"AllTokensAddedTokens"->allScope83A["AddedTokensVsFrozen"],
"QueryRelatedPerfect"->queryRelatedScope83A["Perfect"],
"PerfectScopeCount"->Length[perfectScopes83A],
"SelectedFeasibleScope"->If[
AssociationQ[selectedFeasibleScope83A],
selectedFeasibleScope83A["Name"],
selectedFeasibleScope83A
],
"SelectedFeasiblePolicyLength"->If[
AssociationQ[selectedFeasibleScope83A],
selectedFeasibleScope83A["PolicyLength"],
Missing["NoPolicy"]
],
"FailureDiagnosis"->failureDiagnosis83A,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore83A,modelHashAfter83A],
"FrozenCandidateChanged"->!SameQ[
candidateHashBefore83A,candidateHashAfter83A
],
"CoreChanged"->!SameQ[coreHashBefore83A,coreHashAfter83A],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore83A,canonicalizerHashAfter83A
],
"InterventionChanged"->!SameQ[
interventionHashBefore83A,interventionHashAfter83A
],
"DeduplicationMechanismChanged"->False,
"RetuningApplied"->False,
"S83AIsBlindTest"->False,
"AuditValidityPassed"->auditValidityPassed83A,
"SuggestedNextStage"->Which[
!TrueQ[auditValidityPassed83A],"FIX_AUDIT_ONLY",
Length[perfectScopes83A]>0,"S83B_FREEZE_OUTER_READOUT_CANDIDATE",
True,"S83B_QUERY_LOCAL_RELATIONAL_REPRESENTATION_DEVELOPMENT"
]
|>;

Dataset[{cert83A}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

if "blindPairs83=" in wl_source:
    raise RuntimeError("Stored S83 result rows leaked into S83A")
if wl_source.index("protocolHash83A=") > wl_source.index("legacyRows83A="):
    raise RuntimeError("S83A rows would be generated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# TCCT S83A — Query-Switch Failure Audit\n",
                "\n",
                "只读审计 S83 的有效盲测失败。重新构造旧开发行与 S83 行，判断 K10 ExactRole token 是否仍然可分；不修改冻结候选或核心。\n",
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
