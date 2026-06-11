// Client API minimal. La implementare: generează tipurile din OpenAPI
// (openapi-typescript) ca să nu existe drift între backend și frontend.

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

// MVP: token static, citit din localStorage (un singur utilizator).
function authHeader(): Record<string, string> {
  const token = localStorage.getItem("api_token") ?? "";
  return { Authorization: `Bearer ${token}` };
}

export async function apiGet<T>(path: string): Promise<T> {
  const resp = await fetch(`${API_BASE}/api/v1${path}`, {
    headers: { ...authHeader() },
  });
  if (!resp.ok) throw new Error(`GET ${path}: ${resp.status}`);
  return resp.json() as Promise<T>;
}

export async function apiPost<T>(path: string, body: unknown): Promise<T> {
  const resp = await fetch(`${API_BASE}/api/v1${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(body),
  });
  if (!resp.ok) throw new Error(`POST ${path}: ${resp.status}`);
  return resp.json() as Promise<T>;
}
