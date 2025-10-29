# Data Model: User Authentication

**Feature**: specs/002-login-functionality-add/spec.md  
**Date**: 2025-10-19

## Entities

### User

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | primary key | Generated |
| email | text | unique (lowercased), not null | Normalized canonical |
| display_name | text | optional | <= 80 chars |
| password_hash | text | not null | bcrypt hash |
| failed_attempts | int | >=0 | Increment on failed login |
| lock_until | timestamptz | nullable | If now < lock_until user is locked |
| created_at | timestamptz | not null | Immutable |
| updated_at | timestamptz | not null | Auto-updated |
| last_login_at | timestamptz | nullable | Set on success |

### Session

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | primary key | Opaque reference |
| user_id | UUID | fk -> User.id | Indexed |
| created_at | timestamptz | not null | Set at creation |
| last_activity_at | timestamptz | not null | Updated per request |
| expires_at | timestamptz | not null | Idle timeout base (may extend) |
| revoked_at | timestamptz | nullable | Soft invalidation |
| demo | boolean | not null default false | Distinguish demo sessions |

### AuditEvent (conceptual; may reuse existing log infra)

| Field | Type | Constraints | Notes |
|-------|------|------------|-------|
| id | UUID | pk |  |
| type | text | enum(auth.login.success, auth.login.failure, auth.lockout.trigger, auth.register.success, auth.logout, auth.demo.start) |  |
| user_id | UUID | nullable | Null for failures without confirmed user |
| session_id | UUID | nullable |  |
| occurred_at | timestamptz | not null |  |
| meta | jsonb | - | attempt counts, ip hash |

## Relationships

- User 1..* Session
- User 1..* AuditEvent (nullable where user unknown)

## Validation & Business Rules

- Email format validated; trimmed & lowercased before uniqueness check.
- Password: length ≥8, at least one ASCII letter and one digit.
- On 5th consecutive failed attempt: set lock_until = now + 15 minutes; failed_attempts remains at threshold until unlock.
- On successful login: reset failed_attempts=0, lock_until NULL.
- Session idle expiry: if now - last_activity_at > 30 minutes revoke session.
- Demo sessions flagged demo=true; creation of persistent domain data (outside auth) must be blocked or no-op.

## State Transitions (User Lockout)

| Current | Event | Condition | Next | Action |
|---------|-------|-----------|------|--------|
| Active | FailedLogin | failed_attempts < 4 | Active | failed_attempts++ |
| Active | FailedLogin | failed_attempts == 4 | Locked | failed_attempts=5; lock_until=now+15m; emit lock event |
| Locked | FailedLogin | now < lock_until | Locked | No change |
| Locked | TimePasses | now >= lock_until | Active | failed_attempts=0; lock_until NULL |
| Locked | SuccessfulLogin | now >= lock_until | Active | failed_attempts=0; lock_until NULL |

## Open Questions

None (all resolved in research).
