"""Run only S94 locked-input and protocol cells on the existing licensed kernel."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S94_MixedContextRobustnessBlind_Preflight.ipynb"
FULL_SOURCE = ROOT / "TCCT_S94_MixedContextRobustnessBlind.wl"
RUN_LOG = ROOT / "TCCT_S94_Preflight_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(cells) != 3:
        raise RuntimeError(f"expected three S94 preflight cells, found {len(cells)}")
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
                raise RuntimeError(f"S94 preflight cell {number} failed: {result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed94,
"ProtocolHash"->protocolHash94,
"TestDefinitionHash"->testDefinitionHashBefore94,
"TopologySpecHash"->topologySpecHash94,
"CandidateHash"->pairDecoderLoaded94["CandidateHash"],
"NoCasesBeforeProtocolHash"->noCasesBeforeProtocolHash94,
"BlindScenariosDefined"->ValueQ[blindScenarios94],
"BlindWorldsDefined"->ValueQ[blindWorlds94],
"BlindPairsDefined"->ValueQ[blindPairs94],
"S94ResultCertificateExists"->FileExistsQ[s94ResultCertificatePath]
|>]''',
            timeout_seconds=60,
        )
        source_path = FULL_SOURCE.resolve().as_posix().replace('"', '\\"')
        parse = execute(
            ws,
            session,
            f'''InputForm[Quiet@Check[Module[{{held}},
held=ToExpression[Import["{source_path}","Text"],InputForm,HoldComplete];
<|"FullSourceParseSucceeded"->MatchQ[held,_HoldComplete]|>],
<|"FullSourceParseSucceeded"->False|>]]''',
            timeout_seconds=60,
        )
    finally:
        ws.close()

    for label, result in (("probe", probe), ("parse", parse)):
        if result["status"] != "ok" or result["errors"]:
            raise RuntimeError(f"S94 {label} failed: {result}")
    probe_text = "\n".join(probe["outputs"])
    parse_text = "\n".join(parse["outputs"])
    compact_probe = "".join(probe_text.replace("\\", "").split())
    required = (
        '"PreflightPassed"->True',
        '"NoCasesBeforeProtocolHash"->True',
        '"BlindScenariosDefined"->False',
        '"BlindWorldsDefined"->False',
        '"BlindPairsDefined"->False',
        '"S94ResultCertificateExists"->False',
    )
    missing = [fragment for fragment in required if fragment not in compact_probe]
    if missing or '"FullSourceParseSucceeded" -> True' not in parse_text:
        raise RuntimeError(
            f"S94 preflight mismatch: missing={missing}; "
            f"probe={probe_text}; parse={parse_text}"
        )
    payload = {
        "stage": "S94-PREFLIGHT",
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
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
