# Active Recursive Boundary Controller Test

## Purpose

This is the next test after nested boundary closure.

The previous test asked whether a boundary record from one window predicts the next window.

This test asks whether using that prior boundary record as a controller improves future crossing regulation.

It is still a toy-system audit. It does not prove consciousness.

## Controller setup

No-memory controller:

- no prior boundary record
- routes the same fraction of candidate crossings randomly

Receipt-memory controller:

- preserves the prior 50k-window boundary record
- uses that record to route/block high-risk phase regions in the next 50k-window candidate interval

## Summary

| Seed | verdict | capture mean | false-block mean | precision mean | enrichment mean | utility mean | phase-random utility mean |
|---|---|---:|---:|---:|---:|---:|---:|
| U(2,3) | active_recursive_boundary_control_supported | 0.143856 | 0.000000 | 1.000000 | 1.129348 | 55608.4 | -11961.9 |
| U(3,4) | active_recursive_boundary_control_supported | 0.132835 | 0.000000 | 1.000000 | 1.151026 | 43979.1 | -16109.2 |


## Read

A positive result means:

A preserved boundary record can be used to regulate future crossings better than a no-memory controller.

That is active recursive boundary regulation in a deterministic toy system.

It does not prove consciousness. The consciousness-adjacent claim remains smaller:

A system becomes more complex when records of prior crossings are preserved and used to decide future crossings.

## Honest boundary

This test is strong inside Ulam because the Ulam rule gives exact accepted/rejected labels.

The result does not automatically transfer to biology, neuroscience, AI agents, institutions, or cosmology.

To transfer it, those systems need explicit boundary events, explicit allowed/rejected labels, and real receipt records.
