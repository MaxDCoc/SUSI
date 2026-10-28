# SUSI MVP — Diseño

Fecha: 2026-10-12 · Demo: miércoles 2026-10-14, ~10:00 · Autor: Maximiliano Cocito

## 1. Objetivo y criterio de éxito

Construir una app web funcional que muestre en vivo una rebanada delgada del framework SUSI
(paper "SUSI: Hacia un framework de sistematización de prácticas sostenibles en la Universidad").

El MVP es exitoso si, en la demo, se recorre sin trabas este flujo:

1. Un **Responsable** crea una práctica sostenible y le asocia un indicador.
2. Carga una **medición** con **evidencia** adjunta.
3. Un **Validador** (distinto de quien cargó) la valida.
4. El **tablero** se actualiza y permite comparar facultades.
5. El **panel Green Software** muestra el SCI estimado de ese mismo flujo.

Supuesto: el público es el grupo de investigación y autoridades de UTN (no confirmado).

## 2. Alcance

Entra (requisitos del paper, sección 4.4):

| Req. | Descripción | Estado |
|---|---|---|
| R1 | Catálogo único y normalizado de prácticas | Núcleo |
| R3 | Metamodelo de indicadores | Núcleo |
| R4 | Evidencias y trazabilidad de cambios | Núcleo |
| R2 | Roles y workflow de validación | Incluido |
| R5 | Tableros comparables por facultad, región, dimensión y ODS | Incluido |
| R7 | Observabilidad ambiental del propio software (SCI) | Incluido |

Fuera de alcance (trabajo siguiente): pantalla de importación/exportación (R6; solo existe un comando de
carga inicial), mapeo a indicadores UI GreenMetric 2026, Impact Framework, diferir cargas según intensidad
de carbono, SSO de UTN, versión móvil, internacionalización.

Principios del paper que condicionan el diseño: **madurez incremental** (una práctica puede existir sin
indicadores), **mínimo dato suficiente** (no pedir campos que no alimenten una decisión o indicador),
**evidencia antes que declaración**, y **Green Software como criterio de diseño**.

## 3. Stack y despliegue

- Backend: Python, **Django + Django REST Framework**, PostgreSQL 16.
- Frontend: React + Vite + TypeScript, ECharts para gráficos.
- Librerías Django: `django-guardian` (permisos por objeto), `django-simple-history` (historial de cambios),
  `whitenoise` (sirve el build de React y estáticos con compresión).
- Autenticación: sesión de Django con CSRF (misma origin que el SPA; sin JWT).
- Empaquetado: **Docker Compose con dos contenedores**: `db` (Postgres) y `app` (Django + SPA compilado).
  Desarrollo: servidor de Vite con proxy a Django.
- Demo: local con Docker Compose. Deploy público (Railway/Render) solo si sobra tiempo.
- CI: GitHub Actions con pytest y Semgrep.
- Secretos en variables de entorno; se versiona `.env.example`, nunca `.env`.
- Control de versiones: los commits y pushes los hace el autor con su propia cuenta de GitHub; sin coautores adicionales.

## 4. Arquitectura: monolito modular

El paper (sección 6.2) recomienda empezar por un monolito modular. Apps de Django, cada una con una
responsabilidad:

| App | Responsabilidad | Req. |
|---|---|---|
| `accounts` | Usuarios, roles, pertenencia a facultad | R2 |
| `catalog` | Región, Facultad, Dimensión, ODS, **Práctica** y su estado de madurez | R1 |
| `indicators` | **Indicador** (metamodelo) y **Medición** | R3 |
| `evidence` | **Evidencia** adjunta | R4 |
| `workflow` | Reglas de transición de prácticas y validación de mediciones | R2 |
| `dashboard` | Endpoints de agregación para los tableros | R5 |
| `greenops` | Middleware de medición, muestras, parámetros y cálculo de SCI | R7 |

Las apps se comunican por modelos y servicios importables, no por llamadas HTTP internas.

## 5. Modelo de datos

Campos obligatorios en negrita (mínimo dato suficiente). Fechas en ISO 8601; períodos de medición como `YYYY-MM`.

- **Region**: **nombre**.
- **Facultad**: **nombre**, **region**, `es_nivel_central` (bool). Se precargan
  las 30 Facultades Regionales de UTN y el Rectorado (ver §10).
- **Dimension**: enumeración {ambiental, social, económica, institucional}.
- **ODS**: **numero** (1–17), **nombre**.
- **Practica**: **facultad**, **nombre**, **dimension**, **estado** {identificada, formalizada, medida, optimizada},
  `proposito`, `ods` (M2M), `alcance`, `actividades`, `frecuencia`, `responsable` (usuario),
  `origen` {cargada, ilustrativa}.
- **Indicador**: **practica**, **nombre**, **formula** (texto), **unidad**, **periodicidad** {mensual, trimestral,
  semestral, anual}, **tipo** {institucional, tecnico}, `fuente`, `responsable_datos`, `linea_base`, `meta`,
  `tolerancia`, `referencia_estandar` (ej. "GRI 305").
- **Medicion**: **indicador**, **periodo**, **valor** (decimal), **estado** {borrador, enviada, validada, rechazada},
  **cargado_por**, `validado_por`, `validado_en`, `comentario_validacion`.
- **Evidencia**: pertenece a una **Medicion** o a una **Practica** (al menos una), **tipo** {archivo, enlace},
  `archivo` (solo PDF/PNG/JPG, máx. 2 MB, coherente con la guía de evidencias de GreenMetric) o `url`,
  `descripcion`, **creado_por**.
- **ParametroSCI**: ver §8.
- **MuestraOperacion**: ver §8.

`django-simple-history` registra el historial de **Practica, Indicador, Medicion y Evidencia** (quién cambió qué y cuándo).

## 6. Roles, permisos y reglas de negocio

### Roles
- **Administrador** (Rectorado): ve todo, gestiona catálogos y parámetros SCI, puede validar mediciones de cualquier facultad (también sin poder validar las que él cargó) y puede retroceder el estado de una práctica con motivo.
- **Responsable** (por facultad): crea y edita prácticas, indicadores, mediciones y evidencias **solo de sus facultades**; envía mediciones a validación.
- **Validador** (por facultad): valida o rechaza mediciones de sus facultades. **No puede validar una medición que él mismo cargó.**

Alcance por facultad: `django-guardian` con permisos por objeto. Si resulta inviable en el tiempo disponible, se
reemplaza por un filtro de queryset según la pertenencia del usuario a facultades (mismo comportamiento visible).

### Transiciones de la Medición
`borrador → enviada` (Responsable) · `enviada → validada | rechazada` (Validador) · `rechazada → borrador` ·
`enviada → borrador` (el Responsable la retira mientras nadie la haya revisado).
Un borrador se puede editar y eliminar, junto con sus evidencias y sus archivos; quién la eliminó queda en el historial.
Una medición enviada o validada no se edita ni se elimina (para corregir una validada se registra una nueva).

### Transiciones de la Práctica (validadas en el servidor)
Solo hacia adelante y por acción explícita `promover`:

| Transición | Requisito |
|---|---|
| identificada → formalizada | Tiene `responsable` asignado |
| formalizada → medida | Tiene al menos un indicador con al menos una medición **validada** que tenga al menos una **evidencia** |
| medida → optimizada | El indicador tiene `meta` definida y al menos dos mediciones validadas |

Una práctica puede quedar en *identificada* sin indicador (madurez incremental). El retroceso solo lo hace el
Administrador y queda en el historial.

## 7. API y tablero (R5)

API REST bajo `/api/`, paginada del lado del servidor (tamaño de página por defecto 20):

- Catálogos: `/api/catalogos/` (regiones, facultades, dimensiones, ODS).
- `/api/practicas/` (CRUD + acción `promover`), `/api/indicadores/`, `/api/mediciones/`
  (CRUD + acciones `enviar`, `validar`, `rechazar`), `/api/evidencias/`.
- Tableros (solo lectura, con filtros `facultad`, `region`, `dimension`, `ods`):
  `/api/dashboard/embudo/` (cantidad de prácticas por estado) y `/api/dashboard/resumen/` (KPIs).
- Green: `/api/green/sci/`, `/api/green/muestras/`, `/api/green/parametros/` (escritura solo Administrador).

**Contenido del tablero** (indicadores que el paper propone medir, sección 3.4):
- Embudo identificada → formalizada → medida → optimizada (versión de SUSI de la brecha 96/54/27/19 del paper).
- % de prácticas con responsable, % con indicador, % con evidencia validada, cobertura de prácticas registradas.
- Cobertura institucional: facultades con prácticas cargadas frente al total de 30.
- Comparación por facultad, región, dimensión y ODS. Las agregaciones se cachean con TTL corto.

## 8. Panel Green Software (R7)

### Medición
Un middleware de Django registra por cada operación una `MuestraOperacion`:
`operacion` (nombre lógico, ej. `practica.crear`), `cpu_ms`, `wall_ms`, `bytes_respuesta`, `n_consultas_sql`, `ts`.
Se excluyen las rutas `/api/green/` y los estáticos para no medirse a sí mismo.

### Unidad funcional
**R = 1.000 operaciones del flujo núcleo**: `practica.crear`, `practica.consultar` y `medicion.validar`.
El paper indica que la unidad definitiva debe confirmarse durante la instrumentación; esta es la de partida y se muestra en pantalla.

### Cálculo
`SCI = ((E × I) + M) / R`, según ISO/IEC 21031:2024.

- **E** (kWh): se **estima** como tiempo de CPU × potencia configurable (`potencia_cpu_w`). No se mide hardware.
- **I** (gCO₂e/kWh): intensidad de carbono de la red eléctrica, parámetro configurable con su **fuente y fecha**.
- **M** (gCO₂e): emisiones incorporadas prorrateadas con la fórmula de la especificación,
  `TE × (TS/EL) × (RS/TR)`, con parámetros configurables.

`ParametroSCI` guarda cada juego de parámetros con versión, fuente y fecha, y cada cálculo registra qué versión usó.
**El panel muestra los supuestos y declara que el resultado es una estimación** (coherente con la sección 8 del paper:
las métricas son un plan de instrumentación, no mediciones validadas).

Antes de la demo hay que cargar valores vigentes y con fuente para `intensidad de carbono` y `potencia`;
no se usan números sin respaldo.

### Decisiones de Green Software aplicadas al propio producto
Paginación y filtros del lado del servidor, caché de agregados, carga diferida de gráficos, sin polling,
compresión de respuestas, bundle de React acotado y monolito en dos contenedores (principio de menor complejidad operacional del paper).

## 9. Manejo de errores y seguridad

- Las reglas de §6 devuelven errores 4xx con mensaje explícito (ej. "falta evidencia validada para pasar a *medida*").
- Subida de archivos: tipo y tamaño validados, nombres normalizados, almacenados en un volumen de Docker.
- CSRF y sesión de Django activos; permisos comprobados en cada vista, no solo en la UI.
- Semgrep en CI. Sin secretos en el repositorio.

## 10. Datos de demo y privacidad

Comando `seed_demo`:
- Carga regiones y las **30 Facultades Regionales + Rectorado**, con la regionalización del análisis
  (NEA, NOA, Cuyo, Centro, Buenos Aires, Patagonia, Nivel Central).
  - NEA: Resistencia. NOA: Tucumán, La Rioja. Cuyo: San Rafael, Mendoza.
  - Centro: Rafaela, Concepción del Uruguay, Rosario, Córdoba, Venado Tuerto, Santa Fe, Reconquista, Villa María,
    San Francisco, Concordia, Paraná.
  - Buenos Aires: Bahía Blanca, Mar del Plata, San Nicolás, Avellaneda, Delta, Haedo, Buenos Aires (CABA),
    General Pacheco, La Plata, Trenque Lauquen.
  - Patagonia: del Neuquén, Chubut, Santa Cruz, Tierra del Fuego.
  - Nivel Central: Rectorado.
  - La lista de las 30 FR sale de Wikipedia (a confirmar con fuente oficial). Las regiones de Paraná, Buenos Aires,
    General Pacheco, La Plata, Trenque Lauquen, Chubut, Santa Cruz y Tierra del Fuego no figuran en el análisis
    (no respondieron) y se asignaron con su mismo criterio; el grupo debe verificarlas antes de la demo.
- Carga usuarios de demo (uno por rol) con credenciales generadas en el comando y definidas por variable de entorno; no se versionan.
- Carga prácticas **ilustrativas** inspiradas en las iniciativas del relevamiento (ej. paneles solares y monitoreo
  energético en Mendoza), marcadas `origen = ilustrativa`. Los valores de mediciones de ejemplo son sintéticos y la UI
  los rotula "Datos ilustrativos".
- **No se cargan** nombres, correos ni celulares del Excel de respuestas: son datos personales de quienes respondieron.

## 11. Pruebas

- **pytest-django** sobre lo que más duele si falla: transiciones de práctica y de medición, regla "el validador no valida lo propio",
  permisos por facultad, y cálculo de SCI con parámetros conocidos.
- Un **E2E con Playwright** del flujo de la demo, si el tiempo lo permite.
- GitHub Actions ejecuta pytest y Semgrep en cada push.

## 12. Plan de tiempo y líneas de corte

| Momento | Entregable |
|---|---|
| Lunes noche | Proyecto Django, modelos, migraciones, admin funcionando, Docker Compose |
| Martes mañana | API, reglas de transición, roles y permisos, tests de reglas |
| Martes tarde | React: formularios del flujo, validación y tablero |
| Martes noche | `greenops`, panel SCI, `seed_demo`, pulido |
| Miércoles temprano | Ensayo de la demo y plan B (capturas / video del flujo) |

Si hay retraso se recorta en este orden: (1) `django-guardian` → filtro por pertenencia; (2) filtros finos del tablero;
(3) E2E de Playwright. El flujo núcleo (práctica → indicador → medición → evidencia → validación) no se recorta.

## 13. Riesgos

| Riesgo | Mitigación |
|---|---|
| Curva de Django (primer proyecto) | Admin primero: backoffice demostrable desde el lunes |
| Permisos por objeto toman más de lo previsto | Fallback de queryset por facultad |
| El número de SCI no es creíble | Supuestos y fuente visibles; se rotula como estimación |
| Falla la demo en vivo | Local con Docker Compose, sin dependencia de internet; plan B grabado |
