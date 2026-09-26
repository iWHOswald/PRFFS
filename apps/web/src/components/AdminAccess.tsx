import { FormEvent, ReactNode, useState, useSyncExternalStore } from "react";
import { api } from "../lib/api";
import { getAdminToken, setAdminToken, subscribeAdminSession } from "../lib/adminSession";

export function AdminAccess({ children }: { children: ReactNode }) {
  const token = useSyncExternalStore(subscribeAdminSession, getAdminToken);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await api.checkAdmin(password);
      setAdminToken(password);
      setPassword("");
    } catch {
      setError("Sign-in failed. Check your admin password and try again.");
    } finally {
      setBusy(false);
    }
  }

  if (token) return (
    <>
      <div className="admin-access-bar">
        <span>Signed in as league admin</span>
        <button type="button" onClick={() => setAdminToken("")}>Sign out</button>
      </div>
      {children}
    </>
  );

  return (
    <section className="wide-panel admin-access">
      <h2>League admin sign-in</h2>
      <p>Sign in to manage league notes and draft entries.</p>
      <form onSubmit={signIn}>
        <label htmlFor="admin-password">Admin password</label>
        <input id="admin-password" className="field" type="password" autoComplete="current-password"
          value={password} onChange={(event) => setPassword(event.target.value)} required />
        <button type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        {error ? <p role="alert">{error}</p> : null}
      </form>
    </section>
  );
}
