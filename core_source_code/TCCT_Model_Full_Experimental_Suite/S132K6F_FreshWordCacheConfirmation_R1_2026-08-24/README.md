# S132-K6F Fresh Exact Word-Cache Confirmation

## Outcome

`VERIFIED_FRESH_EXACT_WORD_CACHE_CONFIRMATION_GATE_PASS`

K6F is the frozen fresh-world confirmation of the K6E exact action-word
trace cache. The TCCT rewrite, inference, concept-discovery, activation,
rollback, and exact-verification mechanisms were not changed. The only
optimization caches an already-determined trace result under the exact key
`(direct-evidence generation, start state, action word)`.

## Frozen protocol

- Source, world specifications, random seeds, comparison fields, and gates
  were frozen before any K6F world was materialized.
- 8 structured worlds, 8 action-rank-matched random controls, and 4 near-law
  counterexample challenges were evaluated.
- K6E, the unmodified K6B baseline, and K5A received the same world, query
  seed, and available concept library in one Wolfram process.
- Execution order used a three-way rotation to reduce order bias.
- No arbitrary percentage speed threshold was used. K6E had to be strictly
  faster in aggregate than both baselines while remaining exactly identical.

## Main results

| Metric | Result |
|---|---:|
| Worlds exact and triple-field identical | 20 / 20 |
| Unsafe committed inferences | 0 |
| Logical trace requests | 6,350,146 |
| Exact cache hits | 5,803,541 (91.3922%) |
| Physical trace evaluations | 546,605 |
| Logical trace-cell lookups | 11,881,713 |
| Physical trace-cell lookups | 1,208,489 |
| Trace-cell lookup reduction | 89.8290% |
| K6E aggregate runtime | 684.6175 s |
| K6B aggregate runtime | 698.9397 s |
| K5A aggregate runtime | 733.6525 s |
| K6E wall-time reduction vs K6B | 2.0491% |
| K6E wall-time reduction vs K5A | 6.6837% |
| Final structured concept library | 308 concepts |

The independent verifier reconstructed every learner report from the oracle
tables, checked the cache conservation equations, replayed the concept-library
trajectory, verified all 8 rank-matched controls, repeated discovery after
independent state relabeling on all 8 structured worlds, and confirmed that all
4 near-law targets were genuinely broken and represented.

## Interpretation boundary

This result confirms that the exact word cache is behavior-preserving and
gives a small but reproducible aggregate runtime benefit on this frozen fresh
profile. It does not prove asymptotically efficient concept retrieval, broad
large-library scaling, or open-ended language invention. Random controls had
zero cache hits, correctly showing that the mechanism does not manufacture
reuse when no reusable action-word structure exists.

No PDF was produced.

## Key files

- `protocol/S132K6F_pre_world_manifest.json`: pre-world frozen protocol
- `protocol/S132K6F_freeze_receipt.json`: freeze/materialization/finalization receipt
- `source/TCCT_S132K6F_FreshWordCacheConfirmation.wl`: native Wolfram runner
- `source/TCCT_S132K6F_IndependentVerifier.py`: independent replay verifier
- `results/S132K6F_result.json`: Wolfram result
- `verification/S132K6F_independent_verification.json`: independent audit
