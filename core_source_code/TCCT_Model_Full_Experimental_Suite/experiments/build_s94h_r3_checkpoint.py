"""Build checkpointed, protocol-equivalent S94H R3 worker and merge scripts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94H_IndependentFullQueryConfirmation.wl"
WORKER = ROOT / "TCCT_S94H_CheckpointWorker_R3.wl"
MERGE = ROOT / "TCCT_S94H_CheckpointMerge_R3.wl"
REVISION = ROOT / "TCCT_S94H_HarnessRevision3.json"
R2_REVISION = ROOT / "TCCT_S94H_HarnessRevision2.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


text = SOURCE.read_text(encoding="utf-8")
parts = re.split(r"\(\* S94H CELL \d+ \*\)\r?\n", text)
if len(parts) != 8:
    raise SystemExit("S94H source must contain exactly seven marked cells")

# Cells 1-5 contain the archived core, all input/hash locks, candidate recovery,
# and confirmation definitions.  Cells 6-7 are replaced only at the execution
# layer; their semantic protocol and pass thresholds are preserved below.
prefix = "\n\n".join(
    f"(* S94H R3 PREFIX CELL {i} *)\n{parts[i].strip()}" for i in range(1, 6)
)

scenario_builder = r'''
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
Print["S94H R3 blocked: confirmation scenario shape is invalid."];Abort[]];
'''.strip()

worker_body = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H R3 worker blocked: candidate is not frozen."];Abort[]];
workerIndex94H=Quiet@Check[ToExpression[Last[$CommandLine]],$Failed];
If[!IntegerQ[workerIndex94H]||!MemberQ[Range[0,6],workerIndex94H],
Print["S94H R3 worker requires an integer worker index from 0 through 6."];Abort[]];
workerCount94H=6;
scenarioIndices94H=If[workerIndex94H===0,{1},Range[workerIndex94H,24,workerCount94H]];
checkpointDirectory94H="E:/engine_wolf/TCCT_S94H_R3_Checkpoints";
If[!DirectoryQ[checkpointDirectory94H],
Quiet@Check[CreateDirectory[checkpointDirectory94H],Null]];
If[!DirectoryQ[checkpointDirectory94H],
Print["S94H R3 worker blocked: checkpoint directory is unavailable."];Abort[]];

ClearAll[CheckpointObjectValidQ94H];
CheckpointObjectValidQ94H[obj_,idx_Integer,scenario_Association]:=And[
AssociationQ[obj],SameQ[obj["Stage"],"S94H"],SameQ[obj["HarnessRevision"],3],
SameQ[obj["ScenarioIndex"],idx],SameQ[obj["Scenario"],scenario],
SameQ[obj["CandidateHash"],candidateObjectHash94H],
SameQ[obj["CandidateFileHash"],candidateFileHash94H],
SameQ[obj["ProtocolHash"],confirmationProtocolHash94H],
SameQ[obj["DefinitionHash"],confirmationDefinitionHashBefore94H],
SameQ[obj["PairCount"],scenario["BranchCount"]],
SameQ[obj["WorldCount"],2 scenario["BranchCount"]],
VectorQ[obj["Pairs"],AssociationQ],
SameQ[Length[obj["Pairs"]],scenario["BranchCount"]],
TrueQ[obj["ScenarioValidityPassed"]],
SameQ[obj["CheckpointHash"],Hash[Normal@KeyDrop[obj,{"CheckpointHash"}],
"SHA256","HexString"]]];

Do[
scenario94H=confirmationScenarios94H[[scenarioIndex94H]];
checkpointPath94H=FileNameJoin[{checkpointDirectory94H,
"scenario_"<>IntegerString[scenarioIndex94H,10,2]<>".wxf"}];
If[FileExistsQ[checkpointPath94H]&&FileByteCount[checkpointPath94H]>0,
existingCheckpoint94H=Quiet@Check[Import[checkpointPath94H,"WXF"],$Failed];
If[!TrueQ[CheckpointObjectValidQ94H[existingCheckpoint94H,scenarioIndex94H,scenario94H]],
Print["S94H R3 worker blocked: existing checkpoint failed validation: ",checkpointPath94H];Abort[]];
Print[<|"Worker"->workerIndex94H,"ScenarioIndex"->scenarioIndex94H,
"Status"->"VALID_CHECKPOINT_REUSED","PairCount"->existingCheckpoint94H["PairCount"]|>],
{scenarioElapsed94H,scenarioPairs94H}=AbsoluteTiming[Table[
ConfirmationPair94H[scenario94H["Topology"],scenario94H["TopologyIndex"],
scenario94H["Context"],scenario94H["ContextIndex"],scenario94H["Depth"],
scenario94H["BranchCount"],answer],{answer,scenario94H["BranchCount"]}]];
scenarioValidity94H=And[VectorQ[scenarioPairs94H,AssociationQ],
SameQ[Length[scenarioPairs94H],scenario94H["BranchCount"]],
And@@Lookup[scenarioPairs94H,"ReferenceActionsCorrect",False],
And@@Lookup[scenarioPairs94H,"WorldsValid",False],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,scenarioPairs94H]];
If[!TrueQ[scenarioValidity94H],
Print["S94H R3 worker blocked: scenario validity failed before checkpoint export: ",
scenarioIndex94H];Abort[]];
checkpointPayload94H=<|"Stage"->"S94H","HarnessRevision"->3,
"ExecutionMode"->"CheckpointedSixWorker","ScenarioIndex"->scenarioIndex94H,
"Scenario"->scenario94H,"Pairs"->scenarioPairs94H,
"PairCount"->Length[scenarioPairs94H],"WorldCount"->2 Length[scenarioPairs94H],
"ElapsedSeconds"->scenarioElapsed94H,"ScenarioValidityPassed"->scenarioValidity94H,
"CandidateHash"->candidateObjectHash94H,"CandidateFileHash"->candidateFileHash94H,
"ProtocolHash"->confirmationProtocolHash94H,
"DefinitionHash"->confirmationDefinitionHashBefore94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False|>;
checkpoint94H=Append[checkpointPayload94H,"CheckpointHash"->
Hash[Normal[checkpointPayload94H],"SHA256","HexString"]];
checkpointExport94H=Quiet@Check[Export[checkpointPath94H,checkpoint94H,"WXF"],$Failed];
checkpointReload94H=If[StringQ[checkpointExport94H],
Quiet@Check[Import[checkpointPath94H,"WXF"],$Failed],$Failed];
If[!TrueQ[CheckpointObjectValidQ94H[checkpointReload94H,scenarioIndex94H,scenario94H]],
Print["S94H R3 worker blocked: checkpoint reload validation failed: ",scenarioIndex94H];Abort[]];
Print[<|"Worker"->workerIndex94H,"ScenarioIndex"->scenarioIndex94H,
"Status"->"CHECKPOINT_EXPORTED","PairCount"->Length[scenarioPairs94H],
"ElapsedSeconds"->scenarioElapsed94H,"CheckpointHash"->checkpoint94H["CheckpointHash"]|>]
],{scenarioIndex94H,scenarioIndices94H}];
Print[<|"Stage"->"S94H","HarnessRevision"->3,"Worker"->workerIndex94H,
"AssignedScenarios"->scenarioIndices94H,"WorkerCompleted"->True,
"CandidateHash"->candidateObjectHash94H,"CandidateFileHash"->candidateFileHash94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False|>];
Quit[];
'''.strip()

merge_body = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H R3 merge blocked: candidate is not frozen."];Abort[]];
checkpointDirectory94H="E:/engine_wolf/TCCT_S94H_R3_Checkpoints";
checkpointPaths94H=FileNameJoin[{checkpointDirectory94H,
"scenario_"<>IntegerString[#,10,2]<>".wxf"}]&/@Range[24];
If[!And@@Map[FileExistsQ[#]&&FileByteCount[#]>0&,checkpointPaths94H],
Print["S94H R3 merge blocked: one or more checkpoints are missing."];
Dataset[MapIndexed[<|"ScenarioIndex"->First[#2],"Exists"->FileExistsQ[#1],
"Bytes"->If[FileExistsQ[#1],FileByteCount[#1],0]|>&,checkpointPaths94H]];Abort[]];
checkpoints94H=Quiet@Check[Import[#,"WXF"]&/@checkpointPaths94H,$Failed];
If[!ListQ[checkpoints94H]||!VectorQ[checkpoints94H,AssociationQ],
Print["S94H R3 merge blocked: checkpoint import failed."];Abort[]];
checkpointValidationRows94H=MapThread[Function[{obj,scenario,idx},<|
"ScenarioIndex"->idx,"Association"->AssociationQ[obj],
"IndexMatched"->SameQ[obj["ScenarioIndex"],idx],
"ScenarioMatched"->SameQ[obj["Scenario"],scenario],
"CandidateMatched"->SameQ[obj["CandidateHash"],candidateObjectHash94H],
"CandidateFileMatched"->SameQ[obj["CandidateFileHash"],candidateFileHash94H],
"ProtocolMatched"->SameQ[obj["ProtocolHash"],confirmationProtocolHash94H],
"DefinitionMatched"->SameQ[obj["DefinitionHash"],confirmationDefinitionHashBefore94H],
"PairCountMatched"->SameQ[obj["PairCount"],scenario["BranchCount"]],
"ScenarioValidityPassed"->TrueQ[obj["ScenarioValidityPassed"]],
"CheckpointHashMatched"->SameQ[obj["CheckpointHash"],
Hash[Normal@KeyDrop[obj,{"CheckpointHash"}],"SHA256","HexString"]]|>],
{checkpoints94H,confirmationScenarios94H,Range[24]}];
checkpointSetValidityPassed94H=And@@Flatten[
Values[KeyDrop[#,{"ScenarioIndex"}]]&/@checkpointValidationRows94H];
If[!TrueQ[checkpointSetValidityPassed94H],
Print["S94H R3 merge blocked: checkpoint set validation failed."];
Dataset[checkpointValidationRows94H];Abort[]];

confirmationPairs94H=Flatten[Lookup[checkpoints94H,"Pairs"],1];
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
confirmationValidityPassed94H=And[TrueQ[checkpointSetValidityPassed94H],
SameQ[Length[confirmationScenarios94H],24],SameQ[Length[confirmationPairs94H],312],
SameQ[Total@Lookup[checkpoints94H,"WorldCount"],624],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["ReferenceActionsCorrect"]]],312],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["WorldsValid"]]],312],
SameQ[Count[confirmationPairs94H,p_/;TrueQ[p["ZeroScore"]]],0],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,confirmationPairs94H]];
confirmationCriterionPassed94H=And[confirmationValidityPassed94H,
confirmationAccuracy94H>=0.95,confirmationWorstGroupAccuracy94H>=0.8];

modelHashAfter94H=Hash[Normal[frozen75D],"SHA256","HexString"];
coreHashAfter94H=Hash[CoreDefinitionBundle94H[],"SHA256","HexString"];
candidateHashAfter94H=Hash[Normal@KeyDrop[candidateReloaded94H,{"CandidateHash"}],
"SHA256","HexString"];
confirmationDefinitionHashAfter94H=Hash[ConfirmationDefinitionBundle94H[],
"SHA256","HexString"];
fileHashesAfter94H=FileSHA256Hex94H/@requiredFiles94H;
integrityPassed94H=And[SameQ[modelHashBefore94H,modelHashAfter94H],
SameQ[coreHashBefore94H,coreHashAfter94H],
SameQ[fileHashesBefore94H,fileHashesAfter94H],
SameQ[candidateHashAfter94H,candidateObjectHash94H],
SameQ[confirmationDefinitionHashBefore94H,confirmationDefinitionHashAfter94H]];
resultPayload94H=<|"Stage"->"S94H","Name"->"IndependentFullQueryConfirmation",
"IndependentConfirmation"->True,"BlindTest"->False,"HarnessRevision"->3,
"HarnessCorrections"->{"ScenarioEnumerationAssociationExtraction",
"AssociationValueMappingPreservingKeys","CheckpointedProtocolEquivalentExecution"},
"ExecutionMode"->"CheckpointedSixWorker","CheckpointCount"->24,
"CheckpointSetValidityPassed"->checkpointSetValidityPassed94H,
"CandidateFrozenBeforeConfirmation"->candidateFrozenBeforeConfirmation94H,
"CandidateRecoveredAfterHarnessError"->candidateRecoveredAfterHarnessError94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False,
"CandidateHash"->candidateObjectHash94H,"CandidateFileHash"->candidateFileHash94H,
"Representation"->"SlotRaw12","Family"->"Centroid",
"Scenarios"->Length[confirmationScenarios94H],"Pairs"->Length[confirmationPairs94H],
"Worlds"->Total@Lookup[checkpoints94H,"WorldCount"],
"CorrectPairs"->Count[confirmationPairs94H,p_/;TrueQ[p["PairCorrect"]]],
"Accuracy"->confirmationAccuracy94H,
"WorstAxisGroupAccuracy"->confirmationWorstGroupAccuracy94H,
"MinimumMargin"->Min@Lookup[confirmationPairs94H,"Score"],
"ZeroScores"->Count[confirmationPairs94H,p_/;TrueQ[p["ZeroScore"]]],
"TotalScenarioSeconds"->Total@Lookup[checkpoints94H,"ElapsedSeconds"],
"AxisGroups"->axisGroups94H,
"ConfirmationValidityPassed"->confirmationValidityPassed94H,
"ConfirmationCriterionPassed"->confirmationCriterionPassed94H,
"IntegrityPassed"->integrityPassed94H,"CandidateFrozen"->True,
"CoreChanged"->!SameQ[coreHashBefore94H,coreHashAfter94H],
"OriginalFrozenModelChanged"->!SameQ[modelHashBefore94H,modelHashAfter94H],
"DeduplicationMechanismChanged"->False,"UndirectedFreezeMechanismChanged"->False,
"ProtocolHash"->confirmationProtocolHash94H,
"ConfirmationDefinitionHash"->confirmationDefinitionHashBefore94H,
"Outcome"->Which[!TrueQ[integrityPassed94H],"S94H_INTEGRITY_FAILURE",
!TrueQ[confirmationValidityPassed94H],"S94H_INVALID_CONFIRMATION",
TrueQ[confirmationCriterionPassed94H],"S94H_INDEPENDENT_CONFIRMATION_PASS",
True,"S94H_INDEPENDENT_CONFIRMATION_FAIL"]|>;
resultHash94H=Hash[Normal[resultPayload94H],"SHA256","HexString"];
certificate94H=Append[resultPayload94H,"ResultHash"->resultHash94H];
exportResult94H=Quiet@Check[Export[resultCertificatePath94H,certificate94H,"RawJSON"],$Failed];
certificateExported94H=StringQ[exportResult94H]&&FileExistsQ[resultCertificatePath94H]&&
FileByteCount[resultCertificatePath94H]>0;
If[!TrueQ[certificateExported94H],
Print["S94H R3 merge failed to export the final certificate."];Abort[]];
Print[<|"Stage"->"S94H","HarnessRevision"->3,
"CertificateExported"->certificateExported94H,
"Scenarios"->certificate94H["Scenarios"],"Pairs"->certificate94H["Pairs"],
"Worlds"->certificate94H["Worlds"],"Accuracy"->certificate94H["Accuracy"],
"WorstAxisGroupAccuracy"->certificate94H["WorstAxisGroupAccuracy"],
"ConfirmationValidityPassed"->certificate94H["ConfirmationValidityPassed"],
"ConfirmationCriterionPassed"->certificate94H["ConfirmationCriterionPassed"],
"IntegrityPassed"->certificate94H["IntegrityPassed"],
"CoreChanged"->certificate94H["CoreChanged"],
"CandidateSearchPerformed"->certificate94H["CandidateSearchPerformed"],
"CandidateReexported"->certificate94H["CandidateReexported"],
"Outcome"->certificate94H["Outcome"],"ResultHash"->resultHash94H|>];
Quit[];
'''.strip()

WORKER.write_text(prefix + "\n\n(* S94H R3 SCENARIOS *)\n" + scenario_builder +
                  "\n\n(* S94H R3 WORKER *)\n" + worker_body + "\n",
                  encoding="utf-8")
MERGE.write_text(prefix + "\n\n(* S94H R3 SCENARIOS *)\n" + scenario_builder +
                 "\n\n(* S94H R3 MERGE *)\n" + merge_body + "\n",
                 encoding="utf-8")

if not R2_REVISION.exists():
    raise SystemExit("S94H harness revision 2 record is missing")
revision = {
    "Stage": "S94H",
    "HarnessRevision": 3,
    "CorrectionScope": "ExecutionLayerOnly",
    "Reason": "Monolithic protocol-equivalent run exceeded the 30-minute execution channel limit",
    "SemanticProtocolChanged": False,
    "ExpectedScenarios": 24,
    "ExpectedPairs": 312,
    "ExpectedWorlds": 624,
    "PassAccuracy": 0.95,
    "PassWorstAxisGroupAccuracy": 0.8,
    "WorkerCount": 6,
    "CheckpointCount": 24,
    "CandidateSearchAllowed": False,
    "CandidateReexportAllowed": False,
    "CoreChangeAllowed": False,
    "FrozenCandidateObjectSHA256": "5ec0e4eb89e9bb447a1e103537c7b4a82eab0c807023cd5862048372efdb418b",
    "FrozenCandidateFileSHA256": "8cbf7184200c6a04072f9b375af3137534dc3764bff7a32bf57db4a320187e1e",
    "Revision2SHA256": sha(R2_REVISION),
    "WorkerSourceSHA256": sha(WORKER),
    "MergeSourceSHA256": sha(MERGE),
}
REVISION.write_text(json.dumps(revision, indent=2), encoding="utf-8")

for path in (WORKER, MERGE, REVISION):
    print(path.name, path.stat().st_size, sha(path))
