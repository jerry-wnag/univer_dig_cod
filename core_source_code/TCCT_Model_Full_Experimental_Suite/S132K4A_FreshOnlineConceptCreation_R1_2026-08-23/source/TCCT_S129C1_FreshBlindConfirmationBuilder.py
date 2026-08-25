"""Freeze and materialize the S129-C1 fresh blind confirmation package.

The two-phase interface is deliberate: ``freeze`` records code hashes, seeds,
world dimensions, grammar, budgets, and decision rules before any world is
materialized. ``materialize`` refuses to run if a frozen source hash changed.
No solver is invoked by this builder and no world is resampled based on a
learner outcome.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import shutil
from collections import deque
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
WORKSPACE = HERE.parent
B8 = WORKSPACE / "work" / "S129B8A_IncrementalCompleteSearch_R1"
PACKAGE = WORKSPACE / "work" / "S129C1_FreshBlindConfirmation_R1"
SOURCE = PACKAGE / "source"
INPUT = PACKAGE / "input"
ORACLE = PACKAGE / "oracle"
SEALED = PACKAGE / "sealed"
PROTOCOL = PACKAGE / "protocol"

BUILDER = Path(__file__).resolve()
RUNNER = HERE / "TCCT_S129C1_FreshBlindConfirmation.wl"
VERIFIER = HERE / "TCCT_S129C1_IndependentVerifier.wl"

IN_BOUND_SPECS = [
    ("C01", [4, 5], 1299401),
    ("C02", [5, 6], 1299402),
    ("C03", [3, 4, 5], 1299403),
    ("C04", [2, 5, 4], 1299404),
    ("C05", [4, 3], 1299405),
]
CHALLENGE_SPECS = [
    ("X01", [4, 5], 1299411, "AST_COST_ABOVE_7"),
    ("X02", [3, 4, 3], 1299412, "COMPOSED_PREDICATE_OUTSIDE_FROZEN_PREDICATE_DSL"),
]
RANDOM_CONTROL_SEEDS = [1299491, 1299492, 1299493, 1299494, 1299495]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def var(index: int) -> list[Any]:
    return ["Var", index]


def const(value: int) -> list[Any]:
    return ["Const", value]


def add(left: Any, right: Any) -> list[Any]:
    return ["Add", left, right]


def mul(left: Any, right: Any) -> list[Any]:
    return ["Mul", left, right]


def mod(value: Any, divisor: int) -> list[Any]:
    return ["Mod", value, const(divisor)]


def bitxor(left: Any, right: Any) -> list[Any]:
    return ["BitXor", left, right]


def eq(left: Any, right: Any) -> list[Any]:
    return ["Eq", left, right]


def lt(left: Any, right: Any) -> list[Any]:
    return ["Lt", left, right]


def gate(predicate: Any, yes: Any, no: Any) -> list[Any]:
    return ["If", predicate, yes, no]


def ast_nodes(ast: list[Any]) -> int:
    return 1 + sum(ast_nodes(item) for item in ast[1:] if isinstance(item, list))


def evaluate(ast: list[Any], coordinate: tuple[int, ...]) -> int | bool:
    op = ast[0]
    if op == "Var":
        return coordinate[ast[1] - 1]
    if op == "Const":
        return ast[1]
    if op == "Add":
        return int(evaluate(ast[1], coordinate)) + int(evaluate(ast[2], coordinate))
    if op == "Sub":
        return int(evaluate(ast[1], coordinate)) - int(evaluate(ast[2], coordinate))
    if op == "Mul":
        return int(evaluate(ast[1], coordinate)) * int(evaluate(ast[2], coordinate))
    if op == "Mod":
        return int(evaluate(ast[1], coordinate)) % int(evaluate(ast[2], coordinate))
    if op == "BitXor":
        return int(evaluate(ast[1], coordinate)) ^ int(evaluate(ast[2], coordinate))
    if op == "Eq":
        return evaluate(ast[1], coordinate) == evaluate(ast[2], coordinate)
    if op == "Lt":
        return int(evaluate(ast[1], coordinate)) < int(evaluate(ast[2], coordinate))
    if op == "If":
        return evaluate(ast[2], coordinate) if evaluate(ast[1], coordinate) else evaluate(ast[3], coordinate)
    raise ValueError(op)


def increment_programs(dimensions: list[int]) -> list[list[list[Any]]]:
    programs: list[list[list[Any]]] = []
    for changed, dimension in enumerate(dimensions):
        suite = []
        for component, target_dimension in enumerate(dimensions):
            if component == changed:
                suite.append(mod(add(var(component + 1), const(1)), target_dimension))
            else:
                suite.append(var(component + 1))
        programs.append(suite)
    return programs


def random_in_bound_expression(
    rng: random.Random, dimensions: list[int], target_component: int
) -> list[Any]:
    count = len(dimensions)
    dimension = dimensions[target_component]
    first = rng.randrange(count)
    second = rng.randrange(count)
    constant_value = rng.randrange(1, dimension + 1)
    family = rng.randrange(5)
    if family == 0:
        expression = mod(add(var(first + 1), const(constant_value)), dimension)
    elif family == 1:
        expression = mod(add(add(var(first + 1), var(second + 1)), const(constant_value)), dimension)
    elif family == 2:
        coefficient = rng.randrange(1, min(3, dimension) + 1)
        expression = mod(add(mul(const(coefficient), var(first + 1)), var(second + 1)), dimension)
    elif family == 3:
        expression = mod(bitxor(var(first + 1), const(constant_value)), dimension)
    else:
        predicate_component = rng.randrange(count)
        predicate_value = rng.randrange(dimensions[predicate_component])
        yes_leaf = mod(add(var(first + 1), const(constant_value)), dimension)
        no_constant = rng.randrange(1, dimension + 1)
        no_leaf = mod(add(var(second + 1), const(no_constant)), dimension)
        predicate = rng.choice([
            eq(var(predicate_component + 1), const(predicate_value)),
            lt(var(predicate_component + 1), const(predicate_value)),
        ])
        expression = gate(predicate, yes_leaf, no_leaf)
    if family < 4 and ast_nodes(expression) > 7:
        raise AssertionError("in-bound arithmetic generator exceeded cost 7")
    return expression


def in_bound_programs(dimensions: list[int], seed: int) -> list[list[list[Any]]]:
    rng = random.Random(seed)
    programs = increment_programs(dimensions)
    programs.append([
        random_in_bound_expression(rng, dimensions, component)
        for component in range(len(dimensions))
    ])
    return programs


def challenge_programs(dimensions: list[int], seed: int, kind: str) -> list[list[list[Any]]]:
    rng = random.Random(seed)
    programs = increment_programs(dimensions)
    suite: list[list[Any]] = []
    for component, dimension in enumerate(dimensions):
        first = rng.randrange(len(dimensions))
        second = rng.randrange(len(dimensions))
        c1 = rng.randrange(1, dimension + 1)
        c2 = rng.randrange(1, dimension + 1)
        if kind == "AST_COST_ABOVE_7":
            expression = mod(
                add(mul(add(var(first + 1), const(c1)), var(second + 1)), const(c2)),
                dimension,
            )
            if ast_nodes(expression) <= 7:
                raise AssertionError("deep challenge did not cross cost boundary")
        elif kind == "COMPOSED_PREDICATE_OUTSIDE_FROZEN_PREDICATE_DSL":
            predicate_dimension = dimensions[first]
            predicate = eq(mod(add(var(first + 1), const(1)), predicate_dimension), const(0))
            yes_leaf = mod(add(var(second + 1), const(c1)), dimension)
            no_leaf = mod(add(var(component + 1), const(c2)), dimension)
            expression = gate(predicate, yes_leaf, no_leaf)
        else:
            raise ValueError(kind)
        suite.append(expression)
    programs.append(suite)
    return programs


def reachable_count(table: list[list[int]], start: int) -> int:
    seen = {start}
    queue: deque[int] = deque([start])
    while queue:
        state = queue.popleft()
        for target in table[state - 1]:
            if target not in seen:
                seen.add(target)
                queue.append(target)
    return len(seen)


def make_world(
    world_id: str,
    dimensions: list[int],
    programs: list[list[list[Any]]],
    permutation_seed: int,
    stratum: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    coordinates = list(itertools.product(*(range(dimension) for dimension in dimensions)))
    coordinate_to_old = {coordinate: index for index, coordinate in enumerate(coordinates)}
    old_table: list[list[int]] = []
    for coordinate in coordinates:
        row = []
        for suite in programs:
            target = tuple(int(evaluate(expression, coordinate)) for expression in suite)
            if any(value < 0 or value >= dimensions[index] for index, value in enumerate(target)):
                raise ValueError(f"{world_id}: out-of-range target {target}")
            row.append(coordinate_to_old[target])
        old_table.append(row)

    rng = random.Random(permutation_seed)
    new_to_old = list(range(len(coordinates)))
    rng.shuffle(new_to_old)
    old_to_new = {old: new for new, old in enumerate(new_to_old)}
    phi = [list(coordinates[old]) for old in new_to_old]
    table = [
        [old_to_new[old_table[old][action]] + 1 for action in range(len(programs))]
        for old in new_to_old
    ]
    start = old_to_new[coordinate_to_old[tuple(0 for _ in dimensions)]] + 1
    if reachable_count(table, start) != len(coordinates):
        raise AssertionError(f"{world_id}: preregistered reachability construction failed")

    public = {
        "WorldID": world_id,
        "StateCount": len(coordinates),
        "ActionCount": len(programs),
        "Actions": list(range(1, len(programs) + 1)),
        "StartState": start,
        "CoordinateDimensions": dimensions,
        "Phi": phi,
    }
    oracle = {"WorldID": world_id, "TransitionTable": table}
    truth = {
        "WorldID": world_id,
        "Stratum": stratum,
        "GeneratorPrograms": programs,
        "GeneratorProgramNodeCosts": [[ast_nodes(ast) for ast in suite] for suite in programs],
        "PermutationSeed": permutation_seed,
        "GeneratorProgramsForbiddenToLearner": True,
    }
    return public, oracle, truth


def required_sources() -> dict[Path, Path]:
    return {
        B8 / "source" / "TCCT_S129B6_TCCTNativeOnlineInduction.wl": SOURCE / "TCCT_S129B6_TCCTNativeOnlineInduction.wl",
        B8 / "source" / "TCCT_S129B7_CostCompleteSearchAudit.wl": SOURCE / "TCCT_S129B7_CostCompleteSearchAudit.wl",
        B8 / "source" / "TCCT_S129B8A_IncrementalCompleteSearch.wl": SOURCE / "TCCT_S129B8A_IncrementalCompleteSearch.wl",
        B8 / "input" / "S129B6_public_input.json": INPUT / "S129B6_public_input.json",
        B8 / "input" / "frozen_S129B6_result.json": INPUT / "frozen_S129B6_result.json",
        B8 / "input" / "frozen_S129B7_result.json": INPUT / "frozen_S129B7_result.json",
        B8 / "oracle" / "S129B6_oracle_tables.json": ORACLE / "S129B6_oracle_tables.json",
        B8 / "protocol" / "S129B6_preregistered_manifest.json": PROTOCOL / "S129B6_preregistered_manifest.json",
        B8 / "protocol" / "S129B7_manifest.json": PROTOCOL / "S129B7_manifest.json",
        B8 / "protocol" / "S129B8A_manifest.json": PROTOCOL / "S129B8A_manifest.json",
        BUILDER: SOURCE / BUILDER.name,
        RUNNER: SOURCE / RUNNER.name,
        VERIFIER: SOURCE / VERIFIER.name,
    }


def freeze() -> None:
    for directory in (SOURCE, INPUT, ORACLE, SEALED, PROTOCOL):
        directory.mkdir(parents=True, exist_ok=True)
    for source, target in required_sources().items():
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, target)

    manifest = {
        "Stage": "S129-C1 fresh blind confirmation R1",
        "EvidenceStatus": "LOCAL_PREWORLD_HASH_FROZEN_CONFIRMATORY_AUDIT",
        "FrozenBeforeWorldMaterialization": True,
        "CanonicalTCCTModified": False,
        "S128BModified": False,
        "B8AAlgorithmModified": False,
        "GeneratorTruthVisibleToLearner": False,
        "SolverBasedWorldResamplingAllowed": False,
        "PriorProgramsAllowed": False,
        "PerWorldTemplatesAllowed": False,
        "InBoundWorldSpecifications": [
            {"WorldID": world_id, "Dimensions": dimensions, "Seed": seed}
            for world_id, dimensions, seed in IN_BOUND_SPECS
        ],
        "ChallengeWorldSpecifications": [
            {"WorldID": world_id, "Dimensions": dimensions, "Seed": seed, "Boundary": boundary}
            for world_id, dimensions, seed, boundary in CHALLENGE_SPECS
        ],
        "RandomControlSeeds": RANDOM_CONTROL_SEEDS,
        "InBoundGeneratorFamilies": [
            "Mod(Add(Var,Const),dimension)",
            "Mod(Add(Add(Var,Var),Const),dimension)",
            "Mod(Add(Mul(Const,Var),Var),dimension)",
            "Mod(BitXor(Var,Const),dimension)",
            "If(Eq_or_Lt(Var,Const),in_bound_leaf,in_bound_leaf)",
        ],
        "ReachabilityConstruction": "one independent increment action per coordinate plus one random composite action",
        "FrozenSearchBoundary": {
            "MaximumASTNodeCost": 7,
            "IntermediateAbsoluteValueBound": 512,
            "CandidateSemanticCapPerTarget": 64,
            "PredicateSearchCap": 96,
            "ConditionalDepth": 1,
            "MembershipQueryBudget": 180,
            "EquivalenceCounterexampleBudget": 24,
        },
        "PrimaryDecisionRule": {
            "InBoundExactRequired": "5/5",
            "RandomAutomatonFalseExactRequired": 0,
            "EveryExactClaimRequiresFullTransitionEquivalence": True,
            "AnyInBoundFallbackCountsAsConfirmatoryFailure": True,
        },
        "ChallengeDecisionRule": "descriptive only: exact if certified, otherwise safe fallback; no post-result DSL change",
        "BuilderSHA256": sha256(BUILDER),
        "RunnerSHA256": sha256(RUNNER),
        "VerifierSHA256": sha256(VERIFIER),
        "FrozenB8ASourceSHA256": sha256(B8 / "source" / "TCCT_S129B8A_IncrementalCompleteSearch.wl"),
    }
    manifest_path = PROTOCOL / "S129C1_pre_world_manifest.json"
    dump_json(manifest_path, manifest)
    dump_json(PROTOCOL / "S129C1_freeze_receipt.json", {
        "PreWorldManifestSHA256": sha256(manifest_path),
        "WorldMaterialized": False,
    })
    (PACKAGE / "README.md").write_text(
        """# TCCT S129-C1 fresh blind confirmation R1

This package freezes the generator, seeds, dimensions, B8A source, decision
rules, and verifier before materializing any world. The learner cannot read the
sealed generator programs. No solver-based resampling or post-result DSL change
is allowed. Challenge-world outcomes are descriptive. No PDF is generated.

Run order:

1. builder `freeze`
2. builder `materialize`
3. `source/TCCT_S129C1_FreshBlindConfirmation.wl`
4. `source/TCCT_S129C1_IndependentVerifier.wl`
""",
        encoding="utf-8",
    )
    print(f"FROZEN {manifest_path}")


def materialize() -> None:
    manifest_path = PROTOCOL / "S129C1_pre_world_manifest.json"
    receipt_path = PROTOCOL / "S129C1_freeze_receipt.json"
    if not manifest_path.is_file() or not receipt_path.is_file():
        raise RuntimeError("freeze must run before materialize")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    checks = {
        "PreWorldManifestSHA256": sha256(manifest_path) == receipt["PreWorldManifestSHA256"],
        "BuilderSHA256": sha256(BUILDER) == manifest["BuilderSHA256"],
        "RunnerSHA256": sha256(RUNNER) == manifest["RunnerSHA256"],
        "VerifierSHA256": sha256(VERIFIER) == manifest["VerifierSHA256"],
        "FrozenB8ASourceSHA256": sha256(B8 / "source" / "TCCT_S129B8A_IncrementalCompleteSearch.wl")
        == manifest["FrozenB8ASourceSHA256"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"frozen source verification failed: {checks}")

    public_worlds: list[dict[str, Any]] = []
    oracle_worlds: list[dict[str, Any]] = []
    sealed_worlds: list[dict[str, Any]] = []
    for world_id, dimensions, seed in IN_BOUND_SPECS:
        parts = make_world(world_id, dimensions, in_bound_programs(dimensions, seed), seed, "IN_BOUND")
        public_worlds.append(parts[0])
        oracle_worlds.append(parts[1])
        sealed_worlds.append(parts[2])
    for world_id, dimensions, seed, boundary in CHALLENGE_SPECS:
        parts = make_world(
            world_id,
            dimensions,
            challenge_programs(dimensions, seed, boundary),
            seed,
            "BOUNDARY_CHALLENGE",
        )
        parts[2]["Boundary"] = boundary
        public_worlds.append(parts[0])
        oracle_worlds.append(parts[1])
        sealed_worlds.append(parts[2])

    public_path = INPUT / "S129C1_public_input.json"
    oracle_path = ORACLE / "S129C1_oracle_tables.json"
    truth_path = SEALED / "S129C1_generator_truth.json"
    dump_json(public_path, {
        "Stage": "S129-C1 public learner input",
        "ForbiddenFieldsAbsent": [
            "TransitionTable", "GeneratorPrograms", "WorldType", "Modulus", "Offset", "Seed"
        ],
        "Worlds": public_worlds,
    })
    dump_json(oracle_path, {
        "Stage": "S129-C1 oracle-only transition tables",
        "DirectCandidateGeneratorAccessAllowed": False,
        "Worlds": oracle_worlds,
    })
    dump_json(truth_path, {
        "Stage": "S129-C1 sealed generator truth",
        "ReadableByLearner": False,
        "Worlds": sealed_worlds,
    })
    receipt.update({
        "WorldMaterialized": True,
        "FreezeChecksAtMaterialization": checks,
        "PublicInputSHA256": sha256(public_path),
        "OracleTablesSHA256": sha256(oracle_path),
        "SealedTruthSHA256": sha256(truth_path),
    })
    dump_json(receipt_path, receipt)
    print(f"MATERIALIZED {len(public_worlds)} worlds; no solver invoked")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["freeze", "materialize"])
    args = parser.parse_args()
    if args.phase == "freeze":
        freeze()
    else:
        materialize()


if __name__ == "__main__":
    main()
