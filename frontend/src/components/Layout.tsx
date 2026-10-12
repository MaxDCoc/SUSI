import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { sesion, logout, tieneAlgunRol } = useAuth();
  const navigate = useNavigate();

  async function salir() {
    await logout();
    navigate("/login");
  }

  return (
    <>
      <header className="barra">
        <strong className="marca">SUSI</strong>
        <nav aria-label="Principal">
          <NavLink to="/practicas">Prácticas</NavLink>
          {tieneAlgunRol("validador") && <NavLink to="/validaciones">Validaciones</NavLink>}
          <NavLink to="/tablero">Tablero</NavLink>
          <NavLink to="/green">Green Software</NavLink>
        </nav>
        <span className="usuario">{sesion?.username}</span>
        <button type="button" onClick={salir}>
          Salir
        </button>
      </header>
      <main className="contenido">
        <Outlet />
      </main>
    </>
  );
}
