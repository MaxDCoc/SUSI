# Runbook de la demo — miércoles 2026-10-14, ~10:00

## A. Checklist previo (el martes por la noche y de nuevo el miércoles a las 8:30)

- [ ] `docker compose down -v && docker compose up --build -d` termina sin errores y `docker compose ps` muestra `healthy`.
- [ ] `docker compose exec app python manage.py seed_demo` imprime los 3 usuarios y "Datos de demo cargados.".
- [ ] Probado en la notebook que va a la demo, **sin internet** (el frontend no usa CDN; ECharts viene en el build).
- [ ] **Parámetros SCI cargados con fuente** (ver sección C). Sin esto el panel Green no muestra el número.
- [ ] Alguien del grupo verificó la lista de las 30 Facultades Regionales y la región de las 8 que no estaban en el
      relevamiento (Paraná, Buenos Aires, General Pacheco, La Plata, Trenque Lauquen, Chubut, Santa Cruz y Tierra del Fuego):
      el análisis no las nombra, la lista salió de Wikipedia y las regiones se asignaron con el criterio del análisis.
- [ ] Credenciales de demo anotadas **fuera del repo** (gestor de contraseñas). `.env` no está versionado.
- [ ] Usé la app 5 minutos antes de abrir el panel Green, para que haya muestras de las tres operaciones del flujo núcleo.
- [ ] Plan B grabado (sección E) y abierto en otra pestaña.

## B. Guion (≈ 8 minutos)

Abrir dos ventanas del navegador (una normal para el Responsable y una privada para el Validador) para no cerrar sesión.

1. **Contexto (30 s).** "Del relevamiento: 96% hace sostenibilidad, 54% tiene área, 27% mide, 19% digitaliza. SUSI cierra esa brecha."
2. **Responsable → `responsable.demo`, pestaña *Prácticas*.** Se ven las 9 prácticas con la insignia *Datos ilustrativos*
   (inspiradas en el relevamiento, no cargadas por las facultades). Mostrar los estados de madurez.
3. **Crear una práctica** en Mendoza ("Medición de consumo de agua", dimensión ambiental, ODS 6). Abrirla.
4. **Reglas de madurez:** apretar *Promover a Formalizada* → error en rojo ("Falta asignar un responsable…").
   Apretar *Asumir la responsabilidad* y volver a *Promover* → pasa a Formalizada.
5. **Indicador y medición:** *Nuevo indicador* ("Consumo de agua", fórmula "m³ facturados en el mes", unidad `m3`, mensual) →
   *Cargar medición* (período `2026-09`, valor `120`) → *Agregar evidencia* (un enlace) → *Enviar a validación*.
   **Evidencia antes que declaración:** apretar *Promover a Medida* ahora → error en rojo ("Falta un indicador con al menos
   una medición validada y con evidencia…"): todavía nadie validó la medición.
6. **Validador → ventana privada con `validador.demo`, pestaña *Validaciones*.** Aparecen dos pendientes: la recién cargada
   (Mendoza) y la de Delta, esta última con la insignia *Datos ilustrativos*. **Validar las dos.** Si preguntan por la
   separación de funciones: el servidor rechaza que quien cargó una medición la valide (está cubierto por tests
   automáticos); el Validador solo ve la cola, no tiene botones de carga.
7. **Volver al Responsable:** abrir la práctica de **Mendoza** creada en el paso 3 → *Promover a Medida* (ahora sí: tiene una
   medición validada **con evidencia**). Mostrar el cambio de estado. Si sobra tiempo, repetir con la de Delta
   ("Cálculo de huella de carbono…"), que quedó validada en el paso 6.
8. **Tablero:** el embudo y los KPIs cambiaron. Filtrar por región y por ODS. "Facultades con prácticas cargadas: X / 30."
   Leer el aviso de datos ilustrativos: casi todas las prácticas son ejemplos, no cargas reales.
9. **Green Software:** mostrar el SCI estimado de *este mismo flujo*, la unidad funcional (1.000 operaciones del flujo
   núcleo) y los supuestos con su fuente. Decir explícitamente: **es una estimación**, no una medición de hardware.
   Mostrar la tabla de costo por operación y las decisiones de Green Software aplicadas.
10. **Cierre (30 s):** trabajo siguiente (importación/exportación R6, mapeo a UI GreenMetric 2026, Impact Framework,
    diferir cargas según intensidad de carbono).

## C. Parámetros SCI: cómo cargarlos sin inventar números

En `http://localhost:8000/admin/` → **Parámetros SCI** → *Agregar*. Cada campo necesita un valor con respaldo:

| Campo | De dónde sale |
|---|---|
| Potencia de CPU (W) | Ficha del fabricante del procesador de la notebook/servidor (TDP). Anotar el modelo en *Supuestos*. |
| Intensidad de carbono (gCO₂e/kWh) | Factor de emisión de la red eléctrica argentina publicado por un organismo oficial (por ejemplo, la Secretaría de Energía o CAMMESA; verificar cuál es la fuente vigente). Cargar **fuente** (con URL) y **fecha** del dato. |
| Emisiones incorporadas TE (gCO₂e) | Huella de fabricación del equipo que declare el fabricante (*product carbon footprint*), o una estimación documentada. |
| Vida útil EL (horas) | Años de vida útil considerados × horas por año. Anotar el criterio. |
| RS / TR | Fracción del equipo que usa la aplicación (por ejemplo, 1 núcleo de N). |

Todo lo que no tenga respaldo se declara como supuesto en el campo *Supuestos*; el panel lo muestra en pantalla.

## D. Si algo falla durante la demo

| Síntoma | Qué hacer |
|---|---|
| La app no responde | `docker compose restart app` (tarda ~10 s). |
| "Falta el build del frontend" | Se levantó sin Docker: `cd frontend && npm run build` y copiar `dist/` a `backend/frontend_dist/`. |
| Login falla | Verificar `SUSI_DEMO_PASSWORD` en `.env`; si se cambió después del seed, resetear: `docker compose exec app python manage.py changepassword responsable.demo`. |
| Datos de la demo "ensuciados" | `docker compose down -v && docker compose up -d && docker compose exec app python manage.py seed_demo` (deja la base como al principio; los parámetros SCI hay que volver a cargarlos). |
| Panel Green sin SCI | Faltan parámetros (sección C) o muestras (usar la app y refrescar). |

## E. Plan B

- Grabar el guion completo con la grabadora de pantalla de Windows (Win + G) el martes por la noche.
- Capturas de: práctica con error de regla, cola de validaciones, tablero, panel Green.
- Si el entorno falla y no se recupera en 2 minutos, mostrar el video y contar el flujo sobre las capturas.

## Ensayos

| Fecha | Quién | Qué se probó | Resultado |
|---|---|---|---|
| 2026-10-12 | Implementación (automatizado, no cronometrado) | Pasos 6, 7 y 8 y la regla de *Optimizada* en el navegador integrado contra Docker Compose + Postgres; subida y descarga de un PDF al volumen `media`; panel Green (muestra "No hay parámetros SCI" porque no se cargaron) | OK |
| | | Ensayo completo cronometrado con el guion (pendiente, lo hace el grupo) | |
