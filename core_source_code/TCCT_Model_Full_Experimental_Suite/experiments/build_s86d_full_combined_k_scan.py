import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S86_SOURCE = ROOT / "TCCT_S86_ExternalSixBranchBlind.wl"
S86B_SOURCE = ROOT / "TCCT_S86B_CombinedPolicyDevelopmentAndFreeze.wl"
WL_OUTPUT = ROOT / "TCCT_S86D_FullCombinedKFeasibilityScan.wl"
NB_OUTPUT = ROOT / "TCCT_S86D_FullCombinedKFeasibilityScan.ipynb"
AUTORUN_OUTPUT = ROOT / "TCCT_S86D_FullCombinedKFeasibilityScan_AutoRun.ipynb"
PREFLIGHT_OUTPUT = ROOT / "TCCT_S86D_FullCombinedKFeasibilityScan_Preflight_AutoRun.ipynb"
MARKER = "(* S86D CELL *)"


s86_parts = S86_SOURCE.read_text(encoding="utf-8").split("(* S86 CELL *)")
if len(s86_parts) != 5:
    raise RuntimeError("S86 source no longer has exactly four code cells")

s86b_parts = S86B_SOURCE.read_text(encoding="utf-8").split("(* S86B CELL *)")
if len(s86b_parts) != 6:
    raise RuntimeError("S86B source no longer has exactly five code cells")

cell1 = s86_parts[1].strip() + "\n"
cell2 = s86_parts[2].strip() + "\n"

# Reuse S86B's published raw-row reconstruction helpers only.  Stop before
# any S86B protocol or development row.  Store observations rather than K19
# tokens so all K candidates reuse exactly the same propagation traces.
raw_helpers = s86b_parts[3].split(
    "expectedS86AR1CertificateHash86B=", 1
)[0].strip()
raw_helpers = raw_helpers.replace(
    '"Tokens"->TokenizeObservations86B[observations],',
    '"Observations"->observations,',
)

cell3 = raw_helpers + r'''

ClearAll[
EncodePairForK86D,
TokenizeRawRow86D,
SafePolicy86D,
PolicyPrediction86D,
ScoreRows86D,
EvaluateK86D,
S86DDefinitionBundle
];

encodeCache86D=<||>;

EncodePairForK86D[pair_List,k_Integer]:=Module[{key,cached,encoded,code},
key=Hash[{pair,k},"SHA256","HexString"];
cached=Lookup[encodeCache86D,key,Missing["NotCached"]];
If[!MissingQ[cached],Return[cached]];
encoded=First@EncodeRows75[
{<|"Grammar"->"S86DFullCombinedObservation","Depth"->0,
"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate83B["EncoderParams"],k
];
code=First[encoded["Codes"]];
AssociateTo[encodeCache86D,key->code];
code
];

TokenizeRawRow86D[row_Association,k_Integer]:=Join[
KeyTake[row,{"Source","Grammar","Topology","Depth","Answer","Target",
"PatchedBranch","PatchedBranches","WorldType","GraphCondition"}],
<|"Tokens"->DeleteDuplicates[
({#1["Role"],EncodePairForK86D[#1["RawPair"],k]}&)/@row["Observations"]
]|>
];

SafePolicy86D[rows_List]:=Module[{continueTokens,stopTokens},
continueTokens=Union@@Lookup[
Select[rows,SameQ[#1["Target"],"Continue"]&],"Tokens"
];
stopTokens=Union@@Lookup[
Select[rows,SameQ[#1["Target"],"Stop"]&],"Tokens"
];
Complement[continueTokens,stopTokens]
];

PolicyPrediction86D[tokens_List,policy_List]:=If[
AnyTrue[tokens,MemberQ[policy,#]&],"Continue","Stop"
];

ScoreRows86D[rows_List,policy_List]:=Count[
rows,row_/;SameQ[PolicyPrediction86D[row["Tokens"],policy],row["Target"]]
];

EvaluateK86D[k_Integer]:=Module[
{historical,six,combined,policy,hScore,sScore,cScore,shared},
historical=TokenizeRawRow86D[#,k]&/@historicalRawRows86D;
six=TokenizeRawRow86D[#,k]&/@sixRawRows86D;
combined=Join[historical,six];
policy=SafePolicy86D[combined];
hScore=ScoreRows86D[historical,policy];
sScore=ScoreRows86D[six,policy];
cScore=ScoreRows86D[combined,policy];
shared=Intersection[
Union@@Lookup[Select[combined,SameQ[#1["Target"],"Continue"]&],"Tokens"],
Union@@Lookup[Select[combined,SameQ[#1["Target"],"Stop"]&],"Tokens"]
];
<|
"K"->k,"HistoricalScore"->hScore,"SixBranchScore"->sScore,
"CombinedScore"->cScore,"CombinedPerfect"->SameQ[cScore,552],
"SharedTokens"->Length[shared],"PolicyLength"->Length[policy],
"Policy"->policy
|>
];

S86DDefinitionBundle[]:={
DownValues[CaseByGrammar82C],DownValues[PairBagProfile82C],
DownValues[PrepareCapacityRow82C],DownValues[TopologyTransform83A],
DownValues[SetAnswer83A],DownValues[PrepareAuditRow83A],
DownValues[BuildHybridRows83A],DownValues[PrepareDevelopmentWorld86B],
DownValues[PrepareDevelopmentScenario86B],
DownValues[BuildHistoricalRows86B],DownValues[EncodePairForK86D],
DownValues[TokenizeRawRow86D],DownValues[SafePolicy86D],
DownValues[PolicyPrediction86D],DownValues[ScoreRows86D],
DownValues[EvaluateK86D]
};

expectedS86CCertificateHash86D=
"945cbf88b24e0b25cfc07a23ea2d2b4cad028c5a2eb8ce5a419a4ac33d74800d";
expectedS86CProtocolHash86D=
"2da68ba2a69f44f2fc367441a7bd1bfadce2801350323cdc3397d4466966636f";
expectedBaseCandidateHash86D=
"a51e6a13bdeda37b041eee4b74cfb6e472c7e52107a60f1d5534bb5df44ce44f";

localPerfectKs86D={
10,12,13,14,15,16,18,20,21,23,24,25,26,27,28,29,30,31,32,33,
35,36,37,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,
56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,
76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,
96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,
112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,127,128
};

protocol86D=<|
"Stage"->"S86D",
"Name"->"FullCombinedKFeasibilityScan",
"AuditOnly"->True,
"S86CCertificateHashAcknowledged"->expectedS86CCertificateHash86D,
"S86CProtocolHashAcknowledged"->expectedS86CProtocolHash86D,
"BaseCandidateHash"->expectedBaseCandidateHash86D,
"HistoricalDevelopmentRows"->264,
"SixBranchDevelopmentWorlds"->288,
"CombinedDevelopmentRows"->552,
"CandidateKs"->localPerfectKs86D,
"CandidateKCount"->Length[localPerfectKs86D],
"K19ExcludedByS86C"->!MemberQ[localPerfectKs86D,19],
"Representation"->"KExactRole",
"PolicyRule"->"AllContinueTokensAbsentFromEveryStopRow",
"SelectionRule"->"MinimumKThenMinimumPolicyLength",
"S86LabelsUsedForDevelopment"->True,
"S87DataUsed"->False,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"CandidateExportAllowed"->False,
"CoreMayChange"->False,
"DeduplicationMayChange"->False,
"NoDevelopmentRowEvaluatedBeforeProtocolHash"->True
|>;

protocolHash86D=Hash[Normal[protocol86D],"SHA256","HexString"];
modelHashBefore86D=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashBefore86D=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashBefore86D=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashBefore86D=canonicalizerImplementationHash79B;
interventionHashBefore86D=interventionImplementationHash82;
definitionHashBefore86D=Hash[S86DDefinitionBundle[],"SHA256","HexString"];

preflightPassed86D=And[
TrueQ[preflightPassed86],
SameQ[candidateHashBefore86D,expectedBaseCandidateHash86D],
SameQ[Length[localPerfectKs86D],113],
!MemberQ[localPerfectKs86D,19]
];

If[!TrueQ[preflightPassed86D],
Print["S86D aborted: locked protocol/candidate preflight failed."];Abort[]
];

Dataset[{Join[protocol86D,<|
"ProtocolHash"->protocolHash86D,"PreflightPassed"->preflightPassed86D
|>]}]
'''.strip() + "\n"

cell4 = r'''
historicalSplit86D=BuildHistoricalRows86B[];
historicalRawRows86D=Map[
Join[#1,<|"Source"->"Historical264"|>]&,
Join[
historicalSplit86D["Legacy"],historicalSplit86D["Stress"],
historicalSplit86D["Hybrid"]
]
];

sixScenarios86D=Flatten[
Table[
PrepareDevelopmentScenario86B[topology,depth,patchedBranches],
{topology,blindTopologies86},{depth,blindDepths86},
{patchedBranches,blindPatchedBranchPairs86}
],2
];
sixRawRows86D=Flatten[Lookup[sixScenarios86D,"Worlds"],1];

kResults86D=EvaluateK86D/@localPerfectKs86D;
fullPerfectResults86D=Select[
kResults86D,TrueQ[#1["CombinedPerfect"]]&
];
selectedResult86D=If[
Length[fullPerfectResults86D]>0,
First@SortBy[fullPerfectResults86D,{#1["K"],#1["PolicyLength"]}&],
Missing["NoFullCombinedPerfectK"]
];

dataSummary86D=<|
"HistoricalLegacyRows"->Length[historicalSplit86D["Legacy"]],
"HistoricalStressRows"->Length[historicalSplit86D["Stress"]],
"HistoricalHybridRows"->Length[historicalSplit86D["Hybrid"]],
"HistoricalRows"->Length[historicalRawRows86D],
"SixBranchScenarios"->Length[sixScenarios86D],
"SixBranchWorlds"->Length[sixRawRows86D],
"CombinedRows"->Length[historicalRawRows86D]+Length[sixRawRows86D],
"HistoricalRowsTerminatedNaturally"->Count[
historicalRawRows86D,r_/;TrueQ[r["TerminatedNaturally"]]
],
"HistoricalRowsHitSafetyCap"->Count[
historicalRawRows86D,r_/;TrueQ[r["HitSafetyCap"]]
],
"SixReferenceActionsCorrect"->Count[
sixRawRows86D,r_/;SameQ[r["ReferenceAction"],r["Target"]]
],
"SixCanonicalExact"->Count[
sixRawRows86D,r_/;TrueQ[r["CanonicalCaseExactlyBase"]]
],
"SixProtectedNodesPreserved"->Count[
sixRawRows86D,r_/;TrueQ[r["ProtectedNodesPreserved"]]
],
"SixRowsTerminatedNaturally"->Count[
sixRawRows86D,r_/;TrueQ[r["TerminatedNaturally"]]
],
"SixRowsHitSafetyCap"->Count[
sixRawRows86D,r_/;TrueQ[r["HitSafetyCap"]]
],
"SixTotalTraceSeconds"->Total@Lookup[sixRawRows86D,"TraceSeconds"]
|>;

scanSummary86D=<|
"CandidateKsEvaluated"->Length[kResults86D],
"FullCombinedPerfectKCount"->Length[fullPerfectResults86D],
"FullCombinedPerfectKs"->Lookup[fullPerfectResults86D,"K"],
"SelectedK"->If[
AssociationQ[selectedResult86D],selectedResult86D["K"],selectedResult86D
],
"SelectedPolicyLength"->If[
AssociationQ[selectedResult86D],selectedResult86D["PolicyLength"],
Missing["NoSelection"]
],
"SelectedHistoricalScore"->If[
AssociationQ[selectedResult86D],selectedResult86D["HistoricalScore"],
Missing["NoSelection"]
],
"SelectedSixBranchScore"->If[
AssociationQ[selectedResult86D],selectedResult86D["SixBranchScore"],
Missing["NoSelection"]
],
"SelectedCombinedScore"->If[
AssociationQ[selectedResult86D],selectedResult86D["CombinedScore"],
Missing["NoSelection"]
]
|>;

Column[{
Dataset[{dataSummary86D}],
Dataset[Map[KeyDrop[#1,"Policy"]&,kResults86D]],
Dataset[{scanSummary86D}]
}]
'''.strip() + "\n"

cell5 = r'''
modelHashAfter86D=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter86D=Hash[Normal[frozenCandidate83B],"SHA256","HexString"];
coreHashAfter86D=Hash[CoreDefinitionBundle86[],"SHA256","HexString"];
canonicalizerHashAfter86D=canonicalizerImplementationHash79B;
interventionHashAfter86D=interventionImplementationHash82;
definitionHashAfter86D=Hash[S86DDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter86D=Hash[Normal[protocol86D],"SHA256","HexString"];

scanValidityPassed86D=And[
TrueQ[preflightPassed86D],
SameQ[protocolHash86D,protocolHashAfter86D],
SameQ[modelHashBefore86D,modelHashAfter86D],
SameQ[candidateHashBefore86D,candidateHashAfter86D],
SameQ[candidateHashAfter86D,expectedBaseCandidateHash86D],
SameQ[coreHashBefore86D,coreHashAfter86D],
SameQ[canonicalizerHashBefore86D,canonicalizerHashAfter86D],
SameQ[interventionHashBefore86D,interventionHashAfter86D],
SameQ[definitionHashBefore86D,definitionHashAfter86D],
SameQ[dataSummary86D["HistoricalLegacyRows"],224],
SameQ[dataSummary86D["HistoricalStressRows"],8],
SameQ[dataSummary86D["HistoricalHybridRows"],32],
SameQ[dataSummary86D["HistoricalRows"],264],
SameQ[dataSummary86D["SixBranchScenarios"],24],
SameQ[dataSummary86D["SixBranchWorlds"],288],
SameQ[dataSummary86D["CombinedRows"],552],
SameQ[dataSummary86D["HistoricalRowsTerminatedNaturally"],264],
SameQ[dataSummary86D["HistoricalRowsHitSafetyCap"],0],
SameQ[dataSummary86D["SixReferenceActionsCorrect"],288],
SameQ[dataSummary86D["SixCanonicalExact"],288],
SameQ[dataSummary86D["SixProtectedNodesPreserved"],288],
SameQ[dataSummary86D["SixRowsTerminatedNaturally"],288],
SameQ[dataSummary86D["SixRowsHitSafetyCap"],0],
SameQ[Length[kResults86D],113]
];

cert86D=<|
"Stage"->"S86D",
"Name"->"FullCombinedKFeasibilityScan",
"AuditOnly"->True,
"ScanValidityPassed"->scanValidityPassed86D,
"CandidateKsEvaluated"->Length[kResults86D],
"FullCombinedPerfectKCount"->Length[fullPerfectResults86D],
"FullCombinedPerfectKs"->Lookup[fullPerfectResults86D,"K"],
"SelectedK"->scanSummary86D["SelectedK"],
"SelectedPolicyLength"->scanSummary86D["SelectedPolicyLength"],
"SelectedHistoricalScore"->scanSummary86D["SelectedHistoricalScore"],
"SelectedSixBranchScore"->scanSummary86D["SelectedSixBranchScore"],
"SelectedCombinedScore"->scanSummary86D["SelectedCombinedScore"],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore86D,modelHashAfter86D],
"FrozenCandidateChanged"->!SameQ[candidateHashBefore86D,candidateHashAfter86D],
"CoreChanged"->!SameQ[coreHashBefore86D,coreHashAfter86D],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore86D,canonicalizerHashAfter86D
],
"InterventionChanged"->!SameQ[
interventionHashBefore86D,interventionHashAfter86D
],
"DeduplicationMechanismChanged"->False,
"PolicyAppliedToFrozenCandidate"->False,
"NewCandidateSelected"->False,
"CandidateExported"->False,
"S86DIsBlindTest"->False,
"S87DataUsed"->False,
"Outcome"->Which[
!TrueQ[scanValidityPassed86D],"INVALID_S86D_SCAN",
Length[fullPerfectResults86D]>0,"FULL_COMBINED_PERFECT_K_EXISTS",
True,"NO_K10_THROUGH128_SOLVES_FULL_COMBINED_DATA"
],
"SuggestedNextStage"->If[
TrueQ[scanValidityPassed86D]&&Length[fullPerfectResults86D]>0,
"S86E_FREEZE_SELECTED_K_AND_REVEALED_REGRESSION",
"S86E_OUTER_STRUCTURAL_CONTEXT_AUDIT"
]
|>;

Dataset[{cert86D}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4, cell5]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

if wl_source.index("protocolHash86D=") > wl_source.index("historicalSplit86D="):
    raise RuntimeError("S86D data would be evaluated before protocol hashing")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S86D - Full Combined K Feasibility Scan\n",
        "\n",
        "Audit-only scan over the 113 K values that passed S86C. Propagation is "
        "run once for 264 historical and 288 revealed S86 rows; every K reuses the "
        "same raw observations. No policy is applied to the frozen candidate and no "
        "candidate is exported.\n",
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
