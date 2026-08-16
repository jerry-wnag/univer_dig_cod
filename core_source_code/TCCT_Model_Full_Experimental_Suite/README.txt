A central idea is the **Union-based state deduplication mechanism**: different histories may reuse the same computational state only when their future behavior is sufficiently equivalent. After refining this Union logic to avoid premature or destructive merging, the S113–S118 series progressively tested whether compact hidden state machines could be discovered from behavior alone.

## Progress after the Union refinement

- **S113** — Recovered a 24-state hidden machine prospectively and introduced query-efficient active identification.
- **S114** — Scaled the same policy to a 120-state system while reducing membership queries by about 69%.
- **S115** — Extended discovery to irreversible, non-bijective and many-to-one dynamics.
- **S116** — Removed predefined permutation/transformation semantics and recovered an arbitrary minimal finite-state machine using future residual behavior.
- **S117** — Verified that the model avoids premature Union even when two states remain indistinguishable for up to 20 future steps.
- **S118A** — Removed teacher-provided counterexamples; the learner discovered its own prediction failures and refined incorrect state merges.
- **S118B** — Removed the fixed probe bank and allowed the model to dynamically search for experiments that falsify its current Union decisions.
- **S118B-R2** — Added compositional experiment synthesis such as \(s\,m^k\), allowing the learner to actively construct multi-stage experiments and recover the exact minimal machine.

Later experiments further extended the same state-discovery direction:

- **S119A** — Discovered factorized state structure and generalized to unseen joint-state combinations.
- **S119B** — Recovered sparse interactions between factors while retaining strong structural compression.
- **S120A** — Recovered a hidden factor with no direct observation, using history to distinguish latent states with identical current observations.
- **S120V** -- exposed a failure of exact-support factor grouping under partial action orbits. S120V-R2 replaced exact support equality with overlap-connected support components, fixing all 3 development failures and achieving 12/12 exact recoveries on new prospective random worlds.
The current prototype is best described as a **deterministic, partially observable, active, factorized structured world-model research prototype**.

It is not presented as AGI. Current experiments are primarily finite, discrete and synthetic, and the next major directions include stochastic belief states, multiple hidden factors, multimodal grounding, continual learning and planning.
NOTE:In **TCCT_S95_Strict_Blind_Research_Release_2026-08-12**, the `experiments` folder, which contains the atomic files, was accidentally moved by me to the same directory level as `TCCT_S95_Strict_Blind_Research_Release_2026-08-12` due to an oversight.
