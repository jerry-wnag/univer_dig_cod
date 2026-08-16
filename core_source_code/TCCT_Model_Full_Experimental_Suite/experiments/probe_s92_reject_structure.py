"""Reveal which graph nodes create the S90 cardinality shortcut.

This is an audit of already-revealed S90 mechanics.  It runs no S92 case and
writes no Wolfram result certificate.
"""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S90_InterventionAlgebraBlind.ipynb"
RUN_LOG = ROOT / "TCCT_S92_RejectStructureProbe_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(cells) < 3:
        raise RuntimeError("S90 notebook is missing its setup cells")
    preflight = cells[1].replace(
        '"E:/engine_wolf/TCCT_S90_BlindResultCertificate.json"',
        'FileNameJoin[{Directory[],"TCCT_S92_Nonexistent_Probe_Result.json"}]',
    )
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
    results = []
    try:
        for number, code in enumerate((cells[0], preflight, cells[2]), 1):
            result = execute(ws, session, code, timeout_seconds=300)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"setup cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''
ClearAll[RejectNodeProbe92];
RejectNodeProbe92[target_String,answer_Integer]:=Module[
{base,topologyCase,canonicalCase,trace,pack,levels,vertexList,rows},
base=Case90[73,answer,target];
topologyCase=TopologyTransform90["TripleSerialDiamondIn",base];
canonicalCase=CanonicalCase79B[topologyCase];
trace=RejectTrace78[canonicalCase];
pack=Pack60[canonicalCase];levels=SigLevels61[canonicalCase,3];
vertexList=pack[[12]];
rows=Map[Function[reject,Module[{packed,original,role},
packed=reject[[2]];original=vertexList[[packed]];
role=NodeRole90[original,canonicalCase,answer];
<|"Round"->reject[[1]],"PackedNode"->packed,"OriginalNode"->original,
"Role"->role["Role"],"QueryBranchRelated"->role["QueryBranchRelated"],
"InDegree"->pack[[2,packed]],"OutDegree"->pack[[3,packed]],
"Level2"->Lookup[levels[[3]],packed],"Level3"->Lookup[levels[[4]],packed],
"Code"->EncodePair90[{Lookup[levels[[3]],packed],Lookup[levels[[4]],packed]}]
|>]],trace["Rejects"]];
<|"Target"->target,"Answer"->answer,"ReferenceAction"->ReferenceAction90[canonicalCase],
"RejectCount"->Length[rows],"Rows"->rows|>
];
ClearAll[RejectStateProbe92];
RejectStateProbe92[stopBranch_Integer,answer_Integer]:=Module[
{seed,state,base,topologyCase,canonicalCase,trace,pack,levels,vertexList,rows},
seed=Case90[73,1,"Continue"];
state=ApplyEdgePatch81[seed,BranchStopPatch90[seed,stopBranch]];
base=SetAnswer90[state,answer];
topologyCase=TopologyTransform90["TripleSerialDiamondIn",base];
canonicalCase=CanonicalCase79B[topologyCase];
trace=RejectTrace78[canonicalCase];pack=Pack60[canonicalCase];
levels=SigLevels61[canonicalCase,3];vertexList=pack[[12]];
rows=Map[Function[reject,Module[{packed,original,role},
packed=reject[[2]];original=vertexList[[packed]];
role=NodeRole90[original,canonicalCase,answer];
<|"Round"->reject[[1]],"OriginalNode"->original,"Role"->role["Role"],
"QueryBranchRelated"->role["QueryBranchRelated"],
"InDegree"->pack[[2,packed]],"OutDegree"->pack[[3,packed]],
"Code"->EncodePair90[{Lookup[levels[[3]],packed],Lookup[levels[[4]],packed]}]|>
]],trace["Rejects"]];
<|"StopBranch"->stopBranch,"Answer"->answer,
"Target"->If[SameQ[stopBranch,answer],"Stop","Continue"],
"ReferenceAction"->ReferenceAction90[canonicalCase],
"AllRejectCount"->Length[rows],
"QueryRejectCount"->Count[rows,row_/;TrueQ[row["QueryBranchRelated"]]],
"Rows"->rows|>
];
InputForm[{
RejectNodeProbe92["Continue",1],RejectNodeProbe92["Stop",1],
RejectNodeProbe92["Continue",2],RejectNodeProbe92["Stop",2],
RejectStateProbe92[1,1],RejectStateProbe92[1,2]
}]
''',
            timeout_seconds=300,
        )
    finally:
        ws.close()
    if probe["status"] != "ok" or probe["errors"]:
        raise RuntimeError(f"probe failed: {probe}")
    payload = {
        "stage": "S92-REVEALED-S90-STRUCTURE-PROBE",
        "s92_cases_run": False,
        "result_certificate_created": False,
        "kernel_id": kernel_id,
        "probe_text": "\n".join(probe["outputs"]),
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
