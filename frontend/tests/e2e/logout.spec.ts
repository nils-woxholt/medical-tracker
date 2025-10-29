/**
 * E2E test for logout flow (T051).
 * Flow:
 *  - Visit access screen, perform login (or registration if user absent).
 *  - Verify dashboard identity element visible.
 *  - Click logout button.
 *  - Assert redirected to /access and identity element no longer present.
 */
/**
 * E2E test for logout flow (T051).
 * Flow:
 *  - Visit access screen, perform login (or registration if user absent).
 *  - Verify dashboard identity element visible.
 *  - Click logout button.
 *  - Assert redirected to /access and identity element no longer present.
 */
import { test, expect } from '@playwright/test';

test.setTimeout(60000);

/**
 * Deterministic logout E2E (T051)
 * Strategy: Always perform registration via auth toggle with a unique email, then verify dashboard identity and logout.
 * This avoids branching logic & stale selector mismatches.
 */
test('logout flow redirects to access screen and clears identity', async ({ page, context }) => {
  // Network & console instrumentation
  const netEvents: any[] = [];
  page.on('request', req => {
    if (req.url().includes('/auth/')) {
      netEvents.push({ type: 'request', method: req.method(), url: req.url() });
      // eslint-disable-next-line no-console
      console.log('net.request', { method: req.method(), url: req.url() });
    }
  });
  page.on('response', async res => {
    const url = res.url();
    if (url.includes('/auth/')) {
      const headers = await res.allHeaders();
      netEvents.push({ type: 'response', status: res.status(), url, setCookie: headers['set-cookie'] });
      // eslint-disable-next-line no-console
      console.log('net.response', { status: res.status(), url, setCookie: headers['set-cookie'] });
    }
  });
  page.on('console', msg => {
    if (['warn','error','log'].includes(msg.type())) {
      const txt = msg.text();
      if (/register\.|login\.|session/.test(txt)) {
        // eslint-disable-next-line no-console
        console.log('console.event', { type: msg.type(), text: txt });
      }
    }
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const email = `logout_e2e_${Date.now()}@example.com`;
  const password = 'StrongerPass123!';
  // Perform registration via page.evaluate fetch hitting backend directly so Set-Cookie is captured by browser context.
  const directReg = await page.evaluate(async ({ email, password }) => {
    try {
      const r = await fetch('http://localhost:8000/auth/register', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      const text = await r.text();
      let parsed: any = null; try { parsed = JSON.parse(text); } catch {}
      return { status: r.status, body: text, cookie: document.cookie, parsed };
    } catch (e: any) {
      return { status: 0, error: e?.message };
    }
  }, { email, password });
  console.log('direct.registration.result', directReg);
  let registered = directReg.status === 201;
  // Navigate to access screen for visual identity check later
  await page.goto('/access');
  await expect(page.getByTestId('access-screen')).toBeVisible();
  if (!registered) {
    // Fallback to UI registration (should rarely happen)
    await page.getByTestId('auth-toggle-register').click();
    await page.getByTestId('reg-email').fill(email);
    await page.getByTestId('reg-password').fill(password);
    await page.getByTestId('reg-submit').click();
    await page.getByTestId('register-loading-overlay').waitFor({ state: 'detached', timeout: 10000 }).catch(() => {});
  }

  // Poll session endpoint for up to ~5s, capturing raw bodies each attempt for debug
  // If direct succeeded we'll skip polling until session is established; otherwise poll.
  if (registered) {
    console.log('direct.registration.used');
  }
  const registrationAttempts: any[] = [];
  if (!registered) {
    // Poll using absolute backend session endpoint to avoid rewrite layer.
    for (let i=0;i<10;i++) {
      const status = await page.evaluate(async () => {
        try {
          const r = await fetch('http://localhost:8000/auth/session', { credentials: 'include' });
          const text = await r.text();
          let parsed: any = null; try { parsed = JSON.parse(text); } catch {}
          if (!r.ok) return { ok: false, status: r.status, body: text };
          const auth = !!(parsed?.data?.authenticated || parsed?.authenticated);
          return { ok: true, auth, status: r.status, body: text };
        } catch { return { ok: false, status: 0 }; }
      });
      registrationAttempts.push(status);
      if (status.ok && status.auth) { registered = true; break; }
      await page.waitForTimeout(500);
    }
  }

  // If not registered assume conflict (email exists) and perform explicit login
  if (!registered) {
    // Perform direct backend login via page.evaluate
    const loginDirect = await page.evaluate(async ({ email, password }) => {
      try {
        const r = await fetch('http://localhost:8000/auth/login', {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });
        const text = await r.text();
        let parsed: any = null; try { parsed = JSON.parse(text); } catch {}
        return { status: r.status, body: text, parsed };
      } catch (e: any) {
        return { status: 0, error: e?.message };
      }
    }, { email, password });
    console.log('direct.login.result', loginDirect);
    // Poll session after login
    let loggedIn = false;
    const loginAttempts: any[] = [];
    for (let i=0;i<10;i++) {
      const status = await page.evaluate(async () => {
        try {
          const r = await fetch('http://localhost:8000/auth/session', { credentials: 'include' });
          const text = await r.text();
          let parsed: any = null; try { parsed = JSON.parse(text); } catch {}
          if (!r.ok) return { ok: false, status: r.status, body: text };
          const auth = !!(parsed?.data?.authenticated || parsed?.authenticated);
          return { ok: true, auth, status: r.status, body: text };
        } catch { return { ok: false, status: 0 }; }
      });
      loginAttempts.push(status);
      if (status.ok && status.auth) { loggedIn = true; break; }
      await page.waitForTimeout(500);
    }
    expect(loggedIn).toBeTruthy();
    console.log('login.session.attempts', loginAttempts);
  } else {
    // Successful registration often auto-switches; ensure we can proceed to dashboard
    // Attempt navigation explicitly.
    await page.goto('/dashboard');
  }

  // Ensure on dashboard
  await page.waitForURL('**/dashboard');
  await expect(page.getByTestId('identity')).toBeVisible({ timeout: 15000 });

  // Perform logout
  await page.getByTestId('logout').click();
  await page.waitForURL('**/access');
  // Identity should disappear
  await expect(page.getByTestId('identity')).toHaveCount(0);
  await context.tracing.stop({ path: 'test-results/logout-trace.zip' });
  console.log('registration.session.attempts', registrationAttempts);
  console.log('network.events', netEvents);
  // Dump current cookies from context for debugging
  const cookies = await context.cookies();
  console.log('context.cookies', cookies.filter(c => c.name.toLowerCase().includes('session')));
});
