import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

export const ActionNode: React.FC<NodeProps> = ({ data, selected }) => {
  const simulationStatus = data.simulationStatus || 'inactive';
  const getActionIcon = (actionType: string) => {
    switch (actionType) {
      case 'send_email': return '📧';
      case 'create_task': return '✅';
      case 'update_status': return '🔄';
      case 'assign_user': return '👤';
      case 'call_webhook': return '🌐';
      default: return '🤖';
    }
  };

  return (
    <div className={`
      px-3 py-2 sm:px-4 sm:py-3 shadow-lg rounded-lg border-2 min-w-[140px] sm:min-w-[200px] transition-all
      ${selected ? 'border-green-500 ring-2 ring-green-200' : 'border-green-300'}
      ${simulationStatus === 'active' ? 'border-green-500 ring-2 ring-green-200 bg-green-50' : 'bg-green-50'}
    `}>
      {/* Входные точки */}
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-gray-400"
      />

      <div className="flex items-center space-x-2 sm:space-x-3">
        <div className="text-base sm:text-lg">{getActionIcon(data.config?.actionType)}</div>
        <div className="flex-1 min-w-0">
          <div className="font-medium text-gray-900 text-sm sm:text-base truncate">{data.label}</div>
          <div className="text-xs sm:text-sm text-gray-500 mt-1 hidden sm:block truncate">
            {data.config?.actionType && `Действие: ${data.config.actionType}`}
          </div>
        </div>
      </div>

      {/* Выходные точки */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 sm:w-3 sm:h-3 bg-green-400"
      />
    </div>
  );
};
