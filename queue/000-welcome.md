# Task: Tighten anchors.json policy
Goal: add a guard so new anchor events must append at end with `prev_content_hash`.
Coordinate: S6:L1
Systemic Targets: S3 Propagation, S4 Defense, S6 Truth
Layer Targets: L1 Principles
Sunset: remove if guard proves noisy or blocks legitimate reorders.
Fallback: manual review in doctor until receipts earned.
