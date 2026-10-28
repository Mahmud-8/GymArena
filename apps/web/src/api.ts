export type Member = {
  member_id: string; full_name: string; age: number; member_code: string;
  created_at: string; updated_at: string;
};
export type Session = { member: Member; csrf_token: string; expires_in: number };
export type Details = { full_name: string; age: number };
export type FieldErrors = Record<string, string>;

export class ApiError extends Error {
  constructor(message: string, public status: number, public fields: FieldErrors = {}) {
    super(message);
  }
}

export async function api<T>(path: string, method = 'GET', body?: unknown, headers: Record<string, string> = {}): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  try {
    const response = await fetch(`/api${path}`, {
      method, credentials: 'same-origin', cache: 'no-store', signal: controller.signal,
      headers: { ...(body ? { 'Content-Type': 'application/json' } : {}), ...headers },
      ...(body ? { body: JSON.stringify(body) } : {}),
    });
    if (response.status === 204) return undefined as T;
    const data = await response.json();
    if (!response.ok) throw new ApiError(typeof data.detail === 'string' ? data.detail : 'Please check your details.', response.status, data.fields ?? {});
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('We could not confirm your request. Your details are still here. Please retry the same request.', 0);
  } finally {
    window.clearTimeout(timeout);
  }
}
