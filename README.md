# Evaluating n8n as an Enterprise Integration Platform for Smart Cities

This repository contains the experimental infrastructure, workflows, mock services, and supporting artifacts used in a thesis-driven evaluation of **n8n** as an **Enterprise Application Integration (EAI)** layer for **smart city digital services**.

The project is designed around **reproducible, self-hosted experimentation**. Its main purpose is not only to demonstrate functional orchestration, but also to generate evidence about whether n8n can serve as a viable integration platform for public-sector urban scenarios under realistic operational constraints.

## Research focus

The repository supports the evaluation of n8n across two dimensions central to the thesis:

- **Technical suitability**
  - end-to-end latency
  - API interoperability
  - fault tolerance and recovery
  - traceability, security, and data governance
- **Operational sustainability**
  - local deployment viability
  - resource usage
  - maintainability of the workflows
  - ecosystem maturity and support

These evaluation dimensions are explicitly aligned with the thesis framework, which treats smart-city integration as a problem of interoperability, resilience, auditability, and reproducible operation rather than simple workflow automation.

## Why this repository matters

Urban digital services usually depend on multiple heterogeneous systems: payment gateways, institutional APIs, notification services, identity providers, judicial systems, and operational backends. This repository provides a controlled environment to study whether n8n can orchestrate those interactions without requiring a full redesign of the underlying systems.

Instead of relying on external production dependencies, the project uses **mock APIs implemented in FastAPI**, **versioned n8n workflows**, **Docker-based local deployment**, and **repeatable test inputs**. This makes the repository appropriate for:

- thesis demonstrations
- academic replication
- local benchmarking
- architecture reviews
- reproducibility-oriented presentations

## Reproducibility first

Reproducibility is a first-class concern in this repository.

The project is structured so that a reviewer can:

1. start the local stack with Docker,
2. import the corresponding n8n workflow,
3. trigger the scenario with a fixed payload,
4. observe deterministic or controlled-random behavior,
5. collect latency and execution evidence,
6. repeat the same experiment under the same conditions.

To support this, the repository includes:

- self-hosted infrastructure under `infra/`
- importable n8n workflows under `workflows/`
- dedicated mock services for each case study
- request-level controls for delay, jitter, business rejection, and technical failure
- Postman assets for Case A and case B
- technical documents and dashboard material under `docs/`

## Case studies included

### Case A — Digital Tullave recharge

This scenario models a digital recharge flow for the Tullave / TransMilenio ecosystem. n8n orchestrates the end-to-end transaction by coordinating simulated external services such as funds validation, bank confirmation, collection authorization, recharge activation, fiscal reporting, and email notification.

Main workflow:

- `workflows/casoA/CASO A - FINAL.json`

Primary webhook path:

- `casoA-recarga-tullave-v2`

Mock API base URL inside Docker:

- `http://casea-mock-api:8001`

### Case B — Digital complaint filing

This scenario models a digital complaint workflow involving authentication, identity verification, police classification, prosecution registration, georeferencing, and citizen notification.

Recommended workflow:

- `workflows/casoB/CASO_B_Denuncia_Digital_v6_FINAL.json`

Recommended webhook path:

- `casoB-denuncia-digital-full`

Mock API base URL inside Docker:

- `http://caseb-mock-api:8002`

## Repository structure

```text
.
├── caseA_mock_api/                 # FastAPI mock services for Case A
├── caseB_mock_api/                 # FastAPI mock services for Case B
├── docs/
│   └── CasoA/                      # Technical and dashboard documentation
├── infra/                          # Docker Compose stack and environment files
├── metrics/                        # Reserved space for Prometheus/Grafana assets
├── postman_collections/            # Postman assets for Case A
├── screenshots/                    # Supporting screenshots
└── workflows/
    ├── casoA/                      # Current and historical Case A workflows
    └── casoB/                      # Current and historical Case B workflows
```

## Active local stack

The current Docker Compose stack lives in:

- `infra/docker-compose.yml`

When started, it brings up these core services:

| Service | Purpose | Port |
|---|---|---:|
| `postgres` | Database used by n8n | `5433` on host |
| `casea-mock-api` | Mock API for Case A | `8001` |
| `caseb-mock-api` | Mock API for Case B | `8002` |
| `n8n` | Workflow orchestration platform | `5678` |
| `metabase` | Optional dashboard layer | `3000` |

## Requirements

### Required

- **Docker**
- **Docker Compose** via the `docker compose` plugin

### Optional, for local API development only

- **Python 3.10+**
- `pip`

### Helpful tools

- **Postman** for manual API and workflow testing
- **cURL** for fast reproducible command-line checks

## Quick start

### 1. Prepare the environment file

The Compose stack is under `infra/`, so the environment file must live there as well.

From the repository root:

```bash
cp infra/.env.example infra/.env
```

You can use the provided defaults for a local academic setup, or adjust them if needed.

Example:

```env
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=admin123

N8N_HOST=localhost
N8N_PORT=5678
N8N_PROTOCOL=http

POSTGRES_DB=n8n
POSTGRES_USER=n8n
POSTGRES_PASSWORD=n8n
```

### 2. Start the full stack

```bash
cd infra
docker compose up -d --build
```

### 3. Verify the services

```bash
curl http://localhost:8001/health
curl http://localhost:8002/health
```

Then open:

- n8n: `http://localhost:5678`
- Metabase: `http://localhost:3000`

### 4. Import the workflows into n8n

Recommended imports:

- `workflows/casoA/CASO A - FINAL.json`
- `workflows/casoB/CASO_B_Denuncia_Digital_v6_FINAL.json`

### 5. Use the correct mock service URLs

If n8n and the mock APIs are running inside the same Compose network, **do not use `localhost` inside workflow HTTP nodes**. Use Docker service names instead:

- Case A: `http://casea-mock-api:8001`
- Case B: `http://caseb-mock-api:8002`

This is essential for reproducibility. Inside the n8n container, `localhost` refers to the n8n container itself, not to your host machine and not to the other services.

## Reproducible execution strategy

This repository supports two complementary experiment styles.

### Deterministic runs

Use deterministic settings when you want stable, repeatable execution during demonstrations, screenshots, or baseline measurements.

Recommended approach:

- keep global failure rate at `0`
- keep global delay range fixed
- set `delay_ms` and `jitter_ms` explicitly in the request body when needed
- reuse the same `transaction_id` naming convention per scenario

For near-zero mock variability, use:

```yaml
environment:
  MIN_DELAY_MS: 0
  MAX_DELAY_MS: 0
  FAIL_RATE: 0
```

You can also force deterministic behavior per request by sending `delay_ms`, `jitter_ms`, and `fail_rate` explicitly.

### Controlled stochastic runs

Use controlled randomness when you want to test tolerance under latency variation or injected failures.

Available controls include:

- `delay_ms`
- `jitter_ms`
- `fail_rate`
- `force_error`
- business-level rejection flags such as `force_reject` or `force_insufficient`

This makes it possible to reproduce not only successful flows, but also failure scenarios in a documented and auditable way.

## Case A mock API

### Endpoints

#### GET

- `/health`

#### POST

- `/funds/validate`
- `/bank/confirm`
- `/recaudo/bogota`
- `/tullave/activate`
- `/dian/report`
- `/notify/email`

### Base request shape

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

Additional business flags used by specific endpoints include:

- `force_insufficient`
- `force_reject`
- `channel`

## Case B mock API

### Endpoints

#### GET

- `/health`

#### POST

- `/id-gob/auth`
- `/registraduria/verify-identity`
- `/policia/classify`
- `/fiscalia/register`
- `/georef/geocode`
- `/notify/email`

### Typical request shape

```json
{
  "transaction_id": "caseb-001",
  "citizen_id": "cit-001",
  "document_number": "1010101010",
  "incident_description": "Robbery near station",
  "incident_address": "Bogota, Calle 26",
  "incident_category": "ROBBERY",
  "municipality_code": "11001",
  "delay_ms": 0,
  "jitter_ms": 0,
  "fail_rate": 0,
  "force_error": false
}
```

## Example reproducible requests

### Case A — test webhook

Use this when the workflow is listening in test mode from the n8n editor:

```bash
curl -X POST "http://localhost:5678/webhook-test/casoA-recarga-tullave-v2" \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: tx-e2e-ok-001" \
  -d '{
    "mock_base_url": "http://casea-mock-api:8001",
    "transaction_id": "tx-e2e-ok-001",
    "payment_status": "APPROVED",
    "amount": 12000,
    "account_balance": 50000,
    "delay_ms": 0,
    "jitter_ms": 0,
    "fail_rate": 0
  }'
```

### Case B — test webhook

```bash
curl -X POST "http://localhost:5678/webhook-test/casoB-denuncia-digital-full" \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: caseb-001" \
  -d '{
    "mock_base_url": "http://caseb-mock-api:8002",
    "transaction_id": "caseb-001",
    "citizen_id": "cit-001",
    "document_number": "1010101010",
    "incident_description": "Robbery near station",
    "incident_address": "Bogota, Calle 26",
    "incident_category": "ROBBERY",
    "municipality_code": "11001",
    "delay_ms": 0,
    "jitter_ms": 0,
    "fail_rate": 0
  }'
```

## Expected outputs

Depending on the scenario and the workflow version, a successful run should expose a consolidated result containing most or all of the following:

- transaction identifier
- overall status
- start and end timestamps
- end-to-end latency
- per-service response details
- correlation information
- simulated business decision outcomes

These outputs make the repository useful not only for functional validation, but also for evidence gathering during thesis demonstrations.

## Metrics supported by the repository

With the current implementation, the repository is especially suitable for collecting evidence related to:

- end-to-end workflow latency
- service-level latency from the mock APIs
- API interoperability behavior
- controlled technical failures
- business-rule rejections
- traceability through `transaction_id` and correlation identifiers
- local deployment repeatability

For broader infrastructure measurements such as CPU, memory, or long-run aggregation, the repository can be complemented with external observation tools such as:

- `docker stats`
- Prometheus
- Grafana
- post-processing scripts over exported execution data

## Postman assets

Case A includes ready-to-import Postman artifacts under:

- `postman_collections/CasoAColeccion.postman_collection.json`
- `postman_collections/CasoAEntorno.postman_environment.json`

These are useful when you want a GUI-based, repeatable test harness in addition to command-line cURL requests.

## Troubleshooting

### n8n cannot reach the mock API

Symptom:

- `ECONNREFUSED`
- `The service refused the connection - perhaps it is offline`

Most common cause:

- the workflow is trying to call `localhost` from inside the n8n container

Fix:

- use `http://casea-mock-api:8001` for Case A
- use `http://caseb-mock-api:8002` for Case B

### Test webhook does not respond

Most common causes:

- the workflow is not in **Listen for test event** mode
- the wrong webhook path is being used
- the workflow imported is not the one expected by the request payload

### Metabase fails with `database "metabase_app" does not exist`

The current Compose file points Metabase to a PostgreSQL database named `metabase_app`, but that database is not created automatically by the base PostgreSQL container.

If you want to use Metabase, create it manually after PostgreSQL starts:

```bash
docker exec -it n8n-postgres psql -U n8n -d postgres -c "CREATE DATABASE metabase_app;"
```

Then restart Metabase:

```bash
docker restart metabase
```

## Development notes

If you want to run a mock API outside Docker for debugging, you can start it locally with Uvicorn. Example for Case A:

```bash
cd caseA_mock_api
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

A similar approach applies to `caseB_mock_api/`.

When using host-based APIs while n8n stays inside Docker, remember that workflow URLs may need host-accessible values such as `host.docker.internal`, depending on your OS and Docker setup.

## Academic scope

This repository was created for **academic and experimental purposes** as part of a thesis on evaluating n8n as an integration platform in smart-city contexts.

All external services are simulated. The integrations represented here are **not official production integrations** with public entities, financial institutions, or judicial systems.

## Recommended citation inside presentations or documentation

When presenting this repository, describe it as:

> A self-hosted experimental environment for evaluating n8n as an event-driven integration layer for smart-city digital services, with emphasis on reproducibility, traceability, and controlled fault injection.

