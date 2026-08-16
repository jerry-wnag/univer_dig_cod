"""Export a minimal, immutable S90 world archive from the completed live kernel.

The archive is post-hoc benchmark input.  It contains cached S90 feature vectors,
targets, and the two predictions already produced during S90; it does not rerun
propagation, train a model, or modify any TCCT definition.
"""

import json
import os
import uuid
from pathlib import Path

import websocket

from run_s89_preflight_existing_kernel import execute, idle_kernel, server_token


ROOT = Path(__file__).resolve().parent
ARTIFACT_DIR = ROOT / "artifacts"
ARCHIVE = ARTIFACT_DIR / "TCCT_S90_BenchmarkWorlds.json"
MANIFEST = ARTIFACT_DIR / "TCCT_S90_BenchmarkWorlds_Manifest.json"


def wolfram_path(path: Path) -> str:
    return path.resolve().as_posix().replace('"', '\\"')


def main() -> None:
    os.environ["NO_PROXY"] = "localhost,127.0.0.1"
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    if ARCHIVE.exists():
        raise RuntimeError("S90 benchmark archive already exists; preserve it")

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
InputForm[Module[
  {requiredKeys, rows, payload, archive, manifest, archiveResult, manifestResult},
  requiredKeys = {
    "Topology", "Depth", "AlgebraTuple", "GraphCondition", "Answer",
    "Target", "Prediction", "LegacyPrediction", "FeatureVector"
  };
  If[
    !ValueQ[blindWorlds90] || !ValueQ[cert90] ||
    !SameQ[Length[blindWorlds90], 1296] ||
    !SameQ[Lookup[cert90, "Outcome", Missing[]],
      "S90_BLIND_INTERVENTION_ALGEBRA_PASS"] ||
    !And @@ (Function[row,
      And @@ (Function[key, KeyExistsQ[row, key]] /@ requiredKeys)
    ] /@ blindWorlds90),
    Return[<|"ExportSucceeded" -> False, "Reason" -> "S90_STATE_INVALID"|>]
  ];
  rows = KeyTake[#, requiredKeys] & /@ blindWorlds90;
  If[
    !And @@ (VectorQ[Lookup[#, "FeatureVector", {}], IntegerQ] &&
        Length[Lookup[#, "FeatureVector", {}]] === 27 & /@ rows),
    Return[<|"ExportSucceeded" -> False, "Reason" -> "FEATURE_VECTOR_INVALID"|>]
  ];
  payload = <|
    "Stage" -> "S90-ARCHIVE",
    "Name" -> "PostHocBenchmarkWorldArchive",
    "BlindClaim" -> False,
    "SourceStage" -> "S90",
    "SourceOutcome" -> cert90["Outcome"],
    "SourceCandidateHash" -> cert90["CandidateHash"],
    "SourceProtocolHash" -> cert90["ProtocolHash"],
    "SourceTestDefinitionHash" -> cert90["TestDefinitionHash"],
    "WorldCount" -> Length[rows],
    "TargetCounts" -> Counts[Lookup[rows, "Target"]],
    "Rows" -> rows
  |>;
  archive = Append[payload,
    "ArchivePayloadHash" -> Hash[Normal[payload], "SHA256", "HexString"]];
  manifest = KeyDrop[archive, {"Rows"}];
  archiveResult = Quiet@Check[
    Export["''' + wolfram_path(ARCHIVE) + r'''", archive, "RawJSON"], $Failed];
  manifestResult = Quiet@Check[
    Export["''' + wolfram_path(MANIFEST) + r'''", manifest, "RawJSON"], $Failed];
  <|
    "ExportSucceeded" -> And[
      StringQ[archiveResult], StringQ[manifestResult],
      FileExistsQ["''' + wolfram_path(ARCHIVE) + r'''"],
      FileExistsQ["''' + wolfram_path(MANIFEST) + r'''"]
    ],
    "ArchivePayloadHash" -> archive["ArchivePayloadHash"],
    "WorldCount" -> archive["WorldCount"],
    "TargetCounts" -> archive["TargetCounts"],
    "OriginalFrozenModelChanged" -> False,
    "CoreChanged" -> False,
    "TrainingRun" -> False
  |>
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
        raise RuntimeError(f"archive export failed: {output}")
    if not ARCHIVE.exists() or not MANIFEST.exists():
        raise RuntimeError("kernel reported success but archive files are missing")
    print(json.dumps({
        "kernel_id": kernel_id,
        "archive": str(ARCHIVE),
        "manifest": str(MANIFEST),
        "kernel_output": output,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
