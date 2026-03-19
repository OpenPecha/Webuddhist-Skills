---
name: openspec-generator
version: 1.0.0
description: >
  Generate complete OpenAPI 3.0 specification YAML files from brief natural-language API requirements
  or from a requirements file. Use this skill whenever the user asks to create an API spec, OpenAPI spec,
  open spec, swagger spec, REST API definition, endpoint documentation, or CRUD spec for any resource.
  Also trigger when the user says things like "I need an API for...", "draft a spec for...",
  "create endpoints for...", "openspec for...", "API contract for...", or mentions building REST
  endpoints and wants documentation before coding. Even if the user just names a resource
  (e.g., "users", "products", "orders") and implies they want API definitions, use this skill.
  The output is always a downloadable .yaml file following OpenAPI 3.0 conventions.
author: Your Name
permissions:
  - filesystem:read
  - filesystem:write
triggers:
  - command: /openspec
  - pattern: "create openspec*"
  - pattern: "generate api spec*"
  - pattern: "draft spec for*"
  - pattern: "openapi for*"
---

# OpenSpec Generator

Generate production-ready OpenAPI 3.0 YAML specs from brief requirements. The user can either give a
short description in chat or provide a file path containing detailed requirements.

---

## Input Modes

This skill supports two input modes:

1. **Chat brief** — The user describes the resource or API requirement directly in the message.
   Example: `@Bot create an openspec for products`
2. **Requirements file** — The user provides a file path to a text file containing detailed API
   requirements. Example: `@Bot /openspec from ~/docs/order-api-requirements.txt`

If a file path is provided, read the file contents first, then proceed with the workflow below.

---

## Workflow

1. **Understand the requirement** — Read the user's brief or the contents of the requirements file.
   If the input is ambiguous or missing critical details, **ask clarifying questions before generating
   anything.** Good questions to ask include:
   - What fields/attributes does this resource need?
   - Are there any relationships with other resources (e.g., "a product belongs to a category")?
   - Any specific validations or constraints (e.g., email must be unique)?
   - Any custom status values or enums?
   - Should any endpoints be excluded from the standard CRUD set?
   - Any specific business rules (e.g., soft delete vs hard delete)?
   Keep questions concise and grouped — ask everything in one message, not spread across multiple.
   If the input is clear enough to proceed, skip to step 2.
2. **Parse the requirement** — Extract the resource name, attributes/fields, relationships, and any
   special business rules from the user's description or file.
3. **Reason through the design** — Think through the requirements and design a logical, RESTful API
   structure before writing any YAML. Consider edge cases, field validations, and how endpoints
   relate to each other.
4. **Infer the full data model** — Based on the resource name and context, infer sensible fields
   with appropriate data types. Always include `id`, `created_at`, and `updated_at` as baseline
   fields unless the user says otherwise.
5. **Generate full CRUD endpoints** — Produce all five standard REST operations for the resource.
6. **Validate** — Mentally verify the YAML is strictly valid (correct indentation, no duplicate keys,
   proper `$ref` paths, all required fields present).
7. **Write the YAML file** — Output a valid OpenAPI 3.0 spec as `openspec-{resource}.yaml`.
8. **Send the file** — Write to `~/.openclaw/workspace/openspec-{resource}.yaml` and send it as a
   downloadable attachment to the user. Never paste raw YAML as a chat message.
9. **Return a summary** — After sending the file, provide a brief summary in chat listing:
   - Endpoints generated (method + path)
   - Fields/attributes in the resource schema
   - Any assumptions made during inference
   - Ask the user if they want to add, remove, or modify anything.

---

## Endpoints to Generate (Full CRUD)

For a resource named `{resource}` (e.g., `users`), generate:

| Operation | Method | Path                    | Description              |
|-----------|--------|-------------------------|--------------------------|
| List      | GET    | `/{resources}`          | List all with pagination |
| Create    | POST   | `/{resources}`          | Create a new record      |
| Read      | GET    | `/{resources}/{id}`     | Get a single record      |
| Update    | PUT    | `/{resources}/{id}`     | Update a record          |
| Delete    | DELETE | `/{resources}/{id}`     | Delete a record          |

- Use **plural lowercase** resource names in paths (RESTful convention).
- Use path parameter `{id}` typed as `string` (format: uuid) unless the user specifies otherwise.

---

## Spec Structure Rules

### Header

```yaml
openapi: "3.0.3"
info:
  title: {Resource} API
  description: API specification for managing {resource} resources.
  version: "1.0.0"
servers:
  - url: https://api.example.com/v1
    description: Placeholder — replace with actual server URL
```

### Security

Apply OAuth 2.0 globally:

```yaml
security:
  - oauth2: []

components:
  securitySchemes:
    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            read: Read access
            write: Write access
```

### Standard Response Envelope

Every success response body must follow this envelope:

```yaml
type: object
properties:
  success:
    type: boolean
    example: true
  message:
    type: string
    example: "Resource fetched successfully"
  data:
    # The actual payload goes here (object or array)
```

For **list endpoints**, `data` is an array and include a `meta` object for pagination:

```yaml
meta:
  type: object
  properties:
    page:
      type: integer
      example: 1
    per_page:
      type: integer
      example: 20
    total:
      type: integer
      example: 100
    total_pages:
      type: integer
      example: 5
```

### Standard Error Responses

Include these error responses on every endpoint as applicable:

| Code | When to include              | Schema Reference              |
|------|------------------------------|-------------------------------|
| 400  | POST, PUT (validation)       | `$ref: '#/components/schemas/ErrorResponse'` |
| 401  | All endpoints                | `$ref: '#/components/schemas/ErrorResponse'` |
| 403  | All endpoints                | `$ref: '#/components/schemas/ErrorResponse'` |
| 404  | GET (single), PUT, DELETE    | `$ref: '#/components/schemas/ErrorResponse'` |
| 409  | POST, PUT (conflicts)        | `$ref: '#/components/schemas/ErrorResponse'` |
| 500  | All endpoints                | `$ref: '#/components/schemas/ErrorResponse'` |

Error response schema:

```yaml
ErrorResponse:
  type: object
  properties:
    success:
      type: boolean
      example: false
    message:
      type: string
      example: "Validation failed"
    errors:
      type: array
      items:
        type: object
        properties:
          field:
            type: string
            example: "email"
          message:
            type: string
            example: "Email is already taken"
```

### Query Parameters for List Endpoint

Always include these on the GET list endpoint:

- `page` (integer, default: 1)
- `per_page` (integer, default: 20)
- `sort_by` (string, e.g., `created_at`)
- `order` (string, enum: [asc, desc], default: desc)
- Add `search` (string) parameter if the resource has a name-like or text field.

### Example Values

Every schema property MUST include an `example` field with a realistic, meaningful value.
Examples should feel real, not like placeholders. For instance:
- A user's name: `"Aarav Sharma"` — not `"string"`
- An email: `"aarav.sharma@example.com"` — not `"user@test.com"`
- A price: `499.99` — not `0`

### Component Schemas

Define these reusable schemas under `components/schemas`:

1. **`{Resource}`** — Full resource object (used in GET responses).
2. **`{Resource}Input`** — Request body for POST (all required fields for creation).
3. **`{Resource}Update`** — Request body for PUT (same as Input but all fields optional).
4. **`ErrorResponse`** — Standard error envelope (defined above).
5. **`PaginationMeta`** — Reusable pagination metadata.

### Tags

Group all endpoints under a single tag named after the resource:

```yaml
tags:
  - name: {Resources}
    description: Operations related to {resource} management
```

---

## Field Inference Guidelines

When the user gives a brief like "create a spec for products," infer reasonable fields based on
common domain knowledge. Use these conventions:

- **String** fields: `name`, `title`, `description`, `email`, `phone`, `address`, `status`, `slug`
- **Number** fields: `price`, `quantity`, `amount`, `rating`, `age`, `weight`
- **Boolean** fields: `is_active`, `is_verified`, `is_published`
- **Date-time** fields: `created_at`, `updated_at`, `deleted_at`, `published_at`
- **UUID** fields: `id`, any `_id` foreign key reference
- **Enum** fields: `status` (e.g., active/inactive), `role` (e.g., admin/user)

If you are unsure about which fields to include, prefer generating a reasonable set and note to the
user that they can request modifications.

---

## Output

- File name: `openspec-{resource}.yaml` (resource in singular lowercase, e.g., `openspec-product.yaml`)
- The file must be **valid YAML** and **valid OpenAPI 3.0.3**
- **File delivery is mandatory.** Always write the YAML content to a file on disk using the following steps:
  1. Write the complete YAML content to a file at `~/.openclaw/workspace/openspec-{resource}.yaml`
  2. Send/share the file to the user as a **downloadable attachment** in the current channel (Discord, Telegram, etc.)
  3. Do NOT paste the full YAML content as a text message. The file must be delivered as an attachment.
- After sending the file, return a brief chat summary (see Workflow step 9).
- If the user requests changes, regenerate the full file, overwrite it, and send the updated file again.

---

## Important Notes

- **Ask before you assume.** If the brief is vague or missing key details (fields, relationships,
  constraints), ask clarifying questions first. Group all questions in a single message. Only infer
  and generate directly when the brief is clear enough to produce a useful spec.
- **Reason before you write.** Think through the API design logically before generating YAML —
  consider field types, required vs optional, relationships, and edge cases.
- **ALWAYS return a downloadable `.yaml` file.** Never dump raw YAML as a chat message. Write to disk first, then send as attachment.
- **Strictly valid YAML.** Double-check indentation, no duplicate keys, correct `$ref` paths, and
  all required OpenAPI fields present before writing the file.
- If the user provides specific fields, use those exactly. Only infer fields when the user does not specify them.
- If the user mentions relationships (e.g., "a product belongs to a category"), include the foreign
  key field (e.g., `category_id`) and note the relationship in the description.
- If a requirements file is provided, read the entire file before starting — do not skip or
  summarize sections.
- Keep descriptions concise and professional.
