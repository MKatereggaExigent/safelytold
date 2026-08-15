import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';

const GATEWAY_URL = process.env.GATEWAY_INTERNAL_URL ?? 'http://api-gateway:9085';
const DEFAULT_TENANT_ID = process.env.NEXT_PUBLIC_DEV_TENANT_ID ?? '00000000-0000-0000-0000-000000000001';

/** Bounded, safe grounding text. The gateway answers from this text only -
 * it never offers legal advice beyond what the platform guarantees. */
const RIGHTS_CONTEXT = `SafelyTold privacy-preserving integrity reporting and case-management platform - reporter rights and process.
- You can report anonymously, confidentially, or with your identity on record. In anonymous mode no one - including the platform team - can see who you are unless you choose to reveal yourself.
- The platform prohibits retaliation against anyone who reports in good faith.
- Your report is handled by a trained team. The status of a report: received, under review, investigation, outcome. You are entitled to status updates.
- Evidence you provide is kept secure and its integrity is protected. Do not provide evidence that would identify you unless you choose the confidential or identified mode.
- You are never required to share personal details to make a report.
- The process is human-led; automated tools may assist drafting and summarising but never decide outcomes.
- If you are in immediate danger, contact emergency services first.
- This platform does not give legal advice. For binding legal advice, consult a lawyer or relevant authority in your jurisdiction.`;

export async function POST(request: NextRequest) {
  let body: { jurisdiction?: string; issue?: string; mode?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const issue = (body.issue ?? '').trim();
  if (issue.length < 30) {
    return NextResponse.json(
      { error: 'Please describe your question with more detail (at least 30 characters).' },
      { status: 400 },
    );
  }

  const redacted_input = JSON.stringify({
    platform_context: RIGHTS_CONTEXT,
    jurisdiction: body.jurisdiction ?? 'ZA',
    reporting_mode: body.mode ?? 'anonymous',
    question: issue,
    instructions: 'Answer ONLY from the platform_context. Respond as a JSON object with exactly two keys: "answer" (a clear, neutral explanation) and "citations" (an array of {citation, excerpt} references drawn from the platform_context, empty if none). If the question is not covered by the platform_context, say so plainly and do not invent policy.',
  });

  try {
    const res = await fetch(`${GATEWAY_URL}/v1/gateway/ai/v1/ai/runs`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        'x-tenant-id': DEFAULT_TENANT_ID,
        'x-purpose': 'reporter-legal-assistance',
      },
      body: JSON.stringify({
        tenant_id: DEFAULT_TENANT_ID,
        capability: 'policy_retrieval',
        purpose: 'reporter-legal-assistance',
        redacted_input,
      }),
    });

    if (!res.ok) {
      return NextResponse.json({ error: 'The assistant is temporarily unavailable. Please try again shortly.' }, { status: 502 });
    }

    const data = (await res.json()) as { output?: string };
    const raw = data.output ?? '';
    let answer = raw;
    let citations: Array<{ citation: string; excerpt: string }> = [];

    const cleaned = raw.trim().replace(/^```[a-zA-Z]*\n?/, '').replace(/\n?```$/, '').trim();
    try {
      const parsed = JSON.parse(cleaned) as { answer?: string; citations?: Array<{ citation?: string; excerpt?: string }> };
      if (parsed && typeof parsed.answer === 'string') {
        answer = parsed.answer;
        citations = (parsed.citations ?? [])
          .filter((c) => c && typeof c.citation === 'string' && typeof c.excerpt === 'string')
          .map((c) => ({ citation: c.citation as string, excerpt: c.excerpt as string }))
          .slice(0, 5);
      }
    } catch {
      /* prose fallback - the answer text is used as-is */
    }

    return NextResponse.json({ answer, citations });
  } catch {
    return NextResponse.json({ error: 'The assistant is temporarily unavailable. Please try again shortly.' }, { status: 502 });
  }
}
