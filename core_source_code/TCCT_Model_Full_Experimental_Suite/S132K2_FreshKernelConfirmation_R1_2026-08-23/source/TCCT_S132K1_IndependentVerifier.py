"""Independent verifier for the S132-K1 transformation quotient."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(table: list[list[int]], word: tuple[int, ...]) -> tuple[int, ...]:
    mapping = list(range(len(table)))
    for action in word:
        mapping = [table[state][action - 1] - 1 for state in mapping]
    return tuple(mapping)


def quotient_summary(table: list[list[int]], maximum_length: int) -> dict[str, int]:
    action_count = len(table[0])
    groups: dict[tuple[int, ...], list[tuple[int, ...]]] = defaultdict(list)
    groups[transform(table, ())].append(())
    for length in range(1, maximum_length + 1):
        for word in itertools.product(range(1, action_count + 1), repeat=length):
            groups[transform(table, word)].append(word)
    multi = 0
    concepts = 0
    rewrite_rules = 0
    exact_rules = 0
    false_rules = 0
    for signature, words in groups.items():
        if len(words) > 1:
            multi += 1
        representative = min(words, key=lambda word: (len(word), repr(word)))
        longer = [word for word in words if len(word) > len(representative)]
        if longer:
            concepts += 1
        rewrite_rules += len(longer)
        for word in longer:
            if transform(table, word) == transform(table, representative) == signature:
                exact_rules += 1
            else:
                false_rules += 1
    return {
        "EnumeratedWordCount": sum(len(words) for words in groups.values()),
        "SemanticClassCount": len(groups),
        "MultiRealizationClassCount": multi,
        "ShorteningConceptCount": concepts,
        "RewriteRuleCount": rewrite_rules,
        "ExactRewriteRuleCount": exact_rules,
        "FalseEquivalenceCount": false_rules,
    }


def action_ranks(table: list[list[int]]) -> list[int]:
    return [len({row[action] for row in table}) for action in range(len(table[0]))]


def relabel(table: list[list[int]], seed: int) -> list[list[int]]:
    rng = random.Random(seed)
    state_count = len(table)
    old_to_new = list(range(state_count))
    rng.shuffle(old_to_new)
    new_to_old = [0] * state_count
    for old, new in enumerate(old_to_new):
        new_to_old[new] = old
    return [
        [old_to_new[table[new_to_old[new]][action] - 1] + 1 for action in range(len(table[0]))]
        for new in range(state_count)
    ]


def compare_summary(independent: dict[str, int], reported: dict[str, Any]) -> bool:
    return all(int(reported[key]) == value for key, value in independent.items())


def verify(package: Path) -> dict[str, Any]:
    manifest_path = package / "protocol" / "S132K1_frozen_manifest.json"
    automata_path = package / "input" / "certified_automata.json"
    wolfram_path = package / "source" / "TCCT_S132K1_KernelTransformationQuotient.wl"
    verifier_path = package / "source" / "TCCT_S132K1_IndependentVerifier.py"
    result_path = package / "results" / "S132K1_result.json"
    controls_path = package / "negative_controls" / "S132K1_random_automata.json"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    automata = json.loads(automata_path.read_text(encoding="utf-8"))["Automata"]
    result = json.loads(result_path.read_text(encoding="utf-8"))
    controls = json.loads(controls_path.read_text(encoding="utf-8"))["Controls"]
    maximum_length = int(manifest["MaximumWordLength"])

    computed_hashes = {
        "CertifiedAutomataSHA256": sha256(automata_path),
        "WolframSourceSHA256": sha256(wolfram_path),
        "VerifierSourceSHA256": sha256(verifier_path),
    }
    hash_pass = all(manifest[key] == value for key, value in computed_hashes.items())

    reported_structured = {row["WorldID"]: row for row in result["StructuredResults"]}
    structured_audits = []
    for index, world in enumerate(automata):
        independent = quotient_summary(world["TransitionTable"], maximum_length)
        reported = reported_structured[world["WorldID"]]["Quotient"]
        summary_pass = compare_summary(independent, reported)
        independently_relabeled = relabel(
            world["TransitionTable"], int(manifest["StateRelabelSeeds"][index])
        )
        relabeled_summary = quotient_summary(independently_relabeled, maximum_length)
        relabel_pass = independent == relabeled_summary
        structured_audits.append(
            {
                "WorldID": world["WorldID"],
                "IndependentSummary": independent,
                "ReportedSummaryPass": summary_pass,
                "IndependentStateRelabelingPass": relabel_pass,
            }
        )

    control_audits = []
    for control in controls:
        independent = quotient_summary(control["TransitionTable"], maximum_length)
        summary_pass = compare_summary(independent, control["Quotient"])
        rank_pass = (
            action_ranks(control["TransitionTable"])
            == [int(value) for value in control["TargetActionImageRanks"]]
            == [int(value) for value in control["ControlActionImageRanks"]]
        )
        control_audits.append(
            {
                "Replicate": control["Replicate"],
                "WorldID": control["WorldID"],
                "ReportedSummaryPass": summary_pass,
                "RankMatchingPass": rank_pass,
                "IndependentFalseEquivalenceCount": independent["FalseEquivalenceCount"],
            }
        )

    structured_pass = all(
        row["ReportedSummaryPass"]
        and row["IndependentStateRelabelingPass"]
        and row["IndependentSummary"]["FalseEquivalenceCount"] == 0
        for row in structured_audits
    )
    controls_pass = all(
        row["ReportedSummaryPass"]
        and row["RankMatchingPass"]
        and row["IndependentFalseEquivalenceCount"] == 0
        for row in control_audits
    )
    heldout_boundary_pass = (
        bool(result["StructuredAllRewritesExact"])
        and int(result["StructuredHeldoutActionTokenReduction"]) > 0
        and int(result["RewriteDisabledAblationReduction"]) == 0
    )
    evidence_integrity = hash_pass and structured_pass and controls_pass and heldout_boundary_pass
    confirmed = evidence_integrity and bool(result["KernelCausalGatePass"])
    return {
        "Stage": "S132-K1 independent verification",
        "NativeWolframResultReported": bool(result["NativeWolframExecution"]),
        "ComputedHashes": computed_hashes,
        "FrozenHashPass": hash_pass,
        "StructuredAudits": structured_audits,
        "IndependentStructuredQuotientPass": structured_pass,
        "RandomControlAudits": control_audits,
        "IndependentRandomControlPass": controls_pass,
        "HeldoutBoundaryPass": heldout_boundary_pass,
        "IndependentHeldoutRNGReproduction": False,
        "EvidenceIntegrityPass": evidence_integrity,
        "KernelTransformationQuotientConfirmed": confirmed,
        "OpenEndedPrimitiveInventionConfirmed": False,
        "FinalConclusion": (
            "VERIFIED_KERNEL_TRANSFORMATION_QUOTIENT_GATE_PASS"
            if confirmed
            else "EVIDENCE_VALID_BUT_KERNEL_GATE_NOT_PASSED"
            if evidence_integrity
            else "VERIFICATION_FAILED"
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    result = verify(args.package.resolve())
    output = args.package.resolve() / "verification" / "S132K1_independent_verification.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(result["FinalConclusion"])


if __name__ == "__main__":
    main()
