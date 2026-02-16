"use client";

import { createContext, useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import api from "@/lib/api";
import type { AuthResponse, SignInResponse, User } from "@/lib/types";

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  signUp: (email: string, firstName: string, lastName: string, password: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchProfile = useCallback(async (jwt: string) => {
    try {
      const { data } = await api.get<User>("/auth/profile", {
        headers: { Authorization: `Bearer ${jwt}` },
      });
      setUser(data);
      setToken(jwt);
    } catch {
      localStorage.removeItem("token");
      setUser(null);
      setToken(null);
    }
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("token");
    if (stored) {
      fetchProfile(stored).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [fetchProfile]);

  const signUp = async (email: string, firstName: string, lastName: string, password: string) => {
    const { data } = await api.post<AuthResponse>("/auth/signup", {
      email,
      first_name: firstName,
      last_name: lastName,
      password,
    });
    localStorage.setItem("token", data.token);
    setToken(data.token);
    setUser(data.user);
  };

  const signIn = async (email: string, password: string) => {
    const { data } = await api.post<SignInResponse>("/auth/signin", {
      email,
      password,
    });
    localStorage.setItem("token", data.token);
    setToken(data.token);
    await fetchProfile(data.token);
  };

  const signOut = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, signUp, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
