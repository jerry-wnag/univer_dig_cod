"""Export immutable S92 feature rows from the completed live blind-test kernel."""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts"
ARCHIVE = ARTIFACT_DIR / "TCCT_S92_FailureAuditWorlds.json"
MANIFEST = ARTIFACT_DIR / "TCCT_S92_FailureAuditWorlds_Manifest.json"


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists():
        raise RuntimeError("S92 failure-audit archive already exists; preserve it")
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
    code = r'''
InputForm[Module[{requiredKeys,rows,payload,archive,manifest,archivePath,
manifestPath,archiveResult,manifestResult},
requiredKeys={"Topology","Depth","GraphCondition","Answer","Target",
"ReferenceAction","Prediction","LegacyPrediction","FeatureVector","Cardinality"};
If[!ValueQ[blindWorlds92]||!ValueQ[cert92]||
!SameQ[Length[blindWorlds92],80]||
!SameQ[Lookup[cert92,"Outcome",Missing[]],
"S92_VALID_BLIND_FAILURE_DO_NOT_RETUNE"]||
!And@@(Function[row,And@@(Function[key,KeyExistsQ[row,key]]/@requiredKeys)]/@
blindWorlds92),Return[<|"ExportSucceeded"->False,"Reason"->"S92_STATE_INVALID"|>]];
rows=KeyTake[#,requiredKeys]&/@blindWorlds92;
If[!And@@(VectorQ[Lookup[#,"FeatureVector",{}],IntegerQ]&&
Length[Lookup[#,"FeatureVector",{}]]===27&/@rows),
Return[<|"ExportSucceeded"->False,"Reason"->"FEATURE_VECTOR_INVALID"|>]];
payload=<|"Stage"->"S92-ARCHIVE","Name"->"PostHocFailureAuditArchive",
"BlindClaim"->False,"SourceStage"->"S92","SourceOutcome"->cert92["Outcome"],
"SourceCandidateHash"->cert92["CandidateHash"],
"SourceProtocolHash"->cert92["ProtocolHash"],
"SourceTestDefinitionHash"->cert92["TestDefinitionHash"],
"SourceBlindResultHash"->cert92["BlindResultHash"],
"WorldCount"->Length[rows],"TargetCounts"->Counts[Lookup[rows,"Target"]],
"Rows"->rows|>;
archive=Append[payload,"ArchivePayloadHash"->
Hash[Normal[payload],"SHA256","HexString"]];
manifest=KeyDrop[archive,{"Rows"}];
archivePath=FileNameJoin[{Directory[],"artifacts",
"TCCT_S92_FailureAuditWorlds.json"}];
manifestPath=FileNameJoin[{Directory[],"artifacts",
"TCCT_S92_FailureAuditWorlds_Manifest.json"}];
archiveResult=Quiet@Check[Export[archivePath,archive,"RawJSON"],$Failed];
manifestResult=Quiet@Check[Export[manifestPath,manifest,"RawJSON"],$Failed];
<|"ExportSucceeded"->And[StringQ[archiveResult],StringQ[manifestResult],
FileExistsQ[archivePath],FileExistsQ[manifestPath]],
"ArchivePayloadHash"->archive["ArchivePayloadHash"],
"WorldCount"->archive["WorldCount"],"TargetCounts"->archive["TargetCounts"],
"CoreChanged"->False,"FrozenDecoderChanged"->False,"TrainingRun"->False|>
]]
'''
    try:
        result = execute(ws, session, code, timeout_seconds=60)
    finally:
        ws.close()
    if result["status"] != "ok" or result["errors"]:
        raise RuntimeError(result)
    output = "\n".join(result["outputs"])
    if '"ExportSucceeded" -> True' not in output:
        raise RuntimeError(f"S92 archive export failed: {output}")
    if not ARCHIVE.exists() or not MANIFEST.exists():
        raise RuntimeError("kernel reported success but archive files are missing")
    print(json.dumps({"kernel_id": kernel_id, "archive": str(ARCHIVE),
        "manifest": str(MANIFEST), "kernel_output": output},
        ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
