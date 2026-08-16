"""Validate S92B on the live kernel using temporary output paths."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
NOTEBOOK = ROOT / "TCCT_S92B_PairedContrastDecoderTraining.ipynb"
TEMP_CANDIDATE = Path("E:/engine_wolf/TCCT_S92B_VALIDATION_TEMP_Candidate.wxf")
TEMP_RUNTIME = Path("E:/engine_wolf/TCCT_S92B_VALIDATION_TEMP_Runtime.wl")
TEMP_CERTIFICATE = Path("E:/engine_wolf/TCCT_S92B_VALIDATION_TEMP_Certificate.json")
RUN_LOG = ROOT / "TCCT_S92B_Validation_RunLog.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    temporary_paths = (TEMP_CANDIDATE, TEMP_RUNTIME, TEMP_CERTIFICATE)
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    cells = [
        "".join(cell.get("source", []))
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    if len(cells) != 5:
        raise RuntimeError(f"expected five S92B code cells, found {len(cells)}")

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
        cleanup_paths = ",".join(
            f'"{path.as_posix()}"' for path in temporary_paths
        )
        cleanup_before = execute(
            ws,
            session,
            f'InputForm[Map[Function[p,If[FileExistsQ[p],DeleteFile[p]]],'
            f'{{{cleanup_paths}}}]]',
            timeout_seconds=30,
        )
        if cleanup_before["status"] != "ok" or cleanup_before["errors"]:
            raise RuntimeError(f"S92B temporary pre-cleanup failed: {cleanup_before}")
        for number, code in enumerate(cells[:4], 1):
            result = execute(ws, session, code, timeout_seconds=300)
            result["cell"] = number
            results.append(result)
            if result["status"] != "ok" or result["errors"]:
                raise RuntimeError(f"S92B cell {number} failed: {result}")
        cpath = TEMP_CANDIDATE.resolve().as_posix().replace('"', '\\"')
        rpath = TEMP_RUNTIME.resolve().as_posix().replace('"', '\\"')
        jpath = TEMP_CERTIFICATE.resolve().as_posix().replace('"', '\\"')
        redirect = execute(
            ws,
            session,
            f's92bCandidatePath="{cpath}";s92bRuntimePath="{rpath}";'
            f's92bCertificatePath="{jpath}";InputForm[{{s92bCandidatePath,'
            's92bRuntimePath,s92bCertificatePath}]',
        )
        if redirect["status"] != "ok" or redirect["errors"]:
            raise RuntimeError(f"S92B temporary output redirect failed: {redirect}")
        freeze_result = execute(ws, session, cells[4], timeout_seconds=300)
        freeze_result["cell"] = 5
        results.append(freeze_result)
        if freeze_result["status"] != "ok" or freeze_result["errors"]:
            raise RuntimeError(f"S92B freeze cell failed: {freeze_result}")
        probe = execute(
            ws,
            session,
            r'''InputForm[<|
"PreflightPassed"->preflightPassed92B,
"PairedWorldsValid"->pairedWorldsValid92B,
"CandidateFound"->candidateFound92B,
"EligibleCandidates"->Length[eligibleResults92B],
"SelectedPosition"->If[candidateFound92B,selectedResult92B["Position"],-1],
"SelectedFeature"->If[candidateFound92B,selectedResult92B["Feature"],"NONE"],
"SelectedPolicyRules"->selectedPolicyRules92B,
"AnswerPerfectFolds"->If[candidateFound92B,selectedResult92B["PerfectFolds"],0],
"SecondaryFoldsPerfect"->secondaryFoldsPerfect92B,
"ReversalConsistencyPassed"->reversalConsistencyPassed92B,
"ResearchValidityPassed"->researchValidityPassed92B,
"FreezeValidityPassed"->freezeValidityPassed92B,
"CandidateExported"->candidateExported92B,
"RuntimeExported"->runtimeExported92B,
"RoundTripPassed"->roundTripPassed92B,
"Outcome"->cert92B["Outcome"],
"CoreChanged"->cert92B["CoreChanged"],
"BaseFrozenS87DDecoderChanged"->cert92B["BaseFrozenS87DDecoderChanged"]
|>]''',
            timeout_seconds=60,
        )
    finally:
        ws.close()

    if probe["status"] != "ok" or probe["errors"]:
        raise RuntimeError(f"S92B validation probe failed: {probe}")
    probe_text = "\n".join(probe["outputs"])
    compact_probe = "".join(probe_text.replace("\\", "").split())
    required = (
        '"PreflightPassed"->True',
        '"PairedWorldsValid"->True',
        '"CandidateFound"->True',
        '"AnswerPerfectFolds"->10',
        '"SecondaryFoldsPerfect"->True',
        '"ReversalConsistencyPassed"->True',
        '"ResearchValidityPassed"->True',
        '"FreezeValidityPassed"->True',
        '"CandidateExported"->True',
        '"RuntimeExported"->True',
        '"RoundTripPassed"->True',
        '"CoreChanged"->False',
        '"BaseFrozenS87DDecoderChanged"->False',
    )
    missing = [fragment for fragment in required if fragment not in compact_probe]
    if missing:
        raise RuntimeError(f"S92B validation mismatch: {missing}; probe={probe_text}")
    if not all(path.exists() for path in temporary_paths):
        raise RuntimeError("one or more temporary S92B outputs were not created")
    certificate = json.loads(TEMP_CERTIFICATE.read_text(encoding="utf-8"))
    if certificate.get("Outcome") != "S92B_PAIRED_CONTRAST_DECODER_FROZEN_FOR_S93":
        raise RuntimeError(f"unexpected S92B outcome: {certificate.get('Outcome')}")

    payload = {
        "stage": "S92B-VALIDATION",
        "passed": True,
        "used_existing_licensed_kernel": True,
        "kernel_id": kernel_id,
        "real_outputs_created": False,
        "temporary_outputs_removed_after_validation": True,
        "certificate_result_hash": certificate.get("CertificateResultHash"),
        "candidate_hash": certificate.get("FrozenCandidateHash"),
        "selected_position": certificate.get("SelectedPosition"),
        "selected_feature": certificate.get("SelectedFeature"),
        "probe_text": probe_text,
        "results": results,
    }
    RUN_LOG.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    cleanup_token = server_token()
    cleanup_kernel = idle_kernel(cleanup_token)
    cleanup_session = uuid.uuid4().hex
    cleanup_ws = websocket.create_connection(
        f"ws://localhost:8888/api/kernels/{cleanup_kernel}/channels?token={cleanup_token}",
        timeout=2,
        origin="http://localhost:8888",
        http_proxy_host=None,
        http_proxy_port=None,
    )
    cleanup_paths = ",".join(f'"{path.as_posix()}"' for path in temporary_paths)
    try:
        cleanup_after = execute(
            cleanup_ws,
            cleanup_session,
            f'InputForm[Map[Function[p,If[FileExistsQ[p],DeleteFile[p]]],'
            f'{{{cleanup_paths}}}]]',
            timeout_seconds=30,
        )
    finally:
        cleanup_ws.close()
    if cleanup_after["status"] != "ok" or cleanup_after["errors"]:
        raise RuntimeError(f"S92B temporary cleanup failed: {cleanup_after}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
