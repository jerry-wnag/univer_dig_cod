"""Read compact S92B state from the shared live Wolfram kernel."""

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
    code = r'''InputForm[Module[{probePath,probeExport,probeExists},
probePath=FileNameJoin[{Directory[],"artifacts","TCCT_S92B_WXFProbe.tmp"}];
If[FileExistsQ[probePath],DeleteFile[probePath]];
probeExport=Check[Export[probePath,<|"Probe"->True|>,"WXF"],$Failed];
probeExists=FileExistsQ[probePath];If[probeExists,DeleteFile[probePath]];
<|
"PreflightDefined"->ValueQ[preflightPassed92B],
"PreflightPassed"->If[ValueQ[preflightPassed92B],preflightPassed92B,Missing[]],
"ProtocolDefined"->ValueQ[protocol92B],
"PairsDefined"->ValueQ[pairedWorlds92B],
"Pairs"->If[ValueQ[pairedWorlds92B],Length[pairedWorlds92B],-1],
"PositionResultsDefined"->ValueQ[positionResults92B],
"PositionResults"->If[ValueQ[positionResults92B],Length[positionResults92B],-1],
"CandidateFound"->If[ValueQ[candidateFound92B],candidateFound92B,Missing[]],
"SelectedPosition"->If[ValueQ[selectedResult92B]&&AssociationQ[selectedResult92B],
selectedResult92B["Position"],-1],
"PerfectFolds"->If[ValueQ[selectedResult92B]&&AssociationQ[selectedResult92B],
selectedResult92B["PerfectFolds"],-1],
"FreezeEligible"->If[ValueQ[freezeEligible92B],freezeEligible92B,Missing[]],
"CandidateExportResult"->If[ValueQ[candidateExportResult92B],candidateExportResult92B,Missing[]],
"CandidatePath"->If[ValueQ[s92bCandidatePath],s92bCandidatePath,Missing[]],
"CandidateFileExists"->If[ValueQ[s92bCandidatePath],FileExistsQ[s92bCandidatePath],False],
"MinimalWXFExport"->probeExport,"MinimalWXFExists"->probeExists
|>]]'''
    try:
        result = execute(ws, session, code, timeout_seconds=30)
    finally:
        ws.close()
    print(json.dumps({"kernel_id": kernel_id, "result": result}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
