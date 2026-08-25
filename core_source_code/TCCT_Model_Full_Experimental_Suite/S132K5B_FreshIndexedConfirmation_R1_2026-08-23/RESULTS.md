# S132-K5B Fresh Paired Exact Indexed Confirmation

Final conclusion: `VERIFIED_FRESH_EXACT_INDEXED_CONFIRMATION_GATE_PASS`

## Protocol

- The protocol and all 10 source files were hashed before world materialization.
- Formal corpus: 8 fresh structured worlds from 4 generator families, 8 action-image-rank-matched random controls, and 4 near-law challenge worlds.
- Every indexed/full-scan pair used the same world, query seed, available concept library, and frozen learner semantics.
- Execution order was alternated by row: odd rows indexed-first, even rows full-scan-first.
- The K3B learner, K4A concept discovery/library mechanism, K5A indexed mechanism, maximum word length 4, and TCCT core were not modified.
- No arbitrary percentage speed or savings threshold was used.

## Primary result

| Measure | Indexed | Full scan | Result |
|---|---:|---:|---:|
| Aggregate paired learner runtime | 583.9808575 s | 1397.0810006 s | 2.3923404x speedup |
| Closure item evaluations | 2,994,040 | 5,972,606 full-scan equivalent | 49.8705% reduction |
| Direct-audit state checks | 5,091,067 | 14,938,716 full-rescan equivalent | 65.9203% reduction |

All 20 paired worlds had exact equality on every original K3B output field, including query order, membership-query count, equivalence calls, counterexamples, rejected instances, rollback counts, inferred-transition count, and final exactness. All indexed, full-scan, and schema-disabled models were exact. Unsafe committed inference count was 0.

The aggregate speed result includes the unfavorable empty-library cases. On F501 the indexed run was slightly slower than full scan, and the millisecond-scale random controls were mixed. These rows were not excluded.

## Fresh concept-transfer result

- Structured membership queries: 2,028 baseline versus 1,776 indexed transfer, saving 252 (12.43%).
- Structured concrete oracle-cell cost: 4,056 baseline versus 3,911 indexed transfer, saving 145 (3.58%).
- Positive membership-query savings appeared in all 4 generator families on at least one later world.
- The final structured library contained 308 exact anonymous transformation schemas.
- Rank-matched random controls created no schemas and had aggregate concrete savings of 0.
- F502 individually had concrete savings of -98, so transfer was not beneficial on every world; this adverse row is retained. Aggregate structured savings remained positive without a post-hoc threshold.

## Safety and independent audit

- All 4 near-law challenges were exact under indexed transfer, full scan, and the schema-disabled baseline.
- Their planted relations were genuinely false, with mismatch counts 1, 2, 1, and 1, and all four corresponding concepts were present in the structured library.
- Random state relabeling preserved the discovered schema set in all 8 structured worlds.
- All 8 random controls matched the structured worlds' per-action image ranks.
- An independent Python implementation reconstructed all three learning traces, both evolving libraries, all aggregate counters, source/input hashes, and freeze/materialization order.

## What this establishes

K5B upgrades K5A's retrospective result to fresh paired evidence: exact event-indexed concept activation preserves the frozen learner's behavior while materially reducing activation work and native Wolfram runtime on newly generated worlds.

It does not prove open-ended concept/language invention, noise robustness, unknown world size, or end-to-end scalability. The remaining cost is still large when hundreds of exhaustive length-4 concepts are audited. The next optimization target should therefore be exact candidate generation and witness auditing, with the same full-equivalence verifier and fallback retained.
