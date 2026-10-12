import type { Estado, GrupoResumen } from "../api/types";
import { ESTADOS } from "../api/types";

export const ETIQUETAS_ESTADO: Record<Estado, string> = {
  identificada: "Identificada",
  formalizada: "Formalizada",
  medida: "Medida",
  optimizada: "Optimizada",
};

export const COLORES_ESTADO: Record<Estado, string> = {
  identificada: "#9fb3a8",
  formalizada: "#6f9ed6",
  medida: "#4a9d73",
  optimizada: "#1f6b4a",
};

type Option = Record<string, unknown>;

/** Embudo acumulativo: cada etapa suma las prácticas que alcanzaron al menos ese estado. */
export function embudoOption(embudo: Record<Estado, number>): Option {
  const data = ESTADOS.map((estado, i) => ({
    name: ETIQUETAS_ESTADO[estado],
    value: ESTADOS.slice(i).reduce((suma, e) => suma + embudo[e], 0),
    itemStyle: { color: COLORES_ESTADO[estado] },
  }));
  return {
    tooltip: { trigger: "item", formatter: "{b}: {c} prácticas" },
    series: [
      {
        type: "funnel",
        sort: "none",
        left: "8%",
        width: "84%",
        gap: 4,
        label: { show: true, position: "inside", formatter: "{b}: {c}" },
        data,
      },
    ],
  };
}

export function barrasApiladasOption(grupos: GrupoResumen[]): Option {
  const orden = [...grupos].reverse(); // en barras horizontales el primero queda abajo
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { data: ESTADOS.map((e) => ETIQUETAS_ESTADO[e]) },
    grid: { left: 150, right: 20, top: 40, bottom: 20 },
    xAxis: { type: "value", minInterval: 1 },
    yAxis: { type: "category", data: orden.map((g) => g.etiqueta) },
    series: ESTADOS.map((estado) => ({
      name: ETIQUETAS_ESTADO[estado],
      type: "bar",
      stack: "total",
      itemStyle: { color: COLORES_ESTADO[estado] },
      data: orden.map((g) => g[estado]),
    })),
  };
}
