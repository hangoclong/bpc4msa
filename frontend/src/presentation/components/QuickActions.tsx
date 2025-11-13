/**
 * PRESENTATION LAYER - Quick Actions Panel
 * Send test transactions directly from dashboard
 */

'use client';

import { useState } from 'react';
import { Send, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

interface QuickActionsProps {
  architecture?: 'bpc4msa' | 'synchronous' | 'monolithic';
}

const CONTROL_API_URL = 'http://localhost:8080';

export function QuickActions({ architecture = 'bpc4msa' }: QuickActionsProps) {
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string } | null>(null);

  const sendTransaction = async (withViolation: boolean) => {
    setSending(true);
    setResult(null);

    try {
      const payload = withViolation
        ? {
            // Transaction with violations
            applicant_name: 'Test Violator',
            loan_amount: 2000000, // Exceeds max
            applicant_role: 'invalid_role', // Invalid role
            credit_score: 400, // Too low
            employment_status: 'unemployed',
            status: 'pending'
          }
        : {
            // Valid transaction
            applicant_name: 'Test Customer',
            loan_amount: 50000,
            applicant_role: 'customer',
            credit_score: 750,
            employment_status: 'employed',
            status: 'pending'
          };

      const response = await fetch(`${CONTROL_API_URL}/api/architectures/${architecture}/transactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        const data = await response.json();
        setResult({
          success: true,
          message: `✅ Transaction ${data.transaction_id} sent successfully!`
        });
      } else {
        const error = await response.text();
        setResult({
          success: false,
          message: `❌ Failed: ${error}`
        });
      }
    } catch (error) {
      setResult({
        success: false,
        message: `❌ Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`
      });
    } finally {
      setSending(false);
    }
  };

  const sendBatch = async (count: number, violationRate: number) => {
    setSending(true);
    setResult(null);

    let sent = 0;
    let failed = 0;

    try {
      for (let i = 0; i < count; i++) {
        const shouldViolate = Math.random() < violationRate;
        try {
          await sendTransaction(shouldViolate);
          sent++;
        } catch {
          failed++;
        }
        // Small delay between requests
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      setResult({
        success: true,
        message: `✅ Sent ${sent} transactions (${failed} failed)`
      });
    } catch (error) {
      setResult({
        success: false,
        message: `❌ Batch failed: ${error instanceof Error ? error.message : 'Unknown'}`
      });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Send className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-gray-900">Quick Actions</h3>
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Send test transactions to <strong className="text-gray-900">{architecture}</strong>
      </p>

      <div className="space-y-3">
        {/* Single Transactions */}
        <div className="flex gap-2">
          <button
            onClick={() => sendTransaction(false)}
            disabled={sending}
            className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium flex items-center justify-center gap-2"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
            Send Valid
          </button>
          <button
            onClick={() => sendTransaction(true)}
            disabled={sending}
            className="flex-1 bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm font-medium flex items-center justify-center gap-2"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <AlertCircle className="w-4 h-4" />}
            Send Violation
          </button>
        </div>

        {/* Batch Actions */}
        <div className="pt-3 border-t">
          <p className="text-xs text-gray-600 mb-2">Send Multiple:</p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => sendBatch(10, 0.3)}
              disabled={sending}
              className="bg-blue-600 text-white px-3 py-2 rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
            >
              10 Trans
            </button>
            <button
              onClick={() => sendBatch(25, 0.3)}
              disabled={sending}
              className="bg-blue-600 text-white px-3 py-2 rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
            >
              25 Trans
            </button>
            <button
              onClick={() => sendBatch(50, 0.3)}
              disabled={sending}
              className="bg-blue-600 text-white px-3 py-2 rounded text-xs hover:bg-blue-700 disabled:bg-gray-400"
            >
              50 Trans
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-1">30% violation rate</p>
        </div>

        {/* Result */}
        {result && (
          <div className={`p-3 rounded-lg text-sm ${
            result.success
              ? 'bg-green-50 border border-green-200 text-green-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}>
            {result.message}
          </div>
        )}
      </div>

      <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
        <strong>Tip:</strong> Switch to &quot;Live Monitoring&quot; tab to see events appear in real-time!
      </div>
    </div>
  );
}
