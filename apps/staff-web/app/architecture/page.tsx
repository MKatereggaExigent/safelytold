'use client';

import {useEffect,useState} from 'react';
import {Alert,Badge,PageHeader,Panel} from '@safelytold/ui/components';
import {useSession} from '@safelytold/ui/context';
import {getPlatformArchitecture,type PlatformArchitecture} from '../../lib/admin';

export default function PlatformArchitecturePage(){
 const {session}=useSession();const [data,setData]=useState<PlatformArchitecture|null>(null);const [error,setError]=useState('');const allowed=session.roles.includes('platform_super_admin');
 useEffect(()=>{if(!allowed)return;getPlatformArchitecture(session).then(setData).catch(e=>setError(e instanceof Error?e.message:'Architecture access failed'))},[allowed,session.accessToken]);
 return <main className="shell"><PageHeader eyebrow="Restricted platform assurance" title="Platform architecture" subtitle="Available only to verified and allowlisted platform super-administrators."/>{!allowed&&<Alert tone="danger" title="Access denied">Your verified Keycloak identity does not hold the platform_super_admin role.</Alert>}{error&&<Alert tone="danger" title="Access denied">{error}</Alert>}{allowed&&!data&&!error&&<p className="muted">Loading protected architecture…</p>}{data&&<><Panel title={data.title}><p>{data.summary}</p></Panel><div className="stack">{data.lifecycle.map((item,index)=><Panel key={item.stage} title={`${index+1}. ${item.stage}`}><div className="cluster">{item.capabilities.map(capability=><Badge key={capability}>{capability}</Badge>)}</div></Panel>)}</div></>}</main>
}
