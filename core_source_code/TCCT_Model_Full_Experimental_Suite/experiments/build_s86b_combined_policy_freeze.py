import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
S83A_SOURCE = ROOT / "TCCT_S83A_QuerySwitchFailureAudit.wl"
WL_OUTPUT = ROOT / "TCCT_S86B_CombinedPolicyDevelopmentAndFreeze.wl"
NB_OUTPUT = ROOT / "TCCT_S86B_CombinedPolicyDevelopmentAndFreeze.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86B_CombinedPolicyDevelopmentAndFreeze_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86B_CombinedPolicyDevelopmentAndFreeze_Preflight_AutoRun.ipynb"
MARKER = "(* S86B CELL *)"


s86_parts = S86_SOURCE.read_text(encoding="utf-8").split("(* S86 CELL *)")
if len(s86_parts) != 5:
    raise RuntimeError("S86 source no longer has exactly four code cells")

s83a_parts = S83A_SOURCE.read_text(encoding="utf-8").split("(* S83A CELL *)")
if len(s83a_parts) != 5:
    raise RuntimeError("S83A source no longer has exactly four code cells")

# Locked architecture/candidate preflight and S86 definitions/protocol only.
# No S86 world is evaluated in either source cell.
cell1 = s86_parts[1].strip() + "\n"
cell2 = s86_parts[2].strip() + "\n"

# Reuse only the already-published S83A development-row helper definitions.
# Stop before the old S83A protocol and before any row is generated.
historical_helpers = s83a_parts[2].split("protocol83A=<|", 1)[0].strip()

cell3 = historical_helpers + r'''

ClearAll[
EncodePairForK86B,
TokenizeObservations86B,
TokenizeHistoricalRow86B,
PrepareDevelopmentWorld86B,
PrepareDevelopmentScenario86B,
BuildHistoricalRows86B,
SafePolicy86B,
ScoreTokenRows86B,
PolicyPrediction86B,
S86BDefinitionBundle
];

encodeCache86B=<||>;

EncodePairForK86B[pair_List]:=Module[{key,cached,encoded,code},
key=Hash[pair,"SHA256","HexString"];
cached=Lookup[encodeCache86B,key,Missing["NotCached"]];
If[!MissingQ[cached],Return[cached]];
encoded=First@EncodeRows75[
{<|
"Grammar"->"S86BDevelopmentObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozenCandidate83B["EncoderParams"],
19
];
code=First[encoded["Codes"]];
AssociateTo[encodeCache86B,key->code];
code
];

TokenizeObservations86B[observations_List]:=DeleteDuplicates[
({#1["Role"],EncodePairForK86B[#1["RawPair"]]}&)/@observations
];

TokenizeHistoricalRow86B[row_Association]:=Join[
KeyTake[row,{"Grammar","Depth","Answer","Target","Topology",
"PatchedBranch","WorldType"}],
<|"Source"->"Historical264","Tokens"->
TokenizeObservations86B[row["Observations"]]|>
];

PrepareDevelopmentWorld86B[
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
Length[trace["Rejects"]]===0,{},DeleteDuplicates[trace["Rejects"][[All,2]]]
];
observations=Map[
Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole86[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],"RawPair"->pair|>
],
packedNodes
];
<|
"Source"->"S86Development288",
"Topology"->topology,
"Depth"->depth,
"PatchedBranches"->patchedBranches,
"GraphCondition"->graphCondition,
"Answer"->answer,
"Target"->target,
"ReferenceAction"->ReferenceAction86[canonicalCase],
"BranchCount"->Length[canonicalCase[[1,6]]],
"Tokens"->TokenizeObservations86B[observations],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"TraceSeconds"->traceSeconds
|>
];

PrepareDevelopmentScenario86B[
topology_String,depth_Integer,patchedBranches_List
]:=Module[{seedCase,patch,hybridSeed,baseline,intervention},
seedCase=Case86[depth,1,"Continue"];
patch=DoubleBranchPatch86[seedCase,patchedBranches];
hybridSeed=ApplyEdgePatch81[seedCase,patch];
If[SameQ[hybridSeed,$Failed],Return[$Failed]];
baseline=Table[
PrepareDevelopmentWorld86B[
topology,depth,patchedBranches,"Baseline",answer,"Continue",
SetAnswer86[seedCase,answer]
],
{answer,Range[6]}
];
intervention=Table[
PrepareDevelopmentWorld86B[
topology,depth,patchedBranches,"DoubleIntervention",answer,
If[MemberQ[patchedBranches,answer],"Stop","Continue"],
SetAnswer86[hybridSeed,answer]
],
{answer,Range[6]}
];
<|"Topology"->topology,"Depth"->depth,
"PatchedBranches"->patchedBranches,
"Worlds"->Join[baseline,intervention]|>
];

BuildHistoricalRows86B[]:=Module[{legacy,stress,hybrid},
legacy=Flatten[
Table[
PrepareCapacityRow82C[
grammar,depth,answer,target,
CaseByGrammar82C[grammar,depth,answer,target]
],
{grammar,legacyGrammars83A},{depth,legacyDepths83A},
{answer,Range[4]},{target,{"Continue","Stop"}}
],3
];
stress=Flatten[
Table[
PrepareCapacityRow82C[
"LocalMediatorDevelopment",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],LocalMediatorPatch82[depth,answer]
]
],
{depth,stressDepths83A},{answer,Range[4]}
],1
];
hybrid=Flatten[
Table[
BuildHybridRows83A[topology,depth,patchedBranch],
{topology,auditTopologies83A},{depth,auditDepths83A},
{patchedBranch,auditBranches83A}
],3
];
<|"Legacy"->legacy,"Stress"->stress,"Hybrid"->hybrid|>
];

PolicyPrediction86B[tokens_List,policy_List]:=If[
AnyTrue[tokens,MemberQ[policy,#]&],"Continue","Stop"
];

ScoreTokenRows86B[rows_List,policy_List]:=Count[
rows,row_/;SameQ[PolicyPrediction86B[row["Tokens"],policy],row["Target"]]
];

SafePolicy86B[rows_List]:=Module[
{continueRows,stopRows,continueTokens,stopTokens},
continueRows=Select[rows,SameQ[#1["Target"],"Continue"]&];
stopRows=Select[rows,SameQ[#1["Target"],"Stop"]&];
continueTokens=Union@@Lookup[continueRows,"Tokens"];
stopTokens=Union@@Lookup[stopRows,"Tokens"];
Complement[continueTokens,stopTokens]
];

S86BDefinitionBundle[]:={
DownValues[CaseByGrammar82C],
DownValues[PairBagProfile82C],
DownValues[PrepareCapacityRow82C],
DownValues[TopologyTransform83A],
DownValues[SetAnswer83A],
DownValues[PrepareAuditRow83A],
DownValues[BuildHybridRows83A],
DownValues[EncodePairForK86B],
DownValues[TokenizeObservations86B],
DownValues[TokenizeHistoricalRow86B],
DownValues[PrepareDevelopmentWorld86B],
DownValues[PrepareDevelopmentScenario86B],
DownValues[BuildHistoricalRows86B],
DownValues[SafePolicy86B],
DownValues[ScoreTokenRows86B],
DownValues[PolicyPrediction86B]
};

expectedS86AR1CertificateHash86B=
"2f2e1e4ed0321ac078c9df360e25d119e3108ac19720267fad8378527a234569";
expectedS86AR1ProtocolHash86B=
"c869f4eeddecf521cccd6ad3b04faa7fd202e588d0ef8eb21d2c9f77733c4486";
expectedBaseCandidateHash86B=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";

protocol86B=<|
"Stage"->"S86B",
"Name"->"CombinedPolicyDevelopmentAndFreeze",
"DevelopmentOnly"->True,
"S86AR1CertificateHashAcknowledged"->expectedS86AR1CertificateHash86B,
"S86AR1ProtocolHashAcknowledged"->expectedS86AR1ProtocolHash86B,
"BaseCandidateHash"->expectedBaseCandidateHash86B,
"Representation"->"KExactRole",
"K"->19,
"HistoricalDevelopmentRows"->264,
"S86DevelopmentWorlds"->288,
"CombinedDevelopmentRows"->552,
"PolicyRule"->"AllContinueTokensAbsentFromEveryStopRow",
"S86LabelsUsedForDevelopment"->True,
"S87DataUsed"->False,
"KSearchRun"->False,
"CoreMayChange"->False,
"DeduplicationMayChange"->False,
"NoDevelopmentRowEvaluatedBeforeProtocolHash"->True,
"FreezeOnlyIfCombinedPerfect"->True
|>;

protocolHash86B=Hash[Normal[protocol86B],"SHA256","HexString"];
modelHashBefore86B=Hash[Normal[frozen75D],"SHA256","HexString"];
baseCandidateHashBefore86B=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashBefore86B=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashBefore86B=canonicalizerImplementationHash79B;
interventionHashBefore86B=interventionImplementationHash82;
topologyHashBefore86B=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
developmentDefinitionHashBefore86B=Hash[
S86BDefinitionBundle[],"SHA256","HexString"
];

preflightPassed86B=And[
TrueQ[preflightPassed86],
SameQ[baseCandidateHashBefore86B,expectedBaseCandidateHash86B],
SameQ[frozenCandidate83B["K"],19],
SameQ[frozenCandidate83B["Representation"],"KExactRole"],
SameQ[Length[frozenCandidate83B["Policy"]],26]
];

If[!TrueQ[preflightPassed86B],
Print["S86B aborted: locked S83B/K19 preflight failed."];Abort[]
];

Dataset[{Join[protocol86B,<|
"ProtocolHash"->protocolHash86B,
"PreflightPassed"->preflightPassed86B
|>]}]
'''.strip() + "\n"

cell4 = r'''
historicalSplit86B=BuildHistoricalRows86B[];
historicalRows86B=Join[
historicalSplit86B["Legacy"],historicalSplit86B["Stress"],
historicalSplit86B["Hybrid"]
];
historicalTokenRows86B=TokenizeHistoricalRow86B/@historicalRows86B;

sixBranchScenarios86B=Flatten[
Table[
PrepareDevelopmentScenario86B[topology,depth,patchedBranches],
{topology,blindTopologies86},{depth,blindDepths86},
{patchedBranches,blindPatchedBranchPairs86}
],2
];
sixBranchWorlds86B=Flatten[Lookup[sixBranchScenarios86B,"Worlds"],1];
sixBranchTokenRows86B=Map[
KeyTake[#1,{"Source","Topology","Depth","PatchedBranches",
"GraphCondition","Answer","Target","Tokens"}]&,
sixBranchWorlds86B
];

combinedTokenRows86B=Join[historicalTokenRows86B,sixBranchTokenRows86B];
proposedPolicy86B=SafePolicy86B[combinedTokenRows86B];

historicalOldScore86B=ScoreTokenRows86B[
historicalTokenRows86B,frozenCandidate83B["Policy"]
];
sixBranchOldScore86B=ScoreTokenRows86B[
sixBranchTokenRows86B,frozenCandidate83B["Policy"]
];
combinedOldScore86B=ScoreTokenRows86B[
combinedTokenRows86B,frozenCandidate83B["Policy"]
];

historicalProposedScore86B=ScoreTokenRows86B[
historicalTokenRows86B,proposedPolicy86B
];
sixBranchProposedScore86B=ScoreTokenRows86B[
sixBranchTokenRows86B,proposedPolicy86B
];
combinedProposedScore86B=ScoreTokenRows86B[
combinedTokenRows86B,proposedPolicy86B
];

continueTokens86B=Union@@Lookup[
Select[combinedTokenRows86B,SameQ[#1["Target"],"Continue"]&],"Tokens"
];
stopTokens86B=Union@@Lookup[
Select[combinedTokenRows86B,SameQ[#1["Target"],"Stop"]&],"Tokens"
];
sharedTokens86B=Intersection[continueTokens86B,stopTokens86B];

dataSummary86B=<|
"HistoricalLegacyRows"->Length[historicalSplit86B["Legacy"]],
"HistoricalStressRows"->Length[historicalSplit86B["Stress"]],
"HistoricalHybridRows"->Length[historicalSplit86B["Hybrid"]],
"HistoricalRows"->Length[historicalRows86B],
"SixBranchScenarios"->Length[sixBranchScenarios86B],
"SixBranchWorlds"->Length[sixBranchWorlds86B],
"CombinedRows"->Length[combinedTokenRows86B],
"HistoricalRowsTerminatedNaturally"->Count[
historicalRows86B,row_/;TrueQ[row["TerminatedNaturally"]]
],
"HistoricalRowsHitSafetyCap"->Count[
historicalRows86B,row_/;TrueQ[row["HitSafetyCap"]]
],
"SixBranchReferenceActionsCorrect"->Count[
sixBranchWorlds86B,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"SixBranchCanonicalExact"->Count[
sixBranchWorlds86B,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"SixBranchProtectedNodesPreserved"->Count[
sixBranchWorlds86B,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"SixBranchNonEmptyTokens"->Count[
sixBranchWorlds86B,w_/;Length[w["Tokens"]]>0
],
"SixBranchTerminatedNaturally"->Count[
sixBranchWorlds86B,w_/;TrueQ[w["TerminatedNaturally"]]
],
"SixBranchHitSafetyCap"->Count[
sixBranchWorlds86B,w_/;TrueQ[w["HitSafetyCap"]]
],
"SixBranchTotalTraceSeconds"->Total@Lookup[sixBranchWorlds86B,"TraceSeconds"]
|>;

policySummary86B=<|
"BasePolicyLength"->Length[frozenCandidate83B["Policy"]],
"ProposedPolicyLength"->Length[proposedPolicy86B],
"AddedTokens"->Length[Complement[
proposedPolicy86B,frozenCandidate83B["Policy"]
]],
"RemovedTokens"->Length[Complement[
frozenCandidate83B["Policy"],proposedPolicy86B
]],
"SharedContinueStopTokens"->Length[sharedTokens86B],
"HistoricalOldScore"->historicalOldScore86B,
"SixBranchOldScore"->sixBranchOldScore86B,
"CombinedOldScore"->combinedOldScore86B,
"HistoricalProposedScore"->historicalProposedScore86B,
"SixBranchProposedScore"->sixBranchProposedScore86B,
"CombinedProposedScore"->combinedProposedScore86B,
"CombinedPerfect"->SameQ[combinedProposedScore86B,552]
|>;

Column[{Dataset[{dataSummary86B}],Dataset[{policySummary86B}]}]
'''.strip() + "\n"

cell5 = r'''
modelHashAfterDevelopment86B=Hash[Normal[frozen75D],"SHA256","HexString"];
baseCandidateHashAfterDevelopment86B=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashAfterDevelopment86B=Hash[
CoreDefinitionBundle86[],"SHA256","HexString"
];
canonicalizerHashAfterDevelopment86B=canonicalizerImplementationHash79B;
interventionHashAfterDevelopment86B=interventionImplementationHash82;
topologyHashAfterDevelopment86B=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
developmentDefinitionHashAfter86B=Hash[
S86BDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter86B=Hash[Normal[protocol86B],"SHA256","HexString"];

developmentValidityPassed86B=And[
TrueQ[preflightPassed86B],
SameQ[protocolHash86B,protocolHashAfter86B],
SameQ[modelHashBefore86B,modelHashAfterDevelopment86B],
SameQ[baseCandidateHashBefore86B,baseCandidateHashAfterDevelopment86B],
SameQ[baseCandidateHashAfterDevelopment86B,expectedBaseCandidateHash86B],
SameQ[coreHashBefore86B,coreHashAfterDevelopment86B],
SameQ[canonicalizerHashBefore86B,canonicalizerHashAfterDevelopment86B],
SameQ[interventionHashBefore86B,interventionHashAfterDevelopment86B],
SameQ[topologyHashBefore86B,topologyHashAfterDevelopment86B],
SameQ[developmentDefinitionHashBefore86B,developmentDefinitionHashAfter86B],
SameQ[dataSummary86B["HistoricalLegacyRows"],224],
SameQ[dataSummary86B["HistoricalStressRows"],8],
SameQ[dataSummary86B["HistoricalHybridRows"],32],
SameQ[dataSummary86B["HistoricalRows"],264],
SameQ[dataSummary86B["SixBranchScenarios"],24],
SameQ[dataSummary86B["SixBranchWorlds"],288],
SameQ[dataSummary86B["CombinedRows"],552],
SameQ[dataSummary86B["HistoricalRowsTerminatedNaturally"],264],
SameQ[dataSummary86B["HistoricalRowsHitSafetyCap"],0],
SameQ[dataSummary86B["SixBranchReferenceActionsCorrect"],288],
SameQ[dataSummary86B["SixBranchCanonicalExact"],288],
SameQ[dataSummary86B["SixBranchProtectedNodesPreserved"],288],
SameQ[dataSummary86B["SixBranchNonEmptyTokens"],288],
SameQ[dataSummary86B["SixBranchTerminatedNaturally"],288],
SameQ[dataSummary86B["SixBranchHitSafetyCap"],0],
SameQ[historicalOldScore86B,264]
];

freezeEligible86B=And[
TrueQ[developmentValidityPassed86B],
SameQ[Length[sharedTokens86B],0],
SameQ[historicalProposedScore86B,264],
SameQ[sixBranchProposedScore86B,288],
SameQ[combinedProposedScore86B,552]
];

candidatePath86B="E:/engine_wolf/TCCT_S86B_FrozenCandidate.wl";
candidateExported86B=False;

If[TrueQ[freezeEligible86B],
frozenCandidate86B=<|
"Stage"->"S86B",
"Name"->"CombinedK19PolicyCandidate",
"BaseFrozenModelHash"->frozenCandidate83B["BaseFrozenModelHash"],
"BaseCandidateHash"->expectedBaseCandidateHash86B,
"EncoderParams"->frozenCandidate83B["EncoderParams"],
"Representation"->"KExactRole",
"K"->19,
"Policy"->proposedPolicy86B,
"PolicyLength"->Length[proposedPolicy86B],
"ExactNodeRoleUsed"->True,
"TokenDeduplication"->"DeleteDuplicates",
"HistoricalDevelopmentRows"->264,
"SixBranchDevelopmentWorlds"->288,
"CombinedDevelopmentRows"->552,
"CombinedDevelopmentScore"->combinedProposedScore86B,
"S86LabelsUsedForDevelopment"->True,
"FrozenBeforeS87"->True
|>;
candidateHash86B=Hash[Normal[frozenCandidate86B],"SHA256","HexString"];
candidateExportResult86B=Export[
candidatePath86B,
"frozenCandidate86B="<>ToString[InputForm[frozenCandidate86B]]<>";\n",
"Text"
];
candidateExported86B=And[
StringQ[candidateExportResult86B],FileExistsQ[candidatePath86B]
],
frozenCandidate86B=Missing["CombinedPolicyNotPerfect"];
candidateHash86B=Missing["NotFrozen"]
];

modelHashAfterFreeze86B=Hash[Normal[frozen75D],"SHA256","HexString"];
baseCandidateHashAfterFreeze86B=Hash[
Normal[frozenCandidate83B],"SHA256","HexString"
];
coreHashAfterFreeze86B=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];

freezeValidityPassed86B=And[
TrueQ[freezeEligible86B],
AssociationQ[frozenCandidate86B],
SameQ[frozenCandidate86B["K"],19],
SameQ[frozenCandidate86B["CombinedDevelopmentScore"],552],
SameQ[modelHashBefore86B,modelHashAfterFreeze86B],
SameQ[baseCandidateHashBefore86B,baseCandidateHashAfterFreeze86B],
SameQ[coreHashBefore86B,coreHashAfterFreeze86B],
TrueQ[candidateExported86B]
];

cert86B=<|
"Stage"->"S86B",
"Name"->"CombinedPolicyDevelopmentAndFreeze",
"DevelopmentValidityPassed"->developmentValidityPassed86B,
"Representation"->"KExactRole",
"K"->19,
"BasePolicyLength"->Length[frozenCandidate83B["Policy"]],
"ProposedPolicyLength"->Length[proposedPolicy86B],
"AddedTokens"->policySummary86B["AddedTokens"],
"RemovedTokens"->policySummary86B["RemovedTokens"],
"SharedContinueStopTokens"->Length[sharedTokens86B],
"HistoricalOldScore"->historicalOldScore86B,
"SixBranchOldScore"->sixBranchOldScore86B,
"CombinedOldScore"->combinedOldScore86B,
"HistoricalProposedScore"->historicalProposedScore86B,
"SixBranchProposedScore"->sixBranchProposedScore86B,
"CombinedProposedScore"->combinedProposedScore86B,
"FreezeEligible"->freezeEligible86B,
"CandidateHash"->candidateHash86B,
"CandidateFile"->candidatePath86B,
"CandidateFileExported"->candidateExported86B,
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore86B,modelHashAfterFreeze86B
],
"BaseFrozenCandidateChanged"->!SameQ[
baseCandidateHashBefore86B,baseCandidateHashAfterFreeze86B
],
"CoreChanged"->!SameQ[coreHashBefore86B,coreHashAfterFreeze86B],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore86B,canonicalizerHashAfterDevelopment86B
],
"InterventionChanged"->!SameQ[
interventionHashBefore86B,interventionHashAfterDevelopment86B
],
"TopologyFunctionsChanged"->!SameQ[
topologyHashBefore86B,topologyHashAfterDevelopment86B
],
"DeduplicationMechanismChanged"->False,
"S86BIsBlindTest"->False,
"S87DataUsed"->False,
"FrozenBeforeS87"->TrueQ[freezeValidityPassed86B],
"FreezeValidityPassed"->freezeValidityPassed86B,
"Outcome"->Which[
!TrueQ[developmentValidityPassed86B],"INVALID_S86B_DEVELOPMENT",
!TrueQ[freezeEligible86B],"COMBINED_K19_POLICY_NOT_SEPARABLE_DO_NOT_FREEZE",
TrueQ[freezeValidityPassed86B],"S86B_COMBINED_POLICY_FROZEN",
True,"S86B_FREEZE_FAILED"
],
"SuggestedNextStage"->If[
TrueQ[freezeValidityPassed86B],
"S86C_REVEALED_REGRESSION_THEN_S87_BLIND",
"AUDIT_COMBINED_TOKEN_CONFLICTS"
]
|>;

Dataset[{cert86B}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4, cell5]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

if wl_source.index("protocolHash86B=") > wl_source.index("historicalSplit86B="):
    raise RuntimeError("S86B development data would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86B - Combined K19 Policy Development and Freeze\n",
        "\n",
        "Development-only stage. K remains 19. Core propagation, canonicalization, "
        "intervention, topology transforms, and DeleteDuplicates are locked. The "
        "candidate is exported only if one safe OR policy scores 552/552 across the "
        "264 historical development rows and all 288 revealed S86 worlds.\n",
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
