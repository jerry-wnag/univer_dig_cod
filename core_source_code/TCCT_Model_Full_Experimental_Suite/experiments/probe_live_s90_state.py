"""Read-only probe of the completed S90 Wolfram kernel."""

import json
import os
import uuid

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


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
    try:
        result = execute(
            ws,
            session,
            r'''InputForm[<|
"Directory"->Directory[],
"S90CertificatePresent"->ValueQ[cert90],
"S90Outcome"->If[ValueQ[cert90],Lookup[cert90,"Outcome",Missing[]],Missing[]],
"BlindWorldsPresent"->ValueQ[blindWorlds90],
"WorldCount"->If[ValueQ[blindWorlds90],Length[blindWorlds90],0],
"WorldKeys"->If[ValueQ[blindWorlds90]&&Length[blindWorlds90]>0,Keys[First[blindWorlds90]],{}],
"ObservationKeys"->If[
  ValueQ[blindWorlds90]&&Length[blindWorlds90]>0&&Length[Lookup[First[blindWorlds90],"Observations",{}]]>0,
  Keys[First[Lookup[First[blindWorlds90],"Observations"]]],
  {}
],
"TargetCounts"->If[ValueQ[blindWorlds90],Counts[Lookup[blindWorlds90,"Target"]],<||>],
"KernelID"->"''' + kernel_id + r'''"
|>]''',
        )
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
