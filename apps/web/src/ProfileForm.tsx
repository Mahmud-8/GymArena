import { useRef, useState, type FormEvent } from 'react';
import { ApiError, type Details, type FieldErrors } from './api';

type Props = {
  initial?: Details;
  editing?: boolean;
  onSave: (details: Details, requestId: string) => Promise<void>;
  onBack: () => void;
};

export function ProfileForm({ initial, editing = false, onSave, onBack }: Props) {
  const [name, setName] = useState(initial?.full_name ?? '');
  const [age, setAge] = useState(initial ? String(initial.age) : '');
  const [errors, setErrors] = useState<FieldErrors>({});
  const [message, setMessage] = useState('');
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const requestId = useRef<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (inFlight.current) return;
    const fields: FieldErrors = {};
    const full_name = name.trim().replace(/\s+/gu, ' ');
    const numberAge = Number(age);
    if (!full_name) fields.full_name = 'Enter your full name.';
    if (!age.trim() || !Number.isInteger(numberAge) || numberAge < 1 || numberAge > 120) fields.age = 'Enter a whole-number age between 1 and 120.';
    setErrors(fields); setMessage('');
    if (Object.keys(fields).length) return;
    inFlight.current = true; setPending(true);
    requestId.current ??= crypto.randomUUID();
    try {
      await onSave({ full_name, age: numberAge }, requestId.current);
    } catch (error) {
      const failure = error instanceof ApiError ? error : new ApiError('Please try again.', 0);
      setErrors(failure.fields); setMessage(failure.message);
    } finally {
      inFlight.current = false; setPending(false);
    }
  }

  return <section className="form-panel" aria-labelledby="profile-title">
    <p className="eyebrow">{editing ? 'YOUR PROFILE' : 'FIRST VISIT'}</p>
    <h1 id="profile-title">{editing ? 'Keep your details up to date.' : 'Let’s set up your profile.'}</h1>
    <p className="lead">{editing ? 'Your member code stays the same when you make a correction.' : 'A name. Your age. One member code for every visit.'}</p>
    <form onSubmit={submit} noValidate>
      <div className="field-grid">
        <div className="field">
          <label htmlFor="full-name">Full name</label>
          <input id="full-name" name="full_name" value={name} onChange={e => setName(e.target.value)} maxLength={120} autoComplete="off" disabled={pending} aria-invalid={Boolean(errors.full_name)} aria-describedby={errors.full_name ? 'name-error' : undefined} />
          {errors.full_name && <span className="field-error" id="name-error">{errors.full_name}</span>}
        </div>
        <div className="field age-field">
          <label htmlFor="age">Age</label>
          <input id="age" name="age" type="number" inputMode="numeric" min={1} max={120} step={1} value={age} onChange={e => setAge(e.target.value)} disabled={pending} aria-invalid={Boolean(errors.age)} aria-describedby={errors.age ? 'age-error' : undefined} />
          {errors.age && <span className="field-error" id="age-error">{errors.age}</span>}
        </div>
      </div>
      {message && <div role="alert" className="error-message">{message}</div>}
      <div className="actions">
        <button className="button primary" type="submit" disabled={pending}>{pending ? 'Saving…' : editing ? 'Save changes' : 'Create my profile'}<span aria-hidden="true">↗</span></button>
        <button className="button text-button" type="button" onClick={onBack} disabled={pending}>{editing ? 'Cancel' : 'Back'}</button>
      </div>
    </form>
    {!editing && <p className="privacy-note">Your code gives access to your profile. Keep it private and save it somewhere safe for your next visit.</p>}
  </section>;
}
