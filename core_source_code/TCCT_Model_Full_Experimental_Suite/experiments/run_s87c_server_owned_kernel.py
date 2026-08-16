import json
from pathlib import Path

from jupyter_client import BlockingKernelClient

from recover_kernel_and_run_s87c import NOTEBOOK_PATH, RECOVERY_RESULT, selected_cells
from run_s87c_fresh_kernel import compact, execute, plain_text


ROOT = Path(__file__).resolve().parent
CONNECTION = (
    ROOT
    / ".jupyter_runtime"
    / "kernel-eb44601d-3795-4d40-bc41-54c9f87aa768.json"
)
SERVER_RESULT = RECOVERY_RESULT.with_name(
    "TCCT_S87C_ServerOwnedKernelRun_Result.json"
)


def main() -> None:
    client = BlockingKernelClient(connection_file=str(CONNECTION))
    client.load_connection_file()
    client.start_channels()
    records = []
    try:
        print("server-owned kernel: connecting", flush=True)
        client.wait_for_ready(timeout=180)
        print("server-owned kernel: ready", flush=True)
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
            "mode": "server-owned activated Wolfram kernel",
            "connection_file": CONNECTION.name,
            "steps": records,
            "certificate_text": certificate_text,
        }
        SERVER_RESULT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"result: {SERVER_RESULT}", flush=True)
        print(certificate_text, flush=True)
    finally:
        client.stop_channels()
        print("server-owned kernel: channels closed", flush=True)


if __name__ == "__main__":
    main()
