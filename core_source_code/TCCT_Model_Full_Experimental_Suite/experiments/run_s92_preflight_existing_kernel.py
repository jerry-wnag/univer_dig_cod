"""Run only the S92 setup/protocol cells on the existing licensed kernel."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind_Preflight.ipynb"
FULL_SOURCE = ROOT / "TCCT_S92_CardinalityMatchedUniformActionBlind.wl"
RUN_LOG = ROOT / "TCCT_S92_Preflight_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(cells) != 3:
        raise RuntimeError(f"expected three S92 preflight cells, found {len(cells)}")
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
        for number, code in enumerate(cells, 1):
            result = execute(ws, session, code, timeout_seconds=300)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"S92 preflight cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed92,
"ProtocolHash"->protocolHash92,
"TestDefinitionHash"->testDefinitionHashBefore92,
"CandidateHash"->decoderCandidateHashLoaded92,
"S90CheckpointHash"->s90CheckpointFileHashBefore92,
"S91CheckpointHash"->s91CheckpointFileHashBefore92,
"CasesGeneratedBeforeProtocolHash"->!noCasesBeforeProtocolHash92,
"BlindScenariosDefined"->ValueQ[blindScenarios92],
"BlindWorldsDefined"->ValueQ[blindWorlds92],
"S92ResultCertificateExists"->FileExistsQ[s92ResultCertificatePath]
|>]''',
        )
        source_path = FULL_SOURCE.resolve().as_posix().replace('"', '\\"')
        parse = execute(
            ws,
            session,
            f'''InputForm[Quiet@Check[Module[{{held}},
held=ToExpression[Import["{source_path}","Text"],InputForm,HoldComplete];
<|"FullSourceParseSucceeded"->MatchQ[held,_HoldComplete]|>],
<|"FullSourceParseSucceeded"->False|>]]''',
        )
    finally:
        ws.close()
    for label, result in (("probe", probe), ("parse", parse)):
        if result["status"] != "ok" or result["errors"]:
            raise RuntimeError(f"S92 {label} failed: {result}")
    probe_text = "\n".join(probe["outputs"])
    parse_text = "\n".join(parse["outputs"])
    required = (
        '"PreflightPassed" -> True',
        '"CasesGeneratedBeforeProtocolHash" -> False',
        '"BlindScenariosDefined" -> False',
        '"BlindWorldsDefined" -> False',
        '"S92ResultCertificateExists" -> False',
    )
    missing = [fragment for fragment in required if fragment not in probe_text]
    if missing or '"FullSourceParseSucceeded" -> True' not in parse_text:
        raise RuntimeError(
            f"S92 preflight mismatch: missing={missing}; "
            f"probe={probe_text}; parse={parse_text}"
        )
    payload = {
        "stage": "S92-PREFLIGHT",
        "passed": True,
        "blind_cases_generated": False,
        "result_certificate_created": False,
        "used_existing_licensed_kernel": True,
        "kernel_id": kernel_id,
        "probe_text": probe_text,
        "parse_text": parse_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
