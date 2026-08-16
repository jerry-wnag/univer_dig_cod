"""Development-only grouped-holdout probe for a paired S92B decoder."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "artifacts" / "TCCT_S92_FailureAuditWorlds.json"
RUN_LOG = ROOT / "TCCT_S92B_PairContrastProbe_RunLog.json"


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
InputForm[Module[{{rows,continueRows,stopRows,keys,pairs,pairVector,examples,folds,
train,test,classifier,predictions,score,fullClassifier,fullPredictions}},
rows=Lookup[Import["{archive_path}","RawJSON"],"Rows"];
continueRows=Select[rows,SameQ[#1["Target"],"Continue"]&];
stopRows=Select[rows,SameQ[#1["Target"],"Stop"]&];
keys=({{#1["Topology"],#1["Depth"],#1["Answer"]}}&)/@continueRows;
pairs=Map[Function[key,{{
SelectFirst[continueRows,SameQ[{{#1["Topology"],#1["Depth"],#1["Answer"]}},key]&],
SelectFirst[stopRows,SameQ[{{#1["Topology"],#1["Depth"],#1["Answer"]}},key]&]
}}],keys];
pairVector[a_,b_]:={{Mod[a[[3]]-b[[3]],33],Mod[a[[4]]-b[[4]],33]}};
examples=Flatten[Map[Function[pair,With[{{c=pair[[1]],s=pair[[2]]}},{{
<|"Answer"->c["Answer"],"Vector"->pairVector[c["FeatureVector"],s["FeatureVector"]],
"Target"->"FirstContinue"|>,
<|"Answer"->c["Answer"],"Vector"->pairVector[s["FeatureVector"],c["FeatureVector"]],
"Target"->"FirstStop"|>
}}]],pairs]];
folds=Table[
train=Select[examples,!SameQ[#1["Answer"],heldout]&];
test=Select[examples,SameQ[#1["Answer"],heldout]&];
SeedRandom[920200+heldout,Method->"MersenneTwister"];
classifier=Classify[(#1["Vector"]->#1["Target"])&/@train,Method->"DecisionTree"];
predictions=classifier/@Lookup[test,"Vector"];
score=Count[MapThread[SameQ,{{Lookup[test,"Target"],predictions}}],True];
<|"HeldoutAnswer"->heldout,"Score"->score,"Cases"->Length[test],
"Perfect"->SameQ[score,Length[test]]|>,{{heldout,Range[10]}}];
SeedRandom[920299,Method->"MersenneTwister"];
fullClassifier=Classify[(#1["Vector"]->#1["Target"])&/@examples,Method->"DecisionTree"];
fullPredictions=fullClassifier/@Lookup[examples,"Vector"];
<|"Pairs"->Length[pairs],"OrientedExamples"->Length[examples],
"FeatureSupport"->Counts[Lookup[examples,"Vector"]],
"PerfectFolds"->Count[Lookup[folds,"Perfect"],True],"Folds"->Length[folds],
"FullScore"->Count[MapThread[SameQ,{{Lookup[examples,"Target"],fullPredictions}}],True],
"FullCases"->Length[examples],"FoldRows"->folds|>
]]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=300)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    payload = {
        "stage": "S92B-PAIR-CONTRAST-DEVELOPMENT-PROBE",
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
