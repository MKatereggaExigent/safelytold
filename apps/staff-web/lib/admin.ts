import { apiFetch, type Session } from '@safelytold/ui/api';

/**
 * Superuser administration client.
 *
 * These calls are intentionally NOT tenant-scoped by the caller: the backend
 * endpoints are guarded by the `platform_super_admin` role (and, outside the
 * development bypass, by the `ADMIN_SUPERUSER_EMAILS` allowlist) and target
 * tenants by path parameter.
 */

export function isSuperuser(session: Session): boolean {
  return session.roles.includes('platform_super_admin') || session.isDev === true;
}

/** Session used for superuser calls: dev bypass injects the superadmin role. */
export function adminSession(session: Session): Session {
  if (!session.roles.includes('platform_super_admin')) {
    return { ...session, roles: [...session.roles, 'platform_super_admin'] };
  }
  return session;
}

/* ------------------------------------------------------------------ */
/* Tenancy                                                             */
/* ------------------------------------------------------------------ */

export interface TenantView {
  id: string;
  slug: string;
  display_name: string;
  tenancy_tier: string;
  home_region: string;
  status: string;
  created_at: string;
}

export function listTenants(session: Session): Promise<TenantView[]> {
  return apiFetch('tenancy', '/v1/admin/tenants', { session: adminSession(session) });
}

export function createTenant(
  body: { slug: string; display_name: string; home_region: string },
  session: Session,
): Promise<TenantView> {
  return apiFetch('tenancy', '/v1/admin/tenants', {
    method: 'POST',
    body,
    session: adminSession(session),
  });
}

export interface LegalEntityView {
  id: string;
  tenant_id: string;
  registered_name: string;
  country_code: string;
}

export function listLegalEntities(tenantId: string, session: Session): Promise<LegalEntityView[]> {
  return apiFetch('tenancy', `/v1/admin/tenants/${tenantId}/legal-entities`, { session: adminSession(session) });
}

export function createLegalEntity(
  tenantId: string,
  body: { registered_name: string; country_code: string },
  session: Session,
): Promise<LegalEntityView> {
  return apiFetch('tenancy', `/v1/admin/tenants/${tenantId}/legal-entities`, {
    method: 'POST',
    body,
    session: adminSession(session),
  });
}

export interface OrganisationalUnitView {
  id: string;
  tenant_id: string;
  parent_id: string | null;
  name: string;
  unit_type: string;
  routing_tags: string[];
}

export function listOrganisationalUnits(tenantId: string, session: Session): Promise<OrganisationalUnitView[]> {
  return apiFetch('tenancy', `/v1/admin/tenants/${tenantId}/organisational-units`, {
    session: adminSession(session),
  });
}

export function createOrganisationalUnit(
  tenantId: string,
  body: { name: string; unit_type?: string; routing_tags?: string[] },
  session: Session,
): Promise<OrganisationalUnitView> {
  return apiFetch('tenancy', `/v1/admin/tenants/${tenantId}/organisational-units`, {
    method: 'POST',
    body,
    session: adminSession(session),
  });
}

/* ------------------------------------------------------------------ */
/* Outbound email settings (notification service)                      */
/* ------------------------------------------------------------------ */

export interface EmailSettingsView {
  tenant_id: string;
  delivery_mode: 'tenant_smtp' | 'datasqan_relay';
  smtp_host: string | null;
  smtp_port: number;
  smtp_username: string | null;
  smtp_use_tls: boolean;
  from_address: string | null;
  default_locale: string;
  has_credentials: boolean;
  verification_status: string;
  verification_detail: string | null;
  last_test_sent_at: string | null;
}

export function getEmailSettings(tenantId: string, session: Session): Promise<EmailSettingsView> {
  return apiFetch('notification', `/v1/admin/email-settings/${tenantId}`, { session: adminSession(session) });
}

export function saveEmailSettings(
  tenantId: string,
  body: {
    delivery_mode: 'tenant_smtp' | 'datasqan_relay';
    smtp_host?: string | null;
    smtp_port?: number;
    smtp_username?: string | null;
    smtp_password?: string | null;
    smtp_use_tls?: boolean;
    from_address?: string | null;
    default_locale?: string;
  },
  session: Session,
): Promise<EmailSettingsView> {
  return apiFetch('notification', `/v1/admin/email-settings/${tenantId}`, {
    method: 'PUT',
    body,
    session: adminSession(session),
  });
}

export function testEmailSettings(
  tenantId: string,
  session: Session,
): Promise<EmailSettingsView> {
  return apiFetch('notification', `/v1/admin/email-settings/${tenantId}/test`, {
    method: 'POST',
    body: {},
    session: adminSession(session),
  });
}

/* ------------------------------------------------------------------ */
/* Per-tenant neutral template overrides                               */
/* ------------------------------------------------------------------ */

export interface TemplateOverrideView {
  id: string;
  tenant_id: string;
  template_code: string;
  locale: string;
  subject: string;
  body: string;
}

export function listTemplateOverrides(tenantId: string, session: Session): Promise<TemplateOverrideView[]> {
  return apiFetch('notification', `/v1/admin/templates/${tenantId}`, { session: adminSession(session) });
}

export function saveTemplateOverride(
  tenantId: string,
  templateCode: string,
  locale: string,
  body: { subject: string; body: string },
  session: Session,
): Promise<TemplateOverrideView> {
  return apiFetch('notification', `/v1/admin/templates/${tenantId}/${templateCode}/${locale}`, {
    method: 'PUT',
    body,
    session: adminSession(session),
  });
}

export function deleteTemplateOverride(
  tenantId: string,
  templateCode: string,
  locale: string,
  session: Session,
): Promise<void> {
  return apiFetch('notification', `/v1/admin/templates/${tenantId}/${templateCode}/${locale}`, {
    method: 'DELETE',
    session: adminSession(session),
  });
}
