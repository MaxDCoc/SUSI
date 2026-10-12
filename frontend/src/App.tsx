import type { ReactNode } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import PracticaDetalle from "./pages/PracticaDetalle";
import Practicas from "./pages/Practicas";

function Protegida({ children }: { children: ReactNode }) {
  const { sesion, cargando } = useAuth();
  if (cargando) return <p>Cargando…</p>;
  return sesion?.authenticated ? <>{children}</> : <Navigate to="/login" replace />;
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
            <Route index element={<Navigate to="/practicas" replace />} />
            <Route path="practicas" element={<Practicas />} />
            <Route path="practicas/:id" element={<PracticaDetalle />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
