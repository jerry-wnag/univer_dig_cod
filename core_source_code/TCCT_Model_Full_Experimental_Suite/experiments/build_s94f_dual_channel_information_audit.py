"""Build TCCT S94F dual-channel information-location audit."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94E_RelationBindingFeasibilityAudit.wl"
WL = ROOT / "TCCT_S94F_DualChannelInformationAudit.wl"
NB = ROOT / "TCCT_S94F_DualChannelInformationAudit.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94F_DualChannelInformationAudit_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94F_DualChannelInformationAudit_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94F_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94F_Precommit.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_nb(cells: list[str], title: str, note: str) -> dict:
    result = [{"cell_type": "markdown", "id": "s94f-introduction", "metadata": {},
               "source": [f"# {title}\n", "\n", note + "\n"]}]
    for i, code in enumerate(cells, 1):
        result.append({"cell_type": "code", "id": f"s94f-cell-{i}",
                       "execution_count": None, "metadata": {}, "outputs": [],
                       "source": [line + "\n" for line in code.splitlines()]})
    return {"cells": result,
            "metadata": {"kernelspec": {"display_name": "Wolfram Language 15",
                                           "language": "Wolfram Language",
                                           "name": "wolframlanguage15"},
                         "language_info": {"file_extension": ".wl",
                                             "mimetype": "application/vnd.wolfram.mathematica",
                                             "name": "Wolfram Language", "version": "15.0"}},
            "nbformat": 4, "nbformat_minor": 5}


parts = re.split(r"\(\* S94E CELL \d+ \*\)\r?\n", SOURCE.read_text(encoding="utf-8"))
if len(parts) != 6:
    raise SystemExit("S94E source does not contain exactly five cells")
core = parts[1].strip()
locks = parts[2].replace("94E", "94F").replace("S94E", "S94F")
locks = locks.replace(
    'expectedS94DCertificateFileHash94F=\n'
    '"2d6c529a13d5a7d8ccecf6d2ce19effcd6649d4a3cf74f62638d9f7f2f64b2ad";',
    'expectedS94DCertificateFileHash94F=\n'
    '"2d6c529a13d5a7d8ccecf6d2ce19effcd6649d4a3cf74f62638d9f7f2f64b2ad";\n'
    'expectedS94EResultHash94F=\n'
    '"88cb2d459d7eb30eca1a18a9df0be07b1702a7a5e5387fdd35767adb34fff5e6";\n'
    'expectedS94ECertificateFileHash94F=\n'
    '"278c0340332e7dcb60b1bf3a07f06f0d8a8ce77bf231f3dfbce718a189fb9a6f";',
)
locks = locks.replace(
    's94dAuditPath94F="E:/engine_wolf/TCCT_S94D_RepresentationSufficiencyAudit.json";\n'
    'resultCertificatePath94F="E:/engine_wolf/TCCT_S94F_RelationBindingFeasibilityAudit.json";',
    's94dAuditPath94F="E:/engine_wolf/TCCT_S94D_RepresentationSufficiencyAudit.json";\n'
    's94eAuditPath94F="E:/engine_wolf/TCCT_S94E_RelationBindingFeasibilityAudit.json";\n'
    'resultCertificatePath94F="E:/engine_wolf/TCCT_S94F_DualChannelInformationAudit.json";',
)
locks = locks.replace('s94dAuditPath94F};', 's94dAuditPath94F,s94eAuditPath94F};')
locks = locks.replace(
    's94dAudit94F=Quiet@Check[Import[s94dAuditPath94F,"RawJSON"],$Failed];',
    's94dAudit94F=Quiet@Check[Import[s94dAuditPath94F,"RawJSON"],$Failed];\n'
    's94eAudit94F=Quiet@Check[Import[s94eAuditPath94F,"RawJSON"],$Failed];',
)
locks = locks.replace(
    'TrueQ[s94dAudit94F["IntegrityPassed"]]];',
    'TrueQ[s94dAudit94F["IntegrityPassed"]],\n'
    'SameQ[fileHashesBefore94F[[12]],expectedS94ECertificateFileHash94F],\n'
    'AssociationQ[s94eAudit94F],\n'
    'SameQ[s94eAudit94F["ResultHash"],expectedS94EResultHash94F],\n'
    'SameQ[s94eAudit94F["Outcome"],"S94E_RELATION_BINDING_HYPOTHESIS_REJECTED"],\n'
    'TrueQ[s94eAudit94F["PreflightPassed"]],\n'
    'TrueQ[s94eAudit94F["AuditValidityPassed"]],\n'
    'TrueQ[s94eAudit94F["IntegrityPassed"]]];',
)
locks = locks.replace('"Stage"->"S94F","Name"->"RelationBindingFeasibilityAudit",',
                      '"Stage"->"S94F","Name"->"DualChannelInformationAudit",')
locks = locks.replace(
    '"S94DAuditLocked"->SameQ[fileHashesBefore94F[[11]],\n'
    'expectedS94DCertificateFileHash94F],',
    '"S94DAuditLocked"->SameQ[fileHashesBefore94F[[11]],\n'
    'expectedS94DCertificateFileHash94F],\n'
    '"S94EAuditLocked"->SameQ[fileHashesBefore94F[[12]],\n'
    'expectedS94ECertificateFileHash94F],',
)
for token in ("expectedS94EResultHash94F", "s94eAudit94F", "fileHashesBefore94F[[12]]"):
    if token not in locks:
        raise SystemExit(f"lock transformation failed: {token}")

# Keep graph generation and S94D trace extraction, but omit S94E's rejected-only
# binding hypothesis and all candidate fitting code.
prefix = parts[3].split("ClearAll[FineSlotRole94E", 1)[0]
prefix = prefix.replace("94E", "94F").replace("S94E", "S94F").strip()

definitions = ('If[!TrueQ[preflightPassed94F],\n'
               'Print["S94F blocked: preflight was not passed."];Abort[]];\n\n' + prefix + r'''

ClearAll[SemanticSlot94F,SemanticAlignedMap94F,ChannelWorld94F,
ChannelPairAudit94F,ChannelDiagnosis94F,ChannelDefinitionBundle94F];
semanticSlotOrder94F={"DecisionSource","SafeSource","AlternativeSource",
"CorrectDestination","WrongDestination","DummyDestination"};
SemanticSlot94F[node_,case_List,answer_Integer]:=Module[
{x,n,m,correct,wrong,dummy},x=case[[1]];n=Length[x[[6]]];m=x[[6,answer]];
correct=x[[5,answer]];wrong=x[[5,1+Mod[answer,n]]];dummy=m+3;
Which[SameQ[node,m],"DecisionSource",SameQ[node,m+1],"SafeSource",
SameQ[node,m+2],"AlternativeSource",SameQ[node,correct],"CorrectDestination",
SameQ[node,wrong],"WrongDestination",SameQ[node,dummy],"DummyDestination",
True,"OutsideQuery"]];
SemanticAlignedMap94F[nodeMap_Association,case_List,answer_Integer]:=Module[
{rows},rows=KeyValueMap[<|"Slot"->SemanticSlot94F[#1,case,answer],
"Value"->#2|>&,nodeMap];AssociationMap[Function[slot,
Sort[Lookup[Select[rows,SameQ[Lookup[#,"Slot"],slot]&],"Value",{}],
OrderedQ[{ToString[#1,InputForm],ToString[#2,InputForm]}]&]],semanticSlotOrder94F]];

ChannelWorld94F[row_Association,target_String]:=Module[
{traceWorld,baseCase,rejectedNodes,rejectedRawNodeMap,rejectedCodeNodeMap},
traceWorld=TraceWorldStages94F[row,target];
baseCase=Case94F[row["Depth"],row["Answer"],target,row["TopologyIndex"],
row["ContextIndex"],row["ContextPattern"]];
rejectedNodes=DeleteDuplicates[Lookup[
traceWorld["PostDedupQueryObservations"],"OriginalNode",{}]];
rejectedRawNodeMap=KeyTake[traceWorld["QueryRawMap"],rejectedNodes];
rejectedCodeNodeMap=KeyTake[traceWorld["QueryCodeMap"],rejectedNodes];
<|"ReferenceAction"->traceWorld["ReferenceAction"],
"FullQueryRaw"->SemanticAlignedMap94F[traceWorld["QueryRawMap"],baseCase,row["Answer"]],
"FullQueryTokens"->SemanticAlignedMap94F[traceWorld["QueryCodeMap"],baseCase,row["Answer"]],
"RejectedRaw"->SemanticAlignedMap94F[rejectedRawNodeMap,baseCase,row["Answer"]],
"RejectedTokens"->SemanticAlignedMap94F[rejectedCodeNodeMap,baseCase,row["Answer"]],
"RejectedNodeCount"->Length[rejectedNodes],
"TerminatedNaturally"->traceWorld["TerminatedNaturally"],
"HitSafetyCap"->traceWorld["HitSafetyCap"],"TraceSeconds"->traceWorld["TraceSeconds"]|>];

ChannelDiagnosis94F[fullToken_,rejectedRaw_,rejectedToken_]:=Which[
TrueQ[fullToken]&&!TrueQ[rejectedToken],"OBSERVATION_SCOPE_LOSS_TOKEN_SURVIVES_OUTSIDE_REJECTS",
TrueQ[rejectedRaw]&&!TrueQ[rejectedToken],"FROZEN_ENCODER_COMPRESSION_ON_REJECTED_NODES",
TrueQ[fullToken]&&TrueQ[rejectedToken],"DOWNSTREAM_AGGREGATION_ONLY",
!TrueQ[fullToken]&&TrueQ[rejectedRaw],"FROZEN_ENCODER_COMPRESSION_ACROSS_QUERY_SCOPE",
True,"RAW_STATE_OR_ALIGNMENT_LIMITATION"];
ChannelPairAudit94F[row_Association]:=Module[{continue,stop,fullRaw,fullToken,
rejectedRaw,rejectedToken,diagnosis,changedFullRaw,changedFullToken,
changedRejectedRaw,changedRejectedToken},
continue=ChannelWorld94F[row,"Continue"];stop=ChannelWorld94F[row,"Stop"];
fullRaw=!SameQ[continue["FullQueryRaw"],stop["FullQueryRaw"]];
fullToken=!SameQ[continue["FullQueryTokens"],stop["FullQueryTokens"]];
rejectedRaw=!SameQ[continue["RejectedRaw"],stop["RejectedRaw"]];
rejectedToken=!SameQ[continue["RejectedTokens"],stop["RejectedTokens"]];
changedFullRaw=Select[semanticSlotOrder94F,!SameQ[
continue["FullQueryRaw"][#],stop["FullQueryRaw"][#]]&];
changedFullToken=Select[semanticSlotOrder94F,!SameQ[
continue["FullQueryTokens"][#],stop["FullQueryTokens"][#]]&];
changedRejectedRaw=Select[semanticSlotOrder94F,!SameQ[
continue["RejectedRaw"][#],stop["RejectedRaw"][#]]&];
changedRejectedToken=Select[semanticSlotOrder94F,!SameQ[
continue["RejectedTokens"][#],stop["RejectedTokens"][#]]&];
diagnosis=ChannelDiagnosis94F[fullToken,rejectedRaw,rejectedToken];
Join[KeyTake[row,{"ScenarioKey","Topology","TopologyIndex","ContextPattern",
"ContextIndex","Depth","Answer"}],<|
"FullQueryRawDistinguishable"->fullRaw,
"FullQueryTokenDistinguishable"->fullToken,
"RejectedRawDistinguishable"->rejectedRaw,
"RejectedTokenDistinguishable"->rejectedToken,
"ChangedFullQueryRawSlots"->changedFullRaw,
"ChangedFullQueryTokenSlots"->changedFullToken,
"ChangedRejectedRawSlots"->changedRejectedRaw,
"ChangedRejectedTokenSlots"->changedRejectedToken,
"ContinueRejectedNodeCount"->continue["RejectedNodeCount"],
"StopRejectedNodeCount"->stop["RejectedNodeCount"],"Diagnosis"->diagnosis,
"ReferenceActionsCorrect"->And[SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"TracesValid"->And[continue["TerminatedNaturally"],stop["TerminatedNaturally"],
!continue["HitSafetyCap"],!stop["HitSafetyCap"]],
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>]];
ChannelDefinitionBundle94F[]:={DownValues[SemanticSlot94F],
DownValues[SemanticAlignedMap94F],DownValues[ChannelWorld94F],
DownValues[ChannelPairAudit94F],DownValues[ChannelDiagnosis94F]};
testDefinitionHashBefore94F=Hash[TestDefinitionBundle94F[],"SHA256","HexString"];
traceDefinitionHashBefore94F=Hash[AuditDefinitionBundle94F[],"SHA256","HexString"];
channelDefinitionHashBefore94F=Hash[ChannelDefinitionBundle94F[],"SHA256","HexString"];
protocol94F=<|"Stage"->"S94F","Name"->"DualChannelInformationAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"ExpectedPairs"->8,"Channels"->{"FullQueryFrozenTokens","RejectedRawStates"},
"SemanticNodeAlignment"->True,"FitsReadout"->False,"CandidateFrozen"->False,
"CoreMechanismChanged"->False|>;
protocolHash94F=Hash[Normal[protocol94F],"SHA256","HexString"];
Dataset[{Join[protocol94F,<|"ProtocolHash"->protocolHash94F,
"TestDefinitionHash"->testDefinitionHashBefore94F,
"TraceDefinitionHash"->traceDefinitionHashBefore94F,
"ChannelDefinitionHash"->channelDefinitionHashBefore94F|>]}]
''').strip()

evaluation = r'''
If[!TrueQ[preflightPassed94F],
Print["S94F blocked before evaluation: preflight is not True."];Abort[]];
s94cRows94F=s94cDiagnosticArtifact94F["Rows"];
zeroRows94F=Select[s94cRows94F,Total[Abs[Lookup[#,"CombinedDifference"]]]===0&];
channelAudits94F=ChannelPairAudit94F/@zeroRows94F;
diagnosisCounts94F=Counts[Lookup[channelAudits94F,"Diagnosis"]];
channelSummary94F=<|"Pairs"->Length[channelAudits94F],
"FullQueryRawDistinguishable"->Count[channelAudits94F,p_/;TrueQ[p["FullQueryRawDistinguishable"]]],
"FullQueryTokenDistinguishable"->Count[channelAudits94F,p_/;TrueQ[p["FullQueryTokenDistinguishable"]]],
"RejectedRawDistinguishable"->Count[channelAudits94F,p_/;TrueQ[p["RejectedRawDistinguishable"]]],
"RejectedTokenDistinguishable"->Count[channelAudits94F,p_/;TrueQ[p["RejectedTokenDistinguishable"]]],
"DiagnosisCounts"->diagnosisCounts94F|>;
auditValidityPassed94F=And[SameQ[Length[s94cRows94F],416],
SameQ[Length[zeroRows94F],8],SameQ[Length[channelAudits94F],8],
And@@Lookup[channelAudits94F,"ReferenceActionsCorrect"],
And@@Lookup[channelAudits94F,"TracesValid"]];
Column[{Dataset[channelAudits94F],Dataset[{channelSummary94F}],Dataset[{<|
"AuditValidityPassed"->auditValidityPassed94F|>}]}]
'''.strip()

audit = r'''
If[!TrueQ[preflightPassed94F],
Print["S94F blocked before certificate: preflight is not True."];Abort[]];
modelHashAfter94F=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94F=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94F=Hash[Normal[baseDecoderRaw94F],"SHA256","HexString"];
pairDecoderObjectHashAfter94F=Hash[Normal[pairDecoderRaw94F],"SHA256","HexString"];
coreHashAfter94F=Hash[CoreDefinitionBundle94F[],"SHA256","HexString"];
canonicalizerHashAfter94F=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},"SHA256","HexString"];
interventionHashAfter94F=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94F=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94F=Hash[TCCTFrozenFeatureDefinitionBundleS87D[],
"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94F=Hash[PairRuntimeDefinitionBundle94F[],
"SHA256","HexString"];
testDefinitionHashAfter94F=Hash[TestDefinitionBundle94F[],"SHA256","HexString"];
traceDefinitionHashAfter94F=Hash[AuditDefinitionBundle94F[],"SHA256","HexString"];
channelDefinitionHashAfter94F=Hash[ChannelDefinitionBundle94F[],"SHA256","HexString"];
fileHashesAfter94F=FileSHA256Hex94F/@requiredFiles94F;
integrityPassed94F=And[SameQ[modelHashBefore94F,modelHashAfter94F],
SameQ[k33ObjectHashBefore94F,k33ObjectHashAfter94F],
SameQ[baseDecoderObjectHashBefore94F,baseDecoderObjectHashAfter94F],
SameQ[pairDecoderObjectHashBefore94F,pairDecoderObjectHashAfter94F],
SameQ[coreHashBefore94F,coreHashAfter94F],
SameQ[canonicalizerHashBefore94F,canonicalizerHashAfter94F],
SameQ[interventionHashBefore94F,interventionHashAfter94F],
SameQ[topologyPrimitiveHashBefore94F,topologyPrimitiveHashAfter94F],
SameQ[baseRuntimeDefinitionHashBefore94F,baseRuntimeDefinitionHashAfter94F],
SameQ[pairRuntimeDefinitionHashBefore94F,pairRuntimeDefinitionHashAfter94F],
SameQ[testDefinitionHashBefore94F,testDefinitionHashAfter94F],
SameQ[traceDefinitionHashBefore94F,traceDefinitionHashAfter94F],
SameQ[channelDefinitionHashBefore94F,channelDefinitionHashAfter94F],
SameQ[fileHashesBefore94F,fileHashesAfter94F]];
dominantDiagnosis94F=If[Length[diagnosisCounts94F]===1,
First[Keys[diagnosisCounts94F]],"MIXED_CHANNEL_DIAGNOSIS"];
resultPayload94F=<|"Stage"->"S94F","Name"->"DualChannelInformationAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"PreflightPassed"->preflightPassed94F,"SelectedPairs"->Length[channelAudits94F],
"ChannelSummary"->channelSummary94F,"PairAudits"->channelAudits94F,
"DominantDiagnosis"->dominantDiagnosis94F,
"AuditValidityPassed"->auditValidityPassed94F,"IntegrityPassed"->integrityPassed94F,
"CandidateFrozen"->False,"CoreChanged"->!SameQ[coreHashBefore94F,coreHashAfter94F],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94F,modelHashAfter94F],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94F,pairDecoderObjectHashAfter94F],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94F,canonicalizerHashAfter94F],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94F,interventionHashAfter94F],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94F,coreHashAfter94F],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94F,coreHashAfter94F],
"TotalTraceSeconds"->Total@Lookup[channelAudits94F,"TraceSeconds"],
"Outcome"->If[And[TrueQ[auditValidityPassed94F],TrueQ[integrityPassed94F]],
"S94F_AUDIT_PASS_CHANNEL_LOCALIZED","S94F_INVALID_AUDIT_DO_NOT_INTERPRET"],
"SuggestedNextStage"->Switch[dominantDiagnosis94F,
"OBSERVATION_SCOPE_LOSS_TOKEN_SURVIVES_OUTSIDE_REJECTS","S94G_FULL_QUERY_SCOPE_FEASIBILITY",
"FROZEN_ENCODER_COMPRESSION_ON_REJECTED_NODES","S94G_RAW_RESIDUAL_FEASIBILITY",
"DOWNSTREAM_AGGREGATION_ONLY","S94G_RELATION_PRESERVING_AGGREGATION",
"FROZEN_ENCODER_COMPRESSION_ACROSS_QUERY_SCOPE","S94G_ENCODER_CAPACITY_REVIEW",
_,"S94G_MIXED_CHANNEL_REVIEW"]|>;
resultHash94F=Hash[Normal[resultPayload94F],"SHA256","HexString"];
certificate94F=Append[resultPayload94F,"ResultHash"->resultHash94F];
exportResult94F=Quiet@Check[Export[resultCertificatePath94F,certificate94F,"RawJSON"],$Failed];
certificateExported94F=StringQ[exportResult94F]&&FileExistsQ[resultCertificatePath94F]&&
FileByteCount[resultCertificatePath94F]>0;
Column[{Dataset[{certificate94F}],Dataset[{<|"CertificateExported"->certificateExported94F,
"CertificatePath"->resultCertificatePath94F,"PreflightPassed"->preflightPassed94F,
"AuditValidityPassed"->auditValidityPassed94F,"IntegrityPassed"->integrityPassed94F,
"CoreChanged"->certificate94F["CoreChanged"],"Outcome"->certificate94F["Outcome"]|>}]}]
'''.strip()

cells = [core, locks.strip(), definitions, evaluation, audit]
WL.write_text("\n\n".join(f"(* S94F CELL {i} *)\n{c}" for i, c in enumerate(cells, 1)) + "\n",
              encoding="utf-8")
PREFLIGHT_WL.write_text("\n\n".join(f"(* S94F PREFLIGHT CELL {i} *)\n{c}"
                                      for i, c in enumerate(cells[:3], 1)) + "\n",
                         encoding="utf-8")
NB.write_text(json.dumps(make_nb(cells, "TCCT S94F — Dual-Channel Information Audit",
                                 "Audit only: full-query frozen tokens versus rejected-node raw states. "
                                 "No training or model modification."), ensure_ascii=False, indent=1),
              encoding="utf-8")
PREFLIGHT_NB.write_text(json.dumps(make_nb(cells[:3], "TCCT S94F — Preflight",
                                           "Locked inputs and definitions only."),
                                      ensure_ascii=False, indent=1), encoding="utf-8")
LAUNCHER.write_text('@echo off\nchcp 65001 >nul\nstart "" '
                    '"http://localhost:8889/lab/tree/TCCT_S94F_DualChannelInformationAudit.ipynb"\n'
                    'exit /b 0\n', encoding="utf-8")
pre = {"Stage": "S94F", "Name": "DualChannelInformationAudit", "AuditOnly": True,
       "BlindTest": False, "ExpectedPairs": 8, "CandidateFrozen": False,
       "CoreMechanismChanged": False, "WolframSourceSHA256": sha(WL),
       "NotebookSHA256": sha(NB), "PreflightSourceSHA256": sha(PREFLIGHT_WL),
       "PreflightNotebookSHA256": sha(PREFLIGHT_NB)}
PRECOMMIT.write_text(json.dumps(pre, indent=2), encoding="utf-8")
for path in (WL, NB, PREFLIGHT_WL, PREFLIGHT_NB, LAUNCHER, PRECOMMIT):
    print(path.name, path.stat().st_size, sha(path))
