"""Audit natural cardinality matching for uniform-action revealed S90 worlds."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
RUN_LOG = ROOT / "TCCT_S92_UniformActionCardinalityProbe_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    token = server_token()
    kernel_id = idle_kernel(token)
    session = uuid.uuid4().hex
    ws = websocket.create_connection(
        f"ws://localhost:8888/api/kernels/{kernel_id}/channels?token={token}",
        timeout=2,
        origin="http://localhost:8888",
        http_proxy_host=None,
        http_proxy_port=None,
    )
    code = r'''
ClearAll[UniformActionProbeWorld92];
UniformActionProbeWorld92[target_String,answer_Integer]:=Module[
{base,topologyCase,canonicalization,canonicalCase,trace,levels,pack,
vertexList,packedNodes,observations,originalNode,pair,roleInfo,vector},
base=Case90[73,answer,target];
topologyCase=TopologyTransform90["TripleSerialDiamondIn",base];
canonicalization=CanonicalizePrivateDiamonds79B[topologyCase];
canonicalCase=canonicalization["Case"];
trace=RejectTrace78[canonicalCase];levels=SigLevels61[canonicalCase,3];
pack=Pack60[canonicalCase];vertexList=pack[[12]];
packedNodes=If[Length[trace["Rejects"]]===0,{},
DeleteDuplicates[trace["Rejects"][[All,2]]]];
observations=Map[Function[packedNode,
originalNode=vertexList[[packedNode]];
pair={Lookup[levels[[3]],packedNode],Lookup[levels[[4]],packedNode]};
roleInfo=NodeRole90[originalNode,canonicalCase,answer];
<|"QueryBranchRelated"->roleInfo["QueryBranchRelated"],
"Code"->EncodePair90[pair]|>],packedNodes];
vector=TCCTWorldVectorS87D[<|"Observations"->observations|>];
<|"Target"->target,"Answer"->answer,
"ReferenceAction"->ReferenceAction90[canonicalCase],
"Cardinality"->vector[[{1,2,18}]],"CodeVector"->vector,
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,base],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"]|>
];
uniformProbeRows92=Flatten[Table[
UniformActionProbeWorld92[target,answer],
{target,{"Continue","Stop"}},{answer,Range[9]}]];
InputForm[<|
"Worlds"->Length[uniformProbeRows92],
"ReferenceActionsCorrect"->Count[uniformProbeRows92,row_/;
SameQ[row["ReferenceAction"],row["Target"]]],
"CanonicalCaseExactlyBase"->Count[uniformProbeRows92,row_/;TrueQ[row["CanonicalCaseExactlyBase"]]],
"TerminatedNaturally"->Count[uniformProbeRows92,row_/;TrueQ[row["TerminatedNaturally"]]],
"HitSafetyCap"->Count[uniformProbeRows92,row_/;TrueQ[row["HitSafetyCap"]]],
"CardinalitiesByTarget"->Association@KeyValueMap[
Function[{target,rows},target->Counts[Lookup[rows,"Cardinality"]]],
GroupBy[uniformProbeRows92,#1["Target"]&]],
"EveryWorldCardinalityOneOneZero"->And@@Map[
SameQ[#1["Cardinality"],{1,1,0}]&,uniformProbeRows92],
"OppositeTargetsHaveDifferentFullVectorsPerAnswer"->And@@Table[
UnsameQ[
SelectFirst[uniformProbeRows92,SameQ[#1["Target"],"Continue"]&&SameQ[#1["Answer"],a]&]["CodeVector"],
SelectFirst[uniformProbeRows92,SameQ[#1["Target"],"Stop"]&&SameQ[#1["Answer"],a]&]["CodeVector"]
],{a,Range[9]}]
|>]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=600)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    payload = {
        "stage": "S92-REVEALED-S90-UNIFORM-ACTION-CARDINALITY-PROBE",
        "frozen_model_predictions_run": False,
        "s92_cases_run": False,
        "kernel_id": kernel_id,
        "probe_text": "\n".join(result["outputs"]),
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
