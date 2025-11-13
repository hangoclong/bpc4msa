/**
 * PRESENTATION LAYER - Architecture Selector Component
 * Allows user to select the active architecture for testing
 */

'use client';

import { Server } from 'lucide-react';
import { ArchitectureType } from '../../domain/entities/Experiment';

interface ArchitectureSelectorProps {
  activeArchitecture: ArchitectureType;
  onArchitectureChange: (architecture: ArchitectureType) => void;
}

const architectures: { id: ArchitectureType; name: string; color: string }[] = [
  { id: 'bpc4msa', name: 'BPC4MSA', color: 'blue' },
  { id: 'synchronous', name: 'Synchronous', color: 'green' },
  { id: 'monolithic', name: 'Monolithic', color: 'purple' },
];

export function ArchitectureSelector({
  activeArchitecture,
  onArchitectureChange,
}: ArchitectureSelectorProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <div className="flex items-center gap-2 mb-4">
        <Server className="w-6 h-6 text-gray-700" />
        <h2 className="text-xl font-bold text-gray-900">Active Architecture</h2>
      </div>
      <p className="text-sm text-gray-600 mb-4">
        Select the architecture to target for sending transactions and viewing metrics.
      </p>
      <div className="grid grid-cols-3 gap-3">
        {architectures.map((arch) => (
          <button
            key={arch.id}
            type="button"
            onClick={() => onArchitectureChange(arch.id)}
            className={`p-4 rounded-lg border-2 text-center transition-all ${
              activeArchitecture === arch.id
                ? `border-${arch.color}-500 bg-${arch.color}-50 ring-2 ring-${arch.color}-300`
                : 'border-gray-200 hover:border-gray-400'
            }`}
          >
            <div className={`font-semibold text-gray-900`}>{arch.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}
