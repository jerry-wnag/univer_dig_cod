import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind.wl"
WL = ROOT / "TCCT_S90_InterventionAlgebraBlind.wl"
NB = ROOT / "TCCT_S90_InterventionAlgebraBlind.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S90_InterventionAlgebraBlind_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S90_InterventionAlgebraBlind_Preflight.ipynb"
PRECOMMIT = ROOT / "TCCT_S90_Precommit.json"
LAUNCHER = ROOT / "Start_TCCT_S90_Jupyter.cmd"
OLD_MARKER = "(* S89 CELL *)"
MARKER = "(* S90 CELL *)"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def split_cells() -> list[str]:
    parts = SOURCE.read_text(encoding="utf-8").split(OLD_MARKER)
    cells = [part.strip() + "\n" for part in parts[1:] if part.strip()]
    if len(cells) != 5:
        raise RuntimeError(f"expected five S89 cells, found {len(cells)}")
    return cells


def rename_suffix(source: str, old: str, new: str) -> str:
    out: list[str] = []
    index = 0
    in_string = False
    escaped = False
    comment_depth = 0
    while index < len(source):
        char = source[index]
        nxt = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            out.append(char)
            if char == "(" and nxt == "*":
                out.append(nxt)
                comment_depth += 1
                index += 2
                continue
            if char == "*" and nxt == ")":
                out.append(nxt)
                comment_depth -= 1
                index += 2
                continue
            index += 1
            continue
        if in_string:
            out.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
            continue
        if char == "(" and nxt == "*":
            out.extend((char, nxt))
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            out.append(char)
            in_string = True
            index += 1
            continue
        if char.isalpha() or char == "$":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "$"):
                end += 1
            token = source[index:end]
            if token.endswith(old):
                token = token[: -len(old)] + new
            out.append(token)
            index = end
            continue
        out.append(char)
        index += 1
    return "".join(out)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


def replace_between(source: str, start: str, end: str, replacement: str) -> str:
    left = source.find(start)
    right = source.find(end, left)
    if left < 0 or right < 0:
        raise RuntimeError(f"missing boundary: {start!r} -> {end!r}")
    return source[:left] + replacement.rstrip() + "\n\n" + source[right:]


def check_delimiters(source: str) -> None:
    pairs = {")": "(", "]": "[", "}": "{"}
    stack: list[str] = []
    in_string = False
    escaped = False
    comment_depth = 0
    index = 0
    while index < len(source):
        char = source[index]
        nxt = source[index + 1] if index + 1 < len(source) else ""
        if comment_depth:
            if char == "(" and nxt == "*":
                comment_depth += 1
                index += 2
                continue
            if char == "*" and nxt == ")":
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
        if char == "(" and nxt == "*":
            comment_depth = 1
            index += 2
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append(char)
        elif char in ")]}":
            if not stack or stack.pop() != pairs[char]:
                raise RuntimeError(f"unbalanced delimiter {char} at {index}")
        index += 1
    if in_string or comment_depth or stack:
        raise RuntimeError("unterminated Wolfram source")


s89 = split_cells()
architecture = s89[0]

preflight = rename_suffix(s89[1], "89", "90")
preflight = preflight.replace("TCCT_S89_BlindResultCertificate.json", "TCCT_S90_BlindResultCertificate.json")
preflight = preflight.replace("s89ResultCertificatePath", "s90ResultCertificatePath")
preflight = preflight.replace("S89 aborted", "S90 aborted")
preflight = preflight.replace("prior S89 result", "prior S90 result")
preflight = preflight.replace('"Stage"->"S89"', '"Stage"->"S90"')
preflight = preflight.replace('"Name"->"StopRelocationCounterfactualBlind"', '"Name"->"InterventionAlgebraBlind"')
preflight = preflight.replace('"S89ResultAlreadyPresent"', '"S90ResultAlreadyPresent"')
preflight = preflight.replace("expectedS88CheckpointFileHash90", "expectedS89CheckpointFileHash90")
preflight = preflight.replace("s88Checkpoint", "s89Checkpoint")
preflight = preflight.replace("S88Checkpoint", "S89Checkpoint")
preflight = preflight.replace(
    '"1c56bb0a87eba871f8474a93d4206d6aebbf1d66412a0d3927e62155a81e2fa4"',
    '"7d0f543f6f17384ee8969131547b2766aad1fbaed999e5b039c2708d6d89b032"',
)
preflight = preflight.replace("TCCT_S88_BlindResultCertificate.json", "TCCT_S89_BlindResultCertificate.json")
preflight = preflight.replace('s89Checkpoint90["Stage"],"S88"', 's89Checkpoint90["Stage"],"S89"')
preflight = preflight.replace(
    '"S88_BLIND_EIGHT_BRANCH_FROZEN_DECODER_PASS"',
    '"S89_BLIND_STOP_RELOCATION_PASS"',
)
preflight = preflight.replace('"BranchCount"->8', '"BranchCount"->9')
preflight = preflight.replace('"Depths"->{61,109}', '"Depths"->{73,121}')

definition = rename_suffix(s89[2], "89", "90")
definition = definition.replace("S89TestDefinitionBundle", "S90TestDefinitionBundle")
definition = definition.replace("S89BlindObservation", "S90BlindObservation")
definition = definition.replace("89000000+100 depth", "90000000+100 depth")
definition = replace_once(
    definition,
    "T90[depth,target,answer,90000000+100 depth,8];",
    "T90[depth,target,answer,90000000+100 depth,9];",
    "nine-branch wrapper",
)
definition = definition.replace("relocationPair", "algebraTuple")
definition = definition.replace('"RelocationPair"', '"AlgebraTuple"')
definition = replace_once(
    definition,
    "StopRelocationPatch90,\nPrepareWorld90,",
    "StopRelocationPatch90,\nIdentityPatch90,\nPrepareWorld90,",
    "S90 ClearAll identity",
)
identity_definition = r'''
IdentityPatch90[c_List]:=<|
"Remove"->{},
"Add"->{},
"ValidOnInput"->ListQ[c]
|>;
'''
definition = replace_once(
    definition,
    "PrepareWorld90[\ntopology_String,",
    identity_definition + "\nPrepareWorld90[\ntopology_String,",
    "S90 identity patch definition",
)

scenario = r'''
PrepareScenario90[
topology_String,depth_Integer,algebraTuple_List
]:=Module[
{
branchCount=9,a,b,c,d,seedCase,startPatch,caseA,identityPatch,caseAIdentity,
patchAB,caseB,patchBA,caseARestored,patchAC,caseCDirect,
patchBC,caseCViaB,patchAD,caseD,patchDC,caseCViaD,
stateCases,stateStops,stateWorlds,unaffectedQueries,
allRelocations,allPatchesValid,allStatesSingleStop,
unaffectedPredictionInvariant,stateGraphGroups
},
{a,b,c,d}=algebraTuple;
seedCase=Case90[depth,1,"Continue"];
startPatch=BranchStopPatch90[seedCase,a];
caseA=ApplyEdgePatch81[seedCase,startPatch];
identityPatch=IdentityPatch90[caseA];
caseAIdentity=ApplyEdgePatch81[caseA,identityPatch];
patchAB=StopRelocationPatch90[caseA,{a,b}];
caseB=ApplyEdgePatch81[caseA,patchAB];
patchBA=StopRelocationPatch90[caseB,{b,a}];
caseARestored=ApplyEdgePatch81[caseB,patchBA];
patchAC=StopRelocationPatch90[caseA,{a,c}];
caseCDirect=ApplyEdgePatch81[caseA,patchAC];
patchBC=StopRelocationPatch90[caseB,{b,c}];
caseCViaB=ApplyEdgePatch81[caseB,patchBC];
patchAD=StopRelocationPatch90[caseA,{a,d}];
caseD=ApplyEdgePatch81[caseA,patchAD];
patchDC=StopRelocationPatch90[caseD,{d,c}];
caseCViaD=ApplyEdgePatch81[caseD,patchDC];
If[AnyTrue[
{caseA,caseAIdentity,caseB,caseARestored,caseCDirect,caseCViaB,caseD,caseCViaD},
SameQ[#,$Failed]&],Return[$Failed]];
allRelocations={patchAB,patchBA,patchAC,patchBC,patchAD,patchDC};
allPatchesValid=And[
TrueQ[startPatch["ValidOnInput"]],TrueQ[identityPatch["ValidOnInput"]],
And@@Map[And[
TrueQ[#1["DistinctBranches"]],TrueQ[#1["ComponentPatchesValid"]],
TrueQ[#1["NoCrossBranchConflict"]],TrueQ[#1["ExpectedEditCount"]]
]&,allRelocations]
];
stateCases=<|"A"->caseA,"B"->caseB,"C"->caseCDirect,"D"->caseD|>;
stateStops=<|"A"->a,"B"->b,"C"->c,"D"->d|>;
stateWorlds=Flatten[KeyValueMap[
Function[{label,worldCase},Table[
PrepareWorld90[
topology,depth,algebraTuple,"State"<>label,answer,
If[SameQ[answer,stateStops[label]],"Stop","Continue"],
SetAnswer90[worldCase,answer]
],{answer,Range[branchCount]}]],stateCases],1];
allStatesSingleStop=And@@KeyValueMap[
Function[{label,worldCase},SameQ[
Count[Table[ReferenceAction90[SetAnswer90[worldCase,q]],{q,Range[branchCount]}],"Stop"],1
]],stateCases];
unaffectedQueries=Complement[Range[branchCount],algebraTuple];
unaffectedPredictionInvariant=And@@Map[
Function[q,Module[{predictions},
predictions=Lookup[Select[stateWorlds,SameQ[#1["Answer"],q]&],"Prediction"];
And[Length[predictions]===4,SameQ@@predictions,SameQ[First[predictions],"Continue"]]
]],unaffectedQueries];
stateGraphGroups=GatherBy[stateWorlds,#1["GraphCondition"]&];
<|
"Topology"->topology,
"Depth"->depth,
"AlgebraTuple"->algebraTuple,
"TupleDistinct"->DuplicateFreeQ[algebraTuple],
"AllPatchesValid"->allPatchesValid,
"IdentityExact"->SameQ[caseAIdentity,caseA],
"InverseExact"->SameQ[caseARestored,caseA],
"CompositionExact"->SameQ[caseCViaB,caseCDirect],
"PathIndependenceExact"->SameQ[caseCViaD,caseCDirect],
"AllStatesSingleStop"->allStatesSingleStop,
"FourStateCasesDistinct"->DuplicateFreeQ[Values[stateCases]],
"AllStateGraphsSameAcrossQueries"->And@@Map[
SameQ@@Lookup[#,"TopologyGraphHash"]&,stateGraphGroups
],
"ReferenceActionsCorrect"->And@@Map[
SameQ[#1["ReferenceAction"],#1["Target"]]&,stateWorlds
],
"UnaffectedQueryCount"->Length[unaffectedQueries],
"UnaffectedPredictionInvariant"->unaffectedPredictionInvariant,
"AllThirtySixWorldsCorrect"->And@@Lookup[stateWorlds,"Correct"],
"Worlds"->stateWorlds
|>
];

S90TestDefinitionBundle[]:={
DownValues[T90],DownValues[Case90],DownValues[ReferenceAction90],
DownValues[NodeRole90],DownValues[EncodePair90],DownValues[LegacyPredictTokens90],
DownValues[PredictFrozenDecoder90],DownValues[TripleSerialDiamondIn90],
DownValues[HierarchicalTerminalDiamondIn90],DownValues[SetAnswer90],
DownValues[TopologyTransform90],DownValues[ExpectedContractions90],
DownValues[BranchStopPatch90],DownValues[BranchContinuePatch90],
DownValues[StopRelocationPatch90],DownValues[IdentityPatch90],
DownValues[PrepareWorld90],DownValues[PrepareScenario90]
};
'''
definition = replace_between(definition, "PrepareScenario90[", "S90TestDefinitionBundle[]:=", scenario)
duplicate_bundle = definition.find("S90TestDefinitionBundle[]:=", definition.find("S90TestDefinitionBundle[]:=") + 1)
protocol_boundary = definition.find("blindDepths90=")
if duplicate_bundle >= 0 and protocol_boundary >= 0:
    definition = definition[:duplicate_bundle] + definition[protocol_boundary:]
protocol_boundary = definition.find("blindDepths90=")
if protocol_boundary < 0:
    raise RuntimeError("S90 protocol boundary missing")
definition = definition[:protocol_boundary].rstrip() + r'''

blindDepths90={73,121};
blindTopologies90={"TripleSerialDiamondIn","HierarchicalTerminalDiamondIn"};
blindAlgebraTuples90={
{1,3,6,8},{2,4,7,9},{3,5,8,1},{4,6,9,2},{5,7,1,3},
{6,8,2,4},{7,9,3,5},{8,1,4,6},{9,2,5,7}
};
topologySpec90=<|
"TripleSerialDiamondIn"->"DiamondIn72AfterDoubleDiamondIn79",
"HierarchicalTerminalDiamondIn"->"DiamondIn72AfterHierarchicalDiamondIn80"
|>;
topologySpecHash90=Hash[Normal[topologySpec90],"SHA256","HexString"];
testDefinitionHashBefore90=Hash[S90TestDefinitionBundle[],"SHA256","HexString"];
noCasesBeforeProtocolHash90=And[
!ValueQ[blindScenarios90],!ValueQ[blindWorlds90]
];
protocol90=<|
"Stage"->"S90",
"Name"->"InterventionAlgebraBlind",
"Candidate"->"S87D-FrozenWorldMultisetDecoder",
"CandidateHash"->decoderCandidateHashLoaded90,
"CandidateFileHash"->decoderCandidateFileHashBefore90,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore90,
"K33CandidateHash"->k33CandidateHashLoaded90,
"S89CheckpointFileHash"->s89CheckpointFileHashBefore90,
"BranchCount"->9,
"Depths"->blindDepths90,
"Topologies"->blindTopologies90,
"TopologySpecHash"->topologySpecHash90,
"AlgebraTuples"->blindAlgebraTuples90,
"ExpectedScenarios"->36,
"ExpectedWorlds"->1296,
"ExpectedContinueWorlds"->1152,
"ExpectedStopWorlds"->144,
"ExpectedUnaffectedQueryRelations"->180,
"ExternalGrammar"->"IndependentNineBranchT90",
"InterventionAlgebra"->{"Identity","Inverse","Composition","PathIndependence"},
"StateSemantics"->"ExactlyOneStopAcrossA_B_C_D",
"QueryGrid"->"AllNineQueriesAtFourAlgebraEndpoints",
"FeatureFamily"->"QueriedGlobalMoments",
"FeatureDimension"->27,
"ObservationAggregation"->"FullQueriedObservationMultisetWithoutCodeDeduplication",
"LegacyTokenDeduplication"->"DeleteDuplicatesAfterExactRoleCodePairing",
"SuccessCriterion"->"ValidAlgebraHarnessAndAll1296EndpointWorldsCorrect",
"CandidateFrozenBeforeProtocol"->True,
"S89CheckpointReadOnlyLock"->True,
"S89PredictionsUsedForSelection"->False,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash90
|>;
protocolHash90=Hash[Normal[protocol90],"SHA256","HexString"];
Dataset[{Join[protocol90,<|
"ProtocolHash"->protocolHash90,"TestDefinitionHash"->testDefinitionHashBefore90
|>]}]
'''.strip() + "\n"

run = r'''
blindScenarios90=Flatten[Table[
PrepareScenario90[topology,depth,tuple],
{topology,blindTopologies90},{depth,blindDepths90},{tuple,blindAlgebraTuples90}
],2];
blindWorlds90=Flatten[Lookup[blindScenarios90,"Worlds"],1];

summary90=<|
"Scenarios"->Length[blindScenarios90],
"Worlds"->Length[blindWorlds90],
"TupleDistinct"->Count[blindScenarios90,s_/;TrueQ[s["TupleDistinct"]]],
"AllPatchesValid"->Count[blindScenarios90,s_/;TrueQ[s["AllPatchesValid"]]],
"IdentityExact"->Count[blindScenarios90,s_/;TrueQ[s["IdentityExact"]]],
"InverseExact"->Count[blindScenarios90,s_/;TrueQ[s["InverseExact"]]],
"CompositionExact"->Count[blindScenarios90,s_/;TrueQ[s["CompositionExact"]]],
"PathIndependenceExact"->Count[blindScenarios90,s_/;TrueQ[s["PathIndependenceExact"]]],
"AllStatesSingleStop"->Count[blindScenarios90,s_/;TrueQ[s["AllStatesSingleStop"]]],
"FourStateCasesDistinct"->Count[blindScenarios90,s_/;TrueQ[s["FourStateCasesDistinct"]]],
"AllStateGraphsSameAcrossQueries"->Count[
blindScenarios90,s_/;TrueQ[s["AllStateGraphsSameAcrossQueries"]]
],
"ReferenceActionsCorrectScenarios"->Count[
blindScenarios90,s_/;TrueQ[s["ReferenceActionsCorrect"]]
],
"UnaffectedQueryRelations"->Total@Lookup[blindScenarios90,"UnaffectedQueryCount"],
"UnaffectedPredictionInvariant"->Count[
blindScenarios90,s_/;TrueQ[s["UnaffectedPredictionInvariant"]]
],
"ScenarioPerfect"->Count[
blindScenarios90,s_/;TrueQ[s["AllThirtySixWorldsCorrect"]]
],
"ContinueCorrect"->Count[
blindWorlds90,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"StopCorrect"->Count[
blindWorlds90,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
],
"WorldCorrect"->Count[blindWorlds90,w_/;TrueQ[w["Correct"]]],
"CanonicalCaseExactlyBase"->Count[
blindWorlds90,w_/;TrueQ[w["CanonicalCaseExactlyBase"]]
],
"ContractionCountCorrect"->Count[
blindWorlds90,w_/;TrueQ[w["ContractionCountCorrect"]]
],
"ProtectedNodesPreserved"->Count[
blindWorlds90,w_/;TrueQ[w["ProtectedNodesPreserved"]]
],
"ReferenceActionsCorrect"->Count[
blindWorlds90,w_/;SameQ[w["ReferenceAction"],w["Target"]]
],
"NonEmptyTokens"->Count[blindWorlds90,w_/;w["RawTokenCount"]>0],
"ValidFeatureVectors"->Count[
blindWorlds90,w_/;VectorQ[w["FeatureVector"],IntegerQ]&&Length[w["FeatureVector"]]===27
],
"PredictionFailures"->Count[blindWorlds90,w_/;SameQ[w["Prediction"],$Failed]],
"TerminatedNaturally"->Count[
blindWorlds90,w_/;TrueQ[w["TerminatedNaturally"]]
],
"HitSafetyCap"->Count[blindWorlds90,w_/;TrueQ[w["HitSafetyCap"]]],
"NineBranchWorlds"->Count[blindWorlds90,w_/;SameQ[w["BranchCount"],9]],
"TotalTraceSeconds"->Total@Lookup[blindWorlds90,"TraceSeconds"]
|>;

byTopology90=Map[Function[topology,Module[{worlds},
worlds=Select[blindWorlds90,SameQ[#1["Topology"],topology]&];
<|"Topology"->topology,"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"StopCorrect"->Count[worlds,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]]|>
]],blindTopologies90];
byDepth90=Map[Function[depth,Module[{worlds},
worlds=Select[blindWorlds90,SameQ[#1["Depth"],depth]&];
<|"Depth"->depth,"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"StopCorrect"->Count[worlds,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]]|>
]],blindDepths90];

Column[{
Dataset[Map[KeyTake[#,{"Topology","Depth","AlgebraTuple","TupleDistinct",
"AllPatchesValid","IdentityExact","InverseExact","CompositionExact",
"PathIndependenceExact","AllStatesSingleStop","UnaffectedPredictionInvariant",
"AllThirtySixWorldsCorrect"}]&,blindScenarios90]],
Dataset[byTopology90],Dataset[byDepth90],Dataset[{summary90}]
}]
'''.strip() + "\n"

audit = r'''
modelHashAfter90=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter90=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
decoderObjectHashAfter90=Hash[Normal[KeyDrop[frozenDecoderLoaded90,{"Classifier"}]],"SHA256","HexString"];
coreHashAfter90=Hash[CoreDefinitionBundle90[],"SHA256","HexString"];
canonicalizerHashAfter90=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},"SHA256","HexString"];
interventionHashAfter90=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter90=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"];
decoderRuntimeDefinitionHashAfter90=Hash[TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
testDefinitionHashAfter90=Hash[S90TestDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter90=Hash[Normal[protocol90],"SHA256","HexString"];
k33CandidateFileHashAfter90=FileSHA256Hex90[k33CandidatePath90];
decoderRuntimeFileHashAfter90=FileSHA256Hex90[decoderRuntimePath90];
decoderCandidateFileHashAfter90=FileSHA256Hex90[decoderCandidatePath90];
freezeCertificateFileHashAfter90=FileSHA256Hex90[freezeCertificatePath90];
s89CheckpointFileHashAfter90=FileSHA256Hex90[s89CheckpointPath90];

originalFrozenModelUnchanged90=SameQ[modelHashBefore90,modelHashAfter90,expectedFrozenModelHash90];
k33CandidateUnchanged90=And[SameQ[k33ObjectHashBefore90,k33ObjectHashAfter90],
SameQ[k33ObjectHashAfter90,expectedK33CandidateHash90],
SameQ[k33CandidateFileHashBefore90,k33CandidateFileHashAfter90],
SameQ[k33CandidateFileHashAfter90,expectedK33CandidateFileHash90]];
frozenDecoderUnchanged90=And[SameQ[decoderObjectHashBefore90,decoderObjectHashAfter90],
SameQ[decoderCandidateHashLoaded90,expectedDecoderCandidateHash90],
SameQ[decoderCandidateFileHashBefore90,decoderCandidateFileHashAfter90],
SameQ[decoderCandidateFileHashAfter90,expectedDecoderCandidateFileHash90]];
coreUnchanged90=SameQ[coreHashBefore90,coreHashAfter90];
canonicalizerUnchanged90=SameQ[canonicalizerHashBefore90,canonicalizerHashAfter90];
interventionCoreUnchanged90=SameQ[interventionHashBefore90,interventionHashAfter90];
topologyPrimitivesUnchanged90=SameQ[topologyPrimitiveHashBefore90,topologyPrimitiveHashAfter90];
decoderRuntimeUnchanged90=And[
SameQ[decoderRuntimeDefinitionHashBefore90,decoderRuntimeDefinitionHashAfter90],
SameQ[decoderRuntimeFileHashBefore90,decoderRuntimeFileHashAfter90],
SameQ[decoderRuntimeFileHashAfter90,expectedFeatureRuntimeFileHash90]];
testDefinitionUnchanged90=SameQ[testDefinitionHashBefore90,testDefinitionHashAfter90];
protocolUnchanged90=SameQ[protocolHash90,protocolHashAfter90];
freezeCertificateUnchanged90=And[
SameQ[freezeCertificateFileHashBefore90,freezeCertificateFileHashAfter90],
SameQ[freezeCertificateFileHashAfter90,expectedFreezeCertificateFileHash90]];
s89CheckpointUnchanged90=And[
SameQ[s89CheckpointFileHashBefore90,s89CheckpointFileHashAfter90],
SameQ[s89CheckpointFileHashAfter90,expectedS89CheckpointFileHash90]];
observationAggregationUnchanged90=SameQ[protocol90["ObservationAggregation"],
"FullQueriedObservationMultisetWithoutCodeDeduplication"];

testValidityPassed90=And[TrueQ[preflightPassed90],
TrueQ[originalFrozenModelUnchanged90],TrueQ[k33CandidateUnchanged90],
TrueQ[frozenDecoderUnchanged90],TrueQ[coreUnchanged90],
TrueQ[canonicalizerUnchanged90],TrueQ[interventionCoreUnchanged90],
TrueQ[topologyPrimitivesUnchanged90],TrueQ[decoderRuntimeUnchanged90],
TrueQ[testDefinitionUnchanged90],TrueQ[protocolUnchanged90],
TrueQ[freezeCertificateUnchanged90],TrueQ[s89CheckpointUnchanged90],
TrueQ[observationAggregationUnchanged90],
TrueQ[protocol90["NoCaseEvaluatedBeforeProtocolHash"]],
SameQ[summary90["Scenarios"],36],SameQ[summary90["Worlds"],1296],
SameQ[summary90["TupleDistinct"],36],SameQ[summary90["AllPatchesValid"],36],
SameQ[summary90["IdentityExact"],36],SameQ[summary90["InverseExact"],36],
SameQ[summary90["CompositionExact"],36],SameQ[summary90["PathIndependenceExact"],36],
SameQ[summary90["AllStatesSingleStop"],36],
SameQ[summary90["FourStateCasesDistinct"],36],
SameQ[summary90["AllStateGraphsSameAcrossQueries"],36],
SameQ[summary90["ReferenceActionsCorrectScenarios"],36],
SameQ[summary90["UnaffectedQueryRelations"],180],
SameQ[summary90["UnaffectedPredictionInvariant"],36],
SameQ[summary90["CanonicalCaseExactlyBase"],1296],
SameQ[summary90["ContractionCountCorrect"],1296],
SameQ[summary90["ProtectedNodesPreserved"],1296],
SameQ[summary90["ReferenceActionsCorrect"],1296],
SameQ[summary90["NonEmptyTokens"],1296],SameQ[summary90["ValidFeatureVectors"],1296],
SameQ[summary90["PredictionFailures"],0],SameQ[summary90["TerminatedNaturally"],1296],
SameQ[summary90["HitSafetyCap"],0],SameQ[summary90["NineBranchWorlds"],1296]];

blindPerfect90=And[TrueQ[testValidityPassed90],
SameQ[summary90["ContinueCorrect"],1152],SameQ[summary90["StopCorrect"],144],
SameQ[summary90["WorldCorrect"],1296],SameQ[summary90["ScenarioPerfect"],36]];
accuracy90=N[summary90["WorldCorrect"]/1296];
balancedAccuracy90=N@Mean[{summary90["ContinueCorrect"]/1152,summary90["StopCorrect"]/144}];
resultPayload90=<|"Stage"->"S90","Name"->"InterventionAlgebraBlind",
"CandidateHash"->decoderCandidateHashLoaded90,
"CandidateFileHash"->decoderCandidateFileHashAfter90,
"S89CheckpointFileHash"->s89CheckpointFileHashAfter90,
"ProtocolHash"->protocolHashAfter90,"TestDefinitionHash"->testDefinitionHashAfter90,
"Depths"->blindDepths90,"Topologies"->blindTopologies90,
"AlgebraTuples"->blindAlgebraTuples90,"Scenarios"->summary90["Scenarios"],
"Worlds"->summary90["Worlds"],"ContinueCorrect"->summary90["ContinueCorrect"],
"StopCorrect"->summary90["StopCorrect"],"WorldCorrect"->summary90["WorldCorrect"],
"Accuracy"->accuracy90,"BalancedAccuracy"->balancedAccuracy90,
"ScenarioPerfect"->summary90["ScenarioPerfect"],
"IdentityExact"->summary90["IdentityExact"],"InverseExact"->summary90["InverseExact"],
"CompositionExact"->summary90["CompositionExact"],
"PathIndependenceExact"->summary90["PathIndependenceExact"],
"UnaffectedQueryRelations"->summary90["UnaffectedQueryRelations"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged90],
"OriginalK33CandidateChanged"->!TrueQ[k33CandidateUnchanged90],
"FrozenDecoderChanged"->!TrueQ[frozenDecoderUnchanged90],
"CoreChanged"->!TrueQ[coreUnchanged90],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged90],
"InterventionCoreChanged"->!TrueQ[interventionCoreUnchanged90],
"TopologyPrimitivesChanged"->!TrueQ[topologyPrimitivesUnchanged90],
"FeatureRuntimeChanged"->!TrueQ[decoderRuntimeUnchanged90],
"TestDefinitionChangedDuringRun"->!TrueQ[testDefinitionUnchanged90],
"ProtocolChangedDuringRun"->!TrueQ[protocolUnchanged90],
"DeduplicationMechanismChanged"->!TrueQ[coreUnchanged90],
"ObservationAggregationChanged"->!TrueQ[observationAggregationUnchanged90],
"S89CheckpointChanged"->!TrueQ[s89CheckpointUnchanged90],
"TestValidityPassed"->testValidityPassed90,"BlindPerfect"->blindPerfect90|>;
blindResultHash90=Hash[Normal[resultPayload90],"SHA256","HexString"];
cert90=Join[resultPayload90,<|
"CandidateFrozenBeforeS90"->True,"BlindProtocolHashedBeforeCases"->True,
"S87DDecoderUsed"->True,"S89CheckpointLocked"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,"AllNineQueryPositionsTestedPerState"->True,
"S90IsBlindInterventionAlgebraTest"->True,
"MayClaimBlindInterventionAlgebraConsistency"->blindPerfect90,
"MayClaimGeneralCounterfactualReasoning"->False,"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary90["TotalTraceSeconds"],"BlindResultHash"->blindResultHash90,
"Outcome"->Which[!TrueQ[testValidityPassed90],"INVALID_S90_BLIND_TEST",
TrueQ[blindPerfect90],"S90_BLIND_INTERVENTION_ALGEBRA_PASS",
True,"S90_VALID_BLIND_FAILURE_DO_NOT_RETUNE"],
"SuggestedNextStage"->Which[!TrueQ[testValidityPassed90],
"S90R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",TrueQ[blindPerfect90],
"S91_BASELINE_AND_ABLATION_BENCHMARK",True,"S90A_FAILURE_AUDIT_WITHOUT_RETUNING"]|>];
certificateExportResult90=Quiet@Check[
Export[s90ResultCertificatePath,cert90,"RawJSON"],$Failed];
certificateExported90=And[StringQ[certificateExportResult90],FileExistsQ[s90ResultCertificatePath]];
Column[{Dataset[{cert90}],Dataset[{<|"CertificateExported"->certificateExported90,
"CertificatePath"->s90ResultCertificatePath,"CertificateFileHash"->If[
certificateExported90,FileSHA256Hex90[s90ResultCertificatePath],Missing[]]|>}]}]
'''.strip() + "\n"

cells = [architecture, preflight, definition, run, audit]
for number, cell in enumerate(cells, 1):
    check_delimiters(cell)
    for forbidden in ("Classify[", "BalancedTrainingRules", "allWorlds87A", "bestResult87C"):
        if forbidden in cell:
            raise RuntimeError(f"forbidden symbol in S90 cell {number}: {forbidden}")
combined = "\n".join(cells)
if combined.index("protocolHash90=") > combined.index("blindScenarios90="):
    raise RuntimeError("S90 cases precede protocol hash")

WL.write_text("\n\n".join(f"{MARKER}\n{cell}" for cell in cells), encoding="utf-8")

markdown = {"cell_type": "markdown", "metadata": {}, "source": [
    "# TCCT S90 - Blind Intervention-Algebra Test\n", "\n",
    "The S87D decoder and all TCCT mechanisms remain frozen. S90 uses an unseen "
    "nine-branch grammar and depths 73/121 to test identity, inverse, composition, "
    "path independence, and unaffected-query invariance.\n", "\n",
    "The protocol is hashed before case generation. No training, search, decoder "
    "editing, or retuning is performed. Expected workload: 1,296 worlds. Run once "
    "and preserve either success or failure.\n"]}


def code_cell(source: str, stage: str) -> dict:
    return {"cell_type": "code", "execution_count": None,
            "metadata": {"tcct_stage": stage}, "outputs": [],
            "source": source.splitlines(keepends=True)}


notebook = {"cells": [markdown,
    code_cell(architecture, "S90-ARCHITECTURE"),
    code_cell(preflight, "S90-PREFLIGHT"),
    code_cell(definition, "S90-PROTOCOL"),
    code_cell(run, "S90-BLIND-RUN"),
    code_cell(audit, "S90-AUDIT")],
    "metadata": {"kernelspec": {"display_name": "Wolfram Language 15",
    "language": "Wolfram Language", "name": "wolframlanguage15"},
    "language_info": {"codemirror_mode": "mathematica", "file_extension": ".wl",
    "mimetype": "application/vnd.wolfram.mathematica", "name": "Wolfram Language",
    "pygments_lexer": "mathematica", "version": "15.0"}},
    "nbformat": 4, "nbformat_minor": 5}
NB.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [markdown,
    code_cell(architecture, "S90-ARCHITECTURE"),
    code_cell(preflight, "S90-PREFLIGHT"),
    code_cell(definition, "S90-PROTOCOL")]
PREFLIGHT_NB.write_text(json.dumps(preflight_notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(f"{MARKER}\n{cell}" for cell in cells[:3]) +
    '\nPrint[InputForm[<|"PreflightPassed"->preflightPassed90,'
    '"ProtocolHash"->protocolHash90,"TestDefinitionHash"->testDefinitionHashBefore90,'
    '"CandidateHash"->decoderCandidateHashLoaded90,'
    '"S89CheckpointHash"->s89CheckpointFileHashBefore90,'
    '"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash90,'
    '"BlindScenariosDefined"->ValueQ[blindScenarios90],'
    '"S90ResultCertificateExists"->FileExistsQ[s90ResultCertificatePath]|>]];\n', encoding="utf-8")

LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S90_InterventionAlgebraBlind.ipynb"
set "TCCT_S89_RESULT=E:\engine_wolf\TCCT_S89_BlindResultCertificate.json"
set "TCCT_S90_RESULT=E:\engine_wolf\TCCT_S90_BlindResultCertificate.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s90"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s90"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S90 notebook not found & pause & exit /b 1)
if not exist "%TCCT_S89_RESULT%" (echo Locked S89 certificate not found & pause & exit /b 1)
if not exist "%TCCT_DECODER%" (echo Frozen decoder not found & pause & exit /b 1)
if exist "%TCCT_S90_RESULT%" (
  echo A prior S90 result certificate already exists.
  echo Preserve it and do not rerun or overwrite the blind test.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S90 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8903 --ServerApp.port_retries=5
exit /b 0
''', encoding="utf-8")

precommit = {"Stage": "S90", "Name": "InterventionAlgebraBlind",
    "BlindCasesGeneratedAtBuild": False,
    "BlindResultCertificatePresentAtBuild": Path(r"E:\engine_wolf\TCCT_S90_BlindResultCertificate.json").exists(),
    "CandidateFrozenBeforeProtocol": True,
    "S89CheckpointSHA256": "7d0f543f6f17384ee8969131547b2766aad1fbaed999e5b039c2708d6d89b032",
    "WolframSourceSHA256": sha256(WL), "NotebookSHA256": sha256(NB),
    "BranchCount": 9, "Depths": [73, 121],
    "Topologies": ["TripleSerialDiamondIn", "HierarchicalTerminalDiamondIn"],
    "ExpectedScenarios": 36, "ExpectedWorlds": 1296,
    "ExpectedContinueWorlds": 1152, "ExpectedStopWorlds": 144,
    "ExpectedUnaffectedQueryRelations": 180,
    "ProtocolHash": "ed241ba2ada54af6e44f9dc009a70f4155767de6994072c7c05e5b75515df518",
    "TestDefinitionHash": "ef31b96fa3a1ff1b4c7f4aec17456d60ec3381eca4df7f6ee8b9bf25f320539c",
    "DynamicPreflightPassed": True,
    "BlindCasesGeneratedAtPreflight": False,
    "S90ResultCertificatePresentAtPreflight": False,
    "TrainingRun": False, "CandidateSearchRun": False,
    "DecoderEditApplied": False, "RetuningApplied": False}
PRECOMMIT.write_text(json.dumps(precommit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, PRECOMMIT, LAUNCHER):
    print(path)
