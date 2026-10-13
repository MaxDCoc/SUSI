import { BarChart, FunnelChart } from "echarts/charts";
import { GridComponent, LegendComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { useEffect, useRef } from "react";

// Solo se registran las piezas que se usan (bundle más chico).
echarts.use([BarChart, FunnelChart, GridComponent, LegendComponent, TooltipComponent, CanvasRenderer]);

interface Props {
  option: Record<string, unknown>;
  alto?: number;
  etiqueta: string;
}

const ANGOSTO = 520;

// En pantallas angostas las etiquetas largas se truncan y las barras ganan el ancho que necesitan.
function adaptar(option: Record<string, unknown>, ancho: number): Record<string, unknown> {
  if (ancho >= ANGOSTO || !option.yAxis) return option;
  const yAxis = option.yAxis as Record<string, unknown>;
  return {
    ...option,
    grid: { ...(option.grid as Record<string, unknown>), left: 8, right: 16, top: 64, containLabel: true },
    yAxis: { ...yAxis, axisLabel: { ...(yAxis.axisLabel as Record<string, unknown>), width: 110, overflow: "truncate" } },
  };
}

export default function Chart({ option, alto = 320, etiqueta }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const contenedor = ref.current;
    if (!contenedor) return;
    const grafico = echarts.init(contenedor);
    const dibujar = () => grafico.setOption(adaptar(option, contenedor.clientWidth) as echarts.EChartsCoreOption, true);
    dibujar();
    const ajustar = () => {
      dibujar();
      grafico.resize();
    };
    window.addEventListener("resize", ajustar);
    return () => {
      window.removeEventListener("resize", ajustar);
      grafico.dispose();
    };
  }, [option]);

  return <div ref={ref} style={{ height: alto }} role="img" aria-label={etiqueta} />;
}
