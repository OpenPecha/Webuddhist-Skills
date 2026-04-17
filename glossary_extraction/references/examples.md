# Examples — glossary_extraction

## Minimal run (one segment index)

```bash
cd /path/to/translation_scripts
python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \
  --edition-id YOUR_EDITION_UUID \
  --indices 2
```

## Full flags (explicit paths and model)

```bash
python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \
  --edition-id YOUR_EDITION_UUID \
  --indices 0,1,2 \
  --project-root . \
  --obsidian-subdir obsidian \
  --vault-topic-path "2-authoritative-context/The Way of Boddhisattva" \
  --model gemini-2.5-flash \
  --stem-suffix -full
```

## Dry run (no LLM, minimal API)

Lists which segments would be processed:

```bash
python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \
  --edition-id YOUR_EDITION_UUID \
  --indices 3 \
  --dry-run
```

## Process every segmentation line

Omit `--indices`. **Warning:** many API and LLM calls; use only when intended.

```bash
python skill/glossary_extraction/scripts/run_glossary_to_obsidian.py \
  --edition-id YOUR_EDITION_UUID
```

## Output location

Notes are written under:

`{project_root}/{obsidian_subdir}/{vault_topic_path}/segment-{N}/`

Example with defaults: `obsidian/2-authoritative-context/The Way of Boddhisattva/segment-3/`.

## Programmatic gloss (not the Pecha CLI)

`gloss.generate_gloss` accepts arbitrary `source_text` plus optional `ucca_interpretation`, up to three commentary strings, and `sanskrit_text`. The packaged CLI does not expose a “raw text file” mode; build a small script that calls `generate_gloss` with your strings if you need that.
