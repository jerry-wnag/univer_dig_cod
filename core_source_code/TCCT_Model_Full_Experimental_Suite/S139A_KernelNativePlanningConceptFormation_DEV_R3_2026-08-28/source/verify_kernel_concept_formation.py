from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def main() -> int:
    protocol_path = ROOT / "protocol" / "frozen_protocol.json"
    protocol, protocol_hash = load(protocol_path), digest(protocol_path)
    source_map = {
        "FrozenGeometrySHA256": ROOT / "source" / "adaptive_geometry.py",
        "FrozenConceptDPSHA256": ROOT / "source" / "kernel_concept_dp.py",
        "FrozenTaskBuilderSHA256": ROOT / "source" / "build_kernel_concept_tasks.py",
        "FrozenWolframRunnerSHA256": ROOT / "source" / "run_kernel_concept_formation.wl",
        "FrozenOracleResponderSHA256": ROOT / "source" / "oracle_responder.py",
        "FrozenAuditorSHA256": ROOT / "diagnostic" / "prove_kernel_concept_formation.py",
        "FrozenScorerSHA256": ROOT / "source" / "score_kernel_concept_formation.py",
        "FrozenVerifierSHA256": Path(__file__),
    }
    hashes_pass = all(digest(path) == protocol[key] for key, path in source_map.items())
    public = load(ROOT / "input" / "public_tasks.json")
    manifest = load(ROOT / "sealed" / "materialization_manifest.json")
    result = load(ROOT / "results" / "kernel_native_concept_result.json")
    library = load(ROOT / "library" / "kernel_induced_concepts.json")
    certificate = load(ROOT / "diagnostic" / "kernel_concept_certificate.json")
    score = load(ROOT / "results" / "sealed_score.json")
    boundary_pass = public["ProtocolSHA256"] == manifest["ProtocolSHA256"] == result["ProtocolSHA256"] == \
        score["ProtocolSHA256"] == certificate["ProtocolSHA256"] == protocol_hash
    materialization_pass = len(public["SourceTasks"]) == 3 and len(public["TargetTasks"]) == 5 and \
        manifest["PostSeedWorldFilteringUsed"] is False and manifest["WorldReplacementAfterMaterializationUsed"] is False and \
        manifest["ConceptLabelsMaterialized"] is False and manifest["ConceptBodiesMaterialized"] is False
    kernel_formation_pass = result["ConceptBodiesCreatedByNativeKernel"] is True and \
        result["ConceptBodiesProvidedByGenerator"] is False and \
        result["KernelInducedConceptLibrarySHA256"] == digest(ROOT / "library" / "kernel_induced_concepts.json") and \
        canonical(result["KernelInducedConceptLibrary"]) == canonical(library)
    concept_replay_pass = score["KernelAndIndependentConceptBodiesMatch"] is True and \
        certificate["DifficultyCertificatePass"] is True
    oracle_rows = [json.loads(line) for line in (ROOT / "oracle" / "query_log.jsonl").read_text(
        encoding="utf-8").splitlines() if line]
    oracle_pass = len(oracle_rows) == result["OracleQueryLogLineCount"] and all(
        row["GeneratedByTCCTKernel"] is True and row["TestOutputAccessed"] is False and
        row["HiddenProgramAccessedByLearner"] is False for row in oracle_rows)
    evidence_pass = result["NativeWolframExecution"] is True and result["NativePreScorePass"] is True and \
        score["CapabilityGatePass"] is True and result["PairedDepthParity"] is True and \
        result["CoreRewriteFreezeDedupModified"] is False
    passed = hashes_pass and boundary_pass and materialization_pass and kernel_formation_pass and \
        concept_replay_pass and oracle_pass and evidence_pass
    verification = {
        "Stage": protocol["Stage"] + " verification", "FrozenSourceHashesPass": hashes_pass,
        "ProtocolBoundaryPass": boundary_pass, "FreshMaterializationPass": materialization_pass,
        "NativeKernelConceptFormationPass": kernel_formation_pass,
        "IndependentConceptInductionReplayPass": concept_replay_pass,
        "OracleBoundaryReplayPass": oracle_pass, "EvidenceIntegrityPass": evidence_pass,
        "CapabilityGatePass": passed, "CoreRewriteFreezeDedupModified": False,
        "OpenEndedConceptLanguageClaimed": False,
        "Conclusion": "VERIFIED_KERNEL_NATIVE_RELATIONAL_CONCEPT_FORMATION_PASS" if passed else
                      "KERNEL_NATIVE_RELATIONAL_CONCEPT_FORMATION_VERIFICATION_FAILURE",
    }
    destination = ROOT / "verification" / "independent_verification.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
