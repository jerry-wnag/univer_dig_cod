import time
from queue import Empty

from jupyter_client import BlockingKernelClient


CONNECTION_FILE = r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development\runtime\jupyter_runtime_restart_20260819\kernel-f7a13dee-3aae-4f7c-8a56-3b370148f0b2.json"

code = r'''
records={
  <|"Seed"->1258613,"Net"->netC,"ValidationBalancedAccuracy"->0.71|>,
  <|"Seed"->1258611,"Net"->netA,"ValidationBalancedAccuracy"->0.74|>,
  <|"Seed"->1258612,"Net"->netB,"ValidationBalancedAccuracy"->0.74|>
};
metrics=KeyDrop[#,"Net"]&/@records;
valid=Select[records,Function[record,NumericQ[Lookup[record,"ValidationBalancedAccuracy"]]&&Lookup[record,"ValidationBalancedAccuracy"]>=0.60]];
selected=First@SortBy[valid,Function[record,{-Lookup[record,"ValidationBalancedAccuracy"],Lookup[record,"Seed"]}]];
Print["S125C_KEYDROP_PASS=",FreeQ[metrics,"Net"]&&Length[metrics]===3];
Print["S125C_SELECTION_PASS=",Lookup[selected,"Seed"]===1258611];
Print["S125C_SELECTED_SEED=",Lookup[selected,"Seed"]];
Clear[records,metrics,valid,selected];
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
