# Research & Decisions (Phase 0)

**Feature**: SaaS Medical Tracker (Logs, Medication Master, Conditions & Doctors)  
**Branch**: 001-saas-medical-tracker  
**Date**: 2025-10-16

## Objectives

Resolve PARTIAL gates from initial Constitution Check and prepare for Phase 1 design (data model, contracts, quickstart).

## Open Questions & Clarifications

| ID | Question | Resolution | Status |
|----|----------|-----------|--------|
| Q1 | Exact list of initial API endpoints & verbs? | Enumerated below; to be encoded in openapi.yaml. | RESOLVED |
| Q2 | Auth mechanism for pilot (full OIDC now or later)? | Use simple JWT (HS256) issued by backend login stub; OIDC deferred. | RESOLVED |
| Q3 | Observability metric names & log fields? | Defined in Observability Plan section. | RESOLVED |
| Q4 | Security validation hotspots? | Duplicate name normalization, severity bounds, ownership filters, input length & email format. | RESOLVED |
| Q5 | Is SQLite acceptable for multi-user pilot concurrency? | Yes (low write contention expectation <5 concurrent writes/second); migration path documented. | RESOLVED |

No outstanding TBDs blocking Phase 1.

## Planned API Surface (Initial)

Base URL prefix: `/api/v1`

| Endpoint | Method | Purpose | Request Body | Response (200) | Notes |
|----------|--------|---------|--------------|----------------|-------|
| /auth/login | POST | Obtain JWT | { email, password } | { accessToken, user } | Stub only; password plaintext check (dev) -> replace later |
| /medications | GET | List active medications | query: includeInactive? | [Medication] | Pagination optional (not needed early) |
| /medications | POST | Create medication master | MedicationCreate | Medication | Uniqueness (case-insensitive) enforced |
| /medications/{id} | PATCH | Update medication fields | MedicationUpdate | Medication | Cannot change ID; name uniqueness rechecked |
| /medications/{id}/deactivate | POST | Deactivate medication | n/a | Medication | Sets active=false |
| /logs/medications | GET | Recent medication logs | ?limit= | [MedicationLog] | Default limit 5 (landing) |
| /logs/medications | POST | Create medication log | MedicationLogCreate | MedicationLog | Validates medication active |
| /logs/symptoms | GET | Recent symptom logs | ?limit= | [SymptomLog] | Default limit 5 (landing) |
| /logs/symptoms | POST | Create symptom log | SymptomLogCreate | SymptomLog | Severity 1-5 enforced |
| /feel-vs-yesterday | GET | Compute daily feel delta | none | { status: better,worse,same,unavailable } | Based on avg severity diff |
| /conditions | GET | List conditions | none | [Condition] | |
| /conditions | POST | Create condition | ConditionCreate | Condition | |
| /doctors | GET | List doctors | none | [Doctor] | |
| /doctors | POST | Create doctor | DoctorCreate | Doctor | |
| /passport | GET | Condition passport | none | [{ condition, doctors[] }] | Aggregated view |

Future (deferred): /notes, /uploads, /analytics/*.

## Data Model Considerations (Preview)

- Use UUID primary keys (string) for entities (globally unique, simple client generation) OR autoincrement ints? Decision: Prefer UUID for logs & master for easier future sharding -> Document in data-model.md.
- Add composite unique index (userId, lower(name)) for Medication.
- Indexes: (userId, timestamp DESC) on log tables for recent queries.

## Observability Plan

### Logging (structured JSON)

Fields per request log: timestamp, level, message, request_id, trace_id, span_id, user_id (if authenticated), method, path_template, status_code, latency_ms, error (if any).  
Business event logs: medication_log_created, symptom_log_created with entity ids + derived feel_vs_yesterday status.

### Metrics (Prometheus format)

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| http_requests_total | counter | method, path_template, status_code | Request volume |
| http_request_latency_seconds | histogram | method, path_template | Latency distribution |
| medication_logs_written_total | counter |  | Count medication log creations |
| symptom_logs_written_total | counter |  | Count symptom log creations |
| feel_vs_yesterday_compute_seconds | histogram | status | Time to compute status |
| db_query_seconds | histogram | model, operation | ORM query timings (optional early) |

### Tracing

- Inject/propagate trace-id & span-id headers: `traceparent` (W3C). Each request wrapper creates span; service functions create child spans for DB operations.

### Frontend Vitals Collection

- Use `next/script` for web-vitals polyfill; send vitals (CLS, LCP, FID/INP) to backend endpoint `/telemetry/web-vitals` (deferred if not P1-critical; placeholder in code to avoid scope creep).

## Security & Validation Plan

- Ownership: Every query filters by authenticated userId.
- Authentication: Minimal JWT (HS256) with short expiry (15m) + refresh stub (deferred). Token signed with env secret.
- Input Validation: pydantic models enforce field types, severity bounds 1..5, name length limits (1..120), note length ≤ 1000 chars.
- Case-normalization for medication names: store original + lowercase column for uniqueness check.
- Prevent ID enumeration: 404 if resource not found or not owned (avoid leaking existence).
- Rate limiting: Not in P1 (low risk) – document as future; monitor abuse via request volume metrics.
- Sensitive data: No PHI beyond user-supplied condition names; still treat as sensitive (HTTPS required in deployment).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| SQLite write contention | Log latency | Low expected concurrency; migrate to Postgres once >5 concurrent writers observed (metric threshold) |
| Over-fetching logs | Performance | Default limit 5; enforce hard cap 50; add pagination later |
| Duplicate normalization bugs | Data inconsistency | Central name normalization utility + test cases |
| Missing metrics early | Debug difficulty | Metrics scaffold added before feature flag removal |
| Scope creep (notes/uploads) | Delay MVP | Explicitly deferred; track in backlog |

## Decisions Log

| ID | Decision | Rationale | Alternatives | Date |
|----|----------|-----------|-------------|------|
| D1 | Use SQLite + SQLModel initially | Fast iteration, schema similar to Postgres | Start Postgres now (higher setup complexity) | 2025-10-16 |
| D2 | UUID primary keys | Easier client generation, future distribution | Auto-increment ints (simpler) | 2025-10-16 |
| D3 | Contract-first manual openapi.yaml baseline | Ensures stability & review pre-impl | Rely solely on FastAPI auto-gen (harder to diff) | 2025-10-16 |
| D4 | Minimal JWT auth stub | Avoid early OIDC complexity | Implement OIDC now (slower start) | 2025-10-16 |
| D5 | No repository abstraction | Keep simplicity per constitution | Add repository pattern prematurely | 2025-10-16 |

## Next Steps (Phase 1 Preparation)

1. Author `contracts/openapi.yaml` reflecting endpoint table.
2. Generate TypeScript types (`openapi-typescript`) into `contracts/types/`.
3. Draft `data-model.md` with entity schemas & relationships + migration strategy.
4. Create `quickstart.md` (dev env setup: Node version, Python version, install & run both services, generate types script).
5. Update plan Constitution Check to PASS remaining gates.

All PARTIAL gates now have concrete actions (above). Proceed to Phase 1 design.
