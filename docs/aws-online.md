# Portfolio online en AWS

Objetivo: abrir el dashboard desde cualquier lado y recalcular el P&L a demanda,
sin dejar una maquina prendida y con las credenciales de PPI fuera del HTML.

## Resumen de la propuesta

Servicios administrados y sin servidores: **S3 + CloudFront** para la pagina,
**Lambda** para calcular, **Secrets Manager** para las claves de PPI,
**Cognito** para el login y **Google Drive** como fuente de datos: la planilla
vive en Drive como Google Sheet, se edita desde el celular al comprar y la Lambda
la lee en cada recalculo. El costo esperable para uso personal son centavos por
mes (todo entra en la capa gratuita salvo Secrets Manager, ~0,40 USD/mes).

```
Navegador ──► CloudFront ──► S3 (HTML + JS estaticos)
    │  login (Cognito)
    └──► API Gateway (HTTP API, JWT) ──► Lambda "refresh"  ──► PPI / Yahoo
                                    │          └──► Drive API (export .xlsx de la planilla)
                                    └──► Lambda "data"     ──► S3 (latest.json)
                         Google Drive: planilla "portfolio" (Google Sheet, historial de versiones)
                         S3: latest.json · cache de precios historicos
                         Secrets Manager: claves de PPI · Google: Workload Identity Federation (sin claves)
                         EventBridge Scheduler: refresh automatico en horario de mercado
```

## Por que no alcanza con "meter el script en una Lambda"

1. **API Gateway corta a los 29 s.** PPI se consulta con una pausa de 0,35 s por
   pedido; con ~50 instrumentos mas MEP, tendencia y bonos se pasa de ese tiempo.
   El recalculo tiene que ser **asincrono**: el boton dispara el calculo y el
   navegador consulta hasta que aparece el resultado nuevo.
2. **El HTML de hoy lleva los datos adentro** (`DATA = ...`). Online tienen que
   venir de un JSON que se pide aparte, o cada recalculo obligaria a regenerar y
   volver a publicar la pagina.
3. **Paquete grande.** `yfinance` arrastra pandas y numpy: el zip supera el limite
   de Lambda. Se despliega como **imagen de contenedor** (hasta 10 GB).
4. **Lo lento no cambia entre un recalculo y otro.** Hay que separarlo.

## Diseno

### Dos caminos de calculo

| Camino | Que recalcula | Cuando | Costo en tiempo |
|---|---|---|---|
| **Rapido** (boton) | Precios actuales, MEP y P&L de todas las posiciones | A demanda y cada 5-10 min en horario de mercado | Segundos a ~20 s |
| **Lento** (programado) | Tendencia de 30 dias, watchlist, bonos (analytics) | 1 o 2 veces por dia | Minutos |

La solapa **Anual** va aparte de los dos: los cierres de anios pasados **no
cambian nunca**, asi que se piden una sola vez y se guardan para siempre en S3 o
DynamoDB (clave `ticker + fecha`). Solo el anio en curso usa el precio de hoy. Con
eso `--no-annual` deja de hacer falta.

### Flujo del boton "Recalcular"

1. `POST /refresh` → API Gateway → Lambda `refresh` (invocacion asincrona,
   responde `202` enseguida).
2. La Lambda exporta la planilla de Drive como `.xlsx` a `/tmp`, pide precios,
   calcula el snapshot y escribe `latest.json` en S3 (con la hora de calculo y
   el `modifiedTime` de la planilla).
3. El navegador consulta `GET /data` cada 2-3 s (o mira `generated_at`) y repinta
   las tablas cuando cambia.
4. Si ya hay un calculo en curso, el boton lo informa en vez de lanzar otro.

### Donde vive cada cosa

- **Planilla**: en Google Drive, ver la seccion siguiente.
- **Claves de PPI y de Google**: Secrets Manager, leidas por la Lambda en tiempo
  de ejecucion. Nunca van en el HTML, en variables de entorno de la consola ni en
  el repo. Google no necesita secreto (ver Workload Identity Federation abajo).
- **Cache de precios historicos**: S3 (`cache/closes.json`) o una tabla DynamoDB
  on-demand.
- **Pagina**: `index.html` + JS/CSS en S3, servidos por CloudFront con acceso
  restringido al bucket (OAC).

### Planilla en Google Drive

El flujo buscado es: comprar → anotar la operacion en la planilla desde el
celular → entrar a la web → "Recalcular". Para eso la fuente de datos deja de ser
un archivo que hay que subir y pasa a vivir en Drive.

**Formato: Google Sheet nativo (recomendado).** Se importa `portfolio.xlsx` una
vez a Google Sheets y desde ahi se edita en la app o la web. La Lambda lo pide con
`GET /drive/v3/files/{id}/export?mimeType=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
y recibe un `.xlsx` con los valores de las formulas ya calculados por Google, que
es lo que necesita `openpyxl.load_workbook(path, data_only=True)`. Los nombres de
las hojas se conservan, asi que `PortfolioWorkbook` no cambia.

> Alternativa: dejar el `.xlsx` tal cual en Drive (editado con Excel via Drive
> para escritorio, o en Sheets en modo compatible con Office) y bajarlo con
> `GET /drive/v3/files/{id}?alt=media`. Funciona igual del lado de la Lambda,
> pero editar desde el celular es mas incomodo.

**Acceso: cuenta de servicio de Google Cloud, sin claves JSON.** Crear claves
suele estar bloqueado por politica (`iam.disableServiceAccountKeyCreation`), y
ademas es mejor no tenerlas. La cuenta de servicio tiene la planilla compartida
como **lector** y se usa sin clave en los dos entornos:
- **Local:** tu usuario la impersona con
  `gcloud auth application-default login --impersonate-service-account=<email>`
  (necesitas `roles/iam.serviceAccountTokenCreator` sobre ella).
- **AWS:** **Workload Identity Federation** con un pool y un provider de tipo
  AWS. Google confia en el rol IAM de la Lambda y le entrega tokens de la
  cuenta de servicio; el archivo de configuracion (sin secretos) se genera con
  `gcloud iam workload-identity-pools create-cred-config ... --aws` y se apunta
  con `GOOGLE_APPLICATION_CREDENTIALS`. Asi tampoco hace falta guardar nada de
  Google en Secrets Manager.

El codigo usa `google.auth.default(scopes=[drive.readonly])`, que resuelve los
dos casos sin cambios.

Con eso la Lambda solo ve los archivos que se le compartieron explicitamente, no
el resto del Drive, y no puede modificar nada.

**Detalles:**
- El ID de la planilla va como variable de entorno de la Lambda (`SHEET_ID`); no
  es secreto, el acceso lo da el permiso de compartir.
- La respuesta de `files.get?fields=modifiedTime` se guarda en `latest.json` y la
  pagina muestra "planilla editada a las 14:32", para saber si el calculo ya
  incluye la ultima compra.
- Bajar la planilla agrega ~1-2 s al recalculo.
- El historial de versiones de Google Sheets reemplaza al versionado de S3 para
  volver atras si se rompe algo.
- Antes de migrar, verificar que todas las formulas de la planilla den lo mismo
  en Sheets que en Excel (sobre todo funciones poco comunes o formatos de fecha).

### Login

Cognito User Pool con un unico usuario (vos) y MFA, con el JWT validado por el
authorizer de API Gateway. La pagina estatica tambien debe pedir login antes de
mostrar nada (Lambda@Edge o una pantalla de login que redirige al Hosted UI), o
bien se sirve todo desde la API y se omite CloudFront.

> Alternativa mas simple si se acepta menos seguridad: un token largo guardado
> en el navegador y verificado en una Lambda authorizer. No lo recomiendo para
> algo que maneja las claves de PPI.

## Cambios necesarios en el codigo

1. **Separar datos de pagina.** `DashboardPayload.as_dict()` ya genera el JSON;
   exponerlo como `latest.json` y hacer que el HTML lo pida con `fetch` en vez de
   llevarlo incrustado (hoy `__DATA_JSON__`). Se mantiene el modo "archivo
   suelto" como opcion de la CLI.
2. **Entrada para Lambda** (`handler.py`): exporta la planilla de Drive a
   `/tmp/portfolio.xlsx`, arma `PortfolioApp`, corre el camino rapido o el lento
   y sube el resultado.
3. **Lector de Drive**: con ADC (impersonacion local, Workload Identity
   Federation en AWS) obtiene un token, exporta la planilla y devuelve la ruta
   local y el `modifiedTime`. **Hecho:** `portfolio/sources/google_sheet.py`
   (`GoogleSheet`); la CLI lee de Drive cuando no se le pasa un `.xlsx`.
4. **Camino rapido real.** Hoy `PortfolioApp.snapshot` hace todo junto. Agregar un
   parametro para reutilizar tendencia, watchlist y analytics de bonos de la
   ultima corrida lenta, y refrescar solo precio y MEP.
5. **Cache persistente** de `HistoricalPrices` (la clase ya cachea en memoria; hay
   que volcarla a S3/DynamoDB).
6. **Credenciales desde Secrets Manager** en vez de `PPI_PUBLIC_KEY` /
   `PPI_PRIVATE_KEY` del entorno (`Settings.from_env` se puede reemplazar por un
   `Settings.from_secrets`, que tambien devuelva la clave de Google).
7. **Boton y polling** en el JS, y la hora de edicion de la planilla en la
   cabecera.

## Infraestructura como codigo

Usar **AWS SAM** o **CDK (Python)** para que todo se pueda crear y borrar con un
comando. SAM es suficiente y mas corto: una plantilla con el bucket, las dos
Lambdas (imagen de contenedor), la HTTP API, el user pool, el schedule y los
permisos minimos (la Lambda solo puede leer ese bucket y ese secreto).

## Riesgos y cosas a verificar antes de construir

- **Planilla en Sheets.** Que la exportacion a `.xlsx` lea igual que el archivo
  de hoy: correr la CLI local contra el export y comparar el resultado con el
  generado desde `portfolio.xlsx`.
- **PPI desde Lambda.** Hay que confirmar que PPI acepta el login desde IPs de AWS
  y como se comporta su limite de pedidos con corridas programadas. Es lo primero
  a probar.
- **Yahoo desde Lambda.** `yfinance` suele fallar o ser bloqueado desde IPs de
  nube de forma intermitente. El codigo ya tiene respaldo (PPI y precio manual),
  pero para cedears y USD sin PPI conviene medir cuantos pedidos fallan.
- **Cold start** de una imagen con pandas: 3-6 s. Aceptable para un boton.
- **Concurrencia.** Limitar la Lambda `refresh` a 1 ejecucion simultanea para no
  pisar `latest.json` ni exceder el limite de PPI.
- **Seguridad.** El dashboard tiene tus posiciones: bucket privado, sin acceso
  publico, cifrado en reposo (por defecto), logs sin datos de posiciones.

## Plan por etapas

0. **Planilla a Drive (1-2 h):** importar `portfolio.xlsx` a Google Sheets,
   crear la cuenta de servicio, compartirle la planilla, impersonarla con ADC y probar el export desde
   la CLI local (sin pasarle un `.xlsx`) comparando contra el archivo actual.
1. **Prueba de viabilidad (medio dia):** una Lambda con la imagen que corra el
   calculo actual leyendo la planilla de Drive y deje `latest.json`. Verifica
   PPI, Yahoo y Drive desde AWS.
2. **Pagina online (1 dia):** `fetch` del JSON, S3 + CloudFront, login con Cognito.
3. **A demanda (1 dia):** `/refresh` asincrono, boton con polling, camino rapido.
4. **Automatico (medio dia):** EventBridge en horario de mercado (lun-vie ~11-17 h
   Argentina), alarma si falla, cache historica persistente.

## Costo estimado (uso personal)

| Servicio | Mensual |
|---|---|
| Lambda, API Gateway, S3, CloudFront, Cognito, EventBridge | capa gratuita |
| Secrets Manager (1 secreto, PPI) | ~0,40 USD |
| Google Drive API | gratis |
| ECR (imagen ~1 GB) | ~0,10 USD |
| **Total** | **< 1 USD** |

Si despues de tanto refresco programado el costo de Lambda subiera, alcanza con
espaciar el schedule o limitarlo a los dias habiles.

## Alternativa con menos piezas

Una instancia **Lightsail** (~5 USD/mes) o un contenedor en **App Runner** con el
servidor Flask de la opcion "servidor local", detras de un login simple. Es mucho
menos codigo nuevo (no hace falta separar caminos ni hacer el refresh
asincrono, porque no hay limite de 29 s), pero se paga todo el mes, hay un
servidor que mantener y el login queda mas artesanal. Es un buen primer paso si
se prefiere ver algo funcionando rapido y migrar despues.
