import hashlib
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
NOTEBOOK_PATH = "TCCT_S87A_SevenBranchFailureAudit.ipynb"
CERTIFICATE = Path(r"E:\engine_wolf\TCCT_S87D_FreezeCertificate.json")
CANDIDATE = Path(r"E:\engine_wolf\TCCT_S87D_FrozenWorldMultisetDecoder.wxf")
RUN_LOG = ROOT / "TCCT_S87D_CertificateRepair_RunLog.json"


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
        "username": "codex-s87d-certificate-repair",
        "session": session,
        "date": datetime.now(timezone.utc).isoformat(),
        "msg_type": msg_type,
        "version": "5.3",
    }


def execute(ws, session: str, code: str, timeout_seconds: int = 30) -> dict:
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
    outputs = []
    errors = []
    while time.monotonic() - started < timeout_seconds:
        try:
            message = json.loads(ws.recv())
        except websocket.WebSocketTimeoutException:
            continue
        if message.get("parent_header", {}).get("msg_id") != msg_id:
            continue
        msg_type = message.get("msg_type") or message.get("header", {}).get("msg_type")
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
                }
            )
        if shell_reply is not None and idle_seen:
            return {
                "elapsed_seconds": time.monotonic() - started,
                "status": shell_reply.get("status"),
                "outputs": outputs,
                "errors": errors,
            }
    raise TimeoutError("certificate repair timed out")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    token = server_token()
    kernel_id = current_kernel(token)
    session = uuid.uuid4().hex
    ws = websocket.create_connection(
        f"ws://localhost:8888/api/kernels/{kernel_id}/channels?token={token}",
        timeout=2,
        origin="http://localhost:8888",
        http_proxy_host=None,
        http_proxy_port=None,
    )
    try:
        code = r'''
If[
  !ValueQ[cert87D] || !TrueQ[cert87D["FreezeValidityPassed"]],
  Print["S87D certificate state is unavailable or invalid."];
  Abort[]
];
repairResult87D = Export[
  "E:\\engine_wolf\\TCCT_S87D_FreezeCertificate.json",
  cert87D,
  "RawJSON"
];
InputForm[<|
  "ExportResult" -> repairResult87D,
  "FreezeValidityPassed" -> cert87D["FreezeValidityPassed"],
  "ReadyForS88" -> cert87D["ReadyForS88"],
  "Outcome" -> cert87D["Outcome"],
  "CoreChanged" -> cert87D["CoreChanged"],
  "CandidateHash" -> cert87D["CandidateHash"]
|>]
'''.strip()
        result = execute(ws, session, code)
    finally:
        ws.close()

    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(f"Wolfram repair failed: {result}")
    certificate = json.loads(CERTIFICATE.read_text(encoding="utf-8"))
    required = {
        "FreezeValidityPassed": True,
        "ReadyForS88": True,
        "CoreChanged": False,
        "OriginalFrozenModelChanged": False,
        "OriginalK33CandidateChanged": False,
        "DeduplicationMechanismChanged": False,
        "S88DataReadBeforeFreeze": False,
        "Outcome": "S87D_DECODER_FROZEN_AND_LOCKED_READY_FOR_S88",
    }
    mismatches = {
        key: {"expected": value, "actual": certificate.get(key)}
        for key, value in required.items()
        if certificate.get(key) != value
    }
    if mismatches:
        raise RuntimeError(f"certificate verification failed: {mismatches}")
    payload = {
        "stage": "S87D",
        "repair_only": True,
        "candidate_modified": False,
        "certificate_exported": True,
        "certificate_bytes": CERTIFICATE.stat().st_size,
        "certificate_sha256": sha256(CERTIFICATE),
        "candidate_bytes": CANDIDATE.stat().st_size,
        "candidate_sha256": sha256(CANDIDATE),
        "candidate_hash": certificate["CandidateHash"],
        "outcome": certificate["Outcome"],
        "wolfram_result": result,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

