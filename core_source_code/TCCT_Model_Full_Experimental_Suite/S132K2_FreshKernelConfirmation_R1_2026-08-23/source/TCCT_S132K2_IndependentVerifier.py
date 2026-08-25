"""Independent verifier for S132-K2 fresh kernel confirmation."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_hashes(package: Path) -> dict[str, str]:
    return {
        path.name: sha256(path)
        for path in sorted((package / "source").iterdir())
        if path.is_file()
    }


def compare_summary(independent: dict[str, int], reported: dict[str, Any]) -> bool:
    return all(int(reported[key]) == value for key, value in independent.items())


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K2_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K2_freeze_receipt.json"
    public_path = package / "input" / "S132K2_public_input.json"
    oracle_path = package / "oracle" / "S132K2_oracle_tables.json"
    certified_path = package / "input" / "certified_automata.json"
    discovery_path = package / "discovery" / "S132K2_discovery_result.json"
    result_path = package / "results" / "S132K2_result.json"
    controls_path = package / "negative_controls" / "S132K2_random_automata.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    public = json.loads(public_path.read_text(encoding="utf-8"))
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    certified = json.loads(certified_path.read_text(encoding="utf-8"))
    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    result = json.loads(result_path.read_text(encoding="utf-8"))
    controls = json.loads(controls_path.read_text(encoding="utf-8"))["Controls"]

    source_hash_pass = source_hashes(package) == manifest["SourceHashes"]
    receipt_pass = (
        sha256(manifest_path) == receipt["ManifestSHA256"]
        and receipt["WorldsMaterialized"] is True
        and receipt["MaterializedAfterManifestFreeze"] is True
        and receipt["DiscoveryRunComplete"] is True
        and receipt["CertifiedAutomataMaterialized"] is True
        and sha256(public_path) == receipt["PublicInputSHA256"]
        and sha256(oracle_path) == receipt["OracleSHA256"]
        and sha256(discovery_path) == receipt["DiscoveryResultSHA256"]
        and sha256(certified_path) == receipt["CertifiedAutomataSHA256"]
    )

    exact_count = sum(
        row["Active"].get("ExactCertified") is True for row in discovery["FormalResults"]
    )
    discovery_pass = exact_count == len(manifest["WorldSpecifications"]) == 5

    oracle_by_id = {world["WorldID"]: world["TransitionTable"] for world in oracle["Worlds"]}
    public_ids = {world["WorldID"] for world in public["Worlds"]}
    certified_automata = certified["Automata"]
    certified_boundary_pass = (
        certified["ProgramASTRetained"] is False
        and certified["GeneratorTruthRead"] is False
        and certified["OracleTransitionTablesReadDuringDerivation"] is False
        and {world["WorldID"] for world in certified_automata} == public_ids
        and all(
            world["TransitionTable"] == oracle_by_id[world["WorldID"]]
            for world in certified_automata
        )
    )

    helper = load_module(
        package / "source" / "TCCT_S132K1_IndependentVerifier.py",
        "s132k2_independent_quotient_helper",
    )
    maximum_length = int(manifest["MaximumWordLength"])
    reported_by_id = {world["WorldID"]: world for world in result["StructuredResults"]}
    structured_audits = []
    for index, world in enumerate(certified_automata):
        independent = helper.quotient_summary(world["TransitionTable"], maximum_length)
        reported = reported_by_id[world["WorldID"]]["Quotient"]
        relabeled = helper.relabel(
            world["TransitionTable"], int(manifest["StateRelabelSeeds"][index])
        )
        relabel_pass = independent == helper.quotient_summary(relabeled, maximum_length)
        structured_audits.append(
            {
                "WorldID": world["WorldID"],
                "IndependentSummary": independent,
                "ReportedSummaryPass": compare_summary(independent, reported),
                "IndependentStateRelabelingPass": relabel_pass,
            }
        )

    control_audits = []
    for control in controls:
        independent = helper.quotient_summary(control["TransitionTable"], maximum_length)
        rank_pass = (
            helper.action_ranks(control["TransitionTable"])
            == [int(value) for value in control["TargetActionImageRanks"]]
            == [int(value) for value in control["ControlActionImageRanks"]]
        )
        control_audits.append(
            {
                "Replicate": control["Replicate"],
                "WorldID": control["WorldID"],
                "ReportedSummaryPass": compare_summary(independent, control["Quotient"]),
                "RankMatchingPass": rank_pass,
                "IndependentFalseEquivalenceCount": independent["FalseEquivalenceCount"],
            }
        )

    structured_pass = all(
        audit["ReportedSummaryPass"]
        and audit["IndependentStateRelabelingPass"]
        and audit["IndependentSummary"]["FalseEquivalenceCount"] == 0
        for audit in structured_audits
    )
    controls_pass = all(
        audit["ReportedSummaryPass"]
        and audit["RankMatchingPass"]
        and audit["IndependentFalseEquivalenceCount"] == 0
        for audit in control_audits
    )

    paired_checks = []
    for world in result["StructuredResults"]:
        values = [
            int(control["Heldout"]["ActionTokenReduction"])
            for control in controls
            if control["WorldID"] == world["WorldID"]
        ]
        mean = sum(values) / len(values)
        structured_reduction = int(world["Heldout"]["ActionTokenReduction"])
        paired_checks.append(
            {
                "WorldID": world["WorldID"],
                "StructuredReduction": structured_reduction,
                "FiveControlMean": mean,
                "Pass": structured_reduction > mean,
            }
        )

    result_boundary_pass = (
        result["FreshWorldsMaterializedAfterProtocolFreeze"] is True
        and result["K1MechanismModified"] is False
        and result["ProgramASTReadByConceptLearner"] is False
        and int(result["ConceptPositiveWorldCount"]) == 5
        and int(result["ReductionPositiveWorldCount"]) == 5
        and result["StructuredAllRewritesExact"] is True
        and int(result["RewriteDisabledAblationReduction"]) == 0
        and result["RandomControlsAllRewritesExact"] is True
        and all(check["Pass"] for check in paired_checks)
    )
    evidence_integrity = (
        source_hash_pass
        and receipt_pass
        and discovery_pass
        and certified_boundary_pass
        and structured_pass
        and controls_pass
        and result_boundary_pass
    )
    confirmed = evidence_integrity and result["FreshKernelConfirmationPass"] is True
    return {
        "Stage": "S132-K2 independent fresh-world verification",
        "SourceHashPass": source_hash_pass,
        "PreWorldFreezeAndPhaseOrderPass": receipt_pass,
        "FreshDiscoveryExactCount": exact_count,
        "FreshDiscoveryPass": discovery_pass,
        "CertifiedAutomataEqualOraclePass": certified_boundary_pass,
        "StructuredAudits": structured_audits,
        "IndependentStructuredQuotientPass": structured_pass,
        "RandomControlAudits": control_audits,
        "IndependentRandomControlPass": controls_pass,
        "PairedAdvantageChecks": paired_checks,
        "ResultBoundaryPass": result_boundary_pass,
        "IndependentHeldoutRNGReproduction": False,
        "EvidenceIntegrityPass": evidence_integrity,
        "FreshKernelTransformationQuotientConfirmed": confirmed,
        "OpenEndedPrimitiveInventionConfirmed": False,
        "FinalConclusion": (
            "VERIFIED_FRESH_KERNEL_TRANSFORMATION_QUOTIENT_CONFIRMATION"
            if confirmed
            else "EVIDENCE_VALID_BUT_FRESH_KERNEL_GATE_NOT_PASSED"
            if evidence_integrity
            else "VERIFICATION_FAILED"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    package = args.package.resolve()
    result = verify(package)
    output = package / "verification" / "S132K2_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
