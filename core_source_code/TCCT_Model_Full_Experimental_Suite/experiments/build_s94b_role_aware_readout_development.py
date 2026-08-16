"""Build TCCT S94B role-aware antisymmetric readout development benchmark."""

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE93 = ROOT / "TCCT_S93_PairedCounterfactualBlind.wl"
WL = ROOT / "TCCT_S94B_RoleAwareReadoutDevelopment.wl"
NB = ROOT / "TCCT_S94B_RoleAwareReadoutDevelopment.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94B_RoleAwareReadoutDevelopment_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94B_RoleAwareReadoutDevelopment_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94B_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94B_Precommit.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def notebook(code_cells: list[str], title: str, note: str) -> dict:
    cells = [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [f"# {title}\n", "\n", note],
        }
    ]
    for code in code_cells:
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [line + "\n" for line in code.splitlines()],
            }
        )
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Wolfram Language",
                "language": "Wolfram Language",
                "name": "wolframlanguage15.0",
            },
            "language_info": {
                "codemirror_mode": "mathematica",
                "file_extension": ".wl",
                "mimetype": "application/vnd.wolfram.mathematica",
                "name": "Wolfram Language",
                "version": "15.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


source93 = SOURCE93.read_text(encoding="utf-8")
core = source93.split("(* S93 CELL 2 *)", 1)[0]
core = core.replace("(* S93 CELL 1 *)", "", 1).strip()

locks = r'''
expectedFrozenModelHash94B=
"d6477c370436d09cf3e8cfc8530decd13ebf8bb79120362146ecb419f9d6a6c4";
expectedK33CandidateHash94B=
"2eb674929cfe1710231a4f508d13b20fe0f98d84d2c594c6261f46f370066ae4";
expectedK33CandidateFileHash94B=
"4a252b8977101d024b1b2feb00b4626ca28290c3982cdad199bc78ef7e0c98f1";
expectedBaseCandidateHash94B=
"703e1365490a0123eac61745876dbcf29066abac4c753bb6ec1f61b790e222fe";
expectedBaseCandidateFileHash94B=
"82616c6acde25ecd7bbbc51bc80d03771ec8653bf033167ac9ccd74d7da01d91";
expectedBaseRuntimeFileHash94B=
"7d45fffdb3e33a0f0759ae9fa93c84429743cbe39fc7f02c38eeef11739740ee";
expectedPairCandidateHash94B=
"540229035af53b2e014592fd7e7d2eab70b374844d9a73000026325c6cd39a1c";
expectedPairCandidateFileHash94B=
"aecbe544a4af3a8ad0ba0494bb11312dd4a4b71f1a1c7ae42489a5300c7078ff";
expectedPairRuntimeFileHash94B=
"74a926b8efccaddbd1dd07373ac35a93bc53e9fb08cc456ce1adb6a006d333c6";
expectedS94AAuditFileHash94B=
"ab0f6524f8cb8ee8edb915e132044734f8db8ce20758c09f26ded9de01571571";

k33CandidatePath94B="E:/engine_wolf/TCCT_S86E_K33FrozenCandidate.wl";
baseRuntimePath94B="E:/engine_wolf/TCCT_S87D_FrozenDecoderRuntime.wl";
baseCandidatePath94B="E:/engine_wolf/TCCT_S87D_FrozenWorldMultisetDecoder.wxf";
pairRuntimePath94B="E:/engine_wolf/TCCT_S92B_PairedContrastDecoderRuntime.wl";
pairCandidatePath94B="E:/engine_wolf/TCCT_S92B_FrozenPairedContrastDecoder.wxf";
s94aAuditPath94B="E:/engine_wolf/TCCT_S94A_ModulusFeasibilityAudit.json";
developmentPairsPath94B="E:/engine_wolf/TCCT_S94B_RoleAwareDevelopmentPairs.wxf";
resultCertificatePath94B="E:/engine_wolf/TCCT_S94B_RoleAwareReadoutDevelopment.json";

ClearAll[FileSHA256Hex94B,CoreDefinitionBundle94B,
PairRuntimeDefinitionBundle94B];
FileSHA256Hex94B[path_String]:=If[FileExistsQ[path],
IntegerString[FileHash[path,"SHA256"],16,64],Missing["FileMissing",path]];
CoreDefinitionBundle94B[]:=CoreDefinitionBundle86[];
PairRuntimeDefinitionBundle94B[]:={DownValues[TCCTPairContrastVectorS92B],
DownValues[TCCTLoadFrozenPairDecoderS92B],
DownValues[TCCTPredictOrderedPairVectorsS92B],
DownValues[TCCTPredictOrderedPairWorldsS92B]};

requiredFiles94B={k33CandidatePath94B,baseRuntimePath94B,
baseCandidatePath94B,pairRuntimePath94B,pairCandidatePath94B,s94aAuditPath94B};
If[!And@@(FileExistsQ/@requiredFiles94B),
Print["S94B aborted: one or more locked inputs are missing."];
Dataset[AssociationThread[requiredFiles94B,FileExistsQ/@requiredFiles94B]];Abort[]];
If[FileExistsQ[resultCertificatePath94B]&&
FileByteCount[resultCertificatePath94B]>0,
Print["S94B aborted: a prior development certificate exists. Preserve it."];Abort[]];
If[FileExistsQ[developmentPairsPath94B]&&
FileByteCount[developmentPairsPath94B]>0,
Print["S94B aborted: a prior development-pair artifact exists. Preserve it."];Abort[]];

fileHashesBefore94B=FileSHA256Hex94B/@requiredFiles94B;
Clear[frozenCandidate86E];Get[k33CandidatePath94B];
k33HashLoaded94B=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
Get[baseRuntimePath94B];
baseDecoderLoaded94B=Quiet@Check[
TCCTLoadFrozenDecoderS87D[baseCandidatePath94B],$Failed];
baseDecoderRaw94B=If[AssociationQ[baseDecoderLoaded94B],
KeyDrop[baseDecoderLoaded94B,{"Classifier"}],$Failed];
Get[pairRuntimePath94B];
pairDecoderLoaded94B=Quiet@Check[
TCCTLoadFrozenPairDecoderS92B[pairCandidatePath94B],$Failed];
pairDecoderRaw94B=If[AssociationQ[pairDecoderLoaded94B],
KeyDrop[pairDecoderLoaded94B,{"Policy"}],$Failed];
s94aAudit94B=Quiet@Check[Import[s94aAuditPath94B,"RawJSON"],$Failed];

modelHashBefore94B=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashBefore94B=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashBefore94B=Hash[Normal[baseDecoderRaw94B],"SHA256","HexString"];
pairDecoderObjectHashBefore94B=Hash[Normal[pairDecoderRaw94B],"SHA256","HexString"];
coreHashBefore94B=Hash[CoreDefinitionBundle94B[],"SHA256","HexString"];
canonicalizerHashBefore94B=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashBefore94B=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashBefore94B=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashBefore94B=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashBefore94B=Hash[
PairRuntimeDefinitionBundle94B[],"SHA256","HexString"];

preflightPassed94B=And[
SameQ[modelHashBefore94B,expectedFrozenModelHash94B],
SameQ[k33HashLoaded94B,expectedK33CandidateHash94B],
SameQ[fileHashesBefore94B[[1]],expectedK33CandidateFileHash94B],
AssociationQ[baseDecoderLoaded94B],
SameQ[baseDecoderRaw94B["CandidateHash"],expectedBaseCandidateHash94B],
SameQ[fileHashesBefore94B[[2]],expectedBaseRuntimeFileHash94B],
SameQ[fileHashesBefore94B[[3]],expectedBaseCandidateFileHash94B],
AssociationQ[pairDecoderLoaded94B],
SameQ[pairDecoderRaw94B["CandidateHash"],expectedPairCandidateHash94B],
SameQ[fileHashesBefore94B[[4]],expectedPairRuntimeFileHash94B],
SameQ[fileHashesBefore94B[[5]],expectedPairCandidateFileHash94B],
SameQ[fileHashesBefore94B[[6]],expectedS94AAuditFileHash94B],
AssociationQ[s94aAudit94B],
TrueQ[s94aAudit94B["AuditValidityPassed"]],
SameQ[s94aAudit94B["Outcome"],
"S94A_AUDIT_PASS_MODULUS_ALONE_INSUFFICIENT"],
SameQ[s94aAudit94B["CandidateHash"],expectedPairCandidateHash94B]];

preflight94B=<|"Stage"->"S94B","Name"->"RoleAwareReadoutDevelopment",
"DevelopmentOnly"->True,"BlindTest"->False,
"PreflightPassed"->preflightPassed94B,
"OriginalFrozenModelLocked"->SameQ[modelHashBefore94B,expectedFrozenModelHash94B],
"S94AAuditLocked"->SameQ[fileHashesBefore94B[[6]],expectedS94AAuditFileHash94B],
"CoreChanged"->False,"TrainingRunYet"->False,
"DevelopmentCasesGeneratedYet"->False,"CandidateFrozen"->False|>;
If[!TrueQ[preflightPassed94B],Print[Dataset[{preflight94B}]];
Print["S94B aborted: locked-input preflight failed."];Abort[]];
Dataset[{preflight94B}]
'''.strip()

definitions = r'''
ClearAll[T94B,Case94B,ReferenceAction94B,NodeRole94B,EncodePair94B,
DiamondAfterDoubleAfterHierarchical94B,
HierarchicalAfterDiamondAfterDouble94B,TopologyTransform94B,
ExpectedContractions94B,RoleStats94B,RoleAwareVector94B,
PrepareWorld94B,PrepareScenario94B,RepresentationVector94B,
FitAntisymmetricReadout94B,ScoreAntisymmetricReadout94B,
FoldMemberQ94B,EvaluateCandidate94B,TestDefinitionBundle94B,
ReadoutDefinitionBundle94B];

T94B[depth_Integer,target_String,answer_Integer,seed_Integer,
branchCount_Integer,noisePhase_Integer]:=Module[
{bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,main,perm,anc,
branchAction,i},
bb=1000000000 seed;K=bb+1;
c=Table[bb+100+i,{i,branchCount}];v=Table[bb+200+i,{i,branchCount}];
q=Table[bb+300+i,{i,branchCount}];
e=Flatten[Table[{DirectedEdge[K,c[[i]]],DirectedEdge[c[[i]],v[[i]]]},{i,branchCount}],1];
Do[ib=bb+20000000 i;m=ib+1;safe=ib+2;u=ib+3;dummy=ib+4;
r1=ib+10;r2=ib+20;wrong=c[[1+Mod[i,branchCount]]];
main=Join[P59[q[[i]],r1,depth,ib+1000000],
P59[q[[i]],r2,depth,ib+2000000],{DirectedEdge[r1,m],DirectedEdge[r2,m]},
P59[q[[i]],safe,depth+1,ib+3000000]];
branchAction=If[i===answer,target,If[EvenQ[i+noisePhase],"Continue","Stop"]];
perm=If[branchAction==="Continue",
{DirectedEdge[m,c[[i]]],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],
A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];
{{Union[e],q,K,v,c,f},answer}];

Case94B[depth_Integer,answer_Integer,target_String,
topologyIndex_Integer,noisePhase_Integer]:=T94B[depth,target,answer,
94200000+1000 topologyIndex+100 depth+noisePhase,13,noisePhase];

ReferenceAction94B[c_List]:=Module[{x=c[[1]],answer=c[[2]],branchCount,e,m,
safe,u,dummy,correct,wrong,continueEdges,stopEdges},
branchCount=Length[x[[6]]];e=x[[1]];m=x[[6,answer]];safe=m+1;u=m+2;
dummy=m+3;correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,branchCount]]];
continueEdges={DirectedEdge[m,correct],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]};
stopEdges={DirectedEdge[m,wrong],DirectedEdge[safe,correct],DirectedEdge[u,dummy]};
Which[And@@(MemberQ[e,#]&/@continueEdges),"Continue",
And@@(MemberQ[e,#]&/@stopEdges),"Stop",True,"Undefined"]];

NodeRole94B[originalNode_,case_List,answer_Integer]:=Module[
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

EncodePair94B[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[{<|"Grammar"->"S94BRoleAwareDevelopment",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate86E["EncoderParams"],frozenCandidate86E["K"]];
First[encoded["Codes"]]];

DiamondAfterDoubleAfterHierarchical94B[c_List]:=
DiamondIn72[DoubleDiamondIn79[HierarchicalDiamondIn80[c]]];
HierarchicalAfterDiamondAfterDouble94B[c_List]:=
HierarchicalDiamondIn80[DiamondIn72[DoubleDiamondIn79[c]]];
TopologyTransform94B[topology_String,c_List]:=Switch[topology,
"DiamondAfterDoubleAfterHierarchical",DiamondAfterDoubleAfterHierarchical94B[c],
"HierarchicalAfterDiamondAfterDouble",HierarchicalAfterDiamondAfterDouble94B[c],
_,$Failed];
ExpectedContractions94B[baseCase_List]:=6 DecisionIncomingEdgeCount79B[baseCase];

roleOrder94B={"QueriedDecision","QueriedMediatorSource",
"QueriedCorrectDestination","QueriedWrongDestination","QueriedDummyDestination"};
RoleStats94B[observations_List,role_String]:=Module[{selected,codes,a,b},
selected=Select[observations,SameQ[Lookup[#,"Role"],role]&];
codes=Lookup[selected,"Code",{}];
If[Length[codes]===0,Return[{0,0,0,0,0,0}]];
a=codes[[All,1]];b=codes[[All,2]];
{Length[codes],Total[a],Total[b],Total[a^2],Total[b^2],Total[Abs[a-b]]}];
RoleAwareVector94B[observations_List]:=Flatten[
RoleStats94B[observations,#]&/@roleOrder94B];

PrepareWorld94B[topology_String,topologyIndex_Integer,noisePhase_Integer,
depth_Integer,target_String,answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,observations,
queryObservations,originalNode,pair,roleInfo,globalVector,roleVector,
nonQueryContinue,nonQueryStop},
baseCase=Case94B[depth,answer,target,topologyIndex,noisePhase];
topologyCase=TopologyTransform94B[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions94B[baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole94B[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair94B[pair]|>],packedNodes];
queryObservations=Select[observations,TrueQ[Lookup[#,"QueryBranchRelated",False]]&];
globalVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
roleVector=RoleAwareVector94B[queryObservations];
nonQueryContinue=Count[DeleteCases[Range[13],answer],i_/;EvenQ[i+noisePhase]];
nonQueryStop=12-nonQueryContinue;
<|"Topology"->topology,"TopologyIndex"->topologyIndex,
"NoisePhase"->noisePhase,"Depth"->depth,"Answer"->answer,
"Target"->target,"ReferenceAction"->ReferenceAction94B[canonicalCase],
"NonQueryContinueBranches"->nonQueryContinue,
"NonQueryStopBranches"->nonQueryStop,
"GlobalVector"->globalVector,"RoleVector"->roleVector,
"QueryObservationCount"->Length[queryObservations],
"QueryRoleCounts"->AssociationMap[
Count[Lookup[queryObservations,"Role"],#]&,roleOrder94B],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
expectedContractions],"ProtectedNodesPreserved"->
canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"TraceSeconds"->traceSeconds|>];

PrepareScenario94B[topology_String,topologyIndex_Integer,
noisePhase_Integer,depth_Integer]:=Module[{continueWorlds,stopWorlds,pairs},
continueWorlds=Table[PrepareWorld94B[topology,topologyIndex,noisePhase,
depth,"Continue",answer],{answer,13}];
stopWorlds=Table[PrepareWorld94B[topology,topologyIndex,noisePhase,
depth,"Stop",answer],{answer,13}];
pairs=MapThread[Function[{continue,stop},<|
"Topology"->topology,"TopologyIndex"->topologyIndex,
"NoisePhase"->noisePhase,"Depth"->depth,"Answer"->continue["Answer"],
"ContinueWorld"->continue,"StopWorld"->stop,
"GlobalDifference"->continue["GlobalVector"]-stop["GlobalVector"],
"RoleDifference"->continue["RoleVector"]-stop["RoleVector"],
"CombinedDifference"->Join[
continue["GlobalVector"]-stop["GlobalVector"],
continue["RoleVector"]-stop["RoleVector"]],
"ReferenceRelationCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]]|>],{continueWorlds,stopWorlds}];
<|"Topology"->topology,"TopologyIndex"->topologyIndex,
"NoisePhase"->noisePhase,"Depth"->depth,"Pairs"->pairs,
"ContinueWorlds"->continueWorlds,"StopWorlds"->stopWorlds|>];

RepresentationVector94B[row_Association,representation_String]:=Switch[
representation,"Global27",row["GlobalDifference"],
"Role30",row["RoleDifference"],
"Combined57",row["CombinedDifference"],_,$Failed];

FitAntisymmetricReadout94B[rows_List,representation_String,
family_String,lambda_?NumericQ]:=Module[
{differences,scale,z,mu,covariance,variance,weights},
differences=RepresentationVector94B[#,representation]&/@rows;
If[!MatrixQ[differences,NumericQ],Return[$Failed]];
scale=Sqrt[Mean[#^2]]&/@Transpose[differences];
scale=Map[If[!NumericQ[#]||Abs[N[#]]<10^-12,1.,N[#]]&,scale];
z=N[(#/scale)&/@differences];mu=Mean[z];
covariance=Transpose[z].z/Length[z]-Outer[Times,mu,mu];
variance=Diagonal[covariance];
weights=Switch[family,"Centroid",mu,
"DiagonalRidge",mu/(variance+lambda),
"FullRidge",Quiet@Check[
LinearSolve[covariance+lambda IdentityMatrix[Length[mu]],mu],$Failed],
_,$Failed];
If[!VectorQ[weights,NumericQ],Return[$Failed]];
<|"Representation"->representation,"Family"->family,
"Lambda"->lambda,"Scale"->scale,"Weights"->weights|>];

ScoreAntisymmetricReadout94B[model_Association,difference_List]:=
N[Total[model["Weights"] (difference/model["Scale"])]];
FoldMemberQ94B[row_Association,fold_Association]:=Switch[fold["Axis"],
"Topology",SameQ[row["Topology"],fold["Heldout"]],
"NoisePhase",SameQ[row["NoisePhase"],fold["Heldout"]],
"Answer",SameQ[row["Answer"],fold["Heldout"]],_,False];

EvaluateCandidate94B[rows_List,folds_List,spec_Association]:=Module[
{foldRows},foldRows=Map[Function[fold,Module[{train,test,model,scores},
test=Select[rows,TrueQ[FoldMemberQ94B[#,fold]]&];
train=Select[rows,!TrueQ[FoldMemberQ94B[#,fold]]&];
model=FitAntisymmetricReadout94B[train,spec["Representation"],
spec["Family"],spec["Lambda"]];
scores=If[AssociationQ[model],ScoreAntisymmetricReadout94B[model,
RepresentationVector94B[#,spec["Representation"]]]&/@test,{}];
<|"Axis"->fold["Axis"],"Heldout"->fold["Heldout"],
"Cases"->Length[test],"Correct"->Count[scores,x_/;x>0],
"ZeroScores"->Count[scores,x_/;Abs[x]<10^-12],
"Accuracy"->If[Length[test]>0,N[Count[scores,x_/;x>0]/Length[test]],0.],
"MinimumMargin"->If[Length[scores]>0,Min[scores],-Infinity]|>]],folds];
Join[spec,<|"Folds"->Length[foldRows],"Cases"->Total@Lookup[foldRows,"Cases"],
"Correct"->Total@Lookup[foldRows,"Correct"],
"Accuracy"->N[Total@Lookup[foldRows,"Correct"]/
Total@Lookup[foldRows,"Cases"]],
"WorstFoldAccuracy"->Min@Lookup[foldRows,"Accuracy"],
"ZeroScores"->Total@Lookup[foldRows,"ZeroScores"],
"MinimumMargin"->Min@Lookup[foldRows,"MinimumMargin"],
"FoldResults"->foldRows|>]];

TestDefinitionBundle94B[]:={DownValues[T94B],DownValues[Case94B],
DownValues[ReferenceAction94B],DownValues[NodeRole94B],DownValues[EncodePair94B],
DownValues[DiamondAfterDoubleAfterHierarchical94B],
DownValues[HierarchicalAfterDiamondAfterDouble94B],
DownValues[TopologyTransform94B],DownValues[ExpectedContractions94B],
DownValues[RoleStats94B],DownValues[RoleAwareVector94B],
DownValues[PrepareWorld94B],DownValues[PrepareScenario94B]};
ReadoutDefinitionBundle94B[]:={DownValues[RepresentationVector94B],
DownValues[FitAntisymmetricReadout94B],DownValues[ScoreAntisymmetricReadout94B],
DownValues[FoldMemberQ94B],DownValues[EvaluateCandidate94B]};

testDefinitionHashBefore94B=Hash[TestDefinitionBundle94B[],"SHA256","HexString"];
readoutDefinitionHashBefore94B=Hash[ReadoutDefinitionBundle94B[],
"SHA256","HexString"];
protocol94B=<|"Stage"->"S94B","Name"->"RoleAwareReadoutDevelopment",
"DevelopmentOnly"->True,"BlindTest"->False,
"SourceS94LabelsAlreadyRevealed"->True,
"CoreMechanismChanged"->False,
"NewOuterRepresentation"->"QuerySemanticRoleSlots",
"AntisymmetryConstraint"->"Score[x,y]==-Score[y,x]",
"BranchCount"->13,"Depth"->23,
"Topologies"->{"DiamondAfterDoubleAfterHierarchical",
"HierarchicalAfterDiamondAfterDouble"},
"NoisePhases"->{0,1},"TopologyNoiseCrossed"->True,
"ExpectedScenarios"->4,"ExpectedPairs"->52,"ExpectedWorlds"->104,
"Representations"->{"Global27","Role30","Combined57"},
"CandidateFamilies"->{"Centroid","DiagonalRidge","FullRidge"},
"ValidationAxes"->{"Topology","NoisePhase","Answer"},
"DevelopmentPassAccuracy"->0.95,"DevelopmentPassWorstFoldAccuracy"->0.8,
"CandidateFrozenAtThisStage"->False|>;
protocolHash94B=Hash[Normal[protocol94B],"SHA256","HexString"];
Dataset[{Join[protocol94B,<|"ProtocolHash"->protocolHash94B,
"TestDefinitionHash"->testDefinitionHashBefore94B,
"ReadoutDefinitionHash"->readoutDefinitionHashBefore94B|>]}]
'''.strip()

evaluation = r'''
developmentTopologies94B={"DiamondAfterDoubleAfterHierarchical",
"HierarchicalAfterDiamondAfterDouble"};
developmentScenarios94B=Flatten[Table[
PrepareScenario94B[topology,topologyIndex,noisePhase,23],
{topologyIndex,Length[developmentTopologies94B]},
{topology,{developmentTopologies94B[[topologyIndex]]}},
{noisePhase,{0,1}}],2];
developmentPairs94B=Flatten[Lookup[developmentScenarios94B,"Pairs"],1];
developmentWorlds94B=Join[
Flatten[Lookup[developmentScenarios94B,"ContinueWorlds"],1],
Flatten[Lookup[developmentScenarios94B,"StopWorlds"],1]];

folds94B=Join[
Map[<|"Axis"->"Topology","Heldout"->#|>&,developmentTopologies94B],
Map[<|"Axis"->"NoisePhase","Heldout"->#|>&,{0,1}],
Map[<|"Axis"->"Answer","Heldout"->#|>&,Range[13]]];
representations94B={"Global27","Role30","Combined57"};
candidateSpecs94B=Join[
Map[<|"Representation"->#,"Family"->"Centroid","Lambda"->1.|>&,
representations94B],
Flatten[Table[<|"Representation"->representation,"Family"->family,
"Lambda"->lambda|>,{representation,representations94B},
{family,{"DiagonalRidge","FullRidge"}},
{lambda,{0.1,1.,10.,100.}}],Infinity]];
candidateResults94B=Map[
EvaluateCandidate94B[developmentPairs94B,folds94B,#]&,candidateSpecs94B];
candidateRanking94B=SortBy[candidateResults94B,{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&,
(-Lookup[#,"MinimumMargin"])&}];
bestCandidate94B=First[candidateRanking94B];
bestGlobal94B=First@SortBy[Select[candidateRanking94B,
SameQ[Lookup[#,"Representation"],"Global27"]&],{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&}];
bestRoleAware94B=First@SortBy[Select[candidateRanking94B,
MemberQ[{"Role30","Combined57"},Lookup[#,"Representation"]]&],{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&}];

oldPairRows94B=Map[Function[pair,Module[{forward,reverse},
forward=TCCTPredictOrderedPairVectorsS92B[
pair["ContinueWorld"]["GlobalVector"],pair["StopWorld"]["GlobalVector"],
pairDecoderLoaded94B];
reverse=TCCTPredictOrderedPairVectorsS92B[
pair["StopWorld"]["GlobalVector"],pair["ContinueWorld"]["GlobalVector"],
pairDecoderLoaded94B];
<|"Forward"->forward,"Reverse"->reverse,
"Correct"->And[SameQ[forward,"FirstContinue"],
SameQ[reverse,"FirstStop"]]|>]],developmentPairs94B];

summary94B=<|"Scenarios"->Length[developmentScenarios94B],
"Pairs"->Length[developmentPairs94B],"Worlds"->Length[developmentWorlds94B],
"ReferenceRelationsCorrect"->Count[developmentPairs94B,p_/;
TrueQ[p["ReferenceRelationCorrect"]]],
"MixedContextWorlds"->Count[developmentWorlds94B,w_/;And[
w["NonQueryContinueBranches"]>0,w["NonQueryStopBranches"]>0]],
"CanonicalCaseExactlyBase"->Count[developmentWorlds94B,w_/;
TrueQ[w["CanonicalCaseExactlyBase"]]],
"ContractionCountCorrect"->Count[developmentWorlds94B,w_/;
TrueQ[w["ContractionCountCorrect"]]],
"ProtectedNodesPreserved"->Count[developmentWorlds94B,w_/;
TrueQ[w["ProtectedNodesPreserved"]]],
"ValidGlobalVectors"->Count[developmentWorlds94B,w_/;
VectorQ[w["GlobalVector"],IntegerQ]&&Length[w["GlobalVector"]]===27],
"ValidRoleVectors"->Count[developmentWorlds94B,w_/;
VectorQ[w["RoleVector"],IntegerQ]&&Length[w["RoleVector"]]===30],
"TerminatedNaturally"->Count[developmentWorlds94B,w_/;
TrueQ[w["TerminatedNaturally"]]],
"HitSafetyCap"->Count[developmentWorlds94B,w_/;TrueQ[w["HitSafetyCap"]]],
"OldFrozenPairCorrect"->Count[oldPairRows94B,p_/;TrueQ[p["Correct"]]],
"OldFrozenUnknownPredictions"->Total[
Count[Lookup[oldPairRows94B,#],"Unknown"]&/@{"Forward","Reverse"}],
"TotalTraceSeconds"->Total@Lookup[developmentWorlds94B,"TraceSeconds"]|>;

testValidityPassed94B=And[
SameQ[summary94B["Scenarios"],4],SameQ[summary94B["Pairs"],52],
SameQ[summary94B["Worlds"],104],
SameQ[summary94B["ReferenceRelationsCorrect"],52],
SameQ[summary94B["MixedContextWorlds"],104],
SameQ[summary94B["CanonicalCaseExactlyBase"],104],
SameQ[summary94B["ContractionCountCorrect"],104],
SameQ[summary94B["ProtectedNodesPreserved"],104],
SameQ[summary94B["ValidGlobalVectors"],104],
SameQ[summary94B["ValidRoleVectors"],104],
SameQ[summary94B["TerminatedNaturally"],104],
SameQ[summary94B["HitSafetyCap"],0],
SameQ[Length[folds94B],17],SameQ[Length[candidateResults94B],27]];
roleAwareImproved94B=And[
bestRoleAware94B["Accuracy"]>bestGlobal94B["Accuracy"],
bestRoleAware94B["WorstFoldAccuracy"]>=bestGlobal94B["WorstFoldAccuracy"]];
developmentCriterionPassed94B=And[TrueQ[testValidityPassed94B],
MemberQ[{"Role30","Combined57"},bestCandidate94B["Representation"]],
bestCandidate94B["Accuracy"]>=0.95,
bestCandidate94B["WorstFoldAccuracy"]>=0.8,
SameQ[bestCandidate94B["ZeroScores"],0]];

Column[{Dataset[{summary94B}],
Dataset[KeyDrop[#,"FoldResults"]&/@Take[candidateRanking94B,UpTo[12]]],
Dataset[{<|"BestGlobal"->KeyDrop[bestGlobal94B,"FoldResults"],
"BestRoleAware"->KeyDrop[bestRoleAware94B,"FoldResults"],
"RoleAwareImproved"->roleAwareImproved94B,
"DevelopmentCriterionPassed"->developmentCriterionPassed94B|>}]}]
'''.strip()

audit = r'''
modelHashAfter94B=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94B=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94B=Hash[Normal[baseDecoderRaw94B],"SHA256","HexString"];
pairDecoderObjectHashAfter94B=Hash[Normal[pairDecoderRaw94B],"SHA256","HexString"];
coreHashAfter94B=Hash[CoreDefinitionBundle94B[],"SHA256","HexString"];
canonicalizerHashAfter94B=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter94B=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94B=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94B=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94B=Hash[
PairRuntimeDefinitionBundle94B[],"SHA256","HexString"];
testDefinitionHashAfter94B=Hash[TestDefinitionBundle94B[],"SHA256","HexString"];
readoutDefinitionHashAfter94B=Hash[ReadoutDefinitionBundle94B[],
"SHA256","HexString"];
fileHashesAfter94B=FileSHA256Hex94B/@requiredFiles94B;

integrityPassed94B=And[
SameQ[modelHashBefore94B,modelHashAfter94B],
SameQ[k33ObjectHashBefore94B,k33ObjectHashAfter94B],
SameQ[baseDecoderObjectHashBefore94B,baseDecoderObjectHashAfter94B],
SameQ[pairDecoderObjectHashBefore94B,pairDecoderObjectHashAfter94B],
SameQ[coreHashBefore94B,coreHashAfter94B],
SameQ[canonicalizerHashBefore94B,canonicalizerHashAfter94B],
SameQ[interventionHashBefore94B,interventionHashAfter94B],
SameQ[topologyPrimitiveHashBefore94B,topologyPrimitiveHashAfter94B],
SameQ[baseRuntimeDefinitionHashBefore94B,baseRuntimeDefinitionHashAfter94B],
SameQ[pairRuntimeDefinitionHashBefore94B,pairRuntimeDefinitionHashAfter94B],
SameQ[testDefinitionHashBefore94B,testDefinitionHashAfter94B],
SameQ[readoutDefinitionHashBefore94B,readoutDefinitionHashAfter94B],
SameQ[fileHashesBefore94B,fileHashesAfter94B]];

developmentArtifact94B=<|"Stage"->"S94B",
"DevelopmentOnly"->True,"SourceS94LabelsAlreadyRevealed"->True,
"ProtocolHash"->protocolHash94B,
"TestDefinitionHash"->testDefinitionHashAfter94B,
"ReadoutDefinitionHash"->readoutDefinitionHashAfter94B,
"Rows"->Map[KeyTake[#,{"Topology","TopologyIndex","NoisePhase","Depth",
"Answer","GlobalDifference","RoleDifference","CombinedDifference"}]&,
developmentPairs94B]|>;
developmentArtifactObjectHash94B=Hash[Normal[developmentArtifact94B],
"SHA256","HexString"];
developmentArtifactExportResult94B=Quiet@Check[
Export[developmentPairsPath94B,developmentArtifact94B,"WXF"],$Failed];
developmentArtifactExported94B=StringQ[developmentArtifactExportResult94B]&&
FileExistsQ[developmentPairsPath94B]&&FileByteCount[developmentPairsPath94B]>0;
developmentArtifactFileHash94B=If[TrueQ[developmentArtifactExported94B],
FileSHA256Hex94B[developmentPairsPath94B],Missing[]];

compactRanking94B=Map[KeyDrop[#,"FoldResults"]&,
Take[candidateRanking94B,UpTo[12]]];
resultPayload94B=<|"Stage"->"S94B",
"Name"->"RoleAwareReadoutDevelopment","DevelopmentOnly"->True,
"BlindTest"->False,"UsesRevealedS94Labels"->True,
"MayClaimBlindResult"->False,"ProtocolHash"->protocolHash94B,
"Scenarios"->summary94B["Scenarios"],"Pairs"->summary94B["Pairs"],
"Worlds"->summary94B["Worlds"],
"OldFrozenPairCorrect"->summary94B["OldFrozenPairCorrect"],
"OldFrozenUnknownPredictions"->summary94B["OldFrozenUnknownPredictions"],
"BestGlobal"->KeyDrop[bestGlobal94B,"FoldResults"],
"BestRoleAware"->KeyDrop[bestRoleAware94B,"FoldResults"],
"BestOverall"->KeyDrop[bestCandidate94B,"FoldResults"],
"CandidateRankingTop12"->compactRanking94B,
"RoleAwareImproved"->roleAwareImproved94B,
"DevelopmentCriterionPassed"->developmentCriterionPassed94B,
"TestValidityPassed"->testValidityPassed94B,
"IntegrityPassed"->integrityPassed94B,
"DevelopmentArtifactExported"->developmentArtifactExported94B,
"DevelopmentArtifactObjectHash"->developmentArtifactObjectHash94B,
"DevelopmentArtifactFileHash"->developmentArtifactFileHash94B,
"CandidateFrozen"->False,"DynamicModulusSelected"->False,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94B,modelHashAfter94B],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94B,
pairDecoderObjectHashAfter94B],
"CoreChanged"->!SameQ[coreHashBefore94B,coreHashAfter94B],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94B,
canonicalizerHashAfter94B],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94B,
interventionHashAfter94B],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94B,coreHashAfter94B],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94B,coreHashAfter94B],
"TotalTraceSeconds"->summary94B["TotalTraceSeconds"],
"Outcome"->Which[!TrueQ[testValidityPassed94B]||!TrueQ[integrityPassed94B]||
!TrueQ[developmentArtifactExported94B],"S94B_INVALID_DEVELOPMENT_RUN",
TrueQ[developmentCriterionPassed94B],
"S94B_ROLE_AWARE_DEVELOPMENT_PASS_READY_FOR_CONFIRMATION",
TrueQ[roleAwareImproved94B],"S94B_ROLE_AWARE_PARTIAL_IMPROVEMENT",
True,"S94B_NO_CONTEXT_INVARIANT_READOUT_FOUND"],
"SuggestedNextStage"->Which[TrueQ[developmentCriterionPassed94B],
"S94C_INDEPENDENT_DEVELOPMENT_CONFIRMATION_BEFORE_FREEZE",
TrueQ[roleAwareImproved94B],"S94C_EXPAND_ROLE_AWARE_DEVELOPMENT_CONTEXTS",
True,"S94C_REDESIGN_QUERY_ROLE_REPRESENTATION"]|>;
resultHash94B=Hash[Normal[resultPayload94B],"SHA256","HexString"];
certificate94B=Append[resultPayload94B,"ResultHash"->resultHash94B];
certificateExportResult94B=Quiet@Check[
Export[resultCertificatePath94B,certificate94B,"RawJSON"],$Failed];
certificateExported94B=StringQ[certificateExportResult94B]&&
FileExistsQ[resultCertificatePath94B]&&FileByteCount[resultCertificatePath94B]>0;

Column[{Dataset[{certificate94B}],Dataset[{<|
"CertificateExported"->certificateExported94B,
"CertificatePath"->resultCertificatePath94B,
"CertificateBytes"->If[FileExistsQ[resultCertificatePath94B],
FileByteCount[resultCertificatePath94B],0],
"DevelopmentPairsExported"->developmentArtifactExported94B,
"DevelopmentPairsPath"->developmentPairsPath94B,
"CoreChanged"->certificate94B["CoreChanged"],
"Outcome"->certificate94B["Outcome"]|>}]}]
'''.strip()

cells = [core, locks, definitions, evaluation, audit]
WL.write_text(
    "\n\n".join(
        f"(* S94B CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells, 1)
    )
    + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL.write_text(
    "\n\n".join(
        f"(* S94B PREFLIGHT CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells[:3], 1)
    )
    + "\n",
    encoding="utf-8",
)

NB.write_text(
    json.dumps(
        notebook(
            cells,
            "TCCT S94B — Role-Aware Antisymmetric Readout Development",
            "Development-only stage using revealed S94 labels. Run all cells once. "
            "No frozen candidate is overwritten or automatically selected.",
        ),
        ensure_ascii=False,
        indent=1,
    )
    + "\n",
    encoding="utf-8",
)
PREFLIGHT_NB.write_text(
    json.dumps(
        notebook(
            cells[:3],
            "TCCT S94B — Preflight",
            "Locked-input and source-definition check only; no development worlds are generated.",
        ),
        ensure_ascii=False,
        indent=1,
    )
    + "\n",
    encoding="utf-8",
)

LAUNCHER.write_text(
    "@echo off\n"
    "chcp 65001 >nul\n"
    'start "" "http://localhost:8888/lab/tree/TCCT_S94B_RoleAwareReadoutDevelopment.ipynb"\n'
    "exit /b 0\n",
    encoding="utf-8",
)

precommit = {
    "Stage": "S94B",
    "Name": "RoleAwareReadoutDevelopment",
    "DevelopmentOnly": True,
    "BlindTest": False,
    "UsesRevealedS94Labels": True,
    "CoreMechanismChanged": False,
    "CandidateFrozen": False,
    "DynamicModulusSelected": False,
    "ExpectedScenarios": 4,
    "ExpectedPairs": 52,
    "ExpectedWorlds": 104,
    "ExpectedCandidateSpecifications": 27,
    "ExpectedValidationFolds": 17,
    "ProtocolHash": "376cbf7e8a5d1fe039dd64323f1cca4be522e48d34e4a5248872082b4362e9af",
    "TestDefinitionHash": "1ea0f8b521a6a1971847af15a0b427bc74665d0cca9cbc383c5fa8c36b6fe01f",
    "ReadoutDefinitionHash": "07bb48323032cd124fe48ad490e866732281174efe254519f087fc5cd80e1704",
    "DynamicPreflightPassed": True,
    "FullSourceParsePassed": True,
    "DevelopmentCasesGeneratedDuringPreflight": False,
    "CandidateResultsGeneratedDuringPreflight": False,
    "SmokeTestDepth": 3,
    "SmokeTestPassed": True,
    "SmokeTestIncludedInDevelopmentData": False,
    "WolframSourceSHA256": sha256(WL),
    "NotebookSHA256": sha256(NB),
    "PreflightSourceSHA256": sha256(PREFLIGHT_WL),
    "PreflightNotebookSHA256": sha256(PREFLIGHT_NB),
}
PRECOMMIT.write_text(
    json.dumps(precommit, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path)
