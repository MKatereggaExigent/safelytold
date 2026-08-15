'use client';

import { useEffect, useState } from 'react';
import { Alert, Badge, Button, PageHeader, Panel } from '@safelytold/ui/components';
import { getSalesCatalogue, type SalesCatalogue, type SalesPlan } from '@safelytold/ui/api';

const FALLBACK_CONTACT = { email: 'sales@datasqan.com', phone: '+27686159700' };

function money(value: number): string {
  return new Intl.NumberFormat('en-ZA', { style: 'currency', currency: 'ZAR', maximumFractionDigits: 0 }).format(value);
}

function organisationSize(plan: SalesPlan): string {
  if (plan.required_isolation === 'dedicated_data_plane') return 'Dedicated data plane';
  if (plan.required_isolation === 'customer_environment') return 'Customer environment';
  if (plan.employee_min && plan.employee_max) return `${plan.employee_min.toLocaleString()}–${plan.employee_max.toLocaleString()} people`;
  if (plan.employee_min) return `${plan.employee_min.toLocaleString()}+ people`;
  return 'Custom organisation size';
}

export default function PricingPage() {
  const [catalogue, setCatalogue] = useState<SalesCatalogue | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    getSalesCatalogue().then(setCatalogue).catch(() => setError(true));
  }, []);
  const contact = catalogue?.sales_contact ?? FALLBACK_CONTACT;

  return (
    <main className="shell">
      <PageHeader
        eyebrow="SafelyTold for organisations"
        title="Annual plans for trustworthy reporting and case management"
        subtitle="Reporting is always free for employees, suppliers, customers and members of the public. Subscribing organisations fund the service. Prices exclude VAT."
        actions={<a href={`mailto:${contact.email}?subject=SafelyTold%20sales%20enquiry`}><Button>Contact sales</Button></a>}
      />

      <Alert tone="info" title="Privacy is not a premium feature">
        Anonymous reporting, encryption, the secure anonymous mailbox, sealed evidence and fundamental privacy and fairness controls are included in every edition.
      </Alert>

      {error && <Alert tone="warn" title="Live plan catalogue unavailable">Contact sales for the current annual quotation.</Alert>}
      {!catalogue && !error && <p className="muted">Loading annual plans…</p>}

      <div className="grid">
        {catalogue?.plans.map((plan) => <PlanCard key={plan.code} plan={plan} email={contact.email} />)}
      </div>

      <div className="split">
        <Panel title="Optional managed services">
          <p>Telephone hotlines, trained human intake, multilingual operators, awareness campaigns and managed triage are quoted separately so customers pay only for the operations they need.</p>
        </Panel>
        <Panel title="Speak to sales">
          <p>Discuss employee numbers, countries, languages, isolation, SSO, private connectivity, retention and service levels.</p>
          <div className="row">
            <a href={`mailto:${contact.email}`}><Button>Email {contact.email}</Button></a>
            <a href={`tel:${contact.phone}`}><Button variant="secondary">Call {contact.phone}</Button></a>
          </div>
        </Panel>
      </div>
    </main>
  );
}

function PlanCard({ plan, email }: { plan: SalesPlan; email: string }) {
  const monthly = plan.monthly_max
    ? `${money(plan.monthly_equivalent)}–${money(plan.monthly_max)}+`
    : `${plan.price_from ? 'From ' : ''}${money(plan.monthly_equivalent)}`;
  return (
    <Panel title={plan.name} subtitle={organisationSize(plan)}>
      <Badge>Annual contract</Badge>
      <p><strong style={{ fontSize: '1.45rem' }}>{monthly}</strong><br /><span className="muted">monthly equivalent, excluding VAT</span></p>
      <p><strong>Annual:</strong> {plan.custom_annual || plan.annual_price === null ? 'Custom quotation' : `${plan.price_from ? 'From ' : ''}${money(plan.annual_price)}`}</p>
      <p><strong>Setup:</strong> {plan.price_from ? 'From ' : ''}{money(plan.setup_fee)}</p>
      {plan.enterprise_capabilities.length > 0 && (
        <details><summary>Enterprise capabilities</summary><ul>{plan.enterprise_capabilities.map((item) => <li key={item}>{item}</li>)}</ul></details>
      )}
      <a href={`mailto:${email}?subject=${encodeURIComponent(`${plan.name} enquiry`)}`}><Button variant="secondary">Request a proposal</Button></a>
    </Panel>
  );
}
