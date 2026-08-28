from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    protocol = read(ROOT / "protocol" / "frozen_protocol.json")
    native = read(ROOT / "results" / "kernel_native_concept_result.json")
    score = read(ROOT / "results" / "sealed_score.json")
    base_verification = read(ROOT / "verification" / "independent_verification.json")
    certificate = read(ROOT / "diagnostic" / "kernel_concept_certificate.json")
    manifest = read(ROOT / "sealed" / "materialization_manifest.json")
    library = native["KernelInducedConceptLibrary"]
    independent = certificate["IndependentlyInducedConceptLibrary"]
    allowed_features = set(protocol["AllowedPrimitiveNumericStateFeatures"] +
                           protocol["AllowedPrimitiveNumericQueryFeatures"])
    allowed_operators = set(protocol["AllowedGenericComparisonOperators"])
    invented_atoms = {tuple(atom) for atom in library["InventedAtomicPredicates"]}
    selected_atoms = [tuple(atom) for concept in library["Concepts"] for atom in concept["Conditions"]]
    atom_shape_pass = all(len(atom) == 3 and atom[0] in allowed_features and
                          atom[1] in allowed_operators and isinstance(atom[2], int)
                          for atom in invented_atoms)
    selected_from_invented = all(atom in invented_atoms for atom in selected_atoms)
    hashes = {
        "FrozenPredicateVerifierSHA256": Path(__file__),
        "FrozenConceptDPSHA256": ROOT / "source" / "kernel_concept_dp.py",
        "FrozenWolframRunnerSHA256": ROOT / "source" / "run_kernel_concept_formation.wl",
    }
    checks = {
        "FrozenCriticalHashesPass": all(protocol[key] == digest(path) for key, path in hashes.items()),
        "NoPredeclaredNamedBooleanPredicates": protocol["PredeclaredNamedBooleanPredicates"] == [] and
            library["PredeclaredNamedBooleanPredicates"] == [],
        "OnlyAllowedRawFeaturesAndGenericOperators": atom_shape_pass,
        "SelectedConditionsWereInventedFromSourceVocabulary": selected_from_invented,
        "AtLeastOneExactSupportedConcept": library["ConceptCount"] >= 1 and all(
            concept["TrainingFalsePositiveCount"] == 0 for concept in library["Concepts"]),
        "NativeAndIndependentConceptBodiesMatch": score["KernelAndIndependentConceptBodiesMatch"] is True,
        "AllFiveFreshTargetsExact": score["ExactTargetPassCount"] == 5,
        "AdversarialControlSafe": score["AdversarialControlSafe"] is True,
        "NoReusableConceptFallbackExercised": score["NoReusableConceptFallbackExercised"] is True,
        "NoFilteringOrReplacement": manifest["PostSeedWorldFilteringUsed"] is False and
            manifest["WorldReplacementAfterMaterializationUsed"] is False,
        "BaseIndependentVerificationPass": base_verification["CapabilityGatePass"] is True,
        "CoreUnchanged": score["CoreRewriteFreezeDedupModified"] is False,
        "IndependentLibraryMetadataMatch": independent["InventedAtomicPredicateCount"] ==
            library["InventedAtomicPredicateCount"],
    }
    result = {
        "Stage": protocol["Stage"] + " predicate-invention verification",
        "ProtocolSHA256": digest(ROOT / "protocol" / "frozen_protocol.json"),
        "InventedAtomicPredicateCount": library["InventedAtomicPredicateCount"],
        "SelectedConceptCount": library["ConceptCount"],
        "SelectedConcepts": library["Concepts"],
        "Checks": checks,
        "PredicateInventionDiagnosticPass": all(checks.values()),
        "CoreRewriteFreezeDedupModified": False,
        "OpenEndedLanguageInventionClaimed": False,
        "Conclusion": "BOUNDED_NUMERIC_PREDICATE_INVENTION_DIAGNOSTIC_PASS" if all(checks.values()) else
                      "BOUNDED_NUMERIC_PREDICATE_INVENTION_DIAGNOSTIC_FAIL",
    }
    destination = ROOT / "verification" / "predicate_invention_verification.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"InventedAtomicPredicateCount": result["InventedAtomicPredicateCount"],
                      "SelectedConceptCount": result["SelectedConceptCount"],
                      "PredicateInventionDiagnosticPass": result["PredicateInventionDiagnosticPass"]},
                     separators=(",", ":")))
    return 0 if result["PredicateInventionDiagnosticPass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
