"""Validate all S92A cells on the existing licensed kernel with a temporary certificate."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S92A_FailureMechanismAudit.ipynb"
TEMP_CERT = ROOT / "artifacts" / "TCCT_S92A_ValidationTemporaryCertificate.json"
RUN_LOG = ROOT / "TCCT_S92A_Validation_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    if TEMP_CERT.exists():
        TEMP_CERT.unlink()
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(cells) != 5:
        raise RuntimeError(f"expected five S92A code cells, found {len(cells)}")

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
        for number, code in enumerate(cells[:4], 1):
            result = execute(ws, session, code, timeout_seconds=300)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"S92A cell {number} failed: {result}")
        temp_path = TEMP_CERT.resolve().as_posix().replace('"', '\\"')
        redirect = execute(
            ws, session, f's92aCertificatePath="{temp_path}"; InputForm[s92aCertificatePath]'
        )
        if redirect["status"] != "ok" or redirect["errors"]:
            raise RuntimeError(f"temporary certificate redirect failed: {redirect}")
        audit_result = execute(ws, session, cells[4], timeout_seconds=300)
        audit_result["cell"] = 5
        results.append(audit_result)
        if audit_result["status"] != "ok" or audit_result["errors"]:
            raise RuntimeError(f"S92A audit cell failed: {audit_result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed92A,
"FreshPredictionsMatchArchive"->freshPredictionsMatchArchive92A,
"PairedRowsValid"->pairedRowsValid92A,
"CardinalityPairsMatched"->cardinalityPairedMatches92A,
"FullVectorPairsDifferent"->fullVectorPairedDifferences92A,
"ExactCoordinateSupportDisjoint"->exactCoordinateSupportDisjoint92A,
"CardinalityGateSensitivityObserved"->cardinalityGateSensitivityObserved92A,
"MaximumStopPredictionsUnderCardinalityProbes"->cardinalityProbeStopMaximum92A,
"Diagnosis"->diagnosis92A,
"AuditValidityPassed"->auditValidityPassed92A,
"Outcome"->cert92A["Outcome"],
"CertificateExported"->certificateExported92A,
"CoreChanged"->cert92A["CoreChanged"],
"FrozenDecoderChanged"->cert92A["FrozenDecoderChanged"],
"TrainingRun"->cert92A["TrainingRun"],
"RetuningApplied"->cert92A["RetuningApplied"]
|>]''',
            timeout_seconds=60,
        )
    finally:
        ws.close()

    if probe["status"] != "ok" or probe["errors"]:
        raise RuntimeError(f"S92A validation probe failed: {probe}")
    probe_text = "\n".join(probe["outputs"])
    required = (
        '"PreflightPassed" -> True',
        '"FreshPredictionsMatchArchive" -> True',
        '"PairedRowsValid" -> True',
        '"CardinalityPairsMatched" -> 40',
        '"FullVectorPairsDifferent" -> 40',
        '"ExactCoordinateSupportDisjoint" -> True',
        '"AuditValidityPassed" -> True',
        '"CertificateExported" -> True',
        '"CoreChanged" -> False',
        '"FrozenDecoderChanged" -> False',
        '"TrainingRun" -> False',
        '"RetuningApplied" -> False',
    )
    compact_probe = "".join(probe_text.split())
    missing = [
        fragment
        for fragment in required
        if "".join(fragment.split()) not in compact_probe
    ]
    if missing:
        raise RuntimeError(f"S92A validation mismatch: {missing}; probe={probe_text}")
    if not TEMP_CERT.exists():
        raise RuntimeError("temporary S92A certificate was not created")
    temp_certificate = json.loads(TEMP_CERT.read_text(encoding="utf-8"))
    if temp_certificate.get("Outcome") != "S92A_VALID_FAILURE_MECHANISM_AUDIT_COMPLETE":
        raise RuntimeError(
            f"unexpected temporary certificate outcome: {temp_certificate.get('Outcome')}"
        )

    payload = {
        "stage": "S92A-VALIDATION",
        "passed": True,
        "used_existing_licensed_kernel": True,
        "kernel_id": kernel_id,
        "real_certificate_created": False,
        "temporary_certificate_removed_after_validation": True,
        "probe_text": probe_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    TEMP_CERT.unlink()
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
