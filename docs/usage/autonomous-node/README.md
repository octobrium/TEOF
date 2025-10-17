# Autonomous Node (retired helper)

The former `tools.autonomy.node_runner` and `scripts/run-autonomous-node.sh` wrapper
have been retired to tighten the automation surface. Existing artifacts under this
directory remain as historical receipts of the experiment.

For ongoing automation, prefer the guarded autonomy loop (`python -m tools.autonomy.auto_loop`)
or compose bespoke runs from the supported CLI (`teof status`, `teof scan`, `teof ideas evaluate`)
capturing receipts per workflow policy.
