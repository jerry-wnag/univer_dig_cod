"""Audit fully symmetric side channels on revealed S90 cases only."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
RUN_LOG = ROOT / "TCCT_S92_NeutralPatchV3Probe_RunLog.json"


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
ClearAll[UniformMatchedPatchProbe92];
UniformMatchedPatchProbe92[c_List]:=Module[
{x=c[[1]],edges,branchCount,correct,wrong,dummy,m,safe,u,add},
edges=x[[1]];branchCount=Length[x[[6]]];
add=Flatten[Table[
m=x[[6,i]];safe=m+1;u=m+2;dummy=m+3;
correct=x[[5,i]];wrong=x[[5,1+Mod[i,branchCount]]];
{DirectedEdge[safe,correct],DirectedEdge[safe,dummy],
DirectedEdge[u,wrong],DirectedEdge[u,dummy]},
{i,branchCount}],1];
WithEdges81[c,Union[edges,add]]
];
probeRowsV392=Flatten[Table[
CardinalityProbeWorldV292[s,a],{s,Range[9]},{a,Range[9]}]];
cardinalityCountsV392=Association@KeyValueMap[
Function[{target,rows},target->Counts[Lookup[rows,"Cardinality"]]],
GroupBy[probeRowsV392,#1["Target"]&]];
InputForm[<|
"Worlds"->Length[probeRowsV392],
"ReferenceActionsCorrect"->Count[probeRowsV392,row_/;
SameQ[row["ReferenceAction"],row["Target"]]],
"CanonicalCaseExactlyBase"->Count[probeRowsV392,row_/;TrueQ[row["CanonicalCaseExactlyBase"]]],
"TerminatedNaturally"->Count[probeRowsV392,row_/;TrueQ[row["TerminatedNaturally"]]],
"HitSafetyCap"->Count[probeRowsV392,row_/;TrueQ[row["HitSafetyCap"]]],
"CardinalitiesByTarget"->cardinalityCountsV392,
"EveryWorldHasOneCommonCardinality"->SameQ[Length[DeleteDuplicates[
Lookup[probeRowsV392,"Cardinality"]]],1],
"ClassSupportsIdentical"->SameQ[
DeleteDuplicates[Lookup[Select[probeRowsV392,SameQ[#1["Target"],"Stop"]&],"Cardinality"]],
DeleteDuplicates[Lookup[Select[probeRowsV392,SameQ[#1["Target"],"Continue"]&],"Cardinality"]]
]
|>]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=900)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    payload = {
        "stage": "S92-REVEALED-S90-NEUTRAL-PATCH-V3-PROBE",
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
