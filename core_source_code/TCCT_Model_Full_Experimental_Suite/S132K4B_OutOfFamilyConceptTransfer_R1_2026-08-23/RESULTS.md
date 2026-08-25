# S132-K4B Results

## Outcome

`VERIFIED_FRESH_OUT_OF_FAMILY_BOUNDED_CONCEPT_TRANSFER_GATE_PASS`

The protocol and all source hashes were frozen before materializing the formal
worlds. The native Wolfram run passed, and the independent Python implementation
reconstructed every query trace, learner counter, concept-library update,
rank-matched control, near-law challenge, aggregate, and final gate.

The K3B learner, K4A discovery/library mechanism, and canonical TCCT core were
not modified. The library began empty and no K4A schema library was preloaded.

## Formal metrics

| Measure | Result |
|---|---:|
| Fresh structured worlds | 12/12 exact in both modes |
| Rank-matched random controls | 12/12 exact in both modes |
| Near-law challenges | 4/4 exact in both modes |
| Total exact final models | 56/56 |
| Unsafe committed inferences | 0 |
| Generator families with positive later-world MQ savings | 4/4 |
| Starting structured concept library | 0 |
| Final structured concept library | 337 |
| Final random-control concept library | 9 |
| Structured membership queries | 2164 -> 1855 |
| Structured membership-query savings | 309 (14.28%) |
| Structured logical interaction cost | 2176 -> 1870 |
| Structured logical-cost savings | 306 (14.06%) |
| Structured concrete oracle-cell cost | 4328 -> 4056 |
| Structured concrete-cost savings | 272 (6.28%) |
| Random-control membership-query savings | 2 |
| Random-control concrete-cost savings | -59 |
| Near-law membership-query savings | 8 |
| Near-law concrete-cost savings | -243 |
| State-relabel discovery invariance | 12/12 |
| Broken near-law target represented in learned library | 4/4 |
| Native Wolfram runtime | 1707.47 seconds (28.46 minutes) |

## Structured-world trajectory

| World | Family | States x actions | Library before -> after | New | Baseline MQ | Transfer MQ | MQ saved | Concrete saved | Counterexamples / rollbacks | Exact |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| O401 | Dihedral product | 21 x 4 | 0 -> 119 | 119 | 84 | 84 | 0 | 0 | 0 / 0 | yes |
| O402 | Overwrite/gate | 20 x 4 | 119 -> 225 | 106 | 80 | 68 | 12 | -16 | 2 / 2 | yes |
| O403 | Boolean affine | 48 x 4 | 225 -> 234 | 9 | 192 | 136 | 56 | 56 | 0 / 0 | yes |
| O404 | Conjugated semigroup | 37 x 4 | 234 -> 236 | 2 | 148 | 106 | 42 | 42 | 0 / 0 | yes |
| O405 | Dihedral product | 36 x 4 | 236 -> 260 | 24 | 144 | 96 | 48 | 48 | 0 / 0 | yes |
| O406 | Overwrite/gate | 30 x 4 | 260 -> 285 | 25 | 120 | 105 | 15 | 15 | 0 / 0 | yes |
| O407 | Boolean affine | 64 x 4 | 285 -> 293 | 8 | 256 | 246 | 10 | 10 | 0 / 0 | yes |
| O408 | Conjugated semigroup | 53 x 4 | 293 -> 293 | 0 | 212 | 212 | 0 | 0 | 0 / 0 | yes |
| O409 | Dihedral product | 33 x 4 | 293 -> 298 | 5 | 132 | 87 | 45 | 45 | 0 / 0 | yes |
| O410 | Overwrite/gate | 48 x 4 | 298 -> 330 | 32 | 192 | 173 | 19 | 10 | 1 / 1 | yes |
| O411 | Boolean affine | 80 x 4 | 330 -> 336 | 6 | 320 | 258 | 62 | 62 | 0 / 0 | yes |
| O412 | Conjugated semigroup | 71 x 4 | 336 -> 337 | 1 | 284 | 284 | 0 | 0 | 0 / 0 | yes |

O402 is the clearest adverse structured case. It saved 12 direct membership
queries but triggered two counterexamples and therefore cost 16 additional
concrete oracle cells. O408 and O412 obtained no savings. These results are
retained; cross-family transfer is useful in aggregate, not universally.

## Controls and near-law behavior

The random controls accumulated nine accidental but exact short relations. They
saved only two membership queries and triggered two counterexamples, producing
a net concrete cost of 59 cells. Thus the system did not gain useful efficiency
from random structure.

The four deliberately near-law targets had 1, 2, 1, and 1 mismatch states. All
four target schemas existed in the learned structured library. The final models
remained exact and unsafe commits remained zero, but six counterexamples and
rollbacks made the challenge stream 243 concrete cells more expensive. This is
safe behavior, not efficient behavior.

An independently generated second state relabeling preserved the discovered
schema set in all twelve structured worlds. The learned concepts therefore do
not depend on arbitrary state IDs in this test.

## Interpretation and boundary

This run supports a stronger claim than K4A: within the fixed anonymous
action-word equivalence meta-language, concepts formed from an empty library can
transfer across four generator families with different state constructions and
dynamics while preserving exactness and reducing aggregate query cost.

It does not establish open-ended primitive or grammar invention. World size was
provided to the learner, observation noise was absent, the maximum word length
remained four, and this was not an end-to-end Transformer perception test.

The principal newly exposed limitation is scaling. The structured library grew
to 337 schemas, all of which were concretely instantiated and repeatedly audited.
The formal native run took 28.46 minutes. This is about 15.6 times K4A's native
runtime for a workload only 1.4 times larger in world count, although the world
families and relation densities also differ. The next mechanism problem is
therefore exact, safe concept indexing and demand-driven activation—not adding
more hand-written concept templates.
