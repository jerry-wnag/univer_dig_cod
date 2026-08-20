"""S125-D frozen inference speed benchmark.

This benchmark does not retrain or modify any model. It reads the five S125-C
frozen TCCT rule files and frozen .wlnet HDF5 arrays, then executes both
reasoner families in one NumPy CPU process. The workload matches the S125-C
shape: 74 state signatures plus 592 transition signatures, each containing
14 public probes and a frozen maximum sequence length of 16.

The NumPy Transformer implementation mirrors the frozen Wolfram architecture
(linear map, pre-normalized causal multi-head attention, residual MLP blocks,
last-token readout). This is an architecture-level same-runtime benchmark, not
a measurement of Wolfram kernel overhead.
"""

from __future__ import annotations

import argparse
import csv
import gc
import hashlib
import itertools
import json
import math
import os
import platform
import re
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Sequence

import h5py
import numpy as np


DEFAULT_ROOT = Path(
    r"E:\TCCT_CODEX_HANDOFF_2026-08-13\S97A_ReadoutBaseline_Development"
    r"\S125C_Jupyter_Pilot5_MultiRestartMatched_Output"
)
DEFAULT_OUTPUT = Path(
    r"C:\Users\王鑫\Documents\Codex\2026-08-20"
    r"\referenced-chatgpt-conversation-this-is-an\outputs"
)

PUBLIC_ACTIONS = tuple(range(8))
PUBLIC_PROBES = tuple(range(14))
FACTOR_SIZES = (2, 3, 4, 5)
REASON_MAX_SEQUENCE_LENGTH = 16
POSITION_DIMENSION = 8
INPUT_DIMENSION = 8 + 14 + 3 + POSITION_DIMENSION
STATE_SIGNATURE_COUNT = 74
TRANSITION_SIGNATURE_COUNT = 592
TOTAL_SIGNATURE_COUNT = STATE_SIGNATURE_COUNT + TRANSITION_SIGNATURE_COUNT
EXPECTED_MATCHED_PARAMETERS = 85_890
EXPECTED_STRONG_PARAMETERS = 339_170
BENCHMARK_VERSION = "S125-D-v1"


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

        factor_section_match = re.search(
            r'"LearnedFactors"\s*->\s*\{(.*?)\},\s*"Parents"', text, re.S
        )
        if not factor_section_match:
            raise ValueError(f"Cannot locate LearnedFactors in {path}")
        factor_section = factor_section_match.group(1)
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
        for match in factor_pattern.finditer(factor_section):
            factor_index = int(match.group(1))
            probes = tuple(parse_integer_list(match.group(2)))
            actions = tuple(parse_integer_list(match.group(3)))
            state_count = int(match.group(4))
            signature_entries = re.findall(
                r'(\d+)\s*->\s*\{([^}]*)\}', match.group(5), re.S
            )
            signatures = {
                int(state): tuple(parse_integer_list(bits))
                for state, bits in signature_entries
            }
            if len(signatures) != state_count:
                raise ValueError(
                    f"Factor {factor_index} signature count mismatch in {path}"
                )
            factors_by_index[factor_index] = LearnedFactor(
                probes=probes, actions=actions, signatures=signatures
            )
        if sorted(factors_by_index) != [1, 2, 3, 4]:
            raise ValueError(f"Expected four learned factors in {path}")
        self.factors = tuple(factors_by_index[index] for index in range(1, 5))

        parents_match = re.search(
            r'"Parents"\s*->\s*<\|(.*?)\|>,\s*"ConditionalTransitions"',
            text,
            re.S,
        )
        if not parents_match:
            raise ValueError(f"Cannot locate Parents in {path}")
        self.parents = {
            int(action): tuple(parse_integer_list(parent_list))
            for action, parent_list in re.findall(
                r'(\d+)\s*->\s*\{([^}]*)\}', parents_match.group(1), re.S
            )
        }

        transitions_match = re.search(
            r'"ConditionalTransitions"\s*->\s*<\|(.*?)\|>,\s*'
            r'"StartState"\s*->',
            text,
            re.S,
        )
        if not transitions_match:
            raise ValueError(f"Cannot locate ConditionalTransitions in {path}")
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
            raise ValueError(f"Cannot locate joint StartState in {path}")
        self.start_state = tuple(parse_integer_list(start_states[-1]))

        hash_match = re.search(r'"Hash"\s*->\s*"([0-9a-f]+)"', text)
        self.model_hash = hash_match.group(1) if hash_match else ""

        self.action_to_factor: dict[int, int] = {}
        self.probe_to_factor_and_position: dict[int, tuple[int, int]] = {}
        for factor_position, factor in enumerate(self.factors):
            for action in factor.actions:
                self.action_to_factor[action] = factor_position
            for probe_position, probe in enumerate(factor.probes):
                self.probe_to_factor_and_position[probe] = (
                    factor_position,
                    probe_position,
                )
        if sorted(self.action_to_factor) != list(PUBLIC_ACTIONS):
            raise ValueError(f"TCCT action map is incomplete in {path}")
        if sorted(self.probe_to_factor_and_position) != list(PUBLIC_PROBES):
            raise ValueError(f"TCCT probe map is incomplete in {path}")

    @property
    def conditional_cell_count(self) -> int:
        return len(self.transitions)

    def state_after(self, sequence: Sequence[int]) -> tuple[int, ...]:
        state = list(self.start_state)
        for action in sequence:
            target_factor = self.action_to_factor[action]
            parent_factors_one_based = self.parents.get(action, ())
            parent_states = tuple(state[index - 1] for index in parent_factors_one_based)
            key = (action, state[target_factor], parent_states)
            destination = self.transitions.get(key)
            if destination is None:
                raise KeyError(f"Missing TCCT transition {key} in {self.path}")
            state[target_factor] = destination
        return tuple(state)

    def signature_cached(self, sequence: Sequence[int]) -> tuple[int, ...]:
        state = self.state_after(sequence)
        result: list[int] = []
        for probe in PUBLIC_PROBES:
            factor_position, probe_position = self.probe_to_factor_and_position[probe]
            local_state = state[factor_position]
            result.append(self.factors[factor_position].signatures[local_state][probe_position])
        return tuple(result)

    def signature_reference(self, sequence: Sequence[int]) -> tuple[int, ...]:
        # Mirrors the S125-C Table[S119BFactorizedOutput[seq, probe], ...]
        # path, which recomputes the factorized state once for every probe.
        result: list[int] = []
        for probe in PUBLIC_PROBES:
            state = self.state_after(sequence)
            factor_position, probe_position = self.probe_to_factor_and_position[probe]
            local_state = state[factor_position]
            result.append(self.factors[factor_position].signatures[local_state][probe_position])
        return tuple(result)


@dataclass(frozen=True)
class TransformerBlockArrays:
    norm1_scale: np.ndarray
    norm1_bias: np.ndarray
    query_weight: np.ndarray
    query_bias: np.ndarray
    key_weight: np.ndarray
    key_bias: np.ndarray
    value_weight: np.ndarray
    value_bias: np.ndarray
    merge_weight: np.ndarray
    merge_bias: np.ndarray
    norm2_scale: np.ndarray
    norm2_bias: np.ndarray
    ff1_weight: np.ndarray
    ff1_bias: np.ndarray
    ff2_weight: np.ndarray
    ff2_bias: np.ndarray


class FrozenTransformerReasoner:
    def __init__(self, path: Path, heads: int = 4):
        self.path = path
        with h5py.File(path, "r") as handle:
            array_group = handle["Arrays"]
            ordered = [
                np.asarray(array_group[str(index)], dtype=np.float32)
                for index in range(1, len(array_group) + 1)
            ]
            version_value = handle["Version"][()]
        self.wlnet_version = (
            version_value.decode("utf-8")
            if isinstance(version_value, (bytes, bytearray))
            else str(version_value)
        )
        if (len(ordered) - 6) % 16 != 0:
            raise ValueError(f"Unexpected frozen array count in {path}")
        self.block_count = (len(ordered) - 6) // 16
        self.input_weight = ordered[0]
        self.input_bias = ordered[1]
        self.model_dimension = int(self.input_weight.shape[0])
        self.heads = heads
        if self.model_dimension % heads != 0:
            raise ValueError(f"Model dimension/head mismatch in {path}")
        self.head_dimension = self.model_dimension // heads

        blocks: list[TransformerBlockArrays] = []
        cursor = 2
        for _ in range(self.block_count):
            values = ordered[cursor : cursor + 16]
            blocks.append(TransformerBlockArrays(*values))
            cursor += 16
        self.blocks = tuple(blocks)
        self.final_norm_scale = ordered[cursor]
        self.final_norm_bias = ordered[cursor + 1]
        self.output_weight = ordered[cursor + 2]
        self.output_bias = ordered[cursor + 3]
        self.parameter_count = int(sum(array.size for array in ordered))
        self.parameter_bytes = int(sum(array.nbytes for array in ordered))

    @staticmethod
    def linear(x: np.ndarray, weight: np.ndarray, bias: np.ndarray) -> np.ndarray:
        return np.matmul(x, weight.T) + bias

    @staticmethod
    def layer_norm(
        x: np.ndarray, scale: np.ndarray, bias: np.ndarray, epsilon: float = 1.0e-5
    ) -> np.ndarray:
        mean = x.mean(axis=-1, keepdims=True, dtype=np.float32)
        centered = x - mean
        variance = np.mean(centered * centered, axis=-1, keepdims=True, dtype=np.float32)
        return centered / np.sqrt(variance + epsilon) * scale + bias

    @staticmethod
    def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
        shifted = x - np.max(x, axis=axis, keepdims=True)
        exponentials = np.exp(shifted)
        return exponentials / np.sum(exponentials, axis=axis, keepdims=True)

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        if inputs.ndim != 3 or inputs.shape[-1] != INPUT_DIMENSION:
            raise ValueError(f"Unexpected input shape {inputs.shape}")
        x = self.linear(inputs.astype(np.float32, copy=False), self.input_weight, self.input_bias)
        sequence_length = x.shape[1]
        causal_mask = np.triu(
            np.full((sequence_length, sequence_length), -1.0e9, dtype=np.float32),
            k=1,
        )
        for block in self.blocks:
            normalized = self.layer_norm(x, block.norm1_scale, block.norm1_bias)
            query = self.linear(normalized, block.query_weight, block.query_bias)
            key = self.linear(normalized, block.key_weight, block.key_bias)
            value = self.linear(normalized, block.value_weight, block.value_bias)
            batch_size = x.shape[0]
            query = query.reshape(
                batch_size, sequence_length, self.heads, self.head_dimension
            ).transpose(0, 2, 1, 3)
            key = key.reshape(
                batch_size, sequence_length, self.heads, self.head_dimension
            ).transpose(0, 2, 1, 3)
            value = value.reshape(
                batch_size, sequence_length, self.heads, self.head_dimension
            ).transpose(0, 2, 1, 3)
            scores = np.matmul(query, key.swapaxes(-1, -2)) / math.sqrt(
                self.head_dimension
            )
            weights = self.softmax(scores + causal_mask[None, None, :, :], axis=-1)
            context = np.matmul(weights, value).transpose(0, 2, 1, 3).reshape(
                batch_size, sequence_length, self.model_dimension
            )
            x = x + self.linear(context, block.merge_weight, block.merge_bias)
            normalized = self.layer_norm(x, block.norm2_scale, block.norm2_bias)
            hidden = self.linear(normalized, block.ff1_weight, block.ff1_bias)
            np.maximum(hidden, 0.0, out=hidden)
            x = x + self.linear(hidden, block.ff2_weight, block.ff2_bias)
        x = self.layer_norm(x, self.final_norm_scale, self.final_norm_bias)
        logits = self.linear(x[:, -1, :], self.output_weight, self.output_bias)
        probabilities = self.softmax(logits, axis=-1)
        return np.argmax(probabilities, axis=-1).astype(np.int8)


def position_vector(position: int) -> np.ndarray:
    values: list[float] = []
    for k in range(POSITION_DIMENSION // 2):
        divisor = 10000.0 ** (2.0 * k / POSITION_DIMENSION)
        values.extend((math.sin(position / divisor), math.cos(position / divisor)))
    return np.asarray(values, dtype=np.float32)


POSITION_VECTORS = {
    position: position_vector(position)
    for position in range(1, REASON_MAX_SEQUENCE_LENGTH + 2)
}


def encode_signature_inputs(sequence: Sequence[int]) -> np.ndarray:
    if len(sequence) > REASON_MAX_SEQUENCE_LENGTH:
        raise ValueError("Sequence exceeds the frozen reasoner capacity")
    base = np.zeros(
        (REASON_MAX_SEQUENCE_LENGTH + 1, INPUT_DIMENSION), dtype=np.float32
    )
    for index in range(REASON_MAX_SEQUENCE_LENGTH):
        position = index + 1
        if index < len(sequence):
            base[index, sequence[index]] = 1.0
            base[index, 8 + 14] = 1.0
        else:
            base[index, 8 + 14 + 1] = 1.0
        base[index, -POSITION_DIMENSION:] = POSITION_VECTORS[position]
    result = np.repeat(base[None, :, :], len(PUBLIC_PROBES), axis=0)
    final_position = REASON_MAX_SEQUENCE_LENGTH
    for probe in PUBLIC_PROBES:
        result[probe, final_position, 8 + probe] = 1.0
        result[probe, final_position, 8 + 14 + 2] = 1.0
        result[probe, final_position, -POSITION_DIMENSION:] = POSITION_VECTORS[
            REASON_MAX_SEQUENCE_LENGTH + 1
        ]
    return result


def encode_sequences(sequences: Sequence[Sequence[int]]) -> np.ndarray:
    if not sequences:
        return np.empty(
            (0, REASON_MAX_SEQUENCE_LENGTH + 1, INPUT_DIMENSION), dtype=np.float32
        )
    return np.concatenate([encode_signature_inputs(sequence) for sequence in sequences])


def build_shape_matched_workload() -> tuple[list[tuple[int, ...]], list[tuple[int, ...]]]:
    # The original prospective sequences use one independent minus action per
    # factor. Action identities do not change tensor or rule lookup shapes, so
    # fixed representative actions preserve the 74/592 case and length profile.
    representative_actions = (0, 2, 4, 6)
    state_sequences: list[tuple[int, ...]] = []
    for factor_tuple in itertools.product(*(range(size) for size in FACTOR_SIZES)):
        if sum(value != 0 for value in factor_tuple) < 3:
            continue
        sequence: list[int] = []
        for action, value, size in zip(
            representative_actions, factor_tuple, FACTOR_SIZES
        ):
            sequence.extend([action] * ((-value) % size))
        state_sequences.append(tuple(sequence))
    transition_sequences = [
        state_sequence + (action,)
        for state_sequence in state_sequences
        for action in PUBLIC_ACTIONS
    ]
    if len(state_sequences) != STATE_SIGNATURE_COUNT:
        raise AssertionError("State workload count drifted")
    if len(transition_sequences) != TRANSITION_SIGNATURE_COUNT:
        raise AssertionError("Transition workload count drifted")
    return state_sequences, transition_sequences


def percentile(values: Sequence[float], percentile_value: float) -> float:
    return float(np.percentile(np.asarray(values, dtype=np.float64), percentile_value))


def latency_samples(
    function: Callable[[], object], samples: int, inner_loops: int
) -> dict[str, float | int]:
    timings_ms: list[float] = []
    checksum = 0
    gc.collect()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        for _ in range(samples):
            start = time.perf_counter_ns()
            output = None
            for _ in range(inner_loops):
                output = function()
            elapsed_ns = time.perf_counter_ns() - start
            timings_ms.append(elapsed_ns / 1_000_000.0 / inner_loops)
            checksum ^= hash(str(np.asarray(output).reshape(-1)[:14].tolist()))
    finally:
        if gc_was_enabled:
            gc.enable()
    return {
        "Samples": samples,
        "InnerLoops": inner_loops,
        "MedianMilliseconds": statistics.median(timings_ms),
        "P95Milliseconds": percentile(timings_ms, 95.0),
        "MinimumMilliseconds": min(timings_ms),
        "MaximumMilliseconds": max(timings_ms),
        "Checksum": checksum,
    }


def timed_dataset(function: Callable[[], Sequence[object]], repeats: int) -> dict[str, float]:
    timings: list[float] = []
    checksums: list[int] = []
    for _ in range(repeats):
        gc.collect()
        start = time.perf_counter()
        output = function()
        elapsed = time.perf_counter() - start
        timings.append(elapsed)
        checksums.append(hash(str(np.asarray(output).reshape(-1)[:128].tolist())))
    if len(set(checksums)) != 1:
        raise AssertionError("Inference checksum changed across timing repeats")
    median_seconds = statistics.median(timings)
    return {
        "Repeats": repeats,
        "MedianSeconds": median_seconds,
        "MinimumSeconds": min(timings),
        "MaximumSeconds": max(timings),
        "SignaturesPerSecond": TOTAL_SIGNATURE_COUNT / median_seconds,
        "ProbePredictionsPerSecond": (TOTAL_SIGNATURE_COUNT * len(PUBLIC_PROBES))
        / median_seconds,
    }


def neural_signatures(
    model: FrozenTransformerReasoner,
    sequences: Sequence[Sequence[int]],
    sequence_batch_size: int,
) -> np.ndarray:
    result: list[np.ndarray] = []
    for offset in range(0, len(sequences), sequence_batch_size):
        chunk = sequences[offset : offset + sequence_batch_size]
        inputs = encode_sequences(chunk)
        predictions = model.forward(inputs).reshape(len(chunk), len(PUBLIC_PROBES))
        result.append(predictions)
    return np.concatenate(result, axis=0)


def benchmark_world(
    world_directory: Path,
    all_sequences: list[tuple[int, ...]],
    quick: bool,
) -> dict[str, object]:
    world_seed_match = re.search(r"seed_(\d+)$", world_directory.name)
    if not world_seed_match:
        raise ValueError(f"Cannot parse world seed from {world_directory.name}")
    world_seed = int(world_seed_match.group(1))
    tcct_path = world_directory / "S124_T5R1_TCCT_FROZEN_BEFORE_HIGHORDER.wl"
    matched_path = (
        world_directory / "S124_T5R1_NEURAL_REASONER_FROZEN_BEFORE_HIGHORDER.wlnet"
    )
    strong_path = (
        world_directory / "S125C_STRONG_NEURAL_REASONER_FROZEN_BEFORE_HIGHORDER.wlnet"
    )
    summary_path = world_directory / "S125C_pilot_summary.wl"
    for required_path in (tcct_path, matched_path, strong_path, summary_path):
        if not required_path.is_file():
            raise FileNotFoundError(required_path)

    load_start = time.perf_counter()
    tcct = FrozenTCCT(tcct_path)
    tcct_load_seconds = time.perf_counter() - load_start
    load_start = time.perf_counter()
    matched = FrozenTransformerReasoner(matched_path)
    matched_load_seconds = time.perf_counter() - load_start
    load_start = time.perf_counter()
    strong = FrozenTransformerReasoner(strong_path)
    strong_load_seconds = time.perf_counter() - load_start

    if matched.parameter_count != EXPECTED_MATCHED_PARAMETERS:
        raise AssertionError(f"Matched parameter count drift in {world_directory}")
    if strong.parameter_count != EXPECTED_STRONG_PARAMETERS:
        raise AssertionError(f"Strong parameter count drift in {world_directory}")
    if tcct.conditional_cell_count not in (41, 42):
        raise AssertionError(f"TCCT conditional-cell count drift in {world_directory}")

    # Audit the cached signature path against the literal S125-C reference path.
    reference_outputs = [tcct.signature_reference(sequence) for sequence in all_sequences]
    cached_outputs = [tcct.signature_cached(sequence) for sequence in all_sequences]
    if reference_outputs != cached_outputs:
        raise AssertionError(f"TCCT cached/reference mismatch in {world_directory}")

    longest_sequence = max(all_sequences, key=len)
    prepared_single = encode_signature_inputs(longest_sequence)
    # Warm all execution paths before timing.
    for _ in range(3):
        tcct.signature_reference(longest_sequence)
        tcct.signature_cached(longest_sequence)
        matched.forward(prepared_single)
        strong.forward(prepared_single)

    latency_sample_count = 7 if quick else 25
    tcct_reference_latency = latency_samples(
        lambda: tcct.signature_reference(longest_sequence),
        latency_sample_count,
        10 if quick else 100,
    )
    tcct_cached_latency = latency_samples(
        lambda: tcct.signature_cached(longest_sequence),
        latency_sample_count,
        50 if quick else 500,
    )
    matched_kernel_latency = latency_samples(
        lambda: matched.forward(prepared_single), latency_sample_count, 1
    )
    matched_end_to_end_latency = latency_samples(
        lambda: matched.forward(encode_signature_inputs(longest_sequence)),
        latency_sample_count,
        1,
    )
    strong_kernel_latency = latency_samples(
        lambda: strong.forward(prepared_single), latency_sample_count, 1
    )
    strong_end_to_end_latency = latency_samples(
        lambda: strong.forward(encode_signature_inputs(longest_sequence)),
        latency_sample_count,
        1,
    )

    dataset_repeats = 1 if quick else 3
    tcct_reference_throughput = timed_dataset(
        lambda: [tcct.signature_reference(sequence) for sequence in all_sequences],
        dataset_repeats,
    )
    tcct_cached_throughput = timed_dataset(
        lambda: [tcct.signature_cached(sequence) for sequence in all_sequences],
        dataset_repeats,
    )

    batch_sizes = (1, 32) if quick else (1, 32, 256)
    audit_sequences = all_sequences[:32] + [longest_sequence]
    matched_audit_predictions = {
        batch_size: neural_signatures(matched, audit_sequences, batch_size)
        for batch_size in batch_sizes
    }
    strong_audit_predictions = {
        batch_size: neural_signatures(strong, audit_sequences, batch_size)
        for batch_size in batch_sizes
    }
    if any(
        not np.array_equal(matched_audit_predictions[batch_sizes[0]], value)
        for value in matched_audit_predictions.values()
    ):
        raise AssertionError(f"Matched predictions changed with batching in {world_directory}")
    if any(
        not np.array_equal(strong_audit_predictions[batch_sizes[0]], value)
        for value in strong_audit_predictions.values()
    ):
        raise AssertionError(f"Strong predictions changed with batching in {world_directory}")

    matched_throughput: dict[str, dict[str, float]] = {}
    strong_throughput: dict[str, dict[str, float]] = {}
    for batch_size in batch_sizes:
        matched_throughput[str(batch_size)] = timed_dataset(
            lambda batch_size=batch_size: neural_signatures(
                matched, all_sequences, batch_size
            ),
            1,
        )
        strong_throughput[str(batch_size)] = timed_dataset(
            lambda batch_size=batch_size: neural_signatures(
                strong, all_sequences, batch_size
            ),
            1,
        )

    best_matched_batch = max(
        matched_throughput,
        key=lambda batch: matched_throughput[batch]["SignaturesPerSecond"],
    )
    best_strong_batch = max(
        strong_throughput,
        key=lambda batch: strong_throughput[batch]["SignaturesPerSecond"],
    )
    return {
        "WorldDirectory": world_directory.name,
        "WorldSeed": world_seed,
        "Audits": {
            "TCCTCachedEqualsReference": True,
            "MatchedBatchInvariant": True,
            "StrongBatchInvariant": True,
            "WorkloadSignatureCount": len(all_sequences),
            "WorkloadProbePredictionCount": len(all_sequences) * len(PUBLIC_PROBES),
            "LongestSequenceLength": len(longest_sequence),
        },
        "FrozenArtifacts": {
            "TCCTSHA256": sha256_file(tcct_path),
            "MatchedSHA256": sha256_file(matched_path),
            "StrongSHA256": sha256_file(strong_path),
            "SummarySHA256": sha256_file(summary_path),
            "TCCTFileBytes": tcct_path.stat().st_size,
            "MatchedFileBytes": matched_path.stat().st_size,
            "StrongFileBytes": strong_path.stat().st_size,
            "TCCTConditionalCells": tcct.conditional_cell_count,
            "MatchedParameters": matched.parameter_count,
            "StrongParameters": strong.parameter_count,
            "MatchedParameterBytes": matched.parameter_bytes,
            "StrongParameterBytes": strong.parameter_bytes,
            "MatchedBlocks": matched.block_count,
            "StrongBlocks": strong.block_count,
            "MatchedModelDimension": matched.model_dimension,
            "StrongModelDimension": strong.model_dimension,
            "WLNetVersion": matched.wlnet_version,
        },
        "LoadSeconds": {
            "TCCT": tcct_load_seconds,
            "Matched": matched_load_seconds,
            "Strong": strong_load_seconds,
        },
        "SingleSignatureLatency": {
            "TCCTReference": tcct_reference_latency,
            "TCCTCached": tcct_cached_latency,
            "MatchedKernelOnly": matched_kernel_latency,
            "MatchedEndToEnd": matched_end_to_end_latency,
            "StrongKernelOnly": strong_kernel_latency,
            "StrongEndToEnd": strong_end_to_end_latency,
        },
        "FullWorkloadThroughput": {
            "TCCTReference": tcct_reference_throughput,
            "TCCTCached": tcct_cached_throughput,
            "MatchedBySequenceBatch": matched_throughput,
            "StrongBySequenceBatch": strong_throughput,
            "BestMatchedBatch": int(best_matched_batch),
            "BestStrongBatch": int(best_strong_batch),
        },
    }


def aggregate_results(worlds: Sequence[dict[str, object]]) -> dict[str, object]:
    def values(path: Sequence[str]) -> list[float]:
        result: list[float] = []
        for world in worlds:
            value: object = world
            for key in path:
                value = value[key]  # type: ignore[index]
            result.append(float(value))
        return result

    def describe(path: Sequence[str]) -> dict[str, float]:
        raw = values(path)
        return {
            "Mean": statistics.fmean(raw),
            "Median": statistics.median(raw),
            "Minimum": min(raw),
            "Maximum": max(raw),
        }

    latency_paths = {
        name: ["SingleSignatureLatency", name, "MedianMilliseconds"]
        for name in (
            "TCCTReference",
            "TCCTCached",
            "MatchedKernelOnly",
            "MatchedEndToEnd",
            "StrongKernelOnly",
            "StrongEndToEnd",
        )
    }
    latency_summary = {name: describe(path) for name, path in latency_paths.items()}

    tcct_reference_qps = describe(
        ["FullWorkloadThroughput", "TCCTReference", "SignaturesPerSecond"]
    )
    tcct_cached_qps = describe(
        ["FullWorkloadThroughput", "TCCTCached", "SignaturesPerSecond"]
    )
    matched_best_qps: list[float] = []
    strong_best_qps: list[float] = []
    matched_best_batches: list[int] = []
    strong_best_batches: list[int] = []
    for world in worlds:
        throughput = world["FullWorkloadThroughput"]  # type: ignore[index]
        matched_batch = str(throughput["BestMatchedBatch"])
        strong_batch = str(throughput["BestStrongBatch"])
        matched_best_batches.append(int(matched_batch))
        strong_best_batches.append(int(strong_batch))
        matched_best_qps.append(
            float(throughput["MatchedBySequenceBatch"][matched_batch]["SignaturesPerSecond"])
        )
        strong_best_qps.append(
            float(throughput["StrongBySequenceBatch"][strong_batch]["SignaturesPerSecond"])
        )

    def describe_raw(raw: Sequence[float]) -> dict[str, float]:
        return {
            "Mean": statistics.fmean(raw),
            "Median": statistics.median(raw),
            "Minimum": min(raw),
            "Maximum": max(raw),
        }

    matched_best_summary = describe_raw(matched_best_qps)
    strong_best_summary = describe_raw(strong_best_qps)
    return {
        "WorldCount": len(worlds),
        "AllAuditsPassed": all(
            bool(world["Audits"]["TCCTCachedEqualsReference"])
            and bool(world["Audits"]["MatchedBatchInvariant"])
            and bool(world["Audits"]["StrongBatchInvariant"])
            for world in worlds
        ),
        "SingleSignatureMedianMillisecondsAcrossWorlds": latency_summary,
        "FullWorkloadSignaturesPerSecondAcrossWorlds": {
            "TCCTReference": tcct_reference_qps,
            "TCCTCached": tcct_cached_qps,
            "MatchedBestBatch": matched_best_summary,
            "StrongBestBatch": strong_best_summary,
        },
        "BestMatchedBatches": matched_best_batches,
        "BestStrongBatches": strong_best_batches,
        "SpeedupRatiosUsingCrossWorldMedians": {
            "MatchedEndToEndLatencyDividedByTCCTReference": (
                latency_summary["MatchedEndToEnd"]["Median"]
                / latency_summary["TCCTReference"]["Median"]
            ),
            "MatchedEndToEndLatencyDividedByTCCTCached": (
                latency_summary["MatchedEndToEnd"]["Median"]
                / latency_summary["TCCTCached"]["Median"]
            ),
            "StrongEndToEndLatencyDividedByTCCTReference": (
                latency_summary["StrongEndToEnd"]["Median"]
                / latency_summary["TCCTReference"]["Median"]
            ),
            "StrongEndToEndLatencyDividedByTCCTCached": (
                latency_summary["StrongEndToEnd"]["Median"]
                / latency_summary["TCCTCached"]["Median"]
            ),
            "TCCTReferenceThroughputDividedByMatchedBest": (
                tcct_reference_qps["Median"] / matched_best_summary["Median"]
            ),
            "TCCTCachedThroughputDividedByMatchedBest": (
                tcct_cached_qps["Median"] / matched_best_summary["Median"]
            ),
            "TCCTReferenceThroughputDividedByStrongBest": (
                tcct_reference_qps["Median"] / strong_best_summary["Median"]
            ),
            "TCCTCachedThroughputDividedByStrongBest": (
                tcct_cached_qps["Median"] / strong_best_summary["Median"]
            ),
        },
    }


def write_per_world_csv(path: Path, worlds: Sequence[dict[str, object]]) -> None:
    columns = [
        "WorldSeed",
        "TCCTCells",
        "TCCTReferenceLatencyMs",
        "TCCTCachedLatencyMs",
        "MatchedEndToEndLatencyMs",
        "StrongEndToEndLatencyMs",
        "TCCTReferenceSignaturesPerSecond",
        "TCCTCachedSignaturesPerSecond",
        "MatchedBestBatch",
        "MatchedBestSignaturesPerSecond",
        "StrongBestBatch",
        "StrongBestSignaturesPerSecond",
        "AllAuditsPassed",
    ]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for world in worlds:
            latency = world["SingleSignatureLatency"]
            throughput = world["FullWorkloadThroughput"]
            matched_batch = str(throughput["BestMatchedBatch"])
            strong_batch = str(throughput["BestStrongBatch"])
            audits = world["Audits"]
            writer.writerow(
                {
                    "WorldSeed": world["WorldSeed"],
                    "TCCTCells": world["FrozenArtifacts"]["TCCTConditionalCells"],
                    "TCCTReferenceLatencyMs": latency["TCCTReference"][
                        "MedianMilliseconds"
                    ],
                    "TCCTCachedLatencyMs": latency["TCCTCached"][
                        "MedianMilliseconds"
                    ],
                    "MatchedEndToEndLatencyMs": latency["MatchedEndToEnd"][
                        "MedianMilliseconds"
                    ],
                    "StrongEndToEndLatencyMs": latency["StrongEndToEnd"][
                        "MedianMilliseconds"
                    ],
                    "TCCTReferenceSignaturesPerSecond": throughput[
                        "TCCTReference"
                    ]["SignaturesPerSecond"],
                    "TCCTCachedSignaturesPerSecond": throughput["TCCTCached"][
                        "SignaturesPerSecond"
                    ],
                    "MatchedBestBatch": matched_batch,
                    "MatchedBestSignaturesPerSecond": throughput[
                        "MatchedBySequenceBatch"
                    ][matched_batch]["SignaturesPerSecond"],
                    "StrongBestBatch": strong_batch,
                    "StrongBestSignaturesPerSecond": throughput[
                        "StrongBySequenceBatch"
                    ][strong_batch]["SignaturesPerSecond"],
                    "AllAuditsPassed": bool(audits["TCCTCachedEqualsReference"])
                    and bool(audits["MatchedBatchInvariant"])
                    and bool(audits["StrongBatchInvariant"]),
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--world-limit", type=int, default=5)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    state_sequences, transition_sequences = build_shape_matched_workload()
    all_sequences = state_sequences + transition_sequences
    world_directories = sorted(args.root.glob("world_*_seed_*"))[: args.world_limit]
    if len(world_directories) != args.world_limit:
        raise RuntimeError(
            f"Expected {args.world_limit} world directories, found {len(world_directories)}"
        )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    print(f"BENCHMARK_VERSION={BENCHMARK_VERSION}", flush=True)
    print(f"WORLD_COUNT={len(world_directories)}", flush=True)
    print(f"SIGNATURE_COUNT={len(all_sequences)}", flush=True)

    worlds: list[dict[str, object]] = []
    overall_start = time.perf_counter()
    for world_directory in world_directories:
        print(f"WORLD_START={world_directory.name}", flush=True)
        world_result = benchmark_world(world_directory, all_sequences, args.quick)
        worlds.append(world_result)
        print(
            "WORLD_DONE="
            + world_directory.name
            + ",TCCT_CACHED_MS="
            + f"{world_result['SingleSignatureLatency']['TCCTCached']['MedianMilliseconds']:.6f}"
            + ",MATCHED_MS="
            + f"{world_result['SingleSignatureLatency']['MatchedEndToEnd']['MedianMilliseconds']:.6f}"
            + ",STRONG_MS="
            + f"{world_result['SingleSignatureLatency']['StrongEndToEnd']['MedianMilliseconds']:.6f}",
            flush=True,
        )
    aggregate = aggregate_results(worlds)
    elapsed_seconds = time.perf_counter() - overall_start

    try:
        from threadpoolctl import threadpool_info

        thread_pool_information: object = threadpool_info()
    except Exception as error:  # pragma: no cover - optional diagnostic
        thread_pool_information = {"Unavailable": str(error)}

    raw_result = {
        "BenchmarkVersion": BENCHMARK_VERSION,
        "Protocol": {
            "FrozenModelsOnly": True,
            "Retraining": False,
            "ModelMutation": False,
            "Runtime": "NumPy CPU architecture-level same-process benchmark",
            "NotWolframKernelWallClock": True,
            "TCCTReferenceMeaning": "Literal S125-C per-probe state recomputation",
            "TCCTCachedMeaning": "One state fold per 14-probe signature; identical outputs",
            "Workload": {
                "StateSignatures": len(state_sequences),
                "TransitionSignatures": len(transition_sequences),
                "TotalSignatures": len(all_sequences),
                "ProbesPerSignature": len(PUBLIC_PROBES),
                "TotalProbePredictions": len(all_sequences) * len(PUBLIC_PROBES),
                "FrozenMaximumSequenceLength": REASON_MAX_SEQUENCE_LENGTH,
                "LongestMeasuredSequenceLength": max(map(len, all_sequences)),
            },
        },
        "Environment": {
            "Python": sys.version,
            "NumPy": np.__version__,
            "H5Py": h5py.__version__,
            "Platform": platform.platform(),
            "Processor": platform.processor(),
            "LogicalProcessors": os.cpu_count(),
            "ThreadPools": thread_pool_information,
        },
        "QuickMode": args.quick,
        "ElapsedSeconds": elapsed_seconds,
        "Worlds": worlds,
        "Aggregate": aggregate,
    }
    suffix = "quick" if args.quick else "full"
    raw_path = args.output_dir / f"S125D_speed_benchmark_{suffix}_raw.json"
    summary_path = args.output_dir / f"S125D_speed_benchmark_{suffix}_summary.json"
    csv_path = args.output_dir / f"S125D_speed_benchmark_{suffix}_per_world.csv"
    raw_path.write_text(
        json.dumps(raw_result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary_path.write_text(
        json.dumps(
            {
                "BenchmarkVersion": BENCHMARK_VERSION,
                "Protocol": raw_result["Protocol"],
                "Environment": raw_result["Environment"],
                "ElapsedSeconds": elapsed_seconds,
                "Aggregate": aggregate,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    write_per_world_csv(csv_path, worlds)
    print(f"ALL_AUDITS_PASSED={aggregate['AllAuditsPassed']}", flush=True)
    print(f"RAW_RESULT={raw_path}", flush=True)
    print(f"SUMMARY_RESULT={summary_path}", flush=True)
    print(f"PER_WORLD_CSV={csv_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
