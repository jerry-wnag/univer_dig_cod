"""Validate the S91 audit cell against a temporary certificate, then remove it."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S91_BaselineAblationBenchmark.ipynb"
RUN_LOG = ROOT / "TCCT_S91_AuditValidation_RunLog.json"
TEMP_NAME = "TCCT_S91_Preflight_TemporaryCertificate.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    temp_path = ROOT / TEMP_NAME
    if temp_path.exists():
        raise RuntimeError(f"temporary validation file already exists: {temp_path}")
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code_cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    audit_code = code_cells[4]
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
        setup = execute(
            ws,
            session,
            f's91CertificatePath=FileNameJoin[{{Directory[],"{TEMP_NAME}"}}];',
        )
        if setup["status"] != "ok" or setup["errors"]:
            raise RuntimeError(setup)
        audit = execute(ws, session, audit_code, timeout_seconds=120)
        if audit["status"] != "ok" or audit["errors"]:
            raise RuntimeError(f"S91 audit validation failed: {audit}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"BenchmarkValidityPassed"->benchmarkValidityPassed91,
"Outcome"->cert91["Outcome"],
"FullScore"->cert91["FrozenFullScore"],
"LegacyScore"->cert91["LegacyScore"],
"DegradedAblations"->cert91["DegradedAblations"],
"CertificateExported"->certificateExported91,
"TemporaryCertificateExists"->FileExistsQ[s91CertificatePath]
|>]''',
        )
        cleanup = execute(
            ws,
            session,
            'If[FileExistsQ[s91CertificatePath],DeleteFile[s91CertificatePath]];'
            'InputForm[<|"TemporaryCertificateRemoved"->!FileExistsQ[s91CertificatePath]|>]',
        )
    finally:
        ws.close()
    for label, result in (("probe", probe), ("cleanup", cleanup)):
        if result["status"] != "ok" or result["errors"]:
            raise RuntimeError(f"{label} failed: {result}")
    probe_text = "\n".join(probe["outputs"])
    cleanup_text = "\n".join(cleanup["outputs"])
    required = (
        '"BenchmarkValidityPassed" -> True',
        '"Outcome" -> "S91_VALID_POSTHOC_BASELINE_ABLATION_COMPLETE"',
        '"FullScore" -> 1296',
        '"LegacyScore" -> 128',
        '"DegradedAblations" -> 2',
        '"CertificateExported" -> True',
        '"TemporaryCertificateExists" -> True',
    )
    missing = [fragment for fragment in required if fragment not in probe_text]
    if missing or '"TemporaryCertificateRemoved" -> True' not in cleanup_text:
        raise RuntimeError(
            f"audit validation mismatch: missing={missing}; "
            f"probe={probe_text}; cleanup={cleanup_text}"
        )
    if temp_path.exists():
        raise RuntimeError("temporary validation certificate was not removed")
    payload = {
        "stage": "S91-AUDIT-VALIDATION",
        "passed": True,
        "real_certificate_created": False,
        "temporary_certificate_removed": True,
        "kernel_id": kernel_id,
        "probe_text": probe_text,
        "cleanup_text": cleanup_text,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
