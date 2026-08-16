# Reproducibility and Integrity Guide

## Intended Use of This Release

This package is a historical research archive and external-review snapshot. It contains both compact Wolfram sources and executed notebooks. Some notebooks are large because they preserve outputs from long-running experiments.

For review, start with:

1. `README.md`;
2. `certificates/TCCT_S95_StrictBlindCertificate.json`;
3. `experiments/TCCT_S95_Precommit.json`;
4. `experiments/TCCT_S95_TestDefinitions.wl`;
5. `experiments/TCCT_S95_BuildRecord.json`;
6. `experiments/TCCT_S95_StrictBlind.wl`;
7. `experiments/TCCT_S95_StrictBlind.ipynb`;
8. `certificates/TCCT_S94H_R3_IndependentFullQueryConfirmation.json`.

## Environment

The original runs used Windows and Wolfram Language 15.x through JupyterLab. A compatible setup requires:

- Wolfram Engine or Mathematica 15.x;
- Python 3;
- JupyterLab;
- Wolfram Language for Jupyter.

The launchers under `experiments/` are historical provenance. Many contain local paths such as `E:\engine_wolf` or `E:\anaconda`. Review and update them before running on another machine.

## Artifact Paths

Historical source files may refer to frozen artifacts using absolute paths. Their public copies are provided under:

- `artifacts/frozen_models/`;
- `artifacts/development/`;
- `certificates/`;
- `checkpoints/S94H_R3/`;
- `checkpoints/S95/`.

A clean portable rerun should parameterize these paths. Editing paths is an execution-harness change; it must not change candidate values, test definitions, labels, thresholds, or model logic.

## S95 Integrity Chain

The S95 build record reports:

- precommit SHA-256: `9b2f2a71fd23607f2c523fddf1f57f8204d5696f81782bb16cd27915bc721e03`;
- test-definition SHA-256: `065b83626f841c822fa22356b67d33f9f36efc26f0d8b2cecc177d7d7c5dcc12`;
- locked S94H-R3 certificate SHA-256: `ee8bedbe7570025cd495d6ccf5c899173897a6c0b2521c2d45c4144ed4f4cc5e`;
- frozen candidate file SHA-256: `8cbf7184200c6a04072f9b375af3137534dc3764bff7a32bf57db4a320187e1e`;
- S95 worlds executed during build: `0`.

The final S95 certificate reports:

- result hash: `4b0479683f4bd201687aae3b02d892b69d0109570371d93853a1f004ebb4a875`;
- precommit and test-definition hashes matching the build record;
- 12 valid checkpoints;
- no training, search, re-export, core change, rule change, deduplication change, or undirected-freeze change.

Use `MANIFEST_SHA256.csv` to verify the distributed snapshot itself. The manifest excludes itself by design. `RELEASE_INTEGRITY.json` summarizes package counts and key certificate hashes.

## Recommended Independent Replication Procedure

1. Create a clean environment on a second machine.
2. Verify `MANIFEST_SHA256.csv` before execution.
3. Inspect the S95 precommit and test-definition files before opening the executed notebook.
4. Redirect only the artifact and checkpoint paths to the local release directory.
5. Run a zero-sample preflight that verifies candidate and protocol hashes.
6. Run the 12 scenarios without training, search, candidate re-export, or rule changes.
7. Export a new certificate and compare all aggregate metrics, per-axis metrics, and result hashes where deterministic serialization permits.
8. Record software versions, CPU, memory, wall-clock time, and any harness-only edits.

## Excluded Files

The release intentionally excludes:

- Wolfram license and password files;
- Jupyter server runtime files and access tokens;
- PID files;
- Python bytecode and caches;
- local connection files;
- stdout/stderr logs that only describe local server operation;
- the zero-byte S94 certificate;
- the bundled Jupyter vendor repository, which should be obtained from its upstream source.

## Known Reproduction Risk

This archive was built during rapid iterative research. Some historical notebooks depend on definitions created by earlier cells and local artifacts. The S95 source is self-contained relative to its listed frozen artifacts, but the entire S71-S95 history is not yet a single-command portable pipeline. Creating that compact reference implementation is a recommended next stage.
