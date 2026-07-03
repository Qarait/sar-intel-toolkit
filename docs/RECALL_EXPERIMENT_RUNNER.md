# Recall Experiment Runner

This is the professional glue for the aerial recall track. It assembles dataset provenance, a candidate sweep, and the fine-tune report gate into one experiment directory.

Current mode is precomputed-candidate: train/evaluate elsewhere, then pass the candidate sweep here. This keeps CI GPU-free while preserving the publish/no-publish gate.

```bash
python scripts/run_recall_experiment.py \
  --dataset-yaml /data/sar_intel_person_yolo/combined_person.yaml \
  --dataset-manifest /data/sar_intel_person_yolo/combined_manifest.json \
  --baseline-sweep output/visdrone_det_sweep.json \
  --candidate-sweep output/visdrone_det_finetuned_sweep.json \
  --output-dir output/recall_experiment \
  --experiment-name heridal-visdrone-yolo26n
```

Outputs:

```text
output/recall_experiment/
  training_metadata.json
  candidate_sweep.json
  finetune_report.json
  recall_experiment_summary.json
```

A `PASS` means `claim_allowed` is true under the fixed gate thresholds. A `FAIL` is still useful: it preserves the exact dataset and sweep provenance for the failed candidate.