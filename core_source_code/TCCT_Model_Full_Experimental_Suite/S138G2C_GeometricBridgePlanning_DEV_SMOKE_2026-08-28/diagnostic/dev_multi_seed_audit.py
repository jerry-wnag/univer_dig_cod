from __future__ import annotations

import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "source"))

from build_geometric_bridge_tasks import DISCRIMINATING_SHAPES, build_task  # noqa: E402
from geometry_world import apply_program, models, queries  # noqa: E402
from prove_geometric_bridge_difficulty import best_one, dcount, two_worst  # noqa: E402


def main() -> int:
    audited = 0
    for seed in range(1389000, 1389050):
        rng = random.Random(seed)
        roles = ["GEOMETRIC_TWO_STEP_BRIDGE"] * 3 + ["GEOMETRIC_IRREDUCIBLE_CONTROL"] * 2
        rng.shuffle(roles)
        for index, (role, shape) in enumerate(zip(roles, rng.sample(DISCRIMINATING_SHAPES, 5)), 1):
            task, sealed, _ = build_task(rng, f"D{seed}_{index}", role, shape)
            rows, query_rows = models(task), queries(task)
            hashes = [row["InputSHA256"] for row in query_rows]
            current = dcount(rows)
            best1 = best_one(rows, hashes)
            best2 = min([current] + [two_worst(rows, query, hashes) for query in hashes])
            training_exact = all(apply_program(task, model["Program"], "TRAIN") ==
                                 task["InitialTrain"][0]["Output"] for model in rows)
            if role == "GEOMETRIC_TWO_STEP_BRIDGE":
                valid = best1 == current and best2 == 1
            else:
                valid = best1 == current and best2 == current and \
                        sealed["PrivateGeneratorMetadata"]["UninstrumentedContextSlot"] is not None
            if not (valid and training_exact and current == 3):
                raise RuntimeError((seed, index, role, current, best1, best2, training_exact))
            audited += 1
    print({"DevelopmentWorldsAudited": audited, "SeedCount": 50,
           "AllDifficultyContractsPass": True, "FormalSeedTouched": False})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
