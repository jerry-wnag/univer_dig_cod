"""Build TCCT S94H independent confirmation before readout freeze."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94G_FullQueryScopeDevelopment.wl"
WL = ROOT / "TCCT_S94H_IndependentFullQueryConfirmation.wl"
NB = ROOT / "TCCT_S94H_IndependentFullQueryConfirmation.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94H_Jupyter.cmd"
RECOVERY_NB = ROOT / "TCCT_S94H_Recovery_R1.ipynb"
RECOVERY_LAUNCHER = ROOT / "Start_TCCT_S94H_Recovery_R1_Jupyter.cmd"
RECOVERY_NB_R2 = ROOT / "TCCT_S94H_Recovery_R2.ipynb"
RECOVERY_LAUNCHER_R2 = ROOT / "Start_TCCT_S94H_Recovery_R2_Jupyter.cmd"
SMOKE_R2 = ROOT / "TCCT_S94H_HarnessSmoke_R2.wl"
PRECOMMIT = ROOT / "TCCT_S94H_Precommit.json"
REVISION = ROOT / "TCCT_S94H_HarnessRevision1.json"
REVISION2 = ROOT / "TCCT_S94H_HarnessRevision2.json"

FROZEN_CANDIDATE_OBJECT_HASH = (
    "5ec0e4eb89e9bb447a1e103537c7b4a82eab0c807023cd5862048372efdb418b"
)
FROZEN_CANDIDATE_FILE_HASH = (
    "8cbf7184200c6a04072f9b375af3137534dc3764bff7a32bf57db4a320187e1e"
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook(cells: list[str]) -> dict:
    out = [{"cell_type": "markdown", "id": "s94h-introduction", "metadata": {},
            "source": ["# TCCT S94H — Independent Full-Query Confirmation\n", "\n",
                       "The unique SlotRaw12 + Centroid candidate is frozen before any "
                       "confirmation world is generated. No candidate search is performed.\n"]}]
    for i, code in enumerate(cells, 1):
        out.append({"cell_type": "code", "id": f"s94h-cell-{i}",
                    "execution_count": None, "metadata": {}, "outputs": [],
                    "source": [line + "\n" for line in code.splitlines()]})
    return {"cells": out, "metadata": {
        "kernelspec": {"display_name": "Wolfram Language 15",
                       "language": "Wolfram Language", "name": "wolframlanguage15"},
        "language_info": {"file_extension": ".wl",
                          "mimetype": "application/vnd.wolfram.mathematica",
                          "name": "Wolfram Language", "version": "15.0"}},
        "nbformat": 4, "nbformat_minor": 5}


parts = re.split(r"\(\* S94G CELL \d+ \*\)\r?\n", SOURCE.read_text(encoding="utf-8"))
if len(parts) != 6:
    raise SystemExit("S94G source must have five cells")
core = parts[1].strip()
locks = parts[2].replace("94G", "94H").replace("S94G", "S94H")
locks = locks.replace(
    'expectedS94FCertificateFileHash94H=\n'
    '"ce776f1959926f3e81584dd10f34ee675fc90a07a7d44b3915583cd5050e6e20";',
    'expectedS94FCertificateFileHash94H=\n'
    '"ce776f1959926f3e81584dd10f34ee675fc90a07a7d44b3915583cd5050e6e20";\n'
    'expectedS94GResultHash94H=\n'
    '"d1c1ad6fc51b6545246146556c7c48aa635d66589c138997743d8b9f6151a46b";\n'
    'expectedS94GCertificateFileHash94H=\n'
    '"cbb4c1331e8055ad9806bbc870a25cefb65c457abb54d3d506edc48ba04fefed";\n'
    'expectedS94GArtifactFileHash94H=\n'
    '"21d84fe268a1a61cb1e13c2f457144564cc79569aa7d1fbefc3a4e5fa4a221f4";',
)
locks = locks.replace(
    's94fAuditPath94H="E:/engine_wolf/TCCT_S94F_DualChannelInformationAudit.json";\n'
    'developmentArtifactPath94H="E:/engine_wolf/TCCT_S94H_FullQueryScopeDevelopmentPairs.wxf";\n'
    'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_FullQueryScopeDevelopment.json";',
    's94fAuditPath94H="E:/engine_wolf/TCCT_S94F_DualChannelInformationAudit.json";\n'
    's94gCertificatePath94H="E:/engine_wolf/TCCT_S94G_FullQueryScopeDevelopment.json";\n'
    's94gArtifactPath94H="E:/engine_wolf/TCCT_S94G_FullQueryScopeDevelopmentPairs.wxf";\n'
    'frozenCandidatePath94H="E:/engine_wolf/TCCT_S94H_FrozenFullQueryReadout.wxf";\n'
    'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_IndependentFullQueryConfirmation.json";',
)
locks = locks.replace('s94dAuditPath94H,s94eAuditPath94H,s94fAuditPath94H};',
                      's94dAuditPath94H,s94eAuditPath94H,s94fAuditPath94H,\n'
                      's94gCertificatePath94H,s94gArtifactPath94H};')
locks = locks.replace(
    'If[FileExistsQ[developmentArtifactPath94H]&&\n'
    'FileByteCount[developmentArtifactPath94H]>0,\n'
    'Print["S94H aborted: a prior development artifact exists. Preserve it."];Abort[]];',
    'expectedFrozenCandidateObjectHash94H=\n'
    f'"{FROZEN_CANDIDATE_OBJECT_HASH}";\n'
    'expectedFrozenCandidateFileHash94H=\n'
    f'"{FROZEN_CANDIDATE_FILE_HASH}";\n'
    'If[!FileExistsQ[frozenCandidatePath94H]||FileByteCount[frozenCandidatePath94H]<=0,\n'
    'Print["S94H recovery aborted: the previously frozen candidate is missing."];Abort[]];\n'
    'If[!SameQ[FileSHA256Hex94H[frozenCandidatePath94H],\n'
    'expectedFrozenCandidateFileHash94H],\n'
    'Print["S94H recovery aborted: frozen candidate file hash mismatch."];Abort[]];',
)
locks = locks.replace(
    's94fAudit94H=Quiet@Check[Import[s94fAuditPath94H,"RawJSON"],$Failed];',
    's94fAudit94H=Quiet@Check[Import[s94fAuditPath94H,"RawJSON"],$Failed];\n'
    's94gCertificate94H=Quiet@Check[Import[s94gCertificatePath94H,"RawJSON"],$Failed];\n'
    's94gArtifact94H=Quiet@Check[Import[s94gArtifactPath94H,"WXF"],$Failed];',
)
locks = locks.replace(
    'TrueQ[s94fAudit94H["IntegrityPassed"]]];',
    'TrueQ[s94fAudit94H["IntegrityPassed"]],\n'
    'SameQ[fileHashesBefore94H[[14]],expectedS94GCertificateFileHash94H],\n'
    'SameQ[fileHashesBefore94H[[15]],expectedS94GArtifactFileHash94H],\n'
    'AssociationQ[s94gCertificate94H],AssociationQ[s94gArtifact94H],\n'
    'SameQ[s94gCertificate94H["ResultHash"],expectedS94GResultHash94H],\n'
    'SameQ[s94gCertificate94H["Outcome"],"S94G_FULL_QUERY_SCOPE_DEVELOPMENT_PASS"],\n'
    'TrueQ[s94gCertificate94H["DevelopmentCriterionPassed"]],\n'
    'TrueQ[s94gCertificate94H["TestValidityPassed"]],\n'
    'TrueQ[s94gCertificate94H["IntegrityPassed"]],\n'
    'SameQ[s94gCertificate94H["DevelopmentArtifactFileHash"],\n'
    'expectedS94GArtifactFileHash94H]];',
)
locks = locks.replace('"Stage"->"S94H","Name"->"FullQueryScopeDevelopment",',
                      '"Stage"->"S94H","Name"->"IndependentFullQueryConfirmation",')
locks = locks.replace(
    '"S94FAuditLocked"->SameQ[fileHashesBefore94H[[13]],\n'
    'expectedS94FCertificateFileHash94H],',
    '"S94FAuditLocked"->SameQ[fileHashesBefore94H[[13]],\n'
    'expectedS94FCertificateFileHash94H],\n'
    '"S94GDevelopmentLocked"->And[\n'
    'SameQ[fileHashesBefore94H[[14]],expectedS94GCertificateFileHash94H],\n'
    'SameQ[fileHashesBefore94H[[15]],expectedS94GArtifactFileHash94H]],',
)
for token in ("expectedS94GResultHash94H", "s94gArtifact94H", "fileHashesBefore94H[[15]]"):
    if token not in locks:
        raise SystemExit(f"S94H lock transform failed: {token}")

# Core representation and semantic alignment definitions are reused verbatim,
# but no S94G development rows are regenerated.
definitions = parts[3].replace("94G", "94H").replace("S94G", "S94H").strip()

freeze = r'''
If[!TrueQ[preflightPassed94H],
Print["S94H blocked before candidate freeze: preflight is not True."];Abort[]];
If[Or[ValueQ[confirmationScenarios94H],ValueQ[confirmationPairs94H],
ValueQ[confirmationWorldsGenerated94H]],
Print["S94H aborted: confirmation data existed before candidate freeze."];Abort[]];
developmentRows94H=s94gArtifact94H["Rows"];
selectionRule94H=<|"Representation"->"SlotRaw12","Family"->"Centroid",
"Lambda"->1.,"Reason"->"Simplest representation among tied perfect candidates"|>;
x94H=N[Lookup[Lookup[#,"Differences"],"SlotRaw12"]&/@developmentRows94H];
scale94H=Sqrt[Mean[#^2]]&/@Transpose[x94H];
scale94H=Map[If[!NumericQ[#]||Abs[#]<10^-12,1.,#]&,scale94H];
weights94H=Mean[(#/scale94H)&/@x94H];
developmentScores94H=N[Total[weights94H (#/scale94H)]]&/@x94H;
candidatePayload94H=<|"Stage"->"S94H","Name"->"FrozenFullQueryReadout",
"Representation"->"SlotRaw12","Family"->"Centroid","Lambda"->1.,
"Scale"->scale94H,"Weights"->weights94H,"SelectionRule"->selectionRule94H,
"TrainingPairs"->Length[developmentRows94H],
"TrainingCorrect"->Count[developmentScores94H,s_/;s>0],
"TrainingMinimumMargin"->Min[developmentScores94H],
"SourceS94GResultHash"->expectedS94GResultHash94H,
"SourceS94GArtifactFileHash"->expectedS94GArtifactFileHash94H,
"FrozenBeforeConfirmationDataGeneration"->True|>;
candidateObjectHash94H=Hash[Normal[candidatePayload94H],"SHA256","HexString"];
frozenCandidate94H=Append[candidatePayload94H,"CandidateHash"->candidateObjectHash94H];
candidateFileHash94H=FileSHA256Hex94H[frozenCandidatePath94H];
candidateReloaded94H=Quiet@Check[Import[frozenCandidatePath94H,"WXF"],$Failed];
candidateReloadMatched94H=AssociationQ[candidateReloaded94H]&&
SameQ[candidateReloaded94H["CandidateHash"],candidateObjectHash94H]&&
SameQ[Hash[Normal@KeyDrop[candidateReloaded94H,{"CandidateHash"}],
"SHA256","HexString"],candidateObjectHash94H];
candidateRecoveredAfterHarnessError94H=And[
SameQ[candidateObjectHash94H,expectedFrozenCandidateObjectHash94H],
SameQ[candidateFileHash94H,expectedFrozenCandidateFileHash94H],
candidateReloadMatched94H];
candidateFrozenBeforeConfirmation94H=And[candidateRecoveredAfterHarnessError94H,
candidateReloadMatched94H,SameQ[Length[developmentRows94H],416],
SameQ[Count[developmentScores94H,s_/;s>0],416],
!ValueQ[confirmationScenarios94H],!ValueQ[confirmationPairs94H]];
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H aborted: candidate freeze sequence failed."];Abort[]];
Dataset[{<|"Stage"->"S94H","CandidateFrozenBeforeConfirmation"->True,
"Representation"->"SlotRaw12","Family"->"Centroid",
"CandidateHash"->candidateObjectHash94H,"CandidateFileHash"->candidateFileHash94H,
"CandidateRecoveredAfterHarnessError"->candidateRecoveredAfterHarnessError94H,
"CandidateReexported"->False,"ConfirmationWorldsGeneratedYet"->False,
"CandidateSearchPerformed"->False|>}]
'''.strip()

confirmation_defs = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H blocked: candidate was not frozen before confirmation definitions."];Abort[]];
ClearAll[ConfirmationContextAction94H,ConfirmationCase94H,
HierarchicalAfterDoubleAfterDiamond94H,DoubleAfterDiamondAfterHierarchical94H,
ConfirmationTopologyTransform94H,ConfirmationWorld94H,
ConfirmationPair94H,ConfirmationDefinitionBundle94H];
confirmationTopologies94H={"HierarchicalAfterDoubleAfterDiamond",
"DoubleAfterDiamondAfterHierarchical"};
confirmationContexts94H={"CyclicTwoOfFive","OuterThird","PrimeIndex"};
confirmationDepths94H={21,43};confirmationBranchCounts94H={9,17};
ConfirmationContextAction94H[i_Integer,pattern_String,n_Integer]:=Switch[pattern,
"CyclicTwoOfFive",If[MemberQ[{1,2},Mod[i,5]],"Continue","Stop"],
"OuterThird",If[i<=Ceiling[n/3]||i>Floor[2 n/3],"Continue","Stop"],
"PrimeIndex",If[PrimeQ[i],"Continue","Stop"],_,"Undefined"];
ConfirmationCase94H[depth_Integer,answer_Integer,target_String,
topologyIndex_Integer,contextIndex_Integer,branchCount_Integer,pattern_String]:=
Module[{seed,bb,K,c,v,q,e,f={},ib,m,safe,u,dummy,r1,r2,wrong,main,perm,anc,
branchAction,i},seed=94400000+100000 topologyIndex+10000 contextIndex+
100 branchCount+depth;bb=1000000000 seed;K=bb+1;
c=Table[bb+100+i,{i,branchCount}];v=Table[bb+200+i,{i,branchCount}];
q=Table[bb+300+i,{i,branchCount}];
e=Flatten[Table[{DirectedEdge[K,c[[i]]],DirectedEdge[c[[i]],v[[i]]]},{i,branchCount}],1];
Do[ib=bb+20000000 i;m=ib+1;safe=ib+2;u=ib+3;dummy=ib+4;
r1=ib+10;r2=ib+20;wrong=c[[1+Mod[i,branchCount]]];
main=Join[P59[q[[i]],r1,depth,ib+1000000],P59[q[[i]],r2,depth,ib+2000000],
{DirectedEdge[r1,m],DirectedEdge[r2,m]},P59[q[[i]],safe,depth+1,ib+3000000]];
branchAction=If[i===answer,target,ConfirmationContextAction94H[i,pattern,branchCount]];
perm=If[branchAction==="Continue",
{DirectedEdge[m,c[[i]]],DirectedEdge[safe,dummy],DirectedEdge[u,wrong]},
{DirectedEdge[m,wrong],DirectedEdge[safe,c[[i]]],DirectedEdge[u,dummy]}];
anc=Join[A59[m,i,bb+970000000+10000 i],A59[c[[i]],i,bb+980000000+10000 i]];
e=Join[e,main,perm,anc];AppendTo[f,m],{i,branchCount}];{{Union[e],q,K,v,c,f},answer}];
HierarchicalAfterDoubleAfterDiamond94H[c_List]:=
HierarchicalDiamondIn80[DoubleDiamondIn79[DiamondIn72[c]]];
DoubleAfterDiamondAfterHierarchical94H[c_List]:=
DoubleDiamondIn79[DiamondIn72[HierarchicalDiamondIn80[c]]];
ConfirmationTopologyTransform94H[name_String,c_List]:=Switch[name,
"HierarchicalAfterDoubleAfterDiamond",HierarchicalAfterDoubleAfterDiamond94H[c],
"DoubleAfterDiamondAfterHierarchical",DoubleAfterDiamondAfterHierarchical94H[c],_,$Failed];
ConfirmationWorld94H[topology_String,topologyIndex_Integer,context_String,
contextIndex_Integer,depth_Integer,branchCount_Integer,target_String,answer_Integer]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,traceSeconds,trace,levels,pack,
vertexList,queryNodes,rawMap,codeMap,slotMap,vector},
baseCase=ConfirmationCase94H[depth,answer,target,topologyIndex,contextIndex,
branchCount,context];topologyCase=ConfirmationTopologyTransform94H[topology,baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];vertexList=pack[[12]];
queryNodes=Select[Range[Length[vertexList]],TrueQ[
NodeRole94H[vertexList[[#]],canonicalCase,answer]["QueryBranchRelated"]]&];
rawMap=AssociationThread[vertexList[[queryNodes]],
({Lookup[levels[[3]],#],Lookup[levels[[4]],#]}&)/@queryNodes];
codeMap=AssociationThread[Keys[rawMap],EncodePair94H/@Values[rawMap]];
If[!AssociationQ[codeMap]||!SameQ[Keys[codeMap],Keys[rawMap]]||
!SameQ[Length[codeMap],Length[rawMap]],
Print["S94H blocked: encoded query map failed structural validation."];Abort[]];
slotMap=SemanticAlignedMap94H[codeMap,canonicalCase,answer];vector=SlotRawVector94H[slotMap];
<|"Vector"->vector,"ReferenceAction"->ReferenceAction94H[canonicalCase],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
ExpectedContractions94H[baseCase]],"ProtectedNodesPreserved"->
canonicalization["ProtectedNodesPreserved"],"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"TraceSeconds"->traceSeconds|>];
ConfirmationPair94H[topology_String,ti_Integer,context_String,ci_Integer,
depth_Integer,n_Integer,answer_Integer]:=Module[{continue,stop,difference,score,reverse},
continue=ConfirmationWorld94H[topology,ti,context,ci,depth,n,"Continue",answer];
stop=ConfirmationWorld94H[topology,ti,context,ci,depth,n,"Stop",answer];
difference=continue["Vector"]-stop["Vector"];
score=N[Total[candidateReloaded94H["Weights"]
(difference/candidateReloaded94H["Scale"])]];reverse=-score;
<|"Topology"->topology,"Context"->context,"Depth"->depth,"BranchCount"->n,
"Answer"->answer,"Score"->score,"ReverseScore"->reverse,
"PairCorrect"->And[score>0,reverse<0],"ZeroScore"->Abs[score]<10^-12,
"ReferenceActionsCorrect"->And[SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],"WorldsValid"->And[
continue["CanonicalCaseExactlyBase"],stop["CanonicalCaseExactlyBase"],
continue["ContractionCountCorrect"],stop["ContractionCountCorrect"],
continue["ProtectedNodesPreserved"],stop["ProtectedNodesPreserved"],
continue["TerminatedNaturally"],stop["TerminatedNaturally"],
!continue["HitSafetyCap"],!stop["HitSafetyCap"]],
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>];
ConfirmationDefinitionBundle94H[]:={DownValues[ConfirmationContextAction94H],
DownValues[ConfirmationCase94H],DownValues[HierarchicalAfterDoubleAfterDiamond94H],
DownValues[DoubleAfterDiamondAfterHierarchical94H],
DownValues[ConfirmationTopologyTransform94H],DownValues[ConfirmationWorld94H],
DownValues[ConfirmationPair94H]};
confirmationDefinitionHashBefore94H=Hash[ConfirmationDefinitionBundle94H[],
"SHA256","HexString"];
confirmationProtocol94H=<|"Stage"->"S94H","IndependentConfirmation"->True,
"CandidateHash"->candidateObjectHash94H,"CandidateFrozenBeforeData"->True,
"Topologies"->confirmationTopologies94H,"Contexts"->confirmationContexts94H,
"Depths"->confirmationDepths94H,"BranchCounts"->confirmationBranchCounts94H,
"ExpectedScenarios"->24,"ExpectedPairs"->312,"ExpectedWorlds"->624,
"PassAccuracy"->0.95,"PassWorstAxisGroupAccuracy"->0.8,
"CandidateSearchPerformed"->False|>;
confirmationProtocolHash94H=Hash[Normal[confirmationProtocol94H],"SHA256","HexString"];
Dataset[{Append[confirmationProtocol94H,"ProtocolHash"->confirmationProtocolHash94H]}]
'''.strip()

evaluation = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H blocked before confirmation generation: candidate is not frozen."];Abort[]];
confirmationScenarios94H=Cases[Table[
<|"Topology"->confirmationTopologies94H[[ti]],"TopologyIndex"->ti,
"Context"->confirmationContexts94H[[ci]],"ContextIndex"->ci,
"Depth"->depth,"BranchCount"->n|>,
{ti,Length[confirmationTopologies94H]},
{ci,Length[confirmationContexts94H]},
{depth,confirmationDepths94H},{n,confirmationBranchCounts94H}],_Association,Infinity];
confirmationScenarioShapePassed94H=And[
SameQ[Length[confirmationScenarios94H],24],
VectorQ[confirmationScenarios94H,AssociationQ],
SameQ[Sort@DeleteDuplicates@Lookup[confirmationScenarios94H,"BranchCount"],
Sort@confirmationBranchCounts94H]];
If[!TrueQ[confirmationScenarioShapePassed94H],
Print["S94H blocked: confirmation scenario shape is invalid."];Abort[]];
confirmationWorldsGenerated94H=True;
confirmationPairs94H=Flatten[Map[Function[s,Table[ConfirmationPair94H[
s["Topology"],s["TopologyIndex"],s["Context"],s["ContextIndex"],s["Depth"],
s["BranchCount"],answer],{answer,s["BranchCount"]}]],confirmationScenarios94H],1];
axisGroups94H=Flatten[Map[Function[axis,Map[Function[value,Module[{rows},
rows=Select[confirmationPairs94H,SameQ[Lookup[#,axis],value]&];
<|"Axis"->axis,"Value"->ToString[value],"Pairs"->Length[rows],
"Correct"->Count[rows,p_/;TrueQ[p["PairCorrect"]]],
"Accuracy"->N[Count[rows,p_/;TrueQ[p["PairCorrect"]]]/Length[rows]],
"MinimumMargin"->Min[Lookup[rows,"Score"]]|>]],DeleteDuplicates@Lookup[
confirmationPairs94H,axis]]],{"Topology","Context","Depth","BranchCount","Answer"}],1];
confirmationAccuracy94H=N[Count[confirmationPairs94H,p_/;TrueQ[p["PairCorrect"]]]/
Length[confirmationPairs94H]];
confirmationWorstGroupAccuracy94H=Min@Lookup[axisGroups94H,"Accuracy"];
confirmationValidityPassed94H=And[SameQ[Length[confirmationScenarios94H],24],
TrueQ[confirmationScenarioShapePassed94H],
SameQ[Length[confirmationPairs94H],312],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["ReferenceActionsCorrect"]]],312],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["WorldsValid"]]],312],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["ZeroScore"]]],0],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,confirmationPairs94H]];
confirmationCriterionPassed94H=And[confirmationValidityPassed94H,
confirmationAccuracy94H>=0.95,confirmationWorstGroupAccuracy94H>=0.8];
Column[{Dataset[axisGroups94H],Dataset[{<|"Pairs"->Length[confirmationPairs94H],
"Correct"->Count[confirmationPairs94H,p_/;TrueQ[p["PairCorrect"]]],
"Accuracy"->confirmationAccuracy94H,"WorstAxisGroupAccuracy"->
confirmationWorstGroupAccuracy94H,"MinimumMargin"->Min@Lookup[confirmationPairs94H,"Score"],
"ConfirmationValidityPassed"->confirmationValidityPassed94H,
"ConfirmationCriterionPassed"->confirmationCriterionPassed94H|>}]}]
'''.strip()

audit = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H blocked before certificate: freeze order invalid."];Abort[]];
modelHashAfter94H=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter94H=Hash[CoreDefinitionBundle94H[],"SHA256","HexString"];
candidateHashAfter94H=Hash[Normal@KeyDrop[candidateReloaded94H,{"CandidateHash"}],
"SHA256","HexString"];
confirmationDefinitionHashAfter94H=Hash[ConfirmationDefinitionBundle94H[],
"SHA256","HexString"];
fileHashesAfter94H=FileSHA256Hex94H/@requiredFiles94H;
integrityPassed94H=And[SameQ[modelHashBefore94H,modelHashAfter94H],
SameQ[coreHashBefore94H,coreHashAfter94H],SameQ[fileHashesBefore94H,fileHashesAfter94H],
SameQ[candidateHashAfter94H,candidateObjectHash94H],
SameQ[confirmationDefinitionHashBefore94H,confirmationDefinitionHashAfter94H]];
resultPayload94H=<|"Stage"->"S94H","Name"->"IndependentFullQueryConfirmation",
"IndependentConfirmation"->True,"BlindTest"->False,
"HarnessRevision"->2,
"HarnessCorrections"->{"ScenarioEnumerationFlattenDepthOnly",
"AssociationValueMappingPreservingKeys"},
"CandidateFrozenBeforeConfirmation"->candidateFrozenBeforeConfirmation94H,
"CandidateRecoveredAfterHarnessError"->candidateRecoveredAfterHarnessError94H,
"CandidateReexported"->False,
"CandidateSearchPerformed"->False,"CandidateHash"->candidateObjectHash94H,
"CandidateFileHash"->candidateFileHash94H,"Representation"->"SlotRaw12",
"Family"->"Centroid","Scenarios"->Length[confirmationScenarios94H],
"Pairs"->Length[confirmationPairs94H],"Worlds"->2 Length[confirmationPairs94H],
"CorrectPairs"->Count[confirmationPairs94H,p_/;TrueQ[p["PairCorrect"]]],
"Accuracy"->confirmationAccuracy94H,"WorstAxisGroupAccuracy"->
confirmationWorstGroupAccuracy94H,"MinimumMargin"->Min@Lookup[confirmationPairs94H,"Score"],
"ZeroScores"->Count[confirmationPairs94H,p_/;TrueQ[p["ZeroScore"]]],
"AxisGroups"->axisGroups94H,"ConfirmationValidityPassed"->confirmationValidityPassed94H,
"ConfirmationCriterionPassed"->confirmationCriterionPassed94H,
"IntegrityPassed"->integrityPassed94H,"CandidateFrozen"->True,
"CoreChanged"->!SameQ[coreHashBefore94H,coreHashAfter94H],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94H,modelHashAfter94H],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94H,coreHashAfter94H],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94H,coreHashAfter94H],
"TotalTraceSeconds"->Total@Lookup[confirmationPairs94H,"TraceSeconds"],
"Outcome"->Which[!TrueQ[confirmationValidityPassed94H]||!TrueQ[integrityPassed94H],
"S94H_INVALID_CONFIRMATION_DO_NOT_INTERPRET",TrueQ[confirmationCriterionPassed94H],
"S94H_INDEPENDENT_CONFIRMATION_PASS",True,"S94H_INDEPENDENT_CONFIRMATION_FAIL"],
"SuggestedNextStage"->If[TrueQ[confirmationCriterionPassed94H],
"S94I_BLIND_PROTOCOL_PRECOMMIT","S94I_CONFIRMATION_FAILURE_AUDIT"]|>;
resultHash94H=Hash[Normal[resultPayload94H],"SHA256","HexString"];
certificate94H=Append[resultPayload94H,"ResultHash"->resultHash94H];
exportResult94H=Quiet@Check[Export[resultCertificatePath94H,certificate94H,"RawJSON"],$Failed];
certificateExported94H=StringQ[exportResult94H]&&FileExistsQ[resultCertificatePath94H]&&
FileByteCount[resultCertificatePath94H]>0;
Column[{Dataset[{certificate94H}],Dataset[{<|"CertificateExported"->certificateExported94H,
"CertificatePath"->resultCertificatePath94H,"CandidateFrozenBeforeConfirmation"->
candidateFrozenBeforeConfirmation94H,"ConfirmationValidityPassed"->confirmationValidityPassed94H,
"IntegrityPassed"->integrityPassed94H,"CoreChanged"->certificate94H["CoreChanged"],
"Outcome"->certificate94H["Outcome"]|>}]}]
'''.strip()

cells = [core, locks.strip(), definitions, freeze, confirmation_defs, evaluation, audit]
WL.write_text("\n\n".join(f"(* S94H CELL {i} *)\n{c}" for i, c in enumerate(cells, 1)) + "\n",
              encoding="utf-8")
NB.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1), encoding="utf-8")
RECOVERY_NB.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1),
                       encoding="utf-8")
RECOVERY_NB_R2.write_text(json.dumps(notebook(cells), ensure_ascii=False, indent=1),
                          encoding="utf-8")
LAUNCHER.write_text('@echo off\nchcp 65001 >nul\nstart "" '
                    '"http://localhost:8889/lab/tree/TCCT_S94H_IndependentFullQueryConfirmation.ipynb"\n'
                    'exit /b 0\n', encoding="utf-8")
RECOVERY_LAUNCHER.write_text(r'''@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S94H_Recovery_R1.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S94H_FrozenFullQueryReadout.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s94h_r1"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s94h_r1"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)

if not exist "%TCCT_NOTEBOOK%" (
  echo S94H recovery notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)

if not exist "%TCCT_CANDIDATE%" (
  echo Frozen S94H candidate not found: %TCCT_CANDIDATE%
  echo Candidate recovery cannot continue.
  pause
  exit /b 1
)

if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"

start "TCCT S94H Recovery R1 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8894 --ServerApp.port_retries=0
exit /b 0
''', encoding="utf-8")
RECOVERY_LAUNCHER_R2.write_text(r'''@echo off
chcp 65001 >nul
setlocal

set "TCCT_DIR=%~dp0"
set "TCCT_NOTEBOOK=%TCCT_DIR%TCCT_S94H_Recovery_R2.ipynb"
set "TCCT_CANDIDATE=E:\engine_wolf\TCCT_S94H_FrozenFullQueryReadout.wxf"
set "JUPYTER_LAB=E:\anaconda\Scripts\jupyter-lab.exe"
set "JUPYTER_DATA_DIR=E:\engine_wolf\jupyter\data"
set "JUPYTER_CONFIG_DIR=%TCCT_DIR%.jupyter_config_s94h_r2"
set "JUPYTER_RUNTIME_DIR=%TCCT_DIR%.jupyter_runtime_s94h_r2"
set "PYTHONUTF8=1"

if not exist "%JUPYTER_LAB%" (
  echo JupyterLab not found: %JUPYTER_LAB%
  pause
  exit /b 1
)
if not exist "%TCCT_NOTEBOOK%" (
  echo S94H recovery R2 notebook not found: %TCCT_NOTEBOOK%
  pause
  exit /b 1
)
if not exist "%TCCT_CANDIDATE%" (
  echo Frozen S94H candidate not found: %TCCT_CANDIDATE%
  pause
  exit /b 1
)
if not exist "%JUPYTER_CONFIG_DIR%" mkdir "%JUPYTER_CONFIG_DIR%"
if not exist "%JUPYTER_RUNTIME_DIR%" mkdir "%JUPYTER_RUNTIME_DIR%"
start "TCCT S94H Recovery R2 JupyterLab" /min "%JUPYTER_LAB%" "%TCCT_NOTEBOOK%" --ServerApp.root_dir="%TCCT_DIR%" --ServerApp.port=8895 --ServerApp.port_retries=0
exit /b 0
''', encoding="utf-8")

smoke_r2 = r'''
mappingSmokeInput94H=<|101->{1,2},102->{3,4}|>;
mappingSmokeOutput94H=AssociationThread[Keys[mappingSmokeInput94H],
Identity/@Values[mappingSmokeInput94H]];
mappingSmokePassed94H=And[AssociationQ[mappingSmokeOutput94H],
SameQ[Keys[mappingSmokeOutput94H],Keys[mappingSmokeInput94H]],
SameQ[Values[mappingSmokeOutput94H],Values[mappingSmokeInput94H]]];
If[!TrueQ[mappingSmokePassed94H],
Print["S94H R2 smoke aborted: association value mapping failed."];Abort[]];
smokeWorld94H=ConfirmationWorld94H[First[confirmationTopologies94H],1,
First[confirmationContexts94H],1,21,9,"Continue",1];
smokeVector94H=Lookup[smokeWorld94H,"Vector",Missing[]];
smokePassed94H=And[AssociationQ[smokeWorld94H],
VectorQ[smokeVector94H,NumericQ],SameQ[Length[smokeVector94H],12],
TrueQ[smokeWorld94H["CanonicalCaseExactlyBase"]],
TrueQ[smokeWorld94H["ContractionCountCorrect"]],
TrueQ[smokeWorld94H["ProtectedNodesPreserved"]],
TrueQ[smokeWorld94H["TerminatedNaturally"]],
!TrueQ[smokeWorld94H["HitSafetyCap"]]];
Print[<|"Stage"->"S94H","HarnessRevision"->2,
"MappingSmokePassed"->mappingSmokePassed94H,
"WorldSmokePassed"->smokePassed94H,"VectorLength"->Length[smokeVector94H],
"CandidateHash"->candidateObjectHash94H,
"CandidateFileHash"->candidateFileHash94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False|>];
If[!TrueQ[smokePassed94H],Abort[]];
Quit[];
'''.strip()
SMOKE_R2.write_text("\n\n".join(
    f"(* S94H R2 SMOKE CELL {i} *)\n{c}"
    for i, c in enumerate(cells[:5] + [smoke_r2], 1)
) + "\n", encoding="utf-8")
pre = {"Stage": "S94H", "Name": "IndependentFullQueryConfirmation",
       "IndependentConfirmation": True, "BlindTest": False,
       "SelectedCandidate": "SlotRaw12_Centroid", "CandidateSearchAllowed": False,
       "ExpectedScenarios": 24, "ExpectedPairs": 312, "ExpectedWorlds": 624,
       "PassAccuracy": 0.95, "PassWorstAxisGroupAccuracy": 0.8,
       "NewTopologies": ["HierarchicalAfterDoubleAfterDiamond",
                         "DoubleAfterDiamondAfterHierarchical"],
       "NewContexts": ["CyclicTwoOfFive", "OuterThird", "PrimeIndex"],
       "NewDepths": [21, 43], "NewBranchCounts": [9, 17],
       "WolframSourceSHA256": sha(WL), "NotebookSHA256": sha(NB)}
if not PRECOMMIT.exists():
    raise SystemExit("Original S94H precommit is missing; refusing to revise protocol")
original_precommit = json.loads(PRECOMMIT.read_text(encoding="utf-8"))
revision = {
    "Stage": "S94H",
    "HarnessRevision": 1,
    "CorrectionScope": "TestHarnessOnly",
    "ObservedError": "Table::iterb",
    "RootCause": "Scenario enumeration was flattened one level too little",
    "Correction": "Use four explicit iterators and Flatten[...,3] with a 24-association gate",
    "CandidateSearchAllowed": False,
    "CandidateReexportAllowed": False,
    "FrozenCandidateObjectSHA256": FROZEN_CANDIDATE_OBJECT_HASH,
    "FrozenCandidateFileSHA256": FROZEN_CANDIDATE_FILE_HASH,
    "CoreChangeAllowed": False,
    "OriginalPrecommitSHA256": sha(PRECOMMIT),
    "OriginalWolframSourceSHA256": original_precommit["WolframSourceSHA256"],
    "OriginalNotebookSHA256": original_precommit["NotebookSHA256"],
    "RevisedWolframSourceSHA256": sha(WL),
    "RevisedNotebookSHA256": sha(NB),
}
if not REVISION.exists():
    REVISION.write_text(json.dumps(revision, indent=2), encoding="utf-8")
revision2 = {
    "Stage": "S94H",
    "HarnessRevision": 2,
    "CorrectionScope": "TestHarnessOnly",
    "ObservedError": "AssociationMap::invrlf",
    "RootCause": "AssociationMap passed complete key-value rules to a list-only encoder",
    "Correction": "Encode Values explicitly and rebuild the Association with unchanged Keys",
    "StructuralGateAdded": True,
    "SingleWorldSmokeRequiredBeforeFullRun": True,
    "CandidateSearchAllowed": False,
    "CandidateReexportAllowed": False,
    "FrozenCandidateObjectSHA256": FROZEN_CANDIDATE_OBJECT_HASH,
    "FrozenCandidateFileSHA256": FROZEN_CANDIDATE_FILE_HASH,
    "CoreChangeAllowed": False,
    "Revision1SHA256": sha(REVISION),
    "RevisedWolframSourceSHA256": sha(WL),
    "RecoveryR2NotebookSHA256": sha(RECOVERY_NB_R2),
    "SmokeR2SourceSHA256": sha(SMOKE_R2),
}
REVISION2.write_text(json.dumps(revision2, indent=2), encoding="utf-8")
for path in (WL, NB, LAUNCHER, PRECOMMIT):
    print(path.name, path.stat().st_size, sha(path))
