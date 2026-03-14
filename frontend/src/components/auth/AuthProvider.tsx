"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface AuthUser {
  id: number;
  email: string;
  is_premium: boolean;
  subscription_status?: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  refreshUser: async () => {},
});

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const setTokens = useCallback(
    (accessToken: string, refreshToken: string) => {
      localStorage.setItem("chartora_access_token", accessToken);
      localStorage.setItem("chartora_refresh_token", refreshToken);
    },
    [],
  );

  const clearTokens = useCallback(() => {
    localStorage.removeItem("chartora_access_token");
    localStorage.removeItem("chartora_refresh_token");
  }, []);

  const fetchUser = useCallback(async (): Promise<AuthUser | null> => {
    const token = localStorage.getItem("chartora_access_token");
    if (!token) return null;

    const res = await apiFetch("/api/v1/auth/me", {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!res.ok) {
      // Try refreshing the token
      const refreshToken = localStorage.getItem("chartora_refresh_token");
      if (refreshToken) {
        const refreshRes = await apiFetch("/api/v1/auth/refresh", {
          method: "POST",
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem("chartora_access_token", data.access_token);
          // Retry /me with new token
          const retryRes = await apiFetch("/api/v1/auth/me", {
            headers: { Authorization: `Bearer ${data.access_token}` },
          });
          if (retryRes.ok) return retryRes.json();
        }
      }
      clearTokens();
      return null;
    }

    return res.json();
  }, [clearTokens]);

  const refreshUser = useCallback(async () => {
    try {
      const u = await fetchUser();
      setUser(u);
      if (u?.is_premium) {
        document.documentElement.dataset.premium = "true";
      } else {
        delete document.documentElement.dataset.premium;
      }
    } catch {
      setUser(null);
      delete document.documentElement.dataset.premium;
    }
  }, [fetchUser]);

  useEffect(() => {
    let cancelled = false;
    fetchUser()
      .then((u) => {
        if (cancelled) return;
        setUser(u);
        if (u?.is_premium) {
          document.documentElement.dataset.premium = "true";
        } else {
          delete document.documentElement.dataset.premium;
        }
      })
      .catch(() => {
        if (cancelled) return;
        setUser(null);
        delete document.documentElement.dataset.premium;
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [fetchUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const res = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Login failed");
      }

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
      if (data.user.is_premium) {
        document.documentElement.dataset.premium = "true";
      }
    },
    [setTokens],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      const res = await apiFetch("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail ?? "Registration failed");
      }

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
    },
    [setTokens],
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
    delete document.documentElement.dataset.premium;
  }, [clearTokens]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout, refreshUser }),
    [user, loading, login, register, logout, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
