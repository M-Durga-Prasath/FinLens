let cachedToken = null;
let tokenExpiresAt = 0;
let pendingFetch = null;

export async function getBackendToken({ forceRefresh = false } = {}) {
  const now = Date.now();

  if (!forceRefresh && cachedToken && tokenExpiresAt > now + 60 * 1000) {
    return cachedToken;
  }

  if (pendingFetch) {
    return pendingFetch;
  }

  pendingFetch = (async () => {
    try {
      const res = await fetch("/api/auth/backend-token");
      if (!res.ok) {
        if (res.status === 401) {
          cachedToken = null;
          tokenExpiresAt = 0;
          return null;
        }
        throw new Error(`Failed to retrieve backend auth token: ${res.status}`);
      }

      const data = await res.json();
      if (!data.token) {
        throw new Error("No token returned by /api/auth/backend-token");
      }

      cachedToken = data.token;
      // Tokens expire = 60 mins' refresh window = 50 mins
      tokenExpiresAt = now + 50 * 60 * 1000;
      return cachedToken;
    } finally {
      pendingFetch = null;
    }
  })();

  return pendingFetch;
}

export function clearBackendToken() {
  cachedToken = null;
  tokenExpiresAt = 0;
  pendingFetch = null;
}
