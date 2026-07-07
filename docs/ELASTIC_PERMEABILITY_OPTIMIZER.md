# Elastic Permeability Optimizer

## Purpose

This test asks the wobble-zone question directly:

> How open should the boundary be?

It varies route fraction and quorum threshold under clean and stressed conditions.

This is Ulam-only. It does not prove claims about human politics, black holes, consciousness, or general AI safety.

## Stress model

- bin corruption: 1.5%
- alpha detuning: 6e-7
- combined corruption + detuning

## Failure rule

```text
precision < 0.99 OR false_block > 0.001 OR utility <= 0
```

## Summary

| Seed | optimal route fraction | optimal quorum | safe all stress | mean utility | mean capture | max false-block | min precision |
|---|---:|---:|---|---:|---:|---:|---:|
| U(2,3) | 0.15 | 3-of-3 | True | 22957.14 | 0.059369 | 0.000000 | 1.000000 |
| U(3,4) | 0.2 | 3-of-3 | True | 27009.89 | 0.081573 | 0.000000 | 1.000000 |

## Read

A boundary that is too open captures more but starts false-blocking accepted future paths.

A boundary that is too strict preserves safety but loses too much useful capture.

The optimal state is the best safe point under stress: high utility, high precision, near-zero false blocks.

This is the executable version of the wobble-zone thesis:

> firm enough to cohere, flexible enough to adapt.

## Practical OpenLine translation

Do not make the boundary maximally porous.

Do not freeze it either.

Use verified quorum and tune permeability to the widest safe band.
