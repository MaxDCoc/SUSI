import { describe, expect, it } from "vitest";

import type { GrupoResumen } from "../api/types";
import { barrasApiladasOption, embudoOption, ETIQUETAS_ESTADO } from "./options";

describe("embudoOption", () => {
  it("acumula: cada etapa cuenta las prácticas que alcanzaron al menos ese estado", () => {
    const option = embudoOption({ identificada: 5, formalizada: 3, medida: 2, optimizada: 1 });

    const datos = (option.series as { data: { name: string; value: number }[] }[])[0].data;
    expect(datos.map((d) => d.value)).toEqual([11, 6, 3, 1]);
    expect(datos.map((d) => d.name)).toEqual(["Identificada", "Formalizada", "Medida", "Optimizada"]);
  });

  it("con todo en cero devuelve ceros sin fallar", () => {
    const option = embudoOption({ identificada: 0, formalizada: 0, medida: 0, optimizada: 0 });

    const datos = (option.series as { data: { value: number }[] }[])[0].data;
    expect(datos.map((d) => d.value)).toEqual([0, 0, 0, 0]);
  });
});

describe("barrasApiladasOption", () => {
  const grupos: GrupoResumen[] = [
    { clave: 1, etiqueta: "Mendoza", total: 3, identificada: 1, formalizada: 1, medida: 1, optimizada: 0 },
    { clave: 2, etiqueta: "Delta", total: 2, identificada: 0, formalizada: 2, medida: 0, optimizada: 0 },
  ];

  it("arma una serie apilada por estado y una categoría por grupo (el primero queda arriba)", () => {
    const option = barrasApiladasOption(grupos);

    expect((option.yAxis as { data: string[] }).data).toEqual(["Delta", "Mendoza"]);
    const series = option.series as { name: string; stack: string; data: number[] }[];
    expect(series.map((s) => s.name)).toEqual(Object.values(ETIQUETAS_ESTADO));
    expect(series.every((s) => s.stack === "total")).toBe(true);
    expect(series[1].data).toEqual([2, 1]); // formalizada: Delta, Mendoza
  });
});
