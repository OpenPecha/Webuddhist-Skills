# Troubleshooting — glossary_extraction

## `ModuleNotFoundError: models` or `config` or `model`

The CLI adds the repo root to `sys.path`, but your working directory and `--project-root` should be the **translation_scripts** repository root (where `models/`, `config/`, and the top-level `model` package live).

If you import `gloss` or `ucca_generator` from another cwd, set `PYTHONPATH` to the repo root or run from that root.

## `scripts/model.py` vs `glossary_extraction/model.py`

`run_glossary_to_obsidian.py` uses **`scripts/model.py`**, which does `from model import get_model_router` — that is the **repository** router, not a duplicate copy under the skill. The large `model.py` at `skill/glossary_extraction/model.py` is separate; the main CLI path does not load it.

## HTTP errors from Pecha

- Check VPN or network access to `base_url` and `production_url` in `pecha_api.py`.
- Confirm `edition_id` exists and segmentations return the indices you pass.
- Production `segment-related` may differ from staging; 4xx often means bad span or edition.

## Empty or malformed gloss JSON

- Try a smaller `--indices` set or another `--model` supported by your router.
- Very long combined context (source + commentaries + UCCA) can hit token limits; the gloss module sets a high `max_output_tokens` but the provider may still truncate.

## Obsidian wikilinks broken

- Use forward slashes in `--vault-topic-path`.
- Wikilink targets omit `.md`; do not rename stems after export without updating the hub note.

## `--dry-run` works but full run fails

Dry run only hits segmentations. Full run adds content fetch, `segment-related`, and LLM calls — isolate whether the failure is HTTP (Pecha) or model (keys, quota, model name).
