import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { api } from "../api/client";
import type { Rol, Sesion } from "../api/types";

interface AuthValue {
  sesion: Sesion | null;
  cargando: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  tieneRol: (facultadId: number, rol: Rol) => boolean;
  tieneAlgunRol: (rol: Rol) => boolean;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [sesion, setSesion] = useState<Sesion | null>(null);
  const [cargando, setCargando] = useState(true);

  // Este GET también deja la cookie CSRF que necesitan los POST (incluido el login).
  useEffect(() => {
    api<Sesion>("/api/auth/session/")
      .then(setSesion)
      .catch(() => setSesion({ authenticated: false, membresias: [] }))
      .finally(() => setCargando(false));
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setSesion(await api<Sesion>("/api/auth/login/", { method: "POST", body: { username, password } }));
  }, []);

  const logout = useCallback(async () => {
    setSesion(await api<Sesion>("/api/auth/logout/", { method: "POST" }));
  }, []);

  const value = useMemo<AuthValue>(
    () => ({
      sesion,
      cargando,
      login,
      logout,
      tieneRol: (facultadId, rol) =>
        !!sesion?.es_admin || !!sesion?.membresias.some((m) => m.facultad === facultadId && m.rol === rol),
      tieneAlgunRol: (rol) => !!sesion?.es_admin || !!sesion?.membresias.some((m) => m.rol === rol),
    }),
    [sesion, cargando, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
