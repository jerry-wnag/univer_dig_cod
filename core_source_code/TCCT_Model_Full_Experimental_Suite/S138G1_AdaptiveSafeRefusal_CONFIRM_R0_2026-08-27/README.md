# S138-G1 CONFIRM R0 — Materialization Failure

Status: **NO MODEL RUN / INVALID CHALLENGE MATERIALIZATION**

The protocol and learner sources were frozen before task generation. Task
materialization then failed because the builder excluded all neutral training
shapes previously used by S138-F and S138-G. The finite area-5-to-8 catalog
contains only 16 shapes symmetric about both axes: S138-F had used 11 and
S138-G had used the remaining 5, leaving zero candidates although each fresh
task required three.

This is a benchmark-construction capacity error, not a TCCT result. No task was
generated, no Oracle query was issued, and no model score is claimed. The
frozen R0 protocol and source hashes are retained unchanged.

R1 must be frozen separately. It may reuse neutral training geometry because
those examples have identical outputs under the three target structural
hypotheses and therefore carry no hidden-family information. Fresh test witness
shapes, assignments, colors, placements, and outputs remain required.
