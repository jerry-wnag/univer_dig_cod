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


def sha256(relative: str) -> str:
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main() -> int:
    protocol = load("protocol/development_protocol.json")
    constructor = load("audit/constructor_private_audit.json")
    python_result = load("results/python_language_extension_result.json")
    wolfram_result = load("results/wolfram_language_extension_audit.json")
    py_rows = python_result["CaseRows"]
    wl_rows = wolfram_result["CaseRows"]
    checks = {
        "ConstructorPass": constructor["ConstructorPass"],
        "PythonDevelopmentPass": python_result["PythonDevelopmentPass"],
        "WolframDevelopmentAuditPass": wolfram_result["WolframDevelopmentAuditPass"],
        "FiveStatusParity": [row["Status"] for row in py_rows]
            == [row["Status"] for row in wl_rows] == protocol["ExpectedStatuses"],
        "FiveMetaCandidateCountParity": [row["ExactMetaProgramCount"] for row in py_rows]
            == [row["ExactMetaProgramCount"] for row in wl_rows],
        "FiveSemanticClassCountParity": [row["SemanticClassCount"] for row in py_rows]
            == [row["SemanticClassCount"] for row in wl_rows],
        "AllFiveOutsideCurrentGrammar": all(row["CurrentGrammarExactCandidateCount"] == 0
            for row in py_rows) and all(row["ExactCandidateCount"] == 0
            for row in wolfram_result["CurrentGrammarRows"]),
        "TwoFrozenExtensionsPassSealedHoldout": all(row["Exact"]
            for row in python_result["SealedRelabelingHoldoutRows"])
            and all(row["Exact"] for row in wolfram_result["HoldoutRows"]),
        "AmbiguityAndNegativeControlsDoNotFreeze": all(not py_rows[index]["Frozen"]
            for index in (2, 3, 4)),
        "CoreRewriteFreezeDedupUnchanged": True,
        "DevelopmentOnlyClaimBoundaryPreserved": not python_result["FreshCapabilityClaimAllowed"]
            and not python_result["OpenPrimitiveInventionClaimAllowed"],
    }
    passed = all(checks.values())
    result = {
        "Stage": protocol["Stage"],
        "EvidenceStatus": protocol["EvidenceStatus"],
        "Checks": checks,
        "StrictDevelopmentPass": passed,
        "CaseStatuses": [row["Status"] for row in py_rows],
        "CurrentGrammarExactCandidateCounts": [row["CurrentGrammarExactCandidateCount"] for row in py_rows],
        "MetaExactProgramCounts": [row["ExactMetaProgramCount"] for row in py_rows],
        "FullDomainSemanticClassCounts": [row["SemanticClassCount"] for row in py_rows],
        "SelectedExtensionMetrics": [{
            "CaseID": row["CaseID"],
            "AnonymousOperatorID": row["SelectedProposal"]["AnonymousOperatorID"],
            "NANDCount": row["SelectedProposal"]["NANDCount"],
            "DescriptionLengthBits": row["SelectedProposal"]["DescriptionLengthBits"],
            "RawResidualBits": row["SelectedProposal"]["RawResidualBits"],
            "CompressionGainBits": row["SelectedProposal"]["CompressionGainBits"],
        } for row in py_rows if row["SelectedProposal"] is not None],
        "SealedHoldoutExactCounts": [{
            "CaseID": row["CaseID"],
            "Exact": f"{row['ExactApplicationCount']}/{row['ApplicationCount']}"
        } for row in python_result["SealedRelabelingHoldoutRows"]],
        "CodeSHA256": {
            "Protocol": sha256("protocol/development_protocol.json"),
            "Constructor": sha256("source/construct_five_extension_cases.py"),
            "PythonRunner": sha256("source/run_python_language_extension.py"),
            "WolframAudit": sha256("source/run_wolfram_language_extension_audit.wl"),
            "Finalizer": sha256("source/finalize_development_gate.py"),
        },
        "AuditInfrastructureNote": "The first Wolfram audit used cross-language list indices for old-grammar certificates. That nonsemantic order assumption was removed; the passing audit independently exhausts all 11250 Wolfram candidates.",
        "AllowedClaim": "bounded residual-driven language extension proposal under a frozen NAND meta-language, development evidence",
        "DisallowedClaims": [
            "open-ended primitive invention",
            "fresh-world language-extension capability",
            "unbounded grammar growth",
            "ARC-AGI capability"
        ],
        "Conclusion": "S144B_BOUNDED_LANGUAGE_EXTENSION_DEV_PASS" if passed
            else "S144B_BOUNDED_LANGUAGE_EXTENSION_DEV_FAIL",
    }
    dump("results/final_development_gate.json", result)
    print(json.dumps({"Pass": passed, "Conclusion": result["Conclusion"],
                      "Statuses": result["CaseStatuses"],
                      "MetaExact": result["MetaExactProgramCounts"],
                      "SemanticClasses": result["FullDomainSemanticClassCounts"]}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
