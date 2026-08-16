import json
import time
import uuid
from pathlib import Path
from urllib.request import Request, urlopen

import websocket

from run_s87c_on_existing_kernel import (
    NOTEBOOK,
    NOTEBOOK_PATH,
    RESULT,
    current_kernel,
    execute,
    plain_text,
    server_token,
)


RECOVERY_RESULT = RESULT.with_name("TCCT_S87C_RecoveryRun_Result.json")


def restart_kernel(token: str, kernel_id: str) -> None:
    request = Request(
        f"http://localhost:8888/api/kernels/{kernel_id}/restart?token={token}",
        data=b"",
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        if response.status not in {200, 201}:
            raise RuntimeError(f"kernel restart returned HTTP {response.status}")


def connect_kernel(token: str, kernel_id: str):
    url = f"ws://localhost:8888/api/kernels/{kernel_id}/channels?token={token}"
    last_error = None
    for _ in range(30):
        try:
            return websocket.create_connection(
                url,
                timeout=2,
                origin="http://localhost:8888",
                http_proxy_host=None,
                http_proxy_port=None,
            )
        except Exception as exc:
            last_error = exc
            time.sleep(1)
    raise RuntimeError(f"new kernel websocket did not become available: {last_error}")


def selected_cells() -> list[tuple[str, str, int]]:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    base = []
    s87b = []
    s87c = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = "".join(cell.get("source", [])).strip()
        if not source:
            continue
        stage = cell.get("metadata", {}).get("tcct_stage")
        if stage == "S87B":
            s87b.append(source)
        elif stage == "S87C":
            s87c.append(source)
        elif len(base) < 6:
            base.append(source)
    if len(base) != 6 or len(s87b) != 2 or len(s87c) != 2:
        raise RuntimeError(
            f"unexpected cell layout: base={len(base)}, S87B={len(s87b)}, S87C={len(s87c)}"
        )
    plan = [
        ("S87A architecture", base[0], 120),
        ("S87A preflight", base[1], 60),
        ("S87A definitions", base[2], 60),
        ("S87A audit definitions", base[3], 60),
        ("S87A trace reconstruction", base[4], 700),
        ("S87A certificate", base[5], 60),
        ("S87B preflight", s87b[0], 60),
        ("S87B research", s87b[1], 180),
        ("S87C preflight", s87c[0], 60),
        ("S87C research", s87c[1], 900),
    ]
    return plan


def compact(result: dict) -> dict:
    return {
        "label": result.get("label"),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "status": result.get("shell_reply", {}).get("status"),
        "errors": result.get("errors", []),
        "output_count": len(result.get("outputs", [])),
    }


def main() -> None:
    token = server_token()
    kernel_id = current_kernel(token)
    print(f"restarting zombie kernel: {kernel_id}", flush=True)
    restart_kernel(token, kernel_id)
    time.sleep(3)
    ws = connect_kernel(token, kernel_id)
    session = uuid.uuid4().hex
    records = []
    try:
        readiness = execute(ws, session, "InputForm[1+1]", "new kernel probe", 30)
        if readiness["errors"] or "2" not in plain_text(readiness):
            raise RuntimeError("new kernel did not pass arithmetic probe")
        records.append(compact(readiness))
        for label, source, timeout_seconds in selected_cells():
            result = execute(ws, session, source, label, timeout_seconds)
            records.append(compact(result))
            if result["errors"] or result.get("shell_reply", {}).get("status") == "error":
                raise RuntimeError(f"{label} failed: {result['errors']}")

        certificate = execute(ws, session, "InputForm[cert87C]", "S87C certificate", 30)
        records.append(compact(certificate))
        certificate_text = plain_text(certificate)
        if certificate["errors"] or "Stage -> S87C" not in certificate_text:
            raise RuntimeError(f"invalid S87C certificate: {certificate_text}")
        payload = {
            "kernel_id": kernel_id,
            "notebook": NOTEBOOK_PATH,
            "steps": records,
            "certificate_text": certificate_text,
        }
        RECOVERY_RESULT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"result: {RECOVERY_RESULT}", flush=True)
        print(certificate_text, flush=True)
    finally:
        ws.close()


if __name__ == "__main__":
    main()
