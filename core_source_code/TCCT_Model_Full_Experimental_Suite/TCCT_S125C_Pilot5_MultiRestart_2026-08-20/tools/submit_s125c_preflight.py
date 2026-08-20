import time
from queue import Empty

from jupyter_client import BlockingKernelClient


CONNECTION_FILE = r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development\runtime\jupyter_runtime_restart_20260819\kernel-f7a13dee-3aae-4f7c-8a56-3b370148f0b2.json"
SOURCE = r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development\TCCT_S124_T5R1_StrictFreshWorldGeneralizationAttribution.ipynb"
RUNNER = r"C:\Users\王鑫\Documents\Codex\2026-08-20\referenced-chatgpt-conversation-this-is-an\outputs\TCCT_S125C_Pilot5_MultiRestartMatchedComparison.wl"


def wl_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


code = "\n".join(
    [
        f'SetEnvironment["S125_T5R1_SOURCE"->{wl_string(SOURCE)}];',
        'SetEnvironment["S125_EXECUTION_MODE"->"JupyterKernel"];',
        'SetEnvironment["S125C_PREFLIGHT_ONLY"->"True"];',
        f'Get[{wl_string(RUNNER)}]',
    ]
)

client = BlockingKernelClient(connection_file=CONNECTION_FILE)
client.load_connection_file()
client.start_channels()
client.wait_for_ready(timeout=60)
message_id = client.execute(code, store_history=True, allow_stdin=False, stop_on_error=True)
deadline = time.time() + 180
try:
    while time.time() < deadline:
        try:
            message = client.get_iopub_msg(timeout=2)
        except Empty:
            continue
        if message.get("parent_header", {}).get("msg_id") != message_id:
            continue
        message_type = message.get("msg_type")
        content = message.get("content", {})
        if message_type == "stream":
            print(content.get("text", ""), end="", flush=True)
        elif message_type == "error":
            print("ERROR=" + content.get("evalue", ""), flush=True)
        elif message_type == "status" and content.get("execution_state") == "idle":
            break
finally:
    client.stop_channels()
