import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S87_NOTEBOOK = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind.ipynb"
WL_OUTPUT = ROOT / "TCCT_S87A_SevenBranchFailureAudit.wl"
NB_OUTPUT = ROOT / "TCCT_S87A_SevenBranchFailureAudit.ipynb"
MARKER = "(* S87A CELL *)"


def load_code_cells(path: Path) -> list[str]:
    notebook = json.loads(path.read_text(encoding="utf-8"))
    return [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]


def check_wl_delimiters(source: str) -> None:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[tuple[str, int]] = []
    in_string = False
    escaped = False
    comment_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            if char == "(" and next_char == "*":
                comment_depth += 1
                index += 2
                continue
            if char == "*" and next_char == ")":
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "(" and next_char == "*":
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in ")]}":
            if not stack or stack[-1][0] != pairs[char]:
                raise RuntimeError(f"unbalanced Wolfram delimiter {char} at {index}")
            stack.pop()
        index += 1
    if in_string or comment_depth or stack:
        raise RuntimeError(
            f"unterminated Wolfram source: string={in_string}, "
            f"comment_depth={comment_depth}, stack_tail={stack[-3:]}"
        )


s87_cells = load_code_cells(S87_NOTEBOOK)
if len(s87_cells) != 5:
    raise RuntimeError("S87 notebook no longer has exactly five code cells")

# Reuse only the frozen architecture, preflight, and protocol/definition cells.
# The revealed S87 runtime cell is intentionally not rerun. S87A reconstructs
# the same worlds once with extra read-only observations for failure diagnosis.
architecture_cell, preflight_cell, definition_cell = [
    cell.strip() + "\n" for cell in s87_cells[:3]
]

audit_definitions_cell = r'''
ClearAll[
EncodePairForK87A,
ObservationTokenForK87A,
PrepareWorld87A,
PrepareScenario87A,
TokensForKey87A,
ContinueTokensForKey87A,
StopTokensForKey87A,
SafePolicyForKey87A,
SharedTokensForKey87A,
ScoreWorldsForKey87A,
S87AAuditDefinitionBundle
];

expectedS87ProtocolHash87A=
"0c6f158cf154f8a89618a41d25c3ff7fc6e37f2f5b2c1a4db31d32f1666512c1";
lockedS87BlindResultHash87A=
"e1ae2e5a44061354afdc3204ad8103eaa64144a7fc5de635bafc215709bfec95";

encodeCache87A=<||>;

EncodePairForK87A[pair_List,k_Integer]:=Module[{key,cached,encoded,code},
key=Hash[{pair,k},"SHA256","HexString"];
cached=Lookup[encodeCache87A,key,Missing["NotCached"]];
If[!MissingQ[cached],Return[cached]];
encoded=First@EncodeRows75[
{<|
"Grammar"->"S87ARevealedAuditObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled",
"StatePairs"->{pair}
|>},
frozenCandidate86E["EncoderParams"],k
];
code=First[encoded["Codes"]];
AssociateTo[encodeCache87A,key->code];
code
];

ObservationTokenForK87A[observation_Association,k_Integer]:={
observation["Role"],EncodePairForK87A[observation["RawPair"],k]
};

PrepareWorld87A[
topology_String,
depth_Integer,
interventionPair_List,
graphCondition_String,
answer_Integer,
target_String,
baseCase_List
]:=Module[
{
topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,
observations,originalNode,pair,roleInfo,rawTokens,k33Tokens,prediction
},
topologyCase=TopologyTransform87[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions87[topology,baseCase];
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
roleInfo=NodeRole87[originalNode,canonicalCase,answer];
<|
"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"RawPair"->pair,
"Code"->EncodePair87[pair]
|>
],
packedNodes
];
rawTokens=DeleteDuplicates[({#1["Role"],#1["RawPair"]}&)/@observations];
k33Tokens=DeleteDuplicates[({#1["Role"],#1["Code"]}&)/@observations];
prediction=PredictTokens87[k33Tokens];
<|
"Topology"->topology,
"Depth"->depth,
"InterventionPair"->interventionPair,
"GraphCondition"->graphCondition,
"Answer"->answer,
"Target"->target,
"ReferenceAction"->ReferenceAction87[canonicalCase],
"BranchCount"->Length[canonicalCase[[1,6]]],
"Prediction"->prediction,
"Correct"->SameQ[prediction,target],
"TopologyGraphHash"->Hash[topologyCase[[1,1]],"SHA256","HexString"],
"CanonicalGraphHash"->Hash[canonicalCase[[1,1]],"SHA256","HexString"],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[
canonicalization["Contractions"],expectedContractions
],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"StateObservationCount"->Length[observations],
"RawTokenCount"->Length[observations],
"TokenCount"->Length[k33Tokens],
"DuplicateTokensRemoved"->Length[observations]-Length[k33Tokens],
"PolicyHitTokens"->Intersection[k33Tokens,frozenCandidate86E["Policy"]],
"Observations"->observations,
"RawExactTokens"->rawTokens,
"K33Tokens"->k33Tokens,
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],
"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds
|>
];

PrepareScenario87A[
topology_String,depth_Integer,interventionPair_List
]:=Module[
{
branchCount=7,seedCase,patch,hybridSeed,baseWorlds,hybridWorlds,
worldPairs,baseGraphHashes,hybridGraphHashes
},
seedCase=Case87[depth,1,"Continue"];
patch=MixedPathCutStopPatch87[seedCase,interventionPair];
hybridSeed=ApplyEdgePatch81[seedCase,patch];
If[SameQ[hybridSeed,$Failed],Return[$Failed]];
baseWorlds=Table[
PrepareWorld87A[
topology,depth,interventionPair,"Baseline",answer,"Continue",
SetAnswer87[seedCase,answer]
],
{answer,Range[branchCount]}
];
hybridWorlds=Table[
PrepareWorld87A[
topology,depth,interventionPair,"MixedPathCutStopIntervention",answer,
If[SameQ[answer,Last[interventionPair]],"Stop","Continue"],
SetAnswer87[hybridSeed,answer]
],
{answer,Range[branchCount]}
];
worldPairs=MapThread[
Function[{base,hybrid},
<|
"Answer"->base["Answer"],
"StopPatchedQuery"->SameQ[Last[interventionPair],base["Answer"]],
"SameQuery"->SameQ[base["Answer"],hybrid["Answer"]],
"ReferenceRelationCorrect"->If[
SameQ[Last[interventionPair],base["Answer"]],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Stop"]
],
And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[hybrid["ReferenceAction"],"Continue"]
]
],
"PredictionRelationCorrect"->If[
SameQ[Last[interventionPair],base["Answer"]],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Stop"]
],
And[
SameQ[base["Prediction"],"Continue"],
SameQ[hybrid["Prediction"],"Continue"]
]
],
"PairCorrect"->And[TrueQ[base["Correct"]],TrueQ[hybrid["Correct"]]],
"BaselineWorld"->base,
"InterventionWorld"->hybrid
|>
],
{baseWorlds,hybridWorlds}
];
baseGraphHashes=Lookup[baseWorlds,"TopologyGraphHash"];
hybridGraphHashes=Lookup[hybridWorlds,"TopologyGraphHash"];
<|
"Topology"->topology,
"Depth"->depth,
"InterventionPair"->interventionPair,
"MixedInterventionValidity"->patch["ComponentPatchesValid"],
"MixedInterventionNoConflict"->patch["NoCrossBranchConflict"],
"MixedEditCountCorrect"->patch["ExpectedEditCount"],
"BaselineSameGraphAcrossQueries"->SameQ@@baseGraphHashes,
"InterventionSameGraphAcrossQueries"->SameQ@@hybridGraphHashes,
"MixedInterventionChangesGraph"->UnsameQ[First[baseGraphHashes],First[hybridGraphHashes]],
"ReferenceRelationsCorrect"->And@@Lookup[worldPairs,"ReferenceRelationCorrect"],
"PredictionRelationsCorrect"->And@@Lookup[worldPairs,"PredictionRelationCorrect"],
"AllFourteenWorldsCorrect"->And@@Join[
Lookup[baseWorlds,"Correct"],Lookup[hybridWorlds,"Correct"]
],
"WorldPairs"->worldPairs,
"BaselineWorlds"->baseWorlds,
"InterventionWorlds"->hybridWorlds
|>
];

TokensForKey87A[world_Association,key_String]:=Switch[
key,
"RawExactTokens",world["RawExactTokens"],
"K33Tokens",world["K33Tokens"],
_,$Failed
];

ContinueTokensForKey87A[worlds_List,key_String]:=Union@@Map[
TokensForKey87A[#1,key]&,
Select[worlds,SameQ[#1["Target"],"Continue"]&]
];

StopTokensForKey87A[worlds_List,key_String]:=Union@@Map[
TokensForKey87A[#1,key]&,
Select[worlds,SameQ[#1["Target"],"Stop"]&]
];

SafePolicyForKey87A[worlds_List,key_String]:=Complement[
ContinueTokensForKey87A[worlds,key],
StopTokensForKey87A[worlds,key]
];

SharedTokensForKey87A[worlds_List,key_String]:=Intersection[
ContinueTokensForKey87A[worlds,key],
StopTokensForKey87A[worlds,key]
];

ScoreWorldsForKey87A[worlds_List,key_String,policy_List]:=Count[
worlds,
world_/;SameQ[
If[AnyTrue[TokensForKey87A[world,key],MemberQ[policy,#]&],"Continue","Stop"],
world["Target"]
]
];

S87AAuditDefinitionBundle[]:={
DownValues[EncodePairForK87A],DownValues[ObservationTokenForK87A],
DownValues[PrepareWorld87A],DownValues[PrepareScenario87A],
DownValues[TokensForKey87A],DownValues[ContinueTokensForKey87A],
DownValues[StopTokensForKey87A],DownValues[SafePolicyForKey87A],
DownValues[SharedTokensForKey87A],DownValues[ScoreWorldsForKey87A]
};

auditProtocol87A=<|
"Stage"->"S87A",
"Name"->"SevenBranchFailureAuditWithoutRetuning",
"AuditOnly"->True,
"S87AlreadyRevealed"->True,
"BlindClaimRun"->False,
"OriginalS87ProtocolHash"->protocolHash87,
"LockedS87BlindResultHash"->lockedS87BlindResultHash87A,
"CandidateHash"->candidateHashLoaded87,
"K"->33,
"RepresentationsCompared"->{"RawExactRole","K33ExactRole","FrozenK33Policy"},
"DiagnosticKScan"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"NewCandidateSelected"->False,
"NewKSelected"->False,
"PolicyEdited"->False,
"RetuningApplied"->False,
"CandidateExported"->False,
"S88Run"->False,
"TokenDeduplication"->"DeleteDuplicatesAfterExactRoleTokenConstruction",
"ExpectedS87DeterministicResult"-><|
"Scenarios"->28,"WorldPairs"->196,"Worlds"->392,
"BaselineCorrect"->0,"InterventionContinueCorrect"->0,
"InterventionStopCorrect"->20,"WorldCorrect"->20,
"PairCorrect"->0,"PredictionRelationsCorrect"->0,"ScenarioPerfect"->0
|>
|>;

auditProtocolHash87A=Hash[Normal[auditProtocol87A],"SHA256","HexString"];
auditDefinitionHashBefore87A=Hash[
S87AAuditDefinitionBundle[],"SHA256","HexString"
];

Dataset[{Join[auditProtocol87A,<|"AuditProtocolHash"->auditProtocolHash87A|>]}]
'''.strip() + "\n"

run_cell = r'''
auditScenarios87A=Flatten[
Table[
PrepareScenario87A[topology,depth,interventionPair],
{topology,blindTopologies87},
{depth,blindDepths87},
{interventionPair,blindInterventionPairs87}
],
2
];

auditWorldPairs87A=Flatten[Lookup[auditScenarios87A,"WorldPairs"],1];
baselineWorlds87A=Flatten[Lookup[auditScenarios87A,"BaselineWorlds"],1];
interventionWorlds87A=Flatten[Lookup[auditScenarios87A,"InterventionWorlds"],1];
allWorlds87A=Join[baselineWorlds87A,interventionWorlds87A];

reproducedSummary87A=<|
"Scenarios"->Length[auditScenarios87A],
"WorldPairs"->Length[auditWorldPairs87A],
"Worlds"->Length[allWorlds87A],
"MixedInterventionValidity"->Count[
auditScenarios87A,s_/;TrueQ[s["MixedInterventionValidity"]]
],
"MixedInterventionNoConflict"->Count[
auditScenarios87A,s_/;TrueQ[s["MixedInterventionNoConflict"]]
],
"MixedEditCountCorrect"->Count[
auditScenarios87A,s_/;TrueQ[s["MixedEditCountCorrect"]]
],
"ReferenceRelationsCorrect"->Count[
auditWorldPairs87A,p_/;TrueQ[p["ReferenceRelationCorrect"]]
],
"PredictionRelationsCorrect"->Count[
auditWorldPairs87A,p_/;TrueQ[p["PredictionRelationCorrect"]]
],
"PairCorrect"->Count[auditWorldPairs87A,p_/;TrueQ[p["PairCorrect"]]],
"ScenarioPerfect"->Count[
auditScenarios87A,s_/;TrueQ[s["AllFourteenWorldsCorrect"]]
],
"BaselineCorrect"->Count[baselineWorlds87A,w_/;TrueQ[w["Correct"]]],
"InterventionContinueCorrect"->Count[
interventionWorlds87A,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"InterventionStopCorrect"->Count[
interventionWorlds87A,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"WorldCorrect"->Count[allWorlds87A,w_/;TrueQ[w["Correct"]]],
"CanonicalCaseExactlyBase"->Count[
allWorlds87A,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
allWorlds87A,w_/;TrueQ[w["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
allWorlds87A,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"ReferenceActionsCorrect"->Count[
allWorlds87A,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"NonEmptyTokens"->Count[allWorlds87A,w_/;w["TokenCount"]>0],
"TerminatedNaturally"->Count[
allWorlds87A,w_/;TrueQ[w["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[allWorlds87A,w_/;TrueQ[w["HitSafetyCap"]]],
"SevenBranchWorlds"->Count[allWorlds87A,w_/;SameQ[w["BranchCount"],7]],
"TotalTraceSeconds"->Total[Lookup[allWorlds87A,"TraceSeconds"]]
|>;

rawSafePolicy87A=SafePolicyForKey87A[allWorlds87A,"RawExactTokens"];
k33SafePolicy87A=SafePolicyForKey87A[allWorlds87A,"K33Tokens"];
rawSharedTokens87A=SharedTokensForKey87A[allWorlds87A,"RawExactTokens"];
k33SharedTokens87A=SharedTokensForKey87A[allWorlds87A,"K33Tokens"];

rawSafeScore87A=ScoreWorldsForKey87A[
allWorlds87A,"RawExactTokens",rawSafePolicy87A
];
k33SafeScore87A=ScoreWorldsForKey87A[
allWorlds87A,"K33Tokens",k33SafePolicy87A
];
frozenPolicyScore87A=Count[allWorlds87A,w_/;TrueQ[w["Correct"]]];

representationAudit87A={
<|
"Representation"->"RawExactRole",
"Worlds"->Length[allWorlds87A],
"SafePolicyScore"->rawSafeScore87A,
"SafePolicyPerfect"->SameQ[rawSafeScore87A,Length[allWorlds87A]],
"ContinueTokenCount"->Length@ContinueTokensForKey87A[
allWorlds87A,"RawExactTokens"
],
"StopTokenCount"->Length@StopTokensForKey87A[allWorlds87A,"RawExactTokens"],
"SharedTokenCount"->Length[rawSharedTokens87A],
"SafePolicyLength"->Length[rawSafePolicy87A],
"AppliedToFrozenModel"->False
|>,
<|
"Representation"->"K33ExactRole",
"Worlds"->Length[allWorlds87A],
"SafePolicyScore"->k33SafeScore87A,
"SafePolicyPerfect"->SameQ[k33SafeScore87A,Length[allWorlds87A]],
"ContinueTokenCount"->Length@ContinueTokensForKey87A[allWorlds87A,"K33Tokens"],
"StopTokenCount"->Length@StopTokensForKey87A[allWorlds87A,"K33Tokens"],
"SharedTokenCount"->Length[k33SharedTokens87A],
"SafePolicyLength"->Length[k33SafePolicy87A],
"AppliedToFrozenModel"->False
|>,
<|
"Representation"->"FrozenK33Policy",
"Worlds"->Length[allWorlds87A],
"SafePolicyScore"->frozenPolicyScore87A,
"SafePolicyPerfect"->SameQ[frozenPolicyScore87A,Length[allWorlds87A]],
"ContinueTokenCount"->Missing["NotApplicable"],
"StopTokenCount"->Missing["NotApplicable"],
"SharedTokenCount"->Missing["NotApplicable"],
"SafePolicyLength"->Length[frozenCandidate86E["Policy"]],
"AppliedToFrozenModel"->True
|>
};

predictionAudit87A=<|
"ContinueTargets"->Count[allWorlds87A,w_/;SameQ[w["Target"],"Continue"]],
"StopTargets"->Count[allWorlds87A,w_/;SameQ[w["Target"],"Stop"]],
"PredictedContinue"->Count[
allWorlds87A,w_/;SameQ[w["Prediction"],"Continue"]
],
"PredictedStop"->Count[allWorlds87A,w_/;SameQ[w["Prediction"],"Stop"]],
"ZeroPolicyHitContinueTargets"->Count[
allWorlds87A,w_/;SameQ[w["Target"],"Continue"]&&Length[w["PolicyHitTokens"]]===0
],
"ZeroPolicyHitStopTargets"->Count[
allWorlds87A,w_/;SameQ[w["Target"],"Stop"]&&Length[w["PolicyHitTokens"]]===0
],
"PolicyHitContinueTargets"->Count[
allWorlds87A,w_/;SameQ[w["Target"],"Continue"]&&Length[w["PolicyHitTokens"]]>0
],
"PolicyHitStopTargets"->Count[
allWorlds87A,w_/;SameQ[w["Target"],"Stop"]&&Length[w["PolicyHitTokens"]]>0
]
|>;

diagnosis87A=Which[
rawSafeScore87A<Length[allWorlds87A],
"RAW_EXACT_ROLE_NOT_SEPARABLE",
k33SafeScore87A<Length[allWorlds87A]&&
frozenPolicyScore87A<k33SafeScore87A,
"K33_COLLISION_AND_FROZEN_POLICY_COVERAGE_GAP",
k33SafeScore87A<Length[allWorlds87A],
"K33_MODULO_COLLISION",
frozenPolicyScore87A<Length[allWorlds87A],
"FROZEN_POLICY_COVERAGE_GAP",
True,
"NO_REPRESENTATION_FAILURE_FOUND"
];

Column[{
Dataset[{reproducedSummary87A}],
Dataset[representationAudit87A],
Dataset[{predictionAudit87A}],
Dataset[{<|"Diagnosis"->diagnosis87A|>}]
}]
'''.strip() + "\n"

certificate_cell = r'''
modelHashAfter87A=Hash[Normal[frozen75D],"SHA256","HexString"];
candidateHashAfter87A=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
coreHashAfter87A=Hash[CoreDefinitionBundle87[],"SHA256","HexString"];
canonicalizerHashAfter87A=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter87A=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyHashAfter87A=Hash[
{DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"
];
testDefinitionHashAfter87A=Hash[
S87TestDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter87A=Hash[Normal[protocol87],"SHA256","HexString"];
auditProtocolHashAfter87A=Hash[
Normal[auditProtocol87A],"SHA256","HexString"
];
auditDefinitionHashAfter87A=Hash[
S87AAuditDefinitionBundle[],"SHA256","HexString"
];
k33CandidateFileHashAfter87A=FileHash[k33CandidatePath87,"SHA256"];
oldK19CandidateFileHashAfter87A=FileHash[oldK19CandidatePath87,"SHA256"];

originalFrozenModelUnchanged87A=And[
SameQ[modelHashBefore87,modelHashAfter87A],
SameQ[modelHashAfter87A,expectedFrozenModelHash79A]
];
frozenCandidateUnchanged87A=And[
SameQ[candidateHashBefore87,candidateHashAfter87A],
SameQ[candidateHashAfter87A,expectedCandidateHash87]
];
coreUnchanged87A=SameQ[coreHashBefore87,coreHashAfter87A];
canonicalizerUnchanged87A=And[
SameQ[canonicalizerHashBefore87,canonicalizerHashAfter87A],
SameQ[canonicalizerHashAfter87A,expectedCanonicalizerHash87]
];
interventionUnchanged87A=And[
SameQ[interventionHashBefore87,interventionHashAfter87A],
SameQ[interventionHashAfter87A,expectedInterventionHash87]
];
topologiesUnchanged87A=SameQ[topologyHashBefore87,topologyHashAfter87A];
originalS87DefinitionsUnchanged87A=SameQ[
testDefinitionHashBefore87,testDefinitionHashAfter87A
];
originalS87ProtocolUnchanged87A=And[
SameQ[protocolHash87,protocolHashAfter87A],
SameQ[protocolHashAfter87A,expectedS87ProtocolHash87A]
];
auditProtocolUnchanged87A=SameQ[
auditProtocolHash87A,auditProtocolHashAfter87A
];
auditDefinitionsUnchanged87A=SameQ[
auditDefinitionHashBefore87A,auditDefinitionHashAfter87A
];
deduplicationMechanismUnchanged87A=And[
TrueQ[coreUnchanged87A],
TrueQ[originalS87DefinitionsUnchanged87A],
SameQ[
protocol87["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleCodePairing"
],
SameQ[
auditProtocol87A["TokenDeduplication"],
"DeleteDuplicatesAfterExactRoleTokenConstruction"
]
];
k33CandidateFileUnchanged87A=SameQ[
k33CandidateFileHashBefore87,k33CandidateFileHashAfter87A
];
oldK19CandidateFileUnchanged87A=SameQ[
oldK19CandidateFileHashBefore87,oldK19CandidateFileHashAfter87A
];

expectedDeterministic87A=auditProtocol87A["ExpectedS87DeterministicResult"];
deterministicReproductionPassed87A=And[
SameQ[reproducedSummary87A["Scenarios"],expectedDeterministic87A["Scenarios"]],
SameQ[reproducedSummary87A["WorldPairs"],expectedDeterministic87A["WorldPairs"]],
SameQ[reproducedSummary87A["Worlds"],expectedDeterministic87A["Worlds"]],
SameQ[reproducedSummary87A["BaselineCorrect"],expectedDeterministic87A["BaselineCorrect"]],
SameQ[reproducedSummary87A["InterventionContinueCorrect"],expectedDeterministic87A["InterventionContinueCorrect"]],
SameQ[reproducedSummary87A["InterventionStopCorrect"],expectedDeterministic87A["InterventionStopCorrect"]],
SameQ[reproducedSummary87A["WorldCorrect"],expectedDeterministic87A["WorldCorrect"]],
SameQ[reproducedSummary87A["PairCorrect"],expectedDeterministic87A["PairCorrect"]],
SameQ[reproducedSummary87A["PredictionRelationsCorrect"],expectedDeterministic87A["PredictionRelationsCorrect"]],
SameQ[reproducedSummary87A["ScenarioPerfect"],expectedDeterministic87A["ScenarioPerfect"]]
];

auditValidityPassed87A=And[
TrueQ[preflightPassed87],
TrueQ[deterministicReproductionPassed87A],
SameQ[reproducedSummary87A["MixedInterventionValidity"],28],
SameQ[reproducedSummary87A["MixedInterventionNoConflict"],28],
SameQ[reproducedSummary87A["MixedEditCountCorrect"],28],
SameQ[reproducedSummary87A["ReferenceRelationsCorrect"],196],
SameQ[reproducedSummary87A["CanonicalCaseExactlyBase"],392],
SameQ[reproducedSummary87A["ContractionCountCorrect"],392],
SameQ[reproducedSummary87A["ProtectedNodesPreserved"],392],
SameQ[reproducedSummary87A["ReferenceActionsCorrect"],392],
SameQ[reproducedSummary87A["NonEmptyTokens"],392],
SameQ[reproducedSummary87A["TerminatedNaturally"],392],
SameQ[reproducedSummary87A["HitSafetyCap"],0],
SameQ[reproducedSummary87A["SevenBranchWorlds"],392],
TrueQ[originalFrozenModelUnchanged87A],
TrueQ[frozenCandidateUnchanged87A],
TrueQ[coreUnchanged87A],
TrueQ[canonicalizerUnchanged87A],
TrueQ[interventionUnchanged87A],
TrueQ[topologiesUnchanged87A],
TrueQ[originalS87DefinitionsUnchanged87A],
TrueQ[originalS87ProtocolUnchanged87A],
TrueQ[auditProtocolUnchanged87A],
TrueQ[auditDefinitionsUnchanged87A],
TrueQ[deduplicationMechanismUnchanged87A],
TrueQ[k33CandidateFileUnchanged87A],
TrueQ[oldK19CandidateFileUnchanged87A]
];

cert87A=<|
"Stage"->"S87A",
"Name"->"SevenBranchFailureAuditWithoutRetuning",
"AuditOnly"->True,
"AuditValidityPassed"->auditValidityPassed87A,
"S87DeterministicResultReproduced"->deterministicReproductionPassed87A,
"LockedS87BlindResultHash"->lockedS87BlindResultHash87A,
"S87ProtocolHash"->protocolHashAfter87A,
"AuditProtocolHash"->auditProtocolHashAfter87A,
"WorldsAudited"->Length[allWorlds87A],
"FrozenPolicyScore"->frozenPolicyScore87A,
"RawExactRoleScore"->rawSafeScore87A,
"RawExactRolePerfect"->SameQ[rawSafeScore87A,Length[allWorlds87A]],
"K33SafePolicyScore"->k33SafeScore87A,
"K33SafePolicyPerfect"->SameQ[k33SafeScore87A,Length[allWorlds87A]],
"RawSharedTokenCount"->Length[rawSharedTokens87A],
"K33SharedTokenCount"->Length[k33SharedTokens87A],
"Diagnosis"->diagnosis87A,
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged87A],
"FrozenCandidateChanged"->!TrueQ[frozenCandidateUnchanged87A],
"CoreChanged"->!TrueQ[coreUnchanged87A],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged87A],
"InterventionChanged"->!TrueQ[interventionUnchanged87A],
"TopologyImplementationsChanged"->!TrueQ[topologiesUnchanged87A],
"OriginalS87DefinitionsChanged"->!TrueQ[originalS87DefinitionsUnchanged87A],
"OriginalS87ProtocolChanged"->!TrueQ[originalS87ProtocolUnchanged87A],
"DeduplicationMechanismChanged"->!TrueQ[deduplicationMechanismUnchanged87A],
"CandidateFileChanged"->!TrueQ[k33CandidateFileUnchanged87A],
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DiagnosticKScan"->False,
"NewCandidateSelected"->False,
"NewKSelected"->False,
"PolicyEdited"->False,
"RetuningApplied"->False,
"CandidateExported"->False,
"S87LabelsUsedForDiagnosisOnly"->True,
"S87LabelsAppliedToFrozenModel"->False,
"BlindClaimRun"->False,
"MayReplaceS87BlindResult"->False,
"TotalTraceSeconds"->reproducedSummary87A["TotalTraceSeconds"],
"Outcome"->If[
TrueQ[auditValidityPassed87A],
"S87A_VALID_FAILURE_DIAGNOSIS_NO_RETUNING",
"S87A_INVALID_AUDIT"
],
"SuggestedNextStage"->If[
TrueQ[auditValidityPassed87A],
"S87B_DESIGN_RESEARCH_BRANCH_FROM_DIAGNOSIS",
"FIX_S87A_HARNESS_ONLY"
]
|>;

Dataset[{cert87A}]
'''.strip() + "\n"

cells = [
    architecture_cell,
    preflight_cell,
    definition_cell,
    audit_definitions_cell,
    run_cell,
    certificate_cell,
]

combined = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
for cell_number, cell in enumerate(cells, start=1):
    try:
        check_wl_delimiters(cell)
    except RuntimeError as exc:
        raise RuntimeError(f"S87A code cell {cell_number}: {exc}") from exc
for forbidden in (
    'AssociateTo[frozenCandidate86E',
    'frozenCandidate86E["K"]=',
    'frozenCandidate86E["Policy"]=',
    'Export[k33CandidatePath87',
):
    if forbidden in combined:
        raise RuntimeError(f"forbidden frozen-candidate mutation found: {forbidden}")

for required in (
    '"AuditOnly"->True',
    '"CandidateSearchRun"->False',
    '"NewKSelected"->False',
    '"PolicyEdited"->False',
    '"CandidateExported"->False',
    '"MayReplaceS87BlindResult"->False',
    '"DeduplicationMechanismChanged"->!TrueQ[deduplicationMechanismUnchanged87A]',
):
    if required not in combined:
        raise RuntimeError(f"missing S87A safety guard: {required}")

WL_OUTPUT.write_text(combined + "\n", encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S87A - Seven-Branch Failure Audit (No Retuning)\n",
        "\n",
        "S87 is already revealed and remains a valid blind failure. This audit "
        "reconstructs the same 392 worlds once, retaining raw observations so "
        "that raw-state separability, K=33 collisions, and frozen-policy coverage "
        "can be distinguished.\n",
        "\n",
        "This is not a new blind test. It performs no training, K search, policy "
        "edit, candidate selection, export, or retuning. The original core, "
        "canonicalizer, intervention, topology, deduplication rule, and frozen "
        "candidate are hash-locked.\n",
        "\n",
        "Use **Kernel -> Restart Kernel and Run All Cells**. The long cell should "
        "take roughly as long as S87 because it traces the same worlds once.\n",
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
            "file_extension": ".wl",
            "mimetype": "application/vnd.wolfram.mathematica",
            "name": "Wolfram Language",
            "pygments_lexer": "mathematica",
            "version": "15.0",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

NB_OUTPUT.write_text(
    json.dumps(notebook, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(WL_OUTPUT)
print(NB_OUTPUT)
