# Pecha API usage (glossary_extraction)

All URLs and paths below match `skill/glossary_extraction/scripts/pecha_api.py`. If hosts change, edit that file.

## Base URLs

| Name | Variable | Used for |
| --- | --- | --- |
| Staging / dev | `base_url` | Editions, content, segmentations, text lookups |
| Production | `production_url` | `segment-related` (related commentary / translations) |

## Endpoints the skill calls

### Segmentations

- **GET** `{base_url}/editions/{edition_id}/segmentations`
- **Purpose** — Discover root segmentation lines and `(span_start, span_end, segment_id)` ranges for the CLI loop.

### Edition content (primary Tibetan span)

- **GET** `{base_url}/editions/{edition_id}/content`
- **Query** — `span_start`, `span_end` (from segmentation row).
- **Purpose** — Primary `source_text` passed into UCCA and gloss.

### Related segments (commentary / translation)

- **GET** `{production_url}/instances/{edition_id}/segment-related`
- **Query** — `span_start`, `span_end`, `transform` (boolean as lowercase string). Optional: `segment_id` in other helpers.
- **Purpose** — Instances related to the span; parsed into commentary and translation lists for UCCA context.

## Other helpers in `pecha_api.py`

These exist for notebooks or other workflows; the main CLI may not call every function:

- `GET {base_url}/texts/{text_id}` — text metadata
- `GET {base_url}/editions/{edition_id}` — edition JSON
- `GET {base_url}/editions/{edition_id}/content` without span — full edition content resolution path

## Contracts

- Responses are JSON; failures should surface as HTTP errors (`raise_for_status`).
- Span coordinates must align with the segmentation API for consistent related-instance results.
