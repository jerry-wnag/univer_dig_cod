"""Build a resumable Jupyter GUI for the protocol-equivalent S94H R3 run."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "TCCT_S94H_IndependentFullQueryConfirmation.wl"
MERGE_SOURCE = ROOT / "TCCT_S94H_CheckpointMerge_R3.wl"
NOTEBOOK = ROOT / "TCCT_S94H_R3_Resumable_GUI_Compat.ipynb"
LAUNCHER = ROOT / "Start_TCCT_S94H_R3_Resumable_GUI.cmd"
INTERFACE_RECORD = ROOT / "TCCT_S94H_R3_GUI_InterfaceRecord.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_cell(code: str, cell_id: str) -> dict:
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {},
        "execution_count": None,
        "outputs": [],
        "source": [line + "\n" for line in code.splitlines()],
    }


source_parts = re.split(
    r"\(\* S94H CELL \d+ \*\)\r?\n", SOURCE.read_text(encoding="utf-8")
)
if len(source_parts) != 8:
    raise SystemExit("S94H source must contain exactly seven marked cells")

# R1's invalid do-not-interpret certificate is preserved at the legacy path.
# R3 writes only to its own result path, so the two harness revisions cannot
# block or overwrite one another.
for idx, source_part in enumerate(source_parts):
    source_parts[idx] = source_part.replace(
        'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_IndependentFullQueryConfirmation.json";',
        'resultCertificatePath94H="E:/engine_wolf/TCCT_S94H_R3_IndependentFullQueryConfirmation.json";',
    )

merge_text = MERGE_SOURCE.read_text(encoding="utf-8")
scenario_marker = "(* S94H R3 SCENARIOS *)"
merge_marker = "(* S94H R3 MERGE *)"
if scenario_marker not in merge_text or merge_marker not in merge_text:
    raise SystemExit("S94H R3 merge source markers are missing")
scenario_builder = merge_text.split(scenario_marker, 1)[1].split(merge_marker, 1)[0].strip()
merge_body = merge_text.split(merge_marker, 1)[1].strip()
merge_body = merge_body.replace('"ExecutionMode"->"CheckpointedSixWorker"',
                                  '"ExecutionMode"->"CheckpointedResumableGUI"')
merge_body = merge_body.replace(
    'SameQ[obj["DefinitionHash"],confirmationDefinitionHashBefore94H]',
    'CompatibleDefinitionHashQ94H[obj["DefinitionHash"]]',
)
merge_body = merge_body.replace(
    '"CheckpointSetValidityPassed"->checkpointSetValidityPassed94H,',
    '"CheckpointSetValidityPassed"->checkpointSetValidityPassed94H,\n'
    '"DefinitionHashFrontendCompatibilityAuditPassed"->'
    'definitionHashFrontendCompatibilityAuditPassed94H,\n'
    '"CompatibleDefinitionHashes"->compatibleDefinitionHashes94H,',
)
merge_body = re.sub(r"\nQuit\[\];\s*$", "", merge_body)

checkpoint_runtime = r'''
If[!TrueQ[candidateFrozenBeforeConfirmation94H],
Print["S94H R3 GUI blocked: candidate is not frozen."];Abort[]];
checkpointDirectory94H="E:/engine_wolf/TCCT_S94H_R3_Checkpoints";
If[!DirectoryQ[checkpointDirectory94H],
Quiet@Check[CreateDirectory[checkpointDirectory94H],Null]];
If[!DirectoryQ[checkpointDirectory94H],
Print["S94H R3 GUI blocked: checkpoint directory is unavailable."];Abort[]];

definitionCompatibilityAuditPath94H=FileNameJoin[{Directory[],
"TCCT_S94H_R3_DefinitionCompatibilityAudit.json"}];
definitionCompatibilityAudit94H=Quiet@Check[
Import[definitionCompatibilityAuditPath94H,"RawJSON"],$Failed];
definitionHashFrontendCompatibilityAuditPassed94H=And[
AssociationQ[definitionCompatibilityAudit94H],
SameQ[definitionCompatibilityAudit94H["Stage"],"S94H"],
SameQ[definitionCompatibilityAudit94H["HarnessRevision"],3],
TrueQ[definitionCompatibilityAudit94H["AuditOnly"]],
TrueQ[definitionCompatibilityAudit94H["StoredCheckpointHashValid"]],
TrueQ[definitionCompatibilityAudit94H[
"SemanticPairOutputsExactIgnoringTiming"]],
TrueQ[definitionCompatibilityAudit94H["CompatibilityPassed"]],
SameQ[definitionCompatibilityAudit94H["CandidateHash"],
candidateObjectHash94H],
SameQ[definitionCompatibilityAudit94H["CandidateFileHash"],
candidateFileHash94H],
SameQ[definitionCompatibilityAudit94H["ProtocolHash"],
confirmationProtocolHash94H],
SameQ[definitionCompatibilityAudit94H["AuditHash"],
Hash[Normal@KeyDrop[definitionCompatibilityAudit94H,{"AuditHash"}],
"SHA256","HexString"]]
];
If[!TrueQ[definitionHashFrontendCompatibilityAuditPassed94H],
Print["S94H R3 GUI blocked: definition-hash compatibility audit failed."];
Abort[]];
compatibleDefinitionHashes94H=DeleteDuplicates[{
confirmationDefinitionHashBefore94H,
definitionCompatibilityAudit94H["StoredDefinitionHash"],
definitionCompatibilityAudit94H["RecomputedDefinitionHash"]
}];
CompatibleDefinitionHashQ94H[value_]:=MemberQ[
compatibleDefinitionHashes94H,value];

ClearAll[CheckpointObjectValidQ94H,RunCheckpointScenario94H,
CheckpointProgress94H];
CheckpointObjectValidQ94H[obj_,idx_Integer,scenario_Association]:=And[
AssociationQ[obj],SameQ[obj["Stage"],"S94H"],SameQ[obj["HarnessRevision"],3],
SameQ[obj["ScenarioIndex"],idx],SameQ[obj["Scenario"],scenario],
SameQ[obj["CandidateHash"],candidateObjectHash94H],
SameQ[obj["CandidateFileHash"],candidateFileHash94H],
SameQ[obj["ProtocolHash"],confirmationProtocolHash94H],
CompatibleDefinitionHashQ94H[obj["DefinitionHash"]],
SameQ[obj["PairCount"],scenario["BranchCount"]],
SameQ[obj["WorldCount"],2 scenario["BranchCount"]],
VectorQ[obj["Pairs"],AssociationQ],
SameQ[Length[obj["Pairs"]],scenario["BranchCount"]],
TrueQ[obj["ScenarioValidityPassed"]],
SameQ[obj["CheckpointHash"],Hash[Normal@KeyDrop[obj,{"CheckpointHash"}],
"SHA256","HexString"]]];

CheckpointProgress94H[]:=Module[{paths,done},
paths=FileNameJoin[{checkpointDirectory94H,
"scenario_"<>IntegerString[#,10,2]<>".wxf"}]&/@Range[24];
done=Pick[Range[24],FileExistsQ/@paths,True];
<|"Completed"->Length[done],"Expected"->24,"CompletedScenarioIndices"->done,
"RemainingScenarioIndices"->Complement[Range[24],done],
"CandidateHash"->candidateObjectHash94H,
"CandidateFileHash"->candidateFileHash94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False|>];

RunCheckpointScenario94H[idx_Integer]:=Module[
{scenario,path,existing,elapsed,pairs,validity,payload,checkpoint,
exportResult,reloaded,result},
If[!MemberQ[Range[24],idx],Return[<|"ScenarioIndex"->idx,
"Status"->"INVALID_SCENARIO_INDEX"|>]];
scenario=confirmationScenarios94H[[idx]];
path=FileNameJoin[{checkpointDirectory94H,
"scenario_"<>IntegerString[idx,10,2]<>".wxf"}];
If[FileExistsQ[path]&&FileByteCount[path]>0,
existing=Quiet@Check[Import[path,"WXF"],$Failed];
If[TrueQ[CheckpointObjectValidQ94H[existing,idx,scenario]],
Return[<|"ScenarioIndex"->idx,"Scenario"->scenario,
"Status"->"VALID_CHECKPOINT_REUSED","PairCount"->existing["PairCount"],
"ElapsedSeconds"->existing["ElapsedSeconds"],
"CheckpointHash"->existing["CheckpointHash"],
"Progress"->CheckpointProgress94H[]|>],
Print["S94H R3 GUI blocked: existing checkpoint failed validation: ",path];Abort[]]];
{elapsed,pairs}=AbsoluteTiming[Table[ConfirmationPair94H[
scenario["Topology"],scenario["TopologyIndex"],scenario["Context"],
scenario["ContextIndex"],scenario["Depth"],scenario["BranchCount"],answer],
{answer,scenario["BranchCount"]}]];
validity=And[VectorQ[pairs,AssociationQ],
SameQ[Length[pairs],scenario["BranchCount"]],
And@@Lookup[pairs,"ReferenceActionsCorrect",False],
And@@Lookup[pairs,"WorldsValid",False],
And@@Map[Abs[#Score+#ReverseScore]<10^-12&,pairs]];
If[!TrueQ[validity],
Print["S94H R3 GUI blocked: scenario validity failed before export: ",idx];Abort[]];
payload=<|"Stage"->"S94H","HarnessRevision"->3,
"ExecutionMode"->"CheckpointedResumableGUI","ScenarioIndex"->idx,
"Scenario"->scenario,"Pairs"->pairs,"PairCount"->Length[pairs],
"WorldCount"->2 Length[pairs],"ElapsedSeconds"->elapsed,
"ScenarioValidityPassed"->validity,"CandidateHash"->candidateObjectHash94H,
"CandidateFileHash"->candidateFileHash94H,
"ProtocolHash"->confirmationProtocolHash94H,
"DefinitionHash"->confirmationDefinitionHashBefore94H,
"CandidateSearchPerformed"->False,"CandidateReexported"->False|>;
checkpoint=Append[payload,"CheckpointHash"->
Hash[Normal[payload],"SHA256","HexString"]];
exportResult=Quiet@Check[Export[path,checkpoint,"WXF"],$Failed];
If[!StringQ[exportResult]||!FileExistsQ[path]||FileByteCount[path]<=0,
Print["S94H R3 GUI blocked: checkpoint export failed: ",idx];Abort[]];
reloaded=Quiet@Check[Import[path,"WXF"],$Failed];
If[!TrueQ[CheckpointObjectValidQ94H[reloaded,idx,scenario]],
Print["S94H R3 GUI blocked: checkpoint reload validation failed: ",idx];Abort[]];
result=<|"ScenarioIndex"->idx,"Scenario"->scenario,
"Status"->"CHECKPOINT_EXPORTED","PairCount"->Length[pairs],
"ElapsedSeconds"->elapsed,"CheckpointHash"->checkpoint["CheckpointHash"],
"Progress"->CheckpointProgress94H[]|>;
result];

Dataset[{CheckpointProgress94H[]}]
'''.strip()

cells: list[dict] = [
    {
        "cell_type": "markdown",
        "id": "s94h-r3-gui-intro",
        "metadata": {},
        "source": [
            "# TCCT S94H R3 - Resumable Independent Confirmation (Compatibility Fix)\n",
            "\n",
            "请选择 **Kernel → Restart Kernel and Run All Cells**。\n",
            "\n",
            "每个场景完成后立即保存。已经完成的检查点会自动复用；断网、关闭页面或重启后可继续。",
            "最后一格只在 24 个检查点全部通过哈希和完整性验证后才导出正式证书。\n",
            "\n",
            "兼容性修复仅处理 Wolfram 命令行与 Jupyter 的定义哈希差异；已通过同场景 9/9 语义复算审计。\n",
            "本界面不搜索候选、不重新训练、不重新导出冻结候选，也不修改核心机制、规则、去重或无向冻结。\n",
        ],
    }
]

for idx in range(1, 6):
    cells.append(code_cell(source_parts[idx].strip(), f"s94h-r3-setup-{idx}"))
cells.append(code_cell(scenario_builder + "\n\n" + checkpoint_runtime,
                       "s94h-r3-checkpoint-runtime"))
for idx in range(1, 25):
    cells.append(code_cell(
        f'Dataset[{{RunCheckpointScenario94H[{idx}]}}]',
        f"s94h-r3-scenario-{idx:02d}",
    ))
cells.append(code_cell(merge_body, "s94h-r3-final-merge"))

notebook = {
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
NOTEBOOK.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")

LAUNCHER.write_text(
    '@echo off\nchcp 65001 >nul\n'
    'start "" "http://127.0.0.1:8894/lab/tree/TCCT_S94H_R3_Resumable_GUI_Compat.ipynb"\n'
    'exit /b 0\n',
    encoding="utf-8",
)

record = {
    "Stage": "S94H",
    "HarnessRevision": 3,
    "Interface": "ResumableJupyterGUI",
    "SemanticProtocolChanged": False,
    "ExpectedScenarios": 24,
    "ExpectedPairs": 312,
    "ExpectedWorlds": 624,
    "CheckpointReuseAllowedOnlyAfterFullValidation": True,
    "CandidateSearchAllowed": False,
    "CandidateReexportAllowed": False,
    "CoreChangeAllowed": False,
    "FrozenCandidateFileSHA256":
        "8cbf7184200c6a04072f9b375af3137534dc3764bff7a32bf57db4a320187e1e",
    "NotebookSHA256": sha(NOTEBOOK),
}
INTERFACE_RECORD.write_text(json.dumps(record, indent=2), encoding="utf-8")

for path in (NOTEBOOK, LAUNCHER, INTERFACE_RECORD):
    print(path.name, path.stat().st_size, sha(path))
