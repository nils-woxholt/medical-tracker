# Phase 0 Research: Login UI & Conditional Access

**Branch**: `003-implement-login-ui`  
**Date**: 2025-10-25  
**Spec Reference**: `specs/003-implement-login-ui/spec.md`  
**Plan Reference**: `specs/003-implement-login-ui/plan.md`

## Objectives

Establish evidence-backed decisions for password strength, identity masking, error messaging, performance & accessibility budgets, and confirm API contract deltas before Phase 1 design. Identify any clarification needs (none currently) and log verification tasks.

## 1. Password Strength Policy

- **Chosen Rule**: Min length ≥10; ≥2 character classes (letters, digits, symbols).
- **Rationale**: NIST SP 800-63B discourages overly complex composition rules but length strongly correlates with entropy. Length 10 provides baseline (~65 bits with mixed classes) without excessive friction. Two classes ensures avoidance of trivial alphabet-only sequences.
- **Future Considerations**: Introduce breach password screening (e.g., k-Anonymity API) in later slice.
- **UI Guidance**: Plain language: "Use at least 10 characters and mix letters, numbers or symbols." Avoid jargon (entropy, hash).

## 2. Identity Masking Strategy

- **Mask Format**: Show first 3 chars of local part + ellipsis + domain (e.g., `joh...@example.com`). If local part shorter than 3, show all then ellipsis (`a...@x.com`).
- **Accessibility**: Provide full email via `aria-label` or `title` attribute for assistive tech & hover.
- **Truncation Handling**: CSS: `max-width` + `text-overflow: ellipsis` inside a flex container; maintain tooltip.
- **Risk Mitigation**: Prevent revealing full email to shoulder-surfers while still confirming identity.

## 3. Error Messaging (Enumeration Resistance)

- **Login Failure**: Always: "Check your details and try again." Avoid "email not found" or "password incorrect".
- **Registration Conflict**: Generic: "Account already exists or details conflict." Suggest password reset path (future slice) but not implemented now.
- **Network Failure**: "Connection issue. Your data is still here—try again." Ensures user knows inputs preserved.
- **Validation Feedback**: Field-specific (password length/complexity) allowed because user already controls the input; not a vector for enumeration.

## 4. Performance & Bundle Budget Alignment

- **Target Bundle Delta**: ≤25KB gzipped (Spec SC-005). Strategy: Shared form components, lazy import of registration tab if not first view, avoid large UI libraries beyond existing shadcn components.
- **Loading Strategy**: Guard protected routes server-side (Next.js middleware or layout auth check) to eliminate dashboard flash. Use skeleton or spinner only after guard decides.
- **Metrics**: Measure time from initial access screen render to dashboard mount (login) and registration submit to dashboard mount (registration). Add `performance.mark` wrappers for internal profiling in e2e tests.

## 5. Accessibility Considerations

- **Form Controls**: Each input labeled; error messages associated via `aria-describedby`.
- **Focus Management**: On toggle between Login/Register, focus first interactive field.
- **Hit Targets**: Buttons / toggles ≥44px height; ensure spacing in mobile layout.
- **Color Contrast**: Maintain ≥4.5:1 for text; verify via automated axe + manual spot check.
- **Logout Button**: Role=button with accessible name "Log out"; progress state announced via `aria-live` polite region.

## 6. API Contract Delta Verification

- **Endpoints Expected**: `/auth/login`, `/auth/register`, `/auth/logout`.
- **Actions**: Verify presence in existing OpenAPI (`contracts/openapi.yaml`). If absent:
  - Draft Pydantic schemas: `LoginRequest { email, password }`, `RegisterRequest { email, password, display_name? }`, `AuthResponse { access_token (JWT), token_type, user { id, display_name?, email_masked } }`.
  - Confirm backend returns masked or raw email; implement masking client-side if raw.
- **Token Handling**: Constitution preference for JWT implies `Authorization: Bearer` or HTTP-only cookie. Need to inspect current implementation (task logged) and avoid exposing raw JWT in accessible JS scope if using cookies.

## 7. Observability Enhancements

- Add counters/histograms:
  - `auth_attempts_total{action="login"|"register"}`
  - `auth_logout_total`
  - Latency histogram `auth_action_duration_seconds` labeled by action.
- Frontend: Wrap auth actions with structured log entries only on failure (severity=warning) to avoid noise.

## 8. Risks & Mitigations Update

- Combined screen confusion → Clear segmented toggle with ARIA selected states.
- Performance regression from added validation logic → Keep complexity client-side minimal; no heavy password strength zxcvbn library yet.

## 9. Clarifications Needed

None at this time. All assumptions acceptable for Phase 1 progression.

## 10. Verification Tasks (copy to tasks.md in Phase 2)

- Inspect `contracts/openapi.yaml` for auth endpoints; add deltas if missing.
- Confirm token transport (cookie vs bearer) and adjust client storage strategy.
- Implement metrics additions and update backend test expectations.

## Conclusion

Research supports existing spec decisions; no blockers. Proceed to Phase 1: Data Model & Contracts design with verification tasks incorporated.
