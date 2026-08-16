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
NOTEBOOK = ROOT / "TCCT_S87A_SevenBranchFailureAudit.ipynb"
SERVER_OPEN = ROOT / ".jupyter_runtime" / "jpserver-14344-open.html"
RESULT = ROOT / "TCCT_S87C_ExternalKernelRun_Result.json"
NOTEBOOK_PATH = "TCCT_S87A_SevenBranchFailureAudit.ipynb"


def server_token() -> str:
    text = SERVER_OPEN.read_text(encoding="utf-8")
    match = re.search(r"token=([0-9a-f]+)", text)
    if not match:
        raise RuntimeError("Jupyter token not found")
    return match.group(1)


def current_kernel(token: str) -> str:
    with urlopen(
        f"http://localhost:8888/api/sessions?token={token}", timeout=5
    ) as response:
        sessions = json.load(response)
    matches = [session for session in sessions if session.get("path") == NOTEBOOK_PATH]
    if len(matches) != 1:
        raise RuntimeError(f"expected one S87A session, found {len(matches)}")
    kernel = matches[0].get("kernel", {})
    if kernel.get("execution_state") != "idle":
        raise RuntimeError(
            f"kernel is not idle: {kernel.get('execution_state', 'unknown')}"
        )
    return kernel["id"]


def header(msg_type: str, session: str) -> dict:
    return {
        "msg_id": uuid.uuid4().hex,
        "username": "codex-s87c-runner",
        "session": session,
        "date": datetime.now(timezone.utc).isoformat(),
        "msg_type": msg_type,
        "version": "5.3",
    }


def decode_message(payload):
    if isinstance(payload, bytes):
        payload = payload.decode("utf-8")
    return json.loads(payload)


def execute(ws, session: str, code: str, label: str, timeout_seconds: int) -> dict:
    request_header = header("execute_request", session)
    msg_id = request_header["msg_id"]
    request = {
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
    ws.send(json.dumps(request))
    started = time.monotonic()
    last_update = started
    shell_reply = None
    idle_seen = False
    outputs = []
    errors = []
    print(f"{label}: submitted", flush=True)
    while time.monotonic() - started < timeout_seconds:
        try:
            message = decode_message(ws.recv())
        except websocket.WebSocketTimeoutException:
            now = time.monotonic()
            if now - last_update >= 30:
                print(f"{label}: still running ({int(now - started)} s)", flush=True)
                last_update = now
            continue
        parent = message.get("parent_header", {})
        if parent.get("msg_id") != msg_id:
            continue
        msg_type = message.get("msg_type") or message.get("header", {}).get("msg_type")
        content = message.get("content", {})
        if msg_type == "execute_reply":
            shell_reply = content
        elif msg_type == "status" and content.get("execution_state") == "idle":
            idle_seen = True
        elif msg_type == "stream":
            outputs.append({"type": "stream", "text": content.get("text", "")})
        elif msg_type in {"display_data", "execute_result"}:
            data = content.get("data", {})
            outputs.append(
                {
                    "type": msg_type,
                    "text_plain": data.get("text/plain", ""),
                    "text_html": data.get("text/html", ""),
                }
            )
        elif msg_type == "error":
            error = {
                "ename": content.get("ename", ""),
                "evalue": content.get("evalue", ""),
                "traceback": content.get("traceback", []),
            }
            errors.append(error)
        if shell_reply is not None and idle_seen:
            elapsed = time.monotonic() - started
            print(f"{label}: finished in {elapsed:.1f} s", flush=True)
            return {
                "label": label,
                "elapsed_seconds": elapsed,
                "shell_reply": shell_reply,
                "outputs": outputs,
                "errors": errors,
            }
    raise TimeoutError(f"{label} timed out after {timeout_seconds} seconds")


def plain_text(result: dict) -> str:
    chunks = []
    for output in result.get("outputs", []):
        if output.get("text_plain"):
            chunks.append(output["text_plain"])
        if output.get("text"):
            chunks.append(output["text"])
    return "\n".join(chunks)


def s87c_source() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        cell
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
        and cell.get("metadata", {}).get("tcct_stage") == "S87C"
    ]
    if len(cells) != 2:
        raise RuntimeError(f"expected two S87C code cells, found {len(cells)}")
    return "".join(cells[1].get("source", []))


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    token = server_token()
    kernel_id = current_kernel(token)
    session = uuid.uuid4().hex
    ws_url = (
        f"ws://localhost:8888/api/kernels/{kernel_id}/channels?token={token}"
    )
    ws = websocket.create_connection(
        ws_url,
        timeout=2,
        origin="http://localhost:8888",
        http_proxy_host=None,
        http_proxy_port=None,
    )
    try:
        probe_code = r'''
InputForm[<|
"Ready"->And[
ValueQ[allWorlds87A],ValueQ[cert87A],ValueQ[cert87B],ValueQ[protocol87C]
],
"Worlds"->If[ValueQ[allWorlds87A],Length[allWorlds87A],Missing["Unavailable"]],
"S87AValid"->If[ValueQ[cert87A],cert87A["AuditValidityPassed"],False],
"S87BValid"->If[ValueQ[cert87B],cert87B["ResearchValidityPassed"],False]
|>]
'''.strip()
        probe = execute(ws, session, probe_code, "probe", 30)
        probe_text = plain_text(probe)
        if probe["errors"] or "Ready -> True" not in probe_text or "Worlds -> 392" not in probe_text:
            raise RuntimeError(f"existing kernel failed S87C readiness probe: {probe_text}")

        run = execute(ws, session, s87c_source(), "S87C", 900)
        if run["errors"] or run.get("shell_reply", {}).get("status") == "error":
            raise RuntimeError(f"S87C execution failed: {run['errors']}")

        certificate = execute(
            ws,
            session,
            'InputForm[cert87C]',
            "certificate",
            30,
        )
        if certificate["errors"]:
            raise RuntimeError(f"certificate read failed: {certificate['errors']}")
        payload = {
            "kernel_id": kernel_id,
            "notebook": NOTEBOOK_PATH,
            "probe": probe,
            "run": run,
            "certificate": certificate,
            "certificate_text": plain_text(certificate),
        }
        RESULT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"result: {RESULT}", flush=True)
        print(payload["certificate_text"], flush=True)
    finally:
        ws.close()


if __name__ == "__main__":
    main()
