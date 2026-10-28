import { useState } from 'react';
import type { Member } from './api';

export function MemberCard({ member, created, onEdit, onLeave }: { member: Member; created: boolean; onEdit: () => void; onLeave: () => void }) {
  const [copied, setCopied] = useState(false);
  const [copyFailed, setCopyFailed] = useState(false);
  async function copy() {
    try { await navigator.clipboard.writeText(member.member_code); setCopied(true); setCopyFailed(false); }
    catch { setCopyFailed(true); }
  }
  return <section className="form-panel" aria-labelledby="member-title">
    <p className="eyebrow">{created ? 'PROFILE CREATED' : 'YOUR PROFILE'}</p>
    <h1 id="member-title">{created ? 'You’re part of the arena.' : 'Good to see you again.'}</h1>
    <p className="lead">{created ? 'Your details are saved. Keep your member code for your next visit.' : 'Check your details or make a correction before you leave.'}</p>
    <div className="member-summary"><div><span className="small-label">FULL NAME</span><strong>{member.full_name}</strong></div><div><span className="small-label">AGE</span><strong>{member.age}</strong></div></div>
    <div className="code-card"><span className="small-label">YOUR PRIVATE MEMBER CODE</span><strong>{member.member_code}</strong><button className="copy-button" onClick={copy}>{copied ? 'Copied ✓' : 'Copy code'}</button><p role="status">{copyFailed ? 'Copy is unavailable here. Please note down the code above.' : 'Use this code to open your profile on your next visit.'}</p></div>
    <div className="actions"><button className="button secondary" onClick={onEdit}>Edit my details</button><button className="button primary" onClick={onLeave}>Done and sign out<span aria-hidden="true">↗</span></button></div>
  </section>;
}
