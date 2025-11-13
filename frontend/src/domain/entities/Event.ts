/**
 * DOMAIN LAYER - Event Entity
 * Represents real-time compliance events
 */

export interface Violation {
  rule_id: string;
  rule_description: string;
  violated_field: string;
  violated_value: string | number | boolean;
}

export type EventType =
  | 'TransactionCreated'
  | 'ComplianceChecked'
  | 'ViolationDetected'
  | 'AuditLogged';

export class ComplianceEvent {
  constructor(
    public readonly eventType: EventType,
    public readonly timestamp: Date,
    public readonly transactionId?: string,
    public readonly violations?: Violation[],
    public readonly metadata?: Record<string, unknown>,
    public readonly architecture?: string
  ) {}

  hasViolations(): boolean {
    return (this.violations?.length ?? 0) > 0;
  }

  isCompliant(): boolean {
    return !this.hasViolations();
  }

  getViolationCount(): number {
    return this.violations?.length ?? 0;
  }
}
