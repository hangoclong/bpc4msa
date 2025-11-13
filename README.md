# BPC4MSA (Business Process Compliance for Microservices Architecture)

This repository contains the complete implementation and research materials for the BPC4MSA framework, a system designed to empirically validate business process compliance approaches across different software architectures.

## Authors

- N. Long Ha* (University of Economics, Hue University) — corresponding author, hnlong@hueuni.edu.vn
- S. Huong Do (University of Economics, Hue University)
- Quan Truong Tan (University of Economics, Hue University)

## Project Overview

`paper.md` documents the Design Science Research study that produced BPC4MSA, a cloud-native framework meant to close long-standing gaps between design-time policy engineering and runtime enforcement in microservices and cloud environments. The framework is driven by four core capabilities derived from scenario analysis and a systematic literature review:
- **Policy lifecycle management (C1):** machine-readable rule authoring, semantic enrichment, change management, and pattern libraries for reusable controls.
- **Proactive assurance (C2):** design-time and CI/CD integrations that verify services against compliance rules before deployment.
- **Runtime monitoring (C3):** distributed event capture, correlation, and asynchronous compliance checking over an event bus.
- **Auditing & feedback (C4):** immutable event logs, reporting services, and a feedback path that aims to repair the “Broken Feedback Loop” between runtime insights and policy updates.

## Research Prototype & Experiments

The repository hosts the prototype evaluated in Section 6 of `paper.md`. The prototype instantiates the full event-driven vision of BPC4MSA using Python 3.9, FastAPI, Kafka, and PostgreSQL, and runs the same loan-origination process implemented by two baselines (synchronous SOA and monolith) for apples-to-apples comparisons. Experiment automation lives in `run_experiment.sh`, `experiments/`, and `results/`, and relies on Locust-driven stepped-load tests combined with a CPU-intensive 0-1 knapsack compliance check to stress the design’s non-functional qualities.

Key empirical findings:
- The event-driven prototype consumes ~40% more CPU than the baselines, confirming the “resilience tax” of decoupled messaging.
- Throughput per CPU drops by roughly the same margin, but the Kafka-backed queue enables graceful degradation (slow-fail) instead of hard crashes when load spikes, validating the asynchronous auditing pattern.
- The current prototype intentionally omits horizontal consumer scaling; extending it is the primary next step to fully close the feedback-loop mechanism and to benchmark end-to-end latency, as outlined in Section 7 of `paper.md`.

## 🚀 Getting Started

**Prerequisites**
- Docker Desktop / Engine 24+ with the Compose plugin
- ~16 GB RAM available so all three reference architectures can run together
- Bash-compatible shell for the helper scripts in this repo

**1. Boot the full platform**

```bash
git clone https://github.com/<your-org>/bpc4msa-os.git
cd bpc4msa-os
docker compose up --build
```

This command launches the frontend UI (`http://localhost:3000`), control API (`:8080`), statistical analysis service (`:8003`), and all three loan-origination architectures:
- BPC4MSA event-driven stack (`:8000`) backed by Kafka, ZooKeeper, and Postgres
- Synchronous SOA baseline (`:8001`) with a dedicated Postgres instance
- Monolithic baseline (`:8002`) with its own Postgres database

**2. Drive traffic through any architecture**

```bash
./run_experiment.sh bpc4msa 200 0.3   # architecture, transactions, violation_rate
```

Swap the first argument with `synchronous` or `monolithic` to hit the other stacks. The script replays the request profile used in the paper, mixing compliant and violating loan applications. Progress appears in the terminal, and the dashboard’s **Compare Results** tab updates live through the control API and WebSocket service.

**3. Optional load testing & analysis**
- Use `load-testing/locustfile.py` with Locust for stepped-load experiments that reproduce the figures in the paper.
- Export structured CSV/JSON artifacts via `export_experiment_data.py` or reprocess saved runs under `results/`.

**4. Tear everything down**

```bash
docker compose down -v
```

This stops all services and removes the local Docker volumes that hold Postgres state.

