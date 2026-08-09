'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { DEV_AUTH, DEV_SESSION } from '@safelytold/ui/api';
import { Logo } from '@safelytold/ui/components';
import { useSession } from '@safelytold/ui/context';
import { beginLogin } from '../lib/auth';

export function LoginScreen() {
  const router = useRouter();
  const { setSession } = useSession();
  const [busy, setBusy] = useState<'signin' | 'register' | 'dev' | null>(null);

  const start = async (register: boolean) => {
    setBusy(register ? 'register' : 'signin');
    try {
      const url = await beginLogin(register);
      window.location.assign(url);
    } catch {
      setBusy(null);
    }
  };

  const dev = () => {
    setBusy('dev');
    setSession(DEV_SESSION);
    router.replace('/staff');
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
            onClick={() => start(false)}
          >
            {busy === 'signin' ? 'Redirecting to sign in…' : 'Sign in'}
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-lg"
            disabled={busy !== null}
            onClick={() => start(true)}
          >
            {busy === 'register' ? 'Opening registration…' : 'Create an account'}
          </button>
        </div>
        <p className="auth-footnote">
          Multi-factor verification uses a QR code and a time-based one-time passcode.
        </p>
        {DEV_AUTH && (
          <div className="auth-dev">
            <button type="button" className="btn btn-ghost btn-sm" disabled={busy !== null} onClick={dev}>
              {busy === 'dev' ? 'Entering…' : 'Continue in development mode'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
