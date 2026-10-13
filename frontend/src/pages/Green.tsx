import type { MuestrasRespuesta, SciRespuesta } from "../api/types";
import { useApi } from "../api/useApi";

const DECISIONES = [
  "Paginación y filtros del lado del servidor (20 filas por página).",
  "Agregados del tablero en caché, invalidados solo cuando cambian los datos.",
  "Gráficos con carga diferida: ECharts no se descarga hasta abrir el tablero.",
  "Sin polling: la información se pide cuando el usuario actúa.",
  "Respuestas comprimidas (gzip) y bundle de React acotado.",
  "Monolito modular en dos contenedores (principio de menor complejidad operacional).",
];

const fmt = (n: number, decimales = 4) => n.toLocaleString("es-AR", { maximumFractionDigits: decimales });

export default function Green() {
  const sci = useApi<SciRespuesta>("/api/green/sci/");
  const muestras = useApi<MuestrasRespuesta>("/api/green/muestras/");
  const datos = sci.data;

  return (
    <>
      <h1>Green Software: SCI de SUSI</h1>
      {sci.error && (
        <p role="alert" className="error">
          {sci.error}
        </p>
      )}
      {datos && (
        <>
          <p className="aviso">{datos.aviso}</p>

          <section className="tarjeta kpi">
            {datos.sci ? (
              <>
                <strong>{fmt(datos.sci.sci_g_por_1000_ops)} gCO₂e</strong>
                <span>
                  por cada {datos.unidad_funcional.descripcion.toLowerCase()} (estimado sobre {datos.sci.n_operaciones}{" "}
                  operaciones medidas)
                </span>
                <p className="nota">
                  SCI = ((E × I) + M) / R · E = {fmt(datos.sci.e_kwh, 8)} kWh · M = {fmt(datos.sci.m_g, 6)} gCO₂e · R ={" "}
                  {fmt(datos.sci.r_unidades, 4)} unidades funcionales
                </p>
              </>
            ) : (
              <p>{datos.motivo}</p>
            )}
          </section>

          {datos.parametros && (
            <section className="tarjeta">
              <h2>Supuestos (versión {datos.parametros.version})</h2>
              <ul>
                <li>Potencia de CPU: {datos.parametros.potencia_cpu_w} W</li>
                <li>
                  Intensidad de carbono: {datos.parametros.intensidad_carbono_g_kwh} gCO₂e/kWh. Fuente:{" "}
                  {datos.parametros.fuente_intensidad} ({datos.parametros.fecha_intensidad})
                </li>
                <li>
                  Emisiones incorporadas TE: {datos.parametros.te_g} gCO₂e · vida útil EL: {datos.parametros.el_horas} h ·
                  RS/TR: {datos.parametros.rs}/{datos.parametros.tr}
                </li>
                {datos.parametros.supuestos && <li>{datos.parametros.supuestos}</li>}
              </ul>
            </section>
          )}

          <section className="tarjeta">
            <h2>Unidad funcional</h2>
            <p>
              R = {datos.unidad_funcional.descripcion}. Operaciones del flujo núcleo:{" "}
              {datos.unidad_funcional.operaciones.join(", ")}.
            </p>
          </section>
        </>
      )}

      <section className="tarjeta">
        <h2>Costo por operación (promedios medidos)</h2>
        {muestras.data && muestras.data.operaciones.length > 0 ? (
          <div className="tabla">
            <table>
              <thead>
                <tr>
                  <th>Operación</th>
                  <th>Muestras</th>
                  <th>CPU (ms)</th>
                  <th>Tiempo (ms)</th>
                  <th>Bytes</th>
                  <th>Consultas SQL</th>
                </tr>
              </thead>
              <tbody>
                {muestras.data.operaciones.map((o) => (
                  <tr key={o.operacion}>
                    <td>{o.operacion}</td>
                    <td>{o.n}</td>
                    <td>{fmt(o.cpu_ms_prom, 2)}</td>
                    <td>{fmt(o.wall_ms_prom, 2)}</td>
                    <td>{fmt(o.bytes_prom, 0)}</td>
                    <td>{fmt(o.consultas_prom, 1)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p>Todavía no hay muestras: usá la aplicación y volvé a esta pantalla.</p>
        )}
      </section>

      <section className="tarjeta">
        <h2>Decisiones de Green Software aplicadas a SUSI</h2>
        <ul>
          {DECISIONES.map((d) => (
            <li key={d}>{d}</li>
          ))}
        </ul>
      </section>
    </>
  );
}
