export type Rol = "responsable" | "validador";
export type Estado = "identificada" | "formalizada" | "medida" | "optimizada";
export type EstadoMedicion = "borrador" | "enviada" | "validada" | "rechazada";
export type Dimension = "ambiental" | "social" | "economica" | "institucional";

export const ESTADOS: Estado[] = ["identificada", "formalizada", "medida", "optimizada"];

export interface Membresia {
  facultad: number;
  facultad_nombre: string;
  rol: Rol;
}

export interface Sesion {
  authenticated: boolean;
  id?: number;
  username?: string;
  es_admin?: boolean;
  membresias: Membresia[];
}

export interface Opcion {
  valor: string;
  etiqueta: string;
}

export interface Catalogos {
  regiones: { id: number; nombre: string }[];
  facultades: { id: number; nombre: string; region_id: number; es_nivel_central: boolean }[];
  ods: { numero: number; nombre: string }[];
  dimensiones: Opcion[];
  estados: Opcion[];
  periodicidades: Opcion[];
  tipos_indicador: Opcion[];
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface Practica {
  id: number;
  facultad: number;
  facultad_nombre: string;
  nombre: string;
  dimension: Dimension;
  estado: Estado;
  proposito: string;
  ods: number[];
  alcance: string;
  actividades: string;
  frecuencia: string;
  responsable: number | null;
  responsable_nombre: string | null;
  origen: "cargada" | "ilustrativa";
  creado_en: string;
  actualizado_en: string;
}

export interface Indicador {
  id: number;
  practica: number;
  nombre: string;
  formula: string;
  unidad: string;
  periodicidad: string;
  tipo: string;
  fuente: string;
  linea_base: string | null;
  meta: string | null;
  tolerancia: string | null;
  referencia_estandar: string;
}

export interface EvidenciaResumen {
  id: number;
  tipo: "archivo" | "enlace";
  url: string;
  descripcion: string;
  archivo_descarga: string | null;
  creado_por_nombre: string;
  creado_en: string;
}

export interface Medicion {
  id: number;
  indicador: number;
  indicador_nombre: string;
  unidad: string;
  practica_id: number;
  practica_nombre: string;
  practica_origen: "cargada" | "ilustrativa";
  facultad_id: number;
  facultad_nombre: string;
  periodo: string;
  valor: string;
  estado: EstadoMedicion;
  cargado_por: number;
  cargado_por_nombre: string;
  validado_por: number | null;
  validado_por_nombre: string | null;
  validado_en: string | null;
  comentario_validacion: string;
  evidencias: EvidenciaResumen[];
  n_evidencias: number;
}

export interface GrupoResumen {
  clave: number | string;
  etiqueta: string;
  total: number;
  identificada: number;
  formalizada: number;
  medida: number;
  optimizada: number;
}

export interface Kpi {
  cantidad: number;
  porcentaje: number;
}

export interface Resumen {
  total_practicas: number;
  ilustrativas: number;
  kpis: { con_responsable: Kpi; con_indicador: Kpi; con_evidencia_validada: Kpi };
  cobertura: { facultades_con_practicas: number; facultades_total: number; porcentaje: number };
  embudo: Record<Estado, number>;
  por_facultad: GrupoResumen[];
  por_region: GrupoResumen[];
  por_dimension: GrupoResumen[];
  por_ods: GrupoResumen[];
}

export interface ParametroSCI {
  id: number;
  version: number;
  potencia_cpu_w: string;
  intensidad_carbono_g_kwh: string;
  fuente_intensidad: string;
  fecha_intensidad: string;
  te_g: string;
  el_horas: string;
  rs: string;
  tr: string;
  supuestos: string;
}

export interface SciResultado {
  sci_g_por_1000_ops: number;
  e_kwh: number;
  m_g: number;
  n_operaciones: number;
  r_unidades: number;
}

export interface SciRespuesta {
  unidad_funcional: { ops: number; descripcion: string; operaciones: string[] };
  estimacion: boolean;
  aviso: string;
  parametros: ParametroSCI | null;
  sci: SciResultado | null;
  motivo: string | null;
}

export interface OperacionResumen {
  operacion: string;
  n: number;
  cpu_ms_prom: number;
  wall_ms_prom: number;
  bytes_prom: number;
  consultas_prom: number;
}

export interface MuestrasRespuesta {
  total: number;
  operaciones: OperacionResumen[];
}
