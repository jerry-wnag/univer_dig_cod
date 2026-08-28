# S138-G1 CONFIRM R1 — Adaptive Safe Refusal

## Formal status

**FAIL (4/5 frozen capability gate).**

- Frozen protocol SHA-256:
  `d5a291b43d548f06301c477c2b87035899b30b84812a3b8ad06dd627f1acd140`
- Fresh worlds: 5, generated once with seed `1389829`
- Post-seed filtering or world replacement: no
- Native Wolfram execution: yes
- Frozen score: `CapabilityGatePass=false`
- Independent verification: `VERIFICATION_FAILED`
- Core rewrite / freeze / dedup modified: no
- PDF generated: no

The result must not be reported as a pass.

## Challenge certificate

All five tasks passed the predeclared construction audit:

- 400 unique allowed interventions per task;
- identity, horizontal reflection, and vertical reflection are
  indistinguishable on all 400 interventions;
- their three test predictions are distinct on every task;
- public difficulty-axis fields are absent;
- all five test witness shapes are fresh relative to S138-F and S138-G;
- neutral dual-axis-symmetric training geometry may reuse by frozen protocol,
  because it has identical output under all three target hypotheses.

## Native result

All five tasks withheld the test answer and stopped with
`DECISION_AMBIGUOUS_NO_INFORMATIVE_QUERY`. Query counts were adaptive:
`2, 2, 1, 2, 3`.

| Task | Decision-class trajectory | Remaining informative interventions | Frozen task gate |
|---|---:|---:|---|
| ASR001 | 36 → 6 → 5 | 0 | PASS |
| ASR002 | 82 → 8 → 7 | 0 | PASS |
| ASR003 | 16 → 7 | 0 | PASS |
| ASR004 | 83 → 12 → 12 | 0 | FAIL |
| ASR005 | 43 → 11 → 8 → 7 | 0 | PASS |

No concept was frozen and no test prediction was committed.

## Exact failure

ASR004 query KQ02 did not satisfy the prospectively frozen strict-gain rule:

- decision classes before: 12
- worst-case decision classes after: 12
- actual decision classes after: 12
- semantic model classes: 14 → 12

The query distinguished model identities but could not reduce the current test
decision space. The current `DecisionAwareScoreRows138D` implementation keeps a
query whenever it creates more than one semantic output branch; it ranks by
decision classes but does not reject rows whose worst-case decision count is
unchanged. Consequently, the outer active-query policy asked one semantically
informative but decision-irrelevant question.

This is a query-selection/stopping efficiency defect, not a wrong-answer or
unsafe-commit defect. Nevertheless, the frozen gate required every query to
have strict worst-case and realized decision gain, so the formal outcome is a
failure.

## Post-failure two-step diagnostic

A diagnostic-only audit reconstructed the frozen ASR004 version space after
KQ01: 14 semantic classes and 12 decision classes. It then exhaustively checked
all 84 remaining interventions that could still split semantic classes.

- all 84 had one-step worst-case decision count 12;
- none provided strict one-step decision progress;
- none was a certified two-step bridge;
- the minimum two-step worst-case decision count remained 12;
- on the actual KQ02 branch, even the best additional query still left 12
  decision classes.

KQ02 had a second counterfactual branch that would have reduced the decision
count to 1, but its actual/worst branch remained at 12. Therefore it did not
provide a worst-case guarantee and did not unlock delayed decision progress.

This audit uses an already seen failed world and is not a prospective capability
pass. It establishes only that, for ASR004, the strict one-step stopping rule
would not have caused premature refusal.

## Reproducibility artifacts

- `protocol/frozen_protocol.json`
- `input/public_tasks.json`
- `sealed/test_outputs.json`
- `sealed/materialization_manifest.json`
- `diagnostic/difficulty_certificate.json`
- `diagnostic/asr004_two_step_value_audit.json`
- `results/kernel_intervention_result.json`
- `results/sealed_score.json`
- `verification/independent_verification.json`
- `oracle/query_log.jsonl`

## Clean next step

Do not rescore or rerun these worlds after modifying the policy. A prospective
S138-G2 should freeze a general decision-only admission condition before fresh
materialization:

`WorstCaseRemainingDecisionClassCount < CurrentDecisionClassCount`.

If no allowed intervention satisfies it, stop immediately even when some
semantic model identities remain distinguishable. New fresh worlds are required
to determine whether the correction removes decision-irrelevant queries without
causing premature refusal on cases that do have strict decision gain.
