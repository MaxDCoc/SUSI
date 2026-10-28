import { type ChangeEvent, type FormEvent, useState } from "react";

import { api, mensajeDeError } from "../api/client";

interface Props {
  medicionId: number;
  onCreada: () => void;
  onCancelar: () => void;
}

// Mismo máximo que valida el servidor (backend/evidence/validators.py). Se avisa al elegir el archivo para que
// nadie tenga que esperar a que termine de subirse para enterarse de que no entra.
const TAMANO_MAXIMO = 2 * 1024 * 1024;

// Se redondea hacia arriba para que un archivo apenas pasado del límite no se lea como "pesa 2 MB".
const enMegas = (bytes: number) =>
  (Math.ceil((bytes / (1024 * 1024)) * 10) / 10).toLocaleString("es-AR", { maximumFractionDigits: 1 });

export default function EvidenciaForm({ medicionId, onCreada, onCancelar }: Props) {
  const [tipo, setTipo] = useState<"enlace" | "archivo">("enlace");
  const [url, setUrl] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const demasiadoGrande = tipo === "archivo" && archivo !== null && archivo.size > TAMANO_MAXIMO;

  function elegirTipo(nuevo: "enlace" | "archivo") {
    setTipo(nuevo);
    setError(null);
  }

  function elegirArchivo(e: ChangeEvent<HTMLInputElement>) {
    const elegido = e.target.files?.[0] ?? null;
    setArchivo(elegido);
    setError(
      elegido && elegido.size > TAMANO_MAXIMO ? `El archivo supera el máximo de 2 MB (pesa ${enMegas(elegido.size)} MB).` : null,
    );
  }

  async function enviar(e: FormEvent) {
    e.preventDefault();
    if (demasiadoGrande) return;
    setError(null);
    setEnviando(true);
    try {
      const datos = new FormData();
      datos.append("medicion", String(medicionId));
      datos.append("tipo", tipo);
      datos.append("descripcion", descripcion);
      if (tipo === "enlace") datos.append("url", url);
      else if (archivo) datos.append("archivo", archivo);
      await api("/api/evidencias/", { method: "POST", body: datos });
      onCreada();
    } catch (err) {
      setError(mensajeDeError(err));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <form onSubmit={enviar} className="evidencia-form">
      <select value={tipo} onChange={(e) => elegirTipo(e.target.value as "enlace" | "archivo")} aria-label="Tipo de evidencia">
        <option value="enlace">Enlace</option>
        <option value="archivo">Archivo (PDF, PNG o JPG, máx. 2 MB)</option>
      </select>
      {tipo === "enlace" ? (
        <input type="url" required placeholder="https://…" value={url} onChange={(e) => setUrl(e.target.value)} />
      ) : (
        <input
          type="file"
          required
          accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
          onChange={elegirArchivo}
        />
      )}
      <input placeholder="Descripción" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      <div className="fila">
        <button type="submit" disabled={enviando || demasiadoGrande}>
          {enviando ? "Subiendo…" : "Subir evidencia"}
        </button>
        <button type="button" className="secundario" onClick={onCancelar} disabled={enviando}>
          Cancelar
        </button>
      </div>
      {enviando && tipo === "archivo" && <p className="nota">Subiendo el archivo, puede tardar unos segundos.</p>}
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </form>
  );
}
