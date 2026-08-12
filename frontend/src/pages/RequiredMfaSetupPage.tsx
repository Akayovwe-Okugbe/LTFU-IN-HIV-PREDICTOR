import { ArrowRight, Copy, KeyRound } from 'lucide-react';
import { QRCodeSVG } from 'qrcode.react';
import { useEffect, useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Brand } from '../components/Brand';
import { useAuth } from '../context/AuthContext';
import { api } from '../lib/api';
import type { TotpSetupResponse } from '../lib/types';

export default function RequiredMfaSetupPage() {
  const location = useLocation(); const navigate = useNavigate();
  const { completeRequiredMfaSetup } = useAuth();
  const setupToken = (location.state as {setupToken?:string}|null)?.setupToken ?? '';
  const [setup,setSetup]=useState<TotpSetupResponse|null>(null); const [code,setCode]=useState('');
  const [error,setError]=useState(''); const [codes,setCodes]=useState<string[]>([]); const [busy,setBusy]=useState(false);

  useEffect(()=>{ if(!setupToken){setError('MFA setup session is missing. Please sign in again.');return;} api.beginRequiredMfaSetup(setupToken).then(setSetup).catch(e=>setError(e instanceof Error?e.message:'Unable to start MFA setup.'));},[setupToken]);
  async function confirm(e:FormEvent){e.preventDefault();setBusy(true);setError('');try{setCodes(await completeRequiredMfaSetup(setupToken,code));}catch(x){setError(x instanceof Error?x.message:'Unable to complete MFA setup.');}finally{setBusy(false);}}

  return <div className="auth-page"><div className="auth-art"><Brand/><div className="auth-art-copy"><span className="pill">Mandatory account protection</span><h2>MFA is required for privileged MEDISCOPE roles.</h2><p>Clinician and administrator accounts must complete authenticator enrolment before workspace access is issued.</p></div></div><div className="auth-panel"><div className="auth-form-wrap">
    {codes.length>0 ? <><h1>Save your recovery codes</h1><p>Each code can be used once. Store them securely; this set will not be displayed again.</p><div className="recovery-grid">{codes.map(c=><code key={c}>{c}</code>)}</div><button className="button primary wide" onClick={()=>navigate('/app',{replace:true})}>I have saved them<ArrowRight size={18}/></button></> : <><h1>Set up authenticator MFA</h1><p>Scan the QR code with Microsoft Authenticator or another TOTP-compatible app.</p>
      {setup && <div className="totp-enrolment"><div className="qr-card"><QRCodeSVG value={setup.provisioning_uri} size={190} marginSize={2}/></div><div><h3>Manual secret</h3><div className="secret-box"><code>{setup.manual_secret}</code><button type="button" className="icon-button" onClick={()=>navigator.clipboard.writeText(setup.manual_secret)}><Copy size={17}/></button></div></div></div>}
      <form className="auth-form" onSubmit={confirm}><label>Current six-digit code<input className="otp-input" required pattern="[0-9]{6}" maxLength={6} value={code} onChange={e=>setCode(e.target.value.replace(/\D/g,''))}/></label>{error&&<div className="form-error">{error}</div>}<button className="button primary wide" disabled={!setup||busy}><KeyRound size={18}/>{busy?'Securing account…':'Enable MFA & continue'}</button></form></>}
  </div></div></div>;
}
