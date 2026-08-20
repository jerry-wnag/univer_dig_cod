import time
from queue import Empty

from jupyter_client import BlockingKernelClient


CONNECTION_FILE = r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development\runtime\jupyter_runtime_restart_20260819\kernel-9f89d6ac-4a9a-4f02-b9dc-bc3131472762.json"

code = r'''
Print["S125C_PROBE_VERSION=",$Version];
Print["S125C_PROBE_GLOBAL_SYMBOL_COUNT=",Length[Names["Global`*"]]];
Print["S125C_PROBE_T5S_SUMMARY=",Names["Global`t5sSummary"]];
Print["S125C_PROBE_MESSAGES=",$MessageList];
'''

client = BlockingKernelClient(connection_file=CONNECTION_FILE)
client.load_connection_file()
client.start_channels()
client.wait_for_ready(timeout=60)
message_id = client.execute(code, store_history=False, allow_stdin=False, stop_on_error=True)
deadline = time.time() + 90
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
