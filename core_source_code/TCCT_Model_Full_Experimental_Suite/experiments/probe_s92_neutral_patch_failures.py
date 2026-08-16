"""Read the already-computed neutral-patch mismatch positions from the live kernel."""

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
            r'''InputForm[Select[probeRows92,
SameQ[#1["Target"],"Continue"]&&!SameQ[#1["Cardinality"],{2,2,1}]&]]''',
        )
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
