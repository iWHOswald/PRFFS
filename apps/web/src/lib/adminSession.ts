// Keep the credential in memory only. Reloading the page signs the admin out.
let token = "";
const listeners = new Set<() => void>();

export function getAdminToken() {
  return token;
}

export function setAdminToken(value: string) {
  token = value;
  listeners.forEach((listener) => listener());
}

export function subscribeAdminSession(listener: () => void) {
  listeners.add(listener);
  return () => { listeners.delete(listener); };
}
