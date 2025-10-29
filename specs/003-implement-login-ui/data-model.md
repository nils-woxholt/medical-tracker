# Data Model: Login UI & Conditional Access

**Feature Branch**: 003-implement-login-ui  
**Source Spec**: `specs/003-implement-login-ui/spec.md`  
**Phase**: 1 (Design & Contracts)

## Overview

This document translates the feature specification entities into concrete data representations and validation rules. It informs OpenAPI contract shapes and frontend TypeScript types.

## Entities

### User

Represents an account capable of authentication.

| Field | Type | Required | Constraints / Validation | Notes |
|-------|------|----------|---------------------------|-------|
| id | UUID (string) | Yes | Format UUID v4 | Primary key |
| email | string | Yes | Valid email format; max 254 chars | Unique (case-insensitive) |
| password_hash | string | Yes | Result of secure hash (e.g., bcrypt/PBKDF2) | Never exposed client side |
| display_name | string | No | Trimmed; length 1-64; no control chars | Fallback to masked email when absent |
| created_at | datetime (ISO8601) | Yes | Server generated | Immutable |
| updated_at | datetime (ISO8601) | Yes | Server updated | For audit |
| last_login_at | datetime (ISO8601) | No | Set on successful auth | Optional metric |

Relationships: User 1..* Sessions.

### Session

Represents an authenticated interaction context.

| Field | Type | Required | Constraints / Validation | Notes |
|-------|------|----------|---------------------------|-------|
| id | UUID (string) | Yes | UUID v4 | Primary key |
| user_id | UUID (string) | Yes | FK references User.id | Indexed |
| issued_at | datetime | Yes | Server time | |
| expires_at | datetime | Yes | > issued_at | TTL policy |
| revoked | boolean | Yes | Default false | True on logout / invalidation |
| ip_address | string | No | IPv4/IPv6 format | For security analytics |
| user_agent | string | No | Sanitized string | Length ≤512 |

Lifecycle: Created at login / registration; revoked via logout or expiry sweep.

### AccessScreenState (Client-side only)

Ephemeral UI state (not persisted server-side).

| Field | Type | Required | Constraints / Validation | Notes |
|-------|------|----------|---------------------------|-------|
| mode | enum('login','register') | Yes | Defaults 'login' | Toggle source |
| email | string | No | Valid email format if present | Preserved on errors |
| password | string | No | Min length 10 during validation | Never stored after submit |
| display_name | string | No | Length ≤64 | Optional |
| submitting | boolean | Yes | Reflects in-flight request | Prevent duplicates |
| error | string | No | User-friendly message | Generic for login failure |
| success_banner_shown | boolean | No | True post-first registration | Auto dismiss or manual |

### AuthEvent (Telemetry - derived)

For metrics/logging (not a persisted full entity, conceptual schema).

| Field | Type | Required | Constraints / Validation | Notes |
| action | enum('login','register','logout') | Yes | | Metric label |
| outcome | enum('success','failure') | Yes | | Counts per action/outcome |
| duration_ms | integer | Yes | >=0 | For latency histograms |
| user_id | UUID | No | Present on success | |
| timestamp | datetime | Yes | | |

## Derived / Computed Values

- Masked Email: `masked = local_part[0:3] + '...' + '@' + domain` (if local_part length ≥3 else `local_part + '...' + '@' + domain`). Used only for display when display_name absent.
- Auth State: Derived from presence/validity of HTTP-only cookie; frontend queries `/auth/me` or similar endpoint to fetch identity.

## Validation Rules Summary

- Registration: email unique; password strength (≥10 chars, ≥2 character classes); optional display_name sanitized.
- Login: generic error on failure; no enumeration of email existence.
- Logout: idempotent; multiple logout attempts for same session yield success without error.

## State Transitions

User: Creation → Active; (future: disabled, deleted not in current slice).  
Session: Issued → (Revoked | Expired).  
AccessScreenState: login ↔ register; submitting true → false (success/failure) → success_banner_shown (register only first success).

## Open Questions (Design)

None pending; all clarifications resolved (see spec Clarifications section).

## Alignment With Constitution

- Contract-first: Shapes here will be encoded in OpenAPI under feature contracts prior to backend changes.
- Observability: AuthEvent schema informs metrics additions (`auth_attempts_total`, `auth_action_duration_seconds`).
- Accessibility: AccessScreenState ensures progressive enhancement (not depending on token readability in JS).

## Decisions & Rationale

- HTTP-only cookie JWT: reduces XSS exposure and simplifies CSRF mitigation via SameSite.
- Not persisting AccessScreenState: prevents sensitive transient data retention.
- Separate Session entity: supports revocation tracking and potential multi-session management later.

## Alternatives Considered

- LocalStorage token storage (rejected: XSS risk).
- Combining User & Session ephemeral info (rejected: reduces auditability, complicates multi-device support).
- Persisting AccessScreenState (rejected: unnecessary data retention, privacy concern).

## Next Steps

1. Generate OpenAPI endpoints & schemas.
2. Implement metrics per AuthEvent schema.
3. Create quickstart with integration guidance.
