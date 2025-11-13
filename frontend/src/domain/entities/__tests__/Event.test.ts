import { ComplianceEvent } from '../Event';

describe('ComplianceEvent Entity', () => {
  describe('hasViolations', () => {
    it('should return true when violations array has items', () => {
      const violations = [
        { rule_id: 'R1', rule_description: 'Test rule', severity: 'high' as const }
      ];
      const event = new ComplianceEvent('business-event', new Date(), 'TX123', violations);

      expect(event.hasViolations()).toBe(true);
    });

    it('should return false when violations array is empty', () => {
      const event = new ComplianceEvent('business-event', new Date(), 'TX123', []);

      expect(event.hasViolations()).toBe(false);
    });

    it('should return false when violations is undefined', () => {
      const event = new ComplianceEvent('business-event', new Date(), 'TX123');

      expect(event.hasViolations()).toBe(false);
    });
  });

  describe('constructor', () => {
    it('should create event with all properties', () => {
      const timestamp = new Date();
      const violations = [
        { rule_id: 'R1', rule_description: 'Test', severity: 'low' as const }
      ];
      const metadata = { custom: 'data' };

      const event = new ComplianceEvent(
        'violation',
        timestamp,
        'TX456',
        violations,
        metadata
      );

      expect(event.eventType).toBe('violation');
      expect(event.timestamp).toBe(timestamp);
      expect(event.transactionId).toBe('TX456');
      expect(event.violations).toEqual(violations);
      expect(event.metadata).toEqual(metadata);
    });
  });
});
