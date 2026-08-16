import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S88_SOURCE = ROOT / "TCCT_S88_EightBranchFrozenDecoderBlind.wl"
WL_OUTPUT = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind.wl"
NB_OUTPUT = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind.ipynb"
PREFLIGHT_WL_OUTPUT = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind_Preflight.wl"
PREFLIGHT_NB_OUTPUT = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind_Preflight.ipynb"
PRECOMMIT_OUTPUT = ROOT / "TCCT_S89_Precommit.json"
LAUNCHER_OUTPUT = ROOT / "Start_TCCT_S89_Jupyter.cmd"
MARKER = "(* S88 CELL *)"
NEW_MARKER = "(* S89 CELL *)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_cells(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    parts = source.split(MARKER)
    cells = [part.strip() + "\n" for part in parts[1:] if part.strip()]
    if len(cells) != 5:
        raise RuntimeError(f"expected five S88 source cells, found {len(cells)}")
    return cells


def rename_suffix_outside_strings(source: str, old: str, new: str) -> str:
    result: list[str] = []
    index = 0
    in_string = False
    escaped = False
    comment_depth = 0
    while index < len(source):
        char = source[index]
        next_char = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            result.append(char)
            if char == "(" and next_char == "*":
                result.append(next_char)
                comment_depth += 1
                index += 2
                continue
            if char == "*" and next_char == ")":
                result.append(next_char)
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            result.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "(" and next_char == "*":
            result.extend((char, next_char))
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            result.append(char)
            in_string = True
            index += 1
            continue
        if char.isalpha() or char == "$":
            end = index + 1
            while end < len(source) and (
                source[end].isalnum() or source[end] == "$"
            ):
                end += 1
            token = source[index:end]
            if token.endswith(old):
                token = token[: -len(old)] + new
            result.append(token)
            index = end
            continue
        result.append(char)
        index += 1
    return "".join(result)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    start_index = source.find(start)
    end_index = source.find(end, start_index)
    if start_index < 0 or end_index < 0:
        raise RuntimeError(f"replacement boundary missing: {start!r} -> {end!r}")
    return source[:start_index] + replacement.rstrip() + "\n\n" + source[end_index:]


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
            "unterminated Wolfram source: "
            f"string={in_string}, comment_depth={comment_depth}, "
            f"stack_tail={stack[-3:]}"
        )


s88_cells = split_cells(S88_SOURCE)
architecture_cell = s88_cells[0]

preflight_cell = rename_suffix_outside_strings(s88_cells[1], "88", "89")
preflight_cell = preflight_cell.replace(
    "TCCT_S88_BlindResultCertificate.json",
    "TCCT_S89_BlindResultCertificate.json",
)
preflight_cell = preflight_cell.replace(
    "s88ResultCertificatePath", "s89ResultCertificatePath"
)
preflight_cell = preflight_cell.replace("S88 aborted", "S89 aborted")
preflight_cell = preflight_cell.replace("prior S88 result", "prior S89 result")
preflight_cell = preflight_cell.replace('"Stage"->"S88"', '"Stage"->"S89"')
preflight_cell = preflight_cell.replace(
    '"Name"->"EightBranchFrozenDecoderBlind"',
    '"Name"->"StopRelocationCounterfactualBlind"',
)
preflight_cell = preflight_cell.replace(
    '"S88ResultAlreadyPresent"', '"S89ResultAlreadyPresent"'
)
preflight_cell = replace_once(
    preflight_cell,
    'expectedFreezeCertificateFileHash89=\n'
    '"7c83717fc5bf50b1bde853401da8d0fc5931d6b1b23663d75777e1e45516fb8e";',
    'expectedFreezeCertificateFileHash89=\n'
    '"7c83717fc5bf50b1bde853401da8d0fc5931d6b1b23663d75777e1e45516fb8e";\n'
    'expectedS88CheckpointFileHash89=\n'
    '"1c56bb0a87eba871f8474a93d4206d6aebbf1d66412a0d3927e62155a81e2fa4";',
    "S89 expected S88 checkpoint hash",
)
preflight_cell = replace_once(
    preflight_cell,
    'freezeCertificatePath89="E:/engine_wolf/TCCT_S87D_FreezeCertificate.json";',
    'freezeCertificatePath89="E:/engine_wolf/TCCT_S87D_FreezeCertificate.json";\n'
    's88CheckpointPath89="E:/engine_wolf/TCCT_S88_BlindResultCertificate.json";',
    "S89 checkpoint path",
)
preflight_cell = replace_once(
    preflight_cell,
    'decoderCandidatePath89,freezeCertificatePath89\n}',
    'decoderCandidatePath89,freezeCertificatePath89,s88CheckpointPath89\n}',
    "S89 required input list",
)
preflight_cell = replace_once(
    preflight_cell,
    'freezeCertificateFileHashBefore89=FileSHA256Hex89[freezeCertificatePath89];',
    'freezeCertificateFileHashBefore89=FileSHA256Hex89[freezeCertificatePath89];\n'
    's88CheckpointFileHashBefore89=FileSHA256Hex89[s88CheckpointPath89];',
    "S89 S88 checkpoint pre-hash",
)
preflight_cell = replace_once(
    preflight_cell,
    'freezeCertificate89=Quiet@Check[\nImport[freezeCertificatePath89,"RawJSON"],\n$Failed\n];',
    'freezeCertificate89=Quiet@Check[\nImport[freezeCertificatePath89,"RawJSON"],\n$Failed\n];\n\n'
    's88Checkpoint89=Quiet@Check[\nImport[s88CheckpointPath89,"RawJSON"],\n$Failed\n];',
    "S89 checkpoint import",
)
preflight_cell = replace_once(
    preflight_cell,
    'TrueQ[freezeCertificate89["S88DataReadBeforeFreeze"]===False],\n'
    '!FileExistsQ[s89ResultCertificatePath]',
    'TrueQ[freezeCertificate89["S88DataReadBeforeFreeze"]===False],\n'
    'AssociationQ[s88Checkpoint89],\n'
    'SameQ[s88CheckpointFileHashBefore89,expectedS88CheckpointFileHash89],\n'
    'SameQ[s88Checkpoint89["Stage"],"S88"],\n'
    'TrueQ[s88Checkpoint89["TestValidityPassed"]],\n'
    'TrueQ[s88Checkpoint89["BlindPerfect"]],\n'
    'SameQ[s88Checkpoint89["Outcome"],\n'
    '"S88_BLIND_EIGHT_BRANCH_FROZEN_DECODER_PASS"],\n'
    '!FileExistsQ[s89ResultCertificatePath]',
    "S89 checkpoint validation",
)
preflight_cell = replace_once(
    preflight_cell,
    '"RetuningApplied"->False,\n'
    '"S89ResultAlreadyPresent"->FileExistsQ[s89ResultCertificatePath],',
    '"RetuningApplied"->False,\n'
    '"S88CheckpointLocked"->And[\n'
    'SameQ[s88CheckpointFileHashBefore89,expectedS88CheckpointFileHash89],\n'
    'TrueQ[s88Checkpoint89["BlindPerfect"]]\n],\n'
    '"S89ResultAlreadyPresent"->FileExistsQ[s89ResultCertificatePath],',
    "S89 preflight report checkpoint field",
)

definition_cell = rename_suffix_outside_strings(s88_cells[2], "88", "89")
definition_cell = definition_cell.replace(
    "S88TestDefinitionBundle", "S89TestDefinitionBundle"
)
definition_cell = definition_cell.replace("S88BlindObservation", "S89BlindObservation")
definition_cell = definition_cell.replace("88000000+100 depth", "89000000+100 depth")
definition_cell = definition_cell.replace("interventionPair", "relocationPair")
definition_cell = definition_cell.replace('"InterventionPair"', '"RelocationPair"')
definition_cell = definition_cell.replace(
    "BranchStopPatch89,\nPathCutPatch89,\nMixedPathCutStopPatch89,",
    "BranchStopPatch89,\nBranchContinuePatch89,\nStopRelocationPatch89,",
)

patch_definitions = r'''
BranchStopPatch89[c_List,branch_Integer]:=Module[
{x,branchCount,e,m,safe,u,dummy,correct,wrong,remove,add},
x=c[[1]];
branchCount=Length[x[[6]]];
e=x[[1]];
m=x[[6,branch]];
safe=m+1;
u=m+2;
dummy=m+3;
correct=x[[5,branch]];
wrong=x[[5,1+Mod[branch,branchCount]]];
remove={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};
add={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};
<|
"Remove"->remove,
"Add"->add,
"ValidOnInput"->And[
And@@Map[MemberQ[e,#]&,remove],
And@@Map[!MemberQ[e,#]&,add],
Intersection[remove,add]==={}
]
|>
];

BranchContinuePatch89[c_List,branch_Integer]:=Module[
{x,branchCount,e,m,safe,u,dummy,correct,wrong,remove,add},
x=c[[1]];
branchCount=Length[x[[6]]];
e=x[[1]];
m=x[[6,branch]];
safe=m+1;
u=m+2;
dummy=m+3;
correct=x[[5,branch]];
wrong=x[[5,1+Mod[branch,branchCount]]];
remove={
DirectedEdge[m,wrong],
DirectedEdge[safe,correct],
DirectedEdge[u,dummy]
};
add={
DirectedEdge[m,correct],
DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]
};
<|
"Remove"->remove,
"Add"->add,
"ValidOnInput"->And[
And@@Map[MemberQ[e,#]&,remove],
And@@Map[!MemberQ[e,#]&,add],
Intersection[remove,add]==={}
]
|>
];

StopRelocationPatch89[c_List,relocationPair_List]:=Module[
{fromBranch,toBranch,restorePart,stopPart,remove,add},
fromBranch=First[relocationPair];
toBranch=Last[relocationPair];
restorePart=BranchContinuePatch89[c,fromBranch];
stopPart=BranchStopPatch89[c,toBranch];
remove=DeleteDuplicates@Join[restorePart["Remove"],stopPart["Remove"]];
add=DeleteDuplicates@Join[restorePart["Add"],stopPart["Add"]];
<|
"Remove"->remove,
"Add"->add,
"FromBranch"->fromBranch,
"ToBranch"->toBranch,
"DistinctBranches"->UnsameQ[fromBranch,toBranch],
"ComponentPatchesValid"->And[
TrueQ[restorePart["ValidOnInput"]],TrueQ[stopPart["ValidOnInput"]]
],
"NoCrossBranchConflict"->Intersection[remove,add]==={},
"ExpectedEditCount"->And[Length[remove]===6,Length[add]===6]
|>
];
'''
definition_cell = replace_between(
    definition_cell,
    "BranchStopPatch89[c_List,branch_Integer]:=Module[",
    "PrepareWorld89[",
    patch_definitions,
)

scenario_definition = r'''
PrepareScenario89[
topology_String,depth_Integer,relocationPair_List
]:=Module[
{
branchCount=8,seedCase,baselinePatch,baselineSeed,relocationPatch,
counterfactualSeed,baselineWorlds,counterfactualWorlds,worldPairs,
baselineGraphHashes,counterfactualGraphHashes,fromBranch,toBranch,
baselineReferenceActions,counterfactualReferenceActions
},
fromBranch=First[relocationPair];
toBranch=Last[relocationPair];
seedCase=Case89[depth,1,"Continue"];
baselinePatch=BranchStopPatch89[seedCase,fromBranch];
baselineSeed=ApplyEdgePatch81[seedCase,baselinePatch];
If[SameQ[baselineSeed,$Failed],Return[$Failed]];
relocationPatch=StopRelocationPatch89[baselineSeed,relocationPair];
counterfactualSeed=ApplyEdgePatch81[baselineSeed,relocationPatch];
If[SameQ[counterfactualSeed,$Failed],Return[$Failed]];
baselineWorlds=Table[
PrepareWorld89[
topology,depth,relocationPair,"SingleStopBaseline",answer,
If[SameQ[answer,fromBranch],"Stop","Continue"],
SetAnswer89[baselineSeed,answer]
],
{answer,Range[branchCount]}
];
counterfactualWorlds=Table[
PrepareWorld89[
topology,depth,relocationPair,"StopRelocatedCounterfactual",answer,
If[SameQ[answer,toBranch],"Stop","Continue"],
SetAnswer89[counterfactualSeed,answer]
],
{answer,Range[branchCount]}
];
worldPairs=MapThread[
Function[{base,counterfactual},
<|
"Answer"->base["Answer"],
"RelocatedFromQuery"->SameQ[base["Answer"],fromBranch],
"RelocatedToQuery"->SameQ[base["Answer"],toBranch],
"UnaffectedQuery"->!MemberQ[relocationPair,base["Answer"]],
"SameQuery"->SameQ[base["Answer"],counterfactual["Answer"]],
"ReferenceRelationCorrect"->Which[
SameQ[base["Answer"],fromBranch],And[
SameQ[base["ReferenceAction"],"Stop"],
SameQ[counterfactual["ReferenceAction"],"Continue"]
],
SameQ[base["Answer"],toBranch],And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[counterfactual["ReferenceAction"],"Stop"]
],
True,And[
SameQ[base["ReferenceAction"],"Continue"],
SameQ[counterfactual["ReferenceAction"],"Continue"]
]
],
"PredictionRelationCorrect"->Which[
SameQ[base["Answer"],fromBranch],And[
SameQ[base["Prediction"],"Stop"],
SameQ[counterfactual["Prediction"],"Continue"]
],
SameQ[base["Answer"],toBranch],And[
SameQ[base["Prediction"],"Continue"],
SameQ[counterfactual["Prediction"],"Stop"]
],
True,And[
SameQ[base["Prediction"],"Continue"],
SameQ[counterfactual["Prediction"],"Continue"]
]
],
"PairCorrect"->And[TrueQ[base["Correct"]],TrueQ[counterfactual["Correct"]]],
"BaselineWorld"->base,
"CounterfactualWorld"->counterfactual
|>
],
{baselineWorlds,counterfactualWorlds}
];
baselineGraphHashes=Lookup[baselineWorlds,"TopologyGraphHash"];
counterfactualGraphHashes=Lookup[counterfactualWorlds,"TopologyGraphHash"];
baselineReferenceActions=Lookup[baselineWorlds,"ReferenceAction"];
counterfactualReferenceActions=Lookup[counterfactualWorlds,"ReferenceAction"];
<|
"Topology"->topology,
"Depth"->depth,
"RelocationPair"->relocationPair,
"BaselinePatchValid"->TrueQ[baselinePatch["ValidOnInput"]],
"RelocationDistinctBranches"->relocationPatch["DistinctBranches"],
"RelocationComponentsValid"->relocationPatch["ComponentPatchesValid"],
"RelocationNoConflict"->relocationPatch["NoCrossBranchConflict"],
"RelocationEditCountCorrect"->relocationPatch["ExpectedEditCount"],
"BaselineSingleStop"->SameQ[Count[baselineReferenceActions,"Stop"],1],
"CounterfactualSingleStop"->SameQ[Count[counterfactualReferenceActions,"Stop"],1],
"StopCountConserved"->SameQ[
Count[baselineReferenceActions,"Stop"],
Count[counterfactualReferenceActions,"Stop"],1
],
"BaselineSameGraphAcrossQueries"->SameQ@@baselineGraphHashes,
"CounterfactualSameGraphAcrossQueries"->SameQ@@counterfactualGraphHashes,
"RelocationChangesGraph"->UnsameQ[
First[baselineGraphHashes],First[counterfactualGraphHashes]
],
"ReferenceRelationsCorrect"->And@@Lookup[worldPairs,"ReferenceRelationCorrect"],
"PredictionRelationsCorrect"->And@@Lookup[worldPairs,"PredictionRelationCorrect"],
"AllSixteenWorldsCorrect"->And@@Join[
Lookup[baselineWorlds,"Correct"],Lookup[counterfactualWorlds,"Correct"]
],
"WorldPairs"->worldPairs,
"BaselineWorlds"->baselineWorlds,
"CounterfactualWorlds"->counterfactualWorlds
|>
];

S89TestDefinitionBundle[]:={
DownValues[T89],DownValues[Case89],DownValues[ReferenceAction89],
DownValues[NodeRole89],DownValues[EncodePair89],DownValues[LegacyPredictTokens89],
DownValues[PredictFrozenDecoder89],DownValues[TripleSerialDiamondIn89],
DownValues[HierarchicalTerminalDiamondIn89],DownValues[SetAnswer89],
DownValues[TopologyTransform89],DownValues[ExpectedContractions89],
DownValues[BranchStopPatch89],DownValues[BranchContinuePatch89],
DownValues[StopRelocationPatch89],DownValues[PrepareWorld89],
DownValues[PrepareScenario89]
};
'''
definition_cell = replace_between(
    definition_cell,
    "PrepareScenario89[",
    "S89TestDefinitionBundle[]:=",
    scenario_definition,
)
# Remove the old bundle body left after the replacement boundary.
old_bundle_tail_end = definition_cell.find("};blindDepths89=")
old_bundle_start = definition_cell.find("S89TestDefinitionBundle[]:=", definition_cell.find("S89TestDefinitionBundle[]:=") + 1)
if old_bundle_start >= 0 and old_bundle_tail_end >= 0:
    definition_cell = definition_cell[:old_bundle_start] + definition_cell[old_bundle_tail_end + 2 :]

protocol_index = definition_cell.find("blindDepths89=")
if protocol_index < 0:
    raise RuntimeError("S89 protocol boundary missing")
definition_cell = definition_cell[:protocol_index].rstrip() + r'''

blindDepths89={61,109};
blindTopologies89={
"TripleSerialDiamondIn",
"HierarchicalTerminalDiamondIn"
};
blindRelocationPairs89={
{1,5},{2,6},{3,7},{4,8},{5,1},{6,2},{7,3},{8,4}
};

topologySpec89=<|
"TripleSerialDiamondIn"-><|
"Composition"->"DiamondIn72AfterDoubleDiamondIn79",
"PrivateDiamondsPerOriginalIncomingEdge"->3
|>,
"HierarchicalTerminalDiamondIn"-><|
"Composition"->"DiamondIn72AfterHierarchicalDiamondIn80",
"PrivateDiamondsPerOriginalIncomingEdge"->4
|>
|>;
topologySpecHash89=Hash[Normal[topologySpec89],"SHA256","HexString"];
testDefinitionHashBefore89=Hash[
S89TestDefinitionBundle[],"SHA256","HexString"
];
noCasesBeforeProtocolHash89=And[
!ValueQ[blindScenarios89],
!ValueQ[blindWorldPairs89],
!ValueQ[blindWorlds89]
];

protocol89=<|
"Stage"->"S89",
"Name"->"StopRelocationCounterfactualBlind",
"Candidate"->"S87D-FrozenWorldMultisetDecoder",
"CandidateHash"->decoderCandidateHashLoaded89,
"CandidateFileHash"->decoderCandidateFileHashBefore89,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore89,
"K33CandidateHash"->k33CandidateHashLoaded89,
"S88CheckpointFileHash"->s88CheckpointFileHashBefore89,
"BranchCount"->8,
"Depths"->blindDepths89,
"Topologies"->blindTopologies89,
"TopologySpecHash"->topologySpecHash89,
"RelocationPairs"->blindRelocationPairs89,
"ExpectedScenarios"->32,
"ExpectedWorldPairs"->256,
"ExpectedWorlds"->512,
"ExpectedBaselineContinueWorlds"->224,
"ExpectedBaselineStopWorlds"->32,
"ExpectedCounterfactualContinueWorlds"->224,
"ExpectedCounterfactualStopWorlds"->32,
"ExpectedRelocatedFromPairs"->32,
"ExpectedRelocatedToPairs"->32,
"ExpectedUnaffectedPairs"->192,
"ExternalGrammar"->"IndependentEightBranchT89",
"Intervention"->"ConservedSingleStopRelocation",
"InterventionSemantics"->
"RestoreFormerStopBranchAndStopDistinctFormerContinueBranch",
"ConservationLaw"->"ExactlyOneStopBeforeAndAfter",
"QueryGrid"->"AllEightQueriesBeforeAndAfterRelocation",
"FeatureFamily"->"QueriedGlobalMoments",
"FeatureDimension"->27,
"ObservationAggregation"->
"FullQueriedObservationMultisetWithoutCodeDeduplication",
"LegacyTokenDeduplication"->"DeleteDuplicatesAfterExactRoleCodePairing",
"SuccessCriterion"->
"ValidHarnessAndAll512WorldsCorrectIncludingBothDirectionsAndUnaffectedQueries",
"CandidateFrozenBeforeProtocol"->True,
"S88CheckpointReadOnlyLock"->True,
"S88PredictionsUsedForSelection"->False,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DecoderEditApplied"->False,
"RetuningApplied"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash89
|>;

protocolHash89=Hash[Normal[protocol89],"SHA256","HexString"];

Dataset[{Join[protocol89,<|
"ProtocolHash"->protocolHash89,
"TestDefinitionHash"->testDefinitionHashBefore89
|>]}]
'''.strip() + "\n"

run_cell = r'''
blindScenarios89=Flatten[
Table[
PrepareScenario89[topology,depth,relocationPair],
{topology,blindTopologies89},
{depth,blindDepths89},
{relocationPair,blindRelocationPairs89}
],
2
];

blindWorldPairs89=Flatten[Lookup[blindScenarios89,"WorldPairs"],1];
baselineWorlds89=Flatten[Lookup[blindScenarios89,"BaselineWorlds"],1];
counterfactualWorlds89=Flatten[
Lookup[blindScenarios89,"CounterfactualWorlds"],1
];
blindWorlds89=Join[baselineWorlds89,counterfactualWorlds89];

summary89=<|
"Scenarios"->Length[blindScenarios89],
"WorldPairs"->Length[blindWorldPairs89],
"Worlds"->Length[blindWorlds89],
"RelocatedFromQueryPairs"->Count[
blindWorldPairs89,p_/;TrueQ[p["RelocatedFromQuery"]]
],
"RelocatedToQueryPairs"->Count[
blindWorldPairs89,p_/;TrueQ[p["RelocatedToQuery"]]
],
"UnaffectedQueryPairs"->Count[
blindWorldPairs89,p_/;TrueQ[p["UnaffectedQuery"]]
],
"BaselinePatchValid"->Count[
blindScenarios89,s_/;TrueQ[s["BaselinePatchValid"]]
],
"RelocationDistinctBranches"->Count[
blindScenarios89,s_/;TrueQ[s["RelocationDistinctBranches"]]
],
"RelocationComponentsValid"->Count[
blindScenarios89,s_/;TrueQ[s["RelocationComponentsValid"]]
],
"RelocationNoConflict"->Count[
blindScenarios89,s_/;TrueQ[s["RelocationNoConflict"]]
],
"RelocationEditCountCorrect"->Count[
blindScenarios89,s_/;TrueQ[s["RelocationEditCountCorrect"]]
],
"BaselineSingleStop"->Count[
blindScenarios89,s_/;TrueQ[s["BaselineSingleStop"]]
],
"CounterfactualSingleStop"->Count[
blindScenarios89,s_/;TrueQ[s["CounterfactualSingleStop"]]
],
"StopCountConserved"->Count[
blindScenarios89,s_/;TrueQ[s["StopCountConserved"]]
],
"BaselineSameGraphAcrossQueries"->Count[
blindScenarios89,s_/;TrueQ[s["BaselineSameGraphAcrossQueries"]]
],
"CounterfactualSameGraphAcrossQueries"->Count[
blindScenarios89,s_/;TrueQ[s["CounterfactualSameGraphAcrossQueries"]]
],
"RelocationChangesGraph"->Count[
blindScenarios89,s_/;TrueQ[s["RelocationChangesGraph"]]
],
"ReferenceRelationsCorrect"->Count[
blindWorldPairs89,p_/;TrueQ[p["ReferenceRelationCorrect"]]
],
"PredictionRelationsCorrect"->Count[
blindWorldPairs89,p_/;TrueQ[p["PredictionRelationCorrect"]]
],
"PairCorrect"->Count[blindWorldPairs89,p_/;TrueQ[p["PairCorrect"]]],
"ScenarioPerfect"->Count[
blindScenarios89,s_/;TrueQ[s["AllSixteenWorldsCorrect"]]
],
"BaselineContinueCorrect"->Count[
baselineWorlds89,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"BaselineStopCorrect"->Count[
baselineWorlds89,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"CounterfactualContinueCorrect"->Count[
counterfactualWorlds89,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"CounterfactualStopCorrect"->Count[
counterfactualWorlds89,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"WorldCorrect"->Count[blindWorlds89,w_/;TrueQ[w["Correct"]]],
"CanonicalCaseExactlyBase"->Count[
blindWorlds89,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindWorlds89,w_/;TrueQ[w["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
blindWorlds89,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"ReferenceActionsCorrect"->Count[
blindWorlds89,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"NonEmptyTokens"->Count[blindWorlds89,w_/;w["RawTokenCount"]>0],
"ValidFeatureVectors"->Count[
blindWorlds89,w_/;VectorQ[w["FeatureVector"],IntegerQ]&&
Length[w["FeatureVector"]]===27
],
"PredictionFailures"->Count[
blindWorlds89,w_/;SameQ[w["Prediction"],$Failed]
],
"TerminatedNaturally"->Count[
blindWorlds89,w_/;TrueQ[w["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[blindWorlds89,w_/;TrueQ[w["HitSafetyCap"]]],
"EightBranchWorlds"->Count[
blindWorlds89,w_/;SameQ[w["BranchCount"],8]
],
"TotalTraceSeconds"->Total@Lookup[blindWorlds89,"TraceSeconds"]
|>;

byTopology89=Map[
Function[topology,
Module[{worlds,pairs,baseline,counterfactual},
worlds=Select[blindWorlds89,SameQ[#1["Topology"],topology]&];
pairs=Select[blindWorldPairs89,
SameQ[#1["BaselineWorld"]["Topology"],topology]&];
baseline=Select[worlds,SameQ[#1["GraphCondition"],"SingleStopBaseline"]&];
counterfactual=Select[
worlds,SameQ[#1["GraphCondition"],"StopRelocatedCounterfactual"]&
];
<|
"Topology"->topology,
"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
"BaselineContinueCorrect"->Count[
baseline,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"BaselineStopCorrect"->Count[
baseline,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"CounterfactualContinueCorrect"->Count[
counterfactual,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"CounterfactualStopCorrect"->Count[
counterfactual,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
]
|>
]
],
blindTopologies89
];

byDepth89=Map[
Function[depth,
Module[{worlds,baseline,counterfactual},
worlds=Select[blindWorlds89,SameQ[#1["Depth"],depth]&];
baseline=Select[worlds,SameQ[#1["GraphCondition"],"SingleStopBaseline"]&];
counterfactual=Select[
worlds,SameQ[#1["GraphCondition"],"StopRelocatedCounterfactual"]&
];
<|
"Depth"->depth,
"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"BaselineCorrect"->Count[baseline,w_/;TrueQ[w["Correct"]]],
"CounterfactualCorrect"->Count[
counterfactual,w_/;TrueQ[w["Correct"]]
]
|>
]
],
blindDepths89
];

Column[{
Dataset[Map[
KeyTake[#,{"Topology","Depth","RelocationPair",
"BaselinePatchValid","RelocationDistinctBranches",
"RelocationComponentsValid","RelocationNoConflict",
"RelocationEditCountCorrect","StopCountConserved",
"ReferenceRelationsCorrect","PredictionRelationsCorrect",
"AllSixteenWorldsCorrect"}]&,
blindScenarios89
]],
Dataset[byTopology89],
Dataset[byDepth89],
Dataset[{summary89}]
}]
'''.strip() + "\n"

audit_cell = r'''
modelHashAfter89=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter89=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
decoderObjectHashAfter89=Hash[
Normal[KeyDrop[frozenDecoderLoaded89,{"Classifier"}]],"SHA256","HexString"
];
coreHashAfter89=Hash[CoreDefinitionBundle89[],"SHA256","HexString"];
canonicalizerHashAfter89=Hash[
{DownValues[FindPrivateDiamond79B],DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]},"SHA256","HexString"
];
interventionHashAfter89=Hash[
{DownValues[LocalMediatorSources82],DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],DownValues[ReferenceAction82]},
"SHA256","HexString"
];
topologyPrimitiveHashAfter89=Hash[
{DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],
DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"
];
decoderRuntimeDefinitionHashAfter89=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"
];
testDefinitionHashAfter89=Hash[S89TestDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter89=Hash[Normal[protocol89],"SHA256","HexString"];

k33CandidateFileHashAfter89=FileSHA256Hex89[k33CandidatePath89];
decoderRuntimeFileHashAfter89=FileSHA256Hex89[decoderRuntimePath89];
decoderCandidateFileHashAfter89=FileSHA256Hex89[decoderCandidatePath89];
freezeCertificateFileHashAfter89=FileSHA256Hex89[freezeCertificatePath89];
s88CheckpointFileHashAfter89=FileSHA256Hex89[s88CheckpointPath89];

originalFrozenModelUnchanged89=SameQ[
modelHashBefore89,modelHashAfter89,expectedFrozenModelHash89
];
k33CandidateUnchanged89=And[
SameQ[k33ObjectHashBefore89,k33ObjectHashAfter89],
SameQ[k33ObjectHashAfter89,expectedK33CandidateHash89],
SameQ[k33CandidateFileHashBefore89,k33CandidateFileHashAfter89],
SameQ[k33CandidateFileHashAfter89,expectedK33CandidateFileHash89]
];
frozenDecoderUnchanged89=And[
SameQ[decoderObjectHashBefore89,decoderObjectHashAfter89],
SameQ[decoderCandidateHashLoaded89,expectedDecoderCandidateHash89],
SameQ[decoderCandidateFileHashBefore89,decoderCandidateFileHashAfter89],
SameQ[decoderCandidateFileHashAfter89,expectedDecoderCandidateFileHash89]
];
coreUnchanged89=SameQ[coreHashBefore89,coreHashAfter89];
canonicalizerUnchanged89=SameQ[canonicalizerHashBefore89,canonicalizerHashAfter89];
interventionCoreUnchanged89=SameQ[interventionHashBefore89,interventionHashAfter89];
topologyPrimitivesUnchanged89=SameQ[
topologyPrimitiveHashBefore89,topologyPrimitiveHashAfter89
];
decoderRuntimeUnchanged89=And[
SameQ[decoderRuntimeDefinitionHashBefore89,decoderRuntimeDefinitionHashAfter89],
SameQ[decoderRuntimeFileHashBefore89,decoderRuntimeFileHashAfter89],
SameQ[decoderRuntimeFileHashAfter89,expectedFeatureRuntimeFileHash89]
];
testDefinitionUnchanged89=SameQ[
testDefinitionHashBefore89,testDefinitionHashAfter89
];
protocolUnchanged89=SameQ[protocolHash89,protocolHashAfter89];
freezeCertificateUnchanged89=And[
SameQ[freezeCertificateFileHashBefore89,freezeCertificateFileHashAfter89],
SameQ[freezeCertificateFileHashAfter89,expectedFreezeCertificateFileHash89]
];
s88CheckpointUnchanged89=And[
SameQ[s88CheckpointFileHashBefore89,s88CheckpointFileHashAfter89],
SameQ[s88CheckpointFileHashAfter89,expectedS88CheckpointFileHash89]
];
observationAggregationUnchanged89=SameQ[
protocol89["ObservationAggregation"],
"FullQueriedObservationMultisetWithoutCodeDeduplication"
];

testValidityPassed89=And[
TrueQ[preflightPassed89],
TrueQ[originalFrozenModelUnchanged89],
TrueQ[k33CandidateUnchanged89],
TrueQ[frozenDecoderUnchanged89],
TrueQ[coreUnchanged89],
TrueQ[canonicalizerUnchanged89],
TrueQ[interventionCoreUnchanged89],
TrueQ[topologyPrimitivesUnchanged89],
TrueQ[decoderRuntimeUnchanged89],
TrueQ[testDefinitionUnchanged89],
TrueQ[protocolUnchanged89],
TrueQ[freezeCertificateUnchanged89],
TrueQ[s88CheckpointUnchanged89],
TrueQ[observationAggregationUnchanged89],
TrueQ[protocol89["NoCaseEvaluatedBeforeProtocolHash"]],
SameQ[summary89["Scenarios"],32],
SameQ[summary89["WorldPairs"],256],
SameQ[summary89["Worlds"],512],
SameQ[summary89["RelocatedFromQueryPairs"],32],
SameQ[summary89["RelocatedToQueryPairs"],32],
SameQ[summary89["UnaffectedQueryPairs"],192],
SameQ[summary89["BaselinePatchValid"],32],
SameQ[summary89["RelocationDistinctBranches"],32],
SameQ[summary89["RelocationComponentsValid"],32],
SameQ[summary89["RelocationNoConflict"],32],
SameQ[summary89["RelocationEditCountCorrect"],32],
SameQ[summary89["BaselineSingleStop"],32],
SameQ[summary89["CounterfactualSingleStop"],32],
SameQ[summary89["StopCountConserved"],32],
SameQ[summary89["BaselineSameGraphAcrossQueries"],32],
SameQ[summary89["CounterfactualSameGraphAcrossQueries"],32],
SameQ[summary89["RelocationChangesGraph"],32],
SameQ[summary89["ReferenceRelationsCorrect"],256],
SameQ[summary89["CanonicalCaseExactlyBase"],512],
SameQ[summary89["ContractionCountCorrect"],512],
SameQ[summary89["ProtectedNodesPreserved"],512],
SameQ[summary89["ReferenceActionsCorrect"],512],
SameQ[summary89["NonEmptyTokens"],512],
SameQ[summary89["ValidFeatureVectors"],512],
SameQ[summary89["PredictionFailures"],0],
SameQ[summary89["TerminatedNaturally"],512],
SameQ[summary89["HitSafetyCap"],0],
SameQ[summary89["EightBranchWorlds"],512]
];

blindPerfect89=And[
TrueQ[testValidityPassed89],
SameQ[summary89["BaselineContinueCorrect"],224],
SameQ[summary89["BaselineStopCorrect"],32],
SameQ[summary89["CounterfactualContinueCorrect"],224],
SameQ[summary89["CounterfactualStopCorrect"],32],
SameQ[summary89["WorldCorrect"],512],
SameQ[summary89["PairCorrect"],256],
SameQ[summary89["PredictionRelationsCorrect"],256],
SameQ[summary89["ScenarioPerfect"],32]
];

continueCases89=448;
stopCases89=64;
continueCorrect89=summary89["BaselineContinueCorrect"]+
summary89["CounterfactualContinueCorrect"];
stopCorrect89=summary89["BaselineStopCorrect"]+
summary89["CounterfactualStopCorrect"];
accuracy89=N[summary89["WorldCorrect"]/512];
balancedAccuracy89=N@Mean[{
continueCorrect89/continueCases89,stopCorrect89/stopCases89
}];

resultPayload89=<|
"Stage"->"S89",
"Name"->"StopRelocationCounterfactualBlind",
"CandidateHash"->decoderCandidateHashLoaded89,
"CandidateFileHash"->decoderCandidateFileHashAfter89,
"S88CheckpointFileHash"->s88CheckpointFileHashAfter89,
"ProtocolHash"->protocolHashAfter89,
"TestDefinitionHash"->testDefinitionHashAfter89,
"Depths"->blindDepths89,
"Topologies"->blindTopologies89,
"RelocationPairs"->blindRelocationPairs89,
"Scenarios"->summary89["Scenarios"],
"WorldPairs"->summary89["WorldPairs"],
"Worlds"->summary89["Worlds"],
"BaselineContinueCorrect"->summary89["BaselineContinueCorrect"],
"BaselineStopCorrect"->summary89["BaselineStopCorrect"],
"CounterfactualContinueCorrect"->summary89["CounterfactualContinueCorrect"],
"CounterfactualStopCorrect"->summary89["CounterfactualStopCorrect"],
"WorldCorrect"->summary89["WorldCorrect"],
"Accuracy"->accuracy89,
"BalancedAccuracy"->balancedAccuracy89,
"PairCorrect"->summary89["PairCorrect"],
"PredictionRelationsCorrect"->summary89["PredictionRelationsCorrect"],
"ScenarioPerfect"->summary89["ScenarioPerfect"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged89],
"OriginalK33CandidateChanged"->!TrueQ[k33CandidateUnchanged89],
"FrozenDecoderChanged"->!TrueQ[frozenDecoderUnchanged89],
"CoreChanged"->!TrueQ[coreUnchanged89],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged89],
"InterventionCoreChanged"->!TrueQ[interventionCoreUnchanged89],
"TopologyPrimitivesChanged"->!TrueQ[topologyPrimitivesUnchanged89],
"FeatureRuntimeChanged"->!TrueQ[decoderRuntimeUnchanged89],
"TestDefinitionChangedDuringRun"->!TrueQ[testDefinitionUnchanged89],
"ProtocolChangedDuringRun"->!TrueQ[protocolUnchanged89],
"DeduplicationMechanismChanged"->!TrueQ[coreUnchanged89],
"ObservationAggregationChanged"->!TrueQ[observationAggregationUnchanged89],
"S88CheckpointChanged"->!TrueQ[s88CheckpointUnchanged89],
"TestValidityPassed"->testValidityPassed89,
"BlindPerfect"->blindPerfect89
|>;

blindResultHash89=Hash[Normal[resultPayload89],"SHA256","HexString"];

cert89=Join[resultPayload89,<|
"CandidateFrozenBeforeS89"->True,
"BlindProtocolHashedBeforeCases"->True,
"S87DDecoderUsed"->True,
"S88CheckpointLocked"->True,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DecoderEditApplied"->False,
"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"AllEightQueryPositionsTestedPerGraph"->True,
"SameQueryBeforeAfterIntervention"->True,
"StopCountConservedBeforeAfter"->True,
"S89IsBlindCounterfactualRelocationTest"->True,
"MayClaimBlindStopRelocationTransfer"->blindPerfect89,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary89["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash89,
"Outcome"->Which[
!TrueQ[testValidityPassed89],"INVALID_S89_BLIND_TEST",
TrueQ[blindPerfect89],"S89_BLIND_STOP_RELOCATION_PASS",
True,"S89_VALID_BLIND_FAILURE_DO_NOT_RETUNE"
],
"SuggestedNextStage"->Which[
!TrueQ[testValidityPassed89],"S89R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",
TrueQ[blindPerfect89],"S90_INTERVENTION_ALGEBRA_BLIND",
True,"S89A_FAILURE_AUDIT_WITHOUT_RETUNING"
]
|>];

certificateExportResult89=Quiet@Check[
Export[s89ResultCertificatePath,cert89,"RawJSON"],$Failed
];
certificateExported89=And[
StringQ[certificateExportResult89],FileExistsQ[s89ResultCertificatePath]
];

Column[{
Dataset[{cert89}],
Dataset[{<|
"CertificateExported"->certificateExported89,
"CertificatePath"->s89ResultCertificatePath,
"CertificateFileHash"->If[
certificateExported89,FileSHA256Hex89[s89ResultCertificatePath],Missing[]
]
|>}]
}]
'''.strip() + "\n"

cells = [architecture_cell, preflight_cell, definition_cell, run_cell, audit_cell]
for number, cell in enumerate(cells, start=1):
    check_wl_delimiters(cell)
    for forbidden in (
        "Classify[",
        "BalancedTrainingRules",
        "bestResult87C",
        "allWorlds87A",
        "auditDataPayload87B",
    ):
        if forbidden in cell:
            raise RuntimeError(f"forbidden training/revealed state in cell {number}: {forbidden}")

combined = "\n".join(cells)
if combined.index("protocolHash89=") > combined.index("blindScenarios89="):
    raise RuntimeError("S89 cases could be generated before protocol hashing")
if '"TrainingRun"->False' not in combined or '"RetuningApplied"->False' not in combined:
    raise RuntimeError("S89 frozen-run declarations are missing")

wl_source = "\n\n".join(f"{NEW_MARKER}\n{cell}" for cell in cells)
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S89 - Blind Stop-Relocation Counterfactual Test\n",
        "\n",
        "S89 keeps the S87D decoder, TCCT core, canonicalizer, propagation, "
        "undirected freeze behavior, observation aggregation, and deduplication "
        "mechanism unchanged. The only experimental novelty is a conserved "
        "stop-relocation intervention: restore the one factual Stop branch and "
        "move Stop to a distinct branch while preserving exactly one Stop.\n",
        "\n",
        "The protocol and test definitions are hashed before case generation. "
        "There is no training, search, decoder editing, or retuning. Run once "
        "from a fresh kernel and preserve either success or failure. Expected "
        "workload: 512 worlds.\n",
    ],
}


def code_cell(source: str, stage: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tcct_stage": stage},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


notebook = {
    "cells": [
        markdown,
        code_cell(architecture_cell, "S89-ARCHITECTURE"),
        code_cell(preflight_cell, "S89-PREFLIGHT"),
        code_cell(definition_cell, "S89-PROTOCOL"),
        code_cell(run_cell, "S89-BLIND-RUN"),
        code_cell(audit_cell, "S89-AUDIT"),
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
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
)

preflight_cells = cells[:3]
preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [
    markdown,
    code_cell(preflight_cells[0], "S89-ARCHITECTURE"),
    code_cell(preflight_cells[1], "S89-PREFLIGHT"),
    code_cell(preflight_cells[2], "S89-PROTOCOL"),
]
PREFLIGHT_NB_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL_OUTPUT.write_text(
    "\n\n".join(f"{NEW_MARKER}\n{cell}" for cell in preflight_cells)
    + "\n\n"
    + 'Print[InputForm[<|"PreflightPassed"->preflightPassed89,'
    + '"ProtocolHash"->protocolHash89,'
    + '"TestDefinitionHash"->testDefinitionHashBefore89,'
    + '"CandidateHash"->decoderCandidateHashLoaded89,'
    + '"S88CheckpointHash"->s88CheckpointFileHashBefore89,'
    + '"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash89,'
    + '"BlindScenariosDefined"->ValueQ[blindScenarios89],'
    + '"S89ResultCertificateExists"->FileExistsQ[s89ResultCertificatePath]|>]];\n',
    encoding="utf-8",
)

launcher = r'''@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S89_StopRelocationCounterfactualBlind.ipynb"
set "TCCT_S88_RESULT=E:\engine_wolf\TCCT_S88_BlindResultCertificate.json"
set "TCCT_S89_RESULT=E:\engine_wolf\TCCT_S89_BlindResultCertificate.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s89"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s89"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)
if not exist "%TCCT_NOTEBOOK%" (
  echo S89 notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)
if not exist "%TCCT_S88_RESULT%" (
  echo Locked S88 result certificate not found: %TCCT_S88_RESULT%
  pause
  exit /b 1
)
if not exist "%TCCT_DECODER%" (
  echo Frozen S87D decoder not found: %TCCT_DECODER%
  pause
  exit /b 1
)
if exist "%TCCT_S89_RESULT%" (
  echo A prior S89 result certificate already exists.
  echo Preserve it and do not rerun or overwrite the blind test.
  echo %TCCT_S89_RESULT%
  pause
  exit /b 1
)

if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"

start "TCCT S89 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8902 --ServerApp.port_retries=5
exit /b 0
'''
LAUNCHER_OUTPUT.write_text(launcher, encoding="utf-8")

precommit = {
    "Stage": "S89",
    "Name": "StopRelocationCounterfactualBlind",
    "BlindCasesGeneratedAtBuild": False,
    "BlindResultCertificatePresentAtBuild": Path(
        r"E:\engine_wolf\TCCT_S89_BlindResultCertificate.json"
    ).exists(),
    "CandidateFrozenBeforeProtocol": True,
    "S88CheckpointSHA256": "1c56bb0a87eba871f8474a93d4206d6aebbf1d66412a0d3927e62155a81e2fa4",
    "WolframSourceSHA256": sha256(WL_OUTPUT),
    "NotebookSHA256": sha256(NB_OUTPUT),
    "BranchCount": 8,
    "Depths": [61, 109],
    "Topologies": [
        "TripleSerialDiamondIn",
        "HierarchicalTerminalDiamondIn",
    ],
    "RelocationPairs": [
        [1, 5], [2, 6], [3, 7], [4, 8],
        [5, 1], [6, 2], [7, 3], [8, 4],
    ],
    "ExpectedScenarios": 32,
    "ExpectedWorldPairs": 256,
    "ExpectedWorlds": 512,
    "ExpectedContinueWorlds": 448,
    "ExpectedStopWorlds": 64,
    "ProtocolHash": "32f425daed5c9604a2971de24b763360b14f0c64cddd3e08fc0d1cfa9de9b846",
    "TestDefinitionHash": "c78b29923c011330697a70e628f5c53410c5c46dcb0cd36908002a008f8fd7f5",
    "DynamicPreflightPassed": True,
    "BlindCasesGeneratedAtPreflight": False,
    "S89ResultCertificatePresentAtPreflight": False,
    "TrainingRun": False,
    "CandidateSearchRun": False,
    "DecoderEditApplied": False,
    "RetuningApplied": False,
}
PRECOMMIT_OUTPUT.write_text(
    json.dumps(precommit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)

for path in (
    WL_OUTPUT,
    NB_OUTPUT,
    PREFLIGHT_WL_OUTPUT,
    PREFLIGHT_NB_OUTPUT,
    PRECOMMIT_OUTPUT,
    LAUNCHER_OUTPUT,
):
    print(path)
