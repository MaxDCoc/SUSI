import { useEffect, useState } from "react";

import { api, mensajeDeError } from "./client";

export function useApi<T>(ruta: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (!ruta) return;
    let activo = true;
    setCargando(true);
    api<T>(ruta)
      .then((d) => {
        if (activo) {
          setData(d);
          setError(null);
        }
      })
      .catch((e) => {
        if (activo) setError(mensajeDeError(e));
      })
      .finally(() => {
        if (activo) setCargando(false);
      });
    return () => {
      activo = false;
    };
  }, [ruta, version]);

  return { data, error, cargando, recargar: () => setVersion((v) => v + 1) };
}
