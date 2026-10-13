import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { mensajeDeError } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import Marca from "../components/Marca";

// Lo que exige hoy el sistema para subir de nivel (reglas de backend/workflow/services.py).
const NIVELES = [
  { nombre: "Identificada", regla: "Se registra la práctica." },
  { nombre: "Formalizada", regla: "Tiene un responsable asignado." },
  { nombre: "Medida", regla: "Una medición validada, con evidencia." },
  { nombre: "Optimizada", regla: "Tiene meta y dos mediciones validadas." },
];

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(username, password);
      navigate("/");
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  return (
    <main className="login">
      <section className="login-panel">
        <div>
          <Marca tamano={40} />
          <h2>Registrá, medí y validá las prácticas sostenibles de cada Facultad.</h2>
          <p className="sub">Cada práctica avanza por cuatro niveles de madurez a medida que suma responsable, evidencia e indicadores.</p>
        </div>
        <ol className="login-escalera" aria-label="Niveles de madurez de una práctica">
          {NIVELES.map((n) => (
            <li key={n.nombre}>
              <strong>{n.nombre}</strong>
              <span>{n.regla}</span>
            </li>
          ))}
        </ol>
      </section>
      <section className="login-formulario">
        <div>
          <h1>SUSI</h1>
          <p className="sub">Sistema Universitario de Sustentabilidad Integral</p>
          <form onSubmit={enviar}>
            <label>
              Usuario
              <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
            </label>
            <label>
              Contraseña
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button type="submit">Ingresar</button>
          </form>
        </div>
      </section>
    </main>
  );
}
