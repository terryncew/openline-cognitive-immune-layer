# Cognitive Immune Commit Barrier Test

## Purpose

This test asks whether a system can widen intake while protecting the core.

In this toy Ulam setup:

- buffer = what the system can inspect
- commit = what is allowed to update/control the protected interior

This is Ulam-only. It does not prove claims about humans, politics, consciousness, black holes, or general AI safety.

## Compared states

- rigid_filter: narrow intake, narrow commit
- baseline_memory_controller: standard 10% direct route
- porous_direct: wide intake, direct wide commit
- cognitive_immune_layer: wide intake, strict quorum commit barrier
- max_buffer_cognitive_immune_layer: very wide intake, strict quorum commit barrier

## Stress model

- bin corruption: 1.5%
- alpha detuning: 6e-7
- combined corruption + detuning

## Commit failure rule

```text
precision < 0.99 OR false_block > 0.001 OR utility <= 0
```

## Summary

| Seed | optimal state | state | safe all stress | buffer capture | commit utility | commit capture | max false-block | min precision |
|---|---|---|---|---:|---:|---:|---:|---:|
| U(2,3) | max_buffer_cognitive_immune_layer | rigid_filter | False | 0.131564 | 1743.46 | 0.131564 | 0.130937 | 0.854056 |
| U(2,3) | max_buffer_cognitive_immune_layer | baseline_memory_controller | False | 0.257695 | 7534.75 | 0.257695 | 0.245326 | 0.869139 |
| U(2,3) | max_buffer_cognitive_immune_layer | porous_direct | False | 0.686624 | 37448.86 | 0.686624 | 0.604920 | 0.905335 |
| U(2,3) | max_buffer_cognitive_immune_layer | cognitive_immune_layer | True | 0.686624 | 22957.14 | 0.059369 | 0.000000 | 1.000000 |
| U(2,3) | max_buffer_cognitive_immune_layer | max_buffer_cognitive_immune_layer | True | 0.916816 | 22957.14 | 0.059369 | 0.000000 | 1.000000 |
| U(3,4) | max_buffer_cognitive_immune_layer | rigid_filter | False | 0.130698 | -5461.54 | 0.130698 | 0.129709 | 0.860232 |
| U(3,4) | max_buffer_cognitive_immune_layer | baseline_memory_controller | False | 0.248526 | -13049.43 | 0.248526 | 0.253983 | 0.859348 |
| U(3,4) | max_buffer_cognitive_immune_layer | porous_direct | False | 0.648770 | 16068.50 | 0.648770 | 0.527237 | 0.904177 |
| U(3,4) | max_buffer_cognitive_immune_layer | cognitive_immune_layer | True | 0.648770 | 27009.89 | 0.081573 | 0.000000 | 1.000000 |
| U(3,4) | max_buffer_cognitive_immune_layer | max_buffer_cognitive_immune_layer | True | 0.886229 | 27009.89 | 0.081573 | 0.000000 | 1.000000 |

## Read

A rigid filter protects the core by seeing less.

A porous direct system sees more but lets too much write directly to the core.

A cognitive immune layer separates intake from commit: wide buffer, strict write barrier.

The product claim is supported if the cognitive immune layer increases buffer capture while keeping commit precision high and false commits near zero.
