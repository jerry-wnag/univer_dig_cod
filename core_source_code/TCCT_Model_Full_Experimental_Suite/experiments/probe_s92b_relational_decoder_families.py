"""Development-only grouped-holdout probe for S92B decoder design."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "artifacts" / "TCCT_S92_FailureAuditWorlds.json"
RUN_LOG = ROOT / "TCCT_S92B_DevelopmentProbe_RunLog.json"


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
    archive_path = ARCHIVE.resolve().as_posix().replace('"', '\\"')
    code = rf'''
InputForm[Module[{{archive,rows,families,methods,score,foldResult,results}},
archive=Import["{archive_path}","RawJSON"];
rows=Lookup[archive,"Rows"];
families=<|
"RelationalCompact5"->{{3,4,11,12,13}},
"UnaryRelational15"->Range[3,17],
"AllNonCardinality24"->Complement[Range[27],{{1,2,18}}]
|>;
methods={{"DecisionTree","NearestNeighbors"}};
score[target_,prediction_]:=N[Mean[{{
Count[Pick[prediction,target,"Continue"],"Continue"]/
Max[1,Count[target,"Continue"]],
Count[Pick[prediction,target,"Stop"],"Stop"]/
Max[1,Count[target,"Stop"]]}}]];
foldResult[family_,positions_,method_,heldout_]:=Module[
{{train,test,rules,classifier,prediction,target,balanced}},
train=Select[rows,!SameQ[#1["Answer"],heldout]&];
test=Select[rows,SameQ[#1["Answer"],heldout]&];
rules=(#1["FeatureVector"][[positions]]->#1["Target"])&/@train;
SeedRandom[920000+heldout+Length[positions],Method->"MersenneTwister"];
classifier=Quiet@Check[Classify[rules,Method->method],$Failed];
If[Head[classifier]=!=ClassifierFunction,
Return[<|"Family"->family,"Method"->method,"HeldoutAnswer"->heldout,
"Valid"->False,"BalancedAccuracy"->0.,"Score"->0,"Cases"->Length[test]|>]];
prediction=Quiet@Check[classifier/@(#1["FeatureVector"][[positions]]&/@test),$Failed];
target=Lookup[test,"Target"];
If[!ListQ[prediction],prediction=ConstantArray["Invalid",Length[test]]];
<|"Family"->family,"Method"->method,"HeldoutAnswer"->heldout,
"Valid"->And@@(MemberQ[{{"Continue","Stop"}},#]&/@prediction),
"BalancedAccuracy"->score[target,prediction],
"Score"->Count[MapThread[SameQ,{{target,prediction}}],True],
"Cases"->Length[test]|>
];
results=Flatten[KeyValueMap[Function[{{family,positions}},
Flatten[Table[foldResult[family,positions,method,heldout],
{{method,methods}},{{heldout,Range[10]}}]]],families]];
Map[Function[group,Module[{{rs=group}},<|
"Family"->rs[[1]]["Family"],"Method"->rs[[1]]["Method"],
"ValidFolds"->Count[Lookup[rs,"Valid"],True],
"PerfectFolds"->Count[Lookup[rs,"Score"],8],
"MeanBalancedAccuracy"->Mean[Lookup[rs,"BalancedAccuracy"]],
"WorstBalancedAccuracy"->Min[Lookup[rs,"BalancedAccuracy"]],
"TotalScore"->Total[Lookup[rs,"Score"]],"TotalCases"->Total[Lookup[rs,"Cases"]]
|>]],GatherBy[results,{{#1["Family"],#1["Method"]}}&]]
]]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=600)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    payload = {
        "stage": "S92B-DEVELOPMENT-PROBE",
        "blind_test": False,
        "uses_revealed_s92_labels": True,
        "kernel_id": kernel_id,
        "result": result,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
