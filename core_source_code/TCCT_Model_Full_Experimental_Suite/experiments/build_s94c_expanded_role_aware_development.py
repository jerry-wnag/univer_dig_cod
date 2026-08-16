"""Build TCCT S94C expanded role-aware readout development benchmark.

The generated experiment is development-only.  It preserves the frozen TCCT
core and all previously frozen candidates, expands the mixed-context matrix,
and evaluates richer outer readouts under grouped cross-validation.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S94B_WL = ROOT / "TCCT_S94B_RoleAwareReadoutDevelopment.wl"
WL = ROOT / "TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.wl"
NB = ROOT / "TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94C_ExpandedRoleAwareReadoutDevelopment_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94C_ExpandedRoleAwareReadoutDevelopment_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94C_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94C_Precommit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook(code_cells: list[str], title: str, note: str) -> dict:
    cells: list[dict] = [
        {
            "cell_type": "markdown",
            "id": "s94c-introduction",
            "metadata": {},
            "source": [f"# {title}\n", "\n", f"{note}\n"],
        }
    ]
    for index, code in enumerate(code_cells, 1):
        cells.append(
            {
                "cell_type": "code",
                "id": f"s94c-cell-{index}",
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


if not S94B_WL.exists():
    raise SystemExit(f"Missing locked source: {S94B_WL}")

source94b = S94B_WL.read_text(encoding="utf-8")
parts = re.split(r"\(\* S94B CELL \d+ \*\)\r?\n", source94b)
if len(parts) != 6:
    raise SystemExit(f"Expected five S94B cells, found {len(parts) - 1}")

# Cell 1 is the historical core definition block.  Reuse it byte-for-byte.
core = parts[1].strip()

# Cell 2 is the locked-input loader.  Rename only stage-local symbols and then
# add immutable S94B evidence to the input lock set.
locks = parts[2].replace("94B", "94C").replace("S94B", "S94C")
locks = locks.replace(
    'expectedS94AAuditFileHash94C=\n"ab0f6524f8cb8ee8edb915e132044734f8db8ce20758c09f26ded9de01571571";',
    'expectedS94AAuditFileHash94C=\n'
    '"ab0f6524f8cb8ee8edb915e132044734f8db8ce20758c09f26ded9de01571571";\n'
    'expectedS94BResultHash94C=\n'
    '"dc3de125d10d871c62857f051bbff204881512f63286bc0f3882791514724f9d";\n'
    'expectedS94BCertificateFileHash94C=\n'
    '"6b3c44566c80c88495f2a322a0763b7a188383445b554eeffc30e7fa90b4e461f";\n'
    'expectedS94BArtifactFileHash94C=\n'
    '"998fa0de0fd8e14cf9c797287f64c824f7a435c2aa3c8b0b80b0a920075dc3e4";',
)
locks = locks.replace(
    's94aAuditPath94C="E:/engine_wolf/TCCT_S94A_ModulusFeasibilityAudit.json";\n'
    'developmentPairsPath94C="E:/engine_wolf/TCCT_S94C_RoleAwareDevelopmentPairs.wxf";\n'
    'resultCertificatePath94C="E:/engine_wolf/TCCT_S94C_RoleAwareReadoutDevelopment.json";',
    's94aAuditPath94C="E:/engine_wolf/TCCT_S94A_ModulusFeasibilityAudit.json";\n'
    's94bCertificatePath94C="E:/engine_wolf/TCCT_S94B_RoleAwareReadoutDevelopment.json";\n'
    's94bArtifactPath94C="E:/engine_wolf/TCCT_S94B_RoleAwareDevelopmentPairs.wxf";\n'
    'developmentPairsPath94C="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareDevelopmentPairs.wxf";\n'
    'resultCertificatePath94C="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.json";',
)
locks = locks.replace(
    'baseCandidatePath94C,pairRuntimePath94C,pairCandidatePath94C,s94aAuditPath94C};',
    'baseCandidatePath94C,pairRuntimePath94C,pairCandidatePath94C,s94aAuditPath94C,\n'
    's94bCertificatePath94C,s94bArtifactPath94C};',
)
locks = locks.replace(
    's94aAudit94C=Quiet@Check[Import[s94aAuditPath94C,"RawJSON"],$Failed];',
    's94aAudit94C=Quiet@Check[Import[s94aAuditPath94C,"RawJSON"],$Failed];\n'
    's94bCertificate94C=Quiet@Check[Import[s94bCertificatePath94C,"RawJSON"],$Failed];',
)
locks = locks.replace(
    'SameQ[s94aAudit94C["CandidateHash"],expectedPairCandidateHash94C]];',
    'SameQ[s94aAudit94C["CandidateHash"],expectedPairCandidateHash94C],\n'
    'SameQ[fileHashesBefore94C[[7]],expectedS94BCertificateFileHash94C],\n'
    'SameQ[fileHashesBefore94C[[8]],expectedS94BArtifactFileHash94C],\n'
    'AssociationQ[s94bCertificate94C],\n'
    'SameQ[s94bCertificate94C["ResultHash"],expectedS94BResultHash94C],\n'
    'SameQ[s94bCertificate94C["Outcome"],"S94B_ROLE_AWARE_PARTIAL_IMPROVEMENT"],\n'
    'TrueQ[s94bCertificate94C["TestValidityPassed"]],\n'
    'TrueQ[s94bCertificate94C["IntegrityPassed"]]];',
)
locks = locks.replace(
    '"Stage"->"S94C","Name"->"RoleAwareReadoutDevelopment",',
    '"Stage"->"S94C","Name"->"ExpandedRoleAwareReadoutDevelopment",',
)
locks = locks.replace(
    '"S94AAuditLocked"->SameQ[fileHashesBefore94C[[6]],expectedS94AAuditFileHash94C],',
    '"S94AAuditLocked"->SameQ[fileHashesBefore94C[[6]],expectedS94AAuditFileHash94C],\n'
    '"S94BResultLocked"->SameQ[fileHashesBefore94C[[7]],expectedS94BCertificateFileHash94C],',
)

required_lock_fragments = [
    "expectedS94BResultHash94C",
    "s94bCertificatePath94C",
    "fileHashesBefore94C[[8]]",
    "ExpandedRoleAwareReadoutDevelopment",
]
if not all(fragment in locks for fragment in required_lock_fragments):
    raise SystemExit("S94C lock transformation failed")


definitions = r'''
ClearAll[ContextAction94C,T94C,Case94C,ReferenceAction94C,NodeRole94C,
EncodePair94C,DiamondAfterDoubleAfterHierarchical94C,
HierarchicalAfterDiamondAfterDouble94C,DiamondAfterHierarchicalAfterDouble94C,
DoubleAfterHierarchicalAfterDiamond94C,TopologyTransform94C,
ExpectedContractions94C,RoleStatsTwelve94C,RoleMomentVector94C,
RoleInteractionVector94C,RoleEnhancedVector94C,RoleHistogramStats94C,
RoleHistogramVector94C,PrepareWorld94C,PrepareScenario94C,
RepresentationVector94C,FitAntisymmetricReadout94C,
ScoreAntisymmetricReadout94C,FoldMemberQ94C,EvaluateCandidate94C,
RepresentationAudit94C,AxisSummary94C,TestDefinitionBundle94C,
ReadoutDefinitionBundle94C];

contextPatterns94C={"AlternatingEven","AlternatingOdd","BlockHalf","TernarySparse"};
ContextAction94C[i_Integer,pattern_String,branchCount_Integer]:=Switch[pattern,
"AlternatingEven",If[EvenQ[i],"Continue","Stop"],
"AlternatingOdd",If[OddQ[i],"Continue","Stop"],
"BlockHalf",If[i<=Ceiling[branchCount/2],"Continue","Stop"],
"TernarySparse",If[Mod[i,3]===0,"Continue","Stop"],
_,"Undefined"];

T94C[depth_Integer,target_String,answer_Integer,seed_Integer,
branchCount_Integer,contextPattern_String]:=Module[
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
branchAction=If[i===answer,target,ContextAction94C[i,contextPattern,branchCount]];
perm=If[branchAction==="Continue",
{DirectedEdge[m,c[[i]]],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],
A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];
{{Union[e],q,K,v,c,f},answer}];

Case94C[depth_Integer,answer_Integer,target_String,topologyIndex_Integer,
contextIndex_Integer,contextPattern_String]:=T94C[depth,target,answer,
94300000+10000 topologyIndex+1000 contextIndex+10 depth,13,contextPattern];

ReferenceAction94C[c_List]:=Module[{x=c[[1]],answer=c[[2]],branchCount,e,m,
safe,u,dummy,correct,wrong,continueEdges,stopEdges},
branchCount=Length[x[[6]]];e=x[[1]];m=x[[6,answer]];safe=m+1;u=m+2;
dummy=m+3;correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,branchCount]]];
continueEdges={DirectedEdge[m,correct],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]};
stopEdges={DirectedEdge[m,wrong],DirectedEdge[safe,correct],DirectedEdge[u,dummy]};
Which[And@@(MemberQ[e,#]&/@continueEdges),"Continue",
And@@(MemberQ[e,#]&/@stopEdges),"Stop",True,"Undefined"]];

NodeRole94C[originalNode_,case_List,answer_Integer]:=Module[
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

EncodePair94C[pair_List]:=Module[{encoded},
encoded=First@EncodeRows75[{<|"Grammar"->"S94CExpandedRoleAwareDevelopment",
"Depth"->0,"Answer"->0,"Target"->"Unlabeled","StatePairs"->{pair}|>},
frozenCandidate86E["EncoderParams"],frozenCandidate86E["K"]];
First[encoded["Codes"]]];

DiamondAfterDoubleAfterHierarchical94C[c_List]:=
DiamondIn72[DoubleDiamondIn79[HierarchicalDiamondIn80[c]]];
HierarchicalAfterDiamondAfterDouble94C[c_List]:=
HierarchicalDiamondIn80[DiamondIn72[DoubleDiamondIn79[c]]];
DiamondAfterHierarchicalAfterDouble94C[c_List]:=
DiamondIn72[HierarchicalDiamondIn80[DoubleDiamondIn79[c]]];
DoubleAfterHierarchicalAfterDiamond94C[c_List]:=
DoubleDiamondIn79[HierarchicalDiamondIn80[DiamondIn72[c]]];
TopologyTransform94C[topology_String,c_List]:=Switch[topology,
"DiamondAfterDoubleAfterHierarchical",DiamondAfterDoubleAfterHierarchical94C[c],
"HierarchicalAfterDiamondAfterDouble",HierarchicalAfterDiamondAfterDouble94C[c],
"DiamondAfterHierarchicalAfterDouble",DiamondAfterHierarchicalAfterDouble94C[c],
"DoubleAfterHierarchicalAfterDiamond",DoubleAfterHierarchicalAfterDiamond94C[c],
_,$Failed];
ExpectedContractions94C[baseCase_List]:=6 DecisionIncomingEdgeCount79B[baseCase];

roleOrder94C={"QueriedDecision","QueriedMediatorSource",
"QueriedCorrectDestination","QueriedWrongDestination","QueriedDummyDestination"};
interactionRolePairs94C={{1,2},{1,3},{1,4},{3,4},{3,5},{4,5}};
RoleStatsTwelve94C[observations_List,role_String]:=Module[{selected,codes,a,b,d},
selected=Select[observations,SameQ[Lookup[#,"Role"],role]&];
codes=Lookup[selected,"Code",{}];
If[Length[codes]===0,Return[ConstantArray[0,12]]];
a=codes[[All,1]];b=codes[[All,2]];d=a-b;
{Length[codes],Total[a],Total[b],Total[a^2],Total[b^2],Total[a b],
Total[d],Total[Abs[d]],Total[d^2],Max[a],Max[b],Max[Abs[d]]}];
RoleMomentVector94C[observations_List]:=Flatten[
RoleStatsTwelve94C[observations,#]&/@roleOrder94C];
RoleInteractionVector94C[observations_List]:=Module[{stats},
stats=RoleStatsTwelve94C[observations,#]&/@roleOrder94C;
Flatten[(stats[[#[[1]]]] stats[[#[[2]]]])&/@interactionRolePairs94C]];
RoleEnhancedVector94C[observations_List]:=Join[
RoleMomentVector94C[observations],RoleInteractionVector94C[observations]];
RoleHistogramStats94C[observations_List,role_String]:=Module[
{selected,codes,a,b,d},
selected=Select[observations,SameQ[Lookup[#,"Role"],role]&];
codes=Lookup[selected,"Code",{}];
If[Length[codes]===0,Return[ConstantArray[0,99]]];
a=codes[[All,1]];b=codes[[All,2]];d=1+Mod[a-b,33];
Join[BinCounts[a,{0.5,33.5,1}],BinCounts[b,{0.5,33.5,1}],
BinCounts[d,{0.5,33.5,1}]]];
RoleHistogramVector94C[observations_List]:=Flatten[
RoleHistogramStats94C[observations,#]&/@roleOrder94C];

PrepareWorld94C[topology_String,topologyIndex_Integer,contextPattern_String,
contextIndex_Integer,depth_Integer,target_String,answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,expectedContractions,
traceSeconds,trace,levels,pack,vertexList,packedNodes,observations,
queryObservations,originalNode,pair,roleInfo,globalVector,roleMomentVector,
roleEnhancedVector,roleHistogramVector,nonQueryActions},
baseCase=Case94C[depth,answer,target,topologyIndex,contextIndex,contextPattern];
topologyCase=TopologyTransform94C[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
expectedContractions=ExpectedContractions94C[baseCase];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole94C[originalNode,canonicalCase,answer];
<|"Role"->roleInfo["Role"],
"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair94C[pair]|>],packedNodes];
queryObservations=Select[observations,TrueQ[Lookup[#,"QueryBranchRelated",False]]&];
globalVector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
roleMomentVector=RoleMomentVector94C[queryObservations];
roleEnhancedVector=RoleEnhancedVector94C[queryObservations];
roleHistogramVector=RoleHistogramVector94C[queryObservations];
nonQueryActions=ContextAction94C[#,contextPattern,13]&/@DeleteCases[Range[13],answer];
<|"Topology"->topology,"TopologyIndex"->topologyIndex,
"ContextPattern"->contextPattern,"ContextIndex"->contextIndex,
"Depth"->depth,"Answer"->answer,"Target"->target,
"ReferenceAction"->ReferenceAction94C[canonicalCase],
"NonQueryContinueBranches"->Count[nonQueryActions,"Continue"],
"NonQueryStopBranches"->Count[nonQueryActions,"Stop"],
"GlobalVector"->globalVector,"RoleMomentVector"->roleMomentVector,
"RoleEnhancedVector"->roleEnhancedVector,
"RoleHistogramVector"->roleHistogramVector,
"QueryObservationCount"->Length[queryObservations],
"QueryRoleCounts"->AssociationMap[
Count[Lookup[queryObservations,"Role"],#]&,roleOrder94C],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"Contractions"->canonicalization["Contractions"],
"ExpectedContractions"->expectedContractions,
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],expectedContractions],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"TraceSeconds"->traceSeconds|>];

PrepareScenario94C[topology_String,topologyIndex_Integer,contextPattern_String,
contextIndex_Integer,depth_Integer]:=Module[{continueWorlds,stopWorlds,pairs,key},
key=StringRiffle[{topology,contextPattern,ToString[depth]},"|"];
continueWorlds=Table[PrepareWorld94C[topology,topologyIndex,contextPattern,
contextIndex,depth,"Continue",answer],{answer,13}];
stopWorlds=Table[PrepareWorld94C[topology,topologyIndex,contextPattern,
contextIndex,depth,"Stop",answer],{answer,13}];
pairs=MapThread[Function[{continue,stop},<|
"ScenarioKey"->key,"Topology"->topology,"TopologyIndex"->topologyIndex,
"ContextPattern"->contextPattern,"ContextIndex"->contextIndex,
"Depth"->depth,"Answer"->continue["Answer"],
"ContinueWorld"->continue,"StopWorld"->stop,
"GlobalDifference"->continue["GlobalVector"]-stop["GlobalVector"],
"RoleMomentDifference"->continue["RoleMomentVector"]-stop["RoleMomentVector"],
"RoleEnhancedDifference"->continue["RoleEnhancedVector"]-stop["RoleEnhancedVector"],
"RoleHistogramDifference"->continue["RoleHistogramVector"]-stop["RoleHistogramVector"],
"CombinedDifference"->Join[
continue["GlobalVector"]-stop["GlobalVector"],
continue["RoleEnhancedVector"]-stop["RoleEnhancedVector"],
continue["RoleHistogramVector"]-stop["RoleHistogramVector"]],
"ReferenceRelationCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]]|>],{continueWorlds,stopWorlds}];
<|"ScenarioKey"->key,"Topology"->topology,"TopologyIndex"->topologyIndex,
"ContextPattern"->contextPattern,"ContextIndex"->contextIndex,
"Depth"->depth,"Pairs"->pairs,"ContinueWorlds"->continueWorlds,
"StopWorlds"->stopWorlds|>];

RepresentationVector94C[row_Association,representation_String]:=Switch[representation,
"Global27",row["GlobalDifference"],
"RoleMoment60",row["RoleMomentDifference"],
"RoleEnhanced132",row["RoleEnhancedDifference"],
"RoleHistogram495",row["RoleHistogramDifference"],
"Combined654",row["CombinedDifference"],_,$Failed];

FitAntisymmetricReadout94C[rows_List,representation_String,
family_String,lambda_?NumericQ]:=Module[
{differences,scale,z,mu,covariance,variance,weights},
differences=RepresentationVector94C[#,representation]&/@rows;
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
ScoreAntisymmetricReadout94C[model_Association,difference_List]:=
N[Total[model["Weights"] (difference/model["Scale"])]];

FoldMemberQ94C[row_Association,fold_Association]:=Switch[fold["Axis"],
"Topology",SameQ[row["Topology"],fold["Heldout"]],
"ContextPattern",SameQ[row["ContextPattern"],fold["Heldout"]],
"Depth",SameQ[row["Depth"],fold["Heldout"]],
"Answer",SameQ[row["Answer"],fold["Heldout"]],
"Scenario",SameQ[row["ScenarioKey"],fold["Heldout"]],_,False];
EvaluateCandidate94C[rows_List,folds_List,spec_Association]:=Module[
{foldRows},foldRows=Map[Function[fold,Module[{train,test,model,scores},
test=Select[rows,TrueQ[FoldMemberQ94C[#,fold]]&];
train=Select[rows,!TrueQ[FoldMemberQ94C[#,fold]]&];
model=FitAntisymmetricReadout94C[train,spec["Representation"],
spec["Family"],spec["Lambda"]];
scores=If[AssociationQ[model],ScoreAntisymmetricReadout94C[model,
RepresentationVector94C[#,spec["Representation"]]]&/@test,{}];
<|"Axis"->fold["Axis"],"Heldout"->ToString[fold["Heldout"]],
"Cases"->Length[test],"Correct"->Count[scores,x_/;x>0],
"ZeroScores"->Count[scores,x_/;Abs[x]<10^-12],
"Accuracy"->If[Length[test]>0,N[Count[scores,x_/;x>0]/Length[test]],0.],
"MinimumMargin"->If[Length[scores]>0,Min[scores],-Infinity]|>]],folds];
Join[spec,<|"Folds"->Length[foldRows],"Cases"->Total@Lookup[foldRows,"Cases"],
"Correct"->Total@Lookup[foldRows,"Correct"],
"Accuracy"->N[Total@Lookup[foldRows,"Correct"]/Total@Lookup[foldRows,"Cases"]],
"WorstFoldAccuracy"->Min@Lookup[foldRows,"Accuracy"],
"ZeroScores"->Total@Lookup[foldRows,"ZeroScores"],
"MinimumMargin"->Min@Lookup[foldRows,"MinimumMargin"],
"FoldResults"->foldRows|>]];

RepresentationAudit94C[rows_List,representation_String]:=Module[
{vectors,unique,oppositeConflicts},
vectors=RepresentationVector94C[#,representation]&/@rows;
unique=DeleteDuplicates[vectors];oppositeConflicts=Intersection[unique,-unique];
<|"Representation"->representation,"Dimension"->Length[First[vectors]],
"ZeroVectors"->Count[vectors,ConstantArray[0,Length[First[vectors]]]],
"UniqueVectors"->Length[unique],
"AntisymmetricAliasConflicts"->Length[oppositeConflicts]|>];
AxisSummary94C[foldRows_List]:=Map[Function[axis,Module[{rows},
rows=Select[foldRows,SameQ[Lookup[#,"Axis"],axis]&];
<|"Axis"->axis,"Folds"->Length[rows],"Cases"->Total@Lookup[rows,"Cases"],
"Correct"->Total@Lookup[rows,"Correct"],
"Accuracy"->N[Total@Lookup[rows,"Correct"]/Total@Lookup[rows,"Cases"]],
"WorstFoldAccuracy"->Min@Lookup[rows,"Accuracy"]|>]],
{"Topology","ContextPattern","Depth","Answer","Scenario"}];

TestDefinitionBundle94C[]:={DownValues[ContextAction94C],DownValues[T94C],
DownValues[Case94C],DownValues[ReferenceAction94C],DownValues[NodeRole94C],
DownValues[EncodePair94C],DownValues[DiamondAfterDoubleAfterHierarchical94C],
DownValues[HierarchicalAfterDiamondAfterDouble94C],
DownValues[DiamondAfterHierarchicalAfterDouble94C],
DownValues[DoubleAfterHierarchicalAfterDiamond94C],DownValues[TopologyTransform94C],
DownValues[ExpectedContractions94C],DownValues[RoleStatsTwelve94C],
DownValues[RoleMomentVector94C],DownValues[RoleInteractionVector94C],
DownValues[RoleEnhancedVector94C],DownValues[RoleHistogramStats94C],
DownValues[RoleHistogramVector94C],DownValues[PrepareWorld94C],
DownValues[PrepareScenario94C]};
ReadoutDefinitionBundle94C[]:={DownValues[RepresentationVector94C],
DownValues[FitAntisymmetricReadout94C],DownValues[ScoreAntisymmetricReadout94C],
DownValues[FoldMemberQ94C],DownValues[EvaluateCandidate94C],
DownValues[RepresentationAudit94C],DownValues[AxisSummary94C]};

testDefinitionHashBefore94C=Hash[TestDefinitionBundle94C[],"SHA256","HexString"];
readoutDefinitionHashBefore94C=Hash[ReadoutDefinitionBundle94C[],"SHA256","HexString"];
developmentTopologies94C={"DiamondAfterDoubleAfterHierarchical",
"HierarchicalAfterDiamondAfterDouble","DiamondAfterHierarchicalAfterDouble",
"DoubleAfterHierarchicalAfterDiamond"};
developmentDepths94C={17,31};
protocol94C=<|"Stage"->"S94C","Name"->"ExpandedRoleAwareReadoutDevelopment",
"DevelopmentOnly"->True,"BlindTest"->False,
"SourceS94LabelsAlreadyRevealed"->True,"CoreMechanismChanged"->False,
"NewOuterRepresentations"->{"RoleMoment60","RoleEnhanced132",
"RoleHistogram495","Combined654"},
"AntisymmetryConstraint"->"Score[x,y]==-Score[y,x]",
"BranchCount"->13,"Depths"->developmentDepths94C,
"Topologies"->developmentTopologies94C,"ContextPatterns"->contextPatterns94C,
"TopologyContextDepthCrossed"->True,"ExpectedScenarios"->32,
"ExpectedPairs"->416,"ExpectedWorlds"->832,
"Representations"->{"Global27","RoleMoment60","RoleEnhanced132",
"RoleHistogram495","Combined654"},
"CandidateFamilies"->{"Centroid","DiagonalRidge","FullRidgeRestricted"},
"ValidationAxes"->{"Topology","ContextPattern","Depth","Answer","Scenario"},
"DevelopmentPassAccuracy"->0.95,"DevelopmentPassWorstFoldAccuracy"->0.8,
"PriorS94BAccuracy"->0.8461538461538461,"PriorS94BWorstFoldAccuracy"->0.5,
"CandidateFrozenAtThisStage"->False|>;
protocolHash94C=Hash[Normal[protocol94C],"SHA256","HexString"];
Dataset[{Join[protocol94C,<|"ProtocolHash"->protocolHash94C,
"TestDefinitionHash"->testDefinitionHashBefore94C,
"ReadoutDefinitionHash"->readoutDefinitionHashBefore94C|>]}]
'''.strip()


evaluation = r'''
developmentScenarios94C=Flatten[Table[
PrepareScenario94C[topology,topologyIndex,contextPattern,contextIndex,depth],
{topologyIndex,Length[developmentTopologies94C]},
{topology,{developmentTopologies94C[[topologyIndex]]}},
{contextIndex,Length[contextPatterns94C]},
{contextPattern,{contextPatterns94C[[contextIndex]]}},
{depth,developmentDepths94C}],4];
developmentPairs94C=Flatten[Lookup[developmentScenarios94C,"Pairs"],1];
developmentWorlds94C=Join[
Flatten[Lookup[developmentScenarios94C,"ContinueWorlds"],1],
Flatten[Lookup[developmentScenarios94C,"StopWorlds"],1]];

folds94C=Join[
Map[<|"Axis"->"Topology","Heldout"->#|>&,developmentTopologies94C],
Map[<|"Axis"->"ContextPattern","Heldout"->#|>&,contextPatterns94C],
Map[<|"Axis"->"Depth","Heldout"->#|>&,developmentDepths94C],
Map[<|"Axis"->"Answer","Heldout"->#|>&,Range[13]],
Map[<|"Axis"->"Scenario","Heldout"->#|>&,
Lookup[developmentScenarios94C,"ScenarioKey"]]];
representations94C={"Global27","RoleMoment60","RoleEnhanced132",
"RoleHistogram495","Combined654"};
candidateSpecs94C=Join[
Map[<|"Representation"->#,"Family"->"Centroid","Lambda"->1.|>&,
representations94C],
Flatten[Table[<|"Representation"->representation,"Family"->"DiagonalRidge",
"Lambda"->lambda|>,{representation,representations94C},
{lambda,{0.1,1.,10.,100.}}],Infinity],
Flatten[Table[<|"Representation"->representation,"Family"->"FullRidge",
"Lambda"->lambda|>,{representation,{"Global27","RoleMoment60","RoleEnhanced132"}},
{lambda,{1.,10.,100.}}],Infinity]];
candidateResults94C=Map[
EvaluateCandidate94C[developmentPairs94C,folds94C,#]&,candidateSpecs94C];
candidateRanking94C=SortBy[candidateResults94C,{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&,
(-Lookup[#,"MinimumMargin"])&}];
bestCandidate94C=First[candidateRanking94C];
bestGlobal94C=First@SortBy[Select[candidateRanking94C,
SameQ[Lookup[#,"Representation"],"Global27"]&],{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&}];
bestRoleAware94C=First@SortBy[Select[candidateRanking94C,
!SameQ[Lookup[#,"Representation"],"Global27"]&],{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&}];

representationAudits94C=RepresentationAudit94C[developmentPairs94C,#]&/@
representations94C;
bestRepresentationAudit94C=First@Select[representationAudits94C,
SameQ[Lookup[#,"Representation"],bestCandidate94C["Representation"]]&];
bestFullModel94C=FitAntisymmetricReadout94C[developmentPairs94C,
bestCandidate94C["Representation"],bestCandidate94C["Family"],
bestCandidate94C["Lambda"]];
bestFullScores94C=ScoreAntisymmetricReadout94C[bestFullModel94C,
RepresentationVector94C[#,bestCandidate94C["Representation"]]]&/@
developmentPairs94C;
bestTrainingAccuracy94C=N[Count[bestFullScores94C,x_/;x>0]/Length[bestFullScores94C]];
bestWorstFolds94C=Take[SortBy[bestCandidate94C["FoldResults"],{
Lookup[#,"Accuracy"]&,Lookup[#,"MinimumMargin"]&}],UpTo[15]];
bestAxisSummary94C=AxisSummary94C[bestCandidate94C["FoldResults"]];

summary94C=<|"Scenarios"->Length[developmentScenarios94C],
"Pairs"->Length[developmentPairs94C],"Worlds"->Length[developmentWorlds94C],
"ReferenceRelationsCorrect"->Count[developmentPairs94C,p_/;
TrueQ[p["ReferenceRelationCorrect"]]],
"MixedContextWorlds"->Count[developmentWorlds94C,w_/;And[
w["NonQueryContinueBranches"]>0,w["NonQueryStopBranches"]>0]],
"CanonicalCaseExactlyBase"->Count[developmentWorlds94C,w_/;
TrueQ[w["CanonicalCaseExactlyBase"]]],
"ContractionCountCorrect"->Count[developmentWorlds94C,w_/;
TrueQ[w["ContractionCountCorrect"]]],
"ProtectedNodesPreserved"->Count[developmentWorlds94C,w_/;
TrueQ[w["ProtectedNodesPreserved"]]],
"ValidGlobalVectors"->Count[developmentWorlds94C,w_/;
VectorQ[w["GlobalVector"],IntegerQ]&&Length[w["GlobalVector"]]===27],
"ValidRoleMomentVectors"->Count[developmentWorlds94C,w_/;
VectorQ[w["RoleMomentVector"],IntegerQ]&&Length[w["RoleMomentVector"]]===60],
"ValidRoleEnhancedVectors"->Count[developmentWorlds94C,w_/;
VectorQ[w["RoleEnhancedVector"],IntegerQ]&&Length[w["RoleEnhancedVector"]]===132],
"ValidRoleHistogramVectors"->Count[developmentWorlds94C,w_/;
VectorQ[w["RoleHistogramVector"],IntegerQ]&&Length[w["RoleHistogramVector"]]===495],
"TerminatedNaturally"->Count[developmentWorlds94C,w_/;
TrueQ[w["TerminatedNaturally"]]],
"HitSafetyCap"->Count[developmentWorlds94C,w_/;TrueQ[w["HitSafetyCap"]]],
"TotalTraceSeconds"->Total@Lookup[developmentWorlds94C,"TraceSeconds"]|>;

testValidityPassed94C=And[
SameQ[summary94C["Scenarios"],32],SameQ[summary94C["Pairs"],416],
SameQ[summary94C["Worlds"],832],
SameQ[summary94C["ReferenceRelationsCorrect"],416],
SameQ[summary94C["MixedContextWorlds"],832],
SameQ[summary94C["CanonicalCaseExactlyBase"],832],
SameQ[summary94C["ContractionCountCorrect"],832],
SameQ[summary94C["ProtectedNodesPreserved"],832],
SameQ[summary94C["ValidGlobalVectors"],832],
SameQ[summary94C["ValidRoleMomentVectors"],832],
SameQ[summary94C["ValidRoleEnhancedVectors"],832],
SameQ[summary94C["ValidRoleHistogramVectors"],832],
SameQ[summary94C["TerminatedNaturally"],832],
SameQ[summary94C["HitSafetyCap"],0],
SameQ[Length[folds94C],55],SameQ[Length[candidateResults94C],34]];
roleAwareImproved94C=And[
bestRoleAware94C["Accuracy"]>bestGlobal94C["Accuracy"],
bestRoleAware94C["WorstFoldAccuracy"]>=bestGlobal94C["WorstFoldAccuracy"]];
developmentCriterionPassed94C=And[TrueQ[testValidityPassed94C],
!SameQ[bestCandidate94C["Representation"],"Global27"],
bestCandidate94C["Accuracy"]>=0.95,
bestCandidate94C["WorstFoldAccuracy"]>=0.8,
bestTrainingAccuracy94C>=0.95,
SameQ[bestCandidate94C["ZeroScores"],0],
SameQ[bestRepresentationAudit94C["AntisymmetricAliasConflicts"],0]];

Column[{Dataset[{summary94C}],
Dataset[KeyDrop[#,"FoldResults"]&/@Take[candidateRanking94C,UpTo[15]]],
Dataset[representationAudits94C],Dataset[bestAxisSummary94C],
Dataset[bestWorstFolds94C],Dataset[{<|
"BestGlobal"->KeyDrop[bestGlobal94C,"FoldResults"],
"BestRoleAware"->KeyDrop[bestRoleAware94C,"FoldResults"],
"BestOverall"->KeyDrop[bestCandidate94C,"FoldResults"],
"BestTrainingAccuracy"->bestTrainingAccuracy94C,
"RoleAwareImproved"->roleAwareImproved94C,
"DevelopmentCriterionPassed"->developmentCriterionPassed94C|>}]}]
'''.strip()


audit = r'''
modelHashAfter94C=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94C=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94C=Hash[Normal[baseDecoderRaw94C],"SHA256","HexString"];
pairDecoderObjectHashAfter94C=Hash[Normal[pairDecoderRaw94C],"SHA256","HexString"];
coreHashAfter94C=Hash[CoreDefinitionBundle94C[],"SHA256","HexString"];
canonicalizerHashAfter94C=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter94C=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94C=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94C=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94C=Hash[
PairRuntimeDefinitionBundle94C[],"SHA256","HexString"];
testDefinitionHashAfter94C=Hash[TestDefinitionBundle94C[],"SHA256","HexString"];
readoutDefinitionHashAfter94C=Hash[ReadoutDefinitionBundle94C[],"SHA256","HexString"];
fileHashesAfter94C=FileSHA256Hex94C/@requiredFiles94C;

integrityPassed94C=And[
SameQ[modelHashBefore94C,modelHashAfter94C],
SameQ[k33ObjectHashBefore94C,k33ObjectHashAfter94C],
SameQ[baseDecoderObjectHashBefore94C,baseDecoderObjectHashAfter94C],
SameQ[pairDecoderObjectHashBefore94C,pairDecoderObjectHashAfter94C],
SameQ[coreHashBefore94C,coreHashAfter94C],
SameQ[canonicalizerHashBefore94C,canonicalizerHashAfter94C],
SameQ[interventionHashBefore94C,interventionHashAfter94C],
SameQ[topologyPrimitiveHashBefore94C,topologyPrimitiveHashAfter94C],
SameQ[baseRuntimeDefinitionHashBefore94C,baseRuntimeDefinitionHashAfter94C],
SameQ[pairRuntimeDefinitionHashBefore94C,pairRuntimeDefinitionHashAfter94C],
SameQ[testDefinitionHashBefore94C,testDefinitionHashAfter94C],
SameQ[readoutDefinitionHashBefore94C,readoutDefinitionHashAfter94C],
SameQ[fileHashesBefore94C,fileHashesAfter94C]];

developmentArtifact94C=<|"Stage"->"S94C","DevelopmentOnly"->True,
"SourceS94LabelsAlreadyRevealed"->True,"ProtocolHash"->protocolHash94C,
"TestDefinitionHash"->testDefinitionHashAfter94C,
"ReadoutDefinitionHash"->readoutDefinitionHashAfter94C,
"Rows"->Map[KeyTake[#,{
"ScenarioKey","Topology","TopologyIndex","ContextPattern","ContextIndex",
"Depth","Answer","GlobalDifference","RoleMomentDifference",
"RoleEnhancedDifference","RoleHistogramDifference","CombinedDifference"}]&,
developmentPairs94C]|>;
developmentArtifactObjectHash94C=Hash[Normal[developmentArtifact94C],
"SHA256","HexString"];
developmentArtifactExportResult94C=Quiet@Check[
Export[developmentPairsPath94C,developmentArtifact94C,"WXF"],$Failed];
developmentArtifactExported94C=StringQ[developmentArtifactExportResult94C]&&
FileExistsQ[developmentPairsPath94C]&&FileByteCount[developmentPairsPath94C]>0;
developmentArtifactFileHash94C=If[TrueQ[developmentArtifactExported94C],
FileSHA256Hex94C[developmentPairsPath94C],Missing[]];

compactRanking94C=Map[KeyDrop[#,"FoldResults"]&,
Take[candidateRanking94C,UpTo[15]]];
resultPayload94C=<|"Stage"->"S94C",
"Name"->"ExpandedRoleAwareReadoutDevelopment","DevelopmentOnly"->True,
"BlindTest"->False,"UsesRevealedS94Labels"->True,
"MayClaimBlindResult"->False,"ProtocolHash"->protocolHash94C,
"Scenarios"->summary94C["Scenarios"],"Pairs"->summary94C["Pairs"],
"Worlds"->summary94C["Worlds"],
"BestGlobal"->KeyDrop[bestGlobal94C,"FoldResults"],
"BestRoleAware"->KeyDrop[bestRoleAware94C,"FoldResults"],
"BestOverall"->KeyDrop[bestCandidate94C,"FoldResults"],
"BestTrainingAccuracy"->bestTrainingAccuracy94C,
"BestAxisSummary"->bestAxisSummary94C,"BestWorstFolds"->bestWorstFolds94C,
"RepresentationAudits"->representationAudits94C,
"CandidateRankingTop15"->compactRanking94C,
"RoleAwareImproved"->roleAwareImproved94C,
"DevelopmentCriterionPassed"->developmentCriterionPassed94C,
"TestValidityPassed"->testValidityPassed94C,
"IntegrityPassed"->integrityPassed94C,
"DevelopmentArtifactExported"->developmentArtifactExported94C,
"DevelopmentArtifactObjectHash"->developmentArtifactObjectHash94C,
"DevelopmentArtifactFileHash"->developmentArtifactFileHash94C,
"CandidateFrozen"->False,"DynamicModulusSelected"->False,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94C,modelHashAfter94C],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94C,
pairDecoderObjectHashAfter94C],
"CoreChanged"->!SameQ[coreHashBefore94C,coreHashAfter94C],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94C,canonicalizerHashAfter94C],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94C,interventionHashAfter94C],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94C,coreHashAfter94C],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94C,coreHashAfter94C],
"TotalTraceSeconds"->summary94C["TotalTraceSeconds"],
"Outcome"->Which[
!TrueQ[testValidityPassed94C]||!TrueQ[integrityPassed94C]||
!TrueQ[developmentArtifactExported94C],"S94C_INVALID_DEVELOPMENT_RUN",
TrueQ[developmentCriterionPassed94C],
"S94C_EXPANDED_ROLE_AWARE_PASS_READY_FOR_INDEPENDENT_CONFIRMATION",
bestCandidate94C["Accuracy"]>0.8461538461538461,
"S94C_EXPANDED_ROLE_AWARE_PARTIAL_IMPROVEMENT",
True,"S94C_NO_ROBUST_CONTEXT_INVARIANT_READOUT_FOUND"],
"SuggestedNextStage"->Which[
TrueQ[developmentCriterionPassed94C],
"S94D_INDEPENDENT_CONFIRMATION_BEFORE_ANY_FREEZE",
bestRepresentationAudit94C["AntisymmetricAliasConflicts"]>0,
"S94D_REPRESENTATION_SUFFICIENCY_AUDIT",
bestTrainingAccuracy94C<0.95,"S94D_READOUT_CAPACITY_AUDIT",
True,"S94D_WORST_FOLD_ROLE_INTERACTION_AUDIT"]|>;
resultHash94C=Hash[Normal[resultPayload94C],"SHA256","HexString"];
certificate94C=Append[resultPayload94C,"ResultHash"->resultHash94C];
certificateExportResult94C=Quiet@Check[
Export[resultCertificatePath94C,certificate94C,"RawJSON"],$Failed];
certificateExported94C=StringQ[certificateExportResult94C]&&
FileExistsQ[resultCertificatePath94C]&&FileByteCount[resultCertificatePath94C]>0;

Column[{Dataset[{certificate94C}],Dataset[{<|
"CertificateExported"->certificateExported94C,
"CertificatePath"->resultCertificatePath94C,
"CertificateBytes"->If[FileExistsQ[resultCertificatePath94C],
FileByteCount[resultCertificatePath94C],0],
"DevelopmentPairsExported"->developmentArtifactExported94C,
"DevelopmentPairsPath"->developmentPairsPath94C,
"CoreChanged"->certificate94C["CoreChanged"],
"Outcome"->certificate94C["Outcome"]|>}]}]
'''.strip()


cells = [core, locks.strip(), definitions, evaluation, audit]
WL.write_text(
    "\n\n".join(
        f"(* S94C CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells, 1)
    )
    + "\n",
    encoding="utf-8",
)

PREFLIGHT_WL.write_text(
    "\n\n".join(
        f"(* S94C PREFLIGHT CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells[:3], 1)
    )
    + "\n",
    encoding="utf-8",
)

NB.write_text(
    json.dumps(
        notebook(
            cells,
            "TCCT S94C — Expanded Role-Aware Readout Development",
            "Development-only stage using revealed S94 labels. Run all cells once. "
            "No frozen model, core mechanism, modulus, or candidate is changed.",
        ),
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)

PREFLIGHT_NB.write_text(
    json.dumps(
        notebook(
            cells[:3],
            "TCCT S94C — Preflight",
            "Locked-input and definition check only; no development worlds are generated.",
        ),
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)

LAUNCHER.write_text(
    "@echo off\n"
    "chcp 65001 >nul\n"
    'start "" "http://localhost:8889/lab/tree/'
    'TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.ipynb"\n'
    "exit /b 0\n",
    encoding="utf-8",
)

precommit = {
    "Stage": "S94C",
    "Name": "ExpandedRoleAwareReadoutDevelopment",
    "DevelopmentOnly": True,
    "BlindTest": False,
    "CandidateFrozen": False,
    "CoreMechanismChanged": False,
    "ExpectedScenarios": 32,
    "ExpectedPairs": 416,
    "ExpectedWorlds": 832,
    "ExpectedFolds": 55,
    "ExpectedCandidateSpecifications": 34,
    "DevelopmentPassAccuracy": 0.95,
    "DevelopmentPassWorstFoldAccuracy": 0.8,
    "WolframSourceSHA256": sha256(WL),
    "NotebookSHA256": sha256(NB),
    "PreflightSourceSHA256": sha256(PREFLIGHT_WL),
    "PreflightNotebookSHA256": sha256(PREFLIGHT_NB),
}
PRECOMMIT.write_text(json.dumps(precommit, indent=2), encoding="utf-8")

for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(f"{path.name}\t{path.stat().st_size}\t{sha256(path)}")
