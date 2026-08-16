"""Audit a uniform graph-level cardinality patch on already-revealed S90 cases."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
RUN_LOG = ROOT / "TCCT_S92_NeutralPatchProbe_RunLog.json"


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
ClearAll[UniformSafeCorrectPatchProbe92,CardinalityProbeWorld92];
UniformSafeCorrectPatchProbe92[c_List]:=Module[
{x=c[[1]],answer=c[[2]],edges,branchCount,add},
edges=x[[1]];branchCount=Length[x[[6]]];
add=Table[DirectedEdge[x[[6,i]]+1,x[[5,i]]],{i,branchCount}];
WithEdges81[c,Union[edges,add]]
];
CardinalityProbeWorld92[stopBranch_Integer,answer_Integer]:=Module[
{seed,state,patched,base,topologyCase,canonicalization,canonicalCase,
trace,levels,pack,vertexList,packedNodes,observations,originalNode,pair,roleInfo,vector},
seed=Case90[73,1,"Continue"];
state=ApplyEdgePatch81[seed,BranchStopPatch90[seed,stopBranch]];
patched=UniformSafeCorrectPatchProbe92[state];
base=SetAnswer90[patched,answer];
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
"ObservationCount"->vector[[1]],"DistinctCodeCount"->vector[[2]],
"PairCount"->vector[[18]],"Cardinality"->vector[[{1,2,18}]],
"CanonicalCaseExactlyBase"->SameQ[canonicalCase,base],
"TerminatedNaturally"->trace["TerminatedNaturally"],
"HitSafetyCap"->trace["HitSafetyCap"]|>
];
probeRows92=Flatten[Table[CardinalityProbeWorld92[s,a],{s,Range[9]},{a,Range[9]}]];
InputForm[<|
"Worlds"->Length[probeRows92],
"ReferenceActionsCorrect"->Count[probeRows92,row_/;
SameQ[row["ReferenceAction"],row["Target"]]],
"CanonicalCaseExactlyBase"->Count[probeRows92,row_/;TrueQ[row["CanonicalCaseExactlyBase"]]],
"TerminatedNaturally"->Count[probeRows92,row_/;TrueQ[row["TerminatedNaturally"]]],
"HitSafetyCap"->Count[probeRows92,row_/;TrueQ[row["HitSafetyCap"]]],
"CardinalitiesByTarget"->Association@KeyValueMap[
Function[{target,rows},target->Counts[Lookup[rows,"Cardinality"]]],
GroupBy[probeRows92,#1["Target"]&]],
"ExactDistributionMatch"->SameQ@@Values[Association@KeyValueMap[
Function[{target,rows},target->Counts[Lookup[rows,"Cardinality"]]],
GroupBy[probeRows92,#1["Target"]&]]]
|>]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=900)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    payload = {
        "stage": "S92-REVEALED-S90-NEUTRAL-PATCH-PROBE",
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
