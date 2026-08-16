import json
import os
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import websocket


ROOT = Path(__file__).resolve().parent
SERVER_OPEN = ROOT / ".jupyter_runtime" / "jpserver-14344-open.html"
NOTEBOOK = ROOT / "TCCT_S89_StopRelocationCounterfactualBlind_Preflight.ipynb"
RUN_LOG = ROOT / "TCCT_S89_Preflight_RunLog.json"


def server_token() -> str:
    text = SERVER_OPEN.read_text(encoding="utf-8")
    match = re.search(r"token=([0-9a-f]+)", text)
    if not match:
        raise RuntimeError("Jupyter token not found")
    return match.group(1)


def idle_kernel(token: str) -> str:
    with urlopen(
        f"http://localhost:8888/api/sessions?token={token}", timeout=5
    ) as response:
        sessions = json.load(response)
    kernels = {
        session.get("kernel", {}).get("id"): session.get("kernel", {})
        for session in sessions
        if session.get("kernel", {}).get("id")
    }
    if len(kernels) != 1:
        raise RuntimeError(f"expected one shared live kernel, found {len(kernels)}")
    kernel_id, kernel = next(iter(kernels.items()))
    if kernel.get("execution_state") != "idle":
        raise RuntimeError(
            f"kernel is not idle: {kernel.get('execution_state', 'unknown')}"
        )
    return kernel_id


def header(msg_type: str, session: str) -> dict:
    return {
        "msg_id": uuid.uuid4().hex,
        "username": "codex-s89-preflight",
        "session": session,
        "date": datetime.now(timezone.utc).isoformat(),
        "msg_type": msg_type,
        "version": "5.3",
    }


def execute(ws, session: str, code: str, timeout_seconds: int = 300) -> dict:
    request_header = header("execute_request", session)
    msg_id = request_header["msg_id"]
    ws.send(
        json.dumps(
            {
                "header": request_header,
                "parent_header": {},
                "metadata": {},
                "content": {
                    "code": code,
                    "silent": False,
                    "store_history": False,
                    "user_expressions": {},
                    "allow_stdin": False,
                    "stop_on_error": True,
                },
                "channel": "shell",
                "buffers": [],
            }
        )
    )
    started = time.monotonic()
    shell_reply = None
    idle_seen = False
    outputs: list[str] = []
    errors: list[dict] = []
    while time.monotonic() - started < timeout_seconds:
        try:
            message = json.loads(ws.recv())
        except websocket.WebSocketTimeoutException:
            continue
        if message.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        msg_type = message.get("msg_type") or message.get("header", {}).get(
            "msg_type"
        )
        content = message.get("content", {})
        if msg_type == "execute_reply":
            shell_reply = content
        elif msg_type == "status" and content.get("execution_state") == "idle":
            idle_seen = True
        elif msg_type in {"display_data", "execute_result"}:
            outputs.append(content.get("data", {}).get("text/plain", ""))
        elif msg_type == "stream":
            outputs.append(content.get("text", ""))
        elif msg_type == "error":
            errors.append(
                {
                    "ename": content.get("ename", ""),
                    "evalue": content.get("evalue", ""),
                    "traceback": content.get("traceback", []),
                }
            )
        if shell_reply is not None and idle_seen:
            return {
                "elapsed_seconds": time.monotonic() - started,
                "status": shell_reply.get("status"),
                "outputs": outputs,
                "errors": errors,
            }
    raise TimeoutError("S89 preflight timed out")


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(code_cells) != 3:
        raise RuntimeError(f"expected three preflight cells, found {len(code_cells)}")

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
        for number, code in enumerate(code_cells, start=1):
            result = execute(ws, session, code)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"preflight cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed89,
"ProtocolHash"->protocolHash89,
"TestDefinitionHash"->testDefinitionHashBefore89,
"CandidateHash"->decoderCandidateHashLoaded89,
"S88CheckpointHash"->s88CheckpointFileHashBefore89,
"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash89,
"BlindScenariosDefined"->ValueQ[blindScenarios89],
"S89ResultCertificateExists"->FileExistsQ[s89ResultCertificatePath]
|>]''',
        )
        if probe["status"] != "ok" or probe["errors"]:
            raise RuntimeError(f"preflight probe failed: {probe}")
        parse_probe = execute(
            ws,
            session,
            r'''InputForm[Quiet@Check[
Module[{held},
held=ToExpression[
Import["C:/Users/王鑫/.codex/.chatgpt-projects/g-p-6a72c38f146c8191a7937f5612db2fd4/wolfram/TCCT_S89_StopRelocationCounterfactualBlind.wl","Text"],
InputForm,
HoldComplete
];
<|"FullSourceParseSucceeded"->MatchQ[held,_HoldComplete]|>
],
<|"FullSourceParseSucceeded"->False|>
]]''',
        )
        if parse_probe["status"] != "ok" or parse_probe["errors"]:
            raise RuntimeError(f"full source parse probe failed: {parse_probe}")
    finally:
        ws.close()

    probe_text = "\n".join(probe["outputs"])
    required_fragments = (
        '"PreflightPassed" -> True',
        '"CasesGeneratedBeforeProtocolHash" -> False',
        '"BlindScenariosDefined" -> False',
        '"S89ResultCertificateExists" -> False',
    )
    missing = [fragment for fragment in required_fragments if fragment not in probe_text]
    if missing:
        raise RuntimeError(
            f"S89 preflight probe did not pass; missing={missing}; probe={probe_text}"
        )
    parse_probe_text = "\n".join(parse_probe["outputs"])
    if '"FullSourceParseSucceeded" -> True' not in parse_probe_text:
        raise RuntimeError(f"S89 full source parse failed: {parse_probe_text}")
    payload = {
        "stage": "S89-PREFLIGHT",
        "preflight_passed": True,
        "used_existing_licensed_kernel": True,
        "blind_cases_generated": False,
        "result_certificate_created": False,
        "kernel_id": kernel_id,
        "probe_text": probe_text,
        "parse_probe_text": parse_probe_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
