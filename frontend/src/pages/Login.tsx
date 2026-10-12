import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { mensajeDeError } from "../api/client";
import { useAuth } from "../auth/AuthContext";

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
    </main>
  );
}
