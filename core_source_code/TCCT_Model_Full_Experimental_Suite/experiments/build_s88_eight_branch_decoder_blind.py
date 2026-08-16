import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S87_NOTEBOOK = ROOT / "TCCT_S87_SevenBranchMixedInterventionBlind.ipynb"
WL_OUTPUT = ROOT / "TCCT_S88_EightBranchFrozenDecoderBlind.wl"
NB_OUTPUT = ROOT / "TCCT_S88_EightBranchFrozenDecoderBlind.ipynb"
PREFLIGHT_WL_OUTPUT = ROOT / "TCCT_S88_EightBranchFrozenDecoderBlind_Preflight.wl"
PREFLIGHT_NB_OUTPUT = ROOT / "TCCT_S88_EightBranchFrozenDecoderBlind_Preflight.ipynb"
MARKER = "(* S88 CELL *)"


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
        elif char in ")]}" :
            if not stack or stack[-1][0] != pairs[char]:
                raise RuntimeError(
                    f"unbalanced Wolfram delimiter {char} at {index}"
                )
            stack.pop()
        index += 1
    if in_string or comment_depth or stack:
        raise RuntimeError(
            "unterminated Wolfram source: "
            f"string={in_string}, comment_depth={comment_depth}, "
            f"stack_tail={stack[-3:]}"
        )


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return source.replace(old, new, 1)


s87_cells = load_code_cells(S87_NOTEBOOK)
if len(s87_cells) != 5:
    raise RuntimeError("S87 notebook no longer has exactly five code cells")

architecture_cell = s87_cells[0].strip() + "\n"
s87_definition = s87_cells[2]
s87_run = s87_cells[3]

preflight_cell = r'''
expectedFrozenModelHash88=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash88=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedK33CandidateFileHash88=
"4a252b8977101d024b1b2feb00b4626ca28290c3982cdad199bc78ef7e0c98f1";
expectedDecoderCandidateHash88=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedDecoderCandidateFileHash88=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedClassifierBinaryHash88=
"2b8861c03c8169571061a85c12644c6e30a11e8f8f15f5c69c6761215f4752f1";
expectedFeatureRuntimeFileHash88=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedFreezeProtocolHash88=
"03d7a40eefdaec9d9fce599517d3663ba381d50218bfe4934580bd22ca31b86c";
expectedFreezeCertificateFileHash88=
"7c83717fc5bf50b1bde853401da8d0fc5931d6b1b23663d75777e1e45516fb8e";

k33CandidatePath88="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
decoderRuntimePath88="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
decoderCandidatePath88=
"E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
freezeCertificatePath88="E:/engine_wolf/TCCT_S87D_FreezeCertificate.json";
s88ResultCertificatePath=
"E:/engine_wolf/TCCT_S88_BlindResultCertificate.json";

ClearAll[FileSHA256Hex88];
FileSHA256Hex88[path_String]:=If[
FileExistsQ[path],
IntegerString[FileHash[path,"SHA256"],16,64],
Missing["FileMissing",path]
];

requiredFilesPresent88=And@@Map[
FileExistsQ,
{
k33CandidatePath88,decoderRuntimePath88,
decoderCandidatePath88,freezeCertificatePath88
}
];

If[
!TrueQ[requiredFilesPresent88],
Print["S88 aborted: one or more frozen input files are missing."];
Abort[]
];

If[
FileExistsQ[s88ResultCertificatePath],
Print["S88 aborted: a prior S88 result certificate already exists."];
Print["Preserve the prior blind result; do not overwrite or retune."];
Abort[]
];

k33CandidateFileHashBefore88=FileSHA256Hex88[k33CandidatePath88];
decoderRuntimeFileHashBefore88=FileSHA256Hex88[decoderRuntimePath88];
decoderCandidateFileHashBefore88=FileSHA256Hex88[decoderCandidatePath88];
freezeCertificateFileHashBefore88=FileSHA256Hex88[freezeCertificatePath88];

Clear[frozenCandidate86E];
Get[k33CandidatePath88];
k33CandidateHashLoaded88=If[
AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],
Missing["K33CandidateNotLoaded"]
];

Get[decoderRuntimePath88];
frozenDecoderLoaded88=TCCTLoadFrozenDecoderS87D[decoderCandidatePath88];
frozenDecoderRaw88=If[
AssociationQ[frozenDecoderLoaded88],
KeyDrop[frozenDecoderLoaded88,{"Classifier"}],
$Failed
];
decoderCandidateHashLoaded88=If[
AssociationQ[frozenDecoderRaw88],
Lookup[frozenDecoderRaw88,"CandidateHash",Missing["CandidateHashMissing"]],
Missing["DecoderNotLoaded"]
];
decoderPayloadHashLoaded88=If[
AssociationQ[frozenDecoderRaw88],
Hash[
Normal[KeyDrop[frozenDecoderRaw88,{"CandidateHash"}]],
"SHA256","HexString"
],
Missing["DecoderNotLoaded"]
];

freezeCertificate88=Quiet@Check[
Import[freezeCertificatePath88,"RawJSON"],
$Failed
];

ClearAll[CoreDefinitionBundle88];
CoreDefinitionBundle88[]:=CoreDefinitionBundle86[];

modelHashBefore88=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashBefore88=Hash[
Normal[frozenCandidate86E],"SHA256","HexString"
];
decoderObjectHashBefore88=If[
AssociationQ[frozenDecoderRaw88],
Hash[Normal[frozenDecoderRaw88],"SHA256","HexString"],
Missing["DecoderNotLoaded"]
];
coreHashBefore88=Hash[CoreDefinitionBundle88[],"SHA256","HexString"];
canonicalizerHashBefore88=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashBefore88=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyPrimitiveHashBefore88=Hash[
{
DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],
DownValues[HierarchicalDiamondIn80]
},
"SHA256","HexString"
];
decoderRuntimeDefinitionHashBefore88=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"
];

preflightPassed88=And[
TrueQ[preflightPassed86],
SameQ[modelHashBefore88,expectedFrozenModelHash88],
AssociationQ[frozenCandidate86E],
SameQ[k33CandidateHashLoaded88,expectedK33CandidateHash88],
SameQ[k33CandidateFileHashBefore88,expectedK33CandidateFileHash88],
SameQ[frozenCandidate86E["K"],33],
SameQ[frozenCandidate86E["Representation"],"KExactRole"],
AssociationQ[frozenDecoderLoaded88],
AssociationQ[frozenDecoderRaw88],
Head[frozenDecoderLoaded88["Classifier"]]===ClassifierFunction,
SameQ[decoderCandidateHashLoaded88,expectedDecoderCandidateHash88],
SameQ[decoderPayloadHashLoaded88,expectedDecoderCandidateHash88],
SameQ[decoderCandidateFileHashBefore88,expectedDecoderCandidateFileHash88],
SameQ[decoderRuntimeFileHashBefore88,expectedFeatureRuntimeFileHash88],
SameQ[frozenDecoderRaw88["ClassifierBinaryHash"],
expectedClassifierBinaryHash88],
SameQ[frozenDecoderRaw88["FeatureRuntimeFileHash"],
FileHash[decoderRuntimePath88,"SHA256"]],
SameQ[frozenDecoderRaw88["ProtocolHash"],expectedFreezeProtocolHash88],
SameQ[frozenDecoderRaw88["FeatureFamily"],"QueriedGlobalMoments"],
SameQ[frozenDecoderRaw88["FeatureDimension"],27],
SameQ[Length[frozenDecoderRaw88["FeatureNames"]],27],
SameQ[frozenDecoderRaw88["K"],33],
SameQ[frozenDecoderRaw88["BaseFrozenModelHash"],
expectedFrozenModelHash88],
SameQ[frozenDecoderRaw88["BaseK33CandidateHash"],
expectedK33CandidateHash88],
TrueQ[frozenDecoderRaw88["FrozenBeforeS88"]],
TrueQ[frozenDecoderRaw88["S88DataReadBeforeFreeze"]===False],
AssociationQ[freezeCertificate88],
SameQ[freezeCertificateFileHashBefore88,
expectedFreezeCertificateFileHash88],
TrueQ[freezeCertificate88["FreezeValidityPassed"]],
TrueQ[freezeCertificate88["ReadyForS88"]],
SameQ[freezeCertificate88["CandidateHash"],
expectedDecoderCandidateHash88],
SameQ[freezeCertificate88["Outcome"],
"S87D_DECODER_FROZEN_AND_LOCKED_READY_FOR_S88"],
TrueQ[freezeCertificate88["CoreChanged"]===False],
TrueQ[freezeCertificate88["S88DataReadBeforeFreeze"]===False],
!FileExistsQ[s88ResultCertificatePath]
];

preflight88=<|
"Stage"->"S88",
"Name"->"EightBranchFrozenDecoderBlind",
"CandidateFrozenBeforeProtocol"->True,
"DecoderCandidateHash"->decoderCandidateHashLoaded88,
"DecoderCandidateFileHash"->decoderCandidateFileHashBefore88,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore88,
"K33CandidateHash"->k33CandidateHashLoaded88,
"FeatureFamily"->If[
AssociationQ[frozenDecoderRaw88],
frozenDecoderRaw88["FeatureFamily"],Missing[]
],
"FeatureDimension"->If[
AssociationQ[frozenDecoderRaw88],
frozenDecoderRaw88["FeatureDimension"],Missing[]
],
"BranchCount"->8,
"Depths"->{61,109},
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DecoderEditApplied"->False,
"RetuningApplied"->False,
"S88ResultAlreadyPresent"->FileExistsQ[s88ResultCertificatePath],
"PreflightPassed"->preflightPassed88
|>;

If[
!TrueQ[preflightPassed88],
Print[Dataset[{preflight88}]];
Print["S88 aborted: frozen decoder, architecture, or file lock mismatch."];
Abort[]
];

Dataset[{preflight88}]
'''.strip() + "\n"

definition_cell = s87_definition.replace("87", "88")
definition_cell = definition_cell.replace("PredictTokens88", "LegacyPredictTokens88")
definition_cell = replace_once(
    definition_cell,
    "LegacyPredictTokens88,\nSetAnswer88,",
    "LegacyPredictTokens88,\nPredictFrozenDecoder88,\n"
    "TripleSerialDiamondIn88,\nHierarchicalTerminalDiamondIn88,\nSetAnswer88,",
    "S88 ClearAll additions",
)
definition_cell = replace_once(
    definition_cell,
    "T88[depth,target,answer,88000000+100 depth,7];",
    "T88[depth,target,answer,88000000+100 depth,8];",
    "S88 branch-count wrapper",
)
legacy_definition = r'''LegacyPredictTokens88[tokens_List]:=If[
AnyTrue[tokens,MemberQ[frozenCandidate86E["Policy"],#]&],
"Continue",
"Stop"
];'''
decoder_definition = legacy_definition + r'''

PredictFrozenDecoder88[observations_List]:=Module[{probe,prediction},
probe=<|"Observations"->observations|>;
prediction=TCCTPredictWorldS87D[probe,frozenDecoderLoaded88];
If[MemberQ[{"Continue","Stop"},prediction],prediction,$Failed]
];'''
definition_cell = replace_once(
    definition_cell,
    legacy_definition,
    decoder_definition,
    "S88 frozen-decoder predictor",
)
old_topology = r'''TopologyTransform88[topology_String,c_List]:=Switch[
topology,
"DoubleDiamondIn",DoubleDiamondIn79[c],
"HierarchicalDiamondIn",HierarchicalDiamondIn80[c],
_,$Failed
];

ExpectedContractions88[topology_String,baseCase_List]:=Switch[
topology,
"DoubleDiamondIn",2 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];'''
new_topology = r'''TripleSerialDiamondIn88[c_List]:=
DiamondIn72[DoubleDiamondIn79[c]];

HierarchicalTerminalDiamondIn88[c_List]:=
DiamondIn72[HierarchicalDiamondIn80[c]];

TopologyTransform88[topology_String,c_List]:=Switch[
topology,
"TripleSerialDiamondIn",TripleSerialDiamondIn88[c],
"HierarchicalTerminalDiamondIn",HierarchicalTerminalDiamondIn88[c],
_,$Failed
];

ExpectedContractions88[topology_String,baseCase_List]:=Switch[
topology,
"TripleSerialDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalTerminalDiamondIn",4 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]
];'''
definition_cell = replace_once(
    definition_cell,
    old_topology,
    new_topology,
    "S88 composed topology definitions",
)
definition_cell = replace_once(
    definition_cell,
    "traceSeconds,trace,levels,pack,vertexList,packedNodes,\n"
    "observations,originalNode,pair,roleInfo,rawTokens,tokens,prediction",
    "traceSeconds,trace,levels,pack,vertexList,packedNodes,\n"
    "observations,originalNode,pair,roleInfo,rawTokens,tokens,"
    "featureVector,legacyPrediction,prediction",
    "S88 PrepareWorld locals",
)
old_prediction = r'''rawTokens=({#1["Role"],#1["Code"]}&)/@observations;
tokens=DeleteDuplicates[rawTokens];
prediction=LegacyPredictTokens88[tokens];'''
new_prediction = r'''rawTokens=({#1["Role"],#1["Code"]}&)/@observations;
tokens=DeleteDuplicates[rawTokens];
featureVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
legacyPrediction=LegacyPredictTokens88[tokens];
prediction=PredictFrozenDecoder88[observations];'''
definition_cell = replace_once(
    definition_cell,
    old_prediction,
    new_prediction,
    "S88 world prediction",
)
definition_cell = replace_once(
    definition_cell,
    '"Prediction"->prediction,\n"Correct"->SameQ[prediction,target],',
    '"Prediction"->prediction,\n"LegacyPrediction"->legacyPrediction,\n'
    '"FeatureVector"->featureVector,\n"Correct"->SameQ[prediction,target],',
    "S88 world result fields",
)
definition_cell = definition_cell.replace(
    '"PolicyHitTokens"->Intersection[tokens,frozenCandidate86E["Policy"]],',
    '"LegacyPolicyHitTokens"->Intersection[tokens,frozenCandidate86E["Policy"]],',
)
definition_cell = replace_once(
    definition_cell,
    "branchCount=7,seedCase",
    "branchCount=8,seedCase",
    "S88 PrepareScenario branch count",
)
definition_cell = definition_cell.replace(
    "AllFourteenWorldsCorrect", "AllSixteenWorldsCorrect"
)
bundle_anchor = (
    "DownValues[NodeRole88],DownValues[EncodePair88],"
    "DownValues[LegacyPredictTokens88],\n"
    "DownValues[SetAnswer88],DownValues[TopologyTransform88],"
)
bundle_replacement = (
    "DownValues[NodeRole88],DownValues[EncodePair88],"
    "DownValues[LegacyPredictTokens88],\n"
    "DownValues[PredictFrozenDecoder88],"
    "DownValues[TripleSerialDiamondIn88],\n"
    "DownValues[HierarchicalTerminalDiamondIn88],"
    "DownValues[SetAnswer88],DownValues[TopologyTransform88],"
)
definition_cell = replace_once(
    definition_cell,
    bundle_anchor,
    bundle_replacement,
    "S88 definition bundle",
)

protocol_index = definition_cell.find("blindDepths88=")
if protocol_index < 0:
    raise RuntimeError("S88 protocol boundary missing")
definition_cell = definition_cell[:protocol_index].rstrip() + r'''

blindDepths88={61,109};
blindTopologies88={
"TripleSerialDiamondIn",
"HierarchicalTerminalDiamondIn"
};
blindInterventionPairs88={
{1,4},{2,5},{3,6},{4,7},{5,8},{6,1},{7,2},{8,3}
};

topologySpec88=<|
"TripleSerialDiamondIn"-><|
"Composition"->"DiamondIn72AfterDoubleDiamondIn79",
"PrivateDiamondsPerOriginalIncomingEdge"->3,
"PreviouslyEvaluatedAsComposition"->False
|>,
"HierarchicalTerminalDiamondIn"-><|
"Composition"->"DiamondIn72AfterHierarchicalDiamondIn80",
"PrivateDiamondsPerOriginalIncomingEdge"->4,
"PreviouslyEvaluatedAsComposition"->False
|>
|>;
topologySpecHash88=Hash[Normal[topologySpec88],"SHA256","HexString"];
testDefinitionHashBefore88=Hash[
S88TestDefinitionBundle[],"SHA256","HexString"
];
noCasesBeforeProtocolHash88=And[
!ValueQ[blindScenarios88],
!ValueQ[blindWorldPairs88],
!ValueQ[blindWorlds88]
];

protocol88=<|
"Stage"->"S88",
"Name"->"EightBranchFrozenDecoderBlind",
"Candidate"->"S87D-FrozenWorldMultisetDecoder",
"CandidateHash"->decoderCandidateHashLoaded88,
"CandidateFileHash"->decoderCandidateFileHashBefore88,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore88,
"K33CandidateHash"->k33CandidateHashLoaded88,
"BranchCount"->8,
"Depths"->blindDepths88,
"Topologies"->blindTopologies88,
"TopologySpecHash"->topologySpecHash88,
"InterventionPairs"->blindInterventionPairs88,
"ExpectedScenarios"->32,
"ExpectedWorldPairs"->256,
"ExpectedWorlds"->512,
"ExpectedBaselineWorlds"->256,
"ExpectedInterventionContinueWorlds"->224,
"ExpectedInterventionStopWorlds"->32,
"ExternalGrammar"->"IndependentEightBranchT88",
"Intervention"->"OneRedundantPathCutPlusOneBranchStopPatch",
"QueryGrid"->"AllEightQueriesBeforeAndAfterMixedIntervention",
"FeatureFamily"->"QueriedGlobalMoments",
"FeatureDimension"->27,
"ObservationAggregation"->
"FullQueriedObservationMultisetWithoutCodeDeduplication",
"LegacyTokenDeduplication"->"DeleteDuplicatesAfterExactRoleCodePairing",
"SuccessCriterion"->
"ValidHarnessAndAll512WorldsCorrectIncludingBothClasses",
"CandidateFrozenBeforeProtocol"->True,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DecoderEditApplied"->False,
"RetuningApplied"->False,
"S87LabelsReadByS88"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash88
|>;

protocolHash88=Hash[Normal[protocol88],"SHA256","HexString"];

Dataset[{Join[protocol88,<|
"ProtocolHash"->protocolHash88,
"TestDefinitionHash"->testDefinitionHashBefore88
|>]}]
'''.strip() + "\n"

run_cell = s87_run.replace("87", "88")
run_cell = run_cell.replace("AllFourteenWorldsCorrect", "AllSixteenWorldsCorrect")
run_cell = run_cell.replace("SevenBranchWorlds", "EightBranchWorlds")
run_cell = replace_once(
    run_cell,
    'SameQ[w["BranchCount"],7]',
    'SameQ[w["BranchCount"],8]',
    "S88 run branch validation",
)
run_cell = replace_once(
    run_cell,
    '"TotalTraceSeconds"->Total@Lookup[blindWorlds88,"TraceSeconds"]',
    '"ValidFeatureVectors"->Count[blindWorlds88,w_/;\n'
    'VectorQ[w["FeatureVector"],IntegerQ]&&Length[w["FeatureVector"]]===27],\n'
    '"PredictionFailures"->Count[blindWorlds88,w_/;SameQ[w["Prediction"],$Failed]],\n'
    '"TotalTraceSeconds"->Total@Lookup[blindWorlds88,"TraceSeconds"]',
    "S88 feature summary",
)
column_anchor = "Column[{\nDataset[Map["
by_depth = r'''
byDepth88=Map[
Function[depth,
Module[{worlds,base,intervention},
worlds=Select[blindWorlds88,SameQ[#1["Depth"],depth]&];
base=Select[worlds,SameQ[#1["GraphCondition"],"Baseline"]&];
intervention=Select[
worlds,SameQ[#1["GraphCondition"],"MixedPathCutStopIntervention"]&
];
<|
"Depth"->depth,
"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"BaselineCorrect"->Count[base,w_/;TrueQ[w["Correct"]]],
"InterventionContinueCorrect"->Count[
intervention,w_/;SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]
],
"InterventionStopCorrect"->Count[
intervention,w_/;SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]
]
|>
]
],
blindDepths88
];

'''
run_cell = replace_once(
    run_cell,
    column_anchor,
    by_depth + column_anchor,
    "S88 by-depth summary",
)
run_cell = replace_once(
    run_cell,
    "Dataset[byTopology88],\nDataset[{summary88}]",
    "Dataset[byTopology88],\nDataset[byDepth88],\nDataset[{summary88}]",
    "S88 summary outputs",
)
run_cell = run_cell.strip() + "\n"

audit_cell = r'''
modelHashAfter88=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter88=Hash[
Normal[frozenCandidate86E],"SHA256","HexString"
];
decoderObjectHashAfter88=Hash[
Normal[KeyDrop[frozenDecoderLoaded88,{"Classifier"}]],
"SHA256","HexString"
];
coreHashAfter88=Hash[CoreDefinitionBundle88[],"SHA256","HexString"];
canonicalizerHashAfter88=Hash[
{
DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]
},
"SHA256","HexString"
];
interventionHashAfter88=Hash[
{
DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]
},
"SHA256","HexString"
];
topologyPrimitiveHashAfter88=Hash[
{
DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],
DownValues[HierarchicalDiamondIn80]
},
"SHA256","HexString"
];
decoderRuntimeDefinitionHashAfter88=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"
];
testDefinitionHashAfter88=Hash[
S88TestDefinitionBundle[],"SHA256","HexString"
];
protocolHashAfter88=Hash[Normal[protocol88],"SHA256","HexString"];

k33CandidateFileHashAfter88=FileSHA256Hex88[k33CandidatePath88];
decoderRuntimeFileHashAfter88=FileSHA256Hex88[decoderRuntimePath88];
decoderCandidateFileHashAfter88=FileSHA256Hex88[decoderCandidatePath88];
freezeCertificateFileHashAfter88=FileSHA256Hex88[freezeCertificatePath88];

originalFrozenModelUnchanged88=SameQ[
modelHashBefore88,modelHashAfter88,expectedFrozenModelHash88
];
k33CandidateUnchanged88=And[
SameQ[k33ObjectHashBefore88,k33ObjectHashAfter88],
SameQ[k33ObjectHashAfter88,expectedK33CandidateHash88],
SameQ[k33CandidateFileHashBefore88,k33CandidateFileHashAfter88],
SameQ[k33CandidateFileHashAfter88,expectedK33CandidateFileHash88]
];
frozenDecoderUnchanged88=And[
SameQ[decoderObjectHashBefore88,decoderObjectHashAfter88],
SameQ[decoderCandidateHashLoaded88,expectedDecoderCandidateHash88],
SameQ[decoderCandidateFileHashBefore88,decoderCandidateFileHashAfter88],
SameQ[decoderCandidateFileHashAfter88,expectedDecoderCandidateFileHash88]
];
coreUnchanged88=SameQ[coreHashBefore88,coreHashAfter88];
canonicalizerUnchanged88=SameQ[
canonicalizerHashBefore88,canonicalizerHashAfter88
];
interventionUnchanged88=SameQ[
interventionHashBefore88,interventionHashAfter88
];
topologyPrimitivesUnchanged88=SameQ[
topologyPrimitiveHashBefore88,topologyPrimitiveHashAfter88
];
decoderRuntimeUnchanged88=And[
SameQ[
decoderRuntimeDefinitionHashBefore88,
decoderRuntimeDefinitionHashAfter88
],
SameQ[decoderRuntimeFileHashBefore88,decoderRuntimeFileHashAfter88],
SameQ[decoderRuntimeFileHashAfter88,expectedFeatureRuntimeFileHash88]
];
testDefinitionUnchanged88=SameQ[
testDefinitionHashBefore88,testDefinitionHashAfter88
];
protocolUnchanged88=SameQ[protocolHash88,protocolHashAfter88];
freezeCertificateUnchanged88=And[
SameQ[
freezeCertificateFileHashBefore88,
freezeCertificateFileHashAfter88
],
SameQ[
freezeCertificateFileHashAfter88,
expectedFreezeCertificateFileHash88
]
];
observationAggregationUnchanged88=SameQ[
protocol88["ObservationAggregation"],
"FullQueriedObservationMultisetWithoutCodeDeduplication"
];

testValidityPassed88=And[
TrueQ[preflightPassed88],
TrueQ[originalFrozenModelUnchanged88],
TrueQ[k33CandidateUnchanged88],
TrueQ[frozenDecoderUnchanged88],
TrueQ[coreUnchanged88],
TrueQ[canonicalizerUnchanged88],
TrueQ[interventionUnchanged88],
TrueQ[topologyPrimitivesUnchanged88],
TrueQ[decoderRuntimeUnchanged88],
TrueQ[testDefinitionUnchanged88],
TrueQ[protocolUnchanged88],
TrueQ[freezeCertificateUnchanged88],
TrueQ[observationAggregationUnchanged88],
TrueQ[protocol88["NoCaseEvaluatedBeforeProtocolHash"]],
SameQ[summary88["Scenarios"],32],
SameQ[summary88["WorldPairs"],256],
SameQ[summary88["Worlds"],512],
SameQ[summary88["StopPatchedQueryPairs"],32],
SameQ[summary88["NonStopQueryPairs"],224],
SameQ[summary88["MixedInterventionValidity"],32],
SameQ[summary88["MixedInterventionNoConflict"],32],
SameQ[summary88["MixedEditCountCorrect"],32],
SameQ[summary88["BaselineSameGraphAcrossQueries"],32],
SameQ[summary88["InterventionSameGraphAcrossQueries"],32],
SameQ[summary88["MixedInterventionChangesGraph"],32],
SameQ[summary88["ReferenceRelationsCorrect"],256],
SameQ[summary88["CanonicalCaseExactlyBase"],512],
SameQ[summary88["ContractionCountCorrect"],512],
SameQ[summary88["ProtectedNodesPreserved"],512],
SameQ[summary88["ReferenceActionsCorrect"],512],
SameQ[summary88["NonEmptyTokens"],512],
SameQ[summary88["ValidFeatureVectors"],512],
SameQ[summary88["PredictionFailures"],0],
SameQ[summary88["TerminatedNaturally"],512],
SameQ[summary88["HitSafetyCap"],0],
SameQ[summary88["EightBranchWorlds"],512]
];

blindPerfect88=And[
TrueQ[testValidityPassed88],
SameQ[summary88["BaselineCorrect"],256],
SameQ[summary88["InterventionContinueCorrect"],224],
SameQ[summary88["InterventionStopCorrect"],32],
SameQ[summary88["WorldCorrect"],512],
SameQ[summary88["PairCorrect"],256],
SameQ[summary88["PredictionRelationsCorrect"],256],
SameQ[summary88["ScenarioPerfect"],32]
];

continueCases88=480;
stopCases88=32;
continueCorrect88=
summary88["BaselineCorrect"]+summary88["InterventionContinueCorrect"];
stopCorrect88=summary88["InterventionStopCorrect"];
accuracy88=N[summary88["WorldCorrect"]/512];
balancedAccuracy88=N@Mean[{
continueCorrect88/continueCases88,
stopCorrect88/stopCases88
}];

resultPayload88=<|
"Stage"->"S88",
"Name"->"EightBranchFrozenDecoderBlind",
"CandidateHash"->decoderCandidateHashLoaded88,
"CandidateFileHash"->decoderCandidateFileHashAfter88,
"ProtocolHash"->protocolHashAfter88,
"TestDefinitionHash"->testDefinitionHashAfter88,
"Depths"->blindDepths88,
"Topologies"->blindTopologies88,
"InterventionPairs"->blindInterventionPairs88,
"Scenarios"->summary88["Scenarios"],
"WorldPairs"->summary88["WorldPairs"],
"Worlds"->summary88["Worlds"],
"BaselineCorrect"->summary88["BaselineCorrect"],
"InterventionContinueCorrect"->
summary88["InterventionContinueCorrect"],
"InterventionStopCorrect"->summary88["InterventionStopCorrect"],
"WorldCorrect"->summary88["WorldCorrect"],
"Accuracy"->accuracy88,
"BalancedAccuracy"->balancedAccuracy88,
"PairCorrect"->summary88["PairCorrect"],
"PredictionRelationsCorrect"->summary88["PredictionRelationsCorrect"],
"ScenarioPerfect"->summary88["ScenarioPerfect"],
"OriginalFrozenModelChanged"->!TrueQ[originalFrozenModelUnchanged88],
"OriginalK33CandidateChanged"->!TrueQ[k33CandidateUnchanged88],
"FrozenDecoderChanged"->!TrueQ[frozenDecoderUnchanged88],
"CoreChanged"->!TrueQ[coreUnchanged88],
"CanonicalizerChanged"->!TrueQ[canonicalizerUnchanged88],
"InterventionChanged"->!TrueQ[interventionUnchanged88],
"TopologyPrimitivesChanged"->!TrueQ[topologyPrimitivesUnchanged88],
"FeatureRuntimeChanged"->!TrueQ[decoderRuntimeUnchanged88],
"TestDefinitionChangedDuringRun"->!TrueQ[testDefinitionUnchanged88],
"ProtocolChangedDuringRun"->!TrueQ[protocolUnchanged88],
"DeduplicationMechanismChanged"->!TrueQ[coreUnchanged88],
"ObservationAggregationChanged"->!TrueQ[observationAggregationUnchanged88],
"TestValidityPassed"->testValidityPassed88,
"BlindPerfect"->blindPerfect88
|>;

blindResultHash88=Hash[
Normal[resultPayload88],"SHA256","HexString"
];

cert88=Join[
resultPayload88,
<|
"CandidateFrozenBeforeS88"->True,
"BlindProtocolHashedBeforeCases"->True,
"S87DDecoderUsed"->True,
"TrainingRun"->False,
"CandidateSearchRun"->False,
"DecoderEditApplied"->False,
"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"S87LabelsReadByS88"->False,
"AllEightQueryPositionsTestedPerGraph"->True,
"SameQueryBeforeAfterIntervention"->True,
"S88IsBlindCounterfactualCompositionTest"->True,
"MayClaimBlindEightBranchCompositionalTransfer"->blindPerfect88,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary88["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash88,
"Outcome"->Which[
!TrueQ[testValidityPassed88],
"INVALID_S88_BLIND_TEST",
TrueQ[blindPerfect88],
"S88_BLIND_EIGHT_BRANCH_FROZEN_DECODER_PASS",
True,
"S88_VALID_BLIND_FAILURE_DO_NOT_RETUNE"
],
"SuggestedNextStage"->Which[
!TrueQ[testValidityPassed88],
"S88R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",
TrueQ[blindPerfect88],
"S89_NEW_INTERVENTION_SEMANTICS_BLIND",
True,
"S88A_FAILURE_AUDIT_WITHOUT_RETUNING"
]
|>
];

certificateExportResult88=Quiet@Check[
Export[s88ResultCertificatePath,cert88,"RawJSON"],
$Failed
];
certificateExported88=And[
StringQ[certificateExportResult88],
FileExistsQ[s88ResultCertificatePath]
];

Column[{
Dataset[{cert88}],
Dataset[{<|
"CertificateExported"->certificateExported88,
"CertificatePath"->s88ResultCertificatePath,
"CertificateFileHash"->If[
certificateExported88,FileSHA256Hex88[s88ResultCertificatePath],Missing[]
]
|>}]
}]
'''.strip() + "\n"

cells = [
    architecture_cell,
    preflight_cell,
    definition_cell,
    run_cell,
    audit_cell,
]
for index, cell in enumerate(cells, start=1):
    check_wl_delimiters(cell)
    if "S87A" in cell or "allWorlds87A" in cell or "auditDataPayload87B" in cell:
        raise RuntimeError(f"revealed S87 research state leaked into S88 cell {index}")

protocol_and_run = definition_cell + "\n(* S88 RUN BOUNDARY *)\n" + run_cell
if protocol_and_run.index("protocolHash88=") > protocol_and_run.index(
    "blindScenarios88="
):
    raise RuntimeError("S88 cases could be generated before protocol hashing")
for forbidden in (
    "bestResult87C",
    "cert87C",
    "allWorlds87A",
    "auditDataPayload87B",
    "Classify[",
    "BalancedTrainingRules",
):
    if forbidden in "\n".join(cells):
        raise RuntimeError(f"training or revealed-data symbol leaked into S88: {forbidden}")

wl_source = "\n\n".join(f"{MARKER}\n{cell}" for cell in cells)
WL_OUTPUT.write_text(wl_source, encoding="utf-8")

markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S88 - Eight-Branch Frozen-Decoder Blind Test\n",
        "\n",
        "S87D was frozen and hash-locked before this notebook was built. "
        "S88 evaluates the unchanged 27-dimensional QueriedGlobalMoments "
        "extractor and frozen decision tree on an unseen eight-branch grammar, "
        "depths 61 and 109, two new private-diamond topology compositions, "
        "and eight unseen mixed-intervention pairs.\n",
        "\n",
        "This notebook performs no training, model selection, decoder editing, "
        "or retuning. Run once from a fresh kernel and retain either success or "
        "failure. Expected workload: 512 worlds; execution may take several minutes.\n",
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
        code_cell(architecture_cell, "S88-ARCHITECTURE"),
        code_cell(preflight_cell, "S88-PREFLIGHT"),
        code_cell(definition_cell, "S88-PROTOCOL"),
        code_cell(run_cell, "S88-BLIND-RUN"),
        code_cell(audit_cell, "S88-AUDIT"),
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
    json.dumps(notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)

preflight_cells = cells[:3]
preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [
    markdown,
    *[
        code_cell(source, stage)
        for source, stage in zip(
            preflight_cells,
            ("S88-ARCHITECTURE", "S88-PREFLIGHT", "S88-PROTOCOL"),
        )
    ],
]
PREFLIGHT_NB_OUTPUT.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL_OUTPUT.write_text(
    "\n\n".join(f"{MARKER}\n{cell}" for cell in preflight_cells)
    + "\n\n"
    + 'Print[InputForm[<|"PreflightPassed"->preflightPassed88,'
    + '"ProtocolHash"->protocolHash88,'
    + '"TestDefinitionHash"->testDefinitionHashBefore88,'
    + '"CandidateHash"->decoderCandidateHashLoaded88,'
    + '"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash88|>]];\n',
    encoding="utf-8",
)

for path in (
    WL_OUTPUT,
    NB_OUTPUT,
    PREFLIGHT_WL_OUTPUT,
    PREFLIGHT_NB_OUTPUT,
):
    print(path)
