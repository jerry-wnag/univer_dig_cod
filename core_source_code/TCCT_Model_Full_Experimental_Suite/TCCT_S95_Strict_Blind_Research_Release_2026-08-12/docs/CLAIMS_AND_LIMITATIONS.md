# Claims and Limitations

## Supported Claims

The distributed certificates and notebooks support the following claims within the controlled TCCT synthetic graph families:

1. The system performs deterministic relational-state propagation and can recover correct outcomes across tested depth changes when the propagation horizon is sufficient.
2. Frozen candidates have transferred across several unseen topology, arity, query-role, and intervention configurations.
3. The system has passed blind tests involving paired structural counterfactuals, stop relocation, and a predefined intervention algebra.
4. S95 is a pre-registered strict blind pass: 180/180 pairs across 360 worlds, with 1.0 overall and worst-axis-group accuracy.
5. Major certificates explicitly report that the original frozen model, core mechanism, deduplication mechanism, and undirected-freeze mechanism were not changed during their corresponding evaluations.
6. Valid failures were retained. In particular, S92 achieved only 0.5 accuracy, which exposed a relational readout limitation and led to a separately labeled development-and-freeze cycle before S93.

## Claims That Are Not Supported

This release does not support claims of:

- artificial general intelligence;
- a general-purpose AI foundation model;
- unrestricted causal reasoning or causal discovery;
- natural-language understanding;
- autonomous open-ended learning;
- robustness on arbitrary real-world graphs;
- superiority to Transformers or graph neural networks;
- production readiness;
- human-level reasoning;
- guaranteed generalization outside the tested grammar.

## Why the Counterfactual Claim Is Limited

The project evaluates controlled structural interventions and compares paired graph worlds. This is a real operational form of counterfactual reasoning inside the benchmark: the system evaluates how the predicted action changes under a specified intervention while other construction rules are held fixed.

However, these tests use synthetic worlds, predefined intervention semantics, and generated labels. They do not establish causal discovery from observational data, reasoning over ambiguous natural-language narratives, or valid intervention semantics in real scientific domains.

The safest description is:

> TCCT demonstrates frozen, compositional structural-counterfactual reasoning within a controlled synthetic graph grammar.

## Why S95 Is Stronger Than Earlier Results

S95 was pre-registered after the S94H-R3 candidate had been independently confirmed and frozen. The precommit fixed the topologies, contexts, scales, sample counts, thresholds, and prohibited changes before any S95 world was executed. Its test-definition and precommit hashes match the final certificate.

This reduces several common risks:

- tuning directly on the final test;
- quietly changing the candidate after seeing errors;
- changing the task semantics during evaluation;
- reporting only favorable subgroups;
- treating a post-hoc development result as blind evidence.

It does not eliminate benchmark-family bias: the test designer still created both the training environment and the held-out grammar. Independent reproduction remains necessary.

## Known Technical Limitations

- The system is implemented as a research pipeline rather than a compact reusable library.
- Some historical launchers contain local Windows paths.
- Runtime is dominated by unoptimized Wolfram graph construction, tracing, and notebook overhead.
- Earlier finite-modulus encodings exhibited collisions. Later readouts reduced observed failures, but unrestricted collision safety has not been proven.
- Many new topologies remain compositions of known canonicalizable primitives.
- The current benchmark does not measure noisy perception, missing edges, continuous attributes, adversarial input, or real-world causal ambiguity.
- S91 compared symbolic baselines and ablations; it was not a fair Transformer or GNN benchmark.
- There is no independent external replication in this snapshot.

## Current Maturity Assessment

TCCT is a **specialized research prototype at the evidence-building/pre-publication stage**. It has passed the stages of executable implementation, mechanism auditing, frozen-candidate evaluation, valid-failure analysis, independent confirmation, and one strict pre-registered blind test.

It has not passed the stages required of an AI foundation layer: broad task coverage, scalable training, standard downstream interfaces, external benchmarks, independent reproduction, production robustness, and safety/security evaluation.

The gap to a publishable specialized-method paper is moderate and concrete. The gap to a foundation model is qualitative, not merely a matter of adding more test cases.
