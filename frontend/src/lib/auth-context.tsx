"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { ManagerUser } from "@/types";
import { api, setStoredToken } from "@/lib/api";

interface AuthContextType {
  user: ManagerUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<ManagerUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    let isMounted = true;

    async function checkAuth() {
      try {
        const currentUser = await api.auth.getMe();
        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        if (isMounted) {
          setUser(null);
          setStoredToken(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    checkAuth();

    function handleUnauthorized() {
      setUser(null);
      setStoredToken(null);
      if (pathname !== "/login") {
        router.push(`/login?redirect=${encodeURIComponent(pathname)}`);
      }
    }

    window.addEventListener("peat_crm_unauthorized", handleUnauthorized);
    return () => {
      isMounted = false;
      window.removeEventListener("peat_crm_unauthorized", handleUnauthorized);
    };
  }, [pathname, router]);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await api.auth.login(username, password);
      setUser(res.manager);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    setIsLoading(true);
    try {
      await api.auth.logout();
    } finally {
      setUser(null);
      setIsLoading(false);
      router.push("/login");
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
