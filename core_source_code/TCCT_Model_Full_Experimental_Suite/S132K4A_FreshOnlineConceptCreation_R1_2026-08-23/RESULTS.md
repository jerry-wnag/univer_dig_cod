# S132-K4A Results

## Outcome

`VERIFIED_FRESH_ONLINE_BOUNDED_CONCEPT_CREATION_GATE_PASS`

The frozen S132-K4A system began with an empty concept library and no K3A
schemas. Ten structured worlds and ten action-image-rank-matched controls were
materialized only after the protocol and source hashes were frozen. The native
Wolfram run passed, and an independent Python implementation reconstructed the
query traces, learner counters, concept-library trajectory, control ranks,
aggregates, and final gate.

## Preregistered gate results

| Measure | Result |
|---|---:|
| Structured worlds | 10/10 exact |
| Matched baselines | 10/10 exact |
| Rank-matched controls | 10/10 exact in both modes |
| Unsafe committed inferences | 0 |
| Starting structured concept library | 0 |
| Final structured concept library | 108 |
| Final control concept library | 0 |
| Eligible later structured worlds with positive MQ savings | 6/9 (66.7%) |
| Structured membership queries | 1484 -> 1289 |
| Structured membership-query savings | 195 (13.14%) |
| Structured logical interaction cost | 1494 -> 1300 |
| Structured logical-cost savings | 194 (12.99%) |
| Structured concrete oracle-cell cost | 2968 -> 2828 |
| Structured concrete-cost savings | 140 (4.72%) |
| Control membership-query savings | 0 |
| Control concrete-cost savings | 0 |
| Native Wolfram runtime | 109.60 seconds |

## Sequential trajectory

| World | States x actions | Library before -> after | New concepts | Baseline MQ | Transfer MQ | MQ saved | Concrete saved | Final inferred | Counterexamples / rollbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Q401 | 20 x 3 | 0 -> 1 | 1 | 60 | 60 | 0 | 0 | 0 | 0 / 0 |
| Q402 | 30 x 3 | 1 -> 3 | 2 | 90 | 90 | 0 | 0 | 0 | 0 / 0 |
| Q403 | 60 x 4 | 3 -> 50 | 47 | 240 | 228 | 12 | 12 | 12 | 0 / 0 |
| Q404 | 40 x 4 | 50 -> 83 | 33 | 160 | 142 | 18 | 18 | 18 | 0 / 0 |
| Q405 | 48 x 4 | 83 -> 83 | 0 | 192 | 192 | 0 | 0 | 0 | 0 / 0 |
| Q406 | 20 x 3 | 83 -> 85 | 2 | 60 | 60 | 0 | 0 | 0 | 0 / 0 |
| Q407 | 30 x 3 | 85 -> 96 | 11 | 90 | 72 | 18 | -37 | 17 | 1 / 1 |
| Q408 | 60 x 4 | 96 -> 96 | 0 | 240 | 178 | 62 | 62 | 62 | 0 / 0 |
| Q409 | 40 x 4 | 96 -> 108 | 12 | 160 | 108 | 52 | 52 | 52 | 0 / 0 |
| Q410 | 48 x 4 | 108 -> 108 | 0 | 192 | 159 | 33 | 33 | 33 | 0 / 0 |

Q407 is the important adverse case. A transferred hypothesis produced one
counterexample, was rolled back, and the final automaton was still exact. It
saved 18 direct membership queries but cost 37 additional concrete oracle cells
after full equivalence-check accounting. This case is retained rather than
hidden; the aggregate concrete saving remains positive because the other
successful transfers outweigh it.

## What this establishes

Within the frozen meta-language of exact anonymous action-word transformation
equivalences of maximum length four, the system can autonomously create concepts
from completed worlds, add them to a persistent library, reuse them on later
fresh worlds, reject a bad transfer by counterexample, and reduce aggregate
query cost without losing exactness. The control stream did not create any such
concepts and obtained no savings.

This is bounded concept creation, not open-ended invention of new primitives,
grammar, or language. It also does not yet prove the same behavior under a new
generator family, noisy observations, much longer concepts, or integration with
the B8A symbolic learner. The canonical TCCT core was not modified in this
stage.
