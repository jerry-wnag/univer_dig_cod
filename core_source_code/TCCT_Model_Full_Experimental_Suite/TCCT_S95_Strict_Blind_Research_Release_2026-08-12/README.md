# TCCT: A Mechanism-First Symbolic Graph Reasoning Prototype

**Release:** S95 Strict Blind Research Release  
**Snapshot date:** 2026-08-12  
**Status:** Experimental research prototype; ready for external technical review, not production use

**Parent project:** [A Minimal model for causal invariance: path merging via DP-like optimization](https://github.com/jerry-wnag/univer_dig_cod)  
**Existing parent archive:** [Zenodo v9.2.0, DOI 10.5281/zenodo.20619538](https://doi.org/10.5281/zenodo.20619538)

## Overview

TCCT is a deterministic symbolic graph-reasoning research prototype implemented primarily in the Wolfram Language. It studies whether a compact relational mechanism can propagate graph state, preserve query-relevant structure, and make stable decisions under changes in depth, topology, query role, and interventions.

The project uses a mechanism-first experimental process:

- freeze candidates before blind evaluation;
- hash protocols, test definitions, candidates, and result certificates;
- preserve valid failures instead of tuning them away;
- separate the graph core from representation and readout layers;
- audit whether canonicalization, intervention rules, deduplication, or undirected-freeze behavior changed;
- distinguish development results, post-hoc audits, independent confirmations, and strict blind tests.

The strongest current result is S95: a pre-registered strict blind test over new topology compositions, contexts, depths, and branch counts. The frozen system achieved **180/180 correct pairs** across **360 worlds**, with **1.0 overall accuracy**, **1.0 worst-axis-group accuracy**, and a **minimum decision margin of 1.8515601232**. No training, candidate search, re-export, core change, rule change, deduplication change, or undirected-freeze change occurred during S95.

This is meaningful evidence of compositional out-of-distribution generalization inside the studied synthetic graph grammar. It is **not** evidence of general intelligence, unrestricted causal reasoning, causal discovery, or a general-purpose AI foundation model.

## Current Research Stage

TCCT has moved beyond a proof of concept. It is best described as a:

> **hash-locked, mechanism-audited symbolic reasoning prototype with multiple blind-transfer successes, preserved blind failures, an independently confirmed frozen readout, and one pre-registered strict blind pass.**

It is closer to a publishable specialized reasoning system than to an AI foundation model. The next scientific milestone is a fair external benchmark and independent reproduction, not a claim of general intelligence.

## Architecture

The current experimental pipeline has five conceptual layers:

1. **Graph-world generation** — deterministic synthetic graph families, query roles, contexts, and interventions.
2. **Propagation core** — fixed relational-state propagation through the graph.
3. **Canonicalization and deduplication** — normalization of supported topology compositions while preserving the locked undirected-freeze and deduplication semantics.
4. **Representation** — compact multiset-aware, role-aware, or query-scoped symbolic features.
5. **Frozen readout** — deterministic decision logic applied without test-time training or candidate search.

The project history is important: several failures were caused by insufficient outer representation or readout coverage even when the core retained useful information. Later stages therefore improved and froze outer readouts while retaining explicit integrity checks on the original core and rules.

## Verified Capabilities

The evidence in this release supports the following limited capabilities inside the tested synthetic graph families:

- deterministic relational-state propagation;
- depth and propagation-horizon generalization when the horizon is sufficient;
- transfer across multiple unseen graph-topology transformations;
- role-sensitive and query-relative representation;
- paired structural counterfactual comparison;
- local mediator intervention evaluation;
- stop-relocation counterfactual transfer;
- intervention identity, inverse, composition, and path-independence consistency;
- frozen-model evaluation with no test-time training or search;
- checkpointed, resumable long-running evaluation;
- hash-based integrity checks and explicit mechanism-change audits;
- diagnosis of representation/readout bottlenecks after valid blind failures;
- strict pre-registration followed by a successful held-out evaluation.

These are properties of a controlled symbolic benchmark family. They should not be extrapolated to unrestricted real-world graphs or natural-language causal questions without new evidence.

## Selected Experimental Timeline

| Stage | Protocol | Result | Interpretation |
|---|---|---:|---|
| S71 | Frozen model; SharedMerge used for validation; ParallelIn held blind | 32/32 | First clean blind topology-transfer checkpoint in the studied family. |
| S77-S78 | Propagation-horizon and depth stress tests | Exact recovery at sufficient horizon, including depth 127 | The propagation mechanism scaled correctly when allowed enough rounds. |
| S83 | Blind query-switch and topology-composition test | Valid failure | Query-role information was missing from the then-current token interface. |
| S86 | Blind external six-branch counterfactual test | 44/288 | Valid blind failure; motivated a broader exact-role representation. |
| S87 | Blind seven-branch mixed-intervention test | 20/392 | Valid failure localized mainly to outer policy coverage. |
| S87D | Frozen world-multiset decoder | Frozen and hash-locked | Established the candidate used by S88-S92. |
| S88 | Blind eight-branch frozen-decoder test | 512/512 worlds | Blind topology/arity composition transfer. |
| S89 | Blind stop-relocation counterfactual test | 512/512 worlds | Blind relocation transfer with frozen decoder. |
| S90 | Blind intervention-algebra test | 1296/1296 worlds | Identity, inverse, composition, and path-independence checks passed. |
| S91 | Locked post-hoc baseline and ablation benchmark | Completed | Full frozen system scored 1296/1296; legacy policy scored 128/1296. This was not a neural baseline. |
| S92 | Cardinality-matched relational blind test | 40/80 worlds; 0.5 accuracy | Valid blind failure showing that the single-world decoder did not solve the harder relational contrast. |
| S92A-S92B | Failure audit, paired-contrast development and freeze | Decoder frozen | Developed a paired readout after S92 labels were revealed; this is development evidence. |
| S93 | New paired counterfactual blind test | 48/48 pairs; 96/96 oriented decisions | Blind transfer of the frozen paired-contrast decoder. |
| S94 | Mixed-context blind run | Invalid/aborted artifact | The zero-byte certificate is retained; it is not counted as evidence. |
| S94A-S94G | Modulus, role, representation, binding, channel, and full-query audits | Development/audit sequence | Localized information loss and produced a full-query-scope candidate. |
| S94H-R3 | Independent confirmation of the frozen full-query readout | 312/312 pairs, 624 worlds | Independent confirmation with 1.0 worst-group accuracy and minimum margin 2.6671855964. |
| S95 | Pre-registered strict blind test | 180/180 pairs, 360 worlds | Current strongest result: strict blind pass over new topologies, contexts, and scales. |

See [EXPERIMENT_TIMELINE.md](docs/EXPERIMENT_TIMELINE.md) for protocol distinctions and [CLAIMS_AND_LIMITATIONS.md](docs/CLAIMS_AND_LIMITATIONS.md) for claim boundaries.

## S95 Strict Blind Result

The S95 protocol was committed before test-world generation. It locked:

- topologies: `HeterogeneousSerialDiamondIn` and `UnilateralNestedDiamondIn`;
- contexts: `BinaryWeightOdd`, `AlternatingBlocksFour`, and `EndpointOrSquare`;
- scales: depth/branch-count pairs `(29, 11)` and `(61, 19)`;
- expected size: 12 scenarios, 180 pairs, and 360 worlds;
- pass thresholds: overall accuracy at least 0.95 and worst-axis-group accuracy at least 0.80;
- prohibition of training, candidate search, candidate re-export, core changes, rule changes, deduplication changes, and undirected-freeze changes.

Observed result:

| Metric | Value |
|---|---:|
| Scenarios | 12 |
| Pairs | 180 |
| Worlds | 360 |
| Correct pairs | 180 |
| Accuracy | 1.0 |
| Worst-axis-group accuracy | 1.0 |
| Minimum margin | 1.8515601232347252 |
| Zero scores | 0 |
| Outcome | `S95_STRICT_BLIND_PASS` |

The precommit and test-definition hashes in the result certificate match the distributed files. The result certificate is at `certificates/TCCT_S95_StrictBlindCertificate.json`.

## Repository Layout

```text
TCCT_S95_Strict_Blind_Research_Release_2026-08-12/
|-- README.md
|-- LICENSE
|-- CITATION.cff
|-- MANIFEST_SHA256.csv
|-- RELEASE_INTEGRITY.json
|-- experiments/                 S71-S95 Wolfram sources, notebooks,
|                                precommits, builders, and launchers
|-- artifacts/
|   |-- frozen_models/           frozen candidates and decoder runtimes
|   `-- development/             selected development datasets
|-- certificates/                non-empty result and audit certificates
|-- checkpoints/
|   |-- S94H_R3/                 24 independent-confirmation checkpoints
|   `-- S95/                     12 strict-blind checkpoints
|-- docs/
|   |-- CLAIMS_AND_LIMITATIONS.md
|   |-- EXPERIMENT_TIMELINE.md
|   |-- REPRODUCIBILITY.md
|   `-- Blind Topology Transfer Checkpoint.pdf
|-- historical_milestones/       compact metadata from earlier archives
`-- tools/                        recovery and notebook-building utilities
```

Runtime connection files, Jupyter tokens, license configuration, password files, PID files, caches, compiled Python files, and local logs are intentionally excluded.

## Reproduction

### Requirements

- Windows 10 or 11;
- Wolfram Engine or Mathematica 15.x;
- Python 3;
- JupyterLab or Jupyter Notebook;
- Wolfram Language for Jupyter.

The executed S95 notebook is `experiments/TCCT_S95_StrictBlind.ipynb`. The matching Wolfram source, precommit, test definitions, and build record are in the same directory.

The historical Windows launchers contain machine-local paths and may require editing on another computer. They are retained as provenance, not as portable installation scripts. Read [REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md) before attempting a clean rerun.

## What Remains Before a Strong Publication Claim

The highest-priority work is:

1. compare against fair Transformer, graph-neural-network, symbolic-search, and simple heuristic baselines under controlled compute and data budgets;
2. reproduce the result on a second machine from a clean environment;
3. add confidence intervals or repeated pre-registered seeds where stochastic generation is used;
4. test genuinely out-of-grammar motifs rather than only new compositions of supported primitives;
5. measure time and memory scaling independently of notebook overhead;
6. separate a compact reference implementation from the full historical research archive;
7. obtain independent review of the task generator, labels, leakage controls, and claim wording.

## Distance from an AI Foundation Model

TCCT is still far from being an AI foundation model. A foundation model normally requires broad data, large-scale trainable representations, transfer across many task families and modalities, standardized interfaces, robust deployment, safety evaluation, and competitive external benchmarks. TCCT currently has none of those at foundation-model scale.

Its present value is narrower and scientifically cleaner: it is an interpretable research substrate for studying compositional graph reasoning, representation bottlenecks, counterfactual comparisons, and strict blind-evaluation discipline.

## Parent Project, License, and Citation

This AI-reasoning research branch is part of the broader TCCT project maintained at:

- GitHub: <https://github.com/jerry-wnag/univer_dig_cod>
- Existing Zenodo archive: <https://doi.org/10.5281/zenodo.20619538>

The Zenodo record is the parent project's published **v9.2.0** archive dated **2026-06-10**. It predates this S95 snapshot and therefore must not be described as an archive of the S95 files. When this snapshot is deposited as a new Zenodo version, update `CITATION.cff` and this section with the new version-specific DOI.

This release follows the parent repository and is distributed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See [LICENSE](LICENSE). Copyright (c) 2026 Wang Xin.

Until a version-specific S95 DOI is issued, cite this snapshot as:

> Wang, Xin. (2026). *TCCT: S95 Strict Blind Research Release* (research software snapshot, 2026-08-12). GitHub repository: <https://github.com/jerry-wnag/univer_dig_cod>. Parent project archive: <https://doi.org/10.5281/zenodo.20619538>.

Machine-readable citation metadata is provided in `CITATION.cff`.
