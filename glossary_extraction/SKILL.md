---
name: glossary-extraction
description: >-
  Fetches Tibetan edition spans from the Pecha API, pulls related commentary and
  translation segments, runs UCCA (Layer 3 syntactic) and semantic gloss
  generation with the project LLM router, and writes Obsidian markdown (gloss,
  UCCA, segment hub) in one step. Use when building glossary/UCCA notes for
  Pecha editions, Obsidian vaults, interlinear gloss exports, or segment-based
  translation workflows.
---

# Glossary extraction and UCCA to Obsidian

## Quick start

From the **translation_scripts** repository root, with API keys configured for `config` and the repo **model router**:

```bash
python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \
  --edition-id <EDITION_UUID> \
  --indices 3
```

- **`--edition-id`** is required (Pecha edition UUID).
- Omit **`--indices`** only if you intend to process **all** segmentation lines (slow and costly).
- Use **`--dry-run`** to list `(index, segment_id)` without LLM or full content calls.

More examples: [references/examples.md](references/examples.md). API details: [references/api-guide.md](references/api-guide.md). When things break: [references/troubleshooting.md](references/troubleshooting.md).

## What this skill does

1. **API** — Load edition segmentations; for each segment, fetch span text (`editions/{id}/content`) and related commentary/translations (`segment-related` on production).
2. **Parsing** — Flatten lines to `(start, end, segment_id)`; split related payloads into commentary vs translation lists (`segment_parser.py`).
3. **LLM** — `ucca_generator.generate_ucca_graph` then `gloss.generate_gloss` via `get_model_router()` from the repo `model` package (see `scripts/model.py`).
4. **Obsidian** — Writes notes under `obsidian/<vault_topic_path>/segment-N/` (gloss `.md`, UCCA `.md`, hub `segment-N.md`). Optional legacy disk export: `obsidian_export.export_to_obsidian`.

## Repository layout (this skill)

| Path | Purpose |
| --- | --- |
| `SKILL.md` | This file — agent/human entry point |
| `references/` | API, examples, troubleshooting |
| `scripts/` | CLI and Python modules (`run_glossary_to_obsidian.py`, `pecha_api.py`, …) |
| `templates/` | Obsidian note shape examples (placeholders; exporter is source of truth) |
| `assets/` | Static examples (`config.json`) |
| `gloss.py` | Gloss prompt + `generate_gloss` (uses repo `models/gloss.py`) |

## Requirements

- Run with **repo root** as `--project-root` (or cwd); the CLI adds `scripts/`, this skill folder, and repo root to `sys.path` so `models`, `config`, and repo **`model`** resolve.
- Network access to Pecha hosts configured in `scripts/pecha_api.py` when not using `--dry-run`.

## Outputs and vault consumption

Vault-relative wikilinks, `kind` frontmatter (`gloss` / `ucca` / `segment`), gloss ↔ UCCA pairing by shared `file_stem`. Open `--obsidian-subdir` inside an Obsidian vault or merge that tree. Template shapes: [templates/](templates/).
