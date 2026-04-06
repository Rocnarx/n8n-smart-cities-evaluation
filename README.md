# Evaluación de n8n como plataforma de integración (EAI) para ciudades inteligentes

## Descripción general

Este repositorio contiene la infraestructura experimental y los artefactos utilizados para evaluar **n8n** como plataforma de integración **EAI** en un escenario de **ciudades inteligentes**.

El caso principal implementado actualmente es el **Caso A – Recarga Tullave**, compuesto por:

- un **workflow n8n** que orquesta el proceso de extremo a extremo,
- una **API mock en FastAPI** que simula sistemas externos,
- artefactos de prueba para **Postman**,
- documentación técnica de apoyo.

El objetivo del proyecto es generar evidencia reproducible sobre:

- latencia E2E,
- interoperabilidad mediante APIs,
- tolerancia a fallos,
- viabilidad de despliegue local,
- sostenibilidad operativa.

---

## Contenido principal del proyecto

- `docker-compose.yml`: despliegue base de n8n, PostgreSQL, Redis y la API mock.
- `main.py`: API mock del Caso A con endpoints simulados y latencia configurable.
- `CASO_A_Recarga_Tullave_endpoints_simulados_corregido.json`: workflow de n8n corregido para consumir los endpoints simulados.
- `Postman_E2E_Recarga_Tullave.postman_collection.json`: colección Postman para pruebas end-to-end.
- `Postman_E2E_Recarga_Tullave.postman_environment.json`: environment de Postman con variables base.
- `Documento_tecnico_n8n_API_mock_Caso_A.docx`: documento técnico del prototipo.

---

## Requerimientos

### Opción A: ejecución completa con Docker

Necesitas tener instalado:

- **Docker** 24 o superior
- **Docker Compose** (plugin `docker compose`)

### Opción B: n8n en Docker + API mock local

Necesitas tener instalado:

- **Docker**
- **Docker Compose**
- **Python 3.10+**
- **pip**

### Herramientas recomendadas

- **Postman** para pruebas manuales
- **cURL** para pruebas rápidas

---

## Arquitectura resumida

El flujo del **Caso A – Recarga Tullave** sigue esta secuencia:

1. Un cliente envía un evento de pago al **webhook de n8n**.
2. n8n valida el estado del pago.
3. n8n consulta la API mock para validar fondos.
4. Si hay fondos, n8n llama secuencialmente a:
   - confirmación bancaria,
   - recaudo Bogotá,
   - activación Tullave,
   - reporte a DIAN,
   - notificación por correo.
5. n8n devuelve una respuesta consolidada con el resultado del flujo y la latencia E2E.

---

## Endpoints de la API mock

La API mock expone los siguientes endpoints:

### GET

- `/health`

### POST

- `/funds/validate`
- `/bank/confirm`
- `/recaudo/bogota`
- `/tullave/activate`
- `/dian/report`
- `/notify/email`

Todos los endpoints POST aceptan un cuerpo JSON basado en:

```json
{
  "transaction_id": "tx-001",
  "amount": 12000,
  "account_balance": 50000,
  "delay_ms": 0,
  "jitter_ms": 0,
  "fail_rate": 0,
  "force_error": false
}
```

Algunos endpoints además aceptan banderas de negocio como:

- `force_insufficient`
- `force_reject`
- `channel`

---

## Variables de entorno necesarias

Debes definir estas variables:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `POSTGRES_DB` | Nombre de la base de datos de n8n | `n8n` |
| `POSTGRES_USER` | Usuario de PostgreSQL | `n8n` |
| `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `n8npass` |
| `N8N_BASIC_AUTH_ACTIVE` | Activa autenticación básica | `true` |
| `N8N_BASIC_AUTH_USER` | Usuario de acceso a n8n | `admin` |
| `N8N_BASIC_AUTH_PASSWORD` | Contraseña de acceso a n8n | `admin123` |
| `N8N_HOST` | Host público de n8n | `localhost` |
| `N8N_PORT` | Puerto de n8n | `5678` |
| `N8N_PROTOCOL` | Protocolo | `http` |
| `REDIS_PORT` | Puerto de Redis | `6379` |

### Ejemplo de archivo `.env`

```env
POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=n8npass

N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=admin123

N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http

REDIS_PORT=6379
```

---

## Ejecución del proyecto

# 1) Opción A — Todo con Docker

Usa esta opción si quieres levantar:

- PostgreSQL
- Redis
- API mock
- n8n

### Paso 1. Crear el archivo `.env`

Crea un archivo `.env` junto a `docker-compose.yml` con el contenido mostrado arriba.

### Paso 2. Levantar los servicios

```bash
docker compose up -d --build
```

### Paso 3. Verificar que n8n esté arriba

Abre en el navegador:

```text
http://localhost:5678
```

### Paso 4. Verificar que la API mock esté arriba

Si mantienes el mapeo del compose:

```yaml
ports:
  - "8001:8001"
```

prueba desde tu host:

```bash
curl http://localhost:8001/health
```

### Paso 5. Importar el workflow en n8n

Importa el archivo:

```text
CASO_A_Recarga_Tullave_endpoints_simulados_corregido.json
```

El webhook del caso es:

```text
casoA-recarga-tullave-v2
```

### Paso 6. Ajustar `mock_base_url`

Si **n8n y la API mock están dentro del mismo `docker compose`**, el `mock_base_url` que se debe enviar al webhook debe apuntar al nombre del servicio Docker, no a `localhost`.

Usa algo como:

```text
http://casea-mock-api:8001
```

> `localhost` dentro del contenedor de n8n no apunta a tu máquina ni a otros contenedores.

### Paso 7. Probar el flujo end-to-end

Si el workflow está en modo de prueba desde el editor, usa:

```bash
curl -X POST "http://localhost:5678/webhook-test/casoA-recarga-tullave-v2" \
  -H "Content-Type: application/json" \
  -d '{
    "mock_base_url": "http://casea-mock-api:8001",
    "transaction_id": "tx-e2e-ok-001",
    "payment_status": "APPROVED",
    "amount": 12000,
    "account_balance": 50000
  }'
```

Si el workflow ya está activo, usa:

```bash
curl -X POST "http://localhost:5678/webhook/casoA-recarga-tullave-v2" \
  -H "Content-Type: application/json" \
  -d '{
    "mock_base_url": "http://casea-mock-api:8001",
    "transaction_id": "tx-e2e-ok-001",
    "payment_status": "APPROVED",
    "amount": 12000,
    "account_balance": 50000
  }'
```

---

# 2) Opción B — n8n en Docker + API mock local con Python

Usa esta opción si quieres correr la API mock fuera de Docker.

### Paso 1. Instalar dependencias de Python

```bash
pip install fastapi uvicorn pydantic
```

### Paso 2. Ejecutar la API mock

Desde la carpeta donde está `main.py`:

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Paso 3. Verificar la API

```bash
curl http://localhost:8000/health
```

### Paso 4. Levantar n8n con Docker

```bash
docker compose up -d postgres redis n8n
```

### Paso 5. Usar la URL correcta desde n8n hacia tu host

Como n8n está en Docker y la API está en tu máquina host, el `mock_base_url` debe ser:

```text
http://host.docker.internal:8000
```

### Paso 6. Probar el flujo E2E

```bash
curl -X POST "http://localhost:5678/webhook-test/casoA-recarga-tullave-v2" \
  -H "Content-Type: application/json" \
  -d '{
    "mock_base_url": "http://host.docker.internal:8000",
    "transaction_id": "tx-e2e-ok-001",
    "payment_status": "APPROVED",
    "amount": 12000,
    "account_balance": 50000
  }'
```

---

## Latencia y fallos simulados

La API mock permite simular latencia y errores técnicos de manera controlada.

### Parámetros disponibles por request

- `delay_ms`: latencia base fija
- `jitter_ms`: latencia aleatoria adicional
- `fail_rate`: probabilidad de fallo técnico entre 0 y 1
- `force_error`: fuerza un error técnico
- `force_insufficient`: fuerza rechazo por fondos insuficientes
- `force_reject`: fuerza rechazo de negocio

### Variables globales del contenedor mock

En Docker Compose aparecen definidas:

```yaml
environment:
  MIN_DELAY_MS: 0
  MAX_DELAY_MS: 0
  FAIL_RATE: 0
```

Si quieres latencia aleatoria por defecto, puedes cambiarlo por ejemplo a:

```yaml
environment:
  MIN_DELAY_MS: 100
  MAX_DELAY_MS: 900
  FAIL_RATE: 0
```

Así cada servicio simulará una latencia aleatoria incluso si no mandas `delay_ms` en el cuerpo.

---

## Pruebas con Postman

Importa estos archivos en Postman:

- `Postman_E2E_Recarga_Tullave.postman_collection.json`
- `Postman_E2E_Recarga_Tullave.postman_environment.json`

### Variables importantes del environment

| Variable | Uso |
|---|---|
| `n8n_webhook_url` | URL de prueba (`/webhook-test/...`) |
| `n8n_webhook_url_prod` | URL productiva (`/webhook/...`) |
| `mock_base_url` | URL de la API mock |
| `cid` | Correlation ID para trazabilidad |

### Ajustes recomendados

#### Si usas API local con Python

```text
mock_base_url = http://host.docker.internal:8000
```

#### Si usas API mock dentro de Docker Compose

```text
mock_base_url = http://casea-mock-api:8001
```

---

## Resultado esperado del flujo

Cuando el flujo es exitoso, la respuesta final consolidada de n8n debe incluir, entre otros:

- `transaction_id`
- `status`
- `start_time`
- `end_time`
- `latency_ms`
- datos de fondos
- confirmación bancaria
- estado de recaudo
- activación Tullave
- reporte DIAN
- notificación

---

## Errores comunes y solución

### Error: `connect ECONNREFUSED 127.0.0.1:8000`

Causa probable:
- n8n intenta conectarse a `localhost:8000` desde dentro del contenedor.

Solución:
- si la API está en tu host: usa `http://host.docker.internal:8000`
- si la API está en Docker Compose: usa `http://casea-mock-api:8001`

### Error: `The service refused the connection - perhaps it is offline`

Causas probables:
- el webhook no es correcto,
- el workflow no está escuchando en modo test,
- la API mock no está arriba,
- `mock_base_url` apunta a una URL incorrecta.

### Diferencia entre `/webhook-test/` y `/webhook/`

- Usa `/webhook-test/...` cuando estés probando desde el editor y hayas activado **Listen for test event**.
- Usa `/webhook/...` cuando el workflow esté activo/publicado.

---

## Métricas soportadas actualmente

Con el estado actual del prototipo ya puedes obtener:

- **latencia E2E** desde n8n,
- **latencia por servicio** desde la API mock,
- **rechazos de negocio**,
- **fallos técnicos controlados**,
- **trazabilidad por `transaction_id` y `correlation_id`**.

Para métricas como CPU, RAM y percentiles agregados, se recomienda medir externamente con herramientas como:

- `docker stats`
- Prometheus
- Grafana
- procesamiento posterior de resultados

---

## Artefactos relacionados

- Documento técnico: `Documento_tecnico_n8n_API_mock_Caso_A.docx`
- Workflow de n8n: `CASO_A_Recarga_Tullave_endpoints_simulados_corregido.json`
- Colección Postman: `Postman_E2E_Recarga_Tullave.postman_collection.json`
- Environment Postman: `Postman_E2E_Recarga_Tullave.postman_environment.json`

---

## Uso académico

Este repositorio fue construido con fines **académicos y experimentales** para apoyar la evaluación de n8n como plataforma de integración en escenarios de ciudades inteligentes.

Los servicios externos están simulados y **no representan integraciones reales con entidades oficiales**.
