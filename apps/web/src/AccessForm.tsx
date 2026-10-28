import { useRef, useState, type FormEvent } from 'react';
import { ApiError } from './api';

export function AccessForm({ onAccess, onBack }: { onAccess: (code: string) => Promise<void>; onBack: () => void }) {
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current) return;
    if (!code.trim()) { setError('Enter your member code.'); return; }
    inFlight.current = true; setPending(true); setError('');
    try { await onAccess(code); }
    catch (failure) { setError(failure instanceof ApiError ? failure.message : 'Please try again.'); }
    finally { inFlight.current = false; setPending(false); }
  }

  return <section className="form-panel" aria-labelledby="access-title">
    <p className="eyebrow">WELCOME BACK</p>
    <h1 id="access-title">Pick up where<br />you left off.</h1>
    <p className="lead">Use the private member code you received when you registered.</p>
    <form onSubmit={submit} noValidate>
      <div className="field">
        <label htmlFor="member-code">Member code</label>
        <input id="member-code" className="code-input" name="member_code" autoComplete="off" autoCapitalize="characters" spellCheck={false} maxLength={80} placeholder="GA-XXXX-XXXX-XXXX-XXXX" value={code} onChange={e => setCode(e.target.value)} disabled={pending} aria-invalid={Boolean(error)} aria-describedby={error ? 'code-error' : undefined} />
        {error && <span className="field-error" role="alert" id="code-error">{error}</span>}
      </div>
      <div className="actions">
        <button className="button primary" type="submit" disabled={pending}>{pending ? 'Finding your profile…' : 'Confirm my code'}<span aria-hidden="true">↗</span></button>
        <button className="button text-button" type="button" onClick={onBack} disabled={pending}>Back</button>
      </div>
    </form>
  </section>;
}
