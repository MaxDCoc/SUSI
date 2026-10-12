import { type FormEvent, useState } from "react";

import { api, mensajeDeError } from "../api/client";
import type { Indicador, Medicion } from "../api/types";
import MedicionRow from "./MedicionRow";

interface Props {
  indicador: Indicador;
  mediciones: Medicion[];
  puedeEscribir: boolean;
  onCambio: () => void;
}

export default function IndicadorCard({ indicador, mediciones, puedeEscribir, onCambio }: Props) {
  const [periodo, setPeriodo] = useState("");
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function cargar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api("/api/mediciones/", { method: "POST", body: { indicador: indicador.id, periodo, valor } });
      setPeriodo("");
      setValor("");
      onCambio();
    } catch (err) {
      setError(mensajeDeError(err));
    }
  }

  return (
    <article className="tarjeta">
      <h3>
        {indicador.nombre} <small>({indicador.unidad}, {indicador.periodicidad})</small>
      </h3>
      <p className="nota">{indicador.formula}</p>
      {indicador.meta !== null && (
        <p>
          Meta: {Number(indicador.meta)} {indicador.unidad}
        </p>
      )}
      {mediciones.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Período</th>
              <th>Valor</th>
              <th>Estado</th>
              <th>Evidencias</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {mediciones.map((m) => (
              <MedicionRow key={m.id} medicion={m} puedeEscribir={puedeEscribir} onCambio={onCambio} />
            ))}
          </tbody>
        </table>
      )}
      {puedeEscribir && (
        <form onSubmit={cargar} className="fila" style={{ marginTop: "0.75rem" }}>
          <label>
            Período
            <input type="month" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required />
          </label>
          <label>
            Valor ({indicador.unidad})
            <input type="number" step="any" value={valor} onChange={(e) => setValor(e.target.value)} required />
          </label>
          <button type="submit">Cargar medición</button>
        </form>
      )}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </article>
  );
}
