# TCCT S129-C1 fresh blind confirmation R1

This package freezes the generator, seeds, dimensions, B8A source, decision
rules, and verifier before materializing any world. The learner cannot read the
sealed generator programs. No solver-based resampling or post-result DSL change
is allowed. Challenge-world outcomes are descriptive. No PDF is generated.

Run order:

1. builder `freeze`
2. builder `materialize`
3. `source/TCCT_S129C1_FreshBlindConfirmation.wl`
4. `source/TCCT_S129C1_IndependentVerifier.wl`
