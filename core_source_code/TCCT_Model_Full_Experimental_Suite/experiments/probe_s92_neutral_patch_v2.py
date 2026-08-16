"""Audit the second uniform cardinality patch on revealed S90 cases only."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
RUN_LOG = ROOT / "TCCT_S92_NeutralPatchV2Probe_RunLog.json"


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
ClearAll[UniformMatchedPatchProbe92,CardinalityProbeWorldV292];
UniformMatchedPatchProbe92[c_List]:=Module[
{x=c[[1]],edges,branchCount,correct,wrong,m,safe,u,add},
edges=x[[1]];branchCount=Length[x[[6]]];
add=Flatten[Table[
m=x[[6,i]];safe=m+1;u=m+2;correct=x[[5,i]];
wrong=x[[5,1+Mod[i,branchCount]]];
{DirectedEdge[safe,correct],DirectedEdge[u,wrong]},
{i,branchCount}],1];
WithEdges81[c,Union[edges,add]]
];
CardinalityProbeWorldV292[stopBranch_Integer,answer_Integer]:=Module[
{seed,state,patched,base,topologyCase,canonicalization,canonicalCase,
trace,levels,pack,vertexList,packedNodes,observations,originalNode,pair,roleInfo,vector},
seed=Case90[73,1,"Continue"];
state=ApplyEdgePatch81[seed,BranchStopPatch90[seed,stopBranch]];
patched=UniformMatchedPatchProbe92[state];base=SetAnswer90[patched,answer];
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
<|"StopBranch"->stopBranch,"Answer"->answer,
"Target"->If[SameQ[stopBranch,answer],"Stop","Continue"],
"ReferenceAction"->ReferenceAction90[canonicalCase],
"Cardinality"->vector[[{1,2,18}]],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,base],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"]|>
];
probeRowsV292=Flatten[Table[
CardinalityProbeWorldV292[s,a],{s,Range[9]},{a,Range[9]}]];
cardinalityCountsV292=Association@KeyValueMap[
Function[{target,rows},target->Counts[Lookup[rows,"Cardinality"]]],
GroupBy[probeRowsV292,#1["Target"]&]];
InputForm[<|
"Worlds"->Length[probeRowsV292],
"ReferenceActionsCorrect"->Count[probeRowsV292,row_/;
SameQ[row["ReferenceAction"],row["Target"]]],
"CanonicalCaseExactlyBase"->Count[probeRowsV292,row_/;TrueQ[row["CanonicalCaseExactlyBase"]]],
"TerminatedNaturally"->Count[probeRowsV292,row_/;TrueQ[row["TerminatedNaturally"]]],
"HitSafetyCap"->Count[probeRowsV292,row_/;TrueQ[row["HitSafetyCap"]]],
"CardinalitiesByTarget"->cardinalityCountsV292,
"EveryWorldHasMatchedCardinality"->And@@Map[
SameQ[#1["Cardinality"],{2,2,1}]&,probeRowsV292],
"ClassSupportsIdentical"->SameQ[
DeleteDuplicates[Lookup[Select[probeRowsV292,SameQ[#1["Target"],"Stop"]&],"Cardinality"]],
DeleteDuplicates[Lookup[Select[probeRowsV292,SameQ[#1["Target"],"Continue"]&],"Cardinality"]]
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
        "stage": "S92-REVEALED-S90-NEUTRAL-PATCH-V2-PROBE",
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
