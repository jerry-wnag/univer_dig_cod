import json
import os
import time
from pathlib import Path
from queue import Empty

from jupyter_client import KernelManager

from recover_kernel_and_run_s87c import NOTEBOOK_PATH, RECOVERY_RESULT, selected_cells


DIRECT_RESULT = RECOVERY_RESULT.with_name("TCCT_S87C_DirectKernelRun_Result.json")


def execute(client, code: str, label: str, timeout_seconds: int) -> dict:
    msg_id = client.execute(
        code,
        silent=False,
        store_history=False,
        allow_stdin=False,
        stop_on_error=True,
    )
    started = time.monotonic()
    last_update = started
    outputs = []
    errors = []
    idle_seen = False
    print(f"{label}: submitted", flush=True)
    while time.monotonic() - started < timeout_seconds:
        try:
            message = client.get_iopub_msg(timeout=1)
        except Empty:
            now = time.monotonic()
            if now - last_update >= 30:
                print(f"{label}: still running ({int(now - started)} s)", flush=True)
                last_update = now
            continue
        parent = message.get("parent_header", {})
        if parent.get("msg_id") != msg_id:
            continue
        msg_type = message.get("msg_type")
        content = message.get("content", {})
        if msg_type == "status" and content.get("execution_state") == "idle":
            idle_seen = True
        elif msg_type == "stream":
            outputs.append({"type": "stream", "text": content.get("text", "")})
        elif msg_type in {"display_data", "execute_result"}:
            data = content.get("data", {})
            outputs.append(
                {
                    "type": msg_type,
                    "text_plain": data.get("text/plain", ""),
                }
            )
        elif msg_type == "error":
            errors.append(
                {
                    "ename": content.get("ename", ""),
                    "evalue": content.get("evalue", ""),
                    "traceback": content.get("traceback", []),
                }
            )
        if idle_seen:
            elapsed = time.monotonic() - started
            print(f"{label}: finished in {elapsed:.1f} s", flush=True)
            return {
                "label": label,
                "elapsed_seconds": elapsed,
                "outputs": outputs,
                "errors": errors,
            }
    raise TimeoutError(f"{label} timed out after {timeout_seconds} seconds")


def plain_text(result: dict) -> str:
    chunks = []
    for output in result.get("outputs", []):
        if output.get("text_plain"):
            chunks.append(output["text_plain"])
        if output.get("text"):
            chunks.append(output["text"])
    return "\n".join(chunks)


def compact(result: dict) -> dict:
    return {
        "label": result.get("label"),
        "elapsed_seconds": result.get("elapsed_seconds"),
        "errors": result.get("errors", []),
        "output_count": len(result.get("outputs", [])),
    }


def main() -> None:
    os.environ["JUPYTER_DATA_DIR"] = r"E:\engine_wolf\jupyter\data"
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    manager = KernelManager(kernel_name="wolframlanguage15")
    print("direct kernel: starting", flush=True)
    manager.start_kernel()
    client = manager.client()
    client.start_channels()
    records = []
    try:
        client.wait_for_ready(timeout=240)
        print("direct kernel: ready", flush=True)
        probe = execute(client, "InputForm[1+1]", "arithmetic probe", 30)
        records.append(compact(probe))
        if probe["errors"] or "2" not in plain_text(probe):
            raise RuntimeError(f"arithmetic probe failed: {plain_text(probe)}")

        for label, source, timeout_seconds in selected_cells():
            result = execute(client, source, label, timeout_seconds)
            records.append(compact(result))
            if result["errors"]:
                raise RuntimeError(f"{label} failed: {result['errors']}")

        certificate = execute(client, "InputForm[cert87C]", "S87C certificate", 30)
        records.append(compact(certificate))
        certificate_text = plain_text(certificate)
        if certificate["errors"] or "Stage -> S87C" not in certificate_text:
            raise RuntimeError(f"invalid S87C certificate: {certificate_text}")
        payload = {
            "notebook": NOTEBOOK_PATH,
            "mode": "fresh temporary direct Jupyter kernel",
            "steps": records,
            "certificate_text": certificate_text,
        }
        DIRECT_RESULT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"result: {DIRECT_RESULT}", flush=True)
        print(certificate_text, flush=True)
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)
        print("direct kernel: stopped", flush=True)


if __name__ == "__main__":
    main()
