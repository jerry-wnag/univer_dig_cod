"""Build TCCT S94D representation-sufficiency audit.

S94D is audit-only. It replays only the eight zero-difference S94C pairs and
locates the first pipeline stage at which counterfactual information vanishes.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
S94C_WL = ROOT / "TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.wl"
WL = ROOT / "TCCT_S94D_RepresentationSufficiencyAudit.wl"
NB = ROOT / "TCCT_S94D_RepresentationSufficiencyAudit.ipynb"
PREFLIGHT_WL = ROOT / "TCCT_S94D_RepresentationSufficiencyAudit_Preflight.wl"
PREFLIGHT_NB = ROOT / "TCCT_S94D_RepresentationSufficiencyAudit_Preflight.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94D_Jupyter.cmd"
PRECOMMIT = ROOT / "TCCT_S94D_Precommit.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def notebook(code_cells: list[str], title: str, note: str) -> dict:
    cells: list[dict] = [
        {
            "cell_type": "markdown",
            "id": "s94d-introduction",
            "metadata": {},
            "source": [f"# {title}\n", "\n", f"{note}\n"],
        }
    ]
    for index, code in enumerate(code_cells, 1):
        cells.append(
            {
                "cell_type": "code",
                "id": f"s94d-cell-{index}",
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


source = S94C_WL.read_text(encoding="utf-8")
parts = re.split(r"\(\* S94C CELL \d+ \*\)\r?\n", source)
if len(parts) != 6:
    raise SystemExit(f"Expected five S94C cells, found {len(parts) - 1}")

core = parts[1].strip()

# Reuse the proven lock loader, rename stage-local symbols, correct the single
# mistyped S94B certificate hash, and add the S94C diagnostic artifacts.
locks = parts[2].replace("94C", "94D").replace("S94C", "S94D")
locks = locks.replace(
    '"6b3c44566c80c88495f2a322a0763b7a188383445b554eeffc30e7fa90b4e461f";',
    '"6b3c44566c80c88495f2a322a0763b7a188383445b554eefc30e7fa90b4e461f";',
)
locks = locks.replace(
    'expectedS94BArtifactFileHash94D=\n'
    '"998fa0de0fd8e14cf9c797287f64c824f7a435c2aa3c8b0b80b0a920075dc3e4";',
    'expectedS94BArtifactFileHash94D=\n'
    '"998fa0de0fd8e14cf9c797287f64c824f7a435c2aa3c8b0b80b0a920075dc3e4";\n'
    'expectedS94CDiagnosticResultHash94D=\n'
    '"7b54af78cbef4204ceb006799d2650fd365f01ffad3dcf6de3194a8ffea0abfc";\n'
    'expectedS94CCertificateFileHash94D=\n'
    '"7281c001f977f6e8cc3c51b466bd7f48ce953a8465379e68116661ed8a7181e9";\n'
    'expectedS94CArtifactFileHash94D=\n'
    '"52aae85593e68fbc0bc8bd7ec1f1552e484e093156f334f65eff96b8889b6c7a";',
)
locks = locks.replace(
    's94bArtifactPath94D="E:/engine_wolf/TCCT_S94B_RoleAwareDevelopmentPairs.wxf";\n'
    'developmentPairsPath94D="E:/engine_wolf/TCCT_S94D_ExpandedRoleAwareDevelopmentPairs.wxf";\n'
    'resultCertificatePath94D="E:/engine_wolf/TCCT_S94D_ExpandedRoleAwareReadoutDevelopment.json";',
    's94bArtifactPath94D="E:/engine_wolf/TCCT_S94B_RoleAwareDevelopmentPairs.wxf";\n'
    's94cDiagnosticCertificatePath94D="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareReadoutDevelopment.json";\n'
    's94cDiagnosticArtifactPath94D="E:/engine_wolf/TCCT_S94C_ExpandedRoleAwareDevelopmentPairs.wxf";\n'
    'resultCertificatePath94D="E:/engine_wolf/TCCT_S94D_RepresentationSufficiencyAudit.json";',
)
locks = locks.replace(
    's94bCertificatePath94D,s94bArtifactPath94D};',
    's94bCertificatePath94D,s94bArtifactPath94D,\n'
    's94cDiagnosticCertificatePath94D,s94cDiagnosticArtifactPath94D};',
)
locks = locks.replace(
    'If[FileExistsQ[developmentPairsPath94D]&&\n'
    'FileByteCount[developmentPairsPath94D]>0,\n'
    'Print["S94D aborted: a prior development-pair artifact exists. Preserve it."];Abort[]];\n',
    '',
)
locks = locks.replace(
    's94bCertificate94D=Quiet@Check[Import[s94bCertificatePath94D,"RawJSON"],$Failed];',
    's94bCertificate94D=Quiet@Check[Import[s94bCertificatePath94D,"RawJSON"],$Failed];\n'
    's94cDiagnosticCertificate94D=Quiet@Check[\n'
    'Import[s94cDiagnosticCertificatePath94D,"RawJSON"],$Failed];\n'
    's94cDiagnosticArtifact94D=Quiet@Check[\n'
    'Import[s94cDiagnosticArtifactPath94D,"WXF"],$Failed];',
)
locks = locks.replace(
    'TrueQ[s94bCertificate94D["IntegrityPassed"]]];',
    'TrueQ[s94bCertificate94D["IntegrityPassed"]],\n'
    'SameQ[fileHashesBefore94D[[9]],expectedS94CCertificateFileHash94D],\n'
    'SameQ[fileHashesBefore94D[[10]],expectedS94CArtifactFileHash94D],\n'
    'AssociationQ[s94cDiagnosticCertificate94D],\n'
    'AssociationQ[s94cDiagnosticArtifact94D],\n'
    'SameQ[s94cDiagnosticCertificate94D["ResultHash"],\n'
    'expectedS94CDiagnosticResultHash94D],\n'
    'SameQ[s94cDiagnosticCertificate94D["Outcome"],\n'
    '"S94C_EXPANDED_ROLE_AWARE_PARTIAL_IMPROVEMENT"],\n'
    'TrueQ[s94cDiagnosticCertificate94D["TestValidityPassed"]],\n'
    'TrueQ[s94cDiagnosticCertificate94D["IntegrityPassed"]],\n'
    'SameQ[s94cDiagnosticCertificate94D["DevelopmentArtifactFileHash"],\n'
    'expectedS94CArtifactFileHash94D]];',
)
locks = locks.replace(
    '"Stage"->"S94D","Name"->"ExpandedRoleAwareReadoutDevelopment",',
    '"Stage"->"S94D","Name"->"RepresentationSufficiencyAudit",',
)
locks = locks.replace(
    '"S94BResultLocked"->SameQ[fileHashesBefore94D[[7]],expectedS94BCertificateFileHash94D],',
    '"S94BResultLocked"->SameQ[fileHashesBefore94D[[7]],expectedS94BCertificateFileHash94D],\n'
    '"S94CDiagnosticArtifactsLocked"->And[\n'
    'SameQ[fileHashesBefore94D[[9]],expectedS94CCertificateFileHash94D],\n'
    'SameQ[fileHashesBefore94D[[10]],expectedS94CArtifactFileHash94D]],',
)
locks = locks.replace(
    '"DevelopmentOnly"->True,"BlindTest"->False,',
    '"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,',
)

for fragment in (
    "expectedS94CDiagnosticResultHash94D",
    "s94cDiagnosticArtifact94D",
    "fileHashesBefore94D[[10]]",
    "RepresentationSufficiencyAudit",
):
    if fragment not in locks:
        raise SystemExit(f"S94D lock transformation failed: {fragment}")

# Reuse S94C's graph/world definitions but not its evaluation or result logic.
definition_prefix = parts[3].split("testDefinitionHashBefore94C=", 1)[0]
definition_prefix = definition_prefix.replace("94C", "94D").replace("S94C", "S94D").strip()

definitions = (
    'If[!TrueQ[preflightPassed94D],\n'
    'Print["S94D blocked: preflight was not passed in this kernel."];Abort[]];\n\n'
    + definition_prefix
    + r'''

ClearAll[TraceWorldStages94D,PairStageAudit94D,StageSignature94D,
DifferentQ94D,FirstLossDiagnosis94D,AuditDefinitionBundle94D];
StageSignature94D[x_]:=Hash[x,"SHA256","HexString"];
DifferentQ94D[a_,b_]:=!SameQ[a,b];

TraceWorldStages94D[row_Association,target_String]:=Module[
{baseCase,topologyCase,canonicalization,canonicalCase,traceSeconds,trace,
levels,pack,vertexList,allPackedNodes,allOriginalNodes,rawPairs,allRawMap,
allCodeMap,queryPackedNodes,queryOriginalNodes,rejectPackedSequence,
rejectOriginalSequence,queryRejectPackedSequence,preDedupPackedSequence,
postDedupPackedNodes,makeObservation,allRejectObservations,
preDedupQueryObservations,postDedupQueryObservations,globalVector,
roleMomentVector,roleEnhancedVector,roleHistogramVector},
baseCase=Case94D[row["Depth"],row["Answer"],target,row["TopologyIndex"],
row["ContextIndex"],row["ContextPattern"]];
topologyCase=TopologyTransform94D[row["Topology"],baseCase];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
{traceSeconds,trace}=AbsoluteTiming[RejectTrace78[canonicalCase]];
levels=SigLevels61[canonicalCase,3];pack=Pack60[canonicalCase];
vertexList=pack[[12]];allPackedNodes=Range[Length[vertexList]];
allOriginalNodes=vertexList;
rawPairs=({Lookup[levels[[3]],#],Lookup[levels[[4]],#]}&)/@allPackedNodes;
allRawMap=AssociationThread[allOriginalNodes,rawPairs];
allCodeMap=AssociationThread[allOriginalNodes,EncodePair94D/@rawPairs];
queryPackedNodes=Select[allPackedNodes,TrueQ[
NodeRole94D[vertexList[[#]],canonicalCase,row["Answer"]]["QueryBranchRelated"]]&];
queryOriginalNodes=vertexList[[queryPackedNodes]];
rejectPackedSequence=If[Length[trace["Rejects"]]===0,{},trace["Rejects"][[All,2]]];
rejectOriginalSequence=If[Length[rejectPackedSequence]===0,{},
vertexList[[rejectPackedSequence]]];
queryRejectPackedSequence=Select[rejectPackedSequence,
MemberQ[queryPackedNodes,#]&];
preDedupPackedSequence=queryRejectPackedSequence;
postDedupPackedNodes=DeleteDuplicates[queryRejectPackedSequence];
makeObservation=Function[packedNode,Module[{originalNode,roleInfo,pair},
originalNode=vertexList[[packedNode]];
roleInfo=NodeRole94D[originalNode,canonicalCase,row["Answer"]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
<|"OriginalNode"->originalNode,"Role"->roleInfo["Role"],
"RawStateHash"->StageSignature94D[pair],"Code"->EncodePair94D[pair]|>]];
allRejectObservations=makeObservation/@DeleteDuplicates[rejectPackedSequence];
preDedupQueryObservations=makeObservation/@preDedupPackedSequence;
postDedupQueryObservations=makeObservation/@postDedupPackedNodes;
globalVector=TCCTWorldVectorS87D[<|"Observations"->allRejectObservations|>];
roleMomentVector=RoleMomentVector94D[postDedupQueryObservations];
roleEnhancedVector=RoleEnhancedVector94D[postDedupQueryObservations];
roleHistogramVector=RoleHistogramVector94D[postDedupQueryObservations];
<|"Target"->target,"ReferenceAction"->ReferenceAction94D[canonicalCase],
"CanonicalEdges"->canonicalCase[[1,1]],
"AllRawMap"->allRawMap,"AllCodeMap"->allCodeMap,
"QueryRawMap"->KeyTake[allRawMap,queryOriginalNodes],
"QueryCodeMap"->KeyTake[allCodeMap,queryOriginalNodes],
"RejectOriginalSequence"->rejectOriginalSequence,
"PreDedupQueryObservations"->preDedupQueryObservations,
"PostDedupQueryObservations"->postDedupQueryObservations,
"GlobalVector"->globalVector,"RoleMomentVector"->roleMomentVector,
"RoleEnhancedVector"->roleEnhancedVector,
"RoleHistogramVector"->roleHistogramVector,
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,baseCase],
"ContractionCountCorrect"->SameQ[canonicalization["Contractions"],
ExpectedContractions94D[baseCase]],
"ProtectedNodesPreserved"->canonicalization["ProtectedNodesPreserved"],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"],"TraceSeconds"->traceSeconds|>];

FirstLossDiagnosis94D[flags_Association]:=Which[
!TrueQ[flags["CanonicalGraphDistinguishable"]],"INVALID_IDENTICAL_COUNTERFACTUAL_GRAPHS",
!TrueQ[flags["AllRawStatesDistinguishable"]],"RAW_RADIUS_STATE_COLLAPSE",
!TrueQ[flags["AllEncodedTokensDistinguishable"]],"FROZEN_ENCODER_COMPRESSION_LOSS",
!TrueQ[flags["RejectTraceDistinguishable"]],"CORE_REJECT_TRACE_SELECTION_LOSS",
!TrueQ[flags["PreDedupQueryObservationsDistinguishable"]],"QUERY_OBSERVATION_SCOPE_LOSS",
!TrueQ[flags["PostDedupQueryObservationsDistinguishable"]],"DEDUPLICATION_INFORMATION_LOSS",
True,"OUTER_AGGREGATION_LOSS"];

PairStageAudit94D[row_Association]:=Module[{continue,stop,flags,diagnosis},
continue=TraceWorldStages94D[row,"Continue"];
stop=TraceWorldStages94D[row,"Stop"];
flags=<|
"CanonicalGraphDistinguishable"->DifferentQ94D[continue["CanonicalEdges"],stop["CanonicalEdges"]],
"AllRawStatesDistinguishable"->DifferentQ94D[continue["AllRawMap"],stop["AllRawMap"]],
"QueryRawStatesDistinguishable"->DifferentQ94D[continue["QueryRawMap"],stop["QueryRawMap"]],
"AllEncodedTokensDistinguishable"->DifferentQ94D[continue["AllCodeMap"],stop["AllCodeMap"]],
"QueryEncodedTokensDistinguishable"->DifferentQ94D[continue["QueryCodeMap"],stop["QueryCodeMap"]],
"RejectTraceDistinguishable"->DifferentQ94D[continue["RejectOriginalSequence"],stop["RejectOriginalSequence"]],
"PreDedupQueryObservationsDistinguishable"->DifferentQ94D[
continue["PreDedupQueryObservations"],stop["PreDedupQueryObservations"]],
"PostDedupQueryObservationsDistinguishable"->DifferentQ94D[
continue["PostDedupQueryObservations"],stop["PostDedupQueryObservations"]],
"GlobalAggregateDistinguishable"->DifferentQ94D[continue["GlobalVector"],stop["GlobalVector"]],
"RoleMomentAggregateDistinguishable"->DifferentQ94D[
continue["RoleMomentVector"],stop["RoleMomentVector"]],
"RoleEnhancedAggregateDistinguishable"->DifferentQ94D[
continue["RoleEnhancedVector"],stop["RoleEnhancedVector"]],
"RoleHistogramAggregateDistinguishable"->DifferentQ94D[
continue["RoleHistogramVector"],stop["RoleHistogramVector"]]|>;
diagnosis=FirstLossDiagnosis94D[flags];
Join[KeyTake[row,{"ScenarioKey","Topology","TopologyIndex","ContextPattern",
"ContextIndex","Depth","Answer"}],flags,<|
"Diagnosis"->diagnosis,
"ReferenceActionsCorrect"->And[SameQ[continue["ReferenceAction"],"Continue"],
SameQ[stop["ReferenceAction"],"Stop"]],
"RegeneratedGlobalDifferenceMatches"->SameQ[
continue["GlobalVector"]-stop["GlobalVector"],row["GlobalDifference"]],
"RegeneratedRoleMomentDifferenceMatches"->SameQ[
continue["RoleMomentVector"]-stop["RoleMomentVector"],row["RoleMomentDifference"]],
"RegeneratedRoleEnhancedDifferenceMatches"->SameQ[
continue["RoleEnhancedVector"]-stop["RoleEnhancedVector"],row["RoleEnhancedDifference"]],
"RegeneratedRoleHistogramDifferenceMatches"->SameQ[
continue["RoleHistogramVector"]-stop["RoleHistogramVector"],row["RoleHistogramDifference"]],
"CanonicalizationValid"->And[continue["CanonicalCaseExactlyBase"],
stop["CanonicalCaseExactlyBase"],continue["ContractionCountCorrect"],
stop["ContractionCountCorrect"],continue["ProtectedNodesPreserved"],
stop["ProtectedNodesPreserved"]],
"TracesValid"->And[continue["TerminatedNaturally"],stop["TerminatedNaturally"],
!continue["HitSafetyCap"],!stop["HitSafetyCap"]],
"TraceSeconds"->continue["TraceSeconds"]+stop["TraceSeconds"]|>]];

AuditDefinitionBundle94D[]:={DownValues[TraceWorldStages94D],
DownValues[PairStageAudit94D],DownValues[StageSignature94D],
DownValues[DifferentQ94D],DownValues[FirstLossDiagnosis94D]};
testDefinitionHashBefore94D=Hash[TestDefinitionBundle94D[],"SHA256","HexString"];
auditDefinitionHashBefore94D=Hash[AuditDefinitionBundle94D[],"SHA256","HexString"];
protocol94D=<|"Stage"->"S94D","Name"->"RepresentationSufficiencyAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"UsesRevealedS94CFailures"->True,"ExpectedSelectedPairs"->8,
"PipelineStages"->{"CanonicalGraph","AllRawRadiusStates","AllEncodedTokens",
"RejectTrace","PreDedupQueryObservations","PostDedupQueryObservations",
"OuterAggregates"},"CandidateFrozen"->False,"CoreMechanismChanged"->False|>;
protocolHash94D=Hash[Normal[protocol94D],"SHA256","HexString"];
Dataset[{Join[protocol94D,<|"ProtocolHash"->protocolHash94D,
"TestDefinitionHash"->testDefinitionHashBefore94D,
"AuditDefinitionHash"->auditDefinitionHashBefore94D|>]}]
'''
).strip()


evaluation = r'''
If[!TrueQ[preflightPassed94D],
Print["S94D blocked before evaluation: preflight is not True."];Abort[]];
s94cRows94D=s94cDiagnosticArtifact94D["Rows"];
zeroDifferenceRows94D=Select[s94cRows94D,And[
Total[Abs[Lookup[#,"GlobalDifference"]]]===0,
Total[Abs[Lookup[#,"RoleMomentDifference"]]]===0,
Total[Abs[Lookup[#,"RoleEnhancedDifference"]]]===0,
Total[Abs[Lookup[#,"RoleHistogramDifference"]]]===0,
Total[Abs[Lookup[#,"CombinedDifference"]]]===0]&];
pairAudits94D=PairStageAudit94D/@zeroDifferenceRows94D;
diagnosisCounts94D=Counts[Lookup[pairAudits94D,"Diagnosis"]];
stageSummary94D=Map[Function[key,<|"StageFlag"->key,
"DistinguishablePairs"->Count[Lookup[pairAudits94D,key],True],
"Pairs"->Length[pairAudits94D]|>],{
"CanonicalGraphDistinguishable","AllRawStatesDistinguishable",
"QueryRawStatesDistinguishable","AllEncodedTokensDistinguishable",
"QueryEncodedTokensDistinguishable","RejectTraceDistinguishable",
"PreDedupQueryObservationsDistinguishable",
"PostDedupQueryObservationsDistinguishable",
"GlobalAggregateDistinguishable","RoleMomentAggregateDistinguishable",
"RoleEnhancedAggregateDistinguishable","RoleHistogramAggregateDistinguishable"}];
auditValidityPassed94D=And[
SameQ[Length[s94cRows94D],416],SameQ[Length[zeroDifferenceRows94D],8],
SameQ[Length[pairAudits94D],8],
And@@Lookup[pairAudits94D,"ReferenceActionsCorrect"],
And@@Lookup[pairAudits94D,"RegeneratedGlobalDifferenceMatches"],
And@@Lookup[pairAudits94D,"RegeneratedRoleMomentDifferenceMatches"],
And@@Lookup[pairAudits94D,"RegeneratedRoleEnhancedDifferenceMatches"],
And@@Lookup[pairAudits94D,"RegeneratedRoleHistogramDifferenceMatches"],
And@@Lookup[pairAudits94D,"CanonicalizationValid"],
And@@Lookup[pairAudits94D,"TracesValid"]];
Column[{Dataset[pairAudits94D],Dataset[stageSummary94D],Dataset[{<|
"SelectedPairs"->Length[zeroDifferenceRows94D],
"DiagnosisCounts"->diagnosisCounts94D,
"AuditValidityPassed"->auditValidityPassed94D|>}]}]
'''.strip()


audit = r'''
If[!TrueQ[preflightPassed94D],
Print["S94D blocked before certificate: preflight is not True."];Abort[]];
modelHashAfter94D=Hash[Normal[frozen75D],"SHA256","HexString"];
k33ObjectHashAfter94D=Hash[Normal[frozenCandidate86E],"SHA256","HexString"];
baseDecoderObjectHashAfter94D=Hash[Normal[baseDecoderRaw94D],"SHA256","HexString"];
pairDecoderObjectHashAfter94D=Hash[Normal[pairDecoderRaw94D],"SHA256","HexString"];
coreHashAfter94D=Hash[CoreDefinitionBundle94D[],"SHA256","HexString"];
canonicalizerHashAfter94D=Hash[{DownValues[FindPrivateDiamond79B],
DownValues[CanonicalizePrivateDiamonds79B],DownValues[CanonicalCase79B]},
"SHA256","HexString"];
interventionHashAfter94D=Hash[{DownValues[LocalMediatorSources82],
DownValues[FullSemanticPatch82],DownValues[LocalMediatorPatch82],
DownValues[ReferenceAction82]},"SHA256","HexString"];
topologyPrimitiveHashAfter94D=Hash[{DownValues[DiamondIn72],
DownValues[DoubleDiamondIn79],DownValues[HierarchicalDiamondIn80]},
"SHA256","HexString"];
baseRuntimeDefinitionHashAfter94D=Hash[
TCCTFrozenFeatureDefinitionBundleS87D[],"SHA256","HexString"];
pairRuntimeDefinitionHashAfter94D=Hash[
PairRuntimeDefinitionBundle94D[],"SHA256","HexString"];
testDefinitionHashAfter94D=Hash[TestDefinitionBundle94D[],"SHA256","HexString"];
auditDefinitionHashAfter94D=Hash[AuditDefinitionBundle94D[],"SHA256","HexString"];
fileHashesAfter94D=FileSHA256Hex94D/@requiredFiles94D;
integrityPassed94D=And[
SameQ[modelHashBefore94D,modelHashAfter94D],
SameQ[k33ObjectHashBefore94D,k33ObjectHashAfter94D],
SameQ[baseDecoderObjectHashBefore94D,baseDecoderObjectHashAfter94D],
SameQ[pairDecoderObjectHashBefore94D,pairDecoderObjectHashAfter94D],
SameQ[coreHashBefore94D,coreHashAfter94D],
SameQ[canonicalizerHashBefore94D,canonicalizerHashAfter94D],
SameQ[interventionHashBefore94D,interventionHashAfter94D],
SameQ[topologyPrimitiveHashBefore94D,topologyPrimitiveHashAfter94D],
SameQ[baseRuntimeDefinitionHashBefore94D,baseRuntimeDefinitionHashAfter94D],
SameQ[pairRuntimeDefinitionHashBefore94D,pairRuntimeDefinitionHashAfter94D],
SameQ[testDefinitionHashBefore94D,testDefinitionHashAfter94D],
SameQ[auditDefinitionHashBefore94D,auditDefinitionHashAfter94D],
SameQ[fileHashesBefore94D,fileHashesAfter94D]];
dominantDiagnosis94D=If[Length[diagnosisCounts94D]===1,
First[Keys[diagnosisCounts94D]],"MULTIPLE_INFORMATION_LOSS_STAGES"];
resultPayload94D=<|"Stage"->"S94D","Name"->"RepresentationSufficiencyAudit",
"AuditOnly"->True,"DevelopmentOnly"->True,"BlindTest"->False,
"UsesRevealedS94CFailures"->True,"PreflightPassed"->preflightPassed94D,
"S94CFormalStatus"->"DIAGNOSTIC_ONLY_DUE_TO_PRECHECK_HASH_TYPO",
"SelectedZeroDifferencePairs"->Length[zeroDifferenceRows94D],
"StageSummary"->stageSummary94D,"PairAudits"->pairAudits94D,
"DiagnosisCounts"->diagnosisCounts94D,"DominantDiagnosis"->dominantDiagnosis94D,
"AuditValidityPassed"->auditValidityPassed94D,
"IntegrityPassed"->integrityPassed94D,
"CandidateFrozen"->False,"DynamicModulusSelected"->False,
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94D,modelHashAfter94D],
"FrozenPairDecoderChanged"->!SameQ[pairDecoderObjectHashBefore94D,pairDecoderObjectHashAfter94D],
"CoreChanged"->!SameQ[coreHashBefore94D,coreHashAfter94D],
"CanonicalizerChanged"->!SameQ[canonicalizerHashBefore94D,canonicalizerHashAfter94D],
"InterventionCoreChanged"->!SameQ[interventionHashBefore94D,interventionHashAfter94D],
"DeduplicationMechanismChanged"->!SameQ[coreHashBefore94D,coreHashAfter94D],
"UndirectedFreezeMechanismChanged"->!SameQ[coreHashBefore94D,coreHashAfter94D],
"TotalTraceSeconds"->Total@Lookup[pairAudits94D,"TraceSeconds"],
"Outcome"->If[And[TrueQ[preflightPassed94D],TrueQ[auditValidityPassed94D],
TrueQ[integrityPassed94D]],"S94D_AUDIT_PASS_LOSS_STAGE_IDENTIFIED",
"S94D_INVALID_AUDIT_DO_NOT_INTERPRET"],
"SuggestedNextStage"->Switch[dominantDiagnosis94D,
"OUTER_AGGREGATION_LOSS","S94E_REDESIGN_OUTER_AGGREGATION_ONLY",
"DEDUPLICATION_INFORMATION_LOSS","S94E_DEDUPLICATION_SEMANTICS_REVIEW",
"QUERY_OBSERVATION_SCOPE_LOSS","S94E_QUERY_SCOPE_REPRESENTATION_REVIEW",
"FROZEN_ENCODER_COMPRESSION_LOSS","S94E_ENCODER_CAPACITY_REVIEW_NO_CORE_CHANGE",
"CORE_REJECT_TRACE_SELECTION_LOSS","S94E_CORE_MECHANISM_LIMITATION_REVIEW",
"RAW_RADIUS_STATE_COLLAPSE","S94E_RAW_STATE_RADIUS_LIMITATION_REVIEW",
_,"S94E_PAIR_SPECIFIC_LOSS_ANALYSIS"]|>;
resultHash94D=Hash[Normal[resultPayload94D],"SHA256","HexString"];
certificate94D=Append[resultPayload94D,"ResultHash"->resultHash94D];
certificateExportResult94D=Quiet@Check[
Export[resultCertificatePath94D,certificate94D,"RawJSON"],$Failed];
certificateExported94D=StringQ[certificateExportResult94D]&&
FileExistsQ[resultCertificatePath94D]&&FileByteCount[resultCertificatePath94D]>0;
Column[{Dataset[{certificate94D}],Dataset[{<|
"CertificateExported"->certificateExported94D,
"CertificatePath"->resultCertificatePath94D,
"CertificateBytes"->If[FileExistsQ[resultCertificatePath94D],
FileByteCount[resultCertificatePath94D],0],
"PreflightPassed"->preflightPassed94D,"AuditValidityPassed"->auditValidityPassed94D,
"IntegrityPassed"->integrityPassed94D,"CoreChanged"->certificate94D["CoreChanged"],
"Outcome"->certificate94D["Outcome"]|>}]}]
'''.strip()


cells = [core, locks.strip(), definitions, evaluation, audit]
WL.write_text(
    "\n\n".join(
        f"(* S94D CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells, 1)
    )
    + "\n",
    encoding="utf-8",
)
PREFLIGHT_WL.write_text(
    "\n\n".join(
        f"(* S94D PREFLIGHT CELL {index} *)\n{cell}"
        for index, cell in enumerate(cells[:3], 1)
    )
    + "\n",
    encoding="utf-8",
)
NB.write_text(
    json.dumps(
        notebook(
            cells,
            "TCCT S94D — Representation Sufficiency Audit",
            "Audit-only replay of the eight revealed S94C zero-difference pairs. "
            "No training, tuning, freezing, or core modification is performed.",
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
            "TCCT S94D — Preflight",
            "Corrected immutable-input lock and definitions only; no failure pair is replayed.",
        ),
        ensure_ascii=False,
        indent=1,
    ),
    encoding="utf-8",
)
LAUNCHER.write_text(
    "@echo off\nchcp 65001 >nul\n"
    'start "" "http://localhost:8889/lab/tree/'
    'TCCT_S94D_RepresentationSufficiencyAudit.ipynb"\nexit /b 0\n',
    encoding="utf-8",
)
precommit = {
    "Stage": "S94D",
    "Name": "RepresentationSufficiencyAudit",
    "AuditOnly": True,
    "BlindTest": False,
    "ExpectedSelectedPairs": 8,
    "CandidateFrozen": False,
    "CoreMechanismChanged": False,
    "CorrectedS94BCertificateSHA256":
        "6b3c44566c80c88495f2a322a0763b7a188383445b554eefc30e7fa90b4e461f",
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
