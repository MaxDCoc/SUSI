import { useState } from "react";
import { Link } from "react-router-dom";

import { api, mensajeDeError } from "../api/client";
import type { Medicion, Page } from "../api/types";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import { puedeValidar } from "../lib/acciones";

export default function Validaciones() {
  const { sesion, tieneRol } = useAuth();
  const lista = useApi<Page<Medicion>>("/api/mediciones/?estado=enviada&page_size=50");
  const [comentarios, setComentarios] = useState<Record<number, string>>({});
  const [errores, setErrores] = useState<Record<number, string>>({});

  async function resolver(medicion: Medicion, accion: "validar" | "rechazar") {
    setErrores((prev) => ({ ...prev, [medicion.id]: "" }));
    try {
      await api(`/api/mediciones/${medicion.id}/${accion}/`, {
        method: "POST",
        body: { comentario: comentarios[medicion.id] ?? "" },
      });
      lista.recargar();
    } catch (e) {
      setErrores((prev) => ({ ...prev, [medicion.id]: mensajeDeError(e) }));
    }
  }

  return (
    <>
      <h1>Mediciones para validar</h1>
      {lista.error && (
        <p role="alert" className="error">
          {lista.error}
        </p>
      )}
      {lista.data?.count === 0 && <p>No hay mediciones pendientes de validación.</p>}
      {lista.data?.results.map((m) => {
        const puede = puedeValidar(m, sesion, tieneRol);
        const propia = sesion?.id === m.cargado_por;
        return (
          <article key={m.id} className="tarjeta">
            <h3>
              <Link to={`/practicas/${m.practica_id}`}>{m.practica_nombre}</Link>
            </h3>
            <p>
              {m.facultad_nombre} · {m.indicador_nombre} · {m.periodo} ·{" "}
              <strong>
                {Number(m.valor)} {m.unidad}
              </strong>
            </p>
            <p className="nota">Cargada por {m.cargado_por_nombre}</p>
            <ul className="evidencias">
              {m.evidencias.map((ev) => (
                <li key={ev.id}>
                  <a
                    href={ev.tipo === "enlace" ? ev.url : (ev.archivo_descarga ?? "#")}
                    target="_blank"
                    rel="noreferrer noopener"
                  >
                    {ev.descripcion || (ev.tipo === "enlace" ? ev.url : "Archivo adjunto")}
                  </a>
                </li>
              ))}
              {m.evidencias.length === 0 && <li className="nota">Sin evidencia adjunta</li>}
            </ul>
            <div className="fila">
              <label style={{ flex: 1 }}>
                Comentario (obligatorio para rechazar)
                <input
                  value={comentarios[m.id] ?? ""}
                  onChange={(e) => setComentarios((prev) => ({ ...prev, [m.id]: e.target.value }))}
                />
              </label>
              <button type="button" disabled={!puede} onClick={() => resolver(m, "validar")}>
                Validar
              </button>
              <button type="button" className="secundario" disabled={!puede} onClick={() => resolver(m, "rechazar")}>
                Rechazar
              </button>
            </div>
            {propia && <p className="nota">No podés validar una medición que cargaste vos.</p>}
            {errores[m.id] && (
              <p role="alert" className="error">
                {errores[m.id]}
              </p>
            )}
          </article>
        );
      })}
    </>
  );
}
