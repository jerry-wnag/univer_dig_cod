"""Build TCCT S94E relation-binding feasibility audit."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S94D_WL = ROOT / "TCCT_S94D_RepresentationSufficiencyAudit.wl"
WL = ROOT / "TCCT_S94E_RelationBindingFeasibilityAudit.wl"
NB = ROOT / "TCCT_S94E_RelationBindingFeasibilityAudit.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94E_RelationBindingFeasibilityAudit_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94E_RelationBindingFeasibilityAudit_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94E_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94E_Precommit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook(code_cells: list[str], title: str, note: str) -> dict:
    cells: list[dict] = [
        {
            "cell_type": "markdown",
            "id": "s94e-introduction",
            "metadata": {},
            "source": [f"# {title}\n", "\n", f"{note}\n"],
        }
    ]
    for index, code in enumerate(code_cells, 1):
        cells.append(
            {
                "cell_type": "code",
                "id": f"s94e-cell-{index}",
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


source = S94D_WL.read_text(encoding="utf-8")
parts = re.split(r"\(\* S94D CELL \d+ \*\)\r?\n", source)
if len(parts) != 6:
    raise SystemExit(f"Expected five S94D cells, found {len(parts) - 1}")

core = parts[1].strip()
locks = parts[2].replace("94D", "94E").replace("S94D", "S94E")
locks = locks.replace(
    'expectedS94CArtifactFileHash94E=\n'
    '"52aae85593e68fbc0bc8bd7ec1f1552e484e093156f334f65eff96b8889b6c7a";',
    'expectedS94CArtifactFileHash94E=\n'
    '"52aae85593e68fbc0bc8bd7ec1f1552e484e093156f334f65eff96b8889b6c7a";\n'
    'expectedS94DResultHash94E=\n'
    '"5d94413b21203c3b06dd661a972b6271b078163545d46a487963f58223951f83";\n'
    'expectedS94DCertificateFileHash94E=\n'
    '"2d6c529a13d5a7d8ccecf6d2ce19effcd6649d4a3cf74f62638d9f7f2f64b2ad";',
)
locks = locks.replace(
    's94cDiagnosticArtifactPath94E="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareDevelopmentPairs.wxf";\n'
    'resultCertificatePath94E="E:/engine_wolf/TCCT_S94E_RepresentationSufficiencyAudit.json";',
    's94cDiagnosticArtifactPath94E="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareDevelopmentPairs.wxf";\n'
    's94dAuditPath94E="E:/engine_wolf/TCCT_S94D_RepresentationSufficiencyAudit.json";\n'
    'resultCertificatePath94E="E:/engine_wolf/TCCT_S94E_RelationBindingFeasibilityAudit.json";',
)
locks = locks.replace(
    's94cDiagnosticCertificatePath94E,s94cDiagnosticArtifactPath94E};',
    's94cDiagnosticCertificatePath94E,s94cDiagnosticArtifactPath94E,\n'
    's94dAuditPath94E};',
)
locks = locks.replace(
    's94cDiagnosticArtifact94E=Quiet@Check[\n'
    'Import[s94cDiagnosticArtifactPath94E,"WXF"],$Failed];',
    's94cDiagnosticArtifact94E=Quiet@Check[\n'
    'Import[s94cDiagnosticArtifactPath94E,"WXF"],$Failed];\n'
    's94dAudit94E=Quiet@Check[Import[s94dAuditPath94E,"RawJSON"],$Failed];',
)
locks = locks.replace(
    'SameQ[s94cDiagnosticCertificate94E["DevelopmentArtifactFileHash"],\n'
    'expectedS94CArtifactFileHash94E]];',
    'SameQ[s94cDiagnosticCertificate94E["DevelopmentArtifactFileHash"],\n'
    'expectedS94CArtifactFileHash94E],\n'
    'SameQ[fileHashesBefore94E[[11]],expectedS94DCertificateFileHash94E],\n'
    'AssociationQ[s94dAudit94E],\n'
    'SameQ[s94dAudit94E["ResultHash"],expectedS94DResultHash94E],\n'
    'SameQ[s94dAudit94E["Outcome"],"S94D_AUDIT_PASS_LOSS_STAGE_IDENTIFIED"],\n'
    'TrueQ[s94dAudit94E["PreflightPassed"]],\n'
    'TrueQ[s94dAudit94E["AuditValidityPassed"]],\n'
    'TrueQ[s94dAudit94E["IntegrityPassed"]]];',
)
locks = locks.replace(
    '"Stage"->"S94E","Name"->"RepresentationSufficiencyAudit",',
    '"Stage"->"S94E","Name"->"RelationBindingFeasibilityAudit",',
)
locks = locks.replace(
    '"S94CDiagnosticArtifactsLocked"->And[\n'
    'SameQ[fileHashesBefore94E[[9]],expectedS94CCertificateFileHash94E],\n'
    'SameQ[fileHashesBefore94E[[10]],expectedS94CArtifactFileHash94E]],',
    '"S94CDiagnosticArtifactsLocked"->And[\n'
    'SameQ[fileHashesBefore94E[[9]],expectedS94CCertificateFileHash94E],\n'
    'SameQ[fileHashesBefore94E[[10]],expectedS94CArtifactFileHash94E]],\n'
    '"S94DAuditLocked"->SameQ[fileHashesBefore94E[[11]],\n'
    'expectedS94DCertificateFileHash94E],',
)

for fragment in (
    "expectedS94DResultHash94E",
    "s94dAudit94E",
    "fileHashesBefore94E[[11]]",
    "RelationBindingFeasibilityAudit",
):
    if fragment not in locks:
        raise SystemExit(f"S94E lock transformation failed: {fragment}")

definition_prefix = parts[3].split("testDefinitionHashBefore94D=", 1)[0]
definition_prefix = definition_prefix.replace("94D", "94E").replace("S94D", "S94E").strip()

definitions = (
    'If[!TrueQ[preflightPassed94E],\n'
    'Print["S94E blocked: preflight was not passed in this kernel."];Abort[]];\n\n'
    + definition_prefix
    + r'''

ClearAll[FineSlotRole94E,FineSlotObservations94E,FineSlotCodeMap94E,
FineSlotVector94E,RelationBindingVector94E,BoundWorld94E,BoundPair94E,
BindingRepresentationVector94E,FitBindingReadout94E,ScoreBindingReadout94E,
BindingFoldMemberQ94E,EvaluateBindingCandidate94E,BindingDefinitionBundle94E];
fineSlotOrder94E={"DecisionSource","SafeSource","AlternativeSource",
"CorrectDestination","WrongDestination","DummyDestination"};
bindingRelationPairs94E={{"DecisionSource","CorrectDestination"},
{"DecisionSource","WrongDestination"},{"SafeSource","CorrectDestination"},
{"SafeSource","DummyDestination"},{"AlternativeSource","WrongDestination"},
{"AlternativeSource","DummyDestination"}};

FineSlotRole94E[originalNode_,case_List,answer_Integer]:=Module[
{x,branchCount,m,correct,wrong,dummy},
x=case[[1]];branchCount=Length[x[[6]]];m=x[[6,answer]];
correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,branchCount]]];dummy=m+3;
Which[SameQ[originalNode,m],"DecisionSource",
SameQ[originalNode,m+1],"SafeSource",
SameQ[originalNode,m+2],"AlternativeSource",
SameQ[originalNode,correct],"CorrectDestination",
SameQ[originalNode,wrong],"WrongDestination",
SameQ[originalNode,dummy],"DummyDestination",True,"OutsideQueryBinding"]];

FineSlotObservations94E[observations_List,case_List,answer_Integer]:=
Map[Append[#,"FineSlot"->FineSlotRole94E[Lookup[#,"OriginalNode"],case,answer]]&,
observations];
FineSlotCodeMap94E[observations_List]:=AssociationMap[Function[slot,
Sort[Lookup[Select[observations,SameQ[Lookup[#,"FineSlot"],slot]&],"Code",{}]]],
fineSlotOrder94E];
FineSlotVector94E[observations_List]:=Flatten[Map[Function[slot,Module[{codes,a,b},
codes=Lookup[Select[observations,SameQ[Lookup[#,"FineSlot"],slot]&],"Code",{}];
If[Length[codes]===0,{0,0,0},a=codes[[All,1]];b=codes[[All,2]];
{Length[codes],Total[a],Total[b]}]]],fineSlotOrder94E]];
RelationBindingVector94E[observations_List]:=Module[{slotMap,slotCode},
slotMap=FineSlotCodeMap94E[observations];
slotCode[slot_]:=If[Length[Lookup[slotMap,slot,{}]]===0,{0,0},
First[Lookup[slotMap,slot]]];
Flatten[Map[Function[pair,Module[{source,destination},
source=slotCode[pair[[1]]];destination=slotCode[pair[[2]]];
Join[source,destination,source-destination,source destination]]],
bindingRelationPairs94E]]];

BoundWorld94E[row_Association,target_String]:=Module[
{traceWorld,baseCase,fineObservations,slotMap,slotVector,relationVector},
traceWorld=TraceWorldStages94E[row,target];
baseCase=Case94E[row["Depth"],row["Answer"],target,row["TopologyIndex"],
row["ContextIndex"],row["ContextPattern"]];
fineObservations=FineSlotObservations94E[
traceWorld["PostDedupQueryObservations"],baseCase,row["Answer"]];
slotMap=FineSlotCodeMap94E[fineObservations];
slotVector=FineSlotVector94E[fineObservations];
relationVector=RelationBindingVector94E[fineObservations];
Join[traceWorld,<|"FineSlotObservations"->fineObservations,
"FineSlotCodeMap"->slotMap,"FineSlotVector"->slotVector,
"RelationBindingVector"->relationVector,
"CombinedBindingVector"->Join[slotVector,relationVector]|>]];

BoundPair94E[row_Association]:=Module[{continue,stop},
continue=BoundWorld94E[row,"Continue"];stop=BoundWorld94E[row,"Stop"];
Join[KeyTake[row,{"ScenarioKey","Topology","TopologyIndex","ContextPattern",
"ContextIndex","Depth","Answer"}],<|
"PostDedupObservationsDistinguishable"->DifferentQ94E[
continue["PostDedupQueryObservations"],stop["PostDedupQueryObservations"]],
"OldAggregatesAllEqual"->And[
SameQ[continue["GlobalVector"],stop["GlobalVector"]],
SameQ[continue["RoleMomentVector"],stop["RoleMomentVector"]],
SameQ[continue["RoleEnhancedVector"],stop["RoleEnhancedVector"]],
SameQ[continue["RoleHistogramVector"],stop["RoleHistogramVector"]]],
"FineSlotCodeMapDistinguishable"->DifferentQ94E[
continue["FineSlotCodeMap"],stop["FineSlotCodeMap"]],
"FineSlotDifference"->continue["FineSlotVector"]-stop["FineSlotVector"],
"RelationBindingDifference"->continue["RelationBindingVector"]-
stop["RelationBindingVector"],
"CombinedBindingDifference"->continue["CombinedBindingVector"]-
stop["CombinedBindingVector"],
"ReferenceActionsCorrect"->And[SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"TracesValid"->And[continue["TerminatedNaturally"],stop["TerminatedNaturally"],
!continue["HitSafetyCap"],!stop["HitSafetyCap"]],
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>]];

BindingRepresentationVector94E[row_Association,representation_String]:=Switch[
representation,"FineSlot18",row["FineSlotDifference"],
"RelationBinding48",row["RelationBindingDifference"],
"CombinedBinding66",row["CombinedBindingDifference"],_,$Failed];
FitBindingReadout94E[rows_List,representation_String,family_String,
lambda_?NumericQ]:=Module[{differences,scale,z,mu,covariance,variance,weights},
differences=BindingRepresentationVector94E[#,representation]&/@rows;
If[!MatrixQ[differences,NumericQ],Return[$Failed]];
scale=Sqrt[Mean[#^2]]&/@Transpose[differences];
scale=Map[If[!NumericQ[#]||Abs[N[#]]<10^-12,1.,N[#]]&,scale];
z=N[(#/scale)&/@differences];mu=Mean[z];
covariance=Transpose[z].z/Length[z]-Outer[Times,mu,mu];
variance=Diagonal[covariance];
weights=Switch[family,"Centroid",mu,"DiagonalRidge",mu/(variance+lambda),
"FullRidge",Quiet@Check[LinearSolve[
covariance+lambda IdentityMatrix[Length[mu]],mu],$Failed],_,$Failed];
If[!VectorQ[weights,NumericQ],Return[$Failed]];
<|"Representation"->representation,"Family"->family,"Lambda"->lambda,
"Scale"->scale,"Weights"->weights|>];
ScoreBindingReadout94E[model_Association,difference_List]:=
N[Total[model["Weights"] (difference/model["Scale"])]];
BindingFoldMemberQ94E[row_Association,fold_Association]:=Switch[fold["Axis"],
"Topology",SameQ[row["Topology"],fold["Heldout"]],
"Depth",SameQ[row["Depth"],fold["Heldout"]],_,False];
EvaluateBindingCandidate94E[rows_List,folds_List,spec_Association]:=Module[
{foldRows},foldRows=Map[Function[fold,Module[{train,test,model,scores},
test=Select[rows,TrueQ[BindingFoldMemberQ94E[#,fold]]&];
train=Select[rows,!TrueQ[BindingFoldMemberQ94E[#,fold]]&];
model=FitBindingReadout94E[train,spec["Representation"],spec["Family"],
spec["Lambda"]];
scores=If[AssociationQ[model],ScoreBindingReadout94E[model,
BindingRepresentationVector94E[#,spec["Representation"]]]&/@test,{}];
<|"Axis"->fold["Axis"],"Heldout"->ToString[fold["Heldout"]],
"Cases"->Length[test],"Correct"->Count[scores,x_/;x>0],
"ZeroScores"->Count[scores,x_/;Abs[x]<10^-12],
"Accuracy"->N[Count[scores,x_/;x>0]/Length[test]],
"MinimumMargin"->Min[scores]|>]],folds];
Join[spec,<|"Folds"->Length[foldRows],"Cases"->Total@Lookup[foldRows,"Cases"],
"Correct"->Total@Lookup[foldRows,"Correct"],
"Accuracy"->N[Total@Lookup[foldRows,"Correct"]/Total@Lookup[foldRows,"Cases"]],
"WorstFoldAccuracy"->Min@Lookup[foldRows,"Accuracy"],
"ZeroScores"->Total@Lookup[foldRows,"ZeroScores"],
"MinimumMargin"->Min@Lookup[foldRows,"MinimumMargin"],
"FoldResults"->foldRows|>]];

BindingDefinitionBundle94E[]:={DownValues[FineSlotRole94E],
DownValues[FineSlotObservations94E],DownValues[FineSlotCodeMap94E],
DownValues[FineSlotVector94E],DownValues[RelationBindingVector94E],
DownValues[BoundWorld94E],DownValues[BoundPair94E],
DownValues[BindingRepresentationVector94E],DownValues[FitBindingReadout94E],
DownValues[ScoreBindingReadout94E],DownValues[BindingFoldMemberQ94E],
DownValues[EvaluateBindingCandidate94E]};
testDefinitionHashBefore94E=Hash[TestDefinitionBundle94E[],"SHA256","HexString"];
traceAuditDefinitionHashBefore94E=Hash[AuditDefinitionBundle94E[],
"SHA256","HexString"];
bindingDefinitionHashBefore94E=Hash[BindingDefinitionBundle94E[],
"SHA256","HexString"];
protocol94E=<|"Stage"->"S94E","Name"->"RelationBindingFeasibilityAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"UsesRevealedS94CFailures"->True,"ExpectedPairs"->8,
"FineSemanticSlots"->fineSlotOrder94E,
"Representations"->{"FineSlot18","RelationBinding48","CombinedBinding66"},
"ValidationAxes"->{"Topology","Depth"},
"FeasibilityPassAccuracy"->1.0,"FeasibilityPassWorstFoldAccuracy"->1.0,
"CandidateFrozen"->False,"CoreMechanismChanged"->False|>;
protocolHash94E=Hash[Normal[protocol94E],"SHA256","HexString"];
Dataset[{Join[protocol94E,<|"ProtocolHash"->protocolHash94E,
"TestDefinitionHash"->testDefinitionHashBefore94E,
"TraceAuditDefinitionHash"->traceAuditDefinitionHashBefore94E,
"BindingDefinitionHash"->bindingDefinitionHashBefore94E|>]}]
'''
).strip()


evaluation = r'''
If[!TrueQ[preflightPassed94E],
Print["S94E blocked before evaluation: preflight is not True."];Abort[]];
s94cRows94E=s94cDiagnosticArtifact94E["Rows"];
zeroDifferenceRows94E=Select[s94cRows94E,
Total[Abs[Lookup[#,"CombinedDifference"]]]===0&];
bindingPairs94E=BoundPair94E/@zeroDifferenceRows94E;
bindingFolds94E=Join[
Map[<|"Axis"->"Topology","Heldout"->#|>&,DeleteDuplicates@Lookup[bindingPairs94E,"Topology"]],
Map[<|"Axis"->"Depth","Heldout"->#|>&,DeleteDuplicates@Lookup[bindingPairs94E,"Depth"]]];
bindingRepresentations94E={"FineSlot18","RelationBinding48","CombinedBinding66"};
bindingCandidateSpecs94E=Flatten[Table[
<|"Representation"->representation,"Family"->family,"Lambda"->lambda|>,
{representation,bindingRepresentations94E},
{family,{"Centroid","DiagonalRidge","FullRidge"}},
{lambda,If[family==="Centroid",{1.},{1.,10.,100.}]}],Infinity];
bindingCandidateResults94E=EvaluateBindingCandidate94E[
bindingPairs94E,bindingFolds94E,#]&/@bindingCandidateSpecs94E;
bindingCandidateRanking94E=SortBy[bindingCandidateResults94E,{
(-Lookup[#,"Accuracy"])&,(-Lookup[#,"WorstFoldAccuracy"])&,
(-Lookup[#,"MinimumMargin"])&}];
bestBindingCandidate94E=First[bindingCandidateRanking94E];
bindingHypothesisRecovered94E=And[
And@@Lookup[bindingPairs94E,"PostDedupObservationsDistinguishable"],
And@@Lookup[bindingPairs94E,"OldAggregatesAllEqual"],
And@@Lookup[bindingPairs94E,"FineSlotCodeMapDistinguishable"]];
feasibilityCriterionPassed94E=And[bindingHypothesisRecovered94E,
SameQ[bestBindingCandidate94E["Accuracy"],1.0],
SameQ[bestBindingCandidate94E["WorstFoldAccuracy"],1.0],
SameQ[bestBindingCandidate94E["ZeroScores"],0]];
auditValidityPassed94E=And[SameQ[Length[s94cRows94E],416],
SameQ[Length[zeroDifferenceRows94E],8],SameQ[Length[bindingPairs94E],8],
And@@Lookup[bindingPairs94E,"ReferenceActionsCorrect"],
And@@Lookup[bindingPairs94E,"TracesValid"],SameQ[Length[bindingFolds94E],6],
SameQ[Length[bindingCandidateResults94E],21]];
Column[{Dataset[KeyDrop[#,{"FineSlotDifference","RelationBindingDifference",
"CombinedBindingDifference"}]&/@bindingPairs94E],
Dataset[KeyDrop[#,"FoldResults"]&/@Take[bindingCandidateRanking94E,UpTo[12]]],
Dataset[{<|"BindingHypothesisRecovered"->bindingHypothesisRecovered94E,
"BestBindingCandidate"->KeyDrop[bestBindingCandidate94E,"FoldResults"],
"FeasibilityCriterionPassed"->feasibilityCriterionPassed94E,
"AuditValidityPassed"->auditValidityPassed94E|>}]}]
'''.strip()


audit = r'''
If[!TrueQ[preflightPassed94E],
Print["S94E blocked before certificate: preflight is not True."];Abort[]];
modelHashAfter94E=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94E=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94E=Hash[Normal[baseDecoderRaw94E],"SHA256","HexString"];
pairDecoderObjectHashAfter94E=Hash[Normal[pairDecoderRaw94E],"SHA256","HexString"];
coreHashAfter94E=Hash[CoreDefinitionBundle94E[],"SHA256","HexString"];
canonicalizerHashAfter94E=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter94E=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94E=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94E=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94E=Hash[
PairRuntimeDefinitionBundle94E[],"SHA256","HexString"];
testDefinitionHashAfter94E=Hash[TestDefinitionBundle94E[],"SHA256","HexString"];
traceAuditDefinitionHashAfter94E=Hash[AuditDefinitionBundle94E[],
"SHA256","HexString"];
bindingDefinitionHashAfter94E=Hash[BindingDefinitionBundle94E[],
"SHA256","HexString"];
fileHashesAfter94E=FileSHA256Hex94E/@requiredFiles94E;
integrityPassed94E=And[
SameQ[modelHashBefore94E,modelHashAfter94E],
SameQ[k33ObjectHashBefore94E,k33ObjectHashAfter94E],
SameQ[baseDecoderObjectHashBefore94E,baseDecoderObjectHashAfter94E],
SameQ[pairDecoderObjectHashBefore94E,pairDecoderObjectHashAfter94E],
SameQ[coreHashBefore94E,coreHashAfter94E],
SameQ[canonicalizerHashBefore94E,canonicalizerHashAfter94E],
SameQ[interventionHashBefore94E,interventionHashAfter94E],
SameQ[topologyPrimitiveHashBefore94E,topologyPrimitiveHashAfter94E],
SameQ[baseRuntimeDefinitionHashBefore94E,baseRuntimeDefinitionHashAfter94E],
SameQ[pairRuntimeDefinitionHashBefore94E,pairRuntimeDefinitionHashAfter94E],
SameQ[testDefinitionHashBefore94E,testDefinitionHashAfter94E],
SameQ[traceAuditDefinitionHashBefore94E,traceAuditDefinitionHashAfter94E],
SameQ[bindingDefinitionHashBefore94E,bindingDefinitionHashAfter94E],
SameQ[fileHashesBefore94E,fileHashesAfter94E]];
resultPayload94E=<|"Stage"->"S94E","Name"->"RelationBindingFeasibilityAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"UsesRevealedS94CFailures"->True,"PreflightPassed"->preflightPassed94E,
"SelectedPairs"->Length[bindingPairs94E],
"CorrectedS94DInterpretation"->"OUTER_RELATION_BINDING_AGGREGATION_LOSS",
"PostDedupObservationsDistinguishable"->Count[bindingPairs94E,p_/;
TrueQ[p["PostDedupObservationsDistinguishable"]]],
"OldAggregatesAllEqual"->Count[bindingPairs94E,p_/;TrueQ[p["OldAggregatesAllEqual"]]],
"FineSlotCodeMapsDistinguishable"->Count[bindingPairs94E,p_/;
TrueQ[p["FineSlotCodeMapDistinguishable"]]],
"BestBindingCandidate"->KeyDrop[bestBindingCandidate94E,"FoldResults"],
"CandidateRankingTop12"->Map[KeyDrop[#,"FoldResults"]&,
Take[bindingCandidateRanking94E,UpTo[12]]],
"BindingHypothesisRecovered"->bindingHypothesisRecovered94E,
"FeasibilityCriterionPassed"->feasibilityCriterionPassed94E,
"AuditValidityPassed"->auditValidityPassed94E,
"IntegrityPassed"->integrityPassed94E,
"CandidateFrozen"->False,"DynamicModulusSelected"->False,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94E,modelHashAfter94E],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94E,pairDecoderObjectHashAfter94E],
"CoreChanged"->!SameQ[coreHashBefore94E,coreHashAfter94E],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94E,canonicalizerHashAfter94E],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94E,interventionHashAfter94E],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94E,coreHashAfter94E],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94E,coreHashAfter94E],
"TotalTraceSeconds"->Total@Lookup[bindingPairs94E,"TraceSeconds"],
"Outcome"->Which[
!TrueQ[auditValidityPassed94E]||!TrueQ[integrityPassed94E],
"S94E_INVALID_AUDIT_DO_NOT_INTERPRET",
TrueQ[feasibilityCriterionPassed94E],
"S94E_RELATION_BINDING_FEASIBILITY_PASS",
TrueQ[bindingHypothesisRecovered94E],
"S94E_BINDING_RECOVERED_READOUT_NOT_ROBUST",
True,"S94E_RELATION_BINDING_HYPOTHESIS_REJECTED"],
"SuggestedNextStage"->If[TrueQ[feasibilityCriterionPassed94E],
"S94F_FULL_GROUPED_RELATION_BINDING_CONFIRMATION",
"S94F_BINDING_REPRESENTATION_REDESIGN"]|>;
resultHash94E=Hash[Normal[resultPayload94E],"SHA256","HexString"];
certificate94E=Append[resultPayload94E,"ResultHash"->resultHash94E];
certificateExportResult94E=Quiet@Check[
Export[resultCertificatePath94E,certificate94E,"RawJSON"],$Failed];
certificateExported94E=StringQ[certificateExportResult94E]&&
FileExistsQ[resultCertificatePath94E]&&FileByteCount[resultCertificatePath94E]>0;
Column[{Dataset[{certificate94E}],Dataset[{<|
"CertificateExported"->certificateExported94E,
"CertificatePath"->resultCertificatePath94E,
"CertificateBytes"->If[FileExistsQ[resultCertificatePath94E],
FileByteCount[resultCertificatePath94E],0],
"PreflightPassed"->preflightPassed94E,"AuditValidityPassed"->auditValidityPassed94E,
"IntegrityPassed"->integrityPassed94E,"CoreChanged"->certificate94E["CoreChanged"],
"Outcome"->certificate94E["Outcome"]|>}]}]
'''.strip()


cells = [core, locks.strip(), definitions, evaluation, audit]
WL.write_text(
    "\n\n".join(
        f"(* S94E CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells, 1)
    )
    + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL.write_text(
    "\n\n".join(
        f"(* S94E PREFLIGHT CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells[:3], 1)
    )
    + "\n",
    encoding="utf-8",
)
NB.write_text(
    json.dumps(
        notebook(
            cells,
            "TCCT S94E — Relation-Binding Feasibility Audit",
            "Audit-only development on eight revealed failures. No core, frozen "
            "candidate, deduplication, or propagation rule is modified.",
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
            "TCCT S94E — Preflight",
            "Locked-input and definition check only; no failure pair is replayed.",
        ),
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
LAUNCHER.write_text(
    "@echo off\nchcp 65001 >nul\n"
    'start "" "http://localhost:8889/lab/tree/'
    'TCCT_S94E_RelationBindingFeasibilityAudit.ipynb"\nexit /b 0\n',
    encoding="utf-8",
)
precommit = {
    "Stage": "S94E",
    "Name": "RelationBindingFeasibilityAudit",
    "AuditOnly": True,
    "BlindTest": False,
    "ExpectedPairs": 8,
    "ExpectedFolds": 6,
    "ExpectedCandidateSpecifications": 21,
    "CandidateFrozen": False,
    "CoreMechanismChanged": False,
    "WolframSourceSHA256": "",
    "NotebookSHA256": "",
    "PreflightSourceSHA256": "",
    "PreflightNotebookSHA256": "",
}
precommit["WolframSourceSHA256"] = sha256(WL)
precommit["NotebookSHA256"] = sha256(NB)
precommit["PreflightSourceSHA256"] = sha256(PREFLIGHT_WL)
precommit["PreflightNotebookSHA256"] = sha256(PREFLIGHT_NB)
PRECOMMIT.write_text(json.dumps(precommit, indent=2), encoding="utf-8")

for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(f"{path.name}\t{path.stat().st_size}\t{sha256(path)}")
