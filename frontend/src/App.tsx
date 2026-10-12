import { lazy, type ReactNode, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { AuthProvider, useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import PracticaDetalle from "./pages/PracticaDetalle";
import Practicas from "./pages/Practicas";
import Validaciones from "./pages/Validaciones";

// Páginas con gráficos: se descargan recién al abrirlas.
const Tablero = lazy(() => import("./pages/Tablero"));
const Green = lazy(() => import("./pages/Green"));

function Protegida({ children }: { children: ReactNode }) {
  const { sesion, cargando } = useAuth();
  if (cargando) return <p>Cargando…</p>;
  return sesion?.authenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<p>Cargando…</p>}>
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
              <Route path="validaciones" element={<Validaciones />} />
              <Route path="tablero" element={<Tablero />} />
              <Route path="green" element={<Green />} />
            </Route>
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  );
}
