'use client';

import { Suspense, useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useSession } from '@safelytold/ui/context';
import { completeLogin } from '../../../lib/auth';

function CallbackInner() {
  const params = useSearchParams();
  const router = useRouter();
  const { setSession } = useSession();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const finish = async () => {
      const oidcError = params.get('error');
      if (oidcError) {
        setError(params.get('error_description') ?? oidcError);
        return;
      }
      const code = params.get('code');
      const state = params.get('state');
      if (!code || !state) {
        setError('Missing authorization code or state.');
        return;
      }
      try {
        const session = await completeLogin(code, state);
        if (!active) return;
        setSession(session);
        const next = sessionStorage.getItem('wpc:oidc:next') ?? '/dashboard';
        sessionStorage.removeItem('wpc:oidc:next');
        router.replace(next);
      } catch (err) {
        if (active) setError(err instanceof Error ? err.message : 'Sign-in failed.');
      }
    };
    void finish();
    return () => {
      active = false;
    };
  }, [params, router, setSession]);

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <h1 className="auth-title">Staff sign-in</h1>
        {error ? (
          <p className="auth-error">
            {error}
            <br />
            <a className="btn btn-ghost btn-sm" href="/staff/login" style={{ marginTop: 14 }}>
              Back to sign in
            </a>
          </p>
        ) : (
          <p className="auth-subtitle">Completing sign-in…</p>
        )}
      </div>
    </div>
  );
}

export default function CallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="auth-screen">
          <div className="auth-card">
            <p className="auth-subtitle">Completing sign-in…</p>
          </div>
        </div>
      }
    >
      <CallbackInner />
    </Suspense>
  );
}
