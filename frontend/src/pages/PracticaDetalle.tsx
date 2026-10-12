import { type FormEvent, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, mensajeDeError } from "../api/client";
import type { Catalogos, Indicador, Medicion, Page, Practica } from "../api/types";
import { ESTADOS } from "../api/types";
import { useApi } from "../api/useApi";
import { useAuth } from "../auth/AuthContext";
import { EstadoBadge, IlustrativoBadge } from "../components/Badge";
import IndicadorCard from "../components/IndicadorCard";
import { puedeRetroceder } from "../lib/acciones";

const INDICADOR_VACIO = { nombre: "", formula: "", unidad: "", periodicidad: "mensual", tipo: "institucional", meta: "" };

export default function PracticaDetalle() {
  const { id } = useParams();
  const { sesion, tieneRol } = useAuth();
  const catalogos = useApi<Catalogos>("/api/catalogos/");
  const practica = useApi<Practica>(`/api/practicas/${id}/`);
  const indicadores = useApi<Page<Indicador>>(`/api/indicadores/?practica=${id}&page_size=100`);
  const mediciones = useApi<Page<Medicion>>(`/api/mediciones/?practica=${id}&page_size=100`);
  const [error, setError] = useState<string | null>(null);
  const [nuevo, setNuevo] = useState(INDICADOR_VACIO);
  const [pendiente, setPendiente] = useState(false);
  const [motivo, setMotivo] = useState("");

  function recargar() {
    practica.recargar();
    indicadores.recargar();
    mediciones.recargar();
  }

  if (practica.error) {
    return (
      <p role="alert" className="error">
        {practica.error}
      </p>
    );
  }
  if (!practica.data) return <p>Cargando…</p>;

  const p = practica.data;
  const puedeEscribir = tieneRol(p.facultad, "responsable");
  const siguiente = catalogos.data?.estados[ESTADOS.indexOf(p.estado) + 1];

  // Un clic doble no puede saltar dos niveles: se manda el estado que se ve y se bloquea el botón mientras espera.
  async function promover() {
    setError(null);
    setPendiente(true);
    try {
      await api(`/api/practicas/${p.id}/promover/`, { method: "POST", body: { desde: p.estado } });
      recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setPendiente(false);
    }
  }

  async function retroceder() {
    setError(null);
    setPendiente(true);
    try {
      await api(`/api/practicas/${p.id}/retroceder/`, { method: "POST", body: { motivo: motivo.trim() } });
      setMotivo("");
      recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    } finally {
      setPendiente(false);
    }
  }

  async function asumirResponsabilidad() {
    setError(null);
    try {
      await api(`/api/practicas/${p.id}/`, { method: "PATCH", body: { responsable: sesion?.id } });
      recargar();
    } catch (e) {
      setError(mensajeDeError(e));
    }
  }

  async function crearIndicador(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/api/indicadores/", {
        method: "POST",
        body: { practica: p.id, ...nuevo, meta: nuevo.meta === "" ? null : nuevo.meta },
      });
      setNuevo(INDICADOR_VACIO);
      recargar();
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  return (
    <>
      <p>
        <Link to="/practicas">← Prácticas</Link>
      </p>
      <h1>
        {p.nombre} <EstadoBadge estado={p.estado} /> {p.origen === "ilustrativa" && <IlustrativoBadge />}
      </h1>
      <p className="nota">
        {p.facultad_nombre} · {p.dimension} · Responsable: {p.responsable_nombre ?? "sin asignar"}
      </p>
      {p.proposito && <p>{p.proposito}</p>}

      {puedeEscribir && (
        <p className="fila">
          {siguiente && (
            <button type="button" disabled={pendiente} onClick={promover}>
              Promover a {siguiente.etiqueta}
            </button>
          )}
          {p.responsable === null && (
            <button type="button" className="secundario" onClick={asumirResponsabilidad}>
              Asumir la responsabilidad
            </button>
          )}
        </p>
      )}
      {puedeRetroceder(sesion, p.estado) && (
        <p className="fila">
          <label>
            Motivo del retroceso
            <input value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </label>
          <button type="button" className="secundario" disabled={pendiente || motivo.trim() === ""} onClick={retroceder}>
            Retroceder
          </button>
        </p>
      )}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}

      <h2>Indicadores</h2>
      {indicadores.data?.results.length === 0 && <p>Esta práctica todavía no tiene indicadores.</p>}
      {indicadores.data?.results.map((ind) => (
        <IndicadorCard
          key={ind.id}
          indicador={ind}
          mediciones={mediciones.data?.results.filter((m) => m.indicador === ind.id) ?? []}
          puedeEscribir={puedeEscribir}
          onCambio={recargar}
        />
      ))}

      {puedeEscribir && (
        <details className="tarjeta">
          <summary>Nuevo indicador</summary>
          <form onSubmit={crearIndicador} className="formulario" style={{ marginTop: "0.75rem" }}>
            <label>
              Nombre
              <input value={nuevo.nombre} onChange={(e) => setNuevo({ ...nuevo, nombre: e.target.value })} required />
            </label>
            <label>
              Fórmula
              <input value={nuevo.formula} onChange={(e) => setNuevo({ ...nuevo, formula: e.target.value })} required />
            </label>
            <label>
              Unidad
              <input value={nuevo.unidad} onChange={(e) => setNuevo({ ...nuevo, unidad: e.target.value })} required />
            </label>
            <label>
              Periodicidad
              <select value={nuevo.periodicidad} onChange={(e) => setNuevo({ ...nuevo, periodicidad: e.target.value })}>
                {catalogos.data?.periodicidades.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.etiqueta}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Tipo
              <select value={nuevo.tipo} onChange={(e) => setNuevo({ ...nuevo, tipo: e.target.value })}>
                {catalogos.data?.tipos_indicador.map((o) => (
                  <option key={o.valor} value={o.valor}>
                    {o.etiqueta}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Meta (opcional)
              <input type="number" step="any" value={nuevo.meta} onChange={(e) => setNuevo({ ...nuevo, meta: e.target.value })} />
            </label>
            <button type="submit">Crear indicador</button>
          </form>
        </details>
      )}
    </>
  );
}
