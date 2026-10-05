# Portfolio online en AWS

Objetivo: abrir el dashboard desde cualquier lado y recalcular el P&L a demanda,
sin dejar una maquina prendida y con las credenciales de PPI fuera del HTML.

## Resumen de la propuesta

Servicios administrados y sin servidores: **S3 + CloudFront** para la pagina,
**Lambda** para calcular, **Secrets Manager** para las claves de PPI y
**Cognito** para el login. El costo esperable para uso personal son centavos por
mes (todo entra en la capa gratuita salvo Secrets Manager, ~0,40 USD/mes).

```
Navegador ──► CloudFront ──► S3 (HTML + JS estaticos)
    │  login (Cognito)
    └──► API Gateway (HTTP API, JWT) ──► Lambda "refresh"  ──► PPI / Yahoo
                                    └──► Lambda "data"     ──► S3 (latest.json)
                         S3: portfolio.xlsx (versionado) · cache de precios historicos
                         Secrets Manager: PPI_PUBLIC_KEY / PPI_PRIVATE_KEY
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
2. La Lambda lee `portfolio.xlsx` de S3, pide precios, calcula el snapshot y
   escribe `latest.json` en S3 (con la hora de calculo).
3. El navegador consulta `GET /data` cada 2-3 s (o mira `generated_at`) y repinta
   las tablas cuando cambia.
4. Si ya hay un calculo en curso, el boton lo informa en vez de lanzar otro.

### Donde vive cada cosa

- **`portfolio.xlsx`**: bucket S3 privado con versionado. Se sigue editando en
  Excel y se sube con `aws s3 cp portfolio.xlsx s3://<bucket>/portfolio.xlsx`
  (un `make publish` lo resuelve). El versionado deja volver atras si se sube
  algo roto.
- **Claves de PPI**: Secrets Manager, leidas por la Lambda en tiempo de ejecucion.
  Nunca van en el HTML, en variables de entorno de la consola ni en el repo.
- **Cache de precios historicos**: S3 (`cache/closes.json`) o una tabla DynamoDB
  on-demand.
- **Pagina**: `index.html` + JS/CSS en S3, servidos por CloudFront con acceso
  restringido al bucket (OAC).

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
2. **Entrada para Lambda** (`handler.py`): descarga el xlsx a `/tmp`, arma
   `PortfolioApp`, corre el camino rapido o el lento y sube el resultado.
3. **Camino rapido real.** Hoy `PortfolioApp.snapshot` hace todo junto. Agregar un
   parametro para reutilizar tendencia, watchlist y analytics de bonos de la
   ultima corrida lenta, y refrescar solo precio y MEP.
4. **Cache persistente** de `HistoricalPrices` (la clase ya cachea en memoria; hay
   que volcarla a S3/DynamoDB).
5. **Credenciales desde Secrets Manager** en vez de `PPI_PUBLIC_KEY` /
   `PPI_PRIVATE_KEY` del entorno (`Settings.from_env` se puede reemplazar por un
   `Settings.from_secrets`).
6. **Boton y polling** en el JS.

## Infraestructura como codigo

Usar **AWS SAM** o **CDK (Python)** para que todo se pueda crear y borrar con un
comando. SAM es suficiente y mas corto: una plantilla con el bucket, las dos
Lambdas (imagen de contenedor), la HTTP API, el user pool, el schedule y los
permisos minimos (la Lambda solo puede leer ese bucket y ese secreto).

## Riesgos y cosas a verificar antes de construir

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

1. **Prueba de viabilidad (medio dia):** una Lambda con la imagen que corra el
   calculo actual desde S3 y deje `latest.json`. Verifica PPI y Yahoo desde AWS.
2. **Pagina online (1 dia):** `fetch` del JSON, S3 + CloudFront, login con Cognito.
3. **A demanda (1 dia):** `/refresh` asincrono, boton con polling, camino rapido.
4. **Automatico (medio dia):** EventBridge en horario de mercado (lun-vie ~11-17 h
   Argentina), alarma si falla, cache historica persistente.

## Costo estimado (uso personal)

| Servicio | Mensual |
|---|---|
| Lambda, API Gateway, S3, CloudFront, Cognito, EventBridge | capa gratuita |
| Secrets Manager (1 secreto) | ~0,40 USD |
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
