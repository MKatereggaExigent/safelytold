'use client';

import { useEffect, useRef } from 'react';
import { usePathname } from 'next/navigation';
import { useSession } from '@safelytold/ui/context';
import { isSessionValid, refreshTokens, sessionFromTokens } from '../lib/auth';
import { StaffShell } from './StaffShell';
import { LoginScreen } from './LoginScreen';

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { session, setSession } = useSession();
  const refreshing = useRef(false);

  useEffect(() => {
    if (!session.accessToken || !session.refreshToken) return;
    const interval = window.setInterval(async () => {
      if (!session.expiresAt || session.expiresAt - Date.now() > 60_000) return;
      if (refreshing.current) return;
      refreshing.current = true;
      try {
        const tokens = await refreshTokens(session.refreshToken as string);
        setSession(sessionFromTokens(tokens));
      } catch {
        // Token refresh failed; session expires naturally and AuthGate
        // will fall back to the login screen on the next navigation.
      } finally {
        refreshing.current = false;
      }
    }, 30_000);
    return () => window.clearInterval(interval);
  }, [session, setSession]);

  const isAuthRoute = pathname === '/login' || pathname === '/auth/callback';
  if (isAuthRoute) return <>{children}</>;
  const authed = isSessionValid(session);
  if (!authed) return <LoginScreen />;
  return <StaffShell>{children}</StaffShell>;
}
