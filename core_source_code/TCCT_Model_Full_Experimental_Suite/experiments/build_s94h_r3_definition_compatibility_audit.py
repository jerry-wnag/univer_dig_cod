"""Build a read-only audit comparing CLI and Jupyter S94H definition hashes."""

from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94H_CheckpointWorker_R3.wl"
OUTPUT = ROOT / "TCCT_S94H_R3_DefinitionCompatibilityAudit.wl"

text = SOURCE.read_text(encoding="utf-8")
prefix = text.split("(* S94H R3 WORKER *)", 1)[0]
prefix = prefix.replace(
    'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_IndependentFullQueryConfirmation.json";',
    'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_R3_IndependentFullQueryConfirmation.json";',
)

audit = r'''
(* S94H R3 DEFINITION COMPATIBILITY AUDIT *)
scenarioIndexAudit94H=3;
scenarioAudit94H=confirmationScenarios94H[[scenarioIndexAudit94H]];
checkpointPathAudit94H=FileNameJoin[{
"E:/engine_wolf/TCCT_S94H_R3_Checkpoints","scenario_03.wxf"}];
storedAudit94H=Quiet@Check[Import[checkpointPathAudit94H,"WXF"],$Failed];
If[!AssociationQ[storedAudit94H],
Print["S94H R3 definition compatibility audit blocked: checkpoint 3 unavailable."];Abort[]];

{elapsedAudit94H,recomputedPairsAudit94H}=AbsoluteTiming[Table[
ConfirmationPair94H[scenarioAudit94H["Topology"],scenarioAudit94H["TopologyIndex"],
scenarioAudit94H["Context"],scenarioAudit94H["ContextIndex"],
scenarioAudit94H["Depth"],scenarioAudit94H["BranchCount"],answer],
{answer,scenarioAudit94H["BranchCount"]}]];

semanticPairsAudit94H[pairs_List]:=KeyDrop[#, {"TraceSeconds"}]&/@pairs;
semanticPairOutputsExact94H=SameQ[
semanticPairsAudit94H[storedAudit94H["Pairs"]],
semanticPairsAudit94H[recomputedPairsAudit94H]];
storedCheckpointHashValid94H=SameQ[storedAudit94H["CheckpointHash"],
Hash[Normal@KeyDrop[storedAudit94H,{"CheckpointHash"}],"SHA256","HexString"]];
compatibilityPassed94H=And[
storedCheckpointHashValid94H,
SameQ[storedAudit94H["CandidateHash"],candidateObjectHash94H],
SameQ[storedAudit94H["CandidateFileHash"],candidateFileHash94H],
SameQ[storedAudit94H["ProtocolHash"],confirmationProtocolHash94H],
SameQ[storedAudit94H["Scenario"],scenarioAudit94H],
TrueQ[storedAudit94H["ScenarioValidityPassed"]],
semanticPairOutputsExact94H,
TrueQ[And@@Lookup[recomputedPairsAudit94H,"ReferenceActionsCorrect",False]],
TrueQ[And@@Lookup[recomputedPairsAudit94H,"WorldsValid",False]]
];

auditPayload94H=<|
"Stage"->"S94H","HarnessRevision"->3,
"Name"->"DefinitionHashFrontendCompatibilityAudit",
"AuditOnly"->True,"ScenarioIndex"->scenarioIndexAudit94H,
"StoredExecutionMode"->storedAudit94H["ExecutionMode"],
"StoredDefinitionHash"->storedAudit94H["DefinitionHash"],
"RecomputedDefinitionHash"->confirmationDefinitionHashBefore94H,
"DefinitionHashesDiffer"->UnsameQ[storedAudit94H["DefinitionHash"],
confirmationDefinitionHashBefore94H],
"CandidateHash"->candidateObjectHash94H,
"CandidateFileHash"->candidateFileHash94H,
"ProtocolHash"->confirmationProtocolHash94H,
"StoredCheckpointHashValid"->storedCheckpointHashValid94H,
"SemanticPairOutputsExactIgnoringTiming"->semanticPairOutputsExact94H,
"PairsCompared"->Length[recomputedPairsAudit94H],
"RecomputeSeconds"->elapsedAudit94H,
"CompatibilityPassed"->compatibilityPassed94H,
"CoreChanged"->False,"RulesChanged"->False,
"DeduplicationMechanismChanged"->False,
"UndirectedFreezeMechanismChanged"->False
|>;
auditHash94H=Hash[Normal[auditPayload94H],"SHA256","HexString"];
auditRecord94H=Append[auditPayload94H,"AuditHash"->auditHash94H];
auditOutputPath94H=FileNameJoin[{Directory[],
"TCCT_S94H_R3_DefinitionCompatibilityAudit.json"}];
Export[auditOutputPath94H,auditRecord94H,"RawJSON"];
Print[InputForm[auditRecord94H]];
Quit[];
'''.strip()

OUTPUT.write_text(prefix + "\n\n" + audit + "\n", encoding="utf-8")
print(OUTPUT.name, OUTPUT.stat().st_size)
