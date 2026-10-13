import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import { IconoGreen, IconoPracticas, IconoTablero, IconoValidaciones } from "./Iconos";
import Marca from "./Marca";

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
        <strong className="marca">
          <Marca />
          SUSI
        </strong>
        <nav aria-label="Principal">
          <NavLink to="/practicas">
            <IconoPracticas />
            Prácticas
          </NavLink>
          {tieneAlgunRol("validador") && (
            <NavLink to="/validaciones">
              <IconoValidaciones />
              Validaciones
            </NavLink>
          )}
          <NavLink to="/tablero">
            <IconoTablero />
            Tablero
          </NavLink>
          <NavLink to="/green">
            <IconoGreen />
            Green Software
          </NavLink>
        </nav>
        <span className="usuario">
          <span className="avatar" aria-hidden="true">
            {sesion?.username?.charAt(0)}
          </span>
          {sesion?.username}
        </span>
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
