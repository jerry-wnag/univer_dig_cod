"""Build TCCT S92: balanced, naturally cardinality-matched blind test."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_NB = ROOT / "TCCT_S90_InterventionAlgebraBlind.ipynb"
WL = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind.wl"
NB = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S92_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S92_Precommit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


source_notebook = json.loads(SOURCE_NB.read_text(encoding="utf-8"))
source_cells = [
    "".join(cell.get("source", []))
    for cell in source_notebook.get("cells", [])
    if cell.get("cell_type") == "code" and "".join(cell.get("source", [])).strip()
]
if len(source_cells) < 5:
    raise RuntimeError("the locked S90 notebook does not contain five source cells")
architecture = source_cells[0].strip()

preflight = r'''
expectedFrozenModelHash92=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash92=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedK33CandidateFileHash92=
"4a252b8977101d024b1b2feb00b4626ca28290c3982cdad199bc78ef7e0c98f1";
expectedDecoderCandidateHash92=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedDecoderCandidateFileHash92=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedClassifierBinaryHash92=
"2b8861c03c8169571061a85c12644c6e30a11e8f8f15f5c69c6761215f4752f1";
expectedFeatureRuntimeFileHash92=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedFreezeProtocolHash92=
"03d7a40eefdaec9d9fce599517d3663ba381d50218bfe4934580bd22ca31b86c";
expectedFreezeCertificateFileHash92=
"7c83717fc5bf50b1bde853401da8d0fc5931d6b1b23663d75777e1e45516fb8e";
expectedS90CheckpointFileHash92=
"0e8c9df9e63ea68d59226416de33243440ef4b84a007be0812b2970ed53deb30";
expectedS91CheckpointFileHash92=
"cf335bda73b8a26eacbf32d8d25dcad737a84d503a6f0849dbcd3afc3f1df8cd";

k33CandidatePath92="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
decoderRuntimePath92="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
decoderCandidatePath92="E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
freezeCertificatePath92="E:/engine_wolf/TCCT_S87D_FreezeCertificate.json";
s90CheckpointPath92="E:/engine_wolf/TCCT_S90_BlindResultCertificate.json";
s91CheckpointPath92="E:/engine_wolf/TCCT_S91_BenchmarkCertificate.json";
s92ResultCertificatePath="E:/engine_wolf/TCCT_S92_BlindResultCertificate.json";

ClearAll[FileSHA256Hex92];
FileSHA256Hex92[path_String]:=If[FileExistsQ[path],
IntegerString[FileHash[path,"SHA256"],16,64],Missing["FileMissing",path]];
requiredFilesPresent92=And@@(FileExistsQ/@{
k33CandidatePath92,decoderRuntimePath92,decoderCandidatePath92,
freezeCertificatePath92,s90CheckpointPath92,s91CheckpointPath92});
If[!TrueQ[requiredFilesPresent92],
Print["S92 aborted: one or more locked input files are missing."];Abort[]];
If[FileExistsQ[s92ResultCertificatePath],
Print["S92 aborted: a prior S92 result certificate already exists."];
Print["Preserve it; do not overwrite or retune."];Abort[]];

k33CandidateFileHashBefore92=FileSHA256Hex92[k33CandidatePath92];
decoderRuntimeFileHashBefore92=FileSHA256Hex92[decoderRuntimePath92];
decoderCandidateFileHashBefore92=FileSHA256Hex92[decoderCandidatePath92];
freezeCertificateFileHashBefore92=FileSHA256Hex92[freezeCertificatePath92];
s90CheckpointFileHashBefore92=FileSHA256Hex92[s90CheckpointPath92];
s91CheckpointFileHashBefore92=FileSHA256Hex92[s91CheckpointPath92];

Clear[frozenCandidate86E];Get[k33CandidatePath92];
k33CandidateHashLoaded92=If[AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],Missing[]];
Get[decoderRuntimePath92];
frozenDecoderLoaded92=TCCTLoadFrozenDecoderS87D[decoderCandidatePath92];
frozenDecoderRaw92=If[AssociationQ[frozenDecoderLoaded92],
KeyDrop[frozenDecoderLoaded92,{"Classifier"}],$Failed];
decoderCandidateHashLoaded92=If[AssociationQ[frozenDecoderRaw92],
Lookup[frozenDecoderRaw92,"CandidateHash",Missing[]],Missing[]];
decoderPayloadHashLoaded92=If[AssociationQ[frozenDecoderRaw92],
Hash[Normal[KeyDrop[frozenDecoderRaw92,{"CandidateHash"}]],
"SHA256","HexString"],Missing[]];
freezeCertificate92=Quiet@Check[Import[freezeCertificatePath92,"RawJSON"],$Failed];
s90Checkpoint92=Quiet@Check[Import[s90CheckpointPath92,"RawJSON"],$Failed];
s91Checkpoint92=Quiet@Check[Import[s91CheckpointPath92,"RawJSON"],$Failed];

ClearAll[CoreDefinitionBundle92];
CoreDefinitionBundle92[]:=CoreDefinitionBundle86[];
modelHashBefore92=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashBefore92=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
decoderObjectHashBefore92=If[AssociationQ[frozenDecoderRaw92],
Hash[Normal[frozenDecoderRaw92],"SHA256","HexString"],Missing[]];
coreHashBefore92=Hash[CoreDefinitionBundle92[],"SHA256","HexString"];
canonicalizerHashBefore92=Hash[{
DownValues[FindPrivateDiamond79B],DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]},"SHA256","HexString"];
interventionHashBefore92=Hash[{
DownValues[LocalMediatorSources82],DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],DownValues[ReferenceAction82]},
"SHA256","HexString"];
topologyPrimitiveHashBefore92=Hash[{
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],
DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"];
decoderRuntimeDefinitionHashBefore92=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];

preflightPassed92=And[
TrueQ[preflightPassed86],SameQ[modelHashBefore92,expectedFrozenModelHash92],
AssociationQ[frozenCandidate86E],
SameQ[k33CandidateHashLoaded92,expectedK33CandidateHash92],
SameQ[k33CandidateFileHashBefore92,expectedK33CandidateFileHash92],
SameQ[frozenCandidate86E["K"],33],
SameQ[frozenCandidate86E["Representation"],"KExactRole"],
AssociationQ[frozenDecoderLoaded92],AssociationQ[frozenDecoderRaw92],
Head[frozenDecoderLoaded92["Classifier"]]===ClassifierFunction,
SameQ[decoderCandidateHashLoaded92,expectedDecoderCandidateHash92],
SameQ[decoderPayloadHashLoaded92,expectedDecoderCandidateHash92],
SameQ[decoderCandidateFileHashBefore92,expectedDecoderCandidateFileHash92],
SameQ[decoderRuntimeFileHashBefore92,expectedFeatureRuntimeFileHash92],
SameQ[frozenDecoderRaw92["ClassifierBinaryHash"],expectedClassifierBinaryHash92],
SameQ[frozenDecoderRaw92["FeatureRuntimeFileHash"],
FileHash[decoderRuntimePath92,"SHA256"]],
SameQ[frozenDecoderRaw92["ProtocolHash"],expectedFreezeProtocolHash92],
SameQ[frozenDecoderRaw92["FeatureFamily"],"QueriedGlobalMoments"],
SameQ[frozenDecoderRaw92["FeatureDimension"],27],
SameQ[frozenDecoderRaw92["K"],33],
SameQ[frozenDecoderRaw92["BaseFrozenModelHash"],expectedFrozenModelHash92],
SameQ[frozenDecoderRaw92["BaseK33CandidateHash"],expectedK33CandidateHash92],
TrueQ[frozenDecoderRaw92["FrozenBeforeS88"]],
TrueQ[frozenDecoderRaw92["S88DataReadBeforeFreeze"]===False],
AssociationQ[freezeCertificate92],
SameQ[freezeCertificateFileHashBefore92,expectedFreezeCertificateFileHash92],
TrueQ[freezeCertificate92["FreezeValidityPassed"]],
SameQ[freezeCertificate92["CandidateHash"],expectedDecoderCandidateHash92],
AssociationQ[s90Checkpoint92],
SameQ[s90CheckpointFileHashBefore92,expectedS90CheckpointFileHash92],
TrueQ[s90Checkpoint92["TestValidityPassed"]],TrueQ[s90Checkpoint92["BlindPerfect"]],
SameQ[s90Checkpoint92["Outcome"],"S90_BLIND_INTERVENTION_ALGEBRA_PASS"],
AssociationQ[s91Checkpoint92],
SameQ[s91CheckpointFileHashBefore92,expectedS91CheckpointFileHash92],
TrueQ[s91Checkpoint92["BenchmarkValidityPassed"]],
SameQ[s91Checkpoint92["FrozenCandidateHash"],expectedDecoderCandidateHash92],
SameQ[s91Checkpoint92["Outcome"],
"S91_VALID_POSTHOC_BASELINE_ABLATION_COMPLETE"],
!FileExistsQ[s92ResultCertificatePath]
];
preflight92=<|"Stage"->"S92","Name"->"CardinalityMatchedUniformActionBlind",
"CandidateFrozenBeforeProtocol"->True,
"DecoderCandidateHash"->decoderCandidateHashLoaded92,
"DecoderCandidateFileHash"->decoderCandidateFileHashBefore92,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore92,
"K33CandidateHash"->k33CandidateHashLoaded92,
"S90CheckpointLocked"->SameQ[s90CheckpointFileHashBefore92,
expectedS90CheckpointFileHash92],
"S91CheckpointLocked"->SameQ[s91CheckpointFileHashBefore92,
expectedS91CheckpointFileHash92],
"FeatureFamily"->If[AssociationQ[frozenDecoderRaw92],
frozenDecoderRaw92["FeatureFamily"],Missing[]],
"FeatureDimension"->If[AssociationQ[frozenDecoderRaw92],
frozenDecoderRaw92["FeatureDimension"],Missing[]],
"BranchCount"->10,"Depths"->{97,149},
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"S92ResultAlreadyPresent"->FileExistsQ[s92ResultCertificatePath],
"PreflightPassed"->preflightPassed92|>;
If[!TrueQ[preflightPassed92],Print[Dataset[{preflight92}]];
Print["S92 aborted: frozen inputs or checkpoint locks failed."];Abort[]];
Dataset[{preflight92}]
'''.strip()

definition = r'''
ClearAll[T92,Case92,ReferenceAction92,NodeRole92,EncodePair92,
LegacyPredictTokens92,PredictFrozenDecoder92,TripleSerialDiamondIn92,
HierarchicalTerminalDiamondIn92,TopologyTransform92,ExpectedContractions92,
PrepareWorld92,PrepareScenario92,S92TestDefinitionBundle];

T92[depth_Integer,target_String,answer_Integer,seed_Integer,
branchCount_Integer]:=Module[
{bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,main,perm,anc,i},
bb=1000000000 seed;K=bb+1;
c=Table[bb+100+i,{i,branchCount}];
v=Table[bb+200+i,{i,branchCount}];
q=Table[bb+300+i,{i,branchCount}];
e=Flatten[Table[{
DirectedEdge[K,c[[i]]],DirectedEdge[c[[i]],v[[i]]]},{i,branchCount}],1];
Do[
ib=bb+20000000 i;m=ib+1;safe=ib+2;u=ib+3;dummy=ib+4;
r1=ib+10;r2=ib+20;wrong=c[[1+Mod[i,branchCount]]];
main=Join[P59[q[[i]],r1,depth,ib+1000000],
P59[q[[i]],r2,depth,ib+2000000],
{DirectedEdge[r1,m],DirectedEdge[r2,m]},
P59[q[[i]],safe,depth+1,ib+3000000]];
perm=If[target==="Continue",
{DirectedEdge[m,c[[i]]],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],
A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];
{{Union[e],q,K,v,c,f},answer}
];
Case92[depth_Integer,answer_Integer,target_String]:=
T92[depth,target,answer,92000000+100 depth,10];

ReferenceAction92[c_List]:=Module[
{x=c[[1]],answer=c[[2]],branchCount,e,m,safe,u,dummy,correct,wrong,
continueEdges,stopEdges},
branchCount=Length[x[[6]]];e=x[[1]];m=x[[6,answer]];
safe=m+1;u=m+2;dummy=m+3;correct=x[[5,answer]];
wrong=x[[5,1+Mod[answer,branchCount]]];
continueEdges={DirectedEdge[m,correct],DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]};
stopEdges={DirectedEdge[m,wrong],DirectedEdge[safe,correct],
DirectedEdge[u,dummy]};
Which[And@@(MemberQ[e,#]&/@continueEdges),"Continue",
And@@(MemberQ[e,#]&/@stopEdges),"Stop",True,"Undefined"]
];

NodeRole92[originalNode_,case_List,answer_Integer]:=Module[
{x,branchCount,m,correct,wrong,dummy,querySources,queryBranch,role},
x=case[[1]];branchCount=Length[x[[6]]];m=x[[6,answer]];
correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,branchCount]]];dummy=m+3;
querySources={m,m+1,m+2};queryBranch=Union[querySources,{correct,wrong,dummy}];
role=Which[SameQ[originalNode,m],"QueriedDecision",
MemberQ[querySources,originalNode],"QueriedMediatorSource",
SameQ[originalNode,correct],"QueriedCorrectDestination",
SameQ[originalNode,wrong],"QueriedWrongDestination",
SameQ[originalNode,dummy],"QueriedDummyDestination",
MemberQ[x[[6]],originalNode],"OtherDecision",
MemberQ[x[[5]],originalNode],"OtherAnswerDestination",True,"OtherReject"];
<|"Role"->role,"QueryBranchRelated"->MemberQ[queryBranch,originalNode]|>
];

EncodePair92[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[{<|"Grammar"->"S92BlindObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate86E["EncoderParams"],frozenCandidate86E["K"]];
First[encoded["Codes"]]];
LegacyPredictTokens92[tokens_List]:=If[AnyTrue[tokens,
MemberQ[frozenCandidate86E["Policy"],#]&],"Continue","Stop"];
PredictFrozenDecoder92[observations_List]:=Module[{prediction},
prediction=TCCTPredictWorldS87D[<|"Observations"->observations|>,
frozenDecoderLoaded92];
If[MemberQ[{"Continue","Stop"},prediction],prediction,$Failed]];

TripleSerialDiamondIn92[c_List]:=DiamondIn72[DoubleDiamondIn79[c]];
HierarchicalTerminalDiamondIn92[c_List]:=
DiamondIn72[HierarchicalDiamondIn80[c]];
TopologyTransform92[topology_String,c_List]:=Switch[topology,
"TripleSerialDiamondIn",TripleSerialDiamondIn92[c],
"HierarchicalTerminalDiamondIn",HierarchicalTerminalDiamondIn92[c],_,$Failed];
ExpectedContractions92[topology_String,baseCase_List]:=Switch[topology,
"TripleSerialDiamondIn",3 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalTerminalDiamondIn",4 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]];

PrepareWorld92[topology_String,depth_Integer,target_String,
answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,observations,
originalNode,pair,roleInfo,rawTokens,tokens,featureVector,
legacyPrediction,prediction},
baseCase=Case92[depth,answer,target];
topologyCase=TopologyTransform92[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions92[topology,baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole92[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair92[pair]|>],packedNodes];
rawTokens=({#1["Role"],#1["Code"]}&)/@observations;
tokens=DeleteDuplicates[rawTokens];
featureVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
legacyPrediction=LegacyPredictTokens92[tokens];
prediction=PredictFrozenDecoder92[observations];
<|"Topology"->topology,"Depth"->depth,"GraphCondition"->
"Uniform"<>target,"Answer"->answer,"Target"->target,
"ReferenceAction"->ReferenceAction92[canonicalCase],"BranchCount"->10,
"Prediction"->prediction,"LegacyPrediction"->legacyPrediction,
"FeatureVector"->featureVector,"Cardinality"->featureVector[[{1,2,18}]],
"Correct"->SameQ[prediction,target],
"TopologyGraphHash"->Hash[topologyCase[[1,1]],"SHA256","HexString"],
"CanonicalGraphHash"->Hash[canonicalCase[[1,1]],"SHA256","HexString"],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
expectedContractions],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"StateObservationCount"->Length[observations],
"RawTokenCount"->Length[rawTokens],"TokenCount"->Length[tokens],
"DuplicateTokensRemoved"->Length[rawTokens]-Length[tokens],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds|>
];

PrepareScenario92[topology_String,depth_Integer]:=Module[
{continueWorlds,stopWorlds,worldPairs,continueHashes,stopHashes},
continueWorlds=Table[PrepareWorld92[topology,depth,"Continue",answer],
{answer,Range[10]}];
stopWorlds=Table[PrepareWorld92[topology,depth,"Stop",answer],
{answer,Range[10]}];
worldPairs=MapThread[Function[{continue,stop},<|
"Answer"->continue["Answer"],
"SameAnswer"->SameQ[continue["Answer"],stop["Answer"]],
"CardinalityExactlyMatched"->SameQ[continue["Cardinality"],
stop["Cardinality"],{1,1,0}],
"FullFeatureVectorsDifferent"->UnsameQ[continue["FeatureVector"],
stop["FeatureVector"]],
"ReferenceRelationCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"PredictionRelationCorrect"->And[
SameQ[continue["Prediction"],"Continue"],
SameQ[stop["Prediction"],"Stop"]],
"PairCorrect"->And[TrueQ[continue["Correct"]],TrueQ[stop["Correct"]]]|>],
{continueWorlds,stopWorlds}];
continueHashes=Lookup[continueWorlds,"TopologyGraphHash"];
stopHashes=Lookup[stopWorlds,"TopologyGraphHash"];
<|"Topology"->topology,"Depth"->depth,
"ContinueSameGraphAcrossQueries"->SameQ@@continueHashes,
"StopSameGraphAcrossQueries"->SameQ@@stopHashes,
"OppositeActionsUseDifferentGraphs"->UnsameQ[First[continueHashes],
First[stopHashes]],
"AllCardinalitiesExactlyMatched"->And@@Lookup[worldPairs,
"CardinalityExactlyMatched"],
"AllFullFeatureVectorsDifferent"->And@@Lookup[worldPairs,
"FullFeatureVectorsDifferent"],
"ReferenceRelationsCorrect"->And@@Lookup[worldPairs,
"ReferenceRelationCorrect"],
"PredictionRelationsCorrect"->And@@Lookup[worldPairs,
"PredictionRelationCorrect"],
"AllTwentyWorldsCorrect"->And@@Join[Lookup[continueWorlds,"Correct"],
Lookup[stopWorlds,"Correct"]],"WorldPairs"->worldPairs,
"ContinueWorlds"->continueWorlds,"StopWorlds"->stopWorlds|>
];

S92TestDefinitionBundle[]:={DownValues[T92],DownValues[Case92],
DownValues[ReferenceAction92],DownValues[NodeRole92],DownValues[EncodePair92],
DownValues[LegacyPredictTokens92],DownValues[PredictFrozenDecoder92],
DownValues[TripleSerialDiamondIn92],DownValues[HierarchicalTerminalDiamondIn92],
DownValues[TopologyTransform92],DownValues[ExpectedContractions92],
DownValues[PrepareWorld92],DownValues[PrepareScenario92]};

blindBranchCount92=10;blindDepths92={97,149};
blindTopologies92={"TripleSerialDiamondIn","HierarchicalTerminalDiamondIn"};
topologySpec92=<|"TripleSerialDiamondIn"->
"DiamondIn72AfterDoubleDiamondIn79","HierarchicalTerminalDiamondIn"->
"DiamondIn72AfterHierarchicalDiamondIn80"|>;
topologySpecHash92=Hash[Normal[topologySpec92],"SHA256","HexString"];
testDefinitionHashBefore92=Hash[S92TestDefinitionBundle[],"SHA256","HexString"];
noCasesBeforeProtocolHash92=And[!ValueQ[blindScenarios92],
!ValueQ[blindWorlds92]];
protocol92=<|"Stage"->"S92","Name"->
"CardinalityMatchedUniformActionBlind",
"Candidate"->"S87D-FrozenWorldMultisetDecoder",
"CandidateHash"->decoderCandidateHashLoaded92,
"CandidateFileHash"->decoderCandidateFileHashBefore92,
"FeatureRuntimeFileHash"->decoderRuntimeFileHashBefore92,
"K33CandidateHash"->k33CandidateHashLoaded92,
"S90CheckpointFileHash"->s90CheckpointFileHashBefore92,
"S91CheckpointFileHash"->s91CheckpointFileHashBefore92,
"BranchCount"->blindBranchCount92,"Depths"->blindDepths92,
"Topologies"->blindTopologies92,"TopologySpecHash"->topologySpecHash92,
"ExpectedScenarios"->4,"ExpectedPairs"->40,"ExpectedWorlds"->80,
"ExpectedContinueWorlds"->40,"ExpectedStopWorlds"->40,
"ExternalGrammar"->"IndependentTenBranchT92",
"ActionRegime"->"UniformAllBranchesContinueVersusUniformAllBranchesStop",
"CardinalityConstraint"->
"EveryPairedWorldHasObservationDistinctPairCounts_1_1_0",
"Pairing"->"SameTopologyDepthAnswerOppositeAction",
"FeatureFamily"->"QueriedGlobalMoments","FeatureDimension"->27,
"SuccessCriterion"->
"ValidHarnessExactCardinalityMatchAndAll80WorldsCorrect",
"CandidateFrozenBeforeProtocol"->True,
"S90CheckpointReadOnlyLock"->True,"S91CheckpointReadOnlyLock"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash92|>;
protocolHash92=Hash[Normal[protocol92],"SHA256","HexString"];
Dataset[{Join[protocol92,<|"ProtocolHash"->protocolHash92,
"TestDefinitionHash"->testDefinitionHashBefore92|>]}]
'''.strip()

run = r'''
blindScenarios92=Flatten[Table[PrepareScenario92[topology,depth],
{topology,blindTopologies92},{depth,blindDepths92}],1];
continueWorlds92=Flatten[Lookup[blindScenarios92,"ContinueWorlds"],1];
stopWorlds92=Flatten[Lookup[blindScenarios92,"StopWorlds"],1];
blindWorlds92=Join[continueWorlds92,stopWorlds92];
blindPairs92=Flatten[Lookup[blindScenarios92,"WorldPairs"],1];

summary92=<|"Scenarios"->Length[blindScenarios92],
"Pairs"->Length[blindPairs92],"Worlds"->Length[blindWorlds92],
"ContinueWorlds"->Length[continueWorlds92],"StopWorlds"->Length[stopWorlds92],
"ContinueCorrect"->Count[continueWorlds92,w_/;TrueQ[w["Correct"]]],
"StopCorrect"->Count[stopWorlds92,w_/;TrueQ[w["Correct"]]],
"WorldCorrect"->Count[blindWorlds92,w_/;TrueQ[w["Correct"]]],
"PairCorrect"->Count[blindPairs92,p_/;TrueQ[p["PairCorrect"]]],
"CardinalityPairsMatched"->Count[blindPairs92,p_/;
TrueQ[p["CardinalityExactlyMatched"]]],
"FullFeatureVectorPairsDifferent"->Count[blindPairs92,p_/;
TrueQ[p["FullFeatureVectorsDifferent"]]],
"ReferenceRelationsCorrect"->Count[blindPairs92,p_/;
TrueQ[p["ReferenceRelationCorrect"]]],
"PredictionRelationsCorrect"->Count[blindPairs92,p_/;
TrueQ[p["PredictionRelationCorrect"]]],
"ReferenceActionsCorrect"->Count[blindWorlds92,w_/;
SameQ[w["ReferenceAction"],w["Target"]]],
"CardinalityOneOneZero"->Count[blindWorlds92,w_/;
SameQ[w["Cardinality"],{1,1,0}]],
"CanonicalCaseExactlyBase"->Count[blindWorlds92,w_/;
TrueQ[w["CanonicalCaseExactlyBase"]]],
"ContractionCountCorrect"->Count[blindWorlds92,w_/;
TrueQ[w["ContractionCountCorrect"]]],
"ProtectedNodesPreserved"->Count[blindWorlds92,w_/;
TrueQ[w["ProtectedNodesPreserved"]]],
"ValidFeatureVectors"->Count[blindWorlds92,w_/;
VectorQ[w["FeatureVector"],IntegerQ]&&Length[w["FeatureVector"]]===27],
"PredictionFailures"->Count[blindWorlds92,w_/;SameQ[w["Prediction"],$Failed]],
"TerminatedNaturally"->Count[blindWorlds92,w_/;
TrueQ[w["TerminatedNaturally"]]],
"HitSafetyCap"->Count[blindWorlds92,w_/;TrueQ[w["HitSafetyCap"]]],
"TenBranchWorlds"->Count[blindWorlds92,w_/;SameQ[w["BranchCount"],10]],
"ScenarioCardinalityMatched"->Count[blindScenarios92,s_/;
TrueQ[s["AllCardinalitiesExactlyMatched"]]],
"ScenarioFullVectorsDifferent"->Count[blindScenarios92,s_/;
TrueQ[s["AllFullFeatureVectorsDifferent"]]],
"ScenarioReferenceRelationsCorrect"->Count[blindScenarios92,s_/;
TrueQ[s["ReferenceRelationsCorrect"]]],
"ScenarioPerfect"->Count[blindScenarios92,s_/;TrueQ[s["AllTwentyWorldsCorrect"]]],
"TotalTraceSeconds"->Total@Lookup[blindWorlds92,"TraceSeconds"]|>;

byTopology92=Map[Function[topology,Module[{worlds},
worlds=Select[blindWorlds92,SameQ[#1["Topology"],topology]&];
<|"Topology"->topology,"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"ContinueCorrect"->Count[worlds,w_/;
SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]],
"StopCorrect"->Count[worlds,w_/;
SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]]|>]],blindTopologies92];
byDepth92=Map[Function[depth,Module[{worlds},
worlds=Select[blindWorlds92,SameQ[#1["Depth"],depth]&];
<|"Depth"->depth,"Worlds"->Length[worlds],
"Correct"->Count[worlds,w_/;TrueQ[w["Correct"]]],
"ContinueCorrect"->Count[worlds,w_/;
SameQ[w["Target"],"Continue"]&&TrueQ[w["Correct"]]],
"StopCorrect"->Count[worlds,w_/;
SameQ[w["Target"],"Stop"]&&TrueQ[w["Correct"]]]|>]],blindDepths92];
Column[{Dataset[{summary92}],Dataset[byTopology92],Dataset[byDepth92]}]
'''.strip()

audit = r'''
modelHashAfter92=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter92=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
decoderRawAfter92=KeyDrop[frozenDecoderLoaded92,{"Classifier"}];
decoderObjectHashAfter92=Hash[Normal[decoderRawAfter92],"SHA256","HexString"];
coreHashAfter92=Hash[CoreDefinitionBundle92[],"SHA256","HexString"];
canonicalizerHashAfter92=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter92=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter92=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
decoderRuntimeDefinitionHashAfter92=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
testDefinitionHashAfter92=Hash[S92TestDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter92=Hash[Normal[protocol92],"SHA256","HexString"];
k33CandidateFileHashAfter92=FileSHA256Hex92[k33CandidatePath92];
decoderRuntimeFileHashAfter92=FileSHA256Hex92[decoderRuntimePath92];
decoderCandidateFileHashAfter92=FileSHA256Hex92[decoderCandidatePath92];
freezeCertificateFileHashAfter92=FileSHA256Hex92[freezeCertificatePath92];
s90CheckpointFileHashAfter92=FileSHA256Hex92[s90CheckpointPath92];
s91CheckpointFileHashAfter92=FileSHA256Hex92[s91CheckpointPath92];

integrityPassed92=And[
SameQ[modelHashBefore92,modelHashAfter92],
SameQ[k33ObjectHashBefore92,k33ObjectHashAfter92],
SameQ[decoderObjectHashBefore92,decoderObjectHashAfter92],
SameQ[coreHashBefore92,coreHashAfter92],
SameQ[canonicalizerHashBefore92,canonicalizerHashAfter92],
SameQ[interventionHashBefore92,interventionHashAfter92],
SameQ[topologyPrimitiveHashBefore92,topologyPrimitiveHashAfter92],
SameQ[decoderRuntimeDefinitionHashBefore92,decoderRuntimeDefinitionHashAfter92],
SameQ[testDefinitionHashBefore92,testDefinitionHashAfter92],
SameQ[protocolHash92,protocolHashAfter92],
SameQ[k33CandidateFileHashBefore92,k33CandidateFileHashAfter92],
SameQ[decoderRuntimeFileHashBefore92,decoderRuntimeFileHashAfter92],
SameQ[decoderCandidateFileHashBefore92,decoderCandidateFileHashAfter92],
SameQ[freezeCertificateFileHashBefore92,freezeCertificateFileHashAfter92],
SameQ[s90CheckpointFileHashBefore92,s90CheckpointFileHashAfter92],
SameQ[s91CheckpointFileHashBefore92,s91CheckpointFileHashAfter92]];

cardinalityValidityPassed92=And[
SameQ[summary92["CardinalityPairsMatched"],40],
SameQ[summary92["CardinalityOneOneZero"],80],
SameQ[summary92["FullFeatureVectorPairsDifferent"],40],
SameQ[Counts[Lookup[continueWorlds92,"Cardinality"]],
Counts[Lookup[stopWorlds92,"Cardinality"]],<|{1,1,0}->40|>]];
testValidityPassed92=And[TrueQ[integrityPassed92],
TrueQ[cardinalityValidityPassed92],SameQ[summary92["Scenarios"],4],
SameQ[summary92["Pairs"],40],SameQ[summary92["Worlds"],80],
SameQ[summary92["ContinueWorlds"],40],SameQ[summary92["StopWorlds"],40],
SameQ[summary92["ReferenceRelationsCorrect"],40],
SameQ[summary92["ReferenceActionsCorrect"],80],
SameQ[summary92["CanonicalCaseExactlyBase"],80],
SameQ[summary92["ContractionCountCorrect"],80],
SameQ[summary92["ProtectedNodesPreserved"],80],
SameQ[summary92["ValidFeatureVectors"],80],
SameQ[summary92["PredictionFailures"],0],
SameQ[summary92["TerminatedNaturally"],80],
SameQ[summary92["HitSafetyCap"],0],
SameQ[summary92["TenBranchWorlds"],80],
SameQ[summary92["ScenarioCardinalityMatched"],4],
SameQ[summary92["ScenarioFullVectorsDifferent"],4],
SameQ[summary92["ScenarioReferenceRelationsCorrect"],4]];
blindPerfect92=And[TrueQ[testValidityPassed92],
SameQ[summary92["ContinueCorrect"],40],
SameQ[summary92["StopCorrect"],40],SameQ[summary92["WorldCorrect"],80],
SameQ[summary92["PairCorrect"],40],SameQ[summary92["ScenarioPerfect"],4]];
accuracy92=N[summary92["WorldCorrect"]/80];
balancedAccuracy92=N@Mean[{summary92["ContinueCorrect"]/40,
summary92["StopCorrect"]/40}];
resultPayload92=<|"Stage"->"S92","Name"->
"CardinalityMatchedUniformActionBlind",
"CandidateHash"->decoderCandidateHashLoaded92,
"CandidateFileHash"->decoderCandidateFileHashAfter92,
"S90CheckpointFileHash"->s90CheckpointFileHashAfter92,
"S91CheckpointFileHash"->s91CheckpointFileHashAfter92,
"ProtocolHash"->protocolHashAfter92,
"TestDefinitionHash"->testDefinitionHashAfter92,
"BranchCount"->10,"Depths"->blindDepths92,
"Topologies"->blindTopologies92,"Scenarios"->summary92["Scenarios"],
"Pairs"->summary92["Pairs"],"Worlds"->summary92["Worlds"],
"ContinueCorrect"->summary92["ContinueCorrect"],
"StopCorrect"->summary92["StopCorrect"],
"WorldCorrect"->summary92["WorldCorrect"],"Accuracy"->accuracy92,
"BalancedAccuracy"->balancedAccuracy92,
"PairCorrect"->summary92["PairCorrect"],
"CardinalityPairsMatched"->summary92["CardinalityPairsMatched"],
"CardinalityOneOneZero"->summary92["CardinalityOneOneZero"],
"FullFeatureVectorPairsDifferent"->summary92["FullFeatureVectorPairsDifferent"],
"CardinalityValidityPassed"->cardinalityValidityPassed92,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore92,modelHashAfter92],
"OriginalK33CandidateChanged"->!SameQ[k33ObjectHashBefore92,k33ObjectHashAfter92],
"FrozenDecoderChanged"->!SameQ[decoderObjectHashBefore92,decoderObjectHashAfter92],
"CoreChanged"->!SameQ[coreHashBefore92,coreHashAfter92],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore92,canonicalizerHashAfter92],
"InterventionCoreChanged"->!SameQ[interventionHashBefore92,interventionHashAfter92],
"TopologyPrimitivesChanged"->!SameQ[topologyPrimitiveHashBefore92,
topologyPrimitiveHashAfter92],
"FeatureRuntimeChanged"->!SameQ[decoderRuntimeDefinitionHashBefore92,
decoderRuntimeDefinitionHashAfter92],
"TestDefinitionChangedDuringRun"->!SameQ[testDefinitionHashBefore92,
testDefinitionHashAfter92],
"ProtocolChangedDuringRun"->!SameQ[protocolHash92,protocolHashAfter92],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore92,coreHashAfter92],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore92,coreHashAfter92],
"S90CheckpointChanged"->!SameQ[s90CheckpointFileHashBefore92,
s90CheckpointFileHashAfter92],
"S91CheckpointChanged"->!SameQ[s91CheckpointFileHashBefore92,
s91CheckpointFileHashAfter92],
"TestValidityPassed"->testValidityPassed92,"BlindPerfect"->blindPerfect92|>;
blindResultHash92=Hash[Normal[resultPayload92],"SHA256","HexString"];
cert92=Join[resultPayload92,<|
"CandidateFrozenBeforeS92"->True,"BlindProtocolHashedBeforeCases"->True,
"S87DDecoderUsed"->True,"S91CheckpointLocked"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"S92IsBlindCardinalityMatchedRelationalTest"->True,
"MayClaimCardinalityShortcutExcluded"->And[TrueQ[testValidityPassed92],
TrueQ[cardinalityValidityPassed92]],
"MayClaimBlindRelationalTransferBeyondCardinality"->blindPerfect92,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary92["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash92,
"Outcome"->Which[!TrueQ[testValidityPassed92],"INVALID_S92_BLIND_TEST",
TrueQ[blindPerfect92],"S92_BLIND_CARDINALITY_MATCHED_PASS",
True,"S92_VALID_BLIND_FAILURE_DO_NOT_RETUNE"],
"SuggestedNextStage"->Which[!TrueQ[testValidityPassed92],
"S92R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",TrueQ[blindPerfect92],
"S93_INDEPENDENT_GRAMMAR_REPLICATION",True,
"S92A_FAILURE_AUDIT_THEN_RETRAINED_RELATIONAL_DECODER"]|>];
certificateExportResult92=Quiet@Check[
Export[s92ResultCertificatePath,cert92,"RawJSON"],$Failed];
certificateExported92=And[StringQ[certificateExportResult92],
FileExistsQ[s92ResultCertificatePath]];
Column[{Dataset[{cert92}],Dataset[{<|
"CertificateExported"->certificateExported92,
"CertificatePath"->s92ResultCertificatePath,
"CertificateFileHash"->If[certificateExported92,
FileSHA256Hex92[s92ResultCertificatePath],Missing[]]|>}]}]
'''.strip()

cells = [architecture, preflight, definition, run, audit]
WL.write_text("\n\n".join(
    f"(* S92 CELL {index} *)\n{cell}" for index, cell in enumerate(cells, 1)
) + "\n", encoding="utf-8")


def code_cell(source: str, stage: str) -> dict:
    return {"cell_type": "code", "execution_count": None,
            "metadata": {"tcct_stage": stage}, "outputs": [],
            "source": source.splitlines(keepends=True)}


markdown = {"cell_type": "markdown", "metadata": {}, "source": [
    "# TCCT S92 - Blind Cardinality-Matched Relational Test\n", "\n",
    "The S87D decoder and every TCCT mechanism remain frozen. Continue and Stop "
    "worlds are balanced and paired by topology, depth, and query position. Each "
    "valid pair must have exactly the same cardinality vector `{1,1,0}` while its "
    "full 27-dimensional feature vectors remain different.\n", "\n",
    "This is a one-shot blind test with a new ten-branch grammar and depths 97/149. "
    "The protocol is hashed before world generation. Do not retune after either "
    "success or failure. Expected workload: 80 worlds.\n", "\n",
    "Run **Kernel -> Restart Kernel and Run All Cells** once.\n"]}
notebook = {"cells": [markdown,
    code_cell(architecture, "S92-ARCHITECTURE"),
    code_cell(preflight, "S92-PREFLIGHT"),
    code_cell(definition, "S92-PROTOCOL"),
    code_cell(run, "S92-BLIND-RUN"),
    code_cell(audit, "S92-AUDIT")],
    "metadata": {"kernelspec": {"display_name": "Wolfram Language 15",
    "language": "Wolfram Language", "name": "wolframlanguage15"},
    "language_info": {"codemirror_mode": "mathematica", "file_extension": ".wl",
    "mimetype": "application/vnd.wolfram.mathematica", "name": "Wolfram Language",
    "pygments_lexer": "mathematica", "version": "15.0"}},
    "nbformat": 4, "nbformat_minor": 5}
NB.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
preflight_notebook = dict(notebook)
preflight_notebook["cells"] = [markdown,
    code_cell(architecture, "S92-ARCHITECTURE"),
    code_cell(preflight, "S92-PREFLIGHT"),
    code_cell(definition, "S92-PROTOCOL")]
PREFLIGHT_NB.write_text(json.dumps(preflight_notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(
    f"(* S92 CELL {index} *)\n{cell}" for index, cell in enumerate(cells[:3], 1)
) + "\n", encoding="utf-8")

LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S92_CardinalityMatchedUniformActionBlind.ipynb"
set "TCCT_S91_RESULT=E:\engine_wolf\TCCT_S91_BenchmarkCertificate.json"
set "TCCT_S92_RESULT=E:\engine_wolf\TCCT_S92_BlindResultCertificate.json"
set "TCCT_DECODER=E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s92"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s92"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S92 notebook not found & pause & exit /b 1)
if not exist "%TCCT_S91_RESULT%" (echo Locked S91 certificate not found & pause & exit /b 1)
if not exist "%TCCT_DECODER%" (echo Frozen decoder not found & pause & exit /b 1)
if exist "%TCCT_S92_RESULT%" (
  echo A prior S92 result certificate already exists.
  echo Preserve it and do not rerun or overwrite the blind test.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S92 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8905 --ServerApp.port_retries=5
exit /b 0
''', encoding="utf-8")

precommit = {"Stage": "S92", "Name": "CardinalityMatchedUniformActionBlind",
    "BlindCasesGeneratedAtBuild": False,
    "BlindResultCertificatePresentAtBuild": Path(r"E:\engine_wolf\TCCT_S92_BlindResultCertificate.json").exists(),
    "CandidateFrozenBeforeProtocol": True, "BranchCount": 10,
    "Depths": [97, 149],
    "Topologies": ["TripleSerialDiamondIn", "HierarchicalTerminalDiamondIn"],
    "ExpectedScenarios": 4, "ExpectedPairs": 40, "ExpectedWorlds": 80,
    "ExpectedContinueWorlds": 40, "ExpectedStopWorlds": 40,
    "RequiredCardinality": [1, 1, 0],
    "ProtocolHash": "4e7117970c3e5c4315fb4953364b632404566258a718c7807c8819ba3d30b6bb",
    "TestDefinitionHash": "3f072d5e37942fd007dd5b6fa73319d47da23e41b61ca05486fccc040f2b4904",
    "S91CheckpointSHA256": "cf335bda73b8a26eacbf32d8d25dcad737a84d503a6f0849dbcd3afc3f1df8cd",
    "DynamicPreflightPassed": True,
    "BlindCasesGeneratedAtPreflight": False,
    "S92ResultCertificatePresentAtPreflight": False,
    "TrainingRun": False, "CandidateSearchRun": False,
    "DecoderEditApplied": False, "RetuningApplied": False,
    "WolframSourceSHA256": sha256(WL), "NotebookSHA256": sha256(NB)}
PRECOMMIT.write_text(json.dumps(precommit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path)
