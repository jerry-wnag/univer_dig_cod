"""Build TCCT S94G full-query frozen-token development validation."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94F_DualChannelInformationAudit.wl"
WL = ROOT / "TCCT_S94G_FullQueryScopeDevelopment.wl"
NB = ROOT / "TCCT_S94G_FullQueryScopeDevelopment.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94G_FullQueryScopeDevelopment_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94G_FullQueryScopeDevelopment_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94G_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94G_Precommit.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook(cells: list[str], title: str, note: str) -> dict:
    out = [{"cell_type": "markdown", "id": "s94g-introduction", "metadata": {},
            "source": [f"# {title}\n", "\n", note + "\n"]}]
    for i, code in enumerate(cells, 1):
        out.append({"cell_type": "code", "id": f"s94g-cell-{i}",
                    "execution_count": None, "metadata": {}, "outputs": [],
                    "source": [line + "\n" for line in code.splitlines()]})
    return {"cells": out, "metadata": {
        "kernelspec": {"display_name": "Wolfram Language 15",
                       "language": "Wolfram Language", "name": "wolframlanguage15"},
        "language_info": {"file_extension": ".wl",
                          "mimetype": "application/vnd.wolfram.mathematica",
                          "name": "Wolfram Language", "version": "15.0"}},
        "nbformat": 4, "nbformat_minor": 5}


parts = re.split(r"\(\* S94F CELL \d+ \*\)\r?\n", SOURCE.read_text(encoding="utf-8"))
if len(parts) != 6:
    raise SystemExit("S94F source must have five cells")
core = parts[1].strip()
locks = parts[2].replace("94F", "94G").replace("S94F", "S94G")
locks = locks.replace(
    'expectedS94ECertificateFileHash94G=\n'
    '"278c0340332e7dcb60b1bf3a07f06f0d8a8ce77bf231f3dfbce718a189fb9a6f";',
    'expectedS94ECertificateFileHash94G=\n'
    '"278c0340332e7dcb60b1bf3a07f06f0d8a8ce77bf231f3dfbce718a189fb9a6f";\n'
    'expectedS94FResultHash94G=\n'
    '"980fcc8a39a23795e8206560a9bb6c2a357f57ac1e041f2e10d89caa6d6a2fa1";\n'
    'expectedS94FCertificateFileHash94G=\n'
    '"ce776f1959926f3e81584dd10f34ee675fc90a07a7d44b3915583cd5050e6e20";',
)
locks = locks.replace(
    's94eAuditPath94G="E:/engine_wolf/TCCT_S94E_RelationBindingFeasibilityAudit.json";\n'
    'resultCertificatePath94G="E:/engine_wolf/TCCT_S94G_DualChannelInformationAudit.json";',
    's94eAuditPath94G="E:/engine_wolf/TCCT_S94E_RelationBindingFeasibilityAudit.json";\n'
    's94fAuditPath94G="E:/engine_wolf/TCCT_S94F_DualChannelInformationAudit.json";\n'
    'developmentArtifactPath94G="E:/engine_wolf/TCCT_S94G_FullQueryScopeDevelopmentPairs.wxf";\n'
    'resultCertificatePath94G="E:/engine_wolf/TCCT_S94G_FullQueryScopeDevelopment.json";',
)
locks = locks.replace('s94dAuditPath94G,s94eAuditPath94G};',
                      's94dAuditPath94G,s94eAuditPath94G,s94fAuditPath94G};')
locks = locks.replace(
    'If[FileExistsQ[resultCertificatePath94G]&&\n'
    'FileByteCount[resultCertificatePath94G]>0,\n'
    'Print["S94G aborted: a prior development certificate exists. Preserve it."];Abort[]];',
    'If[FileExistsQ[resultCertificatePath94G]&&\n'
    'FileByteCount[resultCertificatePath94G]>0,\n'
    'Print["S94G aborted: a prior development certificate exists. Preserve it."];Abort[]];\n'
    'If[FileExistsQ[developmentArtifactPath94G]&&\n'
    'FileByteCount[developmentArtifactPath94G]>0,\n'
    'Print["S94G aborted: a prior development artifact exists. Preserve it."];Abort[]];',
)
locks = locks.replace(
    's94eAudit94G=Quiet@Check[Import[s94eAuditPath94G,"RawJSON"],$Failed];',
    's94eAudit94G=Quiet@Check[Import[s94eAuditPath94G,"RawJSON"],$Failed];\n'
    's94fAudit94G=Quiet@Check[Import[s94fAuditPath94G,"RawJSON"],$Failed];',
)
locks = locks.replace(
    'TrueQ[s94eAudit94G["IntegrityPassed"]]];',
    'TrueQ[s94eAudit94G["IntegrityPassed"]],\n'
    'SameQ[fileHashesBefore94G[[13]],expectedS94FCertificateFileHash94G],\n'
    'AssociationQ[s94fAudit94G],\n'
    'SameQ[s94fAudit94G["ResultHash"],expectedS94FResultHash94G],\n'
    'SameQ[s94fAudit94G["Outcome"],"S94F_AUDIT_PASS_CHANNEL_LOCALIZED"],\n'
    'SameQ[s94fAudit94G["DominantDiagnosis"],\n'
    '"OBSERVATION_SCOPE_LOSS_TOKEN_SURVIVES_OUTSIDE_REJECTS"],\n'
    'TrueQ[s94fAudit94G["PreflightPassed"]],\n'
    'TrueQ[s94fAudit94G["AuditValidityPassed"]],\n'
    'TrueQ[s94fAudit94G["IntegrityPassed"]]];',
)
locks = locks.replace('"Stage"->"S94G","Name"->"DualChannelInformationAudit",',
                      '"Stage"->"S94G","Name"->"FullQueryScopeDevelopment",')
locks = locks.replace(
    '"S94EAuditLocked"->SameQ[fileHashesBefore94G[[12]],\n'
    'expectedS94ECertificateFileHash94G],',
    '"S94EAuditLocked"->SameQ[fileHashesBefore94G[[12]],\n'
    'expectedS94ECertificateFileHash94G],\n'
    '"S94FAuditLocked"->SameQ[fileHashesBefore94G[[13]],\n'
    'expectedS94FCertificateFileHash94G],',
)
for token in ("expectedS94FResultHash94G", "s94fAudit94G", "fileHashesBefore94G[[13]]"):
    if token not in locks:
        raise SystemExit(f"S94G lock transformation failed: {token}")

# Reuse S94F graph, trace and semantically aligned full-query extraction.
prefix = parts[3].split("testDefinitionHashBefore94F=", 1)[0]
prefix = prefix.replace("94F", "94G").replace("S94F", "S94G").strip()

definitions = ('If[!TrueQ[preflightPassed94G],\n'
               'Print["S94G blocked: preflight was not passed."];Abort[]];\n\n' + prefix + r'''

ClearAll[SlotCode94G,OneHot94G,SlotRawVector94G,SlotTokenOneHot94G,
RelationNumericVector94G,RelationDeltaOneHot94G,FullQueryFeatureVector94G,
PrepareFullQueryPair94G,FoldMember94G,FitReadout94G,ScoreReadout94G,
EvaluateCandidate94G,RepresentationAudit94G,AxisSummary94G,
ReadoutDefinitionBundle94G];
relationPairs94G={{"DecisionSource","CorrectDestination"},
{"DecisionSource","WrongDestination"},{"SafeSource","CorrectDestination"},
{"SafeSource","DummyDestination"},{"AlternativeSource","WrongDestination"},
{"AlternativeSource","DummyDestination"}};
SlotCode94G[slotMap_Association,slot_String]:=Module[{values},
values=Lookup[slotMap,slot,{}];If[Length[values]===0,{0,0},First[values]]];
OneHot94G[value_Integer,size_Integer]:=If[1<=value<=size,
Normal@SparseArray[{value->1},size],ConstantArray[0,size]];
SlotRawVector94G[slotMap_Association]:=Flatten[
SlotCode94G[slotMap,#]&/@semanticSlotOrder94G];
SlotTokenOneHot94G[slotMap_Association]:=Flatten[Map[Function[slot,
Flatten[OneHot94G[#,33]&/@SlotCode94G[slotMap,slot]]],semanticSlotOrder94G]];
RelationNumericVector94G[slotMap_Association]:=Flatten[Map[Function[pair,
Module[{source,destination,delta},source=SlotCode94G[slotMap,pair[[1]]];
destination=SlotCode94G[slotMap,pair[[2]]];delta=source-destination;
Join[source,destination,delta,source destination,
{Total[source destination],Total[Abs[delta]]}]]],relationPairs94G]];
RelationDeltaOneHot94G[slotMap_Association]:=Flatten[Map[Function[pair,
Module[{source,destination,delta},source=SlotCode94G[slotMap,pair[[1]]];
destination=SlotCode94G[slotMap,pair[[2]]];delta=1+Mod[source-destination,33];
Flatten[OneHot94G[#,33]&/@delta]]],relationPairs94G]];
FullQueryFeatureVector94G[slotMap_Association,representation_String]:=Switch[
representation,"SlotRaw12",SlotRawVector94G[slotMap],
"SlotTokenOneHot396",SlotTokenOneHot94G[slotMap],
"RelationNumeric60",RelationNumericVector94G[slotMap],
"RelationDeltaOneHot396",RelationDeltaOneHot94G[slotMap],
"Combined804",Join[SlotRawVector94G[slotMap],SlotTokenOneHot94G[slotMap],
RelationDeltaOneHot94G[slotMap]],_,$Failed];

PrepareFullQueryPair94G[row_Association]:=Module[{continue,stop,reps,differences},
continue=ChannelWorld94G[row,"Continue"];stop=ChannelWorld94G[row,"Stop"];
reps={"SlotRaw12","SlotTokenOneHot396","RelationNumeric60",
"RelationDeltaOneHot396","Combined804"};
differences=AssociationMap[FullQueryFeatureVector94G[continue["FullQueryTokens"],#]-
FullQueryFeatureVector94G[stop["FullQueryTokens"],#]&,reps];
Join[KeyTake[row,{"ScenarioKey","Topology","TopologyIndex","ContextPattern",
"ContextIndex","Depth","Answer"}],<|"Differences"->differences,
"FullQueryTokensDistinguishable"->!SameQ[continue["FullQueryTokens"],
stop["FullQueryTokens"]],"ReferenceActionsCorrect"->And[
SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],"TracesValid"->And[
continue["TerminatedNaturally"],stop["TerminatedNaturally"],
!continue["HitSafetyCap"],!stop["HitSafetyCap"]],
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>]];
FoldMember94G[row_Association,fold_Association]:=Switch[fold["Axis"],
"Topology",SameQ[row["Topology"],fold["Heldout"]],
"ContextPattern",SameQ[row["ContextPattern"],fold["Heldout"]],
"Depth",SameQ[row["Depth"],fold["Heldout"]],
"Answer",SameQ[row["Answer"],fold["Heldout"]],
"Scenario",SameQ[row["ScenarioKey"],fold["Heldout"]],_,False];
FitReadout94G[rows_List,representation_String,family_String,lambda_?NumericQ]:=Module[
{x,scale,z,mu,variance,covariance,weights},x=N[
Lookup[Lookup[#,"Differences"],representation]&/@rows];
If[!MatrixQ[x,NumericQ],Return[$Failed]];
scale=Sqrt[Mean[#^2]]&/@Transpose[x];
scale=Map[If[!NumericQ[#]||Abs[#]<10^-12,1.,#]&,scale];z=(#/scale)&/@x;mu=Mean[z];
weights=Switch[family,"Centroid",mu,
"DiagonalRidge",variance=Mean[(#-mu)^2&/@z];mu/(variance+lambda),
"FullRidge",covariance=Transpose[z].z/Length[z]-Outer[Times,mu,mu];
Quiet@Check[LinearSolve[covariance+lambda IdentityMatrix[Length[mu]],mu],$Failed],
_,$Failed];If[!VectorQ[weights,NumericQ],Return[$Failed]];
<|"Representation"->representation,"Family"->family,"Lambda"->lambda,
"Scale"->scale,"Weights"->weights|>];
ScoreReadout94G[model_Association,difference_List]:=
N[Total[model["Weights"] (difference/model["Scale"])]];
EvaluateCandidate94G[rows_List,folds_List,spec_Association]:=Module[{foldRows},
foldRows=Map[Function[fold,Module[{train,test,model,scores},
test=Select[rows,TrueQ[FoldMember94G[#,fold]]&];
train=Select[rows,!TrueQ[FoldMember94G[#,fold]]&];
model=FitReadout94G[train,spec["Representation"],spec["Family"],spec["Lambda"]];
scores=If[AssociationQ[model],ScoreReadout94G[model,
Lookup[Lookup[#,"Differences"],spec["Representation"]]]&/@test,{}];
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
RepresentationAudit94G[rows_List,representation_String]:=Module[{vectors,unique},
vectors=Lookup[Lookup[#,"Differences"],representation]&/@rows;
unique=DeleteDuplicates[vectors];
<|"Representation"->representation,"Dimension"->Length[First[vectors]],
"ZeroVectors"->Count[vectors,ConstantArray[0,Length[First[vectors]]]],
"UniqueVectors"->Length[unique],
"AntisymmetricAliasConflicts"->Length[Intersection[unique,-unique]]|>];
AxisSummary94G[foldRows_List]:=Map[Function[axis,Module[{r},
r=Select[foldRows,SameQ[Lookup[#,"Axis"],axis]&];
<|"Axis"->axis,"Folds"->Length[r],"Cases"->Total@Lookup[r,"Cases"],
"Accuracy"->N[Total@Lookup[r,"Correct"]/Total@Lookup[r,"Cases"]],
"WorstFoldAccuracy"->Min@Lookup[r,"Accuracy"]|>]],
{"Topology","ContextPattern","Depth","Answer","Scenario"}];
ReadoutDefinitionBundle94G[]:={DownValues[SlotCode94G],DownValues[OneHot94G],
DownValues[SlotRawVector94G],DownValues[SlotTokenOneHot94G],
DownValues[RelationNumericVector94G],DownValues[RelationDeltaOneHot94G],
DownValues[FullQueryFeatureVector94G],DownValues[PrepareFullQueryPair94G],
DownValues[FoldMember94G],DownValues[FitReadout94G],DownValues[ScoreReadout94G],
DownValues[EvaluateCandidate94G],DownValues[RepresentationAudit94G],
DownValues[AxisSummary94G]};
testDefinitionHashBefore94G=Hash[TestDefinitionBundle94G[],"SHA256","HexString"];
traceDefinitionHashBefore94G=Hash[AuditDefinitionBundle94G[],"SHA256","HexString"];
channelDefinitionHashBefore94G=Hash[ChannelDefinitionBundle94G[],"SHA256","HexString"];
readoutDefinitionHashBefore94G=Hash[ReadoutDefinitionBundle94G[],"SHA256","HexString"];
protocol94G=<|"Stage"->"S94G","Name"->"FullQueryScopeDevelopment",
"DevelopmentOnly"->True,"BlindTest"->False,"UsesRevealedS94Labels"->True,
"Pairs"->416,"WorldsReplayed"->832,"Folds"->55,
"Representations"->{"SlotRaw12","SlotTokenOneHot396","RelationNumeric60",
"RelationDeltaOneHot396","Combined804"},
"AntisymmetryConstraint"->"Score[x,y]==-Score[y,x]",
"DevelopmentPassAccuracy"->0.95,"DevelopmentPassWorstFoldAccuracy"->0.8,
"CandidateFrozen"->False,"CoreMechanismChanged"->False|>;
protocolHash94G=Hash[Normal[protocol94G],"SHA256","HexString"];
Dataset[{Join[protocol94G,<|"ProtocolHash"->protocolHash94G,
"TestDefinitionHash"->testDefinitionHashBefore94G,
"ReadoutDefinitionHash"->readoutDefinitionHashBefore94G|>]}]
''').strip()

evaluation = r'''
If[!TrueQ[preflightPassed94G],
Print["S94G blocked before evaluation: preflight is not True."];Abort[]];
s94cRows94G=s94cDiagnosticArtifact94G["Rows"];
fullQueryPairs94G=PrepareFullQueryPair94G/@s94cRows94G;
topologies94G=DeleteDuplicates@Lookup[fullQueryPairs94G,"Topology"];
contexts94G=DeleteDuplicates@Lookup[fullQueryPairs94G,"ContextPattern"];
depths94G=DeleteDuplicates@Lookup[fullQueryPairs94G,"Depth"];
scenarios94G=DeleteDuplicates@Lookup[fullQueryPairs94G,"ScenarioKey"];
folds94G=Join[Map[<|"Axis"->"Topology","Heldout"->#|>&,topologies94G],
Map[<|"Axis"->"ContextPattern","Heldout"->#|>&,contexts94G],
Map[<|"Axis"->"Depth","Heldout"->#|>&,depths94G],
Map[<|"Axis"->"Answer","Heldout"->#|>&,Range[13]],
Map[<|"Axis"->"Scenario","Heldout"->#|>&,scenarios94G]];
representations94G={"SlotRaw12","SlotTokenOneHot396","RelationNumeric60",
"RelationDeltaOneHot396","Combined804"};
candidateSpecs94G=Join[
Map[<|"Representation"->#,"Family"->"Centroid","Lambda"->1.|>&,representations94G],
Flatten[Table[<|"Representation"->r,"Family"->"DiagonalRidge","Lambda"->l|>,
{r,representations94G},{l,{1.,10.,100.}}],Infinity],
Flatten[Table[<|"Representation"->r,"Family"->"FullRidge","Lambda"->l|>,
{r,{"SlotRaw12","RelationNumeric60"}},{l,{10.,100.}}],Infinity]];
candidateResults94G=EvaluateCandidate94G[fullQueryPairs94G,folds94G,#]&/@candidateSpecs94G;
candidateRanking94G=SortBy[candidateResults94G,{(-Lookup[#,"Accuracy"])&,
(-Lookup[#,"WorstFoldAccuracy"])&,(-Lookup[#,"MinimumMargin"])&}];
bestCandidate94G=First[candidateRanking94G];
representationAudits94G=RepresentationAudit94G[fullQueryPairs94G,#]&/@representations94G;
bestRepresentationAudit94G=First@Select[representationAudits94G,
SameQ[Lookup[#,"Representation"],bestCandidate94G["Representation"]]&];
axisSummary94G=AxisSummary94G[bestCandidate94G["FoldResults"]];
worstFolds94G=Take[SortBy[bestCandidate94G["FoldResults"],
{Lookup[#,"Accuracy"]&,Lookup[#,"MinimumMargin"]&}],UpTo[15]];
developmentCriterionPassed94G=And[
bestCandidate94G["Accuracy"]>=0.95,bestCandidate94G["WorstFoldAccuracy"]>=0.8,
SameQ[bestCandidate94G["ZeroScores"],0],
SameQ[bestRepresentationAudit94G["ZeroVectors"],0],
SameQ[bestRepresentationAudit94G["AntisymmetricAliasConflicts"],0]];
testValidityPassed94G=And[SameQ[Length[s94cRows94G],416],
SameQ[Length[fullQueryPairs94G],416],SameQ[Length[folds94G],55],
SameQ[Length[candidateResults94G],24],
SameQ[Count[fullQueryPairs94G,p_/;TrueQ[p["ReferenceActionsCorrect"]]],416],
SameQ[Count[fullQueryPairs94G,p_/;TrueQ[p["TracesValid"]]],416]];
Column[{Dataset[KeyDrop[#,"FoldResults"]&/@Take[candidateRanking94G,UpTo[15]]],
Dataset[representationAudits94G],Dataset[axisSummary94G],Dataset[worstFolds94G],
Dataset[{<|"BestCandidate"->KeyDrop[bestCandidate94G,"FoldResults"],
"DevelopmentCriterionPassed"->developmentCriterionPassed94G,
"TestValidityPassed"->testValidityPassed94G|>}]}]
'''.strip()

audit = r'''
If[!TrueQ[preflightPassed94G],
Print["S94G blocked before certificate: preflight is not True."];Abort[]];
modelHashAfter94G=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94G=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94G=Hash[Normal[baseDecoderRaw94G],"SHA256","HexString"];
pairDecoderObjectHashAfter94G=Hash[Normal[pairDecoderRaw94G],"SHA256","HexString"];
coreHashAfter94G=Hash[CoreDefinitionBundle94G[],"SHA256","HexString"];
canonicalizerHashAfter94G=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},"SHA256","HexString"];
interventionHashAfter94G=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],DownValues[ReferenceAction82]},
"SHA256","HexString"];
topologyPrimitiveHashAfter94G=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94G=Hash[TCCTFrozenFeatureDefinitionBundleS87D[],
"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94G=Hash[PairRuntimeDefinitionBundle94G[],
"SHA256","HexString"];
testDefinitionHashAfter94G=Hash[TestDefinitionBundle94G[],"SHA256","HexString"];
traceDefinitionHashAfter94G=Hash[AuditDefinitionBundle94G[],"SHA256","HexString"];
channelDefinitionHashAfter94G=Hash[ChannelDefinitionBundle94G[],"SHA256","HexString"];
readoutDefinitionHashAfter94G=Hash[ReadoutDefinitionBundle94G[],"SHA256","HexString"];
fileHashesAfter94G=FileSHA256Hex94G/@requiredFiles94G;
integrityPassed94G=And[SameQ[modelHashBefore94G,modelHashAfter94G],
SameQ[k33ObjectHashBefore94G,k33ObjectHashAfter94G],
SameQ[baseDecoderObjectHashBefore94G,baseDecoderObjectHashAfter94G],
SameQ[pairDecoderObjectHashBefore94G,pairDecoderObjectHashAfter94G],
SameQ[coreHashBefore94G,coreHashAfter94G],
SameQ[canonicalizerHashBefore94G,canonicalizerHashAfter94G],
SameQ[interventionHashBefore94G,interventionHashAfter94G],
SameQ[topologyPrimitiveHashBefore94G,topologyPrimitiveHashAfter94G],
SameQ[baseRuntimeDefinitionHashBefore94G,baseRuntimeDefinitionHashAfter94G],
SameQ[pairRuntimeDefinitionHashBefore94G,pairRuntimeDefinitionHashAfter94G],
SameQ[testDefinitionHashBefore94G,testDefinitionHashAfter94G],
SameQ[traceDefinitionHashBefore94G,traceDefinitionHashAfter94G],
SameQ[channelDefinitionHashBefore94G,channelDefinitionHashAfter94G],
SameQ[readoutDefinitionHashBefore94G,readoutDefinitionHashAfter94G],
SameQ[fileHashesBefore94G,fileHashesAfter94G]];
developmentArtifact94G=<|"Stage"->"S94G","DevelopmentOnly"->True,
"ProtocolHash"->protocolHash94G,"Rows"->fullQueryPairs94G|>;
artifactObjectHash94G=Hash[Normal[developmentArtifact94G],"SHA256","HexString"];
artifactExport94G=Quiet@Check[Export[developmentArtifactPath94G,
developmentArtifact94G,"WXF"],$Failed];
artifactExported94G=StringQ[artifactExport94G]&&FileExistsQ[developmentArtifactPath94G]&&
FileByteCount[developmentArtifactPath94G]>0;
artifactFileHash94G=If[artifactExported94G,FileSHA256Hex94G[developmentArtifactPath94G],Missing[]];
resultPayload94G=<|"Stage"->"S94G","Name"->"FullQueryScopeDevelopment",
"DevelopmentOnly"->True,"BlindTest"->False,"UsesRevealedS94Labels"->True,
"MayClaimBlindResult"->False,"PreflightPassed"->preflightPassed94G,
"Pairs"->Length[fullQueryPairs94G],"Folds"->Length[folds94G],
"FullQueryTokenDistinguishablePairs"->Count[fullQueryPairs94G,p_/;
TrueQ[p["FullQueryTokensDistinguishable"]]],
"OldS94CBestAccuracy"->s94cDiagnosticCertificate94G["BestOverall"]["Accuracy"],
"OldS94CBestWorstFoldAccuracy"->
s94cDiagnosticCertificate94G["BestOverall"]["WorstFoldAccuracy"],
"BestFullQueryCandidate"->KeyDrop[bestCandidate94G,"FoldResults"],
"BestAxisSummary"->axisSummary94G,"BestWorstFolds"->worstFolds94G,
"RepresentationAudits"->representationAudits94G,
"CandidateRankingTop15"->Map[KeyDrop[#,"FoldResults"]&,
Take[candidateRanking94G,UpTo[15]]],
"DevelopmentCriterionPassed"->developmentCriterionPassed94G,
"TestValidityPassed"->testValidityPassed94G,"IntegrityPassed"->integrityPassed94G,
"DevelopmentArtifactExported"->artifactExported94G,
"DevelopmentArtifactObjectHash"->artifactObjectHash94G,
"DevelopmentArtifactFileHash"->artifactFileHash94G,
"CandidateFrozen"->False,"DynamicModulusSelected"->False,
"CoreChanged"->!SameQ[coreHashBefore94G,coreHashAfter94G],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94G,modelHashAfter94G],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94G,pairDecoderObjectHashAfter94G],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94G,canonicalizerHashAfter94G],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94G,interventionHashAfter94G],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94G,coreHashAfter94G],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94G,coreHashAfter94G],
"TotalTraceSeconds"->Total@Lookup[fullQueryPairs94G,"TraceSeconds"],
"Outcome"->Which[!TrueQ[testValidityPassed94G]||!TrueQ[integrityPassed94G]||
!TrueQ[artifactExported94G],"S94G_INVALID_DEVELOPMENT_RUN",
TrueQ[developmentCriterionPassed94G],"S94G_FULL_QUERY_SCOPE_DEVELOPMENT_PASS",
bestCandidate94G["Accuracy"]>
s94cDiagnosticCertificate94G["BestOverall"]["Accuracy"],
"S94G_FULL_QUERY_SCOPE_PARTIAL_IMPROVEMENT",True,"S94G_FULL_QUERY_SCOPE_NO_IMPROVEMENT"],
"SuggestedNextStage"->If[TrueQ[developmentCriterionPassed94G],
"S94H_INDEPENDENT_CONFIRMATION_BEFORE_FREEZE","S94H_FULL_QUERY_READOUT_AUDIT"]|>;
resultHash94G=Hash[Normal[resultPayload94G],"SHA256","HexString"];
certificate94G=Append[resultPayload94G,"ResultHash"->resultHash94G];
exportResult94G=Quiet@Check[Export[resultCertificatePath94G,certificate94G,"RawJSON"],$Failed];
certificateExported94G=StringQ[exportResult94G]&&FileExistsQ[resultCertificatePath94G]&&
FileByteCount[resultCertificatePath94G]>0;
Column[{Dataset[{certificate94G}],Dataset[{<|"CertificateExported"->certificateExported94G,
"CertificatePath"->resultCertificatePath94G,"PreflightPassed"->preflightPassed94G,
"TestValidityPassed"->testValidityPassed94G,"IntegrityPassed"->integrityPassed94G,
"CoreChanged"->certificate94G["CoreChanged"],"Outcome"->certificate94G["Outcome"]|>}]}]
'''.strip()

cells = [core, locks.strip(), definitions, evaluation, audit]
WL.write_text("\n\n".join(f"(* S94G CELL {i} *)\n{c}" for i, c in enumerate(cells, 1)) + "\n",
              encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(f"(* S94G PREFLIGHT CELL {i} *)\n{c}"
                                      for i, c in enumerate(cells[:3], 1)) + "\n",
                         encoding="utf-8")
NB.write_text(json.dumps(notebook(cells, "TCCT S94G — Full-Query Scope Development",
                                  "Development validation on 416 revealed pairs. Full-query frozen tokens only; "
                                  "no core change and no candidate freeze."), ensure_ascii=False, indent=1),
              encoding="utf-8")
PREFLIGHT_NB.write_text(json.dumps(notebook(cells[:3], "TCCT S94G — Preflight",
                                            "Locked inputs and definitions only."),
                                      ensure_ascii=False, indent=1), encoding="utf-8")
LAUNCHER.write_text('@echo off\nchcp 65001 >nul\nstart "" '
                    '"http://localhost:8889/lab/tree/TCCT_S94G_FullQueryScopeDevelopment.ipynb"\n'
                    'exit /b 0\n', encoding="utf-8")
pre = {"Stage": "S94G", "Name": "FullQueryScopeDevelopment", "DevelopmentOnly": True,
       "BlindTest": False, "ExpectedPairs": 416, "ExpectedWorlds": 832,
       "ExpectedFolds": 55, "ExpectedCandidates": 24,
       "PassAccuracy": 0.95, "PassWorstFoldAccuracy": 0.8,
       "CandidateFrozen": False, "CoreMechanismChanged": False,
       "WolframSourceSHA256": digest(WL), "NotebookSHA256": digest(NB),
       "PreflightSourceSHA256": digest(PREFLIGHT_WL),
       "PreflightNotebookSHA256": digest(PREFLIGHT_NB)}
PRECOMMIT.write_text(json.dumps(pre, indent=2), encoding="utf-8")
for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path.name, path.stat().st_size, digest(path))
