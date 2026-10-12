import { type FormEvent, useState } from "react";

import { api, mensajeDeError } from "../api/client";

interface Props {
  medicionId: number;
  onCreada: () => void;
}

export default function EvidenciaForm({ medicionId, onCreada }: Props) {
  const [tipo, setTipo] = useState<"enlace" | "archivo">("enlace");
  const [url, setUrl] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [archivo, setArchivo] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
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
    }
  }

  return (
    <form onSubmit={enviar} className="evidencia-form">
      <select value={tipo} onChange={(e) => setTipo(e.target.value as "enlace" | "archivo")} aria-label="Tipo de evidencia">
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
          onChange={(e) => setArchivo(e.target.files?.[0] ?? null)}
        />
      )}
      <input placeholder="Descripción" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} />
      <button type="submit">Subir evidencia</button>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </form>
  );
}
