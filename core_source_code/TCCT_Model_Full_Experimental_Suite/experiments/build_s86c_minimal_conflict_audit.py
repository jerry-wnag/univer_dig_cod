import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
S83A_SOURCE = ROOT / "TCCT_S83A_QuerySwitchFailureAudit.wl"
WL_OUTPUT = ROOT / "TCCT_S86C_MinimalCrossArityConflictAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S86C_MinimalCrossArityConflictAudit.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86C_MinimalCrossArityConflictAudit_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86C_MinimalCrossArityConflictAudit_Preflight_AutoRun.ipynb"
MARKER = "(* S86C CELL *)"


s86_parts = S86_SOURCE.read_text(encoding="utf-8").split("(* S86 CELL *)")
if len(s86_parts) != 5:
    raise RuntimeError("S86 source no longer has exactly four code cells")

s83a_parts = S83A_SOURCE.read_text(encoding="utf-8").split("(* S83A CELL *)")
if len(s83a_parts) != 5:
    raise RuntimeError("S83A source no longer has exactly four code cells")

cell1 = s86_parts[1].strip() + "\n"
cell2 = s86_parts[2].strip() + "\n"
historical_helpers = s83a_parts[2].split("protocol83A=<|", 1)[0].strip()

cell3 = historical_helpers + r'''

ClearAll[
EncodePairForK86C,
PrepareSixConflictRow86C,
BuildHistoricalConflictRows86C,
BuildSixConflictRows86C,
ObservationToken86C,
ExtractConflictMicroRows86C,
MicroTokenRows86C,
SafeMicroPolicy86C,
ScoreMicroRows86C,
S86CDefinitionBundle
];

encodeCache86C=<||>;

EncodePairForK86C[pair_List,k_Integer]:=Module[{key,cached,encoded,code},
key=Hash[{pair,k},"SHA256","HexString"];
cached=Lookup[encodeCache86C,key,Missing["NotCached"]];
If[!MissingQ[cached],Return[cached]];
encoded=First@EncodeRows75[
{<|"Grammar"->"S86CConflictObservation","Depth"->0,
"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate83B["EncoderParams"],k
];
code=First[encoded["Codes"]];
AssociateTo[encodeCache86C,key->code];
code
];

ObservationToken86C[observation_Association,k_Integer]:={
observation["Role"],EncodePairForK86C[observation["RawPair"],k]
};

PrepareSixConflictRow86C[
topology_String,depth_Integer,patchedBranches_List,answer_Integer,target_String
]:=Module[
{
seedCase,patch,hybridSeed,baseCase,topologyCase,canonicalization,
canonicalCase,traceSeconds,trace,levels,pack,vertexList,packedNodes,
observations,originalNode,pair,roleInfo
},
seedCase=Case86[depth,1,"Continue"];
patch=DoubleBranchPatch86[seedCase,patchedBranches];
hybridSeed=ApplyEdgePatch81[seedCase,patch];
baseCase=SetAnswer86[hybridSeed,answer];
topologyCase=TopologyTransform86[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];
pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[
Length[trace["Rejects"]]===0,{},DeleteDuplicates[trace["Rejects"][[All,2]]]
];
observations=Map[
Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole86[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],"RawPair"->pair|>
],packedNodes
];
<|
"Source"->"SixBranch6",
"Topology"->topology,"Depth"->depth,
"PatchedBranches"->patchedBranches,
"GraphCondition"->"DoubleIntervention",
"Answer"->answer,"Target"->target,"BranchCount"->6,
"ReferenceAction"->ReferenceAction86[canonicalCase],
"Observations"->observations,
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"TraceSeconds"->traceSeconds
|>
];

BuildHistoricalConflictRows86C[]:=Module[
{parallelContinue,hybridContinue,historicalStop},
parallelContinue=Flatten[
Table[
Join[
PrepareCapacityRow82C[
"ParallelIn",depth,2,"Continue",
CaseByGrammar82C["ParallelIn",depth,2,"Continue"]
],<|"Source"->"Historical4","BranchCount"->4|>
],
{depth,{2,5,9,15}}
],1
];
hybridContinue=Flatten[
Table[
Map[
Join[#1,<|"Source"->"Historical4","BranchCount"->4|>]&,
Select[
BuildHybridRows83A[topology,depth,3],
SameQ[#1["Target"],"Continue"]&
]
],
{topology,{"DoubleDiamondIn","HierarchicalDiamondIn"}},
{depth,{23,47}}
],2
];
historicalStop=Flatten[
Table[
Join[
PrepareCapacityRow82C[
grammar,depth,4,"Stop",CaseByGrammar82C[grammar,depth,4,"Stop"]
],<|"Source"->"Historical4","BranchCount"->4|>
],
{grammar,{"S59","DiamondIn"}},{depth,{2,5,9,15}}
],2
];
Join[parallelContinue,hybridContinue,historicalStop]
];

BuildSixConflictRows86C[]:=Join[
Flatten[
Table[
PrepareSixConflictRow86C[topology,depth,{2,3},2,"Stop"],
{topology,{"DoubleDiamondIn","HierarchicalDiamondIn"}},
{depth,{43,71}}
],1
],
Flatten[
Table[
PrepareSixConflictRow86C[topology,depth,{4,5},6,"Continue"],
{topology,{"DoubleDiamondIn","HierarchicalDiamondIn"}},
{depth,{43,71}}
],1
]
];

lockedConflictTokens86C={
{"QueriedCorrectDestination",{8,5}},
{"QueriedDecision",{13,13}},
{"QueriedDecision",{14,11}}
};

ExtractConflictMicroRows86C[rows_List]:=Flatten[
Map[
Function[row,
Map[
Function[observation,<|
"Source"->row["Source"],
"BranchCount"->row["BranchCount"],
"Grammar"->Lookup[row,"Grammar",Missing[]],
"Topology"->Lookup[row,"Topology",Missing[]],
"Depth"->row["Depth"],
"Answer"->row["Answer"],
"Target"->row["Target"],
"Role"->observation["Role"],
"RawPair"->observation["RawPair"],
"RawPairHash"->Hash[observation["RawPair"],"SHA256","HexString"],
"K19Token"->ObservationToken86C[observation,19]
|>],
Select[
row["Observations"],
MemberQ[lockedConflictTokens86C,ObservationToken86C[#1,19]]&
]
]
],rows
],1
];

MicroTokenRows86C[microRows_List,representation_String,k_]:=Map[
Function[row,Join[
KeyTake[row,{"Source","BranchCount","Grammar","Topology","Depth",
"Answer","Target","Role","RawPairHash","K19Token"}],
<|"Tokens"->{Switch[
representation,
"RawExactRole",{row["Role"],row["RawPair"]},
"KExactRole",ObservationToken86C[
<|"Role"->row["Role"],"RawPair"->row["RawPair"]|>,k
],
_,$Failed
]}|>
]],microRows
];

SafeMicroPolicy86C[rows_List]:=Module[
{continueTokens,stopTokens},
continueTokens=Union@@Lookup[
Select[rows,SameQ[#1["Target"],"Continue"]&],"Tokens"
];
stopTokens=Union@@Lookup[
Select[rows,SameQ[#1["Target"],"Stop"]&],"Tokens"
];
Complement[continueTokens,stopTokens]
];

ScoreMicroRows86C[rows_List,policy_List]:=Count[
rows,row_/;SameQ[
If[AnyTrue[row["Tokens"],MemberQ[policy,#]&],"Continue","Stop"],
row["Target"]
]
];

S86CDefinitionBundle[]:={
DownValues[CaseByGrammar82C],DownValues[PairBagProfile82C],
DownValues[PrepareCapacityRow82C],DownValues[TopologyTransform83A],
DownValues[SetAnswer83A],DownValues[PrepareAuditRow83A],
DownValues[BuildHybridRows83A],DownValues[EncodePairForK86C],
DownValues[PrepareSixConflictRow86C],
DownValues[BuildHistoricalConflictRows86C],
DownValues[BuildSixConflictRows86C],DownValues[ObservationToken86C],
DownValues[ExtractConflictMicroRows86C],DownValues[MicroTokenRows86C],
DownValues[SafeMicroPolicy86C],DownValues[ScoreMicroRows86C]
};

expectedS86BProtocolHash86C=
"b92bb188dccab9a379df295d87b066f59942ba55beb4010c75820254c1138c13";
expectedBaseCandidateHash86C=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";
kRange86C=Range[10,128];

protocol86C=<|
"Stage"->"S86C",
"Name"->"MinimalCrossArityConflictAudit",
"AuditOnly"->True,
"S86BValidNonSeparableResultAccepted"->True,
"S86BProtocolHashAcknowledged"->expectedS86BProtocolHash86C,
"BaseCandidateHash"->expectedBaseCandidateHash86C,
"ConflictTokens"->lockedConflictTokens86C,
"HistoricalConflictRows"->16,
"SixBranchConflictRows"->8,
"ExpectedConflictRows"->24,
"ExpectedConflictMicroObservations"->28,
"KRangeAudited"->kRange86C,
"RawExactRoleAudited"->True,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"CandidateExportAllowed"->False,
"CoreMayChange"->False,
"DeduplicationMayChange"->False,
"NoConflictRowEvaluatedBeforeProtocolHash"->True
|>;

protocolHash86C=Hash[Normal[protocol86C],"SHA256","HexString"];
modelHashBefore86C=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore86C=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashBefore86C=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashBefore86C=canonicalizerImplementationHash79B;
interventionHashBefore86C=interventionImplementationHash82;
definitionHashBefore86C=Hash[S86CDefinitionBundle[],"SHA256","HexString"];

preflightPassed86C=And[
TrueQ[preflightPassed86],
SameQ[candidateHashBefore86C,expectedBaseCandidateHash86C],
SameQ[frozenCandidate83B["K"],19],
SameQ[Length[frozenCandidate83B["Policy"]],26]
];

If[!TrueQ[preflightPassed86C],
Print["S86C aborted: frozen S83B/K19 preflight failed."];Abort[]
];

Dataset[{Join[protocol86C,<|
"ProtocolHash"->protocolHash86C,"PreflightPassed"->preflightPassed86C
|>]}]
'''.strip() + "\n"

cell4 = r'''
historicalConflictRows86C=BuildHistoricalConflictRows86C[];
sixConflictRows86C=BuildSixConflictRows86C[];
conflictRows86C=Join[historicalConflictRows86C,sixConflictRows86C];
conflictMicroRows86C=ExtractConflictMicroRows86C[conflictRows86C];

rawMicroTokenRows86C=MicroTokenRows86C[
conflictMicroRows86C,"RawExactRole",Missing["NotApplicable"]
];
rawSafePolicy86C=SafeMicroPolicy86C[rawMicroTokenRows86C];
rawScore86C=ScoreMicroRows86C[rawMicroTokenRows86C,rawSafePolicy86C];

kResults86C=Map[
Function[k,
Module[{rows,policy,score,shared},
rows=MicroTokenRows86C[conflictMicroRows86C,"KExactRole",k];
policy=SafeMicroPolicy86C[rows];
score=ScoreMicroRows86C[rows,policy];
shared=Intersection[
Union@@Lookup[Select[rows,SameQ[#1["Target"],"Continue"]&],"Tokens"],
Union@@Lookup[Select[rows,SameQ[#1["Target"],"Stop"]&],"Tokens"]
];
<|"K"->k,"Score"->score,"Perfect"->SameQ[score,Length[rows]],
"SharedTokens"->Length[shared],"PolicyLength"->Length[policy]|>
]],kRange86C
];
perfectKs86C=Lookup[Select[kResults86C,TrueQ[#1["Perfect"]]&],"K"];

conflictDetails86C=Map[
Function[token,
Module[{rows,continueHashes,stopHashes},
rows=Select[conflictMicroRows86C,SameQ[#1["K19Token"],token]&];
continueHashes=DeleteDuplicates@Lookup[
Select[rows,SameQ[#1["Target"],"Continue"]&],"RawPairHash"
];
stopHashes=DeleteDuplicates@Lookup[
Select[rows,SameQ[#1["Target"],"Stop"]&],"RawPairHash"
];
<|
"K19Token"->token,
"MicroObservations"->Length[rows],
"ContinueObservations"->Count[rows,r_/;SameQ[r["Target"],"Continue"]],
"StopObservations"->Count[rows,r_/;SameQ[r["Target"],"Stop"]],
"ContinueRawPairs"->Length[continueHashes],
"StopRawPairs"->Length[stopHashes],
"ExactRawPairsSharedAcrossTargets"->Length[
Intersection[continueHashes,stopHashes]
]
|>
]],lockedConflictTokens86C
];

exactRawAliasCount86C=Total@Lookup[
conflictDetails86C,"ExactRawPairsSharedAcrossTargets"
];

diagnosis86C=Which[
exactRawAliasCount86C>0,
"RAW_STATE_SEMANTIC_ALIAS_REQUIRES_STRUCTURAL_CONTEXT",
SameQ[rawScore86C,Length[conflictMicroRows86C]]&&Length[perfectKs86C]>0,
"K19_MODULO_COLLISION_LARGER_K_LOCAL_SEPARATION_EXISTS",
SameQ[rawScore86C,Length[conflictMicroRows86C]],
"RAW_EXACT_ROLE_SEPARABLE_NO_PERFECT_K_THROUGH_128",
True,
"RAW_EXACT_ROLE_CONFLICT_REQUIRES_STRUCTURAL_CONTEXT"
];

dataSummary86C=<|
"HistoricalConflictRows"->Length[historicalConflictRows86C],
"SixConflictRows"->Length[sixConflictRows86C],
"ConflictRows"->Length[conflictRows86C],
"ConflictMicroObservations"->Length[conflictMicroRows86C],
"ContinueMicroObservations"->Count[
conflictMicroRows86C,r_/;SameQ[r["Target"],"Continue"]
],
"StopMicroObservations"->Count[
conflictMicroRows86C,r_/;SameQ[r["Target"],"Stop"]
],
"SixReferenceActionsCorrect"->Count[
sixConflictRows86C,r_/;SameQ[r["ReferenceAction"],r["Target"]]
],
"AllRowsTerminatedNaturally"->Count[
conflictRows86C,r_/;TrueQ[r["TerminatedNaturally"]]
],
"RowsHitSafetyCap"->Count[
conflictRows86C,r_/;TrueQ[r["HitSafetyCap"]]
],
"RawExactRoleScore"->rawScore86C,
"RawExactRolePerfect"->SameQ[rawScore86C,Length[conflictMicroRows86C]],
"K19LocalScore"->Lookup[First@Select[kResults86C,SameQ[#1["K"],19]&],"Score"],
"PerfectKs10Through128"->perfectKs86C,
"MinimumPerfectKLocal"->If[
Length[perfectKs86C]>0,First[perfectKs86C],Missing["NoneThrough128"]
],
"Diagnosis"->diagnosis86C
|>;

Column[{
Dataset[{dataSummary86C}],
Dataset[conflictDetails86C],
Dataset[kResults86C]
}]
'''.strip() + "\n"

cell5 = r'''
modelHashAfter86C=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter86C=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashAfter86C=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashAfter86C=canonicalizerImplementationHash79B;
interventionHashAfter86C=interventionImplementationHash82;
definitionHashAfter86C=Hash[S86CDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter86C=Hash[Normal[protocol86C],"SHA256","HexString"];

auditValidityPassed86C=And[
TrueQ[preflightPassed86C],
SameQ[protocolHash86C,protocolHashAfter86C],
SameQ[modelHashBefore86C,modelHashAfter86C],
SameQ[candidateHashBefore86C,candidateHashAfter86C],
SameQ[candidateHashAfter86C,expectedBaseCandidateHash86C],
SameQ[coreHashBefore86C,coreHashAfter86C],
SameQ[canonicalizerHashBefore86C,canonicalizerHashAfter86C],
SameQ[interventionHashBefore86C,interventionHashAfter86C],
SameQ[definitionHashBefore86C,definitionHashAfter86C],
SameQ[dataSummary86C["HistoricalConflictRows"],16],
SameQ[dataSummary86C["SixConflictRows"],8],
SameQ[dataSummary86C["ConflictRows"],24],
SameQ[dataSummary86C["ConflictMicroObservations"],28],
SameQ[dataSummary86C["ContinueMicroObservations"],12],
SameQ[dataSummary86C["StopMicroObservations"],16],
SameQ[dataSummary86C["SixReferenceActionsCorrect"],8],
SameQ[dataSummary86C["AllRowsTerminatedNaturally"],24],
SameQ[dataSummary86C["RowsHitSafetyCap"],0]
];

cert86C=<|
"Stage"->"S86C",
"Name"->"MinimalCrossArityConflictAudit",
"AuditOnly"->True,
"AuditValidityPassed"->auditValidityPassed86C,
"ConflictRows"->Length[conflictRows86C],
"ConflictMicroObservations"->Length[conflictMicroRows86C],
"K19LocalScore"->dataSummary86C["K19LocalScore"],
"RawExactRoleScore"->rawScore86C,
"RawExactRolePerfect"->dataSummary86C["RawExactRolePerfect"],
"ExactRawAliasCount"->exactRawAliasCount86C,
"PerfectKs10Through128"->perfectKs86C,
"MinimumPerfectKLocal"->dataSummary86C["MinimumPerfectKLocal"],
"Diagnosis"->diagnosis86C,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore86C,modelHashAfter86C],
"FrozenCandidateChanged"->!SameQ[
candidateHashBefore86C,candidateHashAfter86C
],
"CoreChanged"->!SameQ[coreHashBefore86C,coreHashAfter86C],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore86C,canonicalizerHashAfter86C
],
"InterventionChanged"->!SameQ[
interventionHashBefore86C,interventionHashAfter86C
],
"DeduplicationMechanismChanged"->False,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"CandidateExported"->False,
"S86CIsBlindTest"->False,
"Outcome"->If[
TrueQ[auditValidityPassed86C],
"S86C_CROSS_ARITY_CONFLICT_LOCALIZED",
"INVALID_S86C_AUDIT"
],
"SuggestedNextStage"->Switch[
diagnosis86C,
"K19_MODULO_COLLISION_LARGER_K_LOCAL_SEPARATION_EXISTS",
"S86D_FULL_COMBINED_SCAN_ON_LOCAL_PERFECT_KS",
"RAW_STATE_SEMANTIC_ALIAS_REQUIRES_STRUCTURAL_CONTEXT",
"S86D_OUTER_STRUCTURAL_CONTEXT_AUDIT",
"RAW_EXACT_ROLE_CONFLICT_REQUIRES_STRUCTURAL_CONTEXT",
"S86D_OUTER_STRUCTURAL_CONTEXT_AUDIT",
_,"S86D_EXTEND_CONFLICT_AUDIT"
]
|>;

Dataset[{cert86C}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4, cell5]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

if wl_source.index("protocolHash86C=") > wl_source.index("historicalConflictRows86C="):
    raise RuntimeError("S86C conflict rows would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86C - Minimal Cross-Arity Conflict Audit\n",
        "\n",
        "Audit-only reconstruction of the 24 rows touching the three S86B "
        "cross-arity conflict tokens. It compares raw exact-role states and scans "
        "K=10..128 on conflict micro-observations. No policy is applied to the "
        "frozen candidate and no candidate can be exported.\n",
    ],
}

notebook = {
    "cells": [
        markdown,
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

payload = json.dumps(notebook, ensure_ascii=False, indent=1)
NB_OUTPUT.write_text(payload, encoding="utf-8")
AUTORUN_OUTPUT.write_text(payload, encoding="utf-8")

preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [markdown, *notebook["cells"][1:4]]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
print(AUTORUN_OUTPUT)
print(PREFLIGHT_OUTPUT)
