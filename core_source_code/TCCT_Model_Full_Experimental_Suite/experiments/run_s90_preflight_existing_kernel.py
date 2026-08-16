import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S90_InterventionAlgebraBlind_Preflight.ipynb"
RUN_LOG = ROOT / "TCCT_S90_Preflight_RunLog.json"


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
        for number, code in enumerate(code_cells, 1):
            result = execute(ws, session, code)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"preflight cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed90,
"ProtocolHash"->protocolHash90,
"TestDefinitionHash"->testDefinitionHashBefore90,
"CandidateHash"->decoderCandidateHashLoaded90,
"S89CheckpointHash"->s89CheckpointFileHashBefore90,
"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash90,
"BlindScenariosDefined"->ValueQ[blindScenarios90],
"S90ResultCertificateExists"->FileExistsQ[s90ResultCertificatePath]
|>]''',
        )
        parse_probe = execute(
            ws,
            session,
            r'''InputForm[Quiet@Check[
Module[{held},held=ToExpression[
Import["C:/Users/王鑫/.codex/.chatgpt-projects/g-p-6a72c38f146c8191a7937f5612db2fd4/wolfram/TCCT_S90_InterventionAlgebraBlind.wl","Text"],
InputForm,HoldComplete];
<|"FullSourceParseSucceeded"->MatchQ[held,_HoldComplete]|>],
<|"FullSourceParseSucceeded"->False|>]]''',
        )
    finally:
        ws.close()
    for label, result in (("probe", probe), ("parse", parse_probe)):
        if result["status"] != "ok" or result["errors"]:
            raise RuntimeError(f"{label} failed: {result}")
    probe_text = "\n".join(probe["outputs"])
    required = (
        '"PreflightPassed" -> True',
        '"CasesGeneratedBeforeProtocolHash" -> False',
        '"BlindScenariosDefined" -> False',
        '"S90ResultCertificateExists" -> False',
    )
    missing = [item for item in required if item not in probe_text]
    parse_text = "\n".join(parse_probe["outputs"])
    if missing or '"FullSourceParseSucceeded" -> True' not in parse_text:
        raise RuntimeError(
            f"S90 preflight failed: missing={missing}, probe={probe_text}, parse={parse_text}"
        )
    payload = {
        "stage": "S90-PREFLIGHT",
        "preflight_passed": True,
        "used_existing_licensed_kernel": True,
        "blind_cases_generated": False,
        "result_certificate_created": False,
        "kernel_id": kernel_id,
        "probe_text": probe_text,
        "parse_probe_text": parse_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
