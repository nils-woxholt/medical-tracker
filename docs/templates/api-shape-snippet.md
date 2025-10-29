# Lean Mode API Shape Snippet

Use this lightweight template to document a provisional endpoint in Lean Mode before full OpenAPI stabilization.

## Endpoint Summary

List the basic metadata for the endpoint.

- Method: GET | POST | PUT | PATCH | DELETE
- Path: /api/...
- Purpose: one sentence describing user value
- Owner: @github-handle or team
- Provisional: yes (remove once consumed by second feature or marked stable)

## Request Shape

```json
{
  "exampleField": "string", // required, description
  "optionalFlag": true,      // optional, description
  "items": [
    { "id": "uuid", "value": 123 }
  ]
}
```

Notes:

- Validation: pydantic model `ExampleCreate` (link to code)
- Auth: requires user session (JWT) | public

## Response Shape (200 OK)

```json
{
  "id": "uuid",
  "status": "active", // enum: active|inactive
  "createdAt": "2025-10-29T12:34:56Z"
}
```

## Error Shapes (Non-200)

| Status | Shape | Notes |
| ------ | ----- | ----- |
| 400    | `{ "error": "validation_failed", "details": ["field ..."] }` | pydantic validation |
| 401    | `{ "error": "unauthorized" }` | missing/invalid auth |
| 404    | `{ "error": "not_found" }` | resource absent |

## Open Questions / TODOs

- List any pending clarifications here

---
Checklist:

- [ ] Request & response examples committed
- [ ] Linked pydantic & TS interfaces exist
- [ ] Marked provisional
- [ ] Added basic test (unit/component/e2e smoke)

Remove this snippet once endpoint enters Strict Mode & full OpenAPI diff process.
