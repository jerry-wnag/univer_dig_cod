# Experiment Timeline: S71-S95

This document summarizes the major methodological transitions. It is not a substitute for the source notebooks and certificates.

## S71-S80: Topology Transfer and Propagation

- **S71** established the first clean blind topology-transfer checkpoint: a frozen candidate selected using SharedMerge validation achieved 32/32 on the held-out ParallelIn topology.
- **S72-S75** expanded topology batteries and localized failures to representation and decision layers while auditing that the core remained unchanged.
- **S75C-S75D** studied semantic feasibility and validated policy completion. These were development stages, not new blind evidence.
- **S76** tested NestedBraidedIn as a blind transfer milestone.
- **S77-S78** tested runtime scaling and propagation horizons. Exact behavior was recovered at sufficient dynamic horizons, including depth 127.
- **S79** exposed a private-diamond composition failure.
- **S79A-S79B** localized and repaired the outer canonicalization handling under explicit integrity checks.
- **S80** tested hierarchical diamond composition.

## S81-S87: Counterfactual Structure and Representation Capacity

- **S81CF** introduced paired structural-counterfactual audits.
- **S82** tested blind local mediator interventions.
- **S82A** audited the failure mechanism.
- **S82B-S82C** investigated query-role representation and capacity, then froze/recovered hash-locked candidates.
- **S83** produced a valid blind failure under query-switch/topology composition, revealing that the token lacked sufficient query-role information.
- **S84-S85** expanded intervention-query grids.
- **S86** produced a valid blind failure on an external six-branch family, scoring 44/288.
- **S86A-S86D** audited cross-arity conflicts and modulus collisions. The audits showed that larger finite moduli could separate observed local states, but modulus alone was not a permanent semantic solution.
- **S86E-S86F** froze a broader K=33 exact-role candidate and ran revealed-data regressions.
- **S87** was another valid blind failure on seven-branch mixed interventions, scoring 20/392.
- **S87A-S87C** showed that the underlying observations retained enough information while the frozen token policy failed to use it compositionally. A world-multiset decoder was developed on revealed data.
- **S87D** froze and hash-locked that decoder before S88.

## S88-S93: Frozen Decoder, Intervention Algebra, and Paired Contrast

- **S88**: frozen decoder passed the blind eight-branch test with 512/512 worlds.
- **S89**: passed blind stop-relocation counterfactual transfer with 512/512 worlds.
- **S90**: passed a blind intervention-algebra battery with 1296/1296 worlds, including identity, inverse, composition, and path-independence checks.
- **S91**: post-hoc locked benchmark and ablation study. The full frozen system scored 1296/1296; the legacy policy scored 128/1296. This was not a neural baseline and did not create new blind evidence.
- **S92**: valid blind failure on cardinality-matched relational contrasts: 40/80 worlds and 0/40 correct pairs. This excluded a simple cardinality shortcut and exposed a single-world readout limitation.
- **S92A**: post-failure audit.
- **S92B**: paired-contrast decoder development and freeze using revealed S92 data.
- **S93**: the frozen paired decoder passed a new blind grammar with 48/48 pairs and 96/96 oriented decisions.

## S94-S95: Full Query Scope and Strict Pre-registration

- **S94**: the initial mixed-context run did not produce a valid certificate. The zero-byte artifact is not distributed as evidence.
- **S94A**: showed that selecting a larger modulus alone was insufficient.
- **S94B-S94C**: role-aware readout development produced partial improvements but exposed weak holdout groups.
- **S94D**: localized the representation-loss stage.
- **S94E**: rejected a narrow relation-binding hypothesis.
- **S94F**: localized the useful information channel.
- **S94G**: full-query-scope development passed on 416 development pairs. It used revealed labels and is explicitly not blind evidence.
- **S94H**: an early confirmation attempt was invalid and is retained as such.
- **S94H-R3**: independent resumable confirmation passed 312/312 pairs across 624 worlds, with 1.0 worst-group accuracy and minimum margin 2.6671855964.
- **S95**: pre-registered strict blind evaluation passed 180/180 pairs across 360 worlds, with 1.0 worst-group accuracy and minimum margin 1.8515601232.

## Protocol Labels

- **Development:** labels may be used to select or construct a candidate. Development scores are not blind evidence.
- **Post-hoc audit:** performed after a result is revealed to identify a mechanism or failure source. It cannot retroactively convert a failure into a success.
- **Independent confirmation:** evaluates a frozen candidate on separately generated confirmation data, but may still share a broader development program.
- **Blind test:** the candidate is frozen before its held-out data are used.
- **Pre-registered strict blind test:** candidate, test definition, thresholds, prohibited changes, and expected sample counts are committed before test-world execution.

The final scientific interpretation should prioritize strict blind evidence, retain valid failures, and treat development results only as hypotheses or candidate-construction evidence.
