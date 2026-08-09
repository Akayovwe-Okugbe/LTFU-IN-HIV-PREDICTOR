import { ArrowRight, BrainCircuit, CheckCircle2, LockKeyhole, ShieldCheck, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Brand } from '../components/Brand';

export default function LandingPage() {
  return <div className="marketing-page">
    <header className="marketing-nav"><Brand /><nav><Link to="/about">About</Link><Link to="/contact">Contact</Link><Link className="button ghost small" to="/login">Sign in</Link><Link className="button primary small" to="/register">Create account</Link></nav></header>
    <main>
      <section className="hero">
        <div className="hero-copy"><span className="pill"><Sparkles size={15}/> Responsible AI for retention support</span><h1>See risk earlier.<br/><em>Keep care connected.</em></h1><p>MEDISCOPE combines secure clinical workflows with two-model machine-learning decision support to help clinicians identify synthetic patients who may need additional retention support.</p><div className="hero-actions"><Link className="button primary" to="/login">Enter secure workspace <ArrowRight size={18}/></Link><Link className="button ghost" to="/about">Explore the platform</Link></div><div className="trust-row"><span><ShieldCheck/> Role-based access</span><span><LockKeyhole/> MFA protected</span><span><CheckCircle2/> Auditable predictions</span></div></div>
        <div className="hero-visual">
          <div className="halo halo-one"/><div className="halo halo-two"/>
          <div className="glass-panel prediction-demo"><div className="demo-top"><span className="status-chip">LTFU risk intelligence</span><BrainCircuit/></div><div className="risk-ring"><div><strong>82%</strong><span>model consensus</span></div></div><div className="model-bars"><div><span>Logistic Regression</span><b>84%</b><i style={{width:'84%'}}/></div><div><span>XGBoost</span><b>80%</b><i style={{width:'80%'}}/></div></div><div className="demo-note">Decision support only · clinician review required</div></div>
          <div className="floating-card card-a"><span>Retention signal</span><strong>2 models agree</strong></div><div className="floating-card card-b"><span>Audit trail</span><strong>Fully traceable</strong></div>
        </div>
      </section>
      <section className="feature-strip"><div><strong>Secure by design</strong><span>JWT · MFA · RBAC</span></div><div><strong>Clinically traceable</strong><span>History · Versions · Snapshots</span></div><div><strong>Model-aware</strong><span>Logistic Regression · XGBoost</span></div><div><strong>Synthetic prototype</strong><span>No real patient data</span></div></section>
    </main>
  </div>;
}
