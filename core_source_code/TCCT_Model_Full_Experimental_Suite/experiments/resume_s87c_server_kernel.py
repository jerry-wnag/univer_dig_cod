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
RESUME_RESULT = RECOVERY_RESULT.with_name("TCCT_S87C_ResumedKernelRun_Result.json")


def main() -> None:
    client = BlockingKernelClient(connection_file=str(CONNECTION))
    client.load_connection_file()
    client.start_channels()
    records = []
    try:
        print("resume: waiting for the in-flight S87A trace", flush=True)
        client.wait_for_ready(timeout=1200)
        print("resume: kernel is responsive", flush=True)
        probe_code = r'''
InputForm[<|
"AllWorldsReady"->And[
ValueQ[allWorlds87A],ListQ[allWorlds87A],Length[allWorlds87A]===392
],
"SummaryReady"->And[
ValueQ[reproducedSummary87A],
reproducedSummary87A["Worlds"]===392
]
|>]
'''.strip()
        probe = execute(client, probe_code, "S87A completion probe", 30)
        records.append(compact(probe))
        probe_text = plain_text(probe)
        if (
            probe["errors"]
            or "AllWorldsReady -> True" not in probe_text
            or "SummaryReady -> True" not in probe_text
        ):
            raise RuntimeError(f"in-flight S87A trace did not complete: {probe_text}")

        remaining = selected_cells()[5:]
        for label, source, timeout_seconds in remaining:
            if label == "S87C research":
                timeout_seconds = 1800
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
            "mode": "resumed server-owned activated Wolfram kernel",
            "connection_file": CONNECTION.name,
            "steps": records,
            "certificate_text": certificate_text,
        }
        RESUME_RESULT.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"result: {RESUME_RESULT}", flush=True)
        print(certificate_text, flush=True)
    finally:
        client.stop_channels()
        print("resume: channels closed", flush=True)


if __name__ == "__main__":
    main()
