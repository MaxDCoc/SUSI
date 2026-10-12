import { lazy, Suspense, useMemo, useState } from "react";

import type { Catalogos, GrupoResumen, Resumen } from "../api/types";
import { useApi } from "../api/useApi";
import { barrasApiladasOption, embudoOption } from "../charts/options";

const Chart = lazy(() => import("../charts/Chart"));

function Grafico({ titulo, option, alto }: { titulo: string; option: Record<string, unknown>; alto?: number }) {
  return (
    <section className="tarjeta">
      <h2 className="grafico-titulo">{titulo}</h2>
      <Suspense fallback={<p>Cargando gráfico…</p>}>
        <Chart option={option} etiqueta={titulo} alto={alto} />
      </Suspense>
    </section>
  );
}

const altoPara = (grupos: GrupoResumen[]) => Math.max(160, 60 + grupos.length * 28);

export default function Tablero() {
  const catalogos = useApi<Catalogos>("/api/catalogos/");
  const [region, setRegion] = useState("");
  const [facultad, setFacultad] = useState("");
  const [dimension, setDimension] = useState("");
  const [ods, setOds] = useState("");

  const params = new URLSearchParams();
  if (region) params.set("region", region);
  if (facultad) params.set("facultad", facultad);
  if (dimension) params.set("dimension", dimension);
  if (ods) params.set("ods", ods);
  const resumen = useApi<Resumen>(`/api/dashboard/resumen/?${params}`);
  const datos = resumen.data;

  const opciones = useMemo(
    () =>
      datos && {
        embudo: embudoOption(datos.embudo),
        facultad: barrasApiladasOption(datos.por_facultad),
        region: barrasApiladasOption(datos.por_region),
        dimension: barrasApiladasOption(datos.por_dimension),
        ods: barrasApiladasOption(datos.por_ods),
      },
    [datos],
  );

  return (
    <>
      <h1>Tablero comparable</h1>
      <div className="filtros">
        <label>
          Región
          <select value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="">Todas</option>
            {catalogos.data?.regiones.map((r) => (
              <option key={r.id} value={r.id}>
                {r.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Facultad
          <select value={facultad} onChange={(e) => setFacultad(e.target.value)}>
            <option value="">Todas</option>
            {catalogos.data?.facultades.map((f) => (
              <option key={f.id} value={f.id}>
                {f.nombre}
              </option>
            ))}
          </select>
        </label>
        <label>
          Dimensión
          <select value={dimension} onChange={(e) => setDimension(e.target.value)}>
            <option value="">Todas</option>
            {catalogos.data?.dimensiones.map((o) => (
              <option key={o.valor} value={o.valor}>
                {o.etiqueta}
              </option>
            ))}
          </select>
        </label>
        <label>
          ODS
          <select value={ods} onChange={(e) => setOds(e.target.value)}>
            <option value="">Todos</option>
            {catalogos.data?.ods.map((o) => (
              <option key={o.numero} value={o.numero}>
                ODS {o.numero}
              </option>
            ))}
          </select>
        </label>
      </div>

      {resumen.error && (
        <p role="alert" className="error">
          {resumen.error}
        </p>
      )}
      {datos && opciones && (
        <>
          {datos.ilustrativas > 0 && (
            <p className="nota">
              {datos.ilustrativas} de {datos.total_practicas} prácticas son datos ilustrativos (ejemplos inspirados en
              el relevamiento, no cargados por las facultades).
            </p>
          )}
          <div className="grilla">
            <div className="tarjeta kpi">
              <strong>{datos.total_practicas}</strong>
              <span>Prácticas registradas</span>
            </div>
            <div className="tarjeta kpi">
              <strong>{datos.kpis.con_responsable.porcentaje}%</strong>
              <span>Con responsable ({datos.kpis.con_responsable.cantidad})</span>
            </div>
            <div className="tarjeta kpi">
              <strong>{datos.kpis.con_indicador.porcentaje}%</strong>
              <span>Con indicador ({datos.kpis.con_indicador.cantidad})</span>
            </div>
            <div className="tarjeta kpi">
              <strong>{datos.kpis.con_evidencia_validada.porcentaje}%</strong>
              <span>Con evidencia validada ({datos.kpis.con_evidencia_validada.cantidad})</span>
            </div>
            <div className="tarjeta kpi">
              <strong>
                {datos.cobertura.facultades_con_practicas} / {datos.cobertura.facultades_total}
              </strong>
              <span>Facultades con prácticas cargadas</span>
            </div>
          </div>

          {datos.total_practicas === 0 ? (
            <p>No hay prácticas con esos filtros.</p>
          ) : (
            <>
              <Grafico titulo="Embudo de madurez (prácticas que alcanzaron cada estado)" option={opciones.embudo} />
              <Grafico titulo="Por región" option={opciones.region} alto={altoPara(datos.por_region)} />
              <Grafico titulo="Por dimensión" option={opciones.dimension} alto={altoPara(datos.por_dimension)} />
              <Grafico titulo="Por facultad" option={opciones.facultad} alto={altoPara(datos.por_facultad)} />
              <Grafico titulo="Por ODS" option={opciones.ods} alto={altoPara(datos.por_ods)} />
            </>
          )}
        </>
      )}
    </>
  );
}
