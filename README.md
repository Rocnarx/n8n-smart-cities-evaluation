# Evaluación de n8n como plataforma de integración (EAI) para ciudades inteligentes
# Evaluation of n8n as an integration platform (EAI) for smart cities

---

## 🇪🇸 Español

### Descripción general

Este repositorio contiene la **infraestructura experimental**, los **casos de estudio** y los **artefactos de medición** utilizados para evaluar **n8n** como una **capa de Enterprise Application Integration (EAI)** orientada a eventos en el contexto de **ciudades inteligentes**.

El objetivo principal es generar **evidencia técnica reproducible** sobre la idoneidad y la sostenibilidad operativa de una plataforma *low-code, open-source y self-hosted* para la integración de servicios digitales urbanos.

---

### 🎯 Objetivo del repositorio

Este repositorio permite:

- Desplegar un entorno **self-hosted reproducible** de n8n mediante Docker.
- Implementar **casos de estudio representativos** de servicios urbanos.
- Ejecutar **experimentos controlados** para medir:
  - Latencia de extremo a extremo (E2E)
  - Tolerancia a fallos y recuperación automática
  - Interoperabilidad mediante APIs
  - Consumo de recursos
  - Sostenibilidad operativa
- Visualizar métricas mediante un **dashboard experimental**.

El diseño del repositorio prioriza la **replicabilidad, trazabilidad y auditabilidad**, alineado con buenas prácticas académicas y de arquitectura de software.

---

### 🧠 Contexto académico

Proyecto de grado – Ingeniería de Sistemas  
Universidad Distrital Francisco José de Caldas  

**Tema:**  
Evaluación de n8n como herramienta de integración de servicios digitales en el contexto de ciudades inteligentes.

El estudio **no busca comparar múltiples herramientas**, sino analizar **bajo qué condiciones técnicas y operativas** n8n cumple los requisitos mínimos de una EAI moderna en escenarios urbanos.

---

### 🏗️ Arquitectura general (alto nivel)

- n8n como **capa central de orquestación**
- Integración basada en:
  - Eventos (webhooks)
  - APIs REST
  - Flujos declarativos
- Ejecución en **queue mode** con workers
- Observabilidad mediante métricas y logs
- Despliegue completamente **self-hosted**

La arquitectura detallada se documenta en `docs/architecture.md`.

---

### 📁 Estructura del repositorio

```
n8n-smart-cities-evaluation/
├── infra/                  # Infraestructura (Docker, variables de entorno)
│   ├── docker-compose.yml
│   └── .env.example
│
├── workflows/              # Flujos n8n exportables (.json)
│   ├── casoA/
│   └── casoB/
│
├── metrics/                # Observabilidad
│   ├── prometheus/
│   └── grafana/
│
├── experiments/            # Experimentos controlados
│   ├── load-tests/
│   └── fault-injection/
│
├── docs/                   # Documentación técnica
│   ├── architecture.md
│   └── methodology.md
│
├── README.md
└── .gitignore
```

---

### 🧪 Casos de estudio

**Caso A – Recarga digital**  
Modelo experimental de un flujo de recarga digital con validaciones, integración vía APIs simuladas, manejo de errores y notificación.

**Caso B – Denuncia digital**  
Modelo experimental de integración interinstitucional con autenticación simulada, clasificación, enrutamiento y trazabilidad.

> ⚠️ Todos los servicios externos son **mocks/simulados**, utilizados únicamente con fines experimentales.

---

### 📊 Métricas evaluadas

- Latencia E2E (p50, p95, p99)
- Tasa de error y recuperación automática
- Reintentos
- Uso de CPU y memoria
- Comportamiento bajo carga
- Mantenibilidad de flujos

La metodología se describe en `docs/methodology.md`.

---

### 🚀 Estado del proyecto

- [x] Estructura del repositorio
- [ ] Infraestructura Docker
- [ ] Flujos base Caso A y B
- [ ] Dashboard de métricas
- [ ] Experimentos
- [ ] Documentación final

---

### 🔁 Reproducibilidad

Cualquier evaluador puede:

1. Clonar el repositorio  
2. Levantar el entorno con Docker  
3. Importar los flujos  
4. Ejecutar los experimentos  
5. Validar las métricas  

---

## 🇺🇸 English

### Overview

This repository contains the **experimental infrastructure**, **case studies**, and **measurement artifacts** used to evaluate **n8n** as an **Enterprise Application Integration (EAI)** layer in the context of **smart cities**.

The main goal is to generate **reproducible technical evidence** regarding the technical suitability and operational sustainability of a *low-code, open-source, self-hosted* platform for urban digital service integration.

---

### 🎯 Repository purpose

This repository enables:

- Deployment of a **reproducible self-hosted** n8n environment using Docker.
- Implementation of **representative urban service case studies**.
- Execution of **controlled experiments** to measure:
  - End-to-end latency (E2E)
  - Fault tolerance and automatic recovery
  - API-based interoperability
  - Resource consumption
  - Operational sustainability
- Visualization of metrics through an **experimental dashboard**.

The repository is designed to be **replicable, traceable, and auditable**, aligned with academic and software architecture best practices.

---

### 🧠 Academic context

Undergraduate thesis project – Systems Engineering  
Universidad Distrital Francisco José de Caldas  

**Topic:**  
Evaluation of n8n as a digital service integration platform in smart city environments.

The study **does not aim to compare multiple tools**, but rather to analyze **under which technical and operational conditions** n8n satisfies the requirements of a modern EAI in urban scenarios.

---

### 🏗️ High-level architecture

- n8n as the **central orchestration layer**
- Event-driven integration using:
  - Webhooks
  - REST APIs
  - Declarative workflows
- Execution in **queue mode** with workers
- Observability via metrics and logs
- Fully **self-hosted deployment**

Detailed architecture is documented in `docs/architecture.md`.

---

### 🧪 Case studies

**Case A – Digital recharge integration**  
Experimental model of a digital recharge workflow including validation, API integration (mocked), error handling, and notification.

**Case B – Digital complaint process**  
Experimental inter-institutional integration model with simulated authentication, classification, routing, and full traceability.

> ⚠️ All external services are **mocked/simulated** and used strictly for experimental purposes.

---

### 📊 Evaluated metrics

- End-to-end latency (p50, p95, p99)
- Error rate and recovery
- Automatic retries
- CPU and memory usage
- Load behavior
- Workflow maintainability

Measurement methodology is documented in `docs/methodology.md`.

---

### 📄 License

This repository is intended for **academic and experimental use**.  
Usage of n8n is subject to its corresponding license.

---

### ✍️ Author

Systems Engineering Student  
Universidad Distrital Francisco José de Caldas
