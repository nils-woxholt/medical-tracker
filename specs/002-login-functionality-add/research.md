# Research & Decisions: User Authentication

**Feature**: specs/002-login-functionality-add/spec.md  
**Date**: 2025-10-19  

## Decisions

### 1. Session Representation

- **Decision**: HTTP-only Secure SameSite=Lax cookie carrying opaque session id referencing server-side session record; JWT optional future.
- **Rationale**: Simplifies revocation (delete record), mitigates XSS token theft risk, aligns with minimal scaling needs.
- **Alternatives Considered**: (a) JWT access + refresh tokens (added rotation complexity not yet needed); (b) LocalStorage token (higher XSS risk); (c) In-memory only (would not survive reloads).

### 2. Password Hashing

- **Decision**: bcrypt via passlib with adaptive cost parameter.
- **Rationale**: Established and already present dependency; easy to tune cost.
- **Alternatives**: Argon2 (better resistance but extra dependency); PBKDF2 (slower adoption).

### 3. Demo User Strategy

- **Decision**: Ephemeral session tied to shared demo principal; no persistence of created user-owned domain data (writes either blocked or stored in transient in-memory structures not surfaced globally).
- **Rationale**: Prevents data clutter & leakage; simplifies cleanup.
- **Alternatives**: Persist demo artifacts with nightly purge (increases operational complexity); fully isolated per-session shadow records (higher implementation cost now).

### 4. Lockout Implementation

- **Decision**: Track failed_attempts and lock_until timestamp on User row; increment transactional update; reset on success.
- **Rationale**: Avoids extra table; simple query path.
- **Alternatives**: Separate FailedLoginAttempt table (more audit detail, not required MVP); in-memory counter (fails across multiple replicas).

### 5. Session Timeout Enforcement

- **Decision**: Rolling idle timeout of 30 minutes; middleware updates last_activity; on exceed, session invalidated.
- **Rationale**: Balances security and usability; matches spec.
- **Alternatives**: Absolute lifetime (predictable expiry but more interruptions); sliding + absolute cap hybrid (may add complexity prematurely).

### 6. Email Uniqueness Normalization

- **Decision**: Lowercase normalization and trim on registration; store canonical lowercase.
- **Rationale**: Prevent duplicate logical accounts; simplifies login matching.
- **Alternatives**: Preserve case (adds matching complexity); store both raw & canonical (unnecessary now).

### 7. CSRF Mitigation

- **Decision**: Use SameSite=Lax and anti-CSRF token (double-submit cookie) for state-changing auth forms (logout, login not strictly required but consistent pattern).
- **Rationale**: Defense-in-depth.
- **Alternatives**: Rely solely on SameSite (insufficient for some edge navigations); origin header checks only (less explicit).

### 8. Observability Signals

- **Decision**: Log events: auth.login.success, auth.login.failure, auth.register.success, auth.logout, auth.lockout.trigger, auth.demo.start with structured fields (user_id, ip_hash, latency_ms, attempt_count).
- **Rationale**: Enables security monitoring & performance measurement.
- **Alternatives**: Minimal logs (reduced forensic value); full tracing integration (possible later).

### 9. API Contract Style

- **Decision**: RESTful JSON endpoints under /auth/* returning consistent { data, error } pattern.
- **Rationale**: Simplicity; FastAPI auto docs integration; existing rest of backend pattern.
- **Alternatives**: GraphQL (overkill); RPC style (less conventional for web auth flows).

## Resolved Unknowns

All NEEDS CLARIFICATION items resolved; no outstanding gating unknowns.

## Follow-up / Future Considerations

- Add password reset & email verification feature as separate specs.
- Evaluate migrating to signed JWT + refresh token if horizontal scale sessions strain DB.
- Consider Argon2 hashing upgrade (cost/benefit analysis later).
- Add device/session management (multi-session view & revoke) in future security enhancement phase.
