import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S82B_SOURCE = ROOT / "TCCT_S82B_QueryRoleSemanticRepresentationDevelopment.wl"
WL_OUTPUT = ROOT / "TCCT_S82C_RepresentationCapacityDiagnosis.wl"
NB_OUTPUT = ROOT / "TCCT_S82C_RepresentationCapacityDiagnosis.ipynb"
MARKER = "(* S82C CELL *)"


def section(text: str, start: str, end: str) -> str:
    if start not in text or end not in text:
        raise RuntimeError(f"Could not extract section: {start!r} -> {end!r}")
    return text[text.index(start) : text.index(end)].rstrip()


s82b = S82B_SOURCE.read_text(encoding="utf-8")
parts = s82b.split("(* S82B CELL *)")
if len(parts) != 5:
    raise RuntimeError("S82B source no longer has exactly four code cells")

# Reuse only frozen architecture, historical topology constructors, and intervention
# definitions. S82B scores, candidate results, and selection are not copied.
base_definitions = parts[1].split(
    "expectedMinimalKernelDefinitionTextHash82B=", 1
)[0].rstrip()

# Remove the old S71 p71 constructor sanity expression; it is not needed here.
if "(* In[408] *)" in base_definitions and "(* In[410] *)" in base_definitions:
    start = base_definitions.index("(* In[408] *)")
    end = base_definitions.index("(* In[410] *)")
    base_definitions = base_definitions[:start] + base_definitions[end:]

cell1 = base_definitions + r'''

expectedMinimalKernelDefinitionTextHash82C=
"d56be85db649ba1ea4118050a019d35a07c28f394396858f1d40a1f90572b922";
expectedCanonicalizerHash82C=
"5e95c90f528a68d1045048e54b5a08809bf54c01b934902faf47f3dc3e5e587d";
expectedStableFrozenArchitectureHash82C=
"d7d16575e25bd1090e35484931dedae9f80254475ee49cd2d79d43f5d4d1355d";
expectedInterventionHash82C=
"45a4f2364a569f5346c9d007c0da716dc1752193fc68abcb2b6acd88c5af54bf";
expectedS82BlindResultHash82C=
"64be56fb8ef29638666efaf92cdcd03994a43e3328236fd0f7bd73a4808aa58f";
expectedS82AAuditResultHash82C=
"bcdcd4ce2882cc0f3ce8e605508e469271f2bdba482b7389795f77a1fb4b6919";
expectedS82BProtocolHash82C=
"e4479a7f80f74778011f3fb03967c5dd350224a4f1b85c0d27f74ef0bde07243";

ClearAll[CoreDefinitionBundle82C];
CoreDefinitionBundle82C[]:={
DownValues[P59],DownValues[A59],DownValues[T59],DownValues[Case59],
OwnValues[rw60],DownValues[Pack60],DownValues[SigLevels61],
DownValues[PropagationSafetyCap78],DownValues[RejectTrace78],
DownValues[DecisionStatePairsFromRejects78],DownValues[EncodeRows75],
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],DownValues[Case79]
};

minimalKernelDefinitionTextHash82C=Hash[
ToString[InputForm[CoreDefinitionBundle82C[]]],
"SHA256","HexString"
];

stableFrozenArchitectureHash82C=Hash[
{
Normal[frozen75D],
minimalKernelDefinitionTextHash82C,
canonicalizerImplementationHash79B
},
"SHA256","HexString"
];

preflightPassed82C=And[
SameQ[modelHash79A,expectedFrozenModelHash79A],
SameQ[
minimalKernelDefinitionTextHash82C,
expectedMinimalKernelDefinitionTextHash82C
],
SameQ[
canonicalizerImplementationHash79B,
expectedCanonicalizerHash82C
],
SameQ[
stableFrozenArchitectureHash82C,
expectedStableFrozenArchitectureHash82C
],
SameQ[
interventionImplementationHash82,
expectedInterventionHash82C
]
];

preflight82C=<|
"Stage"->"S82C",
"Name"->"RepresentationCapacityDiagnosis",
"OriginalFrozenModelChanged"->False,
"CoreChanged"->False,
"PriorS82BlindResultHash"->expectedS82BlindResultHash82C,
"PriorS82AAuditResultHash"->expectedS82AAuditResultHash82C,
"PriorS82BProtocolHash"->expectedS82BProtocolHash82C,
"PriorS82BOutcome"->"NO_ELIGIBLE_ROLE_ONLY_SCHEME",
"S82BlindRowsLoaded"->False,
"S82BlindLabelsUsed"->False,
"StableFrozenArchitectureHash"->stableFrozenArchitectureHash82C,
"PreflightPassed"->preflightPassed82C
|>;

If[
!TrueQ[preflightPassed82C],
Print[Dataset[{preflight82C}]];
Print["S82C aborted: frozen architecture or intervention mismatch."];
Abort[]
];

Dataset[{preflight82C}]
'''.strip() + "\n"

cell2 = r'''
ClearAll[
CaseByGrammar82C,
NodeRole82C,
EncodePairWithK82C,
StateBagComponents82C,
StateBagProfile82C,
PairBagProfile82C,
PrepareCapacityRow82C,
CandidateToken82C,
TokenizedRows82C,
SafePolicy82C,
ScoreRows82C,
EvaluateCapacityCandidate82C
];

legacyGrammars82C={
"S59","ChainIn","SharedMerge","ParallelIn",
"ParallelOut","DiamondIn","SharedParallelIn"
};
legacyDepths82C={2,5,9,15};
stressFitDepths82C={2,5};
stressValidationDepths82C={9,15};
kValues82C=Range[5,23];

kCandidates82C=Map[
Function[k,
<|
"Name"->("K"<>ToString[k]<>"ExactRole"),
"Type"->"KExactRole",
"K"->k,
"Priority"->k-5,
"ProductionEligible"->True
|>
],
kValues82C
];

profileCandidates82C={
<|
"Name"->"K5ExactRolePlusBagProfile",
"Type"->"CodePlusBagProfile",
"K"->5,
"Priority"->100,
"ProductionEligible"->True
|>,
<|
"Name"->"ExactRoleBagProfileOnly",
"Type"->"BagProfileOnly",
"K"->Missing["NotApplicable"],
"Priority"->101,
"ProductionEligible"->True
|>,
<|
"Name"->"ExactRoleRawPairDiagnostic",
"Type"->"RawPair",
"K"->Missing["NotApplicable"],
"Priority"->1000,
"ProductionEligible"->False
|>
};

capacityCandidates82C=Join[
kCandidates82C,
profileCandidates82C
];

protocol82C=<|
"Stage"->"S82C",
"Name"->"RepresentationCapacityDiagnosis",
"Purpose"->"SeparateModuloCapacityFromFeatureInsufficiency",
"LegacyGrammars"->legacyGrammars82C,
"LegacyDepths"->legacyDepths82C,
"LegacyExpectedCases"->224,
"StressFitDepths"->stressFitDepths82C,
"StressValidationDepths"->stressValidationDepths82C,
"KScan"->kValues82C,
"AdditionalRepresentations"->{
"ExactRolePlusUncompressedBagProfile",
"ExactRoleUncompressedBagProfileOnly",
"ExactRoleFullRawPairDiagnosticOnly"
},
"RawPairCandidateMayBeFrozen"->False,
"SelectionRule"->
"AllLegacyAndStressPerfectThenProductionEligibleThenMinimumPriorityThenMinimumPolicyLength",
"UsesS82BlindDepths"->False,
"UsesS82BlindRows"->False,
"UsesS82BlindLabels"->False,
"RerunsS76ThroughS82"->False,
"FutureBlindStage"->"S83"
|>;

protocolHash82C=Hash[Normal[protocol82C],"SHA256","HexString"];
modelHashBefore82C=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashBefore82C=Hash[CoreDefinitionBundle82C[],"SHA256","HexString"];
coreTextHashBefore82C=minimalKernelDefinitionTextHash82C;
canonicalizerHashBefore82C=canonicalizerImplementationHash79B;
interventionHashBefore82C=interventionImplementationHash82;
protocolHashBefore82C=protocolHash82C;

Dataset[{Join[
protocol82C,
<|
"CandidateCount"->Length[capacityCandidates82C],
"ProtocolHash"->protocolHash82C,
"NoCaseEvaluatedBeforeProtocolHash"->True
|>
]}]
'''.strip() + "\n"

cell3 = r'''
CaseByGrammar82C[
grammar_String,depth_Integer,answer_Integer,target_String
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

NodeRole82C[originalNode_,case_List,answer_Integer]:=Module[
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

EncodePairWithK82C[pair_List,k_Integer]:=
EncodePairWithK82C[pair,k]=Module[{encoded},
encoded=First@EncodeRows75[
{<|
"Grammar"->"S82CCapacityObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozen75D["Params"],k
];
First[encoded["Codes"]]
];

StateBagComponents82C[state_]:=If[
MatchQ[state,{_Integer,_Integer}],
<|"Leaves"->{state},"Branches"->{}|>,
Module[{parts},
parts=StateBagComponents82C/@Join[
{state[[1]]},state[[2]],state[[3]]
];
<|
"Leaves"->Flatten[Lookup[parts,"Leaves"],1],
"Branches"->Join[
{{Length[state[[2]]],Length[state[[3]]]}},
Flatten[Lookup[parts,"Branches"],1]
]
|>
]
];

StateBagProfile82C[state_]:=Module[{components},
components=StateBagComponents82C[state];
{
Sort[components["Leaves"]],
Sort[components["Branches"]]
}
];

PairBagProfile82C[pair_List]:={
StateBagProfile82C[pair[[1]]],
StateBagProfile82C[pair[[2]]]
};

PrepareCapacityRow82C[
grammar_String,depth_Integer,answer_Integer,target_String,case_List
]:=Module[
{
canonicalization,canonicalCase,trace,levels,pack,vertexList,
packedNodes,observations,originalNode,pair,roleInfo
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
roleInfo=NodeRole82C[originalNode,canonicalCase,answer];
<|
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"RawPair"->pair,
"RawPairHash"->Hash[pair,"SHA256","HexString"],
"BagProfile"->PairBagProfile82C[pair]
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
"Observations"->observations
|>
];

CandidateToken82C[
observation_Association,
candidate_Association
]:=Module[{role,type,k,pair,profile},
role=observation["Role"];
type=candidate["Type"];
k=candidate["K"];
pair=observation["RawPair"];
profile=observation["BagProfile"];
Switch[
type,
"KExactRole",{role,EncodePairWithK82C[pair,k]},
"CodePlusBagProfile",{role,EncodePairWithK82C[pair,k],profile},
"BagProfileOnly",{role,profile},
"RawPair",{role,pair},
_,$Failed
]
];

TokenizedRows82C[rows_List,candidate_Association]:=Map[
Function[row,
Join[
KeyTake[row,{"Grammar","Depth","Answer","Target"}],
<|
"Tokens"->DeleteDuplicates[
CandidateToken82C[#,candidate]&/@row["Observations"]
]
|>
]
],
rows
];

SafePolicy82C[tokenRows_List]:=Module[
{continueRows,stopRows,continueTokens,stopTokens},
continueRows=Select[tokenRows,SameQ[#["Target"],"Continue"]&];
stopRows=Select[tokenRows,SameQ[#["Target"],"Stop"]&];
continueTokens=Union@@Lookup[continueRows,"Tokens"];
stopTokens=Union@@Lookup[stopRows,"Tokens"];
Complement[continueTokens,stopTokens]
];

ScoreRows82C[tokenRows_List,policy_List]:=Count[
tokenRows,
row_/;SameQ[
If[AnyTrue[row["Tokens"],MemberQ[policy,#]&],"Continue","Stop"],
row["Target"]
]
];

legacyRows82C=Flatten[
Table[
PrepareCapacityRow82C[
grammar,depth,answer,target,
CaseByGrammar82C[grammar,depth,answer,target]
],
{grammar,legacyGrammars82C},
{depth,legacyDepths82C},
{answer,Range[4]},
{target,{"Continue","Stop"}}
],
3
];

stressFitRows82C=Flatten[
Table[
PrepareCapacityRow82C[
"LocalMediatorDevelopment",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,stressFitDepths82C},
{answer,Range[4]}
],
1
];

stressValidationRows82C=Flatten[
Table[
PrepareCapacityRow82C[
"LocalMediatorValidation",depth,answer,"Stop",
ApplyEdgePatch81[
Case59[depth,answer,"Continue"],
LocalMediatorPatch82[depth,answer]
]
],
{depth,stressValidationDepths82C},
{answer,Range[4]}
],
1
];

EvaluateCapacityCandidate82C[candidate_Association]:=Module[
{
legacyTokens,fitTokens,validationTokens,policy,
legacyScore,fitScore,validationScore,allFit,
continueTokens,stopTokens,conflicts
},
legacyTokens=TokenizedRows82C[legacyRows82C,candidate];
fitTokens=TokenizedRows82C[stressFitRows82C,candidate];
validationTokens=TokenizedRows82C[stressValidationRows82C,candidate];
allFit=Join[legacyTokens,fitTokens];
policy=SafePolicy82C[allFit];
legacyScore=ScoreRows82C[legacyTokens,policy];
fitScore=ScoreRows82C[fitTokens,policy];
validationScore=ScoreRows82C[validationTokens,policy];
continueTokens=Union@@Lookup[
Select[allFit,SameQ[#["Target"],"Continue"]&],"Tokens"
];
stopTokens=Union@@Lookup[
Select[allFit,SameQ[#["Target"],"Stop"]&],"Tokens"
];
conflicts=Intersection[continueTokens,stopTokens];
Join[
candidate,
<|
"Policy"->policy,
"PolicyLength"->Length[policy],
"SemanticConflictTokenCount"->Length[conflicts],
"LegacyScore"->legacyScore,
"LegacyCases"->Length[legacyTokens],
"StressFitScore"->fitScore,
"StressFitCases"->Length[fitTokens],
"StressValidationScore"->validationScore,
"StressValidationCases"->Length[validationTokens],
"Perfect"->And[
SameQ[legacyScore,Length[legacyTokens]],
SameQ[fitScore,Length[fitTokens]],
SameQ[validationScore,Length[validationTokens]]
]
|>
]
];

capacityResults82C=EvaluateCapacityCandidate82C/@capacityCandidates82C;
perfectCandidates82C=Select[capacityResults82C,TrueQ[#["Perfect"]]&];
productionPerfect82C=Select[
perfectCandidates82C,
TrueQ[#["ProductionEligible"]]&
];
selectedCapacityCandidate82C=If[
Length[productionPerfect82C]>0,
First@SortBy[
productionPerfect82C,
{#["Priority"],#["PolicyLength"],#["Name"]}&
],
Missing["NoProductionCandidate"]
];

kPerfect82C=Select[
perfectCandidates82C,
SameQ[#["Type"],"KExactRole"]&
];
bagPerfect82C=Select[
perfectCandidates82C,
MemberQ[{"CodePlusBagProfile","BagProfileOnly"},#["Type"]]&
];
rawPairResult82C=First@Select[
capacityResults82C,
SameQ[#["Type"],"RawPair"]&
];

bottleneckDiagnosis82C=Which[
Length[kPerfect82C]>0,
"MODULO_CODEBOOK_CAPACITY_BOTTLENECK",
Length[bagPerfect82C]>0,
"K5_ENCODER_COMPRESSION_LOSES_STRUCTURAL_PROFILE",
TrueQ[rawPairResult82C["Perfect"]],
"COMPACT_FEATURES_INSUFFICIENT_RAW_STATE_SUFFICIENT",
True,
"RAW_STATE_SEMANTIC_CONFLICT_OR_POLICY_FORM_INSUFFICIENT"
];

dataSummary82C=<|
"LegacyCases"->Length[legacyRows82C],
"StressFitCases"->Length[stressFitRows82C],
"StressValidationCases"->Length[stressValidationRows82C],
"AllRowsTerminatedNaturally"->And@@Lookup[
Join[legacyRows82C,stressFitRows82C,stressValidationRows82C],
"TerminatedNaturally"
],
"RowsHitSafetyCap"->Count[
Join[legacyRows82C,stressFitRows82C,stressValidationRows82C],
row_/;TrueQ[row["HitSafetyCap"]]
]
|>;

Column[{
Dataset[{dataSummary82C}],
Dataset[Map[
KeyDrop[#,"Policy"]&,
capacityResults82C
]],
Dataset[{<|
"PerfectCandidateCount"->Length[perfectCandidates82C],
"ProductionPerfectCandidateCount"->Length[productionPerfect82C],
"SmallestPerfectK"->If[
Length[kPerfect82C]>0,
Min@Lookup[kPerfect82C,"K"],
Missing["NoPerfectK"]
],
"RawPairPerfect"->rawPairResult82C["Perfect"],
"BottleneckDiagnosis"->bottleneckDiagnosis82C
|>}]
}]
'''.strip() + "\n"

cell4 = r'''
modelHashAfter82C=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter82C=Hash[CoreDefinitionBundle82C[],"SHA256","HexString"];
coreTextHashAfter82C=Hash[
ToString[InputForm[CoreDefinitionBundle82C[]]],
"SHA256","HexString"
];
canonicalizerHashAfter82C=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter82C=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
protocolHashAfter82C=Hash[Normal[protocol82C],"SHA256","HexString"];

integrityPassed82C=And[
SameQ[modelHashBefore82C,modelHashAfter82C],
SameQ[modelHashAfter82C,expectedFrozenModelHash79A],
SameQ[coreHashBefore82C,coreHashAfter82C],
SameQ[coreTextHashBefore82C,coreTextHashAfter82C],
SameQ[
coreTextHashAfter82C,
expectedMinimalKernelDefinitionTextHash82C
],
SameQ[canonicalizerHashBefore82C,canonicalizerHashAfter82C],
SameQ[canonicalizerHashAfter82C,expectedCanonicalizerHash82C],
SameQ[interventionHashBefore82C,interventionHashAfter82C],
SameQ[interventionHashAfter82C,expectedInterventionHash82C],
SameQ[protocolHashBefore82C,protocolHashAfter82C]
];

diagnosticValidityPassed82C=And[
TrueQ[preflightPassed82C],
TrueQ[integrityPassed82C],
SameQ[Length[legacyRows82C],224],
SameQ[Length[stressFitRows82C],8],
SameQ[Length[stressValidationRows82C],8],
TrueQ[dataSummary82C["AllRowsTerminatedNaturally"]],
SameQ[dataSummary82C["RowsHitSafetyCap"],0]
];

selectionSucceeded82C=And[
TrueQ[diagnosticValidityPassed82C],
AssociationQ[selectedCapacityCandidate82C],
TrueQ[selectedCapacityCandidate82C["Perfect"]],
TrueQ[selectedCapacityCandidate82C["ProductionEligible"]]
];

frozenCandidate82C=If[
TrueQ[selectionSucceeded82C],
<|
"Stage"->"S82C",
"Name"->"CapacityRepairedQueryRoleCandidate",
"BaseFrozenModelHash"->expectedFrozenModelHash79A,
"EncoderParams"->frozen75D["Params"],
"Representation"->selectedCapacityCandidate82C["Type"],
"K"->selectedCapacityCandidate82C["K"],
"Policy"->selectedCapacityCandidate82C["Policy"],
"ExactNodeRoleUsed"->True,
"S82BlindLabelsUsedForSelection"->False,
"FrozenBeforeS83"->True
|>,
Missing["NoCandidateFrozen"]
];

candidateHash82C=If[
AssociationQ[frozenCandidate82C],
Hash[Normal[frozenCandidate82C],"SHA256","HexString"],
Missing["NoCandidateHash"]
];

cert82C=<|
"Stage"->"S82C",
"Name"->"RepresentationCapacityDiagnosis",
"Meaning"->"PostS82DevelopmentNotBlindTest",
"CasesEvaluated"->240,
"CandidatesEvaluated"->Length[capacityResults82C],
"PerfectCandidateCount"->Length[perfectCandidates82C],
"ProductionPerfectCandidateCount"->Length[productionPerfect82C],
"SmallestPerfectK"->If[
Length[kPerfect82C]>0,
Min@Lookup[kPerfect82C,"K"],
Missing["NoPerfectK"]
],
"RawPairPerfect"->rawPairResult82C["Perfect"],
"BottleneckDiagnosis"->bottleneckDiagnosis82C,
"SelectedCandidate"->If[
AssociationQ[selectedCapacityCandidate82C],
selectedCapacityCandidate82C["Name"],
selectedCapacityCandidate82C
],
"SelectedRepresentation"->If[
AssociationQ[selectedCapacityCandidate82C],
selectedCapacityCandidate82C["Type"],
Missing["NoRepresentation"]
],
"SelectedK"->If[
AssociationQ[selectedCapacityCandidate82C],
selectedCapacityCandidate82C["K"],
Missing["NoK"]
],
"SelectedPolicyLength"->If[
AssociationQ[selectedCapacityCandidate82C],
selectedCapacityCandidate82C["PolicyLength"],
Missing["NoPolicy"]
],
"OriginalFrozenModelChanged"->!SameQ[
modelHashBefore82C,modelHashAfter82C
],
"CoreChanged"->!SameQ[coreHashBefore82C,coreHashAfter82C],
"CanonicalizerChanged"->!SameQ[
canonicalizerHashBefore82C,canonicalizerHashAfter82C
],
"InterventionChanged"->!SameQ[
interventionHashBefore82C,interventionHashAfter82C
],
"S82BlindRowsLoaded"->False,
"S82BlindLabelsUsed"->False,
"S82BlindTestRerun"->False,
"S82CIsBlindTest"->False,
"DiagnosticValidityPassed"->diagnosticValidityPassed82C,
"SelectionSucceeded"->selectionSucceeded82C,
"CandidateHash"->candidateHash82C,
"ReadyForNewS83BlindTest"->selectionSucceeded82C,
"SuggestedNextStage"->If[
TrueQ[selectionSucceeded82C],
"S83_FREEZE_CAPACITY_REPAIRED_CANDIDATE_THEN_NEW_BLIND_INTERVENTION",
"S82D_QUERY_RELATIVE_STRUCTURAL_FEATURE_DESIGN"
]
|>;

Dataset[{cert82C}]
'''.strip() + "\n"

cells = [cell1, cell2, cell3, cell4]
wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)

for forbidden in (
    "blindDepths82=",
    "blindCounterfactualPairs82=",
    "PrepareBlindCounterfactualPair82",
    "EvaluateArchitecture82",
    "{31,63}",
):
    if forbidden in wl_source:
        raise RuntimeError(f"S82 blind material leaked into S82C: {forbidden}")

WL_OUTPUT.write_text(wl_source, encoding="utf-8")

notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "s82c-intro",
            "metadata": {},
            "source": [
                "# TCCT S82C — Representation Capacity Diagnosis\n",
                "\n",
                "本阶段诊断 S82B 的角色表示为何仍冲突：扫描 K=5..23，并比较未压缩结构 bag profile 与完整 raw pair。\n",
                "\n",
                "不读取或重跑 S82 盲测；完整 raw pair 仅用于证明信息是否充分，禁止直接冻结。真正的新能力验证仍保留给 S83。\n",
            ],
        },
        *[
            {
                "cell_type": "code",
                "id": f"s82c-code-{index}",
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
