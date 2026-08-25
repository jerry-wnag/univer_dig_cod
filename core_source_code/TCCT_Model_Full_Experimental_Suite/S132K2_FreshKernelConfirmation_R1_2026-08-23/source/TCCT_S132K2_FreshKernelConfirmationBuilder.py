"""Freeze, materialise, and certify S132-K2 fresh worlds in three phases."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any


WORLD_SPECS = [
    ("K201", [4, 5], 1_322_101),
    ("K202", [5, 6], 1_322_102),
    ("K203", [3, 4, 5], 1_322_103),
    ("K204", [2, 5, 4], 1_322_104),
    ("K205", [4, 4, 3], 1_322_105),
]
HELDOUT_SEEDS = [1_322_201 + index for index in range(len(WORLD_SPECS))]
RELABEL_SEEDS = [1_322_301 + index for index in range(len(WORLD_SPECS))]
RANDOM_CONTROL_SEEDS = [
    [1_322_400 + 100 * replicate + index for index in range(len(WORLD_SPECS))]
    for replicate in range(1, 6)
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def verify_frozen_sources(package: Path, manifest: dict[str, Any]) -> dict[str, bool]:
    current = source_hashes(package)
    frozen = manifest["SourceHashes"]
    keys = sorted(set(current) | set(frozen))
    return {key: current.get(key) == frozen.get(key) for key in keys}


def evaluate(ast: list[Any], coordinate: list[int]) -> int | bool:
    op = ast[0]
    if op == "Var":
        return coordinate[int(ast[1]) - 1]
    if op == "Const":
        return int(ast[1])
    values = [evaluate(child, coordinate) for child in ast[1:] if isinstance(child, list)]
    if op == "Add":
        return int(values[0]) + int(values[1])
    if op == "Sub":
        return int(values[0]) - int(values[1])
    if op == "Mul":
        return int(values[0]) * int(values[1])
    if op == "Mod":
        return int(values[0]) % int(values[1])
    if op == "BitXor":
        return int(values[0]) ^ int(values[1])
    if op == "Eq":
        return values[0] == values[1]
    if op == "Lt":
        return int(values[0]) < int(values[1])
    if op == "If":
        return values[1] if bool(values[0]) else values[2]
    raise ValueError(op)


def freeze(args: argparse.Namespace) -> None:
    package = args.package.resolve()
    if package.exists():
        raise SystemExit(f"Refusing to overwrite existing package: {package}")
    for folder in (
        "source",
        "input",
        "oracle",
        "sealed",
        "protocol",
        "discovery",
        "results",
        "negative_controls",
        "verification",
    ):
        (package / folder).mkdir(parents=True, exist_ok=False)

    sources = [
        Path(__file__).resolve(),
        args.generator.resolve(),
        args.discovery_runner.resolve(),
        args.quotient_runner.resolve(),
        args.verifier.resolve(),
        args.k1_source.resolve(),
        args.k1_verifier.resolve(),
        args.b6_source.resolve(),
        args.b7_source.resolve(),
        args.b8_source.resolve(),
    ]
    for source in sources:
        shutil.copy2(source, package / "source" / source.name)

    support_files = [
        args.b6_public.resolve(),
        args.frozen_b6.resolve(),
        args.frozen_b7.resolve(),
    ]
    for source in support_files:
        shutil.copy2(source, package / "input" / source.name)
    shutil.copy2(args.b6_oracle.resolve(), package / "oracle" / args.b6_oracle.name)
    for source in (args.b6_manifest, args.b7_manifest, args.b8_manifest):
        shutil.copy2(source.resolve(), package / "protocol" / source.name)

    manifest = {
        "Stage": "S132-K2 fresh-world kernel transformation quotient confirmation",
        "EvidenceStatus": "LOCAL_PREWORLD_FROZEN_FRESH_WORLD_CONFIRMATION",
        "FrozenUTC": dt.datetime.now(dt.timezone.utc).isoformat(),
        "FrozenBeforeWorldMaterialization": True,
        "ExploratoryK1ResultUsedOnlyToChooseConfirmatoryGate": True,
        "WorldGenerator": "unchanged frozen S129-C1 five-family in-bound generator",
        "WorldSpecifications": [
            {"WorldID": world_id, "Dimensions": dimensions, "Seed": seed}
            for world_id, dimensions, seed in WORLD_SPECS
        ],
        "MaximumWordLength": 6,
        "HeldoutProgramCountPerWorld": 100,
        "HeldoutProgramLength": 60,
        "HeldoutSeeds": HELDOUT_SEEDS,
        "StateRelabelSeeds": RELABEL_SEEDS,
        "RandomControlSeeds": RANDOM_CONTROL_SEEDS,
        "TCCTDiscoveryAlgorithm": "unchanged frozen S129-B8A incremental bounded-complete search",
        "DiscoveryExactRequired": "5/5",
        "ConceptLearnerInput": "certified latent transition automata only",
        "ProgramASTAllowedForConceptLearner": False,
        "GeneratorTruthAllowedForDiscoveryOrConceptLearner": False,
        "CanonicalTCCTModificationAllowed": False,
        "FrozenPrimaryGate": {
            "DiscoveryExactRequired": "5/5",
            "PositiveShorteningConceptsRequired": "5/5",
            "PositiveHeldoutTokenReductionRequired": "5/5",
            "AllStructuredAndRandomRewritesExact": True,
            "StateRelabelingRequired": "5/5",
            "RewriteDisabledAblationReduction": 0,
            "StructuredReductionMustExceedFiveControlMean": "5/5 paired worlds",
        },
        "NoPostResultSeedWorldRuleOrDepthChange": True,
        "OpenEndedPrimitiveInventionClaimAllowed": False,
        "SourceHashes": {},
    }
    manifest["SourceHashes"] = source_hashes(package)
    manifest_path = package / "protocol" / "S132K2_pre_world_manifest.json"
    dump_json(manifest_path, manifest)
    receipt = {
        "ManifestSHA256": sha256(manifest_path),
        "WorldsMaterialized": False,
        "DiscoveryRunComplete": False,
        "CertifiedAutomataMaterialized": False,
        "ConceptRunComplete": False,
    }
    dump_json(package / "protocol" / "S132K2_freeze_receipt.json", receipt)
    print(f"FROZEN {manifest_path}")
    print(receipt["ManifestSHA256"])


def materialize(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K2_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K2_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = verify_frozen_sources(package, manifest)
    checks["Manifest"] = sha256(manifest_path) == receipt["ManifestSHA256"]
    checks["NotPreviouslyMaterialized"] = receipt["WorldsMaterialized"] is False
    if not all(checks.values()):
        raise RuntimeError(f"Pre-world freeze check failed: {checks}")

    generator_path = package / "source" / "TCCT_S129C1_FreshBlindConfirmationBuilder.py"
    generator = load_module(generator_path, "s132k2_frozen_generator")
    public_worlds, oracle_worlds, truth_worlds = [], [], []
    for world_id, dimensions, seed in WORLD_SPECS:
        programs = generator.in_bound_programs(dimensions, seed)
        public, oracle, truth = generator.make_world(
            world_id, dimensions, programs, seed, "S132K2_FRESH"
        )
        public_worlds.append(public)
        oracle_worlds.append(oracle)
        truth_worlds.append(truth)

    public_path = package / "input" / "S132K2_public_input.json"
    oracle_path = package / "oracle" / "S132K2_oracle_tables.json"
    truth_path = package / "sealed" / "S132K2_generator_truth.json"
    dump_json(
        public_path,
        {
            "Stage": "S132-K2 fresh public input",
            "ForbiddenFieldsAbsent": ["TransitionTable", "GeneratorPrograms", "Seed"],
            "Worlds": public_worlds,
        },
    )
    dump_json(
        oracle_path,
        {
            "Stage": "S132-K2 equivalence-oracle tables",
            "DirectCandidateGeneratorAccessAllowed": False,
            "Worlds": oracle_worlds,
        },
    )
    dump_json(
        truth_path,
        {
            "Stage": "S132-K2 sealed generator truth",
            "ReadableByDiscoveryOrConceptLearner": False,
            "Worlds": truth_worlds,
        },
    )
    receipt.update(
        {
            "WorldsMaterialized": True,
            "MaterializedAfterManifestFreeze": True,
            "PublicInputSHA256": sha256(public_path),
            "OracleSHA256": sha256(oracle_path),
            "SealedTruthSHA256": sha256(truth_path),
            "SourceChecksAtMaterialization": checks,
        }
    )
    dump_json(receipt_path, receipt)
    print(f"MATERIALIZED {len(WORLD_SPECS)} fresh worlds")


def certify(package: Path) -> None:
    package = package.resolve()
    manifest_path = package / "protocol" / "S132K2_pre_world_manifest.json"
    receipt_path = package / "protocol" / "S132K2_freeze_receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = verify_frozen_sources(package, manifest)
    checks["Manifest"] = sha256(manifest_path) == receipt["ManifestSHA256"]
    checks["WorldsMaterialized"] = receipt["WorldsMaterialized"] is True
    checks["NotPreviouslyCertified"] = receipt["CertifiedAutomataMaterialized"] is False
    discovery_path = package / "discovery" / "S132K2_discovery_result.json"
    checks["DiscoveryResultExists"] = discovery_path.is_file()
    if not all(checks.values()):
        raise RuntimeError(f"Pre-certification check failed: {checks}")

    discovery = json.loads(discovery_path.read_text(encoding="utf-8"))
    public_path = package / "input" / "S132K2_public_input.json"
    public = json.loads(public_path.read_text(encoding="utf-8"))
    public_by_id = {world["WorldID"]: world for world in public["Worlds"]}
    exact_count = sum(row["Active"].get("ExactCertified") is True for row in discovery["FormalResults"])
    if exact_count != len(WORLD_SPECS):
        raise RuntimeError(f"Discovery exact gate failed: {exact_count}/{len(WORLD_SPECS)}")

    automata = []
    for row in discovery["FormalResults"]:
        world = public_by_id[row["WorldID"]]
        phi = [[int(value) for value in coordinate] for coordinate in world["Phi"]]
        inverse = {tuple(coordinate): index + 1 for index, coordinate in enumerate(phi)}
        programs = row["Active"]["Programs"]
        table = []
        for coordinate in phi:
            target_row = []
            for action_program in programs:
                target = tuple(int(evaluate(component, coordinate)) for component in action_program)
                if target not in inverse:
                    raise RuntimeError(f"Certified program leaves support: {row['WorldID']} {target}")
                target_row.append(inverse[target])
            table.append(target_row)
        automata.append(
            {
                "WorldID": row["WorldID"],
                "StateCount": len(phi),
                "ActionCount": len(programs),
                "CoordinateDimensions": row["CoordinateDimensions"],
                "TransitionTable": table,
                "DerivedFromFreshExactCertifiedPrograms": True,
                "ProgramASTRetainedInConceptInput": False,
            }
        )

    certified_path = package / "input" / "certified_automata.json"
    dump_json(
        certified_path,
        {
            "Stage": "S132-K2 fresh certified automata",
            "DiscoveryExactCount": exact_count,
            "GeneratorTruthRead": False,
            "OracleTransitionTablesReadDuringDerivation": False,
            "ProgramASTRetained": False,
            "Automata": automata,
        },
    )
    receipt.update(
        {
            "DiscoveryRunComplete": True,
            "DiscoveryResultSHA256": sha256(discovery_path),
            "DiscoveryExactCount": exact_count,
            "CertifiedAutomataMaterialized": True,
            "CertifiedAutomataSHA256": sha256(certified_path),
            "SourceChecksAtCertification": checks,
        }
    )
    dump_json(receipt_path, receipt)
    print(f"CERTIFIED {exact_count} fresh automata")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["freeze", "materialize", "certify"])
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--discovery-runner", type=Path)
    parser.add_argument("--quotient-runner", type=Path)
    parser.add_argument("--verifier", type=Path)
    parser.add_argument("--k1-source", type=Path)
    parser.add_argument("--k1-verifier", type=Path)
    parser.add_argument("--b6-source", type=Path)
    parser.add_argument("--b7-source", type=Path)
    parser.add_argument("--b8-source", type=Path)
    parser.add_argument("--b6-public", type=Path)
    parser.add_argument("--frozen-b6", type=Path)
    parser.add_argument("--frozen-b7", type=Path)
    parser.add_argument("--b6-oracle", type=Path)
    parser.add_argument("--b6-manifest", type=Path)
    parser.add_argument("--b7-manifest", type=Path)
    parser.add_argument("--b8-manifest", type=Path)
    args = parser.parse_args()
    if args.phase == "freeze":
        required = [
            "generator",
            "discovery_runner",
            "quotient_runner",
            "verifier",
            "k1_source",
            "k1_verifier",
            "b6_source",
            "b7_source",
            "b8_source",
            "b6_public",
            "frozen_b6",
            "frozen_b7",
            "b6_oracle",
            "b6_manifest",
            "b7_manifest",
            "b8_manifest",
        ]
        missing = [name for name in required if getattr(args, name) is None]
        if missing:
            parser.error(f"freeze requires: {', '.join(missing)}")
        freeze(args)
    elif args.phase == "materialize":
        materialize(args.package)
    else:
        certify(args.package)


if __name__ == "__main__":
    main()
