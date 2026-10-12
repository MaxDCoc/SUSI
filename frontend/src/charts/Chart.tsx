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

export default function Chart({ option, alto = 320, etiqueta }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    const grafico = echarts.init(ref.current);
    grafico.setOption(option as echarts.EChartsCoreOption);
    const ajustar = () => grafico.resize();
    window.addEventListener("resize", ajustar);
    return () => {
      window.removeEventListener("resize", ajustar);
      grafico.dispose();
    };
  }, [option]);

  return <div ref={ref} style={{ height: alto }} role="img" aria-label={etiqueta} />;
}
