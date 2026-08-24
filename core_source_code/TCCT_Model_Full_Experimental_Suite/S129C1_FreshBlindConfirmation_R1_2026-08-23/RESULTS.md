# S129-C1 Fresh Blind Confirmation R1

## Confirmatory outcome

The frozen S129-B8A learner passed the preregistered local fresh-world gate.

- In-bound active exact programs: **5/5**
- Random reachable automata false exact freezes: **0/5**
- Near-law mutation detection: **5/5**
- State-ID relabeling controls: **5/5**
- Independent verification: **PASS**

The generator, seven world seeds and dimensions, B8A source, runner, verifier,
search boundary, and decision rules were SHA-256 frozen before world
materialization. No solver-based resampling was performed. The learner did not
read the sealed generator programs, and no DSL or per-world rule was added after
the outcomes were known.

This is a local hash-frozen confirmation, not an externally preregistered or
large-scale generalization result.

## Formal in-bound worlds

Each world contains one independent increment action per coordinate to guarantee
full reachability, plus one randomly generated composite action. The composite
program was sampled once from the frozen bottom-up grammar; the solver result was
not used to accept or reject a world.

| World | States | Actions | Active outcome | Active queries | Passive outcome | Passive queries | Compression reduction |
|---|---:|---:|---|---:|---|---:|---:|
| C01 | 20 | 3 | exact | 51 | exact | 60 | 21.67% |
| C02 | 30 | 3 | exact | 66 | exact | 90 | 29.33% |
| C03 | 60 | 4 | exact | 97 | **budget fallback** | 181 | 64.58% |
| C04 | 40 | 4 | exact | 87 | exact | 160 | 57.50% |
| C05 | 12 | 3 | exact | 36 | exact | 36 | **-30.56%** |

Every active exact program had zero mismatches over the complete transition
table. Active querying used 337 membership queries in total versus 527 for the
fixed-order passive runs, a 36.05% reduction. This aggregate must be interpreted
with care because passive C03 exhausted its budget instead of reaching an exact
program.

The exact-rate result and the compression result are not the same. Active exact
induction passed 5/5, but only 4/5 worlds were compressive under the frozen
description length that includes both the coordinate map and program. C05 is a
valid exact law but costs 30.56% more than its small raw transition table, so it
must be reported as `EXACT_BUT_NOT_COMPRESSIVE` in interpretation.

## Boundary challenges

The two challenge outcomes were descriptive by preregistration; failure could
not trigger a DSL change.

| World | Frozen-boundary challenge | Outcome | Queries | Compression reduction |
|---|---|---|---:|---:|
| X01 | generator AST cost above 7 | exact | 50 | 15.33% |
| X02 | composed predicate outside the frozen predicate grammar | exact | 82 | 42.82% |

Both learned programs were independently verified with zero transition
mismatches. This does **not** show that the bounded search enumerated cost-9 or
composed-predicate syntax. On these finite coordinate domains, it found shorter
programs with identical semantics. The claim is therefore semantic
equivalence/compression, not unrestricted syntax recovery.

## Negative controls and verification

All five random reachable automata generated successfully. The learner returned
`NO_SURVIVING_PROGRAM_FALLBACK` on all five after 24-39 queries and froze no
false exact program. The independent verifier also established:

- all public learner inputs excluded transition tables, generator programs,
  seeds, and generator parameters;
- sealed generator programs reproduce every oracle transition exactly;
- all logged oracle answers are correct and contain no duplicate queries;
- every claimed exact program has zero full-table mismatches;
- all protocol, source, input, oracle, and sealed-truth hashes match the freeze.

## What this establishes

Within the frozen S129-B8A language and search boundary, TCCT can use active
query, counterexample-driven rewrite, semantic deduplication, and exact freeze to
construct executable laws on new permuted finite worlds without loading prior
programs. The C03 active/passive split is direct evidence that its active query
policy can determine success under a fixed budget.

It does not yet establish autonomous concept invention. The primitive language
was still fixed, the suite contains only five formal worlds with 12-60 states,
and one exact world was not MDL-compressive.

## Next gate: frozen library learning

The next experiment may let the system propose reusable primitives from repeated
certified subprograms, but the library definition cost must be included in total
MDL. The proposed library must then be frozen before unseen worlds and compared
against an identical no-library baseline on exactness, false-exact rate, search
time, membership queries, and total description length. A primitive counts as an
invented concept only if it transfers to unseen compositions; a post-result or
single-world shortcut does not count.

No PDF was generated.
