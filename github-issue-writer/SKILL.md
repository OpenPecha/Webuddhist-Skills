---
name: issue-card-writer
description: Generate structured GitHub issue cards for the WeBuddhist team. Use this when a backend dev needs to document a new or changed endpoint, or when a frontend/app dev needs an integration card. Triggers on "create an issue card", "write a card for this endpoint", "document this API", or when endpoint details or an OpenAPI spec is provided. Works with OpenAPI specs, natural language, or inline endpoint details.
---

**Context:**
The WeBuddhist team (backend, frontend, app devs) uses GitHub issue cards to document API endpoints during integration. Cards must be consistent so any dev can scan them and know: what's the endpoint, what goes in, what comes out, and what can go wrong.

**Accepted Inputs:**
- OpenAPI/Swagger spec (YAML/JSON) → extract endpoints automatically
- Natural language → "we added a language filter to GET /plans/tags"
- Inline details → method, path, params, response pasted in chat
- Any combination of the above

**Instructions:**

1. **Parse the input.** Extract: HTTP method, path, query params, request body, response body, status codes, headers. If info is missing, mark as `[TBD]`.
2. **Pick the card type:**
   - **New endpoint** → full card
   - **Endpoint edit** → full card + "Current Behavior" / "Proposed Change" sections after Context
   - **Backend fix** → full card, focus Context on the bug, still include the related endpoint and response so devs know which API surface is affected
3. **Generate the card** using the template below. Do NOT output any introductory or conversational text. Output ONLY the formatted markdown so it can be directly copied into GitHub.

**Card Template:**

```
# <Short clear title>

## Context
<1-2 sentences: why this endpoint exists, or what's changing and why>

## Endpoint
`<METHOD> <path>`

## Headers
| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes | Bearer token |

## Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|

## Request Body
```json
{}
```

## Response
**200 OK**
```json
{}
```

## Status Codes
| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized |
| 404 | Not found |
| 422 | Validation error |

## Notes
- <Edge cases, gotchas, related issues>
```

Omit sections that don't apply (e.g., no Request Body for GET, no Query Params for POST with body only).

For **endpoint edits**, add after Context:
```
## Current Behavior
<What it does now>

## Proposed Change
<What's changing>
```

**Rules:**
- Realistic example values — Tibetan text for `bo` fields (`སྒོམ`), UUIDs for IDs, real names like "Morning Meditation"
- Multilingual fields as objects: `{ "en": "Meditation", "bo": "སྒོམ" }`
- OpenAPI schemas → concrete JSON examples, not raw schema
- Short scannable notes — bullets, not paragraphs
- `[TBD]` for unknowns, never invent behavior