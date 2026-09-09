from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def dump(relative: str, value: Any) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def digest(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main() -> int:
    protocol = load("protocol/frozen_protocol.json")
    constructor = load("audit/private_fresh_constructor_audit.json")
    py = load("results/python_frozen_fresh_result.json")
    wl = load("results/wolfram_frozen_fresh_audit.json")
    py_rows, wl_rows = py["CaseRows"], wl["CaseRows"]
    checks = {
        "FrozenSeedMaterializationPass": constructor["ConstructorPass"],
        "PythonFrozenFreshPass": py["PythonFrozenFreshPass"],
        "WolframFrozenFreshAuditPass": wl["WolframFrozenFreshAuditPass"],
        "FiveStatusParity": [row["Status"] for row in py_rows]
            == [row["Status"] for row in wl_rows] == protocol["ExpectedStatuses"],
        "CandidateAndSemanticCountParity": [
            (row["ExactMetaProgramCount"], row["SemanticClassCount"]) for row in py_rows]
            == [(row["ExactMetaProgramCount"], row["SemanticClassCount"]) for row in wl_rows],
        "ThreePositiveCasesFreeze": all(py_rows[index]["Frozen"] for index in (0, 1, 2)),
        "ThreePositiveHoldoutsExact": all(row["Exact"] for row in py["SealedFreshHoldoutRows"])
            and all(row["Exact"] for row in wl["HoldoutRows"]),
        "AmbiguousNearAndRandomSafe": not py_rows[3]["Frozen"] and not py_rows[4]["Frozen"]
            and not py["AuxiliaryRandomControl"]["Frozen"],
        "AllCurrentGrammarCandidatesEliminatedInBothEngines": all(
            row["CurrentGrammarExactCandidateCount"] == 0 for row in py_rows)
            and py["AuxiliaryRandomControl"]["CurrentGrammarExactCandidateCount"] == 0
            and all(row["ExactCandidateCount"] == 0 for row in wl["CurrentGrammarRows"]),
        "NoWorldReplacement": not protocol["Freshness"]["FailureWorldReplacementAllowed"],
        "CoreUnchanged": not protocol["CoreRewriteFreezeDedupModified"],
        "ClaimBoundaryPreserved": not protocol["OpenPrimitiveInventionClaimAllowed"],
    }
    passed = all(checks.values())
    result = {
        "Stage": protocol["Stage"], "EvidenceStatus": protocol["EvidenceStatus"],
        "Checks": checks, "StrictFreshPass": passed,
        "CaseStatuses": [row["Status"] for row in py_rows],
        "MetaExactProgramCounts": [row["ExactMetaProgramCount"] for row in py_rows],
        "FullDomainSemanticClassCounts": [row["SemanticClassCount"] for row in py_rows],
        "SelectedFreshExtensionMetrics": [{
            "CaseID": row["CaseID"],
            "AnonymousOperatorID": row["SelectedProposal"]["AnonymousOperatorID"],
            "NANDCount": row["SelectedProposal"]["NANDCount"],
            "DescriptionLengthBits": row["SelectedProposal"]["DescriptionLengthBits"],
            "RawResidualBits": row["SelectedProposal"]["RawResidualBits"],
            "CompressionGainBits": row["SelectedProposal"]["CompressionGainBits"],
        } for row in py_rows if row["SelectedProposal"] is not None],
        "SealedFreshHoldoutExactCounts": [{
            "CaseID": row["CaseID"], "Exact": f"{row['ExactApplicationCount']}/{row['ApplicationCount']}"
        } for row in py["SealedFreshHoldoutRows"]],
        "AuxiliaryRandomStatus": py["AuxiliaryRandomControl"]["Status"],
        "CodeSHA256": {
            "FrozenProtocol": digest("protocol/frozen_protocol.json"),
            "Materializer": digest("source/materialize_fresh_cases.py"),
            "PythonRunner": digest("source/run_frozen_python_fresh_extension.py"),
            "WolframAudit": digest("source/run_wolfram_fresh_extension_audit.wl"),
            "Finalizer": digest("source/finalize_fresh_gate.py"),
        },
        "AllowedClaim": "frozen fresh evidence for bounded residual-driven language extension proposal and safe abstention under a fixed NAND meta-language",
        "DisallowedClaims": [
            "replicated multi-seed language extension",
            "open-ended primitive invention",
            "language-independent invention",
            "unbounded self-modifying cognition",
            "ARC-AGI capability"
        ],
        "Conclusion": "S144C_FROZEN_FRESH_LANGUAGE_EXTENSION_PASS" if passed
            else "S144C_FROZEN_FRESH_LANGUAGE_EXTENSION_FAIL",
    }
    dump("results/final_fresh_gate.json", result)
    print(json.dumps({"Pass": passed, "Conclusion": result["Conclusion"],
        "Statuses": result["CaseStatuses"], "MetaExact": result["MetaExactProgramCounts"],
        "SemanticClasses": result["FullDomainSemanticClassCounts"],
        "HoldoutExact": result["SealedFreshHoldoutExactCounts"]}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
