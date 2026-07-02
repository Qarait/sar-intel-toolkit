# Aerial Dataset Intake Design

## Purpose

Move the recall fix from discussion toward execution by tracking external aerial-person datasets needed for fine-tuning. The script does not download or redistribute data. It audits local dataset roots and records whether each source is ready for converter work.

## Design

`scripts/audit_aerial_datasets.py` owns a small registry of SAR-relevant aerial-person datasets. Each entry states the dataset id, SAR relevance, required local paths, and claim status. The CLI accepts `--dataset-root id=path` values and writes `output/aerial_dataset_audit.json`.

## Claim Discipline

A dataset being present does not fix recall. It only unlocks converter and training work. The project should continue to say the public detector is the pre-fine-tune baseline until a trained candidate passes the fine-tune report gate.