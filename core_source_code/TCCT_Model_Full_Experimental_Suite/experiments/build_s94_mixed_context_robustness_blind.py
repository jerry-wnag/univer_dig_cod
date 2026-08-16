"""Build TCCT S94 mixed-context paired-counterfactual robustness blind test."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE93 = ROOT / "TCCT_S93_PairedCounterfactualBlind.wl"
WL = ROOT / "TCCT_S94_MixedContextRobustnessBlind.wl"
NB = ROOT / "TCCT_S94_MixedContextRobustnessBlind.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94_MixedContextRobustnessBlind_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94_MixedContextRobustnessBlind_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94_Precommit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


source93 = SOURCE93.read_text(encoding="utf-8")
core = source93.split("(* S93 CELL 2 *)", 1)[0]
core = core.replace("(* S93 CELL 1 *)", "", 1).strip()

locks = r'''
expectedFrozenModelHash94=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash94=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedK33CandidateFileHash94=
"4a252b8977101d024b1b2feb00b4626ca28290c3982cdad199bc78ef7e0c98f1";
expectedBaseCandidateHash94=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedBaseCandidateFileHash94=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedBaseRuntimeFileHash94=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedPairCandidateHash94=
"540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c";
expectedPairCandidateFileHash94=
"aecbe544a4af3a8ad0ba0494bb11312dd4a4b71f1a1c7ae42489a5300c7078ff";
expectedPairRuntimeFileHash94=
"74a926b8efccaddbd1dd07373ac35a93bc53e9fb08cc456ce1adb6a006d333c6";
expectedS92BCertificateFileHash94=
"85247775ef008a5ddf2378c54585d645dbf6b910d2b6085c1f8c29a98a9c2eb4";
expectedS92BCertificateResultHash94=
"0e3301be5d06af42d7e44ddb0e2b02e377fc378fcfefe98d928db875fc6c7373";
expectedS93CertificateFileHash94=
"d0c863119cf03e93e27e0db175163cd91ca4c980197a5fd1f6688f3ddc94c072";
expectedS93BlindResultHash94=
"335664ce1be5c14d2b8c7791960c6327f8a0a97067aca25857423be4e0b64d64";

k33CandidatePath94="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
baseRuntimePath94="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
baseCandidatePath94="E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
pairRuntimePath94="E:/engine_wolf/TCCT_S92B_PairedContrastDecoderRuntime.wl";
pairCandidatePath94="E:/engine_wolf/TCCT_S92B_FrozenPairedContrastDecoder.wxf";
s92bCertificatePath94="E:/engine_wolf/TCCT_S92B_PairedContrastDecoderCertificate.json";
s93CertificatePath94="E:/engine_wolf/TCCT_S93_PairedCounterfactualBlindCertificate.json";
s94ResultCertificatePath="E:/engine_wolf/TCCT_S94_MixedContextRobustnessBlindCertificate.json";

ClearAll[FileSHA256Hex94];
FileSHA256Hex94[path_String]:=If[FileExistsQ[path],
IntegerString[FileHash[path,"SHA256"],16,64],Missing["FileMissing",path]];
requiredFiles94={k33CandidatePath94,baseRuntimePath94,baseCandidatePath94,
pairRuntimePath94,pairCandidatePath94,s92bCertificatePath94,s93CertificatePath94};
If[!And@@(FileExistsQ/@requiredFiles94),
Print["S94 aborted: one or more locked inputs are missing."];
Dataset[AssociationThread[requiredFiles94,FileExistsQ/@requiredFiles94]];Abort[]];
If[FileExistsQ[s94ResultCertificatePath],
Print["S94 aborted: a prior blind certificate exists. Preserve it."];Abort[]];

fileHashesBefore94=FileSHA256Hex94/@requiredFiles94;
Clear[frozenCandidate86E];Get[k33CandidatePath94];
k33HashLoaded94=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
Get[baseRuntimePath94];
baseDecoderLoaded94=Quiet@Check[TCCTLoadFrozenDecoderS87D[baseCandidatePath94],$Failed];
baseDecoderRaw94=If[AssociationQ[baseDecoderLoaded94],
KeyDrop[baseDecoderLoaded94,{"Classifier"}],$Failed];
Get[pairRuntimePath94];
pairDecoderLoaded94=Quiet@Check[
TCCTLoadFrozenPairDecoderS92B[pairCandidatePath94],$Failed];
pairDecoderRaw94=If[AssociationQ[pairDecoderLoaded94],
KeyDrop[pairDecoderLoaded94,{"Policy"}],$Failed];
s92bCertificate94=Quiet@Check[Import[s92bCertificatePath94,"RawJSON"],$Failed];
s93Certificate94=Quiet@Check[Import[s93CertificatePath94,"RawJSON"],$Failed];

ClearAll[CoreDefinitionBundle94,PairRuntimeDefinitionBundle94];
CoreDefinitionBundle94[]:=CoreDefinitionBundle86[];
PairRuntimeDefinitionBundle94[]:={DownValues[TCCTPairContrastVectorS92B],
DownValues[TCCTLoadFrozenPairDecoderS92B],
DownValues[TCCTPredictOrderedPairVectorsS92B],
DownValues[TCCTPredictOrderedPairWorldsS92B]};
modelHashBefore94=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashBefore94=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashBefore94=Hash[Normal[baseDecoderRaw94],"SHA256","HexString"];
pairDecoderObjectHashBefore94=Hash[Normal[pairDecoderRaw94],"SHA256","HexString"];
coreHashBefore94=Hash[CoreDefinitionBundle94[],"SHA256","HexString"];
canonicalizerHashBefore94=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashBefore94=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashBefore94=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashBefore94=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashBefore94=Hash[
PairRuntimeDefinitionBundle94[],"SHA256","HexString"];

preflightPassed94=And[TrueQ[preflightPassed86],
SameQ[modelHashBefore94,expectedFrozenModelHash94],
AssociationQ[frozenCandidate86E],SameQ[k33HashLoaded94,expectedK33CandidateHash94],
SameQ[fileHashesBefore94[[1]],expectedK33CandidateFileHash94],
AssociationQ[baseDecoderLoaded94],
SameQ[baseDecoderLoaded94["CandidateHash"],expectedBaseCandidateHash94],
SameQ[fileHashesBefore94[[2]],expectedBaseRuntimeFileHash94],
SameQ[fileHashesBefore94[[3]],expectedBaseCandidateFileHash94],
AssociationQ[pairDecoderLoaded94],
SameQ[pairDecoderLoaded94["CandidateHash"],expectedPairCandidateHash94],
SameQ[fileHashesBefore94[[4]],expectedPairRuntimeFileHash94],
SameQ[fileHashesBefore94[[5]],expectedPairCandidateFileHash94],
SameQ[pairDecoderRaw94["ContrastPosition"],3],
SameQ[pairDecoderRaw94["Modulus"],33],
SameQ[pairDecoderRaw94["PolicyRules"],{
<|"Delta"->6,"Prediction"->"FirstStop"|>,
<|"Delta"->27,"Prediction"->"FirstContinue"|>}],
TrueQ[pairDecoderRaw94["FrozenBeforeS93"]],
AssociationQ[s92bCertificate94],
SameQ[fileHashesBefore94[[6]],expectedS92BCertificateFileHash94],
SameQ[s92bCertificate94["CertificateResultHash"],
expectedS92BCertificateResultHash94],
TrueQ[s92bCertificate94["FreezeValidityPassed"]],
AssociationQ[s93Certificate94],
SameQ[fileHashesBefore94[[7]],expectedS93CertificateFileHash94],
SameQ[s93Certificate94["BlindResultHash"],expectedS93BlindResultHash94],
SameQ[s93Certificate94["Outcome"],
"S93_BLIND_PAIRED_COUNTERFACTUAL_TRANSFER_PASS"],
TrueQ[s93Certificate94["TestValidityPassed"]],
TrueQ[s93Certificate94["BlindPerfect"]],
!FileExistsQ[s94ResultCertificatePath]];
preflight94=<|"Stage"->"S94","Name"->"MixedContextRobustnessBlind",
"PreflightPassed"->preflightPassed94,
"PairCandidateFrozen"->True,
"PairCandidateHash"->If[AssociationQ[pairDecoderLoaded94],
pairDecoderLoaded94["CandidateHash"],Missing[]],
"S93CheckpointLocked"->SameQ[fileHashesBefore94[[7]],
expectedS93CertificateFileHash94],
"BranchCount"->13,"Depths"->{131,193},
"TrainingRun"->False,"CandidateSearchRun"->False,
"RetuningApplied"->False,"S94ResultAlreadyPresent"->
FileExistsQ[s94ResultCertificatePath]|>;
If[!TrueQ[preflightPassed94],Print[Dataset[{preflight94}]];
Print["S94 aborted: frozen inputs or checkpoint locks failed."];Abort[]];
Dataset[{preflight94}]
'''.strip()

protocol = r'''
ClearAll[T94,Case94,ReferenceAction94,NodeRole94,EncodePair94,
DiamondAfterDoubleAfterHierarchical94,
HierarchicalAfterDiamondAfterDouble94,TopologyTransform94,
NoisePhase94,ExpectedContractions94,PrepareWorld94,PrepareScenario94,
S94TestDefinitionBundle];

T94[depth_Integer,target_String,answer_Integer,seed_Integer,
branchCount_Integer,noisePhase_Integer]:=Module[
{bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,main,perm,anc,
branchAction,i},
bb=1000000000 seed;K=bb+1;
c=Table[bb+100+i,{i,branchCount}];v=Table[bb+200+i,{i,branchCount}];
q=Table[bb+300+i,{i,branchCount}];
e=Flatten[Table[{DirectedEdge[K,c[[i]]],DirectedEdge[c[[i]],v[[i]]]},
{i,branchCount}],1];
Do[ib=bb+20000000 i;m=ib+1;safe=ib+2;u=ib+3;dummy=ib+4;
r1=ib+10;r2=ib+20;wrong=c[[1+Mod[i,branchCount]]];
main=Join[P59[q[[i]],r1,depth,ib+1000000],
P59[q[[i]],r2,depth,ib+2000000],{DirectedEdge[r1,m],DirectedEdge[r2,m]},
P59[q[[i]],safe,depth+1,ib+3000000]];
branchAction=If[i===answer,target,
If[EvenQ[i+noisePhase],"Continue","Stop"]];
perm=If[branchAction==="Continue",
{DirectedEdge[m,c[[i]]],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],
A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];
{{Union[e],q,K,v,c,f},answer}
];
Case94[depth_Integer,answer_Integer,target_String,noisePhase_Integer]:=
T94[depth,target,answer,94000000+100 depth+noisePhase,13,noisePhase];

ReferenceAction94[c_List]:=Module[{x=c[[1]],answer=c[[2]],branchCount,e,m,
safe,u,dummy,correct,wrong,continueEdges,stopEdges},
branchCount=Length[x[[6]]];e=x[[1]];m=x[[6,answer]];safe=m+1;u=m+2;
dummy=m+3;correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,branchCount]]];
continueEdges={DirectedEdge[m,correct],DirectedEdge[safe,dummy],
DirectedEdge[u,wrong]};stopEdges={DirectedEdge[m,wrong],
DirectedEdge[safe,correct],DirectedEdge[u,dummy]};
Which[And@@(MemberQ[e,#]&/@continueEdges),"Continue",
And@@(MemberQ[e,#]&/@stopEdges),"Stop",True,"Undefined"]];

NodeRole94[originalNode_,case_List,answer_Integer]:=Module[
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
<|"Role"->role,"QueryBranchRelated"->MemberQ[queryBranch,originalNode]|>];

EncodePair94[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[{<|"Grammar"->"S94MixedContextObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate86E["EncoderParams"],frozenCandidate86E["K"]];
First[encoded["Codes"]]];

DiamondAfterDoubleAfterHierarchical94[c_List]:=
DiamondIn72[DoubleDiamondIn79[HierarchicalDiamondIn80[c]]];
HierarchicalAfterDiamondAfterDouble94[c_List]:=
HierarchicalDiamondIn80[DiamondIn72[DoubleDiamondIn79[c]]];
TopologyTransform94[topology_String,c_List]:=Switch[topology,
"DiamondAfterDoubleAfterHierarchical",
DiamondAfterDoubleAfterHierarchical94[c],
"HierarchicalAfterDiamondAfterDouble",
HierarchicalAfterDiamondAfterDouble94[c],_,$Failed];
NoisePhase94[topology_String]:=Switch[topology,
"DiamondAfterDoubleAfterHierarchical",0,
"HierarchicalAfterDiamondAfterDouble",1,_,Missing["UnknownTopology"]];
ExpectedContractions94[topology_String,baseCase_List]:=Switch[topology,
"DiamondAfterDoubleAfterHierarchical",
6 DecisionIncomingEdgeCount79B[baseCase],
"HierarchicalAfterDiamondAfterDouble",
6 DecisionIncomingEdgeCount79B[baseCase],_,Missing["UnknownTopology"]];

PrepareWorld94[topology_String,depth_Integer,target_String,
answer_Integer]:=Module[{noisePhase,baseCase,topologyCase,canonicalization,
canonicalCase,expectedContractions,traceSeconds,trace,levels,pack,vertexList,
packedNodes,observations,originalNode,pair,roleInfo,featureVector,
singleWorldBaseline,nonQueryContinue,nonQueryStop},
noisePhase=NoisePhase94[topology];
baseCase=Case94[depth,answer,target,noisePhase];
topologyCase=TopologyTransform94[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions94[topology,baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole94[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair94[pair]|>],packedNodes];
featureVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
singleWorldBaseline=TCCTPredictWorldS87D[<|"Observations"->observations|>,
baseDecoderLoaded94];
nonQueryContinue=Count[DeleteCases[Range[13],answer],i_/;
EvenQ[i+noisePhase]];nonQueryStop=12-nonQueryContinue;
<|"Topology"->topology,"Depth"->depth,"NoisePhase"->noisePhase,
"GraphCondition"->"MixedContextQueried"<>target,"Answer"->answer,
"Target"->target,"ReferenceAction"->ReferenceAction94[canonicalCase],
"BranchCount"->13,"NonQueryContinueBranches"->nonQueryContinue,
"NonQueryStopBranches"->nonQueryStop,"FeatureVector"->featureVector,
"Cardinality"->featureVector[[{1,2,18}]],
"SingleWorldBaselinePrediction"->singleWorldBaseline,
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
expectedContractions],"ProtectedNodesPreserved"->
canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds|>];

PrepareScenario94[topology_String,depth_Integer]:=Module[
{continueWorlds,stopWorlds,worldPairs},
continueWorlds=Table[PrepareWorld94[topology,depth,"Continue",answer],
{answer,Range[13]}];stopWorlds=Table[
PrepareWorld94[topology,depth,"Stop",answer],{answer,Range[13]}];
worldPairs=MapThread[Function[{continue,stop},Module[
{continueFirst,stopFirst},continueFirst=TCCTPredictOrderedPairVectorsS92B[
continue["FeatureVector"],stop["FeatureVector"],pairDecoderLoaded94];
stopFirst=TCCTPredictOrderedPairVectorsS92B[stop["FeatureVector"],
continue["FeatureVector"],pairDecoderLoaded94];
<|"Answer"->continue["Answer"],"ContinueFirstPrediction"->continueFirst,
"StopFirstPrediction"->stopFirst,
"ContinueFirstCorrect"->SameQ[continueFirst,"FirstContinue"],
"StopFirstCorrect"->SameQ[stopFirst,"FirstStop"],
"PairCorrect"->And[SameQ[continueFirst,"FirstContinue"],
SameQ[stopFirst,"FirstStop"]],
"CardinalityExactlyMatched"->SameQ[continue["Cardinality"],
stop["Cardinality"]],"FullFeatureVectorsDifferent"->
UnsameQ[continue["FeatureVector"],stop["FeatureVector"]],
"ReferenceRelationCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"ContinueWorld"->continue,"StopWorld"->stop|>]],
{continueWorlds,stopWorlds}];
<|"Topology"->topology,"Depth"->depth,"NoisePhase"->NoisePhase94[topology],
"AllCardinalitiesExactlyMatched"->And@@Lookup[worldPairs,
"CardinalityExactlyMatched"],"AllFullFeatureVectorsDifferent"->
And@@Lookup[worldPairs,"FullFeatureVectorsDifferent"],
"ReferenceRelationsCorrect"->And@@Lookup[worldPairs,
"ReferenceRelationCorrect"],"AllPairsCorrect"->And@@Lookup[worldPairs,
"PairCorrect"],"WorldPairs"->worldPairs,
"ContinueWorlds"->continueWorlds,"StopWorlds"->stopWorlds|>];

S94TestDefinitionBundle[]:={DownValues[T94],DownValues[Case94],
DownValues[ReferenceAction94],DownValues[NodeRole94],DownValues[EncodePair94],
DownValues[DiamondAfterDoubleAfterHierarchical94],
DownValues[HierarchicalAfterDiamondAfterDouble94],
DownValues[TopologyTransform94],DownValues[NoisePhase94],
DownValues[ExpectedContractions94],DownValues[PrepareWorld94],
DownValues[PrepareScenario94]};

blindBranchCount94=13;blindDepths94={131,193};
blindTopologies94={"DiamondAfterDoubleAfterHierarchical",
"HierarchicalAfterDiamondAfterDouble"};
topologySpec94=<|
"DiamondAfterDoubleAfterHierarchical"->
"DiamondIn72AfterDoubleDiamondIn79AfterHierarchicalDiamondIn80_Phase0",
"HierarchicalAfterDiamondAfterDouble"->
"HierarchicalDiamondIn80AfterDiamondIn72AfterDoubleDiamondIn79_Phase1"|>;
topologySpecHash94=Hash[Normal[topologySpec94],"SHA256","HexString"];
testDefinitionHashBefore94=Hash[S94TestDefinitionBundle[],"SHA256","HexString"];
noCasesBeforeProtocolHash94=And[!ValueQ[blindScenarios94],
!ValueQ[blindWorlds94],!ValueQ[blindPairs94]];
protocol94=<|"Stage"->"S94","Name"->"MixedContextRobustnessBlind",
"Candidate"->"S92B-FrozenPairedContrastDecoder",
"CandidateHash"->pairDecoderLoaded94["CandidateHash"],
"CandidateFileHash"->fileHashesBefore94[[5]],
"PairRuntimeFileHash"->fileHashesBefore94[[4]],
"S93CheckpointFileHash"->fileHashesBefore94[[7]],
"BranchCount"->13,"Depths"->blindDepths94,
"Topologies"->blindTopologies94,"TopologySpecHash"->topologySpecHash94,
"ExpectedScenarios"->4,"ExpectedPairs"->52,"ExpectedWorlds"->104,
"ExpectedOrientedDecisions"->104,
"ExternalGrammar"->"IndependentThirteenBranchMixedContextT94",
"QueriedActionRegime"->"ContinueVersusStop",
"NonQueryActionRegime"->"AlternatingContinueStopWithTwoPhases",
"Pairing"->"SameTopologyDepthAnswerNoiseContextBothInputOrders",
"CardinalityConstraint"->"PairedCardinalityMustMatchButNeedNotBeOneOneZero",
"CandidateReads"->"OnlyFrozenPosition3Modulo33PairContrast",
"SuccessCriterion"->"ValidHarnessAndAll52PairsCorrectInBothOrders",
"CandidateFrozenBeforeProtocol"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash94|>;
protocolHash94=Hash[Normal[protocol94],"SHA256","HexString"];
Dataset[{Join[protocol94,<|"ProtocolHash"->protocolHash94,
"TestDefinitionHash"->testDefinitionHashBefore94|>]}]
'''.strip()

evaluation = r'''
blindScenarios94=Flatten[Table[PrepareScenario94[topology,depth],
{topology,blindTopologies94},{depth,blindDepths94}],1];
continueWorlds94=Flatten[Lookup[blindScenarios94,"ContinueWorlds"],1];
stopWorlds94=Flatten[Lookup[blindScenarios94,"StopWorlds"],1];
blindWorlds94=Join[continueWorlds94,stopWorlds94];
blindPairs94=Flatten[Lookup[blindScenarios94,"WorldPairs"],1];
summary94=<|"Scenarios"->Length[blindScenarios94],
"Pairs"->Length[blindPairs94],"Worlds"->Length[blindWorlds94],
"OrientedDecisions"->2 Length[blindPairs94],
"ContinueFirstCorrect"->Count[blindPairs94,p_/;
TrueQ[p["ContinueFirstCorrect"]]],"StopFirstCorrect"->Count[blindPairs94,p_/;
TrueQ[p["StopFirstCorrect"]]],"PairCorrect"->Count[blindPairs94,p_/;
TrueQ[p["PairCorrect"]]],"UnknownPredictions"->Total[
Count[Lookup[blindPairs94,#],"Unknown"]&/@
{"ContinueFirstPrediction","StopFirstPrediction"}],
"CardinalityPairsMatched"->Count[blindPairs94,p_/;
TrueQ[p["CardinalityExactlyMatched"]]],
"FullFeatureVectorPairsDifferent"->Count[blindPairs94,p_/;
TrueQ[p["FullFeatureVectorsDifferent"]]],
"ReferenceRelationsCorrect"->Count[blindPairs94,p_/;
TrueQ[p["ReferenceRelationCorrect"]]],
"ReferenceActionsCorrect"->Count[blindWorlds94,w_/;
SameQ[w["ReferenceAction"],w["Target"]]],
"MixedContextWorlds"->Count[blindWorlds94,w_/;And[
w["NonQueryContinueBranches"]>0,w["NonQueryStopBranches"]>0]],
"CanonicalCaseExactlyBase"->Count[blindWorlds94,w_/;
TrueQ[w["CanonicalCaseExactlyBase"]]],
"ContractionCountCorrect"->Count[blindWorlds94,w_/;
TrueQ[w["ContractionCountCorrect"]]],
"ProtectedNodesPreserved"->Count[blindWorlds94,w_/;
TrueQ[w["ProtectedNodesPreserved"]]],
"ValidFeatureVectors"->Count[blindWorlds94,w_/;
VectorQ[w["FeatureVector"],IntegerQ]&&Length[w["FeatureVector"]]===27],
"TerminatedNaturally"->Count[blindWorlds94,w_/;
TrueQ[w["TerminatedNaturally"]]],"HitSafetyCap"->Count[blindWorlds94,w_/;
TrueQ[w["HitSafetyCap"]]],"ThirteenBranchWorlds"->Count[blindWorlds94,w_/;
SameQ[w["BranchCount"],13]],"ScenarioCardinalityMatched"->
Count[blindScenarios94,s_/;TrueQ[s["AllCardinalitiesExactlyMatched"]]],
"ScenarioFullVectorsDifferent"->Count[blindScenarios94,s_/;
TrueQ[s["AllFullFeatureVectorsDifferent"]]],
"ScenarioReferenceRelationsCorrect"->Count[blindScenarios94,s_/;
TrueQ[s["ReferenceRelationsCorrect"]]],"ScenarioPerfect"->
Count[blindScenarios94,s_/;TrueQ[s["AllPairsCorrect"]]],
"SingleWorldBaselineCorrect"->Count[blindWorlds94,w_/;
SameQ[w["SingleWorldBaselinePrediction"],w["Target"]]],
"CardinalityDistribution"->Counts[Lookup[blindWorlds94,"Cardinality"]],
"TotalTraceSeconds"->Total@Lookup[blindWorlds94,"TraceSeconds"]|>;
byTopology94=Map[Function[topology,Module[{pairs},pairs=Select[blindPairs94,
SameQ[#1["ContinueWorld"]["Topology"],topology]&];
<|"Topology"->topology,"Pairs"->Length[pairs],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
"Unknown"->Total[Count[Lookup[pairs,#],"Unknown"]&/@
{"ContinueFirstPrediction","StopFirstPrediction"}]|>]],blindTopologies94];
byDepth94=Map[Function[depth,Module[{pairs},pairs=Select[blindPairs94,
SameQ[#1["ContinueWorld"]["Depth"],depth]&];
<|"Depth"->depth,"Pairs"->Length[pairs],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]]|>]],blindDepths94];
Column[{Dataset[{summary94}],Dataset[byTopology94],Dataset[byDepth94]}]
'''.strip()

audit = r'''
modelHashAfter94=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94=Hash[Normal[KeyDrop[baseDecoderLoaded94,
{"Classifier"}]],"SHA256","HexString"];
pairDecoderObjectHashAfter94=Hash[Normal[KeyDrop[pairDecoderLoaded94,
{"Policy"}]],"SHA256","HexString"];
coreHashAfter94=Hash[CoreDefinitionBundle94[],"SHA256","HexString"];
canonicalizerHashAfter94=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter94=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94=Hash[PairRuntimeDefinitionBundle94[],
"SHA256","HexString"];
testDefinitionHashAfter94=Hash[S94TestDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter94=Hash[Normal[protocol94],"SHA256","HexString"];
fileHashesAfter94=FileSHA256Hex94/@requiredFiles94;
integrityPassed94=And[SameQ[modelHashBefore94,modelHashAfter94],
SameQ[k33ObjectHashBefore94,k33ObjectHashAfter94],
SameQ[baseDecoderObjectHashBefore94,baseDecoderObjectHashAfter94],
SameQ[pairDecoderObjectHashBefore94,pairDecoderObjectHashAfter94],
SameQ[coreHashBefore94,coreHashAfter94],
SameQ[canonicalizerHashBefore94,canonicalizerHashAfter94],
SameQ[interventionHashBefore94,interventionHashAfter94],
SameQ[topologyPrimitiveHashBefore94,topologyPrimitiveHashAfter94],
SameQ[baseRuntimeDefinitionHashBefore94,baseRuntimeDefinitionHashAfter94],
SameQ[pairRuntimeDefinitionHashBefore94,pairRuntimeDefinitionHashAfter94],
SameQ[testDefinitionHashBefore94,testDefinitionHashAfter94],
SameQ[protocolHash94,protocolHashAfter94],
SameQ[fileHashesBefore94,fileHashesAfter94]];
testValidityPassed94=And[TrueQ[integrityPassed94],
SameQ[summary94["Scenarios"],4],SameQ[summary94["Pairs"],52],
SameQ[summary94["Worlds"],104],SameQ[summary94["OrientedDecisions"],104],
SameQ[summary94["CardinalityPairsMatched"],52],
SameQ[summary94["FullFeatureVectorPairsDifferent"],52],
SameQ[summary94["ReferenceRelationsCorrect"],52],
SameQ[summary94["ReferenceActionsCorrect"],104],
SameQ[summary94["MixedContextWorlds"],104],
SameQ[summary94["CanonicalCaseExactlyBase"],104],
SameQ[summary94["ContractionCountCorrect"],104],
SameQ[summary94["ProtectedNodesPreserved"],104],
SameQ[summary94["ValidFeatureVectors"],104],
SameQ[summary94["TerminatedNaturally"],104],
SameQ[summary94["HitSafetyCap"],0],
SameQ[summary94["ThirteenBranchWorlds"],104],
SameQ[summary94["ScenarioCardinalityMatched"],4],
SameQ[summary94["ScenarioFullVectorsDifferent"],4],
SameQ[summary94["ScenarioReferenceRelationsCorrect"],4]];
blindPerfect94=And[TrueQ[testValidityPassed94],
SameQ[summary94["UnknownPredictions"],0],
SameQ[summary94["ContinueFirstCorrect"],52],
SameQ[summary94["StopFirstCorrect"],52],
SameQ[summary94["PairCorrect"],52],SameQ[summary94["ScenarioPerfect"],4]];
orientedAccuracy94=N[(summary94["ContinueFirstCorrect"]+
summary94["StopFirstCorrect"])/104];
resultPayload94=<|"Stage"->"S94","Name"->"MixedContextRobustnessBlind",
"CandidateHash"->pairDecoderLoaded94["CandidateHash"],
"CandidateFileHash"->fileHashesAfter94[[5]],
"PairRuntimeFileHash"->fileHashesAfter94[[4]],
"S93CheckpointFileHash"->fileHashesAfter94[[7]],
"ProtocolHash"->protocolHashAfter94,
"TestDefinitionHash"->testDefinitionHashAfter94,
"BranchCount"->13,"Depths"->blindDepths94,
"Topologies"->blindTopologies94,"Scenarios"->summary94["Scenarios"],
"Pairs"->summary94["Pairs"],"Worlds"->summary94["Worlds"],
"OrientedDecisions"->summary94["OrientedDecisions"],
"ContinueFirstCorrect"->summary94["ContinueFirstCorrect"],
"StopFirstCorrect"->summary94["StopFirstCorrect"],
"PairCorrect"->summary94["PairCorrect"],
"OrientedAccuracy"->orientedAccuracy94,
"UnknownPredictions"->summary94["UnknownPredictions"],
"CardinalityPairsMatched"->summary94["CardinalityPairsMatched"],
"CardinalityDistribution"->summary94["CardinalityDistribution"],
"FullFeatureVectorPairsDifferent"->
summary94["FullFeatureVectorPairsDifferent"],
"MixedContextWorlds"->summary94["MixedContextWorlds"],
"SingleWorldBaselineCorrect"->summary94["SingleWorldBaselineCorrect"],
"TestValidityPassed"->testValidityPassed94,"BlindPerfect"->blindPerfect94,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94,modelHashAfter94],
"BaseFrozenS87DDecoderChanged"->!SameQ[baseDecoderObjectHashBefore94,
baseDecoderObjectHashAfter94],"FrozenPairDecoderChanged"->
!SameQ[pairDecoderObjectHashBefore94,pairDecoderObjectHashAfter94],
"CoreChanged"->!SameQ[coreHashBefore94,coreHashAfter94],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94,
canonicalizerHashAfter94],"InterventionCoreChanged"->
!SameQ[interventionHashBefore94,interventionHashAfter94],
"TopologyPrimitivesChanged"->!SameQ[topologyPrimitiveHashBefore94,
topologyPrimitiveHashAfter94],"BaseFeatureRuntimeChanged"->
!SameQ[baseRuntimeDefinitionHashBefore94,baseRuntimeDefinitionHashAfter94],
"PairRuntimeChanged"->!SameQ[pairRuntimeDefinitionHashBefore94,
pairRuntimeDefinitionHashAfter94],"TestDefinitionChangedDuringRun"->
!SameQ[testDefinitionHashBefore94,testDefinitionHashAfter94],
"ProtocolChangedDuringRun"->!SameQ[protocolHash94,protocolHashAfter94],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94,coreHashAfter94],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94,coreHashAfter94]|>;
blindResultHash94=Hash[Normal[resultPayload94],"SHA256","HexString"];
cert94=Join[resultPayload94,<|"CandidateFrozenBeforeS94"->True,
"BlindProtocolHashedBeforeCases"->True,"TrainingRun"->False,
"CandidateSearchRun"->False,"DecoderEditApplied"->False,
"RetuningApplied"->False,"HistoricalBlindTestsRerun"->False,
"MayClaimBlindMixedContextRobustness"->blindPerfect94,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary94["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash94,
"Outcome"->Which[!TrueQ[testValidityPassed94],
"S94_INVALID_BLIND_TEST_DO_NOT_INTERPRET",TrueQ[blindPerfect94],
"S94_BLIND_MIXED_CONTEXT_ROBUSTNESS_PASS",True,
"S94_VALID_BLIND_FAILURE_DO_NOT_RETUNE"],
"SuggestedNextStage"->Which[!TrueQ[testValidityPassed94],
"S94R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",TrueQ[blindPerfect94],
"S95_PARTIAL_OBSERVATION_AND_PAIR_MISMATCH_STRESS",True,
"S94A_FAILURE_AUDIT_WITHOUT_RETUNING"]|>];
certificateExportResult94=Quiet@Check[
Export[s94ResultCertificatePath,cert94,"RawJSON"],$Failed];
certificateExported94=StringQ[certificateExportResult94]&&
FileExistsQ[s94ResultCertificatePath];
Column[{Dataset[{cert94}],Dataset[byTopology94],Dataset[byDepth94],
Dataset[{<|"CertificateExported"->certificateExported94,
"CertificatePath"->s94ResultCertificatePath,
"CertificateFileHash"->If[certificateExported94,
FileSHA256Hex94[s94ResultCertificatePath],Missing[]]|>}]}]
'''.strip()

cells = [core, locks, protocol, evaluation, audit]
WL.write_text("\n\n".join(
    f"(* S94 CELL {i} *)\n{cell}" for i, cell in enumerate(cells, 1)
) + "\n", encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(
    f"(* S94 PREFLIGHT CELL {i} *)\n{cell}"
    for i, cell in enumerate(cells[:3], 1)
) + "\n", encoding="utf-8")


def code_cell(source: str, stage: str) -> dict:
    return {"cell_type": "code", "execution_count": None,
            "metadata": {"tcct_stage": stage}, "outputs": [],
            "source": source.splitlines(keepends=True)}


metadata = {"kernelspec": {"display_name": "Wolfram Language 15",
"language": "Wolfram Language", "name": "wolframlanguage15"},
"language_info": {"codemirror_mode": "mathematica", "file_extension": ".wl",
"mimetype": "application/vnd.wolfram.mathematica", "name": "Wolfram Language",
"pygments_lexer": "mathematica", "version": "15.0"}}
markdown = {"cell_type": "markdown", "metadata": {}, "source": [
"# TCCT S94 - Mixed-Context Robustness Blind Test\n", "\n",
"The frozen S92B pair decoder is evaluated without retraining on a new 13-branch "
"grammar. Non-query branches alternate Continue and Stop in two phases, while the "
"queried branch alone changes between each matched pair. New depths and three-layer "
"topology compositions are used. Both pair orientations are scored.\n", "\n",
"Run **Kernel -> Restart Kernel and Run All Cells**. Expected runtime is about "
"10-15 minutes. Preserve the first certificate regardless of outcome.\n"]}
preflight_markdown = {"cell_type": "markdown", "metadata": {}, "source": [
"# TCCT S94 - Preflight Only\n", "\n",
"Locked-input and protocol validation only. No S94 world is generated.\n"]}
notebook = {"cells": [markdown] + [code_cell(cell, stage) for cell, stage in zip(
cells, ["S94-CORE", "S94-LOCKS", "S94-PROTOCOL", "S94-BLIND-EVALUATION",
"S94-AUDIT"])], "metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
preflight_notebook = {"cells": [preflight_markdown] + [
code_cell(cell, stage) for cell, stage in zip(cells[:3],
["S94-PREFLIGHT-CORE", "S94-PREFLIGHT-LOCKS", "S94-PREFLIGHT-PROTOCOL"])],
"metadata": metadata, "nbformat": 4, "nbformat_minor": 5}
NB.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
PREFLIGHT_NB.write_text(json.dumps(preflight_notebook, ensure_ascii=False, indent=1)
+ "\n", encoding="utf-8")

LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S94_MixedContextRobustnessBlind.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S92B_FrozenPairedContrastDecoder.wxf"
set "TCCT_S93=E:\engine_wolf\TCCT_S93_PairedCounterfactualBlindCertificate.json"
set "TCCT_S94_RESULT=E:\engine_wolf\TCCT_S94_MixedContextRobustnessBlindCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s94"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s94"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S94 notebook not found & pause & exit /b 1)
if not exist "%TCCT_CANDIDATE%" (echo Frozen pair candidate not found & pause & exit /b 1)
if not exist "%TCCT_S93%" (echo Locked S93 certificate not found & pause & exit /b 1)
if exist "%TCCT_S94_RESULT%" (echo Prior S94 certificate exists. Preserve it. & pause & exit /b 1)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S94 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8909 --ServerApp.port_retries=5
exit /b 0
''', encoding="utf-8")

precommit = {"Stage": "S94", "Name": "MixedContextRobustnessBlind",
"BlindTest": True, "CandidateFrozenBeforeS94": True,
"FrozenCandidateHash": "540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c",
"S93CertificateSHA256": "d0c863119cf03e93e27e0db175163cd91ca4c980197a5fd1f6688f3ddc94c072",
"BranchCount": 13, "Depths": [131, 193],
"Topologies": ["DiamondAfterDoubleAfterHierarchical",
"HierarchicalAfterDiamondAfterDouble"], "ExpectedScenarios": 4,
"ExpectedPairs": 52, "ExpectedWorlds": 104, "ExpectedOrientedDecisions": 104,
"NonQueryActionRegime": "AlternatingContinueStopWithTwoPhases",
"ProtocolHash": "4e0e41ef24649fde483e2e362e6bf83ffdc589da8ee3ae72f5e4caa6b5b91fd1",
"TestDefinitionHash": "5045ca99a3ba7f0133c917435e716c4cd7d78e3ba44c77729f63ff0e20e9c2ad",
"TopologySpecHash": "04daa5000cf3aa28d20ebdfeadefab5867ee51b853fd1cfd1f86fe1d82dc11e5",
"DynamicPreflightPassed": True, "FullSourceParsePassed": True,
"BlindCasesGeneratedDuringPreflight": False,
"ResultCertificateCreatedDuringPreflight": False,
"TrainingRun": False, "CandidateSearchRun": False, "RetuningApplied": False,
"NoBlindCasesGeneratedDuringBuild": True,
"RealS94CertificateCreatedDuringBuild": False,
"WolframSourceSHA256": sha256(WL), "NotebookSHA256": sha256(NB),
"PreflightSourceSHA256": sha256(PREFLIGHT_WL),
"PreflightNotebookSHA256": sha256(PREFLIGHT_NB)}
PRECOMMIT.write_text(json.dumps(precommit, ensure_ascii=False, indent=2) + "\n",
encoding="utf-8")
for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path)
