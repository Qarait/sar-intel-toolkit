# Aerial Fine-Tune Report Gate Design

## Purpose

The current public detector baseline remains a general pretrained model with low aerial-person recall on VisDrone. This slice does not claim to solve that model-performance problem by itself. It builds the reporting gate that prevents the project from claiming a fine-tuned detector is better until the evidence is comparable, reproducible, and threshold-safe.

## Design

Add a small report builder around the existing `compare_visdrone_runs.py` gate. It consumes a baseline sweep JSON, a candidate sweep JSON, and optional training metadata, then emits a machine-readable fine-tune report. The report states whether an improvement claim is allowed, which thresholds were compared, which validation manifest checksums were used, and why the candidate failed if it did not pass.

The report deliberately reuses the existing comparison criteria: same validation manifest, matching fixed thresholds, minimum recall delta, minimum precision ratio, and average-precision improvement. This avoids building a second source of truth for detector improvement.

## Scope

This slice adds evidence discipline, not trained weights. Training still requires external aerial-person data and compute. The script should make failed candidates obvious and should exit non-zero by default when the gate fails, so it can be used in CI or release scripts later.

## Validation

Tests cover a passing candidate, a failed precision gate, and CLI behavior that writes a report while returning non-zero for a failed candidate. Documentation explains how to use the report after running the baseline and fine-tuned detector sweeps on the same pinned manifest.