from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCHIVE = ROOT / "original_failure"
PYTHON = Path(r"E:\anaconda\python.exe")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")) + "\n", encoding="utf-8")


def encoded_bridge() -> str:
    root_b64 = base64.b64encode(str(ROOT).encode("utf-8")).decode("ascii")
    script = (
        f"$root=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('{root_b64}'));"
        f"$python='{PYTHON}';$responder=Join-Path $root 'source\\oracle_responder.py';"
        "if($env:TCCT_ORACLE_MODE -eq 'reset'){& $python $responder --reset;exit $LASTEXITCODE};"
        "& $python $responder --task-id $env:TCCT_TASK --query-id $env:TCCT_QUERY;exit $LASTEXITCODE"
    )
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def main() -> int:
    receipt = ROOT / "protocol" / "replay_r1_freeze_receipt.json"
    if receipt.exists():
        raise RuntimeError("R1 replay already frozen")
    original_protocol_path = ARCHIVE / "frozen_protocol.json"
    protocol = json.loads(original_protocol_path.read_text(encoding="utf-8"))
    protocol.update({
        "Stage": "S140-C DIAGNOSTIC R1 source-selectivity activation envelope replay",
        "EvidenceStatus": "RETROSPECTIVE_REPLAY_OF_FROZEN_S140B_HIGH_PREFIX_FAILURE",
        "ProtocolFrozenBeforeTaskMaterialization": False,
        "FreshTasksMaterializedAfterProtocolFreeze": False,
        "RetrospectiveReplay": True,
        "OriginalFailureConclusionPreserved": True,
        "PreviousR0InstrumentationFailurePreservedInSeparateDirectory": True,
        "ReplayRevision": "R1",
        "RepairMechanism": "SOURCE_CALIBRATED_MAXIMUM_PREFERRED_FRACTION_ACTIVATION_ENVELOPE",
        "TraceSemantics": "ROOT_CONCEPT_MATCH_RECORDED_AFTER_THE_SAME_ACTIVATION_ENVELOPE_USED_BY_PLANNING",
        "ActivationThresholdFixedConstant": False,
        "ActivationThresholdDerivedOnlyFromSourcePlanningEvents": True,
        "ConceptBodiesModified": False,
        "ExactDynamicProgrammingModified": False,
        "OracleBridgeEncodedCommand": encoded_bridge(),
        "FrozenConceptDPSHA256": digest(ROOT / "source" / "kernel_concept_dp.py"),
        "FrozenWolframRunnerSHA256": digest(ROOT / "source" / "run_kernel_concept_formation.wl"),
        "FrozenOracleResponderSHA256": digest(ROOT / "source" / "oracle_responder.py"),
        "FrozenAuditorSHA256": digest(ROOT / "diagnostic" / "prove_kernel_concept_formation.py"),
        "FrozenReplayVerifierSHA256": digest(ROOT / "diagnostic" / "verify_replay.py"),
        "OriginalFailedProtocolSHA256": digest(original_protocol_path),
        "OriginalFailedPublicSHA256": digest(ARCHIVE / "input" / "public_tasks.json"),
        "OriginalFailedTestOutputsSHA256": digest(ARCHIVE / "sealed" / "test_outputs.json"),
        "OriginalFailedOracleResponsesSHA256": digest(ARCHIVE / "sealed" / "oracle_responses.json"),
        "OriginalFailedNativeResultSHA256": digest(ARCHIVE / "kernel_native_concept_result.json"),
        "OriginalFailedScoreSHA256": digest(ARCHIVE / "sealed_score.json"),
        "PDFRequested": False,
    })
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    write(protocol_path, protocol)
    protocol_hash = digest(protocol_path)
    for relative in ("input/public_tasks.json", "sealed/test_outputs.json",
                     "sealed/oracle_responses.json", "sealed/materialization_manifest.json"):
        path = ROOT / relative
        value = json.loads((ARCHIVE / relative).read_text(encoding="utf-8"))
        value["ProtocolSHA256"] = protocol_hash
        if relative == "input/public_tasks.json":
            value["Stage"] = protocol["Stage"]
        if relative == "sealed/materialization_manifest.json":
            value["RetrospectiveReplayMetadataRewrapped"] = True
        write(path, value)
    write(receipt, {
        "ProtocolSHA256": protocol_hash, "RetrospectiveReplay": True,
        "OriginalFailurePreserved": True, "HiddenTaskBodiesModified": False,
    })
    print(json.dumps({"ProtocolSHA256": protocol_hash, "RetrospectiveReplay": True},
                     separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
