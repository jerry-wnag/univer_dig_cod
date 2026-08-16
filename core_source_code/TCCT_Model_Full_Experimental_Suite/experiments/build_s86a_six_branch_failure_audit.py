import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
WL_OUTPUT = ROOT / "TCCT_S86A_R1_SixBranchFailureAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S86A_R1_SixBranchFailureAudit.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86A_R1_SixBranchFailureAudit_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86A_R1_SixBranchFailureAudit_Preflight_AutoRun.ipynb"
MARKER = "(* S86A CELL *)"


s86 = S86_SOURCE.read_text(encoding="utf-8")
parts = s86.split("(* S86 CELL *)")
if len(parts) != 5:
    raise RuntimeError("S86 source no longer has exactly four code cells")

# The first two S86 cells contain only the locked architecture/candidate
# preflight and the frozen S86 protocol plus function definitions. No S86
# worlds, predictions, scores, or labels are evaluated there.
cell1 = parts[1].strip() + "\n"
cell2 = parts[2].strip() + "\n"

cell3 = r'''
ClearAll[
PrepareAuditWorld86A,
PrepareAuditScenario86A,
EncodePairForK86A,
TokensForWorld86A,
EvaluateORRepresentation86A,
S86AAuditDefinitionBundle
];

(* Runtime memoization lives outside function DownValues.  The original S86A
   changed its audit-definition hash merely by filling its own function cache.
   This audit-only cache never enters the model, candidate, policy, core, or
   deduplication path. *)
encodeCache86A=<||>;

expectedS86ProtocolHash86A=
"340bd60ac6e1938ca523c0fa78ba98463cf0e34900744001ef2d6ed9731d5fd8";
expectedS86BlindResultHash86A=
"017b8c3cbc415e94a0038a5595cb0c9c962d01cc72a30d0258eb7e3c37058262";

PrepareAuditWorld86A[
topology_String,
depth_Integer,
patchedBranches_List,
graphCondition_String,
answer_Integer,
target_String,
baseCase_List
]:=Module[
{
topologyCase,canonicalization,canonicalCase,traceSeconds,trace,
levels,pack,vertexList,packedNodes,observations,originalNode,pair,roleInfo
},
topologyCase=TopologyTransform86[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
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
roleInfo=NodeRole86[originalNode,canonicalCase,answer];
<|
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"RawPair"->pair
|>
],
packedNodes
];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranches"->patchedBranches,
"GraphCondition"->graphCondition,
"Answer"->answer,
"Target"->target,
"ReferenceAction"->ReferenceAction86[canonicalCase],
"BranchCount"->Length[canonicalCase[[1,6]]],
"Observations"->observations,
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"TraceSeconds"->traceSeconds
|>
];

PrepareAuditScenario86A[
topology_String,depth_Integer,patchedBranches_List
]:=Module[
{branchCount=6,seedCase,patch,hybridSeed,baseline,intervention},
seedCase=Case86[depth,1,"Continue"];
patch=DoubleBranchPatch86[seedCase,patchedBranches];
hybridSeed=ApplyEdgePatch81[seedCase,patch];
If[SameQ[hybridSeed,$Failed],Return[$Failed]];
baseline=Table[
PrepareAuditWorld86A[
topology,depth,patchedBranches,"Baseline",answer,"Continue",
SetAnswer86[seedCase,answer]
],
{answer,Range[branchCount]}
];
intervention=Table[
PrepareAuditWorld86A[
topology,depth,patchedBranches,"DoubleIntervention",answer,
If[MemberQ[patchedBranches,answer],"Stop","Continue"],
SetAnswer86[hybridSeed,answer]
],
{answer,Range[branchCount]}
];
<|
"Topology"->topology,
"Depth"->depth,
"PatchedBranches"->patchedBranches,
"Worlds"->Join[baseline,intervention]
|>
];

EncodePairForK86A[pair_List,k_Integer]:=Module[{key,cached,encoded,code},
key=Hash[{pair,k},"SHA256","HexString"];
cached=Lookup[encodeCache86A,key,Missing["NotCached"]];
If[!MissingQ[cached],Return[cached]];
encoded=First@EncodeRows75[
{<|
"Grammar"->"S86ADevelopmentObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozenCandidate83B["EncoderParams"],
k
];
code=First[encoded["Codes"]];
AssociateTo[encodeCache86A,key->code];
code
];

TokensForWorld86A[
world_Association,
representation_String,
k_,
scope_String
]:=Module[{observations,selected},
observations=world["Observations"];
selected=Switch[
scope,
"AllTokens",observations,
"QueryRelatedOnly",Select[
observations,TrueQ[#["QueryBranchRelated"]]&
],
_,{}
];
DeleteDuplicates@Switch[
representation,
"RawExactRole",
({#1["Role"],#1["RawPair"]}&)/@selected,
"KExactRole",
({#1["Role"],EncodePairForK86A[#1["RawPair"],k]}&)/@selected,
_,{}
]
];

EvaluateORRepresentation86A[
worlds_List,
name_String,
representation_String,
k_,
scope_String
]:=Module[
{
tokenRows,continueIndices,stopIndices,continueTokens,stopTokens,
stopUnion,continueUnion,safePolicy,coveredContinue,predictions,score
},
tokenRows=TokensForWorld86A[#,representation,k,scope]&/@worlds;
continueIndices=Flatten@Position[Lookup[worlds,"Target"],"Continue"];
stopIndices=Flatten@Position[Lookup[worlds,"Target"],"Stop"];
continueTokens=tokenRows[[continueIndices]];
stopTokens=tokenRows[[stopIndices]];
stopUnion=DeleteDuplicates@Flatten[stopTokens,1];
continueUnion=DeleteDuplicates@Flatten[continueTokens,1];
safePolicy=Complement[continueUnion,stopUnion];
coveredContinue=Count[
continueTokens,tokens_/;Intersection[tokens,safePolicy]=!={}
];
predictions=If[Intersection[#,safePolicy]=!={},"Continue","Stop"]&/@tokenRows;
score=Count[
MapThread[SameQ,{predictions,Lookup[worlds,"Target"]}],True
];
<|
"Name"->name,
"Representation"->representation,
"K"->k,
"Scope"->scope,
"Worlds"->Length[worlds],
"ContinueWorlds"->Length[continueIndices],
"StopWorlds"->Length[stopIndices],
"UniqueContinueTokens"->Length[continueUnion],
"UniqueStopTokens"->Length[stopUnion],
"SharedTokens"->Length[Intersection[continueUnion,stopUnion]],
"SafePolicyLength"->Length[safePolicy],
"CoveredContinueWorlds"->coveredContinue,
"UncoveredContinueWorlds"->Length[continueIndices]-coveredContinue,
"BestSafeORScore"->score,
"Perfect"->SameQ[score,Length[worlds]],
"SafePolicy"->safePolicy
|>
];

S86AAuditDefinitionBundle[]:={
DownValues[PrepareAuditWorld86A],
DownValues[PrepareAuditScenario86A],
DownValues[EncodePairForK86A],
DownValues[TokensForWorld86A],
DownValues[EvaluateORRepresentation86A]
};

auditTopology86A="DoubleDiamondIn";
auditDepth86A=43;
auditPatchedBranchPairs86A=blindPatchedBranchPairs86;
auditKRange86A=Range[10,64];

protocol86A=<|
"Stage"->"S86A",
"Name"->"SixBranchFailureMechanismAudit",
"AuditHarnessRevision"->"R1ExternalCache",
"AuditOnly"->True,
"S86ValidBlindFailureAcceptedAsDevelopment"->True,
"ExpectedS86ProtocolHash"->expectedS86ProtocolHash86A,
"ExpectedS86BlindResultHash"->expectedS86BlindResultHash86A,
"CandidateHash"->candidateHashLoaded86,
"FrozenCandidateK"->19,
"FrozenCandidatePolicyLength"->26,
"Topology"->auditTopology86A,
"Depth"->auditDepth86A,
"PatchedBranchPairs"->auditPatchedBranchPairs86A,
"ExpectedScenarios"->6,
"ExpectedWorlds"->72,
"KRangeAudited"->auditKRange86A,
"S86LabelsUsedForAudit"->True,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"CoreMayChange"->False,
"DeduplicationMayChange"->False,
"NoAuditWorldEvaluatedBeforeProtocolHash"->True
|>;

protocolHash86A=Hash[Normal[protocol86A],"SHA256","HexString"];
modelHashBefore86A=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore86A=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashBefore86A=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
auditDefinitionHashBefore86A=Hash[
S86AAuditDefinitionBundle[],"SHA256","HexString"
];

Dataset[{Join[protocol86A,<|"ProtocolHash"->protocolHash86A|>]}]
'''.strip() + "\n"

cell4 = r'''
auditScenarios86A=Map[
PrepareAuditScenario86A[
auditTopology86A,auditDepth86A,#
]&,
auditPatchedBranchPairs86A
];

auditWorlds86A=Flatten[Lookup[auditScenarios86A,"Worlds"],1];

auditDataValidity86A=<|
"Scenarios"->Length[auditScenarios86A],
"Worlds"->Length[auditWorlds86A],
"ContinueWorlds"->Count[
auditWorlds86A,w_/;SameQ[w["Target"],"Continue"]
],
"StopWorlds"->Count[
auditWorlds86A,w_/;SameQ[w["Target"],"Stop"]
],
"ReferenceActionsCorrect"->Count[
auditWorlds86A,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"SixBranchWorlds"->Count[
auditWorlds86A,w_/;SameQ[w["BranchCount"],6]
],
"CanonicalExact"->Count[
auditWorlds86A,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"ProtectedNodesPreserved"->Count[
auditWorlds86A,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"NonEmptyObservations"->Count[
auditWorlds86A,w_/;Length[w["Observations"]]>0
],
"TerminatedNaturally"->Count[
auditWorlds86A,w_/;TrueQ[w["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[
auditWorlds86A,w_/;TrueQ[w["HitSafetyCap"]]
],
"TotalTraceSeconds"->Total@Lookup[auditWorlds86A,"TraceSeconds"]
|>;

rawAll86A=EvaluateORRepresentation86A[
auditWorlds86A,"RawAllTokens","RawExactRole",Missing["NotApplicable"],"AllTokens"
];
rawQuery86A=EvaluateORRepresentation86A[
auditWorlds86A,"RawQueryRelated","RawExactRole",Missing["NotApplicable"],
"QueryRelatedOnly"
];
k19All86A=EvaluateORRepresentation86A[
auditWorlds86A,"K19AllTokens","KExactRole",19,"AllTokens"
];
k19Query86A=EvaluateORRepresentation86A[
auditWorlds86A,"K19QueryRelated","KExactRole",19,"QueryRelatedOnly"
];

capacityScan86A=Map[
Function[k,
EvaluateORRepresentation86A[
auditWorlds86A,"K"<>ToString[k]<>"AllTokens","KExactRole",k,"AllTokens"
]
],
auditKRange86A
];

perfectKs86A=Lookup[
Select[capacityScan86A,TrueQ[#["Perfect"]]&],"K"
];

existingCandidatePredictions86A=Map[
Function[world,
If[
Intersection[
TokensForWorld86A[world,"KExactRole",19,"AllTokens"],
frozenCandidate83B["Policy"]
]=!={},
"Continue","Stop"
]
],
auditWorlds86A
];

existingCandidateScore86A=Count[
MapThread[
SameQ,
{existingCandidatePredictions86A,Lookup[auditWorlds86A,"Target"]}
],
True
];

diagnosis86A=Which[
!TrueQ[rawAll86A["Perfect"]],
"RAW_EXACT_ROLE_OR_READOUT_NOT_SEPARABLE",
TrueQ[k19All86A["Perfect"]]&&existingCandidateScore86A<Length[auditWorlds86A],
"K19_REPRESENTATION_SUFFICIENT_FROZEN_POLICY_COVERAGE_GAP",
!TrueQ[k19All86A["Perfect"]]&&Length[perfectKs86A]>0,
"K19_COMPRESSION_INSUFFICIENT_LARGER_K_SUFFICIENT",
!TrueQ[k19All86A["Perfect"]]&&Length[perfectKs86A]===0,
"ENCODER_FAMILY_NOT_SUFFICIENT_UP_TO_K64",
True,
"UNCLASSIFIED"
];

Column[{
Dataset[{auditDataValidity86A}],
Dataset[Map[
KeyDrop[#,"SafePolicy"]&,
{rawAll86A,rawQuery86A,k19All86A,k19Query86A}
]],
Dataset[Map[
KeyTake[#,{"K","BestSafeORScore","Perfect","SafePolicyLength",
"SharedTokens","UncoveredContinueWorlds"}]&,
capacityScan86A
]],
Dataset[{<|
"ExistingFrozenCandidateScore"->existingCandidateScore86A,
"Worlds"->Length[auditWorlds86A],
"PerfectKs"->perfectKs86A,
"MinimumPerfectK"->If[
Length[perfectKs86A]>0,First[perfectKs86A],Missing["NoneThrough64"]
],
"Diagnosis"->diagnosis86A
|>}]
}]
'''.strip() + "\n"

cell5 = r'''
modelHashAfter86A=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter86A=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashAfter86A=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
auditDefinitionHashAfter86A=Hash[
S86AAuditDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter86A=Hash[Normal[protocol86A],"SHA256","HexString"];

auditValidityPassed86A=And[
TrueQ[preflightPassed86],
SameQ[protocolHash86,expectedS86ProtocolHash86A],
SameQ[modelHashBefore86A,modelHashAfter86A],
SameQ[candidateHashBefore86A,candidateHashAfter86A],
SameQ[candidateHashAfter86A,expectedCandidateHash86],
SameQ[coreHashBefore86A,coreHashAfter86A],
SameQ[auditDefinitionHashBefore86A,auditDefinitionHashAfter86A],
SameQ[protocolHash86A,protocolHashAfter86A],
SameQ[auditDataValidity86A["Scenarios"],6],
SameQ[auditDataValidity86A["Worlds"],72],
SameQ[auditDataValidity86A["ContinueWorlds"],60],
SameQ[auditDataValidity86A["StopWorlds"],12],
SameQ[auditDataValidity86A["ReferenceActionsCorrect"],72],
SameQ[auditDataValidity86A["SixBranchWorlds"],72],
SameQ[auditDataValidity86A["CanonicalExact"],72],
SameQ[auditDataValidity86A["ProtectedNodesPreserved"],72],
SameQ[auditDataValidity86A["NonEmptyObservations"],72],
SameQ[auditDataValidity86A["TerminatedNaturally"],72],
SameQ[auditDataValidity86A["HitSafetyCap"],0]
];

cert86A=<|
"Stage"->"S86A",
"Name"->"SixBranchFailureMechanismAudit",
"AuditHarnessRevision"->"R1ExternalCache",
"AuditOnly"->True,
"S86ProtocolHashMatched"->SameQ[
protocolHash86,expectedS86ProtocolHash86A
],
"S86BlindResultHashAcknowledged"->expectedS86BlindResultHash86A,
"WorldsAudited"->Length[auditWorlds86A],
"ExistingFrozenCandidateScore"->existingCandidateScore86A,
"RawAllTokensPerfect"->rawAll86A["Perfect"],
"RawAllTokensBestScore"->rawAll86A["BestSafeORScore"],
"RawQueryRelatedPerfect"->rawQuery86A["Perfect"],
"K19AllTokensPerfect"->k19All86A["Perfect"],
"K19AllTokensBestScore"->k19All86A["BestSafeORScore"],
"K19QueryRelatedPerfect"->k19Query86A["Perfect"],
"PerfectKs10Through64"->perfectKs86A,
"MinimumPerfectK"->If[
Length[perfectKs86A]>0,First[perfectKs86A],Missing["NoneThrough64"]
],
"Diagnosis"->diagnosis86A,
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore86A,modelHashAfter86A
],
"FrozenCandidateChanged"->!SameQ[
candidateHashBefore86A,candidateHashAfter86A
],
"CoreChanged"->!SameQ[coreHashBefore86A,coreHashAfter86A],
"DeduplicationMechanismChanged"->False,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"S86LabelsUsedForAudit"->True,
"S86ARunIsBlindTest"->False,
"AuditValidityPassed"->auditValidityPassed86A,
"TotalTraceSeconds"->auditDataValidity86A["TotalTraceSeconds"],
"Outcome"->If[
TrueQ[auditValidityPassed86A],
"S86A_FAILURE_MECHANISM_LOCALIZED",
"INVALID_S86A_AUDIT"
],
"SuggestedNextStage"->Switch[
diagnosis86A,
"K19_REPRESENTATION_SUFFICIENT_FROZEN_POLICY_COVERAGE_GAP",
"S86B_DEVELOP_SIX_BRANCH_POLICY_THEN_FREEZE_BEFORE_S87",
"K19_COMPRESSION_INSUFFICIENT_LARGER_K_SUFFICIENT",
"S86B_FREEZE_MINIMUM_SUFFICIENT_K_BEFORE_S87",
"RAW_EXACT_ROLE_OR_READOUT_NOT_SEPARABLE",
"S86B_DEVELOP_RICHER_OUTER_READOUT_WITHOUT_CORE_CHANGE",
_,
"S86B_EXTEND_OUTER_ENCODER_AUDIT"
]
|>;

Dataset[{cert86A}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4, cell5]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindScenarios86=",
    "blindWorlds86=",
    "summary86=",
    "cert86=",
    "resultPayload86=",
    "blindPerfect86=",
):
    if forbidden in cell4 or forbidden in cell5:
        raise RuntimeError(f"Full S86 blind runtime leaked into S86A: {forbidden}")

if wl_source.index("protocolHash86A=") > wl_source.index("auditScenarios86A="):
    raise RuntimeError("S86A audit worlds would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86A-R1 - Six-Branch Failure Mechanism Audit\n",
        "\n",
        "S86 is now development data. This audit reconstructs a symmetry-complete "
        "72-world subset and tests raw exact-role separability, K=19 feasibility, "
        "frozen-policy coverage, and K=10..64 capacity.\n",
        "\n",
        "This notebook does not edit or replace the frozen candidate, core propagation, "
        "canonicalization, topology functions, or DeleteDuplicates behavior. It is not "
        "a blind test.\n",
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
preflight_notebook["cells"] = [
    markdown,
    notebook["cells"][1],
    notebook["cells"][2],
    notebook["cells"][3],
]
PREFLIGHT_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1),
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
print(AUTORUN_OUTPUT)
print(PREFLIGHT_OUTPUT)
