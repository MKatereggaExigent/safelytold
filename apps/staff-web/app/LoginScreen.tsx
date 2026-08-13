'use client';

import { useState } from 'react';
import { Logo } from '@safelytold/ui/components';
import { beginLogin } from '../lib/auth';

export function LoginScreen() {
  const [busy, setBusy] = useState<'signin' | null>(null);

  const start = async () => {
    setBusy('signin');
    try {
      const url = await beginLogin();
      window.location.assign(url);
    } catch {
      setBusy(null);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="auth-brand">
          <Logo label="Integrity Workspace" />
        </div>
        <h1 className="auth-title">Sign in to the staff portal</h1>
        <p className="auth-subtitle">
          Authorised access only. Every sign-in is protected by multi-factor authentication
          (authenticator app) — you will be guided to set it up on your first login.
        </p>
        <div className="auth-actions">
          <button
            type="button"
            className="btn btn-primary btn-lg"
            disabled={busy !== null}
            onClick={start}
          >
            {busy === 'signin' ? 'Redirecting to sign in…' : 'Sign in'}
          </button>
        </div>
        <p className="auth-footnote">
          Staff accounts are issued by an authorised tenant administrator. Contact your organisation’s
          SafelyTold administrator if you require access.
        </p>
        <p className="auth-footnote">
          Multi-factor verification uses a QR code and a time-based one-time passcode.
        </p>
      </div>
    </div>
  );
}
