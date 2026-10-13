import type { Estado, GrupoResumen } from "../api/types";
import { ESTADOS } from "../api/types";

export const ETIQUETAS_ESTADO: Record<Estado, string> = {
  identificada: "Identificada",
  formalizada: "Formalizada",
  medida: "Medida",
  optimizada: "Optimizada",
};

// Escalera de madurez de menos a más: los mismos tonos que las insignias (--n1…--n4 en index.css).
export const COLORES_ESTADO: Record<Estado, string> = {
  identificada: "#a9c2b7",
  formalizada: "#6fa896",
  medida: "#1f7d66",
  optimizada: "#0a4d3f",
};

// Color del texto sobre cada tono, con contraste de al menos 4,5:1.
const TEXTO_SOBRE: Record<Estado, string> = {
  identificada: "#10222b",
  formalizada: "#10222b",
  medida: "#ffffff",
  optimizada: "#ffffff",
};

const FUENTE = "IBM Plex Sans Variable, Segoe UI, system-ui, sans-serif";
const TINTA = "#14262f";
const SUAVE = "#4f636b";
const LINEA = "#d8e1de";

type Option = Record<string, unknown>;

const tooltip = (extra: Option = {}): Option => ({
  backgroundColor: "#ffffff",
  borderColor: LINEA,
  borderWidth: 1,
  padding: [8, 12],
  textStyle: { color: TINTA, fontFamily: FUENTE, fontSize: 13 },
  ...extra,
});

/** Embudo acumulativo: cada etapa suma las prácticas que alcanzaron al menos ese estado. */
export function embudoOption(embudo: Record<Estado, number>): Option {
  const data = ESTADOS.map((estado, i) => ({
    name: ETIQUETAS_ESTADO[estado],
    value: ESTADOS.slice(i).reduce((suma, e) => suma + embudo[e], 0),
    itemStyle: { color: COLORES_ESTADO[estado], borderWidth: 0 },
    label: { color: TEXTO_SOBRE[estado] },
  }));
  return {
    textStyle: { fontFamily: FUENTE },
    tooltip: tooltip({ trigger: "item", formatter: "{b}: {c} prácticas" }),
    series: [
      {
        type: "funnel",
        sort: "none",
        left: "6%",
        width: "88%",
        top: 8,
        bottom: 8,
        // Los anchos son proporcionales a la primera etapa; el mínimo deja entrar el texto de las últimas.
        min: 0,
        max: Math.max(1, data[0].value),
        minSize: "32%",
        gap: 4,
        label: { show: true, position: "inside", formatter: "{b}: {c}", fontSize: 14, fontWeight: 600 },
        data,
      },
    ],
  };
}

export function barrasApiladasOption(grupos: GrupoResumen[]): Option {
  const orden = [...grupos].reverse(); // en barras horizontales el primero queda abajo
  return {
    textStyle: { fontFamily: FUENTE, color: SUAVE },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow", shadowStyle: { color: "rgba(16, 34, 43, 0.05)" } } }),
    legend: {
      data: ESTADOS.map((e) => ETIQUETAS_ESTADO[e]),
      top: 0,
      icon: "roundRect",
      itemWidth: 12,
      itemHeight: 12,
      itemGap: 18,
      textStyle: { color: TINTA, fontSize: 13 },
    },
    grid: { left: 150, right: 20, top: 40, bottom: 20 },
    xAxis: {
      type: "value",
      minInterval: 1,
      axisLabel: { color: SUAVE },
      splitLine: { lineStyle: { color: "#e4ebe8" } },
    },
    yAxis: {
      type: "category",
      data: orden.map((g) => g.etiqueta),
      axisTick: { show: false },
      axisLine: { lineStyle: { color: LINEA } },
      axisLabel: { color: TINTA },
    },
    series: ESTADOS.map((estado) => ({
      name: ETIQUETAS_ESTADO[estado],
      type: "bar",
      stack: "total",
      barMaxWidth: 26,
      itemStyle: { color: COLORES_ESTADO[estado] },
      emphasis: { focus: "series" },
      data: orden.map((g) => g[estado]),
    })),
  };
}
