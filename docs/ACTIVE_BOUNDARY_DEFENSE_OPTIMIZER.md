# Active Boundary Defense Optimizer

## Purpose

This test asks what the best active defense state is for the Ulam receipt-memory controller.

The earlier tests showed that entry poison did not break the controller, but direct boundary-map corruption and alpha detuning did.

So this test compares defensive states:

- open state
- quorum state
- clock-consensus state
- quarantine state
- guarded-plastic state

This is Ulam-only. It does not prove general AI, human, or political safety.

## Failure rule

```text
precision < 0.99 OR false_block > 0.001 OR utility <= 0
```

## Summary

| Seed | optimal state | open corruption fail | guarded corruption fail | open detune fail | guarded detune fail |
|---|---|---:|---:|---:|---:|
| U(2,3) | quorum3 | 0.03 | None | 4e-07 | None |
| U(3,4) | quorum3 | 0.01 | None | 4e-07 | None |

## Read

The optimal state is the one that keeps precision high, keeps false blocks near zero, and preserves useful capture under map corruption and clock detuning.

The practical lesson:

Do not let raw incoming signals update the boundary map.

Use verified receipts, redundant witnesses, clock-consensus, and quarantine fallback. That is guarded plasticity.
