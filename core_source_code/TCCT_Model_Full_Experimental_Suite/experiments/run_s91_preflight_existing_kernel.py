"""Run S91 through evaluation on the existing licensed kernel, without export."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S91_BaselineAblationBenchmark.ipynb"
RUN_LOG = ROOT / "TCCT_S91_Preflight_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(code_cells) != 5:
        raise RuntimeError(f"expected five S91 code cells, found {len(code_cells)}")

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
        for number, code in enumerate(code_cells[:4], 1):
            result = execute(ws, session, code, timeout_seconds=300)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"S91 preflight cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed91,
"ProtocolHash"->protocolHashBeforeScoring91,
"FreshFullMatchesCachedS90"->freshFullMatchesCachedS9091,
"ModelCount"->Length[resultRows91],
"FullScore"->fullResult91["Score"],
"FullStopCorrect"->fullResult91["StopCorrect"],
"LegacyScore"->SelectFirst[resultRows91,
  SameQ[#1["Model"],"LegacyK33ExactRole"]&]["Score"],
"DegradedAblations"->Count[ablationRows91,
  row_/;row["Score"]<fullResult91["Score"]],
"S91CertificateExists"->FileExistsQ[s91CertificatePath]
|>]''',
        )
    finally:
        ws.close()
    if probe["status"] != "ok" or probe["errors"]:
        raise RuntimeError(f"S91 probe failed: {probe}")
    probe_text = "\n".join(probe["outputs"])
    required = (
        '"PreflightPassed" -> True',
        '"FreshFullMatchesCachedS90" -> True',
        '"ModelCount" -> 14',
        '"FullScore" -> 1296',
        '"FullStopCorrect" -> 144',
        '"S91CertificateExists" -> False',
    )
    missing = [fragment for fragment in required if fragment not in probe_text]
    if missing:
        raise RuntimeError(f"S91 preflight mismatch: {missing}; {probe_text}")
    payload = {
        "stage": "S91-PREFLIGHT",
        "passed": True,
        "used_existing_licensed_kernel": True,
        "certificate_created": False,
        "kernel_id": kernel_id,
        "probe_text": probe_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
