"""S125-E saturated neural baseline stress test.

The neural baseline is deliberately data-advantaged: it receives multiple
disjoint action paths for every one of the 46 low-order joint states. Every
training/validation prefix is restricted to interaction order <= 2. A model is
eligible for high-order evaluation only if low-order training balanced accuracy
is >= 0.99, held-out-path validation balanced accuracy is >= 0.98, and complete
14-bit validation-signature exact accuracy is >= 0.85.

The confirmatory phase uses frozen TCCT files that were created before their
original high-order opening. This script is an offline frozen-world stress test,
not a newly generated fresh-world run. It does not modify TCCT or the original
S125 artifacts.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import itertools
import json
import os
import random
import re
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


WORKSPACE = Path(__file__).resolve().parent.parent
DEFAULT_TORCH_DEPS = WORKSPACE / "work" / "python_deps"
TORCH_DEPS = Path(os.environ.get("S125E_TORCH_DEPS", str(DEFAULT_TORCH_DEPS)))
if TORCH_DEPS.is_dir():
    sys.path.insert(0, str(TORCH_DEPS))

import numpy as np
import torch
from sklearn.metrics import balanced_accuracy_score
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


DEVELOPMENT_ROOT = Path(
    r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development"
    r"\S125C_Jupyter_Pilot5_MultiRestartMatched_Output"
)
CONFIRMATORY_ROOT = Path(
    r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development"
    r"\S125A_Jupyter_R2_MultiFreshWorld_Output"
)
OUTPUTS = WORKSPACE / "outputs"

BENCHMARK_VERSION = "S125-E-v1"
PUBLIC_ACTIONS = tuple(range(8))
PUBLIC_PROBES = tuple(range(14))
MAX_ACTIONS = 16
PAD_TOKEN = 8
START_TOKEN = 9
EXPECTED_JOINT_STATES = 120
EXPECTED_LOW_ORDER_STATES = 46
EXPECTED_HIGH_ORDER_STATES = 74
EXPECTED_HIGH_ORDER_TRANSITIONS = 592

TRAIN_PATHS_PER_STATE = 128
VALIDATION_PATHS_PER_STATE = 32
TOTAL_PATHS_PER_LOW_STATE = TRAIN_PATHS_PER_STATE + VALIDATION_PATHS_PER_STATE
EMBEDDING_DIMENSION = 64
HIDDEN_DIMENSION = 128
GRU_LAYERS = 2
LEARNING_RATE = 0.002
WEIGHT_DECAY = 1.0e-6
BATCH_SIZE = 256
MAX_EPOCHS = 200
EVALUATION_INTERVAL = 5
PATIENCE_EPOCHS = 50
TRAIN_BALANCED_GATE = 0.99
VALIDATION_BALANCED_GATE = 0.98
VALIDATION_EXACT_GATE = 0.85
CANDIDATE_SEEDS = (1259301, 1259302, 1259303)
DEVELOPMENT_DATA_SEEDS = (1259401, 1259402, 1259403, 1259404, 1259405)
CONFIRMATORY_DATA_SEEDS = (1259501, 1259502, 1259503, 1259504, 1259505)
CONFIRMATORY_WORLD_SEEDS = (1257019, 1257018, 1257007, 1257010, 1257015)
CONFIRMATORY_SELECTION_SEED = 1259001


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_integer_list(text: str) -> list[int]:
    stripped = text.strip()
    if not stripped:
        return []
    return [int(item.strip()) for item in stripped.split(",")]


@dataclass(frozen=True)
class LearnedFactor:
    probes: tuple[int, ...]
    actions: tuple[int, ...]
    signatures: dict[int, tuple[int, ...]]


class FrozenTCCT:
    def __init__(self, path: Path):
        self.path = path
        text = path.read_text(encoding="utf-8")
        factors_match = re.search(
            r'"LearnedFactors"\s*->\s*\{(.*?)\},\s*"Parents"', text, re.S
        )
        if not factors_match:
            raise ValueError(f"Cannot locate LearnedFactors in {path}")
        factor_pattern = re.compile(
            r'<\|"LearnedFactor"\s*->\s*(\d+),\s*'
            r'"Probes"\s*->\s*\{([^}]*)\},\s*'
            r'"Actions"\s*->\s*\{([^}]*)\},\s*'
            r'"StateCount"\s*->\s*(\d+),\s*'
            r'"StateSignatures"\s*->\s*<\|(.*?)\|>,\s*'
            r'"RepresentativeByState"',
            re.S,
        )
        factors_by_index: dict[int, LearnedFactor] = {}
        for match in factor_pattern.finditer(factors_match.group(1)):
            factor_index = int(match.group(1))
            state_count = int(match.group(4))
            signatures = {
                int(state): tuple(parse_integer_list(bits))
                for state, bits in re.findall(
                    r'(\d+)\s*->\s*\{([^}]*)\}', match.group(5), re.S
                )
            }
            if len(signatures) != state_count:
                raise ValueError(f"Factor signature count mismatch in {path}")
            factors_by_index[factor_index] = LearnedFactor(
                probes=tuple(parse_integer_list(match.group(2))),
                actions=tuple(parse_integer_list(match.group(3))),
                signatures=signatures,
            )
        if sorted(factors_by_index) != [1, 2, 3, 4]:
            raise ValueError(f"Expected four factors in {path}")
        self.factors = tuple(factors_by_index[index] for index in range(1, 5))

        parents_match = re.search(
            r'"Parents"\s*->\s*<\|(.*?)\|>,\s*"ConditionalTransitions"',
            text,
            re.S,
        )
        transitions_match = re.search(
            r'"ConditionalTransitions"\s*->\s*<\|(.*?)\|>,\s*'
            r'"StartState"\s*->',
            text,
            re.S,
        )
        if not parents_match or not transitions_match:
            raise ValueError(f"Cannot locate transition model in {path}")
        self.parents = {
            int(action): tuple(parse_integer_list(parent_list))
            for action, parent_list in re.findall(
                r'(\d+)\s*->\s*\{([^}]*)\}', parents_match.group(1), re.S
            )
        }
        self.transitions: dict[tuple[int, int, tuple[int, ...]], int] = {}
        for action, target, parent_states, destination in re.findall(
            r'"\{(\d+),\s*(\d+),\s*\{([^}]*)\}\}"\s*->\s*(\d+)',
            transitions_match.group(1),
            re.S,
        ):
            key = (int(action), int(target), tuple(parse_integer_list(parent_states)))
            self.transitions[key] = int(destination)
        start_states = re.findall(r'"StartState"\s*->\s*\{([^}]*)\}', text, re.S)
        if not start_states:
            raise ValueError(f"Cannot locate joint start state in {path}")
        self.start_state = tuple(parse_integer_list(start_states[-1]))

        self.action_to_factor: dict[int, int] = {}
        self.probe_to_factor_position: dict[int, tuple[int, int]] = {}
        for factor_position, factor in enumerate(self.factors):
            for action in factor.actions:
                self.action_to_factor[action] = factor_position
            for probe_position, probe in enumerate(factor.probes):
                self.probe_to_factor_position[probe] = (
                    factor_position,
                    probe_position,
                )
        if sorted(self.action_to_factor) != list(PUBLIC_ACTIONS):
            raise ValueError(f"Incomplete action map in {path}")
        if sorted(self.probe_to_factor_position) != list(PUBLIC_PROBES):
            raise ValueError(f"Incomplete probe map in {path}")

    def step(self, state: Sequence[int], action: int) -> tuple[int, ...]:
        next_state = list(state)
        factor_position = self.action_to_factor[action]
        parent_states = tuple(
            next_state[index - 1] for index in self.parents.get(action, ())
        )
        key = (action, next_state[factor_position], parent_states)
        if key not in self.transitions:
            raise KeyError(f"Missing transition {key} in {self.path}")
        next_state[factor_position] = self.transitions[key]
        return tuple(next_state)

    def state_after(self, sequence: Sequence[int]) -> tuple[int, ...]:
        state = self.start_state
        for action in sequence:
            state = self.step(state, action)
        return state

    def signature(self, sequence: Sequence[int]) -> tuple[int, ...]:
        state = self.state_after(sequence)
        result: list[int] = []
        for probe in PUBLIC_PROBES:
            factor_position, probe_position = self.probe_to_factor_position[probe]
            local_state = state[factor_position]
            result.append(
                self.factors[factor_position].signatures[local_state][probe_position]
            )
        return tuple(result)

    @property
    def state_counts(self) -> tuple[int, ...]:
        return tuple(len(factor.signatures) for factor in self.factors)

    @property
    def conditional_cells(self) -> int:
        return len(self.transitions)


def active_factor_count(tcct: FrozenTCCT, state: Sequence[int]) -> int:
    return sum(value != start for value, start in zip(state, tcct.start_state))


def all_joint_states(tcct: FrozenTCCT) -> list[tuple[int, ...]]:
    return list(
        itertools.product(*(range(1, count + 1) for count in tcct.state_counts))
    )


def shortest_paths(
    tcct: FrozenTCCT, maximum_interaction_order: int | None
) -> dict[tuple[int, ...], tuple[int, ...]]:
    paths = {tcct.start_state: ()}
    queue = deque([tcct.start_state])
    while queue:
        state = queue.popleft()
        for action in PUBLIC_ACTIONS:
            destination = tcct.step(state, action)
            if (
                maximum_interaction_order is not None
                and active_factor_count(tcct, destination) > maximum_interaction_order
            ):
                continue
            if destination not in paths:
                paths[destination] = paths[state] + (action,)
                queue.append(destination)
    return paths


def generate_low_order_paths(
    tcct: FrozenTCCT, data_seed: int
) -> tuple[list[tuple[int, ...]], list[tuple[int, ...]], dict[str, int]]:
    states = all_joint_states(tcct)
    if len(states) != EXPECTED_JOINT_STATES:
        raise AssertionError("Joint state count drifted")
    low_states = [state for state in states if active_factor_count(tcct, state) <= 2]
    if len(low_states) != EXPECTED_LOW_ORDER_STATES:
        raise AssertionError("Low-order state count drifted")
    shortest = shortest_paths(tcct, maximum_interaction_order=2)
    if set(shortest) != set(low_states):
        raise AssertionError("Not all low-order states are reachable without high-order prefixes")

    rng = random.Random(data_seed)
    buckets = {state: {shortest[state]} for state in low_states}
    attempts = 0
    while (
        min(map(len, buckets.values())) < TOTAL_PATHS_PER_LOW_STATE
        and attempts < 10_000_000
    ):
        attempts += 1
        state = tcct.start_state
        sequence: list[int] = []
        for _ in range(rng.randint(0, MAX_ACTIONS)):
            options: list[tuple[int, tuple[int, ...]]] = []
            for action in PUBLIC_ACTIONS:
                destination = tcct.step(state, action)
                if active_factor_count(tcct, destination) <= 2:
                    options.append((action, destination))
            action, state = rng.choice(options)
            sequence.append(action)
        if len(buckets[state]) < TOTAL_PATHS_PER_LOW_STATE:
            buckets[state].add(tuple(sequence))
    if min(map(len, buckets.values())) < TOTAL_PATHS_PER_LOW_STATE:
        raise RuntimeError("Could not generate enough low-order path variants")

    train_sequences: list[tuple[int, ...]] = []
    validation_sequences: list[tuple[int, ...]] = []
    for state in sorted(buckets):
        sequences = sorted(buckets[state])
        stable_state_code = sum((index + 1) * value * 100 for index, value in enumerate(state))
        random.Random(data_seed + stable_state_code).shuffle(sequences)
        train_sequences.extend(sequences[:TRAIN_PATHS_PER_STATE])
        validation_sequences.extend(
            sequences[
                TRAIN_PATHS_PER_STATE : TRAIN_PATHS_PER_STATE
                + VALIDATION_PATHS_PER_STATE
            ]
        )
    if set(train_sequences) & set(validation_sequences):
        raise AssertionError("Low-order train/validation sequence leakage")
    if any(
        active_factor_count(tcct, tcct.state_after(sequence)) > 2
        for sequence in train_sequences + validation_sequences
    ):
        raise AssertionError("High-order final state leaked into low-order data")
    return train_sequences, validation_sequences, {
        "LowOrderStates": len(low_states),
        "TrainSequences": len(train_sequences),
        "ValidationSequences": len(validation_sequences),
        "GenerationAttempts": attempts,
        "MaximumTrainingInteractionOrder": 2,
        "HighOrderUsedForTrainingOrSelection": False,
    }


def tensorize(
    tcct: FrozenTCCT, sequences: Sequence[Sequence[int]]
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    tokens = np.full(
        (len(sequences), MAX_ACTIONS + 1), PAD_TOKEN, dtype=np.int64
    )
    lengths = np.empty(len(sequences), dtype=np.int64)
    labels = np.empty((len(sequences), len(PUBLIC_PROBES)), dtype=np.float32)
    for index, sequence in enumerate(sequences):
        if len(sequence) > MAX_ACTIONS:
            raise ValueError("Sequence exceeds frozen neural capacity")
        tokens[index, 0] = START_TOKEN
        tokens[index, 1 : 1 + len(sequence)] = sequence
        lengths[index] = len(sequence) + 1
        labels[index] = tcct.signature(sequence)
    return (
        torch.from_numpy(tokens),
        torch.from_numpy(lengths),
        torch.from_numpy(labels),
    )


class SaturatedGRUReasoner(nn.Module):
    def __init__(self):
        super().__init__()
        self.embedding = nn.Embedding(10, EMBEDDING_DIMENSION, padding_idx=PAD_TOKEN)
        self.gru = nn.GRU(
            EMBEDDING_DIMENSION,
            HIDDEN_DIMENSION,
            num_layers=GRU_LAYERS,
            batch_first=True,
            dropout=0.0,
        )
        self.normalization = nn.LayerNorm(HIDDEN_DIMENSION)
        self.output = nn.Linear(HIDDEN_DIMENSION, len(PUBLIC_PROBES))

    def forward(self, tokens: torch.Tensor, lengths: torch.Tensor) -> torch.Tensor:
        sequence_output, _ = self.gru(self.embedding(tokens))
        row = torch.arange(tokens.shape[0], device=tokens.device)
        final = sequence_output[row, lengths - 1]
        return self.output(self.normalization(final))


@torch.no_grad()
def evaluate_model(
    model: SaturatedGRUReasoner, dataset: TensorDataset
) -> dict[str, float]:
    model.eval()
    logits: list[torch.Tensor] = []
    labels: list[torch.Tensor] = []
    for tokens, lengths, target in DataLoader(
        dataset, batch_size=512, shuffle=False, num_workers=0
    ):
        logits.append(model(tokens, lengths).cpu())
        labels.append(target.cpu())
    prediction = (torch.cat(logits) >= 0).numpy().astype(np.int8)
    truth = torch.cat(labels).numpy().astype(np.int8)
    return {
        "BalancedAccuracy": float(
            balanced_accuracy_score(truth.reshape(-1), prediction.reshape(-1))
        ),
        "BitAccuracy": float(np.mean(truth == prediction)),
        "SignatureExactAccuracy": float(np.mean(np.all(truth == prediction, axis=1))),
    }


def train_candidate(
    train_dataset: TensorDataset,
    validation_dataset: TensorDataset,
    candidate_seed: int,
) -> tuple[dict[str, object], dict[str, torch.Tensor]]:
    random.seed(candidate_seed)
    np.random.seed(candidate_seed)
    torch.manual_seed(candidate_seed)
    model = SaturatedGRUReasoner()
    parameter_count = sum(parameter.numel() for parameter in model.parameters())
    labels = train_dataset.tensors[2]
    positive = labels.sum()
    negative = labels.numel() - positive
    criterion = nn.BCEWithLogitsLoss(
        pos_weight=torch.tensor(float(negative / positive), dtype=torch.float32)
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    loader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        generator=torch.Generator().manual_seed(candidate_seed),
    )
    best_score: tuple[float, float, float, float] | None = None
    best_state: dict[str, torch.Tensor] | None = None
    best_epoch = 0
    best_train: dict[str, float] | None = None
    best_validation: dict[str, float] | None = None
    stale_epochs = 0
    start = time.perf_counter()
    for epoch in range(1, MAX_EPOCHS + 1):
        model.train()
        for tokens, lengths, target in loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(tokens, lengths), target)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
        if epoch == 1 or epoch % EVALUATION_INTERVAL == 0:
            train_metrics = evaluate_model(model, train_dataset)
            validation_metrics = evaluate_model(model, validation_dataset)
            score = (
                validation_metrics["BalancedAccuracy"],
                validation_metrics["SignatureExactAccuracy"],
                train_metrics["BalancedAccuracy"],
                train_metrics["SignatureExactAccuracy"],
            )
            if best_score is None or score > best_score:
                best_score = score
                best_state = {
                    key: value.detach().cpu().clone()
                    for key, value in model.state_dict().items()
                }
                best_epoch = epoch
                best_train = train_metrics
                best_validation = validation_metrics
                stale_epochs = 0
            else:
                stale_epochs += EVALUATION_INTERVAL
            if (
                validation_metrics["BalancedAccuracy"] >= VALIDATION_BALANCED_GATE
                and validation_metrics["SignatureExactAccuracy"]
                >= VALIDATION_EXACT_GATE
                and train_metrics["BalancedAccuracy"] >= TRAIN_BALANCED_GATE
            ):
                break
            if stale_epochs >= PATIENCE_EPOCHS:
                break
    if best_state is None or best_train is None or best_validation is None:
        raise RuntimeError("No neural checkpoint was produced")
    record = {
        "Seed": candidate_seed,
        "ParameterCount": parameter_count,
        "BestEpoch": best_epoch,
        "ElapsedSeconds": time.perf_counter() - start,
        "Training": best_train,
        "Validation": best_validation,
        "PassedSaturationGate": bool(
            best_train["BalancedAccuracy"] >= TRAIN_BALANCED_GATE
            and best_validation["BalancedAccuracy"] >= VALIDATION_BALANCED_GATE
            and best_validation["SignatureExactAccuracy"] >= VALIDATION_EXACT_GATE
        ),
    }
    return record, best_state


def predict_signatures(
    model: SaturatedGRUReasoner,
    tcct: FrozenTCCT,
    sequences: Sequence[Sequence[int]],
) -> tuple[np.ndarray, np.ndarray]:
    dataset = TensorDataset(*tensorize(tcct, sequences))
    model.eval()
    predictions: list[torch.Tensor] = []
    truths: list[torch.Tensor] = []
    with torch.no_grad():
        for tokens, lengths, labels in DataLoader(
            dataset, batch_size=512, shuffle=False, num_workers=0
        ):
            predictions.append((model(tokens, lengths) >= 0).cpu())
            truths.append(labels.cpu())
    return (
        torch.cat(predictions).numpy().astype(np.int8),
        torch.cat(truths).numpy().astype(np.int8),
    )


def high_order_metrics(
    model: SaturatedGRUReasoner, tcct: FrozenTCCT
) -> dict[str, object]:
    unrestricted_paths = shortest_paths(tcct, maximum_interaction_order=None)
    if len(unrestricted_paths) != EXPECTED_JOINT_STATES:
        raise AssertionError("Not all joint states are reachable")
    high_states = [
        state
        for state in sorted(unrestricted_paths)
        if active_factor_count(tcct, state) >= 3
    ]
    if len(high_states) != EXPECTED_HIGH_ORDER_STATES:
        raise AssertionError("High-order state count drifted")
    state_sequences = [unrestricted_paths[state] for state in high_states]
    transition_sequences = [
        sequence + (action,)
        for sequence in state_sequences
        for action in PUBLIC_ACTIONS
    ]
    if len(transition_sequences) != EXPECTED_HIGH_ORDER_TRANSITIONS:
        raise AssertionError("High-order transition count drifted")
    if max(map(len, transition_sequences)) > MAX_ACTIONS:
        raise AssertionError("High-order sequence exceeds neural capacity")

    state_prediction, state_truth = predict_signatures(model, tcct, state_sequences)
    transition_prediction, transition_truth = predict_signatures(
        model, tcct, transition_sequences
    )

    def metrics(prediction: np.ndarray, truth: np.ndarray) -> dict[str, object]:
        exact_vector = np.all(prediction == truth, axis=1)
        return {
            "Cases": int(len(truth)),
            "ExactCount": int(exact_vector.sum()),
            "ExactAccuracy": float(exact_vector.mean()),
            "BitAccuracy": float(np.mean(prediction == truth)),
            "BalancedAccuracy": float(
                balanced_accuracy_score(truth.reshape(-1), prediction.reshape(-1))
            ),
        }

    return {
        "State": metrics(state_prediction, state_truth),
        "Transition": metrics(transition_prediction, transition_truth),
        "GroundTruth": "Frozen TCCT signature; original strict run previously established TCCT exact=1.0",
    }


def find_world_directory(root: Path, world_seed: int) -> Path:
    matches = sorted(root.glob(f"world_*_seed_{world_seed}"))
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one directory for world seed {world_seed}")
    return matches[0]


def world_seed_from_directory(path: Path) -> int:
    match = re.search(r"seed_(\d+)$", path.name)
    if not match:
        raise ValueError(f"Cannot parse seed from {path}")
    return int(match.group(1))


def verify_original_strict_summary(world_directory: Path) -> dict[str, bool]:
    summary_path = world_directory / "S124_T5R1_strict_summary.wl"
    text = summary_path.read_text(encoding="utf-8")
    checks = {
        "StrictProspective": bool(
            re.search(r'"StrictProspective"\s*->\s*True', text)
        ),
        "NoHighOrderLeakage": bool(
            re.search(r'"HighOrderTouchedBeforeFreeze"\s*->\s*0', text)
        ),
        "TCCTStateExactOne": bool(
            re.search(r'"TCCTHighOrderExactAccuracy"\s*->\s*1\.', text)
        ),
        "TCCTTransitionExactOne": bool(
            re.search(r'"TCCTTransitionExactAccuracy"\s*->\s*1\.', text)
        ),
        "StrictProtocolPass": bool(
            re.search(r'"StrictProtocolPass"\s*->\s*True', text)
        ),
    }
    if not all(checks.values()):
        raise AssertionError(f"Original strict summary audit failed in {world_directory}")
    return checks


def run_world(
    world_directory: Path,
    data_seed: int,
    output_directory: Path,
    open_high_order: bool,
) -> dict[str, object]:
    world_seed = world_seed_from_directory(world_directory)
    tcct_path = world_directory / "S124_T5R1_TCCT_FROZEN_BEFORE_HIGHORDER.wl"
    if not tcct_path.is_file():
        raise FileNotFoundError(tcct_path)
    tcct = FrozenTCCT(tcct_path)
    train_sequences, validation_sequences, data_audit = generate_low_order_paths(
        tcct, data_seed
    )
    train_dataset = TensorDataset(*tensorize(tcct, train_sequences))
    validation_dataset = TensorDataset(*tensorize(tcct, validation_sequences))

    candidate_records: list[dict[str, object]] = []
    candidate_states: dict[int, dict[str, torch.Tensor]] = {}
    for candidate_seed in CANDIDATE_SEEDS:
        record, state = train_candidate(
            train_dataset, validation_dataset, candidate_seed
        )
        candidate_records.append(record)
        candidate_states[candidate_seed] = state
        print(
            f"CANDIDATE world={world_seed} seed={candidate_seed} "
            f"train_bal={record['Training']['BalancedAccuracy']:.6f} "
            f"val_bal={record['Validation']['BalancedAccuracy']:.6f} "
            f"val_exact={record['Validation']['SignatureExactAccuracy']:.6f} "
            f"pass={record['PassedSaturationGate']}",
            flush=True,
        )
    eligible = [
        record for record in candidate_records if record["PassedSaturationGate"]
    ]
    if not eligible:
        return {
            "Stage": BENCHMARK_VERSION,
            "WorldSeed": world_seed,
            "DataAudit": data_audit,
            "CandidateRecords": candidate_records,
            "SaturationGatePassed": False,
            "HighOrderOpened": False,
            "Outcome": "NEURAL_LOW_ORDER_NOT_SATURATED",
        }
    selected = max(
        eligible,
        key=lambda record: (
            record["Validation"]["BalancedAccuracy"],
            record["Validation"]["SignatureExactAccuracy"],
            record["Training"]["BalancedAccuracy"],
            -record["Seed"],
        ),
    )
    selected_seed = int(selected["Seed"])
    model = SaturatedGRUReasoner()
    model.load_state_dict(candidate_states[selected_seed])
    model.eval()

    output_directory.mkdir(parents=True, exist_ok=True)
    freeze_path = output_directory / f"S125E_saturated_gru_seed_{world_seed}.pt"
    torch.save(
        {
            "BenchmarkVersion": BENCHMARK_VERSION,
            "WorldSeed": world_seed,
            "SelectedCandidateSeed": selected_seed,
            "Architecture": {
                "EmbeddingDimension": EMBEDDING_DIMENSION,
                "HiddenDimension": HIDDEN_DIMENSION,
                "GRULayers": GRU_LAYERS,
                "OutputBits": len(PUBLIC_PROBES),
            },
            "StateDict": model.state_dict(),
        },
        freeze_path,
    )
    freeze_hash = sha256_file(freeze_path)
    # Reload from disk before any optional high-order evaluation.
    frozen_payload = torch.load(freeze_path, map_location="cpu", weights_only=False)
    frozen_model = SaturatedGRUReasoner()
    frozen_model.load_state_dict(frozen_payload["StateDict"])
    frozen_model.eval()

    result: dict[str, object] = {
        "Stage": BENCHMARK_VERSION,
        "WorldSeed": world_seed,
        "TCCTFreezeFileSHA256": sha256_file(tcct_path),
        "TCCTConditionalCells": tcct.conditional_cells,
        "DataSeed": data_seed,
        "DataAudit": data_audit,
        "CandidateRecords": candidate_records,
        "SelectedCandidateSeed": selected_seed,
        "SelectedMetrics": selected,
        "NeuralParameterCount": sum(
            parameter.numel() for parameter in frozen_model.parameters()
        ),
        "NeuralFreezeFile": str(freeze_path),
        "NeuralFreezeSHA256": freeze_hash,
        "SaturationGatePassed": True,
        "HighOrderOpened": False,
    }
    freeze_metadata_path = output_directory / "S125E_freeze_before_highorder.json"
    freeze_metadata_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    if open_high_order:
        strict_checks = verify_original_strict_summary(world_directory)
        result["OriginalStrictWorldChecks"] = strict_checks
        result["HighOrder"] = high_order_metrics(frozen_model, tcct)
        result["HighOrderOpened"] = True
        result["Outcome"] = "SATURATED_NEURAL_HIGH_ORDER_EVALUATED"
    else:
        result["Outcome"] = "DEVELOPMENT_LOW_ORDER_ONLY"
    result_path = output_directory / "S125E_result.json"
    result_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


def write_csv(path: Path, results: Sequence[dict[str, object]]) -> None:
    columns = [
        "WorldSeed",
        "SaturationGatePassed",
        "SelectedCandidateSeed",
        "TrainingBalancedAccuracy",
        "ValidationBalancedAccuracy",
        "ValidationSignatureExactAccuracy",
        "NeuralParameterCount",
        "HighOrderOpened",
        "HighOrderStateExactAccuracy",
        "HighOrderStateBalancedAccuracy",
        "HighOrderTransitionExactAccuracy",
        "HighOrderTransitionBalancedAccuracy",
        "Outcome",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for result in results:
            selected = result.get("SelectedMetrics", {})
            high_order = result.get("HighOrder", {})
            writer.writerow(
                {
                    "WorldSeed": result["WorldSeed"],
                    "SaturationGatePassed": result["SaturationGatePassed"],
                    "SelectedCandidateSeed": result.get(
                        "SelectedCandidateSeed", ""
                    ),
                    "TrainingBalancedAccuracy": selected.get("Training", {}).get(
                        "BalancedAccuracy", ""
                    ),
                    "ValidationBalancedAccuracy": selected.get(
                        "Validation", {}
                    ).get("BalancedAccuracy", ""),
                    "ValidationSignatureExactAccuracy": selected.get(
                        "Validation", {}
                    ).get("SignatureExactAccuracy", ""),
                    "NeuralParameterCount": result.get("NeuralParameterCount", ""),
                    "HighOrderOpened": result.get("HighOrderOpened", False),
                    "HighOrderStateExactAccuracy": high_order.get("State", {}).get(
                        "ExactAccuracy", ""
                    ),
                    "HighOrderStateBalancedAccuracy": high_order.get("State", {}).get(
                        "BalancedAccuracy", ""
                    ),
                    "HighOrderTransitionExactAccuracy": high_order.get(
                        "Transition", {}
                    ).get("ExactAccuracy", ""),
                    "HighOrderTransitionBalancedAccuracy": high_order.get(
                        "Transition", {}
                    ).get("BalancedAccuracy", ""),
                    "Outcome": result["Outcome"],
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("development", "confirmatory"), required=True)
    parser.add_argument("--world-limit", type=int, default=5)
    args = parser.parse_args()

    torch.set_num_threads(min(8, torch.get_num_threads()))
    try:
        torch.use_deterministic_algorithms(True)
    except Exception:
        pass

    if args.phase == "development":
        world_directories = sorted(DEVELOPMENT_ROOT.glob("world_*_seed_*"))[
            : args.world_limit
        ]
        data_seeds = DEVELOPMENT_DATA_SEEDS[: args.world_limit]
        open_high_order = False
        output_root = OUTPUTS / "S125E_SaturatedNeural_Development"
    else:
        selected_world_seeds = CONFIRMATORY_WORLD_SEEDS[: args.world_limit]
        world_directories = [
            find_world_directory(CONFIRMATORY_ROOT, seed)
            for seed in selected_world_seeds
        ]
        data_seeds = CONFIRMATORY_DATA_SEEDS[: args.world_limit]
        open_high_order = True
        output_root = OUTPUTS / "S125E_SaturatedNeural_Confirmatory5"
    if len(world_directories) != args.world_limit:
        raise RuntimeError("World count does not match the requested limit")
    output_root.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, object]] = []
    overall_start = time.perf_counter()
    for run_index, (world_directory, data_seed) in enumerate(
        zip(world_directories, data_seeds), start=1
    ):
        world_seed = world_seed_from_directory(world_directory)
        print(
            f"WORLD_START phase={args.phase} run={run_index} seed={world_seed}",
            flush=True,
        )
        world_output = output_root / f"world_{run_index:02d}_seed_{world_seed}"
        result = run_world(
            world_directory, data_seed, world_output, open_high_order=open_high_order
        )
        results.append(result)
        print(
            f"WORLD_DONE seed={world_seed} saturation={result['SaturationGatePassed']} "
            f"high_order_opened={result.get('HighOrderOpened', False)}",
            flush=True,
        )
        if not result["SaturationGatePassed"]:
            print("STOPPING_BEFORE_ANY_FURTHER_HIGH_ORDER_OPENING", flush=True)
            break

    all_saturated = len(results) == args.world_limit and all(
        result["SaturationGatePassed"] for result in results
    )
    all_high_order_opened = all(
        bool(result.get("HighOrderOpened", False)) for result in results
    )
    aggregate: dict[str, object] = {
        "Stage": BENCHMARK_VERSION,
        "Phase": args.phase,
        "CompletedWorlds": len(results),
        "RequestedWorlds": args.world_limit,
        "AllWorldsSaturated": all_saturated,
        "AllHighOrderOpened": all_high_order_opened,
        "ElapsedSeconds": time.perf_counter() - overall_start,
        "Gates": {
            "TrainingBalancedAccuracy": TRAIN_BALANCED_GATE,
            "ValidationBalancedAccuracy": VALIDATION_BALANCED_GATE,
            "ValidationSignatureExactAccuracy": VALIDATION_EXACT_GATE,
        },
        "Architecture": {
            "Type": "GRU multi-label neural reasoner",
            "EmbeddingDimension": EMBEDDING_DIMENSION,
            "HiddenDimension": HIDDEN_DIMENSION,
            "GRULayers": GRU_LAYERS,
            "CandidateSeeds": CANDIDATE_SEEDS,
        },
        "DataPolicy": {
            "LowOrderStates": EXPECTED_LOW_ORDER_STATES,
            "TrainPathsPerState": TRAIN_PATHS_PER_STATE,
            "ValidationPathsPerState": VALIDATION_PATHS_PER_STATE,
            "MaximumInteractionOrder": 2,
            "HighOrderUsedForTrainingOrSelection": False,
        },
        "ConfirmatorySelection": {
            "Pool": "S125A Jupyter R2 frozen strict worlds 1257001..1257020",
            "SelectionSeed": CONFIRMATORY_SELECTION_SEED,
            "SelectedWorldSeeds": CONFIRMATORY_WORLD_SEEDS,
            "NewFreshWorldGeneration": False,
        },
        "Results": results,
    }
    if args.phase == "confirmatory" and all_saturated and all_high_order_opened:
        state_exact = [
            result["HighOrder"]["State"]["ExactAccuracy"] for result in results
        ]
        transition_exact = [
            result["HighOrder"]["Transition"]["ExactAccuracy"]
            for result in results
        ]
        aggregate["ConfirmatorySummary"] = {
            "NeuralHighOrderStateExactMean": float(np.mean(state_exact)),
            "NeuralHighOrderTransitionExactMean": float(
                np.mean(transition_exact)
            ),
            "WorldsWithAnyStateExact": sum(value > 0 for value in state_exact),
            "WorldsWithAnyTransitionExact": sum(
                value > 0 for value in transition_exact
            ),
        }

    aggregate_path = output_root / "S125E_aggregate.json"
    csv_path = output_root / "S125E_per_world.csv"
    aggregate_path.write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_csv(csv_path, results)
    print(f"ALL_WORLDS_SATURATED={all_saturated}", flush=True)
    print(f"AGGREGATE={aggregate_path}", flush=True)
    print(f"CSV={csv_path}", flush=True)
    return 0 if all_saturated else 2


if __name__ == "__main__":
    raise SystemExit(main())
