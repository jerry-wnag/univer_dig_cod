from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
R0_SOURCE = ROOT.parent / "S141D_FreshRepresentationRequired_CONFIRMATORY_R0_2026-08-29" / "source" / "construct_challenge.py"
spec = importlib.util.spec_from_file_location("s141d_r0_constructor", R0_SOURCE)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)
module.ROOT = ROOT


if __name__ == "__main__":
    raise SystemExit(module.main())
