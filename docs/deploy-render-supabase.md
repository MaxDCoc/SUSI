# Desplegar SUSI gratis: Render + Supabase + UptimeRobot

Objetivo: que cualquiera abra una URL y use SUSI, sin instalar nada (ni Docker). Todo en planes gratuitos.

| Pieza | Servicio | Para qué |
|---|---|---|
| App (Django + React) | **Render**, plan gratis, desde este repo (`render.yaml`) | Corre el `Dockerfile`. |
| Base de datos y PDFs | **Supabase**, plan gratis | Postgres y Storage (bucket privado `evidencias`). |
| Mantener todo despierto | **UptimeRobot**, plan gratis | Un ping cada 5 minutos a `/health/db/`. |

Las cuentas las crean ustedes. Ninguna clave ni contraseña se escribe en el repositorio.

## Antes de empezar: límites que hay que conocer

- **Render gratis** se duerme a los 15 minutos sin tráfico (despertar tarda ~1 minuto) y da 750 horas por mes, que alcanzan
  para **un** servicio siempre despierto. Puede reiniciarlo cuando quiera. Por eso el ping de UptimeRobot (paso 5).
- **Supabase gratis** pausa el proyecto si pasa una semana sin actividad **en la base**, y limita la base a 500 MB y el
  almacenamiento a 1 GB. El mismo ping a `/health/db/` hace una consulta, así que cuenta como actividad.
- **Backups:** no cuenten con los del plan gratis. Hagan uno a mano (paso 8) antes de cualquier cosa importante.
- Los límites de los planes gratuitos cambian. Si algo de esta guía no coincide con lo que ven en pantalla, mandan los
  paneles de cada servicio.

## 1. Subir el código a GitHub

Render lee el repositorio. La rama que usen tiene que contener `render.yaml` y el `Dockerfile` (esta rama `feat/deploy`
o `main` una vez integrada). Si el repositorio es privado, Render pide autorización de acceso a GitHub.

## 2. Supabase: base de datos y bucket

1. Crear un proyecto nuevo. **Región: East US (North Virginia)**, para que quede junto a Render (Virginia). Anotar la
   contraseña de la base: no se vuelve a mostrar.
2. **Cadena de conexión.** Botón **Connect** → **Session pooler** (Render gratis solo tiene IPv4, y la conexión directa de
   Supabase es IPv6). Copiar la cadena y reemplazar `[YOUR-PASSWORD]` por la contraseña. Si la contraseña tiene
   caracteres como `@`, `:` o `/`, hay que codificarlos (`%40`, `%3A`, `%2F`) o elegir una contraseña sin ellos.
   Esa cadena es el valor de `DATABASE_URL`.
3. **Bucket.** Storage → *New bucket* → nombre **`evidencias`**, con *Public bucket* **desactivado**.
4. **Claves S3.** En la configuración de Storage buscar la conexión **S3** (el nombre del menú puede variar):
   copiar el **Endpoint** (termina en `/storage/v1/s3`) y la **Region**, y crear una **Access key**. Se obtienen cuatro valores:
   endpoint, región, *access key id* y *secret*.

## 3. Render: crear el servicio

1. Render → **New** → **Blueprint** → elegir el repositorio de SUSI y la rama.
2. Render lee `render.yaml` y pide los valores que no se guardan en el repositorio:

   | Variable | Valor |
   |---|---|
   | `DATABASE_URL` | La cadena del Session pooler del paso 2. |
   | `SUSI_S3_ENDPOINT_URL` | El endpoint S3 de Supabase. |
   | `SUSI_S3_REGION` | La región que muestra Supabase para S3 (por ejemplo `us-east-1`). |
   | `SUSI_S3_ACCESS_KEY` | El *access key id*. |
   | `SUSI_S3_SECRET_KEY` | El *secret*. |

   El resto ya viene en el Blueprint: `DJANGO_SECRET_KEY` se genera sola, `DJANGO_DEBUG=0`, cookies seguras,
   confianza en el proxy HTTPS y el bucket `evidencias`. El dominio `*.onrender.com` se agrega solo a los hosts permitidos.
3. Esperar el primer despliegue (varios minutos: construye el frontend y la imagen). Al arrancar, el contenedor corre las
   migraciones. Cuando figure *Live*, anotar la URL (`https://susi-xxxx.onrender.com`).

## 4. Cargar los datos iniciales (desde tu PC)

Render gratis no tiene consola, así que el seed se corre en tu máquina apuntando a la base de Supabase. En PowerShell,
desde la carpeta `backend` y con el entorno virtual activado (si no lo tenés: `python -m venv .venv`, activarlo y
`pip install -r requirements-dev.txt`):

```powershell
$env:DATABASE_URL = "<la misma cadena del paso 2>"
$env:SUSI_DEMO_PASSWORD = "<una clave fuerte para admin.demo, responsable.demo y validador.demo>"
python manage.py seed_demo
```

Esperado: lista los usuarios creados y termina con "Datos de demo cargados.". Esperen a que el primer despliegue esté
*Live*: antes de eso las tablas no existen. Esta URL es pública, así que usen una clave fuerte. Si no quieren prácticas
de ejemplo: `python manage.py seed_demo --solo-catalogos` y `python manage.py createsuperuser`.

Después, entrar a `https://<tu-url>/admin/` con `admin.demo` y cargar los **Parámetros SCI** con fuente y fecha
(sección C de `docs/demo-runbook.md`). Sin eso el panel Green no muestra el número.

## 5. UptimeRobot: que no se duerman ni la app ni la base

1. Crear una cuenta en UptimeRobot → **Add New Monitor**.
2. Tipo **HTTP(s)**, URL **`https://<tu-url>/health/db/`**, intervalo **5 minutos** (el mínimo del plan gratis).
3. Activar el aviso por email: si la base cae, `/health/db/` responde 503 y les llega la alerta.

Un solo monitor alcanza: mantiene despierta a Render (llega tráfico cada 5 minutos, menos que los 15 de la suspensión) y
toca la base de Supabase. `/health/` (sin base) lo usa Render para saber si el servicio está sano.

## 6. Verificación (hacerla una vez, antes de mostrarlo)

- [ ] `https://<tu-url>/health/` responde `{"status": "ok"}` y `/health/db/` responde `{"status": "ok", "base": "ok"}`.
- [ ] Entrar como `responsable.demo`: aparecen las prácticas ilustrativas.
- [ ] Crear una práctica, un indicador y una medición; **subir un PDF** como evidencia y descargarlo.
- [ ] En Supabase → Storage → `evidencias`: aparece el archivo (prueba que no quedó en el disco de Render).
- [ ] En Render → **Manual Deploy → Restart**: tras reiniciar, el PDF sigue descargándose.
- [ ] Entrar como `validador.demo` y validar la medición; promover la práctica a Medida (guion en `docs/demo-runbook.md`).
- [ ] Tablero con los gráficos y panel Green.
- [ ] Esperar 20 minutos sin tocar nada y volver a abrir la URL: responde enseguida (el monitor la mantuvo despierta).

## 7. Si algo falla

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| El despliegue no arranca y el log dice `DJANGO_SECRET_KEY es obligatoria` | Falta la variable | Revisar el entorno del servicio en Render. |
| `400 Bad Request` en cualquier página | Host no permitido | Si usan dominio propio, agregarlo en `DJANGO_ALLOWED_HOSTS`. El de `onrender.com` ya está. |
| `403 CSRF` al iniciar sesión | Origen no confiable | Con dominio propio, agregar `https://su-dominio` en `DJANGO_CSRF_TRUSTED_ORIGINS`. |
| Error de conexión a la base (`Network is unreachable`, IPv6) | Usaron la conexión directa | Usar la cadena del **Session pooler**. |
| `prepared statement ... does not exist` | Pooler en modo transacción (puerto 6543) | Agregar `DATABASE_DISABLE_PREPARED=1` o pasar a la cadena de sesión (puerto 5432). |
| `SignatureDoesNotMatch` o `NoSuchBucket` al subir un PDF | Endpoint, región o claves S3 mal copiados, o el bucket no se llama `evidencias` | Revisar las cinco variables `SUSI_S3_*` y el nombre del bucket. |
| Después de una semana la app no conecta a la base | Supabase pausó el proyecto | Restaurarlo desde su panel y revisar que el monitor de UptimeRobot siga activo. |
| La primera pantalla tarda ~1 minuto | Render estaba dormido o recién desplegado | Esperar; con el monitor activo no debería repetirse. |

## 8. Backup manual

Los backups del plan gratis de Supabase no son confiables. Desde tu PC, con Docker (no incluye los PDFs del bucket):

```powershell
docker run --rm -v ${PWD}:/backup postgres:16-alpine pg_dump --file=/backup/susi-backup.sql "$env:DATABASE_URL"
```

El archivo contiene todos los datos: guárdenlo fuera del repositorio y no lo suban a GitHub.

## Qué NO está verificado

- Los tests prueban la subida y descarga de PDFs contra un servidor S3 emulado (moto) y la imagen de Docker en el puerto de
  `$PORT`. **No se probó contra Render ni Supabase reales**: el primer despliegue es la prueba de verdad; usen la
  verificación del paso 6.
- Los nombres de menús y botones de Supabase, Render y UptimeRobot son los que encontramos en su documentación y pueden haber cambiado.
- Que el uso de un monitor externo para mantener despierto un servicio gratis esté permitido por los términos de cada
  proveedor: revisarlo antes de depender de esto.
- El medidor de Green Software guarda una fila por operación de la API en la base de Supabase (límite de 500 MB).
  Con el uso de una demo no es un problema, pero conviene vigilar el tamaño si se usa por meses.
