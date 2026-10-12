import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";

function Protegida({ children }: { children: ReactNode }) {
  const { sesion, cargando } = useAuth();
  if (cargando) return <p>Cargando…</p>;
  return sesion?.authenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function Inicio() {
  const { sesion } = useAuth();
  return <h1>Hola, {sesion?.username}</h1>;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            element={
              <Protegida>
                <Layout />
              </Protegida>
            }
          >
            <Route index element={<Inicio />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
