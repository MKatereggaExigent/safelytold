'use client';

import { DEV_AUTH, DEV_TENANT_ID, type Session } from '@safelytold/ui/api';

/* ------------------------------------------------------------------ */
/* OpenID Connect (authorization code + PKCE) against the safelytold      */
/* Keycloak realm. Runs entirely client-side; the safelytold-staff client */
/* is a public client, so no client secret is required.                */
/* ------------------------------------------------------------------ */

export const KEYCLOAK_URL = (
  process.env.NEXT_PUBLIC_KEYCLOAK_URL ?? 'http://localhost:8080'
).replace(/\/$/, '');
export const KEYCLOAK_REALM = 'safelytold';
export const CLIENT_ID = 'safelytold-staff';

const STATE_KEY = 'wpc:oidc:state';
const VERIFIER_KEY = 'wpc:oidc:verifier';
const REDIRECT_KEY = 'wpc:oidc:redirect';

export interface OidcTokens {
  access_token: string;
  refresh_token: string;
  id_token: string;
  expires_in: number;
  token_type: string;
}

function base64Url(bytes: Uint8Array): string {
  let bin = '';
  for (const b of bytes) bin += String.fromCharCode(b);
  return btoa(bin).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

function randomBase64Url(bytes: number): string {
  const buf = new Uint8Array(bytes);
  crypto.getRandomValues(buf);
  return base64Url(buf);
}

async function sha256Base64Url(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return base64Url(new Uint8Array(digest));
}

export function redirectUri(): string {
  return `${window.location.origin}/staff/auth/callback`;
}

export function decodeJwtPayload(token: string): Record<string, unknown> {
  const part = token.split('.')[1] ?? '';
  const pad = part.length % 4 === 0 ? '' : '='.repeat(4 - (part.length % 4));
  const b64 = part.replace(/-/g, '+').replace(/_/g, '/') + pad;
  const json = decodeURIComponent(escape(atob(b64)));
  return JSON.parse(json) as Record<string, unknown>;
}

/** Builds the staff sign-in URL and stashes PKCE verifier + state.
 * Public self-registration is intentionally unsupported. */
export async function beginLogin(next = '/staff'): Promise<string> {
  const verifier = randomBase64Url(64);
  const state = randomBase64Url(24);
  const challenge = await sha256Base64Url(verifier);
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  sessionStorage.setItem(STATE_KEY, state);
  sessionStorage.setItem(REDIRECT_KEY, redirectUri());
  sessionStorage.setItem('wpc:oidc:next', next);
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    redirect_uri: redirectUri(),
    response_type: 'code',
    scope: 'openid profile email',
    code_challenge: challenge,
    code_challenge_method: 'S256',
    state,
  });
  return `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth?${params.toString()}`;
}

async function tokenGrant(params: URLSearchParams): Promise<OidcTokens> {
  const res = await fetch(`${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`, {
    method: 'POST',
    headers: { 'content-type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Token exchange failed (${res.status}): ${text.slice(0, 200)}`);
  }
  return (await res.json()) as OidcTokens;
}

/** Exchanges the authorization code for tokens after the Keycloak round-trip. */
export async function completeLogin(code: string, state: string): Promise<Session> {
  const storedState = sessionStorage.getItem(STATE_KEY);
  if (!storedState || storedState !== state) throw new Error('Invalid OIDC state');
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  const redirect = sessionStorage.getItem(REDIRECT_KEY) ?? redirectUri();
  if (!verifier) throw new Error('Missing PKCE verifier');
  const tokens = await tokenGrant(
    new URLSearchParams({
      grant_type: 'authorization_code',
      client_id: CLIENT_ID,
      code,
      redirect_uri: redirect,
      code_verifier: verifier,
    }),
  );
  sessionStorage.removeItem(STATE_KEY);
  sessionStorage.removeItem(VERIFIER_KEY);
  sessionStorage.removeItem(REDIRECT_KEY);
  return sessionFromTokens(tokens);
}

export async function refreshTokens(refreshToken: string): Promise<OidcTokens> {
  return tokenGrant(
    new URLSearchParams({
      grant_type: 'refresh_token',
      client_id: CLIENT_ID,
      refresh_token: refreshToken,
    }),
  );
}

/** Builds an RP-initiated logout URL. An ID-token hint lets Keycloak end the
 * known session without showing a redundant confirmation screen. */
export function logoutUrl(idToken?: string): string {
  const redirect = `${window.location.origin}/staff/login`;
  const params = new URLSearchParams({
    client_id: CLIENT_ID,
    post_logout_redirect_uri: redirect,
  });
  if (idToken) params.set('id_token_hint', idToken);
  return `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout?${params.toString()}`;
}

/** Maps an access token's claims onto the safelytold Session used by all pages. */
export function sessionFromTokens(tokens: OidcTokens): Session {
  const claims = decodeJwtPayload(tokens.access_token);
  const realmRoles = (claims.realm_access as { roles?: string[] } | undefined)?.roles ?? [];
  const resourceAccess = (claims.resource_access as Record<string, { roles?: string[] }> | undefined) ?? {};
  const clientRoles = Object.values(resourceAccess).flatMap((v) => v?.roles ?? []);
  const roles = [...realmRoles, ...clientRoles].filter((r) => !r.startsWith('default-roles-'));
  const subject = (claims.sub as string) ?? 'anonymous';
  return {
    tenantId: (claims.tenant_id as string) ?? DEV_TENANT_ID,
    subject,
    roles: roles.length ? roles : ['case_manager'],
    purpose: (claims.purpose as string) ?? 'case-management',
    accessToken: tokens.access_token,
    refreshToken: tokens.refresh_token,
    idToken: tokens.id_token,
    expiresAt: Date.now() + tokens.expires_in * 1000,
    displayName: (claims.name as string) ?? (claims.preferred_username as string) ?? subject,
    email: claims.email as string,
  };
}

/** True when the stored session is usable: a dev-bypass session (only when
 * dev auth is enabled) or an unexpired access token. */
export function isSessionValid(session: Session): boolean {
  if (session.isDev) return DEV_AUTH;
  if (!session.accessToken) return false;
  if (session.expiresAt && session.expiresAt - Date.now() < 30_000) return false;
  return true;
}
