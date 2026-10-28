import { useCallback, useEffect, useRef, useState } from 'react';
import { api, ApiError, type Details, type Member, type Session } from './api';
import { AccessForm } from './AccessForm';
import { ProfileForm } from './ProfileForm';
import { MemberCard } from './MemberCard';

type View = 'welcome' | 'register' | 'access' | 'profile' | 'edit';

export default function App() {
  const [view, setView] = useState<View>('welcome');
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [created, setCreated] = useState(false);
  const [notice, setNotice] = useState('');
  const headingTarget = useRef<HTMLDivElement>(null);
  const sessionEpoch = useRef(0);

  const leave = useCallback(async (message = '') => {
    sessionEpoch.current += 1;
    setLoading(true);
    setSession(null); setView('welcome'); setCreated(false);
    setNotice(message);
    try { await api<void>('/member-session', 'DELETE'); }
    catch { setNotice('This screen has been cleared. Re-enter your code to continue.'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => {
    let active = true;
    // A shared kiosk never reveals the previous visitor's profile on reload.
    api<void>('/member-session', 'DELETE')
      .catch(() => { if (active) setNotice('We could not reach the member service. You can retry from this screen.'); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  useEffect(() => { headingTarget.current?.focus(); }, [view]);
  useEffect(() => {
    if (!session) return;
    let timeout: number;
    const reset = () => { window.clearTimeout(timeout); timeout = window.setTimeout(() => { void leave('For your privacy, the kiosk signed out after two minutes without activity.'); }, 120000); };
    reset(); window.addEventListener('pointerdown', reset, { passive: true }); window.addEventListener('keydown', reset);
    return () => { window.clearTimeout(timeout); window.removeEventListener('pointerdown', reset); window.removeEventListener('keydown', reset); };
  }, [session, leave]);

  function accept(value: Session, fresh: boolean) { setSession(value); setCreated(fresh); setNotice(''); setView('profile'); }
  async function register(details: Details, requestId: string) {
    const epoch = sessionEpoch.current;
    const value = await api<Session>('/members', 'POST', details, { 'Idempotency-Key': requestId });
    if (epoch === sessionEpoch.current) accept(value, true);
  }
  async function access(code: string) {
    const epoch = sessionEpoch.current;
    const value = await api<Session>('/member-access', 'POST', { member_code: code });
    if (epoch === sessionEpoch.current) accept(value, false);
  }
  async function correct(details: Details) {
    if (!session) throw new ApiError('Confirm your member code to continue.', 401);
    const epoch = sessionEpoch.current;
    try {
      const member = await api<Member>(`/members/${session.member.member_id}`, 'PATCH', { ...details, expected_updated_at: session.member.updated_at }, { 'X-CSRF-Token': session.csrf_token });
      if (epoch !== sessionEpoch.current) return;
      setSession({ ...session, member }); setCreated(false); setView('profile'); setNotice('Your profile changes have been saved.');
    } catch (failure) {
      if (epoch !== sessionEpoch.current) return;
      if (failure instanceof ApiError && failure.status === 401) { setSession(null); setView('access'); setNotice('Your confirmation expired. Enter your member code to continue.'); }
      if (failure instanceof ApiError && failure.status === 409) {
        const fresh = await api<Session>('/member-session');
        if (epoch === sessionEpoch.current) { setSession(fresh); setNotice('A newer profile has been loaded. Please check the details before saving again.'); }
      }
      throw failure;
    }
  }

  return <div className="app-shell">
    <header className="topbar"><a className="brand" href="/kiosk/" aria-label="GymArena home"><span className="brand-mark" aria-hidden="true">g<span>↗</span></span>gymarena<span className="brand-dot">.</span></a><span className="kiosk-label"><span aria-hidden="true" className="live-dot" />MEMBER KIOSK</span>{session && <button className="quiet-button" onClick={() => void leave()}>Sign out</button>}</header>
    <main>
      <aside className="arena-panel" aria-label="About GymArena"><div className="panel-top"><span className="pill">YOUR NEXT CHAPTER</span><span aria-hidden="true">01 / MEMBER</span></div><div className="arena-type" aria-hidden="true">SHOW<br />UP.<br /><span>LEVEL<br />UP.</span></div><div className="orbit" aria-hidden="true"><div className="orbit-inner">GA</div><span>ONE PROFILE. EVERY VISIT.</span></div><div className="panel-bottom"><span>Small steps.<br />Stronger every day.</span><span className="arrow" aria-hidden="true">↗</span></div></aside>
      <div className="content-panel" ref={headingTarget} tabIndex={-1}>
        <div className="breadcrumb">GYMARENA <span>/</span> {view === 'welcome' ? 'WELCOME' : view === 'register' ? 'NEW MEMBER' : 'MEMBER PROFILE'}</div>
        {notice && <div role="status" className="notice">{notice}</div>}
        {loading ? <p className="lead" role="status">Getting the kiosk ready…</p> : <>
          {view === 'welcome' && <section className="form-panel"><p className="eyebrow">YOUR ARENA STARTS HERE</p><h1>One profile.<br />Every visit.</h1><p className="lead">Make yourself at home. Create your member profile or pick up where you left off.</p><div className="choice-stack"><button className="choice-card new-member" onClick={() => setView('register')}><span className="choice-number">01</span><span><strong>First time here?</strong><small>Create your profile and get your private member code.</small></span><span className="choice-arrow" aria-hidden="true">↗</span></button><button className="choice-card" onClick={() => setView('access')}><span className="choice-number">02</span><span><strong>Welcome back.</strong><small>Use your member code to open your profile.</small></span><span className="choice-arrow" aria-hidden="true">↗</span></button></div><p className="privacy-note">Your profile stays yours. Always sign out before the next person uses the kiosk.</p></section>}
          {view === 'register' && <ProfileForm onSave={register} onBack={() => setView('welcome')} />}
          {view === 'access' && <AccessForm onAccess={access} onBack={() => setView('welcome')} />}
          {view === 'profile' && session && <MemberCard key={session.member.member_id} member={session.member} created={created} onEdit={() => setView('edit')} onLeave={() => void leave()} />}
          {view === 'edit' && session && <ProfileForm key={session.member.updated_at} initial={session.member} editing onSave={correct} onBack={() => setView('profile')} />}
        </>}
        <footer className="content-footer"><span>MEMBER REGISTRATION &amp; PROFILE</span><span>MADE FOR YOUR NEXT VISIT ↗</span></footer>
      </div>
    </main>
  </div>;
}
