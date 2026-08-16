import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82_SOURCE = ROOT / "TCCT_S82_BlindLocalMediatorCounterfactualTest.wl"
S71_SOURCE = ROOT / "TCCT_S71_recovered_full.wl"
S72_SOURCE = ROOT / "TCCT_S72_FrozenTopologyBattery.wl"
WL_OUTPUT = ROOT / "TCCT_S82B_QueryRoleSemanticRepresentationDevelopment.wl"
NB_OUTPUT = ROOT / "TCCT_S82B_QueryRoleSemanticRepresentationDevelopment.ipynb"
MARKER = "(* S82B CELL *)"


def section(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        raise RuntimeError(f"Could not extract section: {start!r} -> {end!r}")
    return text[text.index(start) : text.index(end)].rstrip()


s82 = S82_SOURCE.read_text(encoding="utf-8")
s71 = S71_SOURCE.read_text(encoding="utf-8")
s72 = S72_SOURCE.read_text(encoding="utf-8")

s82_parts = s82.split("(* S82 CELL *)")
if len(s82_parts) != 5:
    raise RuntimeError("S82 source no longer has exactly four code cells")

# Frozen architecture only; no S82 blind rows, scores, or result computation.
frozen_architecture = s82_parts[1].split(
    "expectedMinimalKernelHash82=", 1
)[0].rstrip()
intervention_definitions = s82_parts[2].split("blindDepths82=", 1)[0].rstrip()

# Exact historical topology constructors needed to reconstruct the S75D all-seen set.
legacy_63 = section(
    s71,
    "ClearAll[ChainIn63, SharedMerge63, Case63];",
    "(* In[168] *)",
)
legacy_71 = section(
    s71,
    "ClearAll[ParallelIn71];",
    "(* In[412] *)",
)
parallel_out_72 = section(
    s72,
    "ParallelOut72[c_List]:=Module[",
    "DiamondIn72[c_List]:=Module[",
)
shared_parallel_72 = section(
    s72,
    "SharedParallelIn72[c_List]:=Module[",
    "Case72[",
)

legacy_topologies = (
    legacy_63
    + "\n\n"
    + legacy_71
    + "\n\nClearAll[ParallelOut72,SharedParallelIn72,Case72B];\n"
    + parallel_out_72
    + "\n\n"
    + shared_parallel_72
    + r'''

Case72B[
topology_String,
depth_Integer,
answer_Integer,
target_String
]:=Switch[
topology,
"ParallelOut",
ParallelOut72[Case59[depth,answer,target]],
"DiamondIn",
DiamondIn72[Case59[depth,answer,target]],
"SharedParallelIn",
SharedParallelIn72[Case59[depth,answer,target]],
_,
$Failed
];
'''.rstrip()
)

cell1 = (
    frozen_architecture
    + "\n\n"
    + legacy_topologies
    + "\n\n"
    + intervention_definitions
    + r'''

expectedMinimalKernelDefinitionTextHash82B=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash82B=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedStableFrozenArchitectureHash82B=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedNeutralTopologyHash82B=
"01af33358afe3fcfe876288b6de7c99a89af22599320fec75911661e240bc121";
expectedInterventionHash82B=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedS82ProtocolHash82B=
"7695bea7ea07f903615ce01ad6b6a8481d2741ef1ce08fafb0e2d279e39f09bd";
expectedS82BlindResultHash82B=
"64be56fb8ef29638666efaf92cdcd03994a43e3328236fd0f7bd73a4808aa58f";
expectedS82AAuditResultHash82B=
"bcdcd4ce2882cc0f3ce8e605508e469271f2bdba482b7389795f77a1fb4b6919";

ClearAll[CoreDefinitionBundle82B];
CoreDefinitionBundle82B[]:={
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
};

minimalKernelDefinitionTextHash82B=Hash[
ToString[InputForm[CoreDefinitionBundle82B[]]],
"SHA256",
"HexString"
];

stableFrozenArchitectureHash82B=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash82B,
canonicalizerImplementationHash79B
},
"SHA256",
"HexString"
];

developmentTopologyHash82B=Hash[
{
DownValues[ChainIn63],DownValues[SharedMerge63],DownValues[Case63],
DownValues[ParallelIn71],DownValues[Case71],
DownValues[ParallelOut72],DownValues[SharedParallelIn72],
DownValues[Case72B]
},
"SHA256",
"HexString"
];

preflightPassed82B=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash82B,
expectedMinimalKernelDefinitionTextHash82B
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash82B
],
SameQ[
stableFrozenArchitectureHash82B,
expectedStableFrozenArchitectureHash82B
],
SameQ[
topologyImplementationHash80,
expectedNeutralTopologyHash82B
],
SameQ[
interventionImplementationHash82,
expectedInterventionHash82B
]
];

preflight82B=<|
"Stage"->"S82B",
"Name"->"QueryRoleSemanticRepresentationDevelopment",
"OriginalFrozenModelChanged"->False,
"CoreChanged"->False,
"S82BlindRowsLoaded"->False,
"S82BlindLabelsUsedForSelection"->False,
"S82BlindTestRerun"->False,
"PriorS82ProtocolHash"->expectedS82ProtocolHash82B,
"PriorS82BlindResultHash"->expectedS82BlindResultHash82B,
"PriorS82AAuditResultHash"->expectedS82AAuditResultHash82B,
"StableFrozenArchitectureHash"->stableFrozenArchitectureHash82B,
"DevelopmentTopologyHash"->developmentTopologyHash82B,
"PreflightPassed"->preflightPassed82B
|>;

If[
!TrueQ[preflightPassed82B],
Print[Dataset[{preflight82B}]];
Print["S82B aborted: frozen architecture or intervention mismatch."];
Abort[]
];

Dataset[{preflight82B}]
'''.strip()
    + "\n"
)

cell2 = r'''
ClearAll[
CaseByGrammar82B,
NodeRole82B,
EncodePair82B,
PrepareRoleRow82B,
TokenizeObservation82B,
TokenizedRows82B,
SafePolicy82B,
PredictRoleTokens82B,
ScoreRoleRows82B,
EvaluateScheme82B
];

legacyGrammars82B={
"S59","ChainIn","SharedMerge","ParallelIn",
"ParallelOut","DiamondIn","SharedParallelIn"
};
legacyDepths82B={2,5,9,15};
stressFitDepths82B={2,5};
stressValidationDepths82B={9,15};
roleSchemes82B={
"CodeOnly",
"QueryFlag",
"QueryBranchFlag",
"CoarseRole",
"ExactRole"
};
schemeComplexity82B=<|
"CodeOnly"->0,
"QueryFlag"->1,
"QueryBranchFlag"->1,
"CoarseRole"->2,
"ExactRole"->3
|>;

protocol82B=<|
"Stage"->"S82B",
"Name"->"QueryRoleSemanticRepresentationDevelopment",
"Purpose"->"RepairDesignWithoutS82BlindRetuning",
"LegacyGrammars"->legacyGrammars82B,
"LegacyDepths"->legacyDepths82B,
"LegacyExpectedCases"->224,
"LocalStressFitDepths"->stressFitDepths82B,
"LocalStressValidationDepths"->stressValidationDepths82B,
"LocalStressExpectedCases"->16,
"CandidateSchemes"->roleSchemes82B,
"PolicyRule"->"ContinueTokensMinusAnyObservedStopTokens",
"SelectionRule"->
"LegacyPerfectThenStressFitPerfectThenStressValidationPerfectThenMinimumComplexity",
"UsesS82InterventionFamilyForDevelopment"->True,
"UsesS82BlindDepths"->False,
"UsesS82BlindRows"->False,
"UsesS82BlindLabels"->False,
"RerunsS76ThroughS82"->False,
"FutureBlindStage"->"S83"
|>;

protocolHash82B=Hash[
Normal[protocol82B],
"SHA256",
"HexString"
];

modelHashBefore82B=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashBefore82B=Hash[CoreDefinitionBundle82B[],"SHA256","HexString"];
coreTextHashBefore82B=minimalKernelDefinitionTextHash82B;
canonicalizerHashBefore82B=canonicalizerImplementationHash79B;
interventionHashBefore82B=interventionImplementationHash82;
protocolHashBefore82B=protocolHash82B;

Dataset[{Join[
protocol82B,
<|
"ProtocolHash"->protocolHash82B,
"NoCaseEvaluatedBeforeProtocolHash"->True
|>
]}]
'''.strip() + "\n"

cell3 = r'''
CaseByGrammar82B[
grammar_String,
depth_Integer,
answer_Integer,
target_String
]:=Switch[
grammar,
"S59",Case59[depth,answer,target],
"ChainIn",Case63["ChainIn",depth,answer,target],
"SharedMerge",Case63["SharedMerge",depth,answer,target],
"ParallelIn",Case71[depth,answer,target],
"ParallelOut"|"DiamondIn"|"SharedParallelIn",
Case72B[grammar,depth,answer,target],
_,$Failed
];

NodeRole82B[
originalNode_,
case_List,
answer_Integer
]:=Module[
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

EncodePair82B[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[
{<|
"Grammar"->"S82BRoleObservation",
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

PrepareRoleRow82B[
grammar_String,
depth_Integer,
answer_Integer,
target_String,
case_List
]:=Module[
{
canonicalization,canonicalCase,trace,levels,pack,vertexList,
packedNodes,observations,roleInfo,pair,code,originalNode
},
canonicalization=CanonicalizePrivateDiamonds79B[case];
canonicalCase=canonicalization["Case"];
trace=RejectTrace78[canonicalCase];
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
pair={
Lookup[levels[[3]],packedNode],
Lookup[levels[[4]],packedNode]
};
code=EncodePair82B[pair];
roleInfo=NodeRole82B[originalNode,canonicalCase,answer];
<|
"PackedNode"->packedNode,
"OriginalNode"->originalNode,
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"RawPairHash"->Hash[pair,"SHA256","HexString"],
"Code"->code
|>
],
packedNodes
];
<|
"Grammar"->grammar,
"Depth"->depth,
"Answer"->answer,
"Target"->target,
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"CanonicalizationContractions"->canonicalization["Contractions"],
"Observations"->observations
|>
];

TokenizeObservation82B[observation_Association,scheme_String]:=Module[
{code,role,branch,coarse},
code=observation["Code"];
role=observation["Role"];
branch=observation["QueryBranchRelated"];
coarse=Which[
SameQ[role,"QueriedDecision"],"QueriedDecision",
TrueQ[branch],"QueriedBranchOther",
True,"Other"
];
Switch[
scheme,
"CodeOnly",code,
"QueryFlag",{If[SameQ[role,"QueriedDecision"],"Query","Other"],code},
"QueryBranchFlag",{If[TrueQ[branch],"QueryBranch","Other"],code},
"CoarseRole",{coarse,code},
"ExactRole",{role,code},
_,$Failed
]
];

TokenizedRows82B[rows_List,scheme_String]:=Map[
Function[row,
Join[
KeyTake[row,{"Grammar","Depth","Answer","Target"}],
<|
"Tokens"->DeleteDuplicates[
TokenizeObservation82B[#,scheme]&/@row["Observations"]
]
|>
]
],
rows
];

SafePolicy82B[tokenRows_List]:=Module[
{continueRows,stopRows,continueTokens,stopTokens},
continueRows=Select[tokenRows,SameQ[#["Target"],"Continue"]&];
stopRows=Select[tokenRows,SameQ[#["Target"],"Stop"]&];
continueTokens=Union@@Lookup[continueRows,"Tokens"];
stopTokens=Union@@Lookup[stopRows,"Tokens"];
Complement[continueTokens,stopTokens]
];

PredictRoleTokens82B[tokens_List,policy_List]:=If[
AnyTrue[tokens,MemberQ[policy,#]&],
"Continue",
"Stop"
];

ScoreRoleRows82B[tokenRows_List,policy_List]:=Count[
tokenRows,
row_/;SameQ[
PredictRoleTokens82B[row["Tokens"],policy],
row["Target"]
]
];

legacyRows82B=Flatten[
Table[
PrepareRoleRow82B[
grammar,depth,answer,target,
CaseByGrammar82B[grammar,depth,answer,target]
],
{grammar,legacyGrammars82B},
{depth,legacyDepths82B},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
3
];

stressFitRows82B=Flatten[
Table[
PrepareRoleRow82B[
"LocalMediatorDevelopment",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,stressFitDepths82B},
{answer,Range[4]}
],
1
];

stressValidationRows82B=Flatten[
Table[
PrepareRoleRow82B[
"LocalMediatorValidation",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,stressValidationDepths82B},
{answer,Range[4]}
],
1
];

fitRows82B=Join[legacyRows82B,stressFitRows82B];

EvaluateScheme82B[scheme_String]:=Module[
{
legacyTokenRows,stressFitTokenRows,stressValidationTokenRows,
fitTokenRows,policy,legacyScore,stressFitScore,stressValidationScore,
fitContinueTokens,fitStopTokens
},
legacyTokenRows=TokenizedRows82B[legacyRows82B,scheme];
stressFitTokenRows=TokenizedRows82B[stressFitRows82B,scheme];
stressValidationTokenRows=TokenizedRows82B[
stressValidationRows82B,scheme
];
fitTokenRows=Join[legacyTokenRows,stressFitTokenRows];
policy=SafePolicy82B[fitTokenRows];
legacyScore=ScoreRoleRows82B[legacyTokenRows,policy];
stressFitScore=ScoreRoleRows82B[stressFitTokenRows,policy];
stressValidationScore=ScoreRoleRows82B[
stressValidationTokenRows,policy
];
fitContinueTokens=Union@@Lookup[
Select[fitTokenRows,SameQ[#["Target"],"Continue"]&],
"Tokens"
];
fitStopTokens=Union@@Lookup[
Select[fitTokenRows,SameQ[#["Target"],"Stop"]&],
"Tokens"
];
<|
"Scheme"->scheme,
"Complexity"->schemeComplexity82B[scheme],
"Policy"->policy,
"PolicyLength"->Length[policy],
"FitSemanticConflictTokens"->Intersection[
fitContinueTokens,fitStopTokens
],
"LegacyScore"->legacyScore,
"LegacyCases"->Length[legacyTokenRows],
"StressFitScore"->stressFitScore,
"StressFitCases"->Length[stressFitTokenRows],
"StressValidationScore"->stressValidationScore,
"StressValidationCases"->Length[stressValidationTokenRows],
"Eligible"->And[
SameQ[legacyScore,Length[legacyTokenRows]],
SameQ[stressFitScore,Length[stressFitTokenRows]],
SameQ[stressValidationScore,Length[stressValidationTokenRows]]
]
|>
];

schemeResults82B=EvaluateScheme82B/@roleSchemes82B;
eligibleSchemes82B=Select[schemeResults82B,TrueQ[#["Eligible"]]&];
selectedScheme82B=If[
Length[eligibleSchemes82B]>0,
First@SortBy[
eligibleSchemes82B,
{#["Complexity"],#["PolicyLength"],#["Scheme"]}&
],
Missing["NoEligibleScheme"]
];

dataSummary82B=<|
"LegacyCases"->Length[legacyRows82B],
"LegacyCasesByGrammar"->Counts@Lookup[legacyRows82B,"Grammar"],
"StressFitCases"->Length[stressFitRows82B],
"StressValidationCases"->Length[stressValidationRows82B],
"AllRowsTerminatedNaturally"->And@@Lookup[
Join[legacyRows82B,stressFitRows82B,stressValidationRows82B],
"TerminatedNaturally"
],
"RowsHitSafetyCap"->Count[
Join[legacyRows82B,stressFitRows82B,stressValidationRows82B],
row_/;TrueQ[row["HitSafetyCap"]]
]
|>;

Column[{
Dataset[{dataSummary82B}],
Dataset[Map[KeyDrop[#,"Policy"]&,schemeResults82B]]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfter82B=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter82B=Hash[CoreDefinitionBundle82B[],"SHA256","HexString"];
coreTextHashAfter82B=Hash[
ToString[InputForm[CoreDefinitionBundle82B[]]],
"SHA256",
"HexString"
];
canonicalizerHashAfter82B=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256",
"HexString"
];
interventionHashAfter82B=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256",
"HexString"
];
protocolHashAfter82B=Hash[Normal[protocol82B],"SHA256","HexString"];

integrityPassed82B=And[
SameQ[modelHashBefore82B,modelHashAfter82B],
SameQ[modelHashAfter82B,expectedFrozenModelHash79A],
SameQ[coreHashBefore82B,coreHashAfter82B],
SameQ[coreTextHashBefore82B,coreTextHashAfter82B],
SameQ[
coreTextHashAfter82B,
expectedMinimalKernelDefinitionTextHash82B
],
SameQ[canonicalizerHashBefore82B,canonicalizerHashAfter82B],
SameQ[canonicalizerHashAfter82B,expectedCanonicalizerHash82B],
SameQ[interventionHashBefore82B,interventionHashAfter82B],
SameQ[interventionHashAfter82B,expectedInterventionHash82B],
SameQ[protocolHashBefore82B,protocolHashAfter82B]
];

developmentValidityPassed82B=And[
TrueQ[preflightPassed82B],
TrueQ[integrityPassed82B],
SameQ[Length[legacyRows82B],224],
SameQ[Length[stressFitRows82B],8],
SameQ[Length[stressValidationRows82B],8],
TrueQ[dataSummary82B["AllRowsTerminatedNaturally"]],
SameQ[dataSummary82B["RowsHitSafetyCap"],0]
];

selectionSucceeded82B=And[
TrueQ[developmentValidityPassed82B],
AssociationQ[selectedScheme82B],
TrueQ[selectedScheme82B["Eligible"]]
];

frozenCandidate82B=If[
TrueQ[selectionSucceeded82B],
<|
"Stage"->"S82B",
"Name"->"QueryRoleSemanticRepresentationCandidate",
"BaseFrozenModelHash"->expectedFrozenModelHash79A,
"EncoderParams"->frozen75D["Params"],
"K"->frozen75D["K"],
"RoleScheme"->selectedScheme82B["Scheme"],
"RolePolicy"->selectedScheme82B["Policy"],
"SelectionUsesS82BlindLabels"->False,
"FrozenBeforeS83"->True
|>,
Missing["NoCandidateFrozen"]
];

candidateHash82B=If[
AssociationQ[frozenCandidate82B],
Hash[Normal[frozenCandidate82B],"SHA256","HexString"],
Missing["NoCandidateHash"]
];

cert82B=<|
"Stage"->"S82B",
"Name"->"QueryRoleSemanticRepresentationDevelopment",
"Meaning"->
"PostS82RepairDevelopmentNotANewBlindCounterfactualSuccess",
"CasesEvaluated"->(
Length[legacyRows82B]+Length[stressFitRows82B]+
Length[stressValidationRows82B]
),
"EligibleSchemeCount"->Length[eligibleSchemes82B],
"SelectedScheme"->If[
AssociationQ[selectedScheme82B],
selectedScheme82B["Scheme"],
selectedScheme82B
],
"SelectedPolicyLength"->If[
AssociationQ[selectedScheme82B],
selectedScheme82B["PolicyLength"],
Missing["NoPolicy"]
],
"SelectedLegacyScore"->If[
AssociationQ[selectedScheme82B],
{selectedScheme82B["LegacyScore"],selectedScheme82B["LegacyCases"]},
Missing["NoScore"]
],
"SelectedStressFitScore"->If[
AssociationQ[selectedScheme82B],
{selectedScheme82B["StressFitScore"],selectedScheme82B["StressFitCases"]},
Missing["NoScore"]
],
"SelectedStressValidationScore"->If[
AssociationQ[selectedScheme82B],
{
selectedScheme82B["StressValidationScore"],
selectedScheme82B["StressValidationCases"]
},
Missing["NoScore"]
],
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore82B,modelHashAfter82B
],
"CoreChanged"->!SameQ[coreHashBefore82B,coreHashAfter82B],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore82B,canonicalizerHashAfter82B
],
"InterventionChanged"->!SameQ[
interventionHashBefore82B,interventionHashAfter82B
],
"S82BlindRowsLoaded"->False,
"S82BlindLabelsUsedForSelection"->False,
"S82BlindTestRerun"->False,
"S82BIsBlindTest"->False,
"DevelopmentValidityPassed"->developmentValidityPassed82B,
"SelectionSucceeded"->selectionSucceeded82B,
"CandidateHash"->candidateHash82B,
"ReadyForNewS83BlindTest"->selectionSucceeded82B,
"SuggestedNextStage"->If[
TrueQ[selectionSucceeded82B],
"S83_FREEZE_CANDIDATE_THEN_NEW_INTERVENTION_BLIND_TEST",
"S82C_REPRESENTATION_CAPACITY_DIAGNOSIS_WITHOUT_S82_BLIND_LABELS"
]
|>;

Dataset[{cert82B}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindDepths82=",
    "blindCounterfactualPairs82=",
    "PrepareBlindCounterfactualPair82",
    "EvaluateArchitecture82",
    "counterfactualPairs81=",
    "blindRows80=",
    "{31,63}",
):
    if forbidden in wl_source:
        raise RuntimeError(f"S82 blind material leaked into S82B: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s82b-intro",
            "metadata": {},
            "source": [
                "# TCCT S82B — Query-Role Semantic Representation Development\n",
                "\n",
                "这是 S82 失败后的开发阶段，不是新的盲测成功。它不读取或重跑 S82 的 8 个盲测对，也不使用 S82 标签选择候选。\n",
                "\n",
                "候选仅由 S75D 及更早允许使用的 224 个已见样本，以及深度 2/5 的局部干预开发样本和深度 9/15 的局部干预验证样本决定。通过后只冻结候选；真正的新能力结论留给 S83。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s82b-code-{index}",
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
