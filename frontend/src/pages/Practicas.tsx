import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { api, mensajeDeError } from "../api/client";
import type { Catalogos, Page, Practica } from "../api/types";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import { EstadoBadge, IlustrativoBadge } from "../components/Badge";

const NUEVA_VACIA = { facultad: "", nombre: "", dimension: "ambiental", proposito: "", ods: [] as number[] };

export default function Practicas() {
  const { sesion } = useAuth();
  const navigate = useNavigate();
  const catalogos = useApi<Catalogos>("/api/catalogos/");
  const [pagina, setPagina] = useState(1);
  const [facultad, setFacultad] = useState("");
  const [estado, setEstado] = useState("");
  const [nueva, setNueva] = useState(NUEVA_VACIA);
  const [error, setError] = useState<string | null>(null);

  const params = new URLSearchParams({ page: String(pagina) });
  if (facultad) params.set("facultad", facultad);
  if (estado) params.set("estado", estado);
  const lista = useApi<Page<Practica>>(`/api/practicas/?${params}`);

  const facultadesEscribibles =
    catalogos.data?.facultades.filter(
      (f) => sesion?.es_admin || sesion?.membresias.some((m) => m.facultad === f.id && m.rol === "responsable"),
    ) ?? [];

  async function crear(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      const creada = await api<Practica>("/api/practicas/", {
        method: "POST",
        body: {
          facultad: Number(nueva.facultad),
          nombre: nueva.nombre,
          dimension: nueva.dimension,
          proposito: nueva.proposito,
          ods: nueva.ods,
        },
      });
      navigate(`/practicas/${creada.id}`);
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  const totalPaginas = Math.max(1, Math.ceil((lista.data?.count ?? 0) / 20));

  return (
    <>
      <h1>Prácticas sostenibles</h1>

      <div className="filtros">
        <label>
          Facultad
          <select
            value={facultad}
            onChange={(e) => {
              setFacultad(e.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todas</option>
            {catalogos.data?.facultades.map((f) => (
              <option key={f.id} value={f.id}>
                {f.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Estado
          <select
            value={estado}
            onChange={(e) => {
              setEstado(e.target.value);
              setPagina(1);
            }}
          >
            <option value="">Todos</option>
            {catalogos.data?.estados.map((o) => (
              <option key={o.valor} value={o.valor}>
                {o.etiqueta}
              </option>
            ))}
          </select>
        </label>
      </div>

      {lista.error && (
        <p role="alert" className="error">
          {lista.error}
        </p>
      )}
      <table>
        <thead>
          <tr>
            <th>Práctica</th>
            <th>Facultad</th>
            <th>Dimensión</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          {lista.data?.results.map((p) => (
            <tr key={p.id}>
              <td>
                <Link to={`/practicas/${p.id}`}>{p.nombre}</Link> {p.origen === "ilustrativa" && <IlustrativoBadge />}
              </td>
              <td>{p.facultad_nombre}</td>
              <td>{p.dimension}</td>
              <td>
                <EstadoBadge estado={p.estado} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {lista.data?.count === 0 && <p>No hay prácticas con esos filtros.</p>}
      <div className="fila" style={{ margin: "0.75rem 0 1.5rem" }}>
        <button type="button" className="secundario" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
          Anterior
        </button>
        <span>
          Página {pagina} de {totalPaginas}
        </span>
        <button type="button" className="secundario" disabled={!lista.data?.next} onClick={() => setPagina(pagina + 1)}>
          Siguiente
        </button>
      </div>

      {facultadesEscribibles.length > 0 && (
        <details className="tarjeta">
          <summary>Nueva práctica</summary>
          <form onSubmit={crear} className="formulario" style={{ marginTop: "0.75rem" }}>
            <label>
              Facultad
              <select value={nueva.facultad} onChange={(e) => setNueva({ ...nueva, facultad: e.target.value })} required>
                <option value="">Elegir…</option>
                {facultadesEscribibles.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.nombre}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Nombre
              <input value={nueva.nombre} onChange={(e) => setNueva({ ...nueva, nombre: e.target.value })} required />
            </label>
            <label>
              Dimensión
              <select value={nueva.dimension} onChange={(e) => setNueva({ ...nueva, dimension: e.target.value })}>
                {catalogos.data?.dimensiones.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.etiqueta}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Propósito (opcional)
              <textarea value={nueva.proposito} onChange={(e) => setNueva({ ...nueva, proposito: e.target.value })} />
            </label>
            <label>
              ODS relacionados (opcional, Ctrl/Cmd para varios)
              <select
                multiple
                size={5}
                value={nueva.ods.map(String)}
                onChange={(e) =>
                  setNueva({ ...nueva, ods: Array.from(e.target.selectedOptions, (o) => Number(o.value)) })
                }
              >
                {catalogos.data?.ods.map((o) => (
                  <option key={o.numero} value={o.numero}>
                    ODS {o.numero}: {o.nombre}
                  </option>
                ))}
              </select>
            </label>
            {error && (
              <p role="alert" className="error">
                {error}
              </p>
            )}
            <button type="submit">Crear práctica</button>
          </form>
        </details>
      )}
    </>
  );
}
