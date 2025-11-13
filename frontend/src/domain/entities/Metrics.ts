/**
 * DOMAIN LAYER - Metrics Entity
 * Performance and compliance metrics for a single architecture.
 * This represents the flat data structure returned by the control-api.
 */

export interface SystemMetrics {
  architecture: string;
  total_transactions: number;
  total_violations: number;
  avg_latency_ms: number;
  max_processing_time_ms: number;
  min_processing_time_ms: number;
  // compliance_rate and violation_rate can be calculated on the frontend
}
