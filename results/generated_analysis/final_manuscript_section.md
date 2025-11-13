
# 6. System Implementation and Empirical Results

This section demonstrates the BPC4MSA artifact and presents the results of its empirical evaluation. We first provide an overview of the prototype implementation and illustrate its workflow with a use case. We then present the quantitative results of the comparative experiments.

## 6.1. Prototype Implementation Overview

To evaluate the BPC4MSA framework, a high-fidelity prototype was developed. The system is fully containerized using Docker and orchestrated via `docker-compose`. The architecture consists of several key microservices that realize the framework's design.

- **Key Services:** The core of the prototype includes the `business-logic` service, which exposes the primary API; the `compliance-service`, which acts as the rule engine; the `audit-service`, which logs all events to a PostgreSQL database for immutability; and a `socket-service` for real-time frontend monitoring.
- **Technology Stack:** The backend services are implemented in Python 3.11 with FastAPI. Asynchronous communication is handled by Apache Kafka, which serves as the event bus. The frontend dashboard is a Next.js application. The entire system, including baseline architectures for comparison (Synchronous SOA and Monolithic), is defined in `docker-compose` files for reproducible, one-command deployment.

## 6.2. Use Case Scenario: Loan Application Compliance

To demonstrate the framework in action, we use a loan application process. The workflow is as follows:

1.  **Define:** A compliance officer defines a rule in a `rules.json` file, such as *"Loan amounts cannot exceed $10,000."* 
2.  **Enforce (Runtime):** A user submits a loan application for $15,000 via the `business-logic` API. The service publishes a `LoanApplicationReceived` event to a Kafka topic.
3.  **Monitor:** The `compliance-service`, subscribed to this topic, consumes the event. It evaluates the event payload against the rules and detects a violation.
4.  **Audit & Remediate:** The `compliance-service` publishes a `ViolationDetected` event. The `audit-service` consumes both the original and violation events, logging them to the immutable audit trail. The `socket-service` broadcasts the events to the frontend dashboard, where the violation is highlighted in red for immediate visibility.

This workflow demonstrates the end-to-end, decoupled, and real-time nature of the BPC4MSA framework.

## 6.3. Empirical Evaluation Results

The following subsections present the quantitative results of the comparative experiments designed to evaluate the framework's performance (NQ1) and adaptability (NQ3). The analysis is based on two valid high-load experimental runs, after excluding one anomalous initial run where system performance had not stabilized.

### 6.3.1. Performance and Scalability (NQ1)

**Table 6.1: Performance Comparison of Architectures (Mean ± SD across 2 high-load runs)**

| Architecture   | Throughput (req/min)       | Avg Latency (ms)   |
|:---------------|:---------------------|:--------------|
| bpc4msa        | 17,657.29 ± 1,504.72 | 64.75 ± 81.83 |
| synchronous    | 14,401.04 ± 2,746.80 | 3.12 ± 0.81   |
| monolithic     | 14,634.84 ± 3,906.76 | 3.12 ± 1.14   |

A one-way ANOVA was conducted to evaluate the effect of architecture on throughput. The analysis revealed no statistically significant difference in mean throughput between the architectures, F(2, 3) = 0.79, p = 0.530. This suggests that, across the high-load runs, all three architectures demonstrated comparable throughput capabilities, although with notable variance between runs. BPC4MSA showed the highest peak throughput in one run, while the Monolithic architecture showed the highest in another, indicating performance sensitivity to specific test conditions.

A one-way ANOVA on latency also showed no statistically significant difference, F(2, 3) = 1.13, p = 0.430. However, a qualitative review of the data reveals a critical trend: the BPC4MSA architecture exhibited high performance variance, with its latency spiking to over 122 ms in one run, whereas the Monolithic and Synchronous architectures remained consistently in the low single-digit millisecond range. This highlights a key trade-off: BPC4MSA's decoupling may enable high throughput, but it comes at the cost of predictable latency.

*It is important to note that with a small number of experimental runs (n=2), the statistical power of the ANOVA test is limited. While no significant differences were detected, the descriptive statistics and qualitative trends provide valuable insights into the performance characteristics and trade-offs of each architecture.*

### 6.3.2. Adaptability (NQ3)

To evaluate adaptability, a qualitative and quantitative test was performed to measure the effort required to add a new compliance rule.

**Table 6.2: Adaptability Metrics for Implementing a New Compliance Rule**

| Metric                | BPC4MSA (Event-Driven) | Synchronous SOA | Monolithic BPMS |
| --------------------- | ---------------------- | --------------- | --------------- |
| **Time-to-Implement** | ~15 minutes            | ~25 minutes     | ~22 minutes     |
| **LOC Changed**       | **~8 lines**           | ~25 lines       | ~23 lines       |
| **Services Impacted** | **0 (Hot-reload)**     | 1 (Restart)     | 1 (Restart)     |

The results for the adaptability experiment show a clear advantage for the BPC4MSA framework. The change was accomplished by adding a new rule to an external `rules.json` configuration file. This file was automatically hot-reloaded by the `compliance-service` with zero downtime or service restarts. In contrast, both the Synchronous and Monolithic architectures required code modifications within the service logic and a full application restart to apply the new rule, demonstrating lower adaptability and higher operational friction.
