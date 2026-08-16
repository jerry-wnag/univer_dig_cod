"""Build TCCT S93 preregistered paired-counterfactual blind test."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE92 = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind.wl"
WL = ROOT / "TCCT_S93_PairedCounterfactualBlind.wl"
NB = ROOT / "TCCT_S93_PairedCounterfactualBlind.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S93_PairedCounterfactualBlind_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S93_PairedCounterfactualBlind_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S93_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S93_Precommit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


source92 = SOURCE92.read_text(encoding="utf-8")
core = source92.split("(* S92 CELL 2 *)", 1)[0]
core = core.replace("(* S92 CELL 1 *)", "", 1).strip()

locks = r'''
expectedFrozenModelHash93=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash93=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedK33CandidateFileHash93=
"4a252b8977101d024b1b2feb00b4626ca28290c3982cdad199bc78ef7e0c98f1";
expectedBaseDecoderCandidateHash93=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedBaseDecoderCandidateFileHash93=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedBaseRuntimeFileHash93=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedPairDecoderCandidateHash93=
"540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c";
expectedPairDecoderCandidateFileHash93=
"aecbe544a4af3a8ad0ba0494bb11312dd4a4b71f1a1c7ae42489a5300c7078ff";
expectedPairRuntimeFileHash93=
"74a926b8efccaddbd1dd07373ac35a93bc53e9fb08cc456ce1adb6a006d333c6";
expectedS92CertificateFileHash93=
"22cec6972285fe127e66d740bfdbbf27fbabaa097cb24cc0bbc7196da004a40b";
expectedS92ACertificateFileHash93=
"7d21e30f1da322f2a078cc5c0fe9cf44cec5cfac0cc18f0020517a76ad897309";
expectedS92BCertificateFileHash93=
"85247775ef008a5ddf2378c54585d645dbf6b910d2b6085c1f8c29a98a9c2eb4";
expectedS92BlindResultHash93=
"a715ad1366f300a3e149c9f1df83c8e81744a7583678482900ed8736e4fc2273";
expectedS92AAuditResultHash93=
"976a850af3f591b8766f0aeb3439b70678b051e91ef0452c1df77dfebf0fd9f9";
expectedS92BCertificateResultHash93=
"0e3301be5d06af42d7e44ddb0e2b02e377fc378fcfefe98d928db875fc6c7373";
expectedS92BProtocolHash93=
"decbe5ac7cd99bc31eee33712245f221e8c90d5a046ec3076f0f933e2fde777f";

k33CandidatePath93="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
baseDecoderRuntimePath93="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
baseDecoderCandidatePath93="E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
pairDecoderRuntimePath93="E:/engine_wolf/TCCT_S92B_PairedContrastDecoderRuntime.wl";
pairDecoderCandidatePath93="E:/engine_wolf/TCCT_S92B_FrozenPairedContrastDecoder.wxf";
s92CertificatePath93="E:/engine_wolf/TCCT_S92_BlindResultCertificate.json";
s92aCertificatePath93="E:/engine_wolf/TCCT_S92A_FailureAuditCertificate.json";
s92bCertificatePath93="E:/engine_wolf/TCCT_S92B_PairedContrastDecoderCertificate.json";
s93ResultCertificatePath="E:/engine_wolf/TCCT_S93_PairedCounterfactualBlindCertificate.json";

ClearAll[FileSHA256Hex93];
FileSHA256Hex93[path_String]:=If[FileExistsQ[path],
IntegerString[FileHash[path,"SHA256"],16,64],Missing["FileMissing",path]];
requiredFiles93={k33CandidatePath93,baseDecoderRuntimePath93,
baseDecoderCandidatePath93,pairDecoderRuntimePath93,pairDecoderCandidatePath93,
s92CertificatePath93,s92aCertificatePath93,s92bCertificatePath93};
If[!And@@(FileExistsQ/@requiredFiles93),
Print["S93 aborted: one or more locked input files are missing."];
Dataset[AssociationThread[requiredFiles93,FileExistsQ/@requiredFiles93]];
Abort[]];
If[FileExistsQ[s93ResultCertificatePath],
Print["S93 aborted: a prior blind certificate already exists."];
Print["Preserve it; do not overwrite, rerun, or retune."];Abort[]];

k33CandidateFileHashBefore93=FileSHA256Hex93[k33CandidatePath93];
baseRuntimeFileHashBefore93=FileSHA256Hex93[baseDecoderRuntimePath93];
baseCandidateFileHashBefore93=FileSHA256Hex93[baseDecoderCandidatePath93];
pairRuntimeFileHashBefore93=FileSHA256Hex93[pairDecoderRuntimePath93];
pairCandidateFileHashBefore93=FileSHA256Hex93[pairDecoderCandidatePath93];
s92CertificateFileHashBefore93=FileSHA256Hex93[s92CertificatePath93];
s92aCertificateFileHashBefore93=FileSHA256Hex93[s92aCertificatePath93];
s92bCertificateFileHashBefore93=FileSHA256Hex93[s92bCertificatePath93];

Clear[frozenCandidate86E];Get[k33CandidatePath93];
k33CandidateHashLoaded93=If[AssociationQ[frozenCandidate86E],
Hash[Normal[frozenCandidate86E],"SHA256","HexString"],Missing[]];
Get[baseDecoderRuntimePath93];
baseDecoderLoaded93=Quiet@Check[
TCCTLoadFrozenDecoderS87D[baseDecoderCandidatePath93],$Failed];
baseDecoderRaw93=If[AssociationQ[baseDecoderLoaded93],
KeyDrop[baseDecoderLoaded93,{"Classifier"}],$Failed];
Get[pairDecoderRuntimePath93];
pairDecoderLoaded93=Quiet@Check[
TCCTLoadFrozenPairDecoderS92B[pairDecoderCandidatePath93],$Failed];
pairDecoderRaw93=If[AssociationQ[pairDecoderLoaded93],
KeyDrop[pairDecoderLoaded93,{"Policy"}],$Failed];
s92Certificate93=Quiet@Check[Import[s92CertificatePath93,"RawJSON"],$Failed];
s92aCertificate93=Quiet@Check[Import[s92aCertificatePath93,"RawJSON"],$Failed];
s92bCertificate93=Quiet@Check[Import[s92bCertificatePath93,"RawJSON"],$Failed];

ClearAll[CoreDefinitionBundle93,PairRuntimeDefinitionBundle93];
CoreDefinitionBundle93[]:=CoreDefinitionBundle86[];
PairRuntimeDefinitionBundle93[]:={
DownValues[TCCTPairContrastVectorS92B],
DownValues[TCCTLoadFrozenPairDecoderS92B],
DownValues[TCCTPredictOrderedPairVectorsS92B],
DownValues[TCCTPredictOrderedPairWorldsS92B]};
modelHashBefore93=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashBefore93=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashBefore93=If[AssociationQ[baseDecoderRaw93],
Hash[Normal[baseDecoderRaw93],"SHA256","HexString"],Missing[]];
pairDecoderObjectHashBefore93=If[AssociationQ[pairDecoderRaw93],
Hash[Normal[pairDecoderRaw93],"SHA256","HexString"],Missing[]];
coreHashBefore93=Hash[CoreDefinitionBundle93[],"SHA256","HexString"];
canonicalizerHashBefore93=Hash[{
DownValues[FindPrivateDiamond79B],DownValues[CanonicalizePrivateDiamonds79B],
DownValues[CanonicalCase79B]},"SHA256","HexString"];
interventionHashBefore93=Hash[{
DownValues[LocalMediatorSources82],DownValues[FullSemanticPatch82],
DownValues[LocalMediatorPatch82],DownValues[ReferenceAction82]},
"SHA256","HexString"];
topologyPrimitiveHashBefore93=Hash[{
DownValues[DiamondIn72],DownValues[DoubleDiamondIn79],
DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"];
baseRuntimeDefinitionHashBefore93=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashBefore93=Hash[
PairRuntimeDefinitionBundle93[],"SHA256","HexString"];

preflightPassed93=And[
TrueQ[preflightPassed86],SameQ[modelHashBefore93,expectedFrozenModelHash93],
AssociationQ[frozenCandidate86E],
SameQ[k33CandidateHashLoaded93,expectedK33CandidateHash93],
SameQ[k33CandidateFileHashBefore93,expectedK33CandidateFileHash93],
SameQ[frozenCandidate86E["K"],33],
AssociationQ[baseDecoderLoaded93],AssociationQ[baseDecoderRaw93],
SameQ[baseDecoderLoaded93["CandidateHash"],expectedBaseDecoderCandidateHash93],
SameQ[baseCandidateFileHashBefore93,expectedBaseDecoderCandidateFileHash93],
SameQ[baseRuntimeFileHashBefore93,expectedBaseRuntimeFileHash93],
AssociationQ[pairDecoderLoaded93],AssociationQ[pairDecoderRaw93],
SameQ[pairDecoderLoaded93["CandidateHash"],expectedPairDecoderCandidateHash93],
SameQ[Hash[Normal[KeyDrop[pairDecoderRaw93,{"CandidateHash"}]],
"SHA256","HexString"],expectedPairDecoderCandidateHash93],
SameQ[pairCandidateFileHashBefore93,expectedPairDecoderCandidateFileHash93],
SameQ[pairRuntimeFileHashBefore93,expectedPairRuntimeFileHash93],
SameQ[pairDecoderRaw93["PairRuntimeFileHash"],expectedPairRuntimeFileHash93],
SameQ[pairDecoderRaw93["ContrastPosition"],3],
SameQ[pairDecoderRaw93["ContrastFeature"],"FirstCoordinateTotal"],
SameQ[pairDecoderRaw93["Modulus"],33],
SameQ[pairDecoderRaw93["PolicyRules"],{
<|"Delta"->6,"Prediction"->"FirstStop"|>,
<|"Delta"->27,"Prediction"->"FirstContinue"|>}],
TrueQ[pairDecoderRaw93["FrozenBeforeS93"]],
TrueQ[pairDecoderRaw93["S93DataReadBeforeFreeze"]===False],
AssociationQ[s92Certificate93],
SameQ[s92CertificateFileHashBefore93,expectedS92CertificateFileHash93],
SameQ[s92Certificate93["BlindResultHash"],expectedS92BlindResultHash93],
AssociationQ[s92aCertificate93],
SameQ[s92aCertificateFileHashBefore93,expectedS92ACertificateFileHash93],
SameQ[s92aCertificate93["AuditResultHash"],expectedS92AAuditResultHash93],
AssociationQ[s92bCertificate93],
SameQ[s92bCertificateFileHashBefore93,expectedS92BCertificateFileHash93],
SameQ[s92bCertificate93["CertificateResultHash"],
expectedS92BCertificateResultHash93],
SameQ[s92bCertificate93["ProtocolHash"],expectedS92BProtocolHash93],
SameQ[s92bCertificate93["Outcome"],
"S92B_PAIRED_CONTRAST_DECODER_FROZEN_FOR_S93"],
TrueQ[s92bCertificate93["FreezeValidityPassed"]],
!FileExistsQ[s93ResultCertificatePath]
];
preflight93=<|"Stage"->"S93","Name"->"PairedCounterfactualBlind",
"PreflightPassed"->preflightPassed93,
"PairCandidateFrozenBeforeS93"->True,
"PairCandidateHash"->If[AssociationQ[pairDecoderLoaded93],
pairDecoderLoaded93["CandidateHash"],Missing[]],
"PairCandidateFileHash"->pairCandidateFileHashBefore93,
"PairRuntimeFileHash"->pairRuntimeFileHashBefore93,
"BaseCandidateHash"->If[AssociationQ[baseDecoderLoaded93],
baseDecoderLoaded93["CandidateHash"],Missing[]],
"BranchCount"->12,"Depths"->{113,181},
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"S93ResultAlreadyPresent"->FileExistsQ[s93ResultCertificatePath]|>;
If[!TrueQ[preflightPassed93],Print[Dataset[{preflight93}]];
Print["S93 aborted: frozen inputs or checkpoint locks failed."];Abort[]];
Dataset[{preflight93}]
'''.strip()

protocol = r'''
ClearAll[T93,Case93,ReferenceAction93,NodeRole93,EncodePair93,
HierarchicalThenDoubleIn93,DoubleThenHierarchicalIn93,
TopologyTransform93,ExpectedContractions93,PrepareWorld93,PrepareScenario93,
S93TestDefinitionBundle];

T93[depth_Integer,target_String,answer_Integer,seed_Integer,
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
Case93[depth_Integer,answer_Integer,target_String]:=
T93[depth,target,answer,93000000+100 depth,12];

ReferenceAction93[c_List]:=Module[
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

NodeRole93[originalNode_,case_List,answer_Integer]:=Module[
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

EncodePair93[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[{<|"Grammar"->"S93BlindObservation",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate86E["EncoderParams"],frozenCandidate86E["K"]];
First[encoded["Codes"]]];

HierarchicalThenDoubleIn93[c_List]:=
DoubleDiamondIn79[HierarchicalDiamondIn80[c]];
DoubleThenHierarchicalIn93[c_List]:=
HierarchicalDiamondIn80[DoubleDiamondIn79[c]];
TopologyTransform93[topology_String,c_List]:=Switch[topology,
"HierarchicalThenDoubleIn",HierarchicalThenDoubleIn93[c],
"DoubleThenHierarchicalIn",DoubleThenHierarchicalIn93[c],_,$Failed];
ExpectedContractions93[topology_String,baseCase_List]:=Switch[topology,
"HierarchicalThenDoubleIn",5 DecisionIncomingEdgeCount79B[baseCase],
"DoubleThenHierarchicalIn",5 DecisionIncomingEdgeCount79B[baseCase],
_,Missing["UnknownTopology"]];

PrepareWorld93[topology_String,depth_Integer,target_String,
answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,observations,
originalNode,pair,roleInfo,featureVector,singleWorldBaseline},
baseCase=Case93[depth,answer,target];
topologyCase=TopologyTransform93[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions93[topology,baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole93[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair93[pair]|>],packedNodes];
featureVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
singleWorldBaseline=TCCTPredictWorldS87D[<|"Observations"->observations|>,
baseDecoderLoaded93];
<|"Topology"->topology,"Depth"->depth,"GraphCondition"->
"Uniform"<>target,"Answer"->answer,"Target"->target,
"ReferenceAction"->ReferenceAction93[canonicalCase],"BranchCount"->12,
"FeatureVector"->featureVector,"Cardinality"->featureVector[[{1,2,18}]],
"SingleWorldBaselinePrediction"->singleWorldBaseline,
"TopologyGraphHash"->Hash[topologyCase[[1,1]],"SHA256","HexString"],
"CanonicalGraphHash"->Hash[canonicalCase[[1,1]],"SHA256","HexString"],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
expectedContractions],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"StateObservationCount"->Length[observations],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"Rounds"->trace["Rounds"],
"TraceSeconds"->traceSeconds|>
];

PrepareScenario93[topology_String,depth_Integer]:=Module[
{continueWorlds,stopWorlds,worldPairs,continueHashes,stopHashes},
continueWorlds=Table[PrepareWorld93[topology,depth,"Continue",answer],
{answer,Range[12]}];
stopWorlds=Table[PrepareWorld93[topology,depth,"Stop",answer],
{answer,Range[12]}];
worldPairs=MapThread[Function[{continue,stop},Module[
{continueFirstPrediction,stopFirstPrediction},
continueFirstPrediction=TCCTPredictOrderedPairVectorsS92B[
continue["FeatureVector"],stop["FeatureVector"],pairDecoderLoaded93];
stopFirstPrediction=TCCTPredictOrderedPairVectorsS92B[
stop["FeatureVector"],continue["FeatureVector"],pairDecoderLoaded93];
<|"Answer"->continue["Answer"],
"SameAnswer"->SameQ[continue["Answer"],stop["Answer"]],
"ContinueFirstPrediction"->continueFirstPrediction,
"StopFirstPrediction"->stopFirstPrediction,
"ContinueFirstCorrect"->SameQ[continueFirstPrediction,"FirstContinue"],
"StopFirstCorrect"->SameQ[stopFirstPrediction,"FirstStop"],
"PairCorrect"->And[SameQ[continueFirstPrediction,"FirstContinue"],
SameQ[stopFirstPrediction,"FirstStop"]],
"CardinalityExactlyMatched"->SameQ[continue["Cardinality"],
stop["Cardinality"],{1,1,0}],
"FullFeatureVectorsDifferent"->UnsameQ[continue["FeatureVector"],
stop["FeatureVector"]],
"ReferenceRelationCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"ContinueWorld"->continue,"StopWorld"->stop|>]],
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
"AllPairsCorrect"->And@@Lookup[worldPairs,"PairCorrect"],
"WorldPairs"->worldPairs,"ContinueWorlds"->continueWorlds,
"StopWorlds"->stopWorlds|>
];

S93TestDefinitionBundle[]:={DownValues[T93],DownValues[Case93],
DownValues[ReferenceAction93],DownValues[NodeRole93],DownValues[EncodePair93],
DownValues[HierarchicalThenDoubleIn93],
DownValues[DoubleThenHierarchicalIn93],DownValues[TopologyTransform93],
DownValues[ExpectedContractions93],DownValues[PrepareWorld93],
DownValues[PrepareScenario93]};

blindBranchCount93=12;blindDepths93={113,181};
blindTopologies93={"HierarchicalThenDoubleIn","DoubleThenHierarchicalIn"};
topologySpec93=<|
"HierarchicalThenDoubleIn"->
"DoubleDiamondIn79AfterHierarchicalDiamondIn80",
"DoubleThenHierarchicalIn"->
"HierarchicalDiamondIn80AfterDoubleDiamondIn79"|>;
topologySpecHash93=Hash[Normal[topologySpec93],"SHA256","HexString"];
testDefinitionHashBefore93=Hash[S93TestDefinitionBundle[],"SHA256","HexString"];
noCasesBeforeProtocolHash93=And[!ValueQ[blindScenarios93],
!ValueQ[blindWorlds93],!ValueQ[blindPairs93]];
protocol93=<|"Stage"->"S93","Name"->"PairedCounterfactualBlind",
"Candidate"->"S92B-FrozenPairedContrastDecoder",
"CandidateHash"->pairDecoderLoaded93["CandidateHash"],
"CandidateFileHash"->pairCandidateFileHashBefore93,
"PairRuntimeFileHash"->pairRuntimeFileHashBefore93,
"BaseCandidateHash"->baseDecoderLoaded93["CandidateHash"],
"S92BCheckpointFileHash"->s92bCertificateFileHashBefore93,
"BranchCount"->blindBranchCount93,"Depths"->blindDepths93,
"Topologies"->blindTopologies93,"TopologySpecHash"->topologySpecHash93,
"ExpectedScenarios"->4,"ExpectedPairs"->48,"ExpectedWorlds"->96,
"ExpectedOrientedDecisions"->96,
"ExternalGrammar"->"IndependentTwelveBranchT93",
"ActionRegime"->"UniformAllBranchesContinueVersusUniformAllBranchesStop",
"Pairing"->"SameTopologyDepthAnswerOppositeActionBothInputOrders",
"CardinalityConstraint"->
"EveryPairedWorldHasObservationDistinctPairCounts_1_1_0",
"CandidateReads"->"OnlyFrozenPosition3Modulo33PairContrast",
"ForbiddenCandidateInputs"->{"Cardinality","Topology","Depth","Answer",
"Target","GraphCondition"},
"SuccessCriterion"->
"ValidHarnessAndAll48PairsCorrectInBothInputOrders",
"CandidateFrozenBeforeProtocol"->True,
"S93GrammarAbsentDuringS92BFreeze"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"NoCaseEvaluatedBeforeProtocolHash"->noCasesBeforeProtocolHash93|>;
protocolHash93=Hash[Normal[protocol93],"SHA256","HexString"];
Dataset[{Join[protocol93,<|"ProtocolHash"->protocolHash93,
"TestDefinitionHash"->testDefinitionHashBefore93|>]}]
'''.strip()

evaluation = r'''
blindScenarios93=Flatten[Table[PrepareScenario93[topology,depth],
{topology,blindTopologies93},{depth,blindDepths93}],1];
continueWorlds93=Flatten[Lookup[blindScenarios93,"ContinueWorlds"],1];
stopWorlds93=Flatten[Lookup[blindScenarios93,"StopWorlds"],1];
blindWorlds93=Join[continueWorlds93,stopWorlds93];
blindPairs93=Flatten[Lookup[blindScenarios93,"WorldPairs"],1];

summary93=<|"Scenarios"->Length[blindScenarios93],
"Pairs"->Length[blindPairs93],"Worlds"->Length[blindWorlds93],
"OrientedDecisions"->2 Length[blindPairs93],
"ContinueFirstCorrect"->Count[blindPairs93,p_/;
TrueQ[p["ContinueFirstCorrect"]]],
"StopFirstCorrect"->Count[blindPairs93,p_/;TrueQ[p["StopFirstCorrect"]]],
"PairCorrect"->Count[blindPairs93,p_/;TrueQ[p["PairCorrect"]]],
"UnknownPredictions"->Total[Count[Lookup[blindPairs93,#],"Unknown"]&/@
{"ContinueFirstPrediction","StopFirstPrediction"}],
"CardinalityPairsMatched"->Count[blindPairs93,p_/;
TrueQ[p["CardinalityExactlyMatched"]]],
"FullFeatureVectorPairsDifferent"->Count[blindPairs93,p_/;
TrueQ[p["FullFeatureVectorsDifferent"]]],
"ReferenceRelationsCorrect"->Count[blindPairs93,p_/;
TrueQ[p["ReferenceRelationCorrect"]]],
"ReferenceActionsCorrect"->Count[blindWorlds93,w_/;
SameQ[w["ReferenceAction"],w["Target"]]],
"CardinalityOneOneZero"->Count[blindWorlds93,w_/;
SameQ[w["Cardinality"],{1,1,0}]],
"CanonicalCaseExactlyBase"->Count[blindWorlds93,w_/;
TrueQ[w["CanonicalCaseExactlyBase"]]],
"ContractionCountCorrect"->Count[blindWorlds93,w_/;
TrueQ[w["ContractionCountCorrect"]]],
"ProtectedNodesPreserved"->Count[blindWorlds93,w_/;
TrueQ[w["ProtectedNodesPreserved"]]],
"ValidFeatureVectors"->Count[blindWorlds93,w_/;
VectorQ[w["FeatureVector"],IntegerQ]&&Length[w["FeatureVector"]]===27],
"TerminatedNaturally"->Count[blindWorlds93,w_/;
TrueQ[w["TerminatedNaturally"]]],
"HitSafetyCap"->Count[blindWorlds93,w_/;TrueQ[w["HitSafetyCap"]]],
"TwelveBranchWorlds"->Count[blindWorlds93,w_/;
SameQ[w["BranchCount"],12]],
"ScenarioCardinalityMatched"->Count[blindScenarios93,s_/;
TrueQ[s["AllCardinalitiesExactlyMatched"]]],
"ScenarioFullVectorsDifferent"->Count[blindScenarios93,s_/;
TrueQ[s["AllFullFeatureVectorsDifferent"]]],
"ScenarioReferenceRelationsCorrect"->Count[blindScenarios93,s_/;
TrueQ[s["ReferenceRelationsCorrect"]]],
"ScenarioPerfect"->Count[blindScenarios93,s_/;TrueQ[s["AllPairsCorrect"]]],
"SingleWorldBaselineCorrect"->Count[blindWorlds93,w_/;
SameQ[w["SingleWorldBaselinePrediction"],w["Target"]]],
"TotalTraceSeconds"->Total@Lookup[blindWorlds93,"TraceSeconds"]|>;

byTopology93=Map[Function[topology,Module[{pairs},
pairs=Select[blindPairs93,SameQ[#1["ContinueWorld"]["Topology"],topology]&];
<|"Topology"->topology,"Pairs"->Length[pairs],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
"ContinueFirstCorrect"->Count[pairs,p_/;TrueQ[p["ContinueFirstCorrect"]]],
"StopFirstCorrect"->Count[pairs,p_/;TrueQ[p["StopFirstCorrect"]]]|>]],
blindTopologies93];
byDepth93=Map[Function[depth,Module[{pairs},
pairs=Select[blindPairs93,SameQ[#1["ContinueWorld"]["Depth"],depth]&];
<|"Depth"->depth,"Pairs"->Length[pairs],
"PairCorrect"->Count[pairs,p_/;TrueQ[p["PairCorrect"]]],
"ContinueFirstCorrect"->Count[pairs,p_/;TrueQ[p["ContinueFirstCorrect"]]],
"StopFirstCorrect"->Count[pairs,p_/;TrueQ[p["StopFirstCorrect"]]]|>]],
blindDepths93];
Column[{Dataset[{summary93}],Dataset[byTopology93],Dataset[byDepth93]}]
'''.strip()

audit = r'''
modelHashAfter93=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter93=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderRawAfter93=KeyDrop[baseDecoderLoaded93,{"Classifier"}];
pairDecoderRawAfter93=KeyDrop[pairDecoderLoaded93,{"Policy"}];
baseDecoderObjectHashAfter93=Hash[Normal[baseDecoderRawAfter93],
"SHA256","HexString"];
pairDecoderObjectHashAfter93=Hash[Normal[pairDecoderRawAfter93],
"SHA256","HexString"];
coreHashAfter93=Hash[CoreDefinitionBundle93[],"SHA256","HexString"];
canonicalizerHashAfter93=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter93=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter93=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter93=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter93=Hash[
PairRuntimeDefinitionBundle93[],"SHA256","HexString"];
testDefinitionHashAfter93=Hash[S93TestDefinitionBundle[],"SHA256","HexString"];
protocolHashAfter93=Hash[Normal[protocol93],"SHA256","HexString"];
k33CandidateFileHashAfter93=FileSHA256Hex93[k33CandidatePath93];
baseRuntimeFileHashAfter93=FileSHA256Hex93[baseDecoderRuntimePath93];
baseCandidateFileHashAfter93=FileSHA256Hex93[baseDecoderCandidatePath93];
pairRuntimeFileHashAfter93=FileSHA256Hex93[pairDecoderRuntimePath93];
pairCandidateFileHashAfter93=FileSHA256Hex93[pairDecoderCandidatePath93];
s92CertificateFileHashAfter93=FileSHA256Hex93[s92CertificatePath93];
s92aCertificateFileHashAfter93=FileSHA256Hex93[s92aCertificatePath93];
s92bCertificateFileHashAfter93=FileSHA256Hex93[s92bCertificatePath93];

integrityPassed93=And[
SameQ[modelHashBefore93,modelHashAfter93],
SameQ[k33ObjectHashBefore93,k33ObjectHashAfter93],
SameQ[baseDecoderObjectHashBefore93,baseDecoderObjectHashAfter93],
SameQ[pairDecoderObjectHashBefore93,pairDecoderObjectHashAfter93],
SameQ[coreHashBefore93,coreHashAfter93],
SameQ[canonicalizerHashBefore93,canonicalizerHashAfter93],
SameQ[interventionHashBefore93,interventionHashAfter93],
SameQ[topologyPrimitiveHashBefore93,topologyPrimitiveHashAfter93],
SameQ[baseRuntimeDefinitionHashBefore93,baseRuntimeDefinitionHashAfter93],
SameQ[pairRuntimeDefinitionHashBefore93,pairRuntimeDefinitionHashAfter93],
SameQ[testDefinitionHashBefore93,testDefinitionHashAfter93],
SameQ[protocolHash93,protocolHashAfter93],
SameQ[k33CandidateFileHashBefore93,k33CandidateFileHashAfter93],
SameQ[baseRuntimeFileHashBefore93,baseRuntimeFileHashAfter93],
SameQ[baseCandidateFileHashBefore93,baseCandidateFileHashAfter93],
SameQ[pairRuntimeFileHashBefore93,pairRuntimeFileHashAfter93],
SameQ[pairCandidateFileHashBefore93,pairCandidateFileHashAfter93],
SameQ[s92CertificateFileHashBefore93,s92CertificateFileHashAfter93],
SameQ[s92aCertificateFileHashBefore93,s92aCertificateFileHashAfter93],
SameQ[s92bCertificateFileHashBefore93,s92bCertificateFileHashAfter93]];

cardinalityValidityPassed93=And[
SameQ[summary93["CardinalityPairsMatched"],48],
SameQ[summary93["CardinalityOneOneZero"],96],
SameQ[summary93["FullFeatureVectorPairsDifferent"],48],
SameQ[Counts[Lookup[continueWorlds93,"Cardinality"]],
Counts[Lookup[stopWorlds93,"Cardinality"]],<|{1,1,0}->48|>]];
testValidityPassed93=And[TrueQ[integrityPassed93],
TrueQ[cardinalityValidityPassed93],SameQ[summary93["Scenarios"],4],
SameQ[summary93["Pairs"],48],SameQ[summary93["Worlds"],96],
SameQ[summary93["OrientedDecisions"],96],
SameQ[summary93["ReferenceRelationsCorrect"],48],
SameQ[summary93["ReferenceActionsCorrect"],96],
SameQ[summary93["CanonicalCaseExactlyBase"],96],
SameQ[summary93["ContractionCountCorrect"],96],
SameQ[summary93["ProtectedNodesPreserved"],96],
SameQ[summary93["ValidFeatureVectors"],96],
SameQ[summary93["TerminatedNaturally"],96],
SameQ[summary93["HitSafetyCap"],0],
SameQ[summary93["TwelveBranchWorlds"],96],
SameQ[summary93["ScenarioCardinalityMatched"],4],
SameQ[summary93["ScenarioFullVectorsDifferent"],4],
SameQ[summary93["ScenarioReferenceRelationsCorrect"],4]];
blindPerfect93=And[TrueQ[testValidityPassed93],
SameQ[summary93["UnknownPredictions"],0],
SameQ[summary93["ContinueFirstCorrect"],48],
SameQ[summary93["StopFirstCorrect"],48],
SameQ[summary93["PairCorrect"],48],
SameQ[summary93["ScenarioPerfect"],4]];
orientedAccuracy93=N[(summary93["ContinueFirstCorrect"]+
summary93["StopFirstCorrect"])/96];

resultPayload93=<|"Stage"->"S93","Name"->"PairedCounterfactualBlind",
"CandidateHash"->pairDecoderLoaded93["CandidateHash"],
"CandidateFileHash"->pairCandidateFileHashAfter93,
"PairRuntimeFileHash"->pairRuntimeFileHashAfter93,
"BaseCandidateHash"->baseDecoderLoaded93["CandidateHash"],
"S92BCheckpointFileHash"->s92bCertificateFileHashAfter93,
"ProtocolHash"->protocolHashAfter93,
"TestDefinitionHash"->testDefinitionHashAfter93,
"BranchCount"->12,"Depths"->blindDepths93,
"Topologies"->blindTopologies93,"Scenarios"->summary93["Scenarios"],
"Pairs"->summary93["Pairs"],"Worlds"->summary93["Worlds"],
"OrientedDecisions"->summary93["OrientedDecisions"],
"ContinueFirstCorrect"->summary93["ContinueFirstCorrect"],
"StopFirstCorrect"->summary93["StopFirstCorrect"],
"PairCorrect"->summary93["PairCorrect"],
"OrientedAccuracy"->orientedAccuracy93,
"UnknownPredictions"->summary93["UnknownPredictions"],
"CardinalityPairsMatched"->summary93["CardinalityPairsMatched"],
"CardinalityOneOneZero"->summary93["CardinalityOneOneZero"],
"FullFeatureVectorPairsDifferent"->
summary93["FullFeatureVectorPairsDifferent"],
"SingleWorldBaselineCorrect"->summary93["SingleWorldBaselineCorrect"],
"CardinalityValidityPassed"->cardinalityValidityPassed93,
"TestValidityPassed"->testValidityPassed93,"BlindPerfect"->blindPerfect93,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore93,modelHashAfter93],
"BaseFrozenS87DDecoderChanged"->!SameQ[baseDecoderObjectHashBefore93,
baseDecoderObjectHashAfter93],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore93,
pairDecoderObjectHashAfter93],
"CoreChanged"->!SameQ[coreHashBefore93,coreHashAfter93],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore93,
canonicalizerHashAfter93],
"InterventionCoreChanged"->!SameQ[interventionHashBefore93,
interventionHashAfter93],
"TopologyPrimitivesChanged"->!SameQ[topologyPrimitiveHashBefore93,
topologyPrimitiveHashAfter93],
"BaseFeatureRuntimeChanged"->!SameQ[baseRuntimeDefinitionHashBefore93,
baseRuntimeDefinitionHashAfter93],
"PairRuntimeChanged"->!SameQ[pairRuntimeDefinitionHashBefore93,
pairRuntimeDefinitionHashAfter93],
"TestDefinitionChangedDuringRun"->!SameQ[testDefinitionHashBefore93,
testDefinitionHashAfter93],
"ProtocolChangedDuringRun"->!SameQ[protocolHash93,protocolHashAfter93],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore93,coreHashAfter93],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore93,coreHashAfter93]|>;
blindResultHash93=Hash[Normal[resultPayload93],"SHA256","HexString"];
cert93=Join[resultPayload93,<|
"CandidateFrozenBeforeS93"->True,
"BlindProtocolHashedBeforeCases"->True,
"S93GrammarAbsentDuringS92BFreeze"->True,
"TrainingRun"->False,"CandidateSearchRun"->False,
"DecoderEditApplied"->False,"RetuningApplied"->False,
"HistoricalBlindTestsRerun"->False,
"MayClaimBlindPairedCounterfactualTransfer"->blindPerfect93,
"MayClaimSingleWorldReasoningFixed"->False,
"MayClaimGeneralCounterfactualReasoning"->False,
"MayClaimCausalDiscovery"->False,
"TotalTraceSeconds"->summary93["TotalTraceSeconds"],
"BlindResultHash"->blindResultHash93,
"Outcome"->Which[!TrueQ[testValidityPassed93],
"S93_INVALID_BLIND_TEST_DO_NOT_INTERPRET",
TrueQ[blindPerfect93],"S93_BLIND_PAIRED_COUNTERFACTUAL_TRANSFER_PASS",
True,"S93_VALID_BLIND_FAILURE_DO_NOT_RETUNE"],
"SuggestedNextStage"->Which[!TrueQ[testValidityPassed93],
"S93R_REPAIR_HARNESS_WITHOUT_MODEL_CHANGE",TrueQ[blindPerfect93],
"S94_INDEPENDENT_PAIR_GRAMMAR_AND_NOISE_ROBUSTNESS",
True,"S93A_FAILURE_AUDIT_WITHOUT_RETUNING"]|>];
certificateExportResult93=Quiet@Check[
Export[s93ResultCertificatePath,cert93,"RawJSON"],$Failed];
certificateExported93=StringQ[certificateExportResult93]&&
FileExistsQ[s93ResultCertificatePath];
Column[{Dataset[{cert93}],Dataset[byTopology93],Dataset[byDepth93],
Dataset[{<|"CertificateExported"->certificateExported93,
"CertificatePath"->s93ResultCertificatePath,
"CertificateFileHash"->If[certificateExported93,
FileSHA256Hex93[s93ResultCertificatePath],Missing[]]|>}]}]
'''.strip()

cells = [core, locks, protocol, evaluation, audit]
WL.write_text("\n\n".join(
    f"(* S93 CELL {i} *)\n{cell}" for i, cell in enumerate(cells, 1)
) + "\n", encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(
    f"(* S93 PREFLIGHT CELL {i} *)\n{cell}"
    for i, cell in enumerate(cells[:3], 1)
) + "\n", encoding="utf-8")


def code_cell(source: str, stage: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"tcct_stage": stage},
        "outputs": [],
        "source": source.splitlines(keepends=True),
    }


markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S93 - Preregistered Paired Counterfactual Blind Test\n",
        "\n",
        "S93 evaluates the already frozen S92B paired decoder on a new 12-branch "
        "grammar, unseen answer positions, new depths, and two unseen topology "
        "composition orders. Both input orientations are scored.\n",
        "\n",
        "The protocol and test-definition hashes are created before any S93 world. "
        "No training, candidate search, decoder edit, or retuning is permitted. "
        "Regardless of outcome, preserve the certificate and do not rerun S93 as a "
        "blind test.\n",
        "\n",
        "Run **Kernel -> Restart Kernel and Run All Cells**. Expected runtime is "
        "approximately 5-8 minutes.\n",
    ],
}
preflight_markdown = {
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# TCCT S93 - Preflight Only\n",
        "\n",
        "This notebook loads locked inputs and hashes the S93 protocol without "
        "generating or evaluating any S93 case.\n",
    ],
}

metadata = {
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
}
notebook = {
    "cells": [markdown] + [
        code_cell(cell, stage) for cell, stage in zip(cells, [
            "S93-CORE", "S93-LOCKED-INPUT-PREFLIGHT", "S93-PROTOCOL",
            "S93-BLIND-EVALUATION", "S93-AUDIT-AND-CERTIFICATE"
        ])
    ],
    "metadata": metadata,
    "nbformat": 4,
    "nbformat_minor": 5,
}
preflight_notebook = {
    "cells": [preflight_markdown] + [
        code_cell(cell, stage) for cell, stage in zip(cells[:3], [
            "S93-PREFLIGHT-CORE", "S93-PREFLIGHT-LOCKS", "S93-PREFLIGHT-PROTOCOL"
        ])
    ],
    "metadata": metadata,
    "nbformat": 4,
    "nbformat_minor": 5,
}
NB.write_text(json.dumps(notebook, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
PREFLIGHT_NB.write_text(
    json.dumps(preflight_notebook, ensure_ascii=False, indent=1) + "\n",
    encoding="utf-8",
)

LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal
set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S93_PairedCounterfactualBlind.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S92B_FrozenPairedContrastDecoder.wxf"
set "TCCT_S92B=E:\engine_wolf\TCCT_S92B_PairedContrastDecoderCertificate.json"
set "TCCT_S93_RESULT=E:\engine_wolf\TCCT_S93_PairedCounterfactualBlindCertificate.json"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s93"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s93"
set "PYTHONUTF8=1"
if not exist "%JUPYTER_LAB%" (echo JupyterLab not found & pause & exit /b 1)
if not exist "%TCCT_NOTEBOOK%" (echo S93 notebook not found & pause & exit /b 1)
if not exist "%TCCT_CANDIDATE%" (echo Frozen S92B candidate not found & pause & exit /b 1)
if not exist "%TCCT_S92B%" (echo Locked S92B certificate not found & pause & exit /b 1)
if exist "%TCCT_S93_RESULT%" (
  echo A prior S93 blind certificate already exists.
  echo Preserve it. Do not rerun or overwrite S93.
  pause & exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S93 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8908 --ServerApp.port_retries=5
exit /b 0
''', encoding="utf-8")

precommit = {
    "Stage": "S93",
    "Name": "PairedCounterfactualBlind",
    "BlindTest": True,
    "CandidateFrozenBeforeS93": True,
    "FrozenCandidateHash": "540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c",
    "FrozenCandidateSHA256": "aecbe544a4af3a8ad0ba0494bb11312dd4a4b71f1a1c7ae42489a5300c7078ff",
    "PairRuntimeSHA256": "74a926b8efccaddbd1dd07373ac35a93bc53e9fb08cc456ce1adb6a006d333c6",
    "S92BCertificateSHA256": "85247775ef008a5ddf2378c54585d645dbf6b910d2b6085c1f8c29a98a9c2eb4",
    "BranchCount": 12,
    "Depths": [113, 181],
    "Topologies": ["HierarchicalThenDoubleIn", "DoubleThenHierarchicalIn"],
    "ExpectedScenarios": 4,
    "ExpectedPairs": 48,
    "ExpectedWorlds": 96,
    "ExpectedOrientedDecisions": 96,
    "ProtocolHash": "2ea5fc7dbe7bd6f9f28e147f22e1fe9cd0406e4ea9bbc3d94a77a8a8f5e09efe",
    "TestDefinitionHash": "c06578879fc7bbc806f5bec9228351d043daf2b95341c6a08db4194b6e125629",
    "TopologySpecHash": "f881f9dffb05ea666de0184e5e4e4d059771878b89c701fda77359b427be189e",
    "TrainingRun": False,
    "CandidateSearchRun": False,
    "RetuningApplied": False,
    "CoreEditApplied": False,
    "NoBlindCasesGeneratedDuringBuild": True,
    "DynamicPreflightPassed": True,
    "FullSourceParsePassed": True,
    "RealS93CertificateCreatedDuringBuild": False,
    "WolframSourceSHA256": sha256(WL),
    "NotebookSHA256": sha256(NB),
    "PreflightSourceSHA256": sha256(PREFLIGHT_WL),
    "PreflightNotebookSHA256": sha256(PREFLIGHT_NB),
}
PRECOMMIT.write_text(json.dumps(precommit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path)
